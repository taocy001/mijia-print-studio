"""Decode final JPEGs with macOS Vision; no target URL is visited or printed."""
import mimetypes
import base64
import json
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
decoder=Path(tempfile.gettempdir())/'liuying-decode-qr'
subprocess.run(['xcrun','swiftc',str(ROOT/'tests/decode_qr.swift'),'-o',str(decoder)],check=True)
with sync_playwright() as runtime:
    browser=runtime.chromium.launch();page=browser.new_page(viewport={'width':390,'height':844});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script("window.Studio={landscape:()=>innerWidth>innerHeight,state:()=>'{\"device\":{},\"history\":[]}',printBatch:()=>{throw Error('No printing')}}")
    def route(r):
        assert r.request.method=='GET' and urlparse(r.request.url).hostname=='studio.test'
        file=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.LabelBatch&&window.StudioExtras');page.evaluate('NameLabels.ready');page.evaluate('LayerEditor.ready')
    page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});}")
    links=['https://example.org/media/one','https://example.org/clip?a=1&b=two#start','https://例子.测试/照片?页=一','https://example.org/'+ 'x'*150]
    for media,orientation in [(5009,'portrait'),(5012,'portrait'),(5012,'landscape'),(5014,'portrait')]:
        for index,url in enumerate(links):
            result=page.evaluate("""async([media,orientation,url,index])=>{
              const text=QrSticker.normalize(url),o={kind:'qr',id:'test',text,sizePct:index===3?2:28,fx:index===0?.98:.3333,fy:index===0?.98:.6667,angle:0,hidden:false};
              state={...defaults,mode:'photo',media,orientation,photos:[{src:'/sample.svg',filter:'none',turn:0,zoom:1,x:0,y:0,overlays:[o]}],active:0};
              const pages=await preparePrintPages();return {text,page:pages[0],qr:QrSticker.code(text).size};
            }""",[media,orientation,url,index])
            with tempfile.NamedTemporaryFile(suffix='.jpg') as image:
                image.write(base64.b64decode(result['page']['base64']));image.flush()
                values=json.loads(subprocess.check_output([str(decoder),image.name],text=True))
            assert result['text'] in values,(media,orientation,index,values)
            assert result['page']['ocMask'] is None,result
    invalid=page.evaluate("""()=>['javascript:alert(1)','file:///tmp/a','https://user:password@example.org','not a link','https://example.org/'+ 'x'.repeat(600)].map(url=>{try{QrSticker.code(url);return false;}catch{return true;}})""")
    assert all(invalid),invalid
    guard=page.evaluate("""async()=>{
      state.media=5014;state.mode='collage';state.collageLayout='strip';
      state.photos=Array.from({length:6},()=>({src:'/sample.svg',filter:'none',overlays:[{kind:'qr',text:'https://example.org/'+ 'x'.repeat(150),sizePct:15,fx:.5,fy:.5,angle:0,hidden:false}]}));
      try{await preparePrintPages();return false;}catch(e){return e.message.includes('太小');}
    }""")
    tear=page.evaluate("""async()=>{state.mode='label';state.sceneLayers={label:[{kind:'qr',text:'https://example.org/',sizePct:25,fx:.5,fy:.5}]};try{await preparePrintPages();return false;}catch(e){return e.message.includes('撕线');}}""")
    assert tear
    assert guard,'Small strips must not export unreadable codes'
    page.evaluate("state={...defaults,media:5009,photos:[{src:'/sample.svg',overlays:[]}],active:0};render();")
    page.locator('#menuBtn').click();page.locator('#addQr').click()
    assert page.locator('#settingsBack').is_visible()
    page.screenshot(path='/tmp/qr-editor-mobile.png')
    page.locator('#qrUrl').fill(links[0]);page.locator('#applyQr').click()
    assert page.evaluate("active().overlays.length===1&&LayerEditor.selected().kind==='qr'")
    page.locator('#copyLayer').click();assert page.evaluate('active().overlays.length===2')
    page.locator('#editLayer').click();page.locator('#qrUrl').fill(links[1]);page.locator('#applyQr').click()
    assert page.evaluate('(url)=>active().overlays[0].text!==url&&active().overlays[1].text===url',links[1])
    page.keyboard.press('Delete');assert page.evaluate('active().overlays.length===1')
    package=page.evaluate('ProjectFile.encode()');decoded=page.evaluate('(raw)=>ProjectFile.decode(raw)',package)
    assert decoded['editing']['photos'][0]['overlays'][0]['kind']=='qr'
    masks=page.evaluate("""async()=>{active().overlays[0].hidden=true;active().overlays[0].angle=90;const pages=await preparePrintPages();return {mask:pages[0].ocMask,angle:LayerEditor.metrics(active().overlays[0],1040,1040).angle};}""")
    assert masks=={'mask':None,'angle':0},masks
    assert not errors,errors;browser.close()
print('PASS: final JPEGs scan on all paper sizes, URL normalization, no network targets, size guards, isolated editing')
