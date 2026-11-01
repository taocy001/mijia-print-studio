"""Synthetic batch labels, local imports and pagination; never submits printing."""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch();page=browser.new_page(viewport={'width':390,'height':844});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script("window.Studio={landscape:()=>innerWidth>innerHeight,state:()=>'{\"device\":{},\"history\":[]}',printBatch:()=>{throw Error('No printing')}}")
    def route(r):
        assert r.request.method=='GET'
        file=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.LabelBatch&&window.StudioExtras');page.evaluate('NameLabels.ready');page.evaluate('LayerEditor.ready')
    parsed=page.evaluate(r'''()=>{
      const good=LabelBatch.parse('\uFEFF"Test, A","Sub ""B"""\r\nTest C,',true);
      const invalid=['','A,B,C','"A\nB",C','A"B,C','"A"x,B'];
      return {good,rejected:invalid.map(s=>{try{LabelBatch.parse(s,true);return false;}catch(e){return true;}})};
    }''')
    assert parsed['good']==[{'title':'Test, A','subtitle':'Sub "B"'},{'title':'Test C','subtitle':''}],parsed
    assert all(parsed['rejected']),parsed
    for media,orientation,capacity in [(5009,'portrait',4),(5012,'portrait',6),(5012,'landscape',2),(5014,'portrait',4)]:
        result=page.evaluate("""async([media,orientation,capacity])=>{
          state={...defaults,mode:'label',media,orientation,photos:[],active:0,labelBatchEnabled:true,labelBatchItems:Array.from({length:capacity+1},(_,i)=>({title:'TEST'+i,subtitle:''}))};
          const old=CanvasRenderingContext2D.prototype.fillText,seen=[];let current;
          CanvasRenderingContext2D.prototype.fillText=function(text,...args){if(current&&String(text).startsWith('TEST'))current.push(text);return old.call(this,text,...args)};
          try{for(let i=0;i<2;i++){current=[];compose(true,'photo',i);seen.push(current);}current=null;
            const before=compose().toDataURL(),pages=await preparePrintPages(),after=compose().toDataURL();
            state.labelBatchItems=Array.from({length:capacity*6+1},()=>({title:'X',subtitle:''}));let blocked=false;try{await preparePrintPages();}catch(e){blocked=true;}
            return {seen,count:pages.length,stable:before===after,blocked};
          }finally{CanvasRenderingContext2D.prototype.fillText=old;}
        }""",[media,orientation,capacity])
        assert result['seen']==[[f'TEST{i}' for i in range(capacity)],[f'TEST{capacity}']],(media,result)
        assert result['count']==2 and result['stable'] and result['blocked'],result
    page.evaluate("state.media=5009;state.orientation='portrait';state.labelBatchItems=[{title:'Saved',subtitle:''}];render();LabelBatch.open()")
    page.locator('#batchNames').fill('First\tSmall\nSecond')
    page.locator('#applyNames').click()
    assert page.evaluate('LabelBatch.items()')==[{'title':'First','subtitle':'Small'},{'title':'Second','subtitle':''}]
    with page.expect_file_chooser() as chooser:page.locator('#importNames').click()
    chooser.value.set_files({'name':'labels.csv','mimeType':'text/csv','buffer':b'"Imported, A",\nImported B,Small'})
    page.wait_for_function("LabelBatch.items()[0].title==='Imported, A'")
    with page.expect_file_chooser() as chooser:page.locator('#importNames').click()
    chooser.value.set_files({'name':'bad.csv','mimeType':'text/csv','buffer':b'A,B,C'})
    page.wait_for_function("document.getElementById('batchStatus').textContent.includes('两列')")
    assert page.evaluate("LabelBatch.items()[0].title==='Imported, A'")
    page.locator('[data-label-kind=single]').click()
    assert page.locator('#labelInput').count()==1 and page.evaluate('!LabelBatch.enabled()')
    page.locator('[data-label-kind=batch]').click()
    assert page.evaluate("LabelBatch.items()[0].title==='Imported, A'")
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path='/tmp/label-batch-mobile.png')
    assert not errors,errors;browser.close()
print('PASS: CSV quoting, ordered pagination on all papers, blank tail, overflow blocked, local import atomicity')
