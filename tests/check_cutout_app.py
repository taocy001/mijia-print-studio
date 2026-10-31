from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse,unquote
import mimetypes,io,json,random,sys
from PIL import Image
root=Path(__file__).resolve().parents[1];assets=root/'assets'

with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':411,'height':828},is_mobile=True,has_touch=True);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{},history:[]}),printBatch:()=>{throw Error('Printing is forbidden in tests')}}")
 def route(r):
  path=unquote(urlparse(r.request.url).path);file=assets/(path.lstrip('/') or 'index.html')
  if path.startswith('/private/'):
   buf=io.BytesIO();Image.new('RGB',(800,1200),'#387fa0').save(buf,'JPEG');r.fulfill(body=buf.getvalue(),content_type='image/jpeg');return
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing asset')
 page.route('https://studio.local/**',route);page.goto('https://studio.local/');page.wait_for_function('window.LayerEditor&&window.CropEditor&&window.StudioExtras');page.evaluate('LayerEditor.ready')

 page.evaluate("""async()=>{await CutoutEditor.ready;window.cutoutCalls=[];Studio.cutout=src=>{cutoutCalls.push(src);return JSON.stringify({ok:true})};await addPhotos([{src:'/private/photos/test-a.jpg'},{src:'/private/photos/test-b.jpg'}]);state.mode='id';state.media=5012;state.active=0;render();openLayout();}""")
 page.locator('[data-id-background=white]').click()
 assert page.evaluate("cutoutCalls.length")==1
 assert page.evaluate("preparePrintPages().then(()=>false,e=>e.message.includes('抠图'))")
 page.evaluate('state.active=1;render()')
 paths={c:'/private/cutouts/u2netp-v1-'+'a'*64+'-'+c+'.jpg' for c in ['white','blue','red']}
 page.evaluate("images=>nativeEvent({type:'cutout',value:{source:'/private/photos/test-a.jpg',images}})",paths)
 assert page.evaluate('state.photos[0].idBackground')=='white'
 assert page.evaluate('state.photos[1].idBackground||""')==''
 page.evaluate('state.active=0;render();openLayout()')
 page.locator('[data-id-background=blue]').click();page.wait_for_function("state.photos[0].idBackground==='blue'")
 assert page.evaluate('cutoutCalls.length')==1
 assert page.evaluate("CutoutEditor.source(active()).src.endsWith('-blue.jpg')")
 page.evaluate("state.mode='photo';render()")
 assert page.evaluate("CutoutEditor.source(active()).src.endsWith('/test-a.jpg')")
 page.evaluate("state.mode='id';state.active=1;render();openLayout()")
 page.locator('[data-id-background=red]').click();page.locator('[data-id-background=""]').click()
 page.evaluate("images=>nativeEvent({type:'cutout',value:{source:'/private/photos/test-b.jpg',images}})",paths)
 assert page.evaluate('state.photos[1].idBackground')==''
 page.evaluate("state.photos[1].idCutouts={};openLayout()")
 page.locator('[data-id-background=white]').click();page.evaluate("nativeEvent({type:'cutoutError',value:{source:'/private/photos/test-b.jpg',message:'测试失败'}})")
 assert page.evaluate('state.photos[1].idBackground')==''
 page.evaluate("state.active=0;state.mode='id';render();save();closeSheet()")
 before=page.evaluate('active().src');page.reload();page.wait_for_function('window.CutoutEditor');page.evaluate('CutoutEditor.ready')
 assert page.evaluate('active().src')==before and page.evaluate('active().idBackground')=='blue'
 assert page.evaluate("CutoutEditor.source(active()).src.endsWith('-blue.jpg')")
 assert not errors,errors
 print('PASS cutout bridge: pending print blocked, per-photo isolation, cached color switch, restore original during processing, failure and draft restore')
 b.close()
