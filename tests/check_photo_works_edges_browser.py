"""Verify full-original hold gestures and stable editor bounds without printing."""
import os,mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(**({'channel':os.environ['TEST_BROWSER_CHANNEL']} if os.environ.get('TEST_BROWSER_CHANNEL') else {}))
 page=browser.new_page();page.add_init_script("Object.defineProperty(crypto,'randomUUID',{value:undefined})");errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  f=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
  mime={'.js':'text/javascript','.svg':'image/svg+xml','.html':'text/html','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}.get(f.suffix,mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
  r.fulfill(body=f.read_bytes(),content_type=mime) if f.is_file() else r.fulfill(status=404)
 page.route('https://studio.local/**',route)
 page.add_init_script("window.deviceState={permission:true,device:{},history:[]};window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({}),pick:n=>{window.picks=(window.picks||[]).concat(n)},capture:()=>{window.captures=(window.captures||0)+1;return JSON.stringify({ok:true,id:'test-camera'})},captureAck:()=>JSON.stringify({ok:true}),printBatch:()=>{throw Error('Printing forbidden')}}")
 page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')

 page.evaluate('Promise.all([NameLabels.ready,CardArt.ready])')
 page.evaluate('BoothTemplates.ready')
 page.set_viewport_size({'width':390,'height':844})
 page.evaluate("Object.defineProperty(screen,'width',{value:390,configurable:true});Object.defineProperty(screen,'height',{value:844,configurable:true});state.media=5012;state.mode='photo';state.photos=[];addPhotos([{src:'/sample.svg'}])")
 page.evaluate('Studio.landscape=()=>innerWidth>innerHeight;updateEditorOrientation();render()')
 page.wait_for_function('!!printPreview&&canAdjustPhoto()')
 assert not errors,errors





 # Empty templates preview, cancel and filling remain usable.
 page.evaluate("state={...defaults,photos:[],mode:'photo'};PhotoWorks.initialize();PhotoFlow.apply('grid4');render()")
 page.locator('#templateBtn').click();page.evaluate("PhotoFlow.apply('horizontal')");page.locator('#effectCancel').click()
 assert page.evaluate('PhotoWorks.currentId()')=='grid4'
 page.evaluate("addPhotos(Array.from({length:2},()=>({src:'/sample.svg'})))")
 page.wait_for_function('state.photos.length===2&&ready()')
 assert page.evaluate('state.active')==0 and page.evaluate('PhotoFlow.missing()')==2
 page.evaluate("addPhotos(Array.from({length:2},()=>({src:'/sample.svg'})))")
 page.wait_for_function('state.photos.length===4&&ready()');page.evaluate('render()')
 assert page.evaluate('state.active')==0 and page.evaluate('PhotoFlow.missing()')==0
 # Page-level decorations are independent, just like templates.
 page.evaluate("LayerEditor.create({kind:'text',text:'Owner A'});PhotoWorks.select(1);render()")
 assert page.evaluate('LayerEditor.paperList().length')==0
 page.evaluate('PhotoWorks.select(0);render()');assert page.evaluate('LayerEditor.paperList()[0].text')=='Owner A'
 page.evaluate('LayerEditor.select(null);closeSheet();render()')
 # Slot long-press shows the original without changing focus/template/edits.
 point=page.evaluate("""()=>{const f=photoFrames[1],r=$('preview').getBoundingClientRect(),v=CropEditor.geometry();return{x:r.left+(f.x+f.w/2+v.tx)*r.width/$('preview').width,y:r.top+(f.y+f.h/2+v.ty)*r.height/$('preview').height}}""")
 cdp=page.context.new_cdp_session(page);cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{**point,'id':1}]})
 page.wait_for_timeout(550);assert page.evaluate('OriginalPreview.active()')
 cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});assert not page.evaluate('OriginalPreview.active()')
 # Native texture callbacks accept a live slot object, without modifying its source.
 page.evaluate("PhotoWorks.selectSlot(PhotoFlow.pagePhotos()[1]);Studio.pickTexture=()=>{};StudioExtras.openCoat()")
 page.locator('[data-coat="custom"]').click();page.evaluate("nativeEvent({type:'texture',value:[{src:'/sample.svg'}]})")
 page.wait_for_function('active().coatTexture==="custom"');assert page.evaluate('state.photos[1].coatTexture||null') is None
 page.evaluate('closeSheet()')
 # Face fitting still runs, but completed slots never cause a perpetual polling/render loop.
 result=page.evaluate("""()=>{let calls=0;const old=FaceCrop.plan;FaceCrop.plan=()=>{calls++;return{x:.1,y:.2,zoom:1}};for(const p of state.photos){p.facePending=true;p.faces=[{}];}for(const p of PhotoFlow.pagePhotos())p.facePending=true;state.photos[1].zoom=2;deviceState.device=native.device={connected:true,checkedAt:Date.now(),media:5012};applyPendingFaceCrop();const done=!PhotoWorks.hasPendingFaceCrop(),first=calls;syncPaper();FaceCrop.plan=old;return{done,calls,first,manual:state.photos[1].zoom}}""")
 assert result['done'] and result['calls']==result['first'] and result['calls']>0 and result['manual']==2,result
 # Real batch-selection UI produces only the checked works.
 page.evaluate('confirmPrint()');page.wait_for_selector('#choosePrintWorks');page.locator('#choosePrintWorks').click()
 page.locator('[data-print-work]').evaluate_all('(items)=>items.forEach(i=>i.checked=false)');page.locator('[data-print-work="0"]').check();page.locator('[data-print-work="1"]').check();page.locator('#confirmWorkBatch').click();page.wait_for_selector('#confirmSend')
 assert page.evaluate('pendingPrint.pages.length')==2
 # Old draft migration preserves its visible global collage on the first owner.
 page.evaluate("closeSheet()")
 # save() can use the current initialized work, so construct the legacy storage explicitly.
 page.evaluate("const d=JSON.parse(JSON.stringify(state));delete d.photoWorkVersion;for(const p of d.photos){delete p.work;delete p.photoId;}d.mode='collage';d.photoLayout='grid4';d.collageTemplateId=null;d.templateId=null;d.active=2;localStorage.setItem(window.STUDIO_DRAFT_KEY||'liuying-draft',JSON.stringify(d))")
 page.reload();page.wait_for_function('state.photos.length===4&&ready()&&window.PhotoWorks');page.evaluate('render()')
 assert page.evaluate('state.active')==0 and page.evaluate('PhotoWorks.currentId()')=='grid4'
 assert page.evaluate('state.photos[1].work.template')=='single'
 assert not errors,errors
 browser.close();print('PASS empty templates/fill, layers, slot original, custom texture callback, face-fit completion/manual crop, batch UI and legacy migration')
