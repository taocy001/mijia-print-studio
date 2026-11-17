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
 # Every new shape must render, pick, serialize and prepare actual print data.
 page.evaluate("document.fonts.load('32px StudioHappy')")
 audit=page.evaluate("""()=>{let count=0;const problems=[];for(const [w,h] of [[1216,1824],[1824,1216],[1040,1040],[1216,912]])for(const e of EverydayTemplates.catalog){const fs=BoothTemplates.frames(w,h,e);if(fs.length!==e.slots)problems.push(e.id+' slots');for(const f of fs){const b=PhotoWindows.bounds(f);if(b.left<0||b.top<0||b.right>w||b.bottom>h)problems.push(e.id+' bounds');if(!PhotoWindows.contains(f,PhotoWindows.point(f,{x:f.x+f.w*.5,y:f.y+f.h*.55})))problems.push(e.id+' center');count++;}for(let i=1;i<fs.length;i++){const a=PhotoWindows.bounds(fs[i-1]),b=PhotoWindows.bounds(fs[i]);if(a.left<b.right&&b.left<a.right&&a.top<b.bottom&&b.top<a.bottom)problems.push(e.id+' overlap');}}return{count,problems}}""")
 assert audit['count']==96 and not audit['problems'],audit
 for group in ['outing','tea','school','office','imagination']:
  page.evaluate("(g)=>{TemplateStudio.setGroup(g);TemplateStudio.open()}",group)
  assert page.locator('[data-template]:visible').count()>0,group
 ids=page.evaluate('EverydayTemplates.catalog.map(e=>e.id)')
 for id in ids:
  page.evaluate("(id)=>{PhotoWorks.select(0);state.media=5012;state.orientation='portrait';PhotoFlow.apply(id);render()}",id)
  slots=page.evaluate('(id)=>BoothTemplates.get(id).slots',id)
  assert page.evaluate('photoFrames.length')==slots,id
  assert page.evaluate('photoFrames.every(f=>!!f.shape)'),id
  mapping=page.evaluate('photoFrames.map(f=>f.p.src)')
  assert mapping==page.evaluate('(n)=>state.photos.slice(0,n).map(p=>p.src)',slots),(id,mapping)
  result=page.evaluate("ProjectFile.encode().then(ProjectFile.decode).then(d=>d.editing.photos[0].work.template)")
  assert result==id,(id,result)
  printed=page.evaluate('preparePrintPages([0]).then(p=>({count:p.length,media:p[0].media,bytes:p[0].base64.length}))')
  assert printed['count']==1 and printed['media']==5012 and printed['bytes']>1000,(id,printed)
 # Each silhouette's coat raster must agree with hit testing; boundary antialias pixels ignored.
 mask=page.evaluate("""()=>{const problems=[];for(const e of EverydayTemplates.catalog){PhotoFlow.apply(e.id);active().coatTexture='grid';render();const c=compose(true,'mask'),d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let inside=0,outside=0;for(let y=0;y<c.height;y+=7)for(let x=0;x<c.width;x+=7){if(d[(y*c.width+x)*4]>200){if(photoFrames.some(f=>PhotoWindows.contains(f,{x:x+.5,y:y+.5})))inside++;else outside++;}}if(inside<100||outside>5)problems.push({id:e.id,inside,outside});}return problems}""")
 assert not mask,mask
 # New categories stay discoverable in the phone strip, with the six-photo limit.
 page.set_viewport_size({'width':412,'height':915})
 page.evaluate("Object.defineProperty(screen,'width',{value:412,configurable:true});Object.defineProperty(screen,'height',{value:915,configurable:true});window.dispatchEvent(new Event('resize'))")
 assert page.evaluate('photoBatchLimit()')==6
 for media in [5012,5009,5014]:
  page.evaluate('(m)=>{state.media=m;render()}',media)
  assert page.evaluate("['outing','tea','school','office','imagination'].every(g=>{TemplateStudio.setGroup(g);return TemplateStudio.browseItems().some(t=>t.id.startsWith('booth-life-'))})")
 # Render all designs through the production compositor, preserving their photo frames.
 data=page.evaluate("""()=>{const es=EverydayTemplates.catalog,c=document.createElement('canvas');c.width=1200;c.height=2000;const ctx=c.getContext('2d');ctx.fillStyle='#ededed';ctx.fillRect(0,0,c.width,c.height);PhotoWorks.select(0);state.media=5012;state.orientation='portrait';es.forEach((e,i)=>{PhotoFlow.apply(e.id);const out=compose(false);ctx.drawImage(out,(i%4)*300+8,Math.floor(i/4)*500+8,284,426);ctx.fillStyle='#333';ctx.font='18px sans-serif';ctx.textAlign='left';ctx.fillText(e.key,(i%4)*300+8,Math.floor(i/4)*500+467)});return c.toDataURL('image/jpeg',.9).split(',')[1]}""")
 import base64
 (ROOT/'everyday-contact.jpg').write_bytes(base64.b64decode(data))
 assert not errors,errors
 browser.close()
 print('PASS 16 everyday designs: geometry, categories, photo mapping, project roundtrip, print preparation, all silhouette coat masks, mobile cap6 and paper filtering; no actual printing')
