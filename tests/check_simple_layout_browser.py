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
 page.add_init_script("window.BrowserTransport={};document.addEventListener('DOMContentLoaded',()=>document.documentElement.classList.add('browser-client'))")
 page.set_viewport_size({'width':1440,'height':1000})
 page.goto('https://studio.local/')
 page.evaluate('Promise.all([LayerEditor.ready,BoothTemplates.ready,NameLabels.ready,CardArt.ready])')
 page.evaluate("Object.defineProperty(screen,'width',{value:1440,configurable:true});Object.defineProperty(screen,'height',{value:1000,configurable:true});state.media=5012;state.mode='photo';state.photos=[];addPhotos(Array.from({length:6},()=>({src:'/sample.svg'})))")
 page.wait_for_function('state.photos.length===6&&ready()')
 page.evaluate("state.photos.forEach((p,i)=>{const src='/private/photos/everyday-'+i+'.jpg';images.set(src,images.get(p.src));p.src=src;});render()")
 page.wait_for_selector('#sheet.desktop-inspector .template-card')
 assert not errors,errors
 # Empty plain/template previews share identical paper bounds and visible photo slots.
 for media in [5012,5009,5014]:
  page.evaluate("m=>{state.media=m;state.splitLayout='portrait';state.photos=[];state.active=0;state.emptyPhotoWork={template:'single',layout:{orientation:'portrait',gap:16},slots:{},layers:[]};PhotoWorks.activate();render();save()}",media)
  page.wait_for_timeout(100)
  assert page.locator('#preview').is_visible()
  assert page.locator('#empty').is_hidden()
  assert page.locator('#printBtn').is_disabled()
  assert page.evaluate('emptyPhotoFrames.length')==(2 if media==5014 else 1)
  bounds=page.locator('#preview').bounding_box()
  page.evaluate("PhotoFlow.apply('booth-life-watch');render()")
  page.wait_for_timeout(100)
  templated=page.locator('#preview').bounding_box()
  assert abs(bounds['width']-templated['width'])<2 and abs(bounds['height']-templated['height'])<2,(media,bounds,templated)
  page.evaluate("PhotoFlow.apply('single');render()")
  point=page.evaluate("""()=>{const c=$('preview'),r=c.getBoundingClientRect(),v=CropEditor.geometry(),f=emptyPhotoFrames[0],p=PhotoWindows.point(f,{x:f.x+f.w/2,y:f.y+f.h/2});return {x:r.left+(p.x+v.tx)*r.width/c.width,y:r.top+(p.y+v.ty)*r.height/c.height}}""")
  count=page.evaluate('(window.picks||[]).length');page.mouse.click(**point)
  assert page.evaluate('(window.picks||[]).length')==count+1
 # Only two layout choices, with no separate half-orientation or view controls.
 assert page.locator('[data-desktop-direction]').count()==2
 assert page.locator('#desktopSplitView').count()==0
 page.locator('[data-desktop-direction=landscape]').click();page.wait_for_timeout(100)
 assert page.evaluate('state.splitLayout')=='landscape'
 assert page.evaluate('logicalSize()')==[1824,1216]
 assert page.evaluate('PhotoWorks.panelSize()')==[912,1216]
 assert page.evaluate('emptyPhotoFrames.every((f,i)=>{const b=PhotoWindows.bounds(f);return b.left>=i*912-.01&&b.right<=(i+1)*912+.01&&b.top>=-.01&&b.bottom<=1216.01})')
 page.locator('[data-desktop-direction=portrait]').click();page.wait_for_timeout(100)
 assert page.evaluate('logicalSize()')==[1216,1824]
 assert page.evaluate('PhotoWorks.panelSize()')==[1216,912]
 # Photos keep separate templates, but both halves follow the same page layout choice.
 page.evaluate("addPhotos([{src:'/sample.svg'},{src:'/sample.svg'}])")
 page.wait_for_function('state.photos.length===2&&ready()')
 page.evaluate("PhotoWorks.select(0);PhotoFlow.apply('booth-life-watch');PhotoWorks.select(1);PhotoFlow.apply('booth-fun-volcano');render()")
 for layout in ['portrait','landscape']:
  page.locator('[data-desktop-direction='+layout+']').click();page.wait_for_timeout(100)
  assert page.evaluate('state.splitLayout')==layout
  assert page.evaluate('PhotoWorks.panelSize()')==([1216,912] if layout=='portrait' else [912,1216])
  before=page.evaluate('JSON.stringify([state.active,state.splitLayout,PhotoWorks.currentId()])')
  assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
  assert page.evaluate('JSON.stringify([state.active,state.splitLayout,PhotoWorks.currentId()])')==before
  assert page.evaluate('photoFrames.map(f=>state.photos.indexOf(f.p))')==[0,1]
  assert page.evaluate("JSON.parse(JSON.stringify(state)).photos.map(p=>p.work.template)")==['booth-life-watch','booth-fun-volcano']
  assert page.evaluate("ProjectFile.encode().then(s=>ProjectFile.decode(s)).then(p=>p.editing.splitLayout)")==layout
 # Mobile exposes the same two choices and no extra view switch.
 page.set_viewport_size({'width':390,'height':844})
 page.evaluate('openPaper()');page.wait_for_timeout(100)
 assert page.locator('[data-setting=splitLayout]').count()==2
 assert page.locator('[data-setting=splitOrientation]').count()==0
 assert page.locator('#toggleSplitView').count()==0
 page.evaluate('closeSheet()')
 # Final desktop evidence of the simpler controls and consistent empty frame.
 page.set_viewport_size({'width':1440,'height':1000})
 page.evaluate("state.photos=[];state.active=0;state.emptyPhotoWork.template='single';PhotoWorks.activate();render()")
 page.wait_for_timeout(300);page.screenshot(path=str(ROOT/'simple-empty.png'))
 assert not errors,errors
 browser.close()
 print('PASS empty plain/template paper bounds and pick targets, two layout choices, correct half geometry, templates and print batching, project persistence and mobile controls; no printing')
