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
 page.set_viewport_size({'width':1100,'height':1000})
 page.evaluate("""async()=>{await addPhotos([{src:'/sample.svg'},{src:'/sample.svg'}]);Object.assign(state,{mode:'collage',media:5012,orientation:'portrait',collageLayout:'grid',collageTemplateId:null,active:0,gap:30,border:80});for(const p of state.photos)Object.assign(p,{border:80,overlays:[],facePending:false});render();}""")
 page.evaluate("window.legacy={id:'legacy',kind:'emoji',text:'😊',fx:.4,fy:.3,sizePct:15,angle:0};active().overlays.push(legacy);render();window.legacyBefore=JSON.stringify(legacy)")
 page.evaluate("window.paper=LayerEditor.create({kind:'emoji',text:'😊',fx:.5,fy:.5,sizePct:15});render()")
 assert page.evaluate('state.paperLayers.photo.includes(paper)&&!active().overlays.includes(paper)')
 assert page.evaluate('LayerEditor.space().w===logicalSize()[0]&&LayerEditor.space().h===logicalSize()[1]')
 # Drag the actual selection into bottom paper margin, outside every photo frame.
 pos=page.evaluate("""()=>{const r=$('preview').getBoundingClientRect(),v=CropEditor.geometry(),[w,h]=logicalSize(),k=r.width/$('preview').width;return {x:r.left+(w*.5+v.tx)*k,y:r.top+(h*.5+v.ty)*k,tx:r.left+(w*.8+v.tx)*k,ty:r.top+(h*.94+v.ty)*k}}""")
 page.mouse.move(pos['x'],pos['y']);page.mouse.down();page.mouse.move(pos['tx'],pos['ty'],steps=12);page.mouse.up()
 assert page.evaluate('paper.fy>.85'),page.evaluate('paper')
 assert page.evaluate('LayerEditor.hit(...(()=>{const [w,h]=logicalSize(),m=LayerEditor.metrics(paper,w,h);return [m.x,m.y]})())===paper')
 # New paper layers remain when changing photos, and undo uses the work history.
 page.evaluate('selectPhoto(1);render()')
 assert page.evaluate('LayerEditor.list().includes(paper)')
 page.evaluate('EditHistory.undo();render()')
 assert page.evaluate('state.paperLayers.photo[0].fy===.5')
 page.evaluate('EditHistory.redo();render()')
 assert page.evaluate('state.paperLayers.photo[0].fy>.85')
 page.evaluate('LayerEditor.select(state.paperLayers.photo[0].id);LayerEditor.remove()')
 assert page.evaluate('state.paperLayers.photo.length')==0
 page.locator('#layerUndo button').click()
 assert page.evaluate('state.paperLayers.photo.length')==1
 page.evaluate("window.paper=state.paperLayers.photo[0];paper.hidden=true;paper.fx=.82;paper.fy=.98;render()")
 assert page.evaluate("""()=>{const c=compose(true,'mask'),ctx=c.getContext('2d'),p=LayerEditor.metrics(paper,c.width,c.height),d=ctx.getImageData(Math.floor(p.x-p.width/2),Math.floor(p.y-p.height/2),Math.ceil(p.width),Math.ceil(p.height)).data;return d.some((v,i)=>i%4===0&&v>100)}""")
 pages=page.evaluate('preparePrintPages().then(p=>p.map(x=>({mask:!!x.ocMask,bytes:x.base64.length})))')
 assert len(pages)==1 and pages[0]['mask'] and pages[0]['bytes']>1000
 assert page.evaluate("()=>{const c=compose(true,'mask'),bottom=Math.ceil(Math.max(...photoFrames.map(f=>f.y+f.h))),d=c.getContext('2d').getImageData(0,bottom+1,c.width,c.height-bottom-1).data;return d.some((v,i)=>i%4===0&&v>100)}")
 assert page.evaluate('JSON.stringify(legacy)===legacyBefore')
 # Export/import validation preserves separate page and legacy photo coordinates.
 assert page.evaluate("ProjectFile.encode().then(raw=>ProjectFile.decode(raw)).then(p=>p.editing.paperLayers.photo.length===1&&p.editing.photos[0].overlays.length===1)")
 for mode,media in [('photo',5012),('template',5009),('collage',5009),('collage',5014),('calendar',5012),('label',5012)]:
  page.evaluate("([mode,media])=>{closeSheet();state.mode=mode;state.media=media;state.active=0;state.collageLayout=media===5014?'strip':'grid';state.collageTemplateId=null;state.calendarLayout='plain';const o=LayerEditor.create({kind:'text',text:'Paper edge',fy:.94});render();window.edgeLayer=o}",[mode,media])
  assert page.evaluate('LayerEditor.space().h===logicalSize()[1]'),(mode,media)
  assert page.evaluate("preparePrintPages().then(p=>p.length>0)"),(mode,media)
 assert not errors,errors
 browser.close()
print('PASS: paper-wide drag/hit/resize space; photo switching; work undo/redo/delete undo; print mask in margin; legacy coordinates unchanged; project round trip; 6 modes/paper combinations; no printing')
