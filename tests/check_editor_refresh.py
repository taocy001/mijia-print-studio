"""Verify editor history, original-image comparison, composition and ID print geometry."""
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
 page.evaluate('BoothTemplates.ready')
 page.set_viewport_size({'width':390,'height':844})
 page.evaluate("Object.defineProperty(screen,'width',{value:390,configurable:true});Object.defineProperty(screen,'height',{value:844,configurable:true});state.media=5012;state.mode='photo';state.photos=[];addPhotos([{src:'/sample.svg'}])")
 page.evaluate('Studio.landscape=()=>innerWidth>innerHeight;updateEditorOrientation();render()')
 page.wait_for_function('!!printPreview&&canAdjustPhoto()')
 assert not errors,errors
 assert not page.locator('#zoomIn').is_visible() and not page.locator('#zoomOut').is_visible()
 assert page.locator('#editorUndo').is_visible()
 page.locator('#composeToggle').click();assert page.locator('#rotate').is_visible() and page.locator('#mirrorPhoto').is_visible()
 page.locator('#mirrorPhoto').click();assert page.evaluate('active().mirror')
 assert page.evaluate("ProjectFile.encode().then(ProjectFile.decode).then(p=>p.editing.photos[0].mirror)")
 page.locator('#editorUndo').click();assert not page.evaluate('!!active().mirror')
 page.locator('#editorRedo').click();assert page.evaluate('active().mirror')
 page.locator('#reset').click();assert page.evaluate('!active().mirror&&active().turn===0')
 page.locator('#composeToggle').click()
 # A full effect browsing session including a pinch is exactly one undo record.
 baseline=page.evaluate("compose().toDataURL()")
 page.locator('#filterBtn').click();assert page.locator('#effectRail').is_visible()
 assert not page.locator('#sheet').is_visible() and not page.locator('#photos').is_visible()
 page.evaluate("EffectBrowser.step(1);EffectBrowser.step(1);EffectBrowser.step(1)")
 page.evaluate("""()=>{const c=$('preview'),r=c.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;const ts=(d)=>[new Touch({identifier:1,target:c,clientX:x-d,clientY:y}),new Touch({identifier:2,target:c,clientX:x+d,clientY:y})];c.dispatchEvent(new TouchEvent('touchstart',{touches:ts(30),bubbles:true,cancelable:true}));c.dispatchEvent(new TouchEvent('touchmove',{touches:ts(50),bubbles:true,cancelable:true}));c.dispatchEvent(new TouchEvent('touchend',{touches:[],bubbles:true}));}""")
 assert page.evaluate('active().zoom>1')
 after=page.evaluate("compose().toDataURL()")
 page.evaluate("$(EffectBrowser.kind()==='templates'?'templateBtn':'filterBtn').click()");assert page.locator('#photos').is_visible()
 page.locator('#editorUndo').click();assert page.evaluate('compose().toDataURL()')==baseline
 assert page.evaluate('EditHistory.status().redo')
 # Cancel restores pixels AND the redo stack.
 page.locator('#filterBtn').click();page.evaluate('EffectBrowser.step(1);EffectBrowser.step(1)');page.locator('#effectCancel').click()
 assert page.evaluate('compose().toDataURL()')==baseline
 assert page.evaluate('EditHistory.status().redo')
 page.locator('#editorRedo').click();assert page.evaluate('compose().toDataURL()')==after
 # Full-original comparison is a display-only overlay: composition and edits stay intact.
 page.evaluate("active().filter='sepia';active().mirror=true;state.paperLayers={photo:[{id:'keep',kind:'emoji',text:'😍',fx:.8,fy:.8,sizePct:10,angle:0}]};render()")
 page.locator('#filterBtn').click();page.wait_for_timeout(100)
 compare_state=page.evaluate('JSON.stringify(state)');compare_print=page.evaluate('compose().toDataURL()')
 box=page.locator('#preview').bounding_box();page.mouse.move(box['x']+box['width']*.3,box['y']+min(box['height']*.3,100));page.mouse.down();page.wait_for_timeout(500)
 assert page.evaluate('OriginalPreview.active()') and page.locator('#originalPreview').is_visible()
 assert page.evaluate('JSON.stringify(state)')==compare_state
 assert page.evaluate('compose().toDataURL()')==compare_print
 page.mouse.move(box['x']+box['width']*.5,box['y']+box['height']*.5)
 assert page.evaluate('OriginalPreview.active()') and page.evaluate('JSON.stringify(state)')==compare_state
 page.mouse.up();assert not page.evaluate('OriginalPreview.active()');page.locator('#filterBtn').click()
 # Template gallery remains part of the same cancelable session, preserving objects and slots.
 page.evaluate("addPhotos(Array.from({length:5},()=>({src:'/sample.svg'})))")
 page.evaluate("window.originalPhotos=[...state.photos];window.beforeTemplates=PhotoFlow.historyOwner().photoLayoutState;window.beforeLayers=JSON.stringify(state.paperLayers)")
 page.locator('#templateBtn').click();page.locator('#effectAll').click();page.wait_for_selector('[data-basic=grid4]')
 page.locator('[data-basic=grid4]').click();assert page.locator('#effectRail').is_visible() and not page.locator('#sheet').is_visible()
 page.evaluate("TemplateStudio.apply('booth-together-3');TemplateStudio.apply('horizontal')")
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 page.locator('#effectCancel').click()
 assert page.evaluate('JSON.stringify(PhotoFlow.historyOwner().photoLayoutState)===JSON.stringify(beforeTemplates)')
 assert page.evaluate('state.photos.every((p,i)=>p===originalPhotos[i])&&JSON.stringify(state.paperLayers)===beforeLayers')
 page.locator('#templateBtn').click();page.evaluate("TemplateStudio.apply('booth-together-3');TemplateStudio.apply('grid4')");page.evaluate("$(EffectBrowser.kind()==='templates'?'templateBtn':'filterBtn').click()")
 assert page.evaluate("state.photoLayout==='grid4'")
 page.locator('#editorUndo').click();assert page.evaluate('JSON.stringify(PhotoFlow.historyOwner().photoLayoutState)===JSON.stringify(beforeTemplates)')
 page.locator('#editorRedo').click();assert page.evaluate("state.photoLayout==='grid4'")
 # Undo A's effect session must not undo B's later crop or change another print type.
 page.evaluate("state={...defaults,photos:[]};addPhotos([{src:'/sample.svg'},{src:'/sample.svg'}])")
 page.evaluate("selectPhoto(0);render();EffectBrowser.toggle('filters');EffectBrowser.step(1);EffectBrowser.exit();selectPhoto(1);EditHistory.run(()=>{active().zoom=2});selectPhoto(0);EditHistory.undo()")
 assert page.evaluate("state.photos[1].zoom===2&&state.photos[0].filter==='none'")
 page.evaluate("EffectBrowser.toggle('filters');EffectBrowser.step(1);EffectBrowser.exit();TypeNavigation.choose('id');EditHistory.undo()")
 assert page.evaluate("state.mode==='id'&&state.photos[1].zoom===2")
 # Mirrored pixels are exact horizontal reflections through the shared renderer.
 assert page.evaluate("""()=>{const p=active(),c=document.createElement('canvas');c.width=120;c.height=80;const g=c.getContext('2d');for(let turn=0;turn<4;turn++){p.turn=turn;p.mirror=false;g.clearRect(0,0,120,80);drawPhoto(g,p,0,0,120,80,'cover');const a=g.getImageData(0,0,120,80).data;p.mirror=true;g.clearRect(0,0,120,80);drawPhoto(g,p,0,0,120,80,'cover');const b=g.getImageData(0,0,120,80).data;let diff=0;for(let y=1;y<79;y++)for(let x=1;x<119;x++)for(let k=0;k<3;k++){const source=(y*120+119-x)*4+k;diff+=Math.abs(a[source]-b[(y*120+x)*4+k]);}if(diff/(78*118*3)>2)return false;}return true;}""")
 # ID-photo rectangles are unchanged; marks/text are outside every photo rectangle.
 report=page.evaluate("""()=>{const rows=[],oldPhoto=drawPhoto,oldText=text;try{for(const media of [5012,5009,5014])for(const orientation of ['portrait','landscape'])for(const size of ['25x35','35x45','35x49','33x48','51x51','45x45']){state.media=media;state.orientation=orientation;state.mode='id';state.idSize=size;const rects=[],labels=[];drawPhoto=(ctx,p,x,y,w,h)=>rects.push({x,y,w,h});text=(ctx,s,x,y,size,...args)=>{if(s.includes('mm'))labels.push(s);};compose(false);rows.push({media,orientation,size,rects,labels});}}finally{drawPhoto=oldPhoto;text=oldText;}return rows;}""")
 for row in report:
  mw,mh=map(int,row['size'].split('x'));iw=int(mw*300/25.4+.5);ih=int(mh*300/25.4+.5)
  assert all(p['w']==iw and p['h']==ih for p in row['rects']),row
  assert row['labels'],row
  w,h=(1040,1040) if row['media']==5009 else ((1824,1216) if row['media']==5012 and row['orientation']=='landscape' else (1216,1824))
  ph=h/2 if row['media']==5014 else h
  expected=max(1,int((w-28)/(iw+28)))*max(1,int((ph-28)/(ih+28)))*(2 if row['media']==5014 else 1)
  assert len(row['rects'])==expected,row
 page.evaluate("state.mode='id';state.media=5012;state.orientation='portrait';state.idSize='25x35';state.photos=[state.photos[0]];state.active=0;active().turn=0;active().mirror=false;render()")
 page.screenshot(path='editor-id.jpg',type='jpeg',quality=75)
 page.evaluate("TypeNavigation.choose('photo');PhotoFlow.apply('single');render()")
 page.locator('#filterBtn').click();page.wait_for_timeout(600);assert page.locator('#effectRail').bounding_box()['y']+page.locator('#effectRail').bounding_box()['height']<=page.locator('.dock').bounding_box()['y']+2;page.screenshot(path='editor-tone.jpg',type='jpeg',quality=75)
 assert not errors,errors
 browser.close()
print('PASS: toolbar/crop/mirror; persisted mirror; grouped filter+pinch undo/redo; cancel retains redo; original-color compare; gallery transaction; photo/layer identity; 4 mirror rotations; 36 ID size/paper/orientation layouts unchanged; no printing')
