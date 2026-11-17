"""Verify error guidance in both native and desktop browser UI without printing."""
import os,mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(**({'channel':os.environ['TEST_BROWSER_CHANNEL']} if os.environ.get('TEST_BROWSER_CHANNEL') else {}))
 page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  f=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
  mime={'.js':'text/javascript','.svg':'image/svg+xml','.html':'text/html','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}.get(f.suffix,mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
  r.fulfill(body=f.read_bytes(),content_type=mime) if f.is_file() else r.fulfill(status=404)
 page.route('https://studio.local/**',route)
 page.add_init_script("window.deviceState={permission:true,device:{},history:[]};window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({}),printBatch:()=>{throw Error('Printing forbidden')}}")
 page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')

 page.evaluate('Promise.all([NameLabels.ready,CardArt.ready])')
 modes=['template','collage','polaroid','calendar','id','idcard','label','card']
 for media in [5012,5009,5014]:
  for mode in modes:
   page.evaluate("([media,mode])=>{closeSheet();Object.assign(state,{media,mode,photos:[],active:0,orientation:'portrait',calendarLayout:'photo',collageLayout:'auto',templateId:null});render()}",[media,mode])
   assert page.locator('#paperStage').is_visible(),(media,mode)
   assert page.locator('#preview').is_visible(),(media,mode)
   assert not page.locator('#empty').is_visible(),(media,mode)
   assert page.evaluate('!!printPreview&&printPreview.width>0&&photoFrames.length===0'),(media,mode)
   printable=mode in ['label','card'] or mode=='calendar' and media==5014
   assert page.evaluate('ready()')==printable,(media,mode)
   assert page.locator('#printBtn').is_disabled()==(not printable),(media,mode)
   if not printable:
    assert not page.evaluate('canAdjustPhoto()'),(media,mode)
    assert page.evaluate("preparePrintPages().then(()=>false,()=>true)"),(media,mode)
    assert page.locator('#addMore').is_visible()
   if mode=='calendar':
    labels=page.evaluate("""()=>{const old=CanvasRenderingContext2D.prototype.fillText,seen=[];CanvasRenderingContext2D.prototype.fillText=function(...a){seen.push(a[0]);return old.apply(this,a)};try{compose()}finally{CanvasRenderingContext2D.prototype.fillText=old}return seen}""")
    assert any(' 年 ' in x for x in labels) and '15' in labels,labels
   page.evaluate('CropEditor.render()')
 page.evaluate("Object.assign(state,{mode:'calendar',media:5012,calendarLayout:'plain'});render()")
 assert page.evaluate('ready()')
 assert len(page.evaluate('preparePrintPages()'))==1
 page.evaluate("state.mode='collage';state.collageLayout='strip';render()")
 assert page.evaluate("""()=>{let n=0;const old=drawPhoto;drawPhoto=(...a)=>{n++;old(...a)};try{compose()}finally{drawPhoto=old}return n}""")==3
 # Every template can render before a photo is selected.
 page.evaluate("state.mode='template';state.media=5012")
 assert page.evaluate("""()=>{for(const t of TEMPLATE_CATALOG){state.templateId=t.id;render();if(!printPreview)throw Error(t.id)}return true}""")
 page.evaluate("state.mode='calendar';state.calendarLayout='photo';state.templateId=null;state.photos=[{src:'/sample.svg',overlays:[]}];state.active=0")
 page.evaluate("loadPhoto(state.photos[0]);");page.evaluate('render()')
 assert page.evaluate('ready()&&canAdjustPhoto()')
 assert len(page.evaluate('preparePrintPages()'))==1
 page.evaluate("state.photos.push({src:'/private/photos/missing.jpg'});render()")
 assert not page.evaluate('ready()') and page.locator('#paperStage').is_visible()
 page.evaluate("state.photos=[];state.active=0;render()")
 assert page.locator('#paperStage').is_visible() and page.evaluate('photoFrames.length===0')
 page.evaluate("state.mode='photo';render()")
 assert page.locator('#empty').is_visible() and not page.locator('#paperStage').is_visible()
 assert page.evaluate('printPreview===null&&photoFrames.length===0')
 assert not errors,errors
 browser.close()
print('PASS: empty previews in 8 modes x 3 papers; all templates; strips; add/remove/load failures; print guards; no printing')
