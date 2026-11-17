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
 page.wait_for_selector('#sheet.desktop-inspector .template-card')
 assert not errors,errors
 # Every offered creative window fits the paper and stays large enough at print scale.
 audit=page.evaluate("""()=>{let count=0;const problems=[];for(const [w,h] of [[1216,1824],[1824,1216],[1040,1040],[1216,912]])for(const e of BoothTemplates.catalog.filter(e=>e.version===2)){if(!BoothTemplates.available(e.id,w,h))continue;for(const f of BoothTemplates.frames(w,h,e)){count++;const b=PhotoWindows.bounds(f);if(b.left<0||b.top<0||b.right>w||b.bottom>h||Math.max(f.w/f.h,f.h/f.w)>1.80001||Math.min(f.w,f.h)<310)problems.push({id:e.id,w,h,f});}}return{count,problems}}""")
 assert audit['count']>250 and not audit['problems'],audit
 assert not page.evaluate("TemplateStudio.browseItems().some(t=>t.id==='polaroid'||t.id==='strip'||t.id==='grid6'||BoothTemplates.retired(t.id))")
 assert page.locator('#polaroidTemplate').count()==0
 # Candidate direction predicts the destination, not the currently visible single-photo mode.
 page.evaluate("state.orientation='auto';PhotoFlow.apply('single');render()")
 assert not page.evaluate("TemplateStudio.offered('horizontal')")
 assert page.evaluate("TemplateStudio.offered('grid6-roomy')")
 # Paper-specific availability affects both chooser and swipe sequence.
 page.evaluate("state.media=5014;PhotoWorks.select(0);render();TemplateStudio.setGroup('journal');TemplateStudio.open()")
 page.wait_for_timeout(100)
 assert not page.evaluate("TemplateStudio.browseItems().some(t=>t.id==='booth-v2-journal-4')")
 assert page.locator('[data-template="booth-v2-journal-4"]').count()==0
 page.evaluate("state.media=5012;state.orientation='portrait';PhotoWorks.select(0);PhotoFlow.apply('booth-v2-journal-2');render()")
 # Hit and drag a rotated slot in paper coordinates; its crop stays independent.
 page.evaluate("for(const p of PhotoFlow.pagePhotos()){p.zoom=2;p.x=p.y=0;p.facePending=false;}render()")
 def point(index,fx=.5,fy=.5,empty=False):
  return page.evaluate("""([index,fx,fy,empty])=>{const f=(empty?emptyPhotoFrames:photoFrames)[index],p=PhotoWindows.point(f,{x:f.x+f.w*fx,y:f.y+f.h*fy}),r=$('preview').getBoundingClientRect(),v=CropEditor.geometry();return{x:r.left+(p.x+v.tx)*r.width/$('preview').width,y:r.top+(p.y+v.ty)*r.height/$('preview').height}}""",[index,fx,fy,empty])
 p=point(1);page.mouse.move(**p);page.mouse.down();page.mouse.move(p['x']+120,p['y'],steps=4);page.mouse.up();page.wait_for_timeout(100)
 crop=page.evaluate('({x:active().x,y:active().y,owner:state.active,raw:state.photos[1].zoom})')
 assert crop['x']>0 and crop['y']<0 and crop['owner']==0 and crop['raw']==1,crop
 page.locator('#editorUndo').click();assert abs(page.evaluate('active().x'))<.001
 page.locator('#editorRedo').click();assert page.evaluate('active().x')>0
 # A legacy slot annotation uses the same rotated coordinates as its photograph.
 layerHit=page.evaluate("""()=>{const f=photoFrames[1],o=LayerEditor.create({kind:'text',text:'HELLO',fx:.5,fy:.5,sizePct:8},f.p.overlays);const p=PhotoWindows.point(f,{x:f.x+f.w*.5,y:f.y+f.h*.5});return LayerEditor.hit(p.x,p.y)?.id===o.id}""")
 assert layerHit
 # Hit testing excludes the heart cutout and includes its interior.
 page.evaluate("PhotoWorks.select(0);PhotoFlow.apply('booth-v2-together-2');render()")
 assert page.evaluate("photoFrames.every(f=>!PhotoWindows.contains(f,PhotoWindows.point(f,{x:f.x+f.w*.03,y:f.y+f.h*.03}))&&PhotoWindows.contains(f,PhotoWindows.point(f,{x:f.x+f.w*.5,y:f.y+f.h*.5})))")
 p=point(1);page.mouse.click(**p);assert page.evaluate('PhotoWorks.focus()===state.photos[1].photoId')
 # Blank shape slots still open the picker.
 page.evaluate("PhotoWorks.select(5);PhotoFlow.apply('booth-v2-together-2');render()")
 p=point(0,empty=True);before=page.evaluate('(window.picks||[]).length');page.mouse.click(**p)
 assert page.evaluate('(window.picks||[]).length')==before+1
 # Coating follows the identical clipped and rotated window, including single-photo templates.
 mask=page.evaluate("""()=>{PhotoWorks.select(0);PhotoFlow.apply('booth-v2-together-1');active().coatTexture='grid';render();const c=compose(true,'mask'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data,f=photoFrames[0];let inside=0,outside=0;for(let y=0;y<c.height;y+=3)for(let x=0;x<c.width;x+=3){if(d[(y*c.width+x)*4]>200){if(PhotoWindows.contains(f,{x:x+.5,y:y+.5}))inside++;else outside++;}}return{inside,outside}}""")
 assert mask['inside']>100 and mask['outside']<5,mask
 # Historical IDs are not offered but can still render and round-trip through projects.
 for old in ['polaroid','booth-studio-4','strip','grid6']:
  page.evaluate('(id)=>{PhotoFlow.apply(id);render()}',old)
  assert page.evaluate('photoFrames.length')>0,old
 page.evaluate("PhotoFlow.apply('booth-v2-journal-3');render()")
 result=page.evaluate("""async()=>{const file=await ProjectFile.encode();const d=await ProjectFile.decode(file);return d.editing.photos[0].work.template}""")
 assert result=='booth-v2-journal-3',result
 printed=page.evaluate('preparePrintPages([0]).then(p=>({count:p.length,media:p[0].media,bytes:p[0].base64.length,orientation:p[0].orientation}))')
 assert printed['count']==1 and printed['media']==5012 and printed['bytes']>1000,printed
 # Contact sheet of the new families; no printer is called.
 data=page.evaluate("""()=>{const ids=['journal-2','journal-3','purikura-4','together-1','together-2','comic-3','comic-4','magazine-1','magazine-4','studio-4','season-2','y2k-2'];const c=document.createElement('canvas');c.width=1200;c.height=1800;const ctx=c.getContext('2d');ctx.fillStyle='#ddd';ctx.fillRect(0,0,c.width,c.height);PhotoWorks.select(0);state.media=5012;for(let i=0;i<ids.length;i++){PhotoFlow.apply('booth-v2-'+ids[i]);state.orientation='portrait';const image=compose(false);ctx.drawImage(image,(i%4)*300+8,Math.floor(i/4)*600+24,284,426);ctx.fillStyle='#222';ctx.font='18px sans-serif';ctx.fillText(ids[i],(i%4)*300+8,Math.floor(i/4)*600+480);}return c.toDataURL('image/jpeg',.85).split(',')[1]}""")
 import base64
 (ROOT/'creative-contact.jpg').write_bytes(base64.b64decode(data))
 assert not errors,errors
 browser.close()
 print('PASS creative geometry, retired choices, paper availability, rotated crop/hit/history, heart and blank hit, coating, old templates and project round-trip')
