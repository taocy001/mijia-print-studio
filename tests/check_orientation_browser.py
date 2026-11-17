"""Verify full-original hold gestures and stable editor bounds without printing."""
import os,mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(**({'channel':os.environ['TEST_BROWSER_CHANNEL']} if os.environ.get('TEST_BROWSER_CHANNEL') else {}))
 context=browser.new_context();page=context.new_page();page.context.add_init_script("Object.defineProperty(crypto,'randomUUID',{value:undefined})");errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  f=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
  if urlparse(r.request.url).path.startswith('/private/photos/'):f=ROOT/'assets/sample.svg'
  mime={'.js':'text/javascript','.svg':'image/svg+xml','.html':'text/html','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}.get(f.suffix,mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
  r.fulfill(body=f.read_bytes(),content_type=mime) if f.is_file() else r.fulfill(status=404)
 page.context.route('https://studio.local/**',route)
 page.context.add_init_script("window.deviceState={permission:true,device:{},history:[]};window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({}),pick:n=>{window.picks=(window.picks||[]).concat(n)},capture:()=>{window.captures=(window.captures||0)+1;return JSON.stringify({ok:true,id:'test-camera'})},captureAck:()=>JSON.stringify({ok:true}),printBatch:()=>{throw Error('Printing forbidden')}}")
 page.context.add_init_script("window.BrowserTransport={};document.addEventListener('DOMContentLoaded',()=>document.documentElement.classList.add('browser-client'))")
 page.set_viewport_size({'width':1440,'height':1000})
 page.goto('https://studio.local/')
 page.evaluate('Promise.all([LayerEditor.ready,BoothTemplates.ready,NameLabels.ready,CardArt.ready])')
 page.evaluate("Object.defineProperty(screen,'width',{value:1440,configurable:true});Object.defineProperty(screen,'height',{value:1000,configurable:true});state.media=5012;state.mode='photo';state.photos=[];addPhotos(Array.from({length:6},()=>({src:'/sample.svg'})))")
 page.wait_for_function('state.photos.length===6&&ready()')
 page.evaluate("state.photos.forEach((p,i)=>{const src='/private/photos/everyday-'+i+'.jpg';images.set(src,images.get(p.src));p.src=src;});render()")
 page.wait_for_selector('#sheet.desktop-inspector .template-card')
 assert not errors,errors
 # Desktop controls live in the top bar and fit both common desktop widths.
 page.wait_for_selector('#desktopPaperTools')
 for width in [1000,1440]:
  page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(100)
  assert page.locator('#desktopPaperTools').is_visible()
  assert page.evaluate("document.querySelector('.topbar').scrollWidth<=innerWidth")
 page.evaluate("state.media=5014;state.sixLayout=5014;state.photos.forEach(p=>{p.work.template='single';p.work.layers=[];p.work.layout.splitOrientation='landscape';});PhotoWorks.select(0);render()")
 # Independent orientation settings and complete frame bounds for both halves.
 page.locator('[data-desktop-direction=portrait]').click();page.wait_for_timeout(100)
 assert page.evaluate('state.photos[0].work.layout.splitOrientation')=='portrait'
 assert page.evaluate('state.photos[1].work.layout.splitOrientation')=='landscape'
 assert page.evaluate('PhotoWorks.panelSize()')==[912,1216]
 assert page.evaluate('photoFrames.map(f=>state.photos.indexOf(f.p))')==[0,1]
 assert page.evaluate("photoFrames.every((f,i)=>{const b=PhotoWindows.bounds(f);return b.left>=-.01&&b.right<=1216.01&&b.top>=i*912-.01&&b.bottom<=(i+1)*912+.01})")
 page.evaluate('EditHistory.undo()');assert page.evaluate('state.photos[0].work.layout.splitOrientation')=='landscape'
 page.evaluate('EditHistory.redo()');assert page.evaluate('state.photos[0].work.layout.splitOrientation')=='portrait'
 # Rotating the whole preview preserves the pixels of the physical print.
 page.evaluate("LayerEditor.create({text:'MASK',hidden:true,fx:.3,fy:.4});window.physicalBefore=physical(compose()).toDataURL();window.maskBefore=physical(compose(true,'mask')).toDataURL()")
 page.locator('#desktopSplitView').click();page.wait_for_timeout(100)
 assert page.evaluate('logicalSize()')==[1824,1216]
 assert page.evaluate('physical(compose()).toDataURL()===physicalBefore')
 assert page.evaluate("physical(compose(true,'mask')).toDataURL()===maskBefore")
 assert page.evaluate("photoFrames.every((f,i)=>{const b=PhotoWindows.bounds(f);return b.left>=i*912-.01&&b.right<=(i+1)*912+.01&&b.top>=-.01&&b.bottom<=1216.01})")
 page.evaluate('PhotoWorks.select(1);render()')
 page.wait_for_function("document.getElementById('desktopWorkTarget').textContent.includes('右幅')")
 page.locator('[data-desktop-direction=portrait]').click();page.wait_for_timeout(100)
 assert page.evaluate('state.photos[0].work.layout.splitOrientation')=='portrait'
 assert page.evaluate('state.photos[1].work.layout.splitOrientation')=='portrait'
 # Actual template/shape rendering, and rendering a batch does not change editing state.
 page.evaluate("PhotoWorks.select(0);PhotoFlow.apply('booth-life-watch');PhotoWorks.select(1);PhotoFlow.apply('booth-fun-volcano');render()")
 signature=page.evaluate('JSON.stringify([state.active,state.splitView,state.orientation,state.splitOrientation,PhotoWorks.currentId()])')
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 assert page.evaluate('JSON.stringify([state.active,state.splitView,state.orientation,state.splitOrientation,PhotoWorks.currentId()])')==signature
 page.evaluate('confirmPrint()');page.wait_for_selector('#confirmSend')
 assert '左幅：照片 1 · 右幅：照片 2' in page.locator('#sheetBody').inner_text()
 page.evaluate('closeSheet()')
 # Portable works preserve both half orientations and the view rotation.
 page.evaluate("setPaperOrientation('landscape')")
 encoded=page.evaluate('ProjectFile.encode()')
 import json
 editing=json.loads(encoded)['editing']
 assert editing['splitView']=='landscape'
 assert [p['work']['layout']['splitOrientation'] for p in editing['photos'][:2]]==['portrait','landscape']
 restored=page.evaluate('''async raw=>{const old=BrowserTransport.request;let n=0;BrowserTransport.request=async(method,blob)=>{if(method!=='upload')throw Error('Unexpected operation');const image=new Image();image.src=URL.createObjectURL(blob);await image.decode();const src='/private/photos/roundtrip-'+(++n)+'.jpg';images.set(src,image);return {src};};try{await ProjectFile.restore(raw);return JSON.parse(await ProjectFile.encode()).editing;}finally{BrowserTransport.request=old;}}''',encoded)
 assert restored['splitView']=='landscape'
 assert [p['work']['layout']['splitOrientation'] for p in restored['photos'][:2]]==['portrait','landscape']
 # No-template uses the real photo, at the same paper ratio as the template preview.
 page.evaluate("state.media=5012;PhotoWorks.select(0);PhotoFlow.apply('single');setPaperOrientation('landscape');TemplateStudio.open()")
 page.wait_for_selector('#noTemplate img')
 dims=page.locator('#noTemplate img').evaluate('(img)=>[img.naturalWidth,img.naturalHeight]')
 assert dims==[240,160],dims
 page.evaluate("active().fit='bottom';active().border=150;active().caption='';render()")
 assert page.evaluate('''async()=>{const im=new Image();im.src=await TemplateStudio.thumbnail('single');await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const g=c.getContext('2d');g.drawImage(im,0,0);return [...g.getImageData(im.width/2,im.height-3,1,1).data].every(v=>v>248);}''')
 page.evaluate("active().fit='cover';active().border=0;render()")
 assert page.evaluate('logicalSize()')==[1824,1216]
 page.evaluate("PhotoFlow.apply('booth-life-watch');render()")
 assert page.evaluate('logicalSize()')==[1824,1216]
 # Rotated half: native touchscreen dragging keeps working over several animation frames.
 page.set_viewport_size({'width':390,'height':844})
 cdp=page.context.new_cdp_session(page);cdp.send('Emulation.setTouchEmulationEnabled',{'enabled':True,'maxTouchPoints':2})
 page.evaluate("closeSheet();state.media=5014;state.splitView='portrait';state.photos.forEach(p=>{p.work.template='single';p.work.layers=[];p.work.layout.splitOrientation='portrait';p.zoom=2;p.x=p.y=0});PhotoWorks.select(0);render()")
 page.wait_for_timeout(100)
 point=page.evaluate("""()=>{const c=$('preview'),r=c.getBoundingClientRect(),f=photoFrames[1],v=CropEditor.geometry(),p=PhotoWindows.point(f,{x:f.x+f.w/2,y:f.y+f.h/2});return {x:r.left+(p.x+v.tx)*r.width/c.width,y:r.top+(p.y+v.ty)*r.height/c.height};}""")
 def touch(kind,dx=0):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind=='touchEnd' else [{'x':point['x']+dx,'y':point['y'],'id':1}]})
 touch('touchStart');page.wait_for_timeout(60);touch('touchMove',10);page.wait_for_timeout(60)
 first=page.evaluate('[state.photos[1].x,state.photos[1].y]')
 touch('touchMove',20);page.wait_for_timeout(60)
 second=page.evaluate('[state.photos[1].x,state.photos[1].y]');touch('touchEnd')
 assert first!=[0,0] and first!=second,(first,second)
 assert page.evaluate('state.photos[0].x===0&&state.photos[0].y===0')
 # Paper layers use the same rotated space and hit coordinates.
 page.evaluate("LayerEditor.create({text:'ROTATED',color:'#ff0000',stroke:'',fx:.3,fy:.4});render()")
 assert page.evaluate("(()=>{const s=LayerEditor.space(),p=PhotoWindows.point(s,{x:s.x+s.w*.3,y:s.y+s.h*.4});return LayerEditor.hit(p.x,p.y)?.text==='ROTATED'})()")
 assert not page.locator('#desktopPaperTools').is_visible()
 # Current-half orientation remains available in the mobile paper sheet.
 page.evaluate('openPaper()')
 assert page.locator('[data-setting=splitOrientation]').count()==3
 assert page.locator('[data-setting=splitOrientation]').first.is_visible()
 assert not errors,errors
 page.screenshot(path=str(ROOT/'orientation-mobile.png'))
 page.evaluate('closeSheet()')
 page=page.context.new_page()
 page.set_viewport_size({'width':1440,'height':1000})
 page.goto('https://studio.local/')
 page.evaluate('Promise.all([LayerEditor.ready,BoothTemplates.ready,NameLabels.ready,CardArt.ready])')
 page.wait_for_function('state.photos.length>0&&ready()')
 page.evaluate("state.photos.forEach(p=>{p.zoom=1;p.x=p.y=0;p.work.layers=[]});PhotoWorks.select(0);PhotoFlow.apply('booth-life-watch');PhotoWorks.select(1);PhotoFlow.apply('booth-fun-volcano');state.splitView='landscape';render()")
 page.wait_for_function("document.body.classList.contains('desktop-editor')")
 page.wait_for_timeout(500)
 page.screenshot(path=str(ROOT/'orientation-desktop.png'))
 browser.close()
 print('PASS independent orientation, native rotated crop, frame/layer coordinates, physical view invariance, desktop controls, mobile controls and real no-template preview; no printing')
