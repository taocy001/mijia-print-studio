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

 import json
 result=page.evaluate("""()=>{
  EffectBrowser.exit(false);const out=[],bad=[];const ids=['single',...PhotoFlow.basics.map(t=>t.id),...TEMPLATE_CATALOG.map(t=>t.id)];
  for(const [media,orientation] of [[5012,'portrait'],[5012,'landscape'],[5009,'portrait'],[5014,'portrait'],[5014,'landscape']]){
   state.media=media;state.splitLayout=orientation;PhotoWorks.select(0);
   for(const id of [...new Set(ids)]){
    if(media===5014&&((PhotoFlow.basics.find(t=>t.id===id)?.slots||BoothTemplates.get(id)?.slots||1)>1))continue;
    PhotoWorks.apply(id);state.orientation=orientation;PhotoWorks.saveCurrent();
    photoFrames=[];emptyPhotoFrames=[];collectingPhotoFrames=true;let c;try{c=compose(true);}finally{collectingPhotoFrames=false;}
    const p=physical(c),ctx=p.getContext('2d'),back=document.createElement('canvas');back.width=c.width;back.height=c.height;const b=back.getContext('2d');
    if(media===5009){b.translate(1040,1040);b.rotate(Math.PI);}else if(c.width>c.height){b.translate(0,1216);b.rotate(-Math.PI/2);}b.drawImage(p,0,0);
    const a=c.getContext('2d').getImageData(0,0,c.width,c.height).data,z=b.getImageData(0,0,c.width,c.height).data;
    let mismatch=0;for(let k=0;k<a.length;k+=4)if(a[k]!==z[k]||a[k+1]!==z[k+1]||a[k+2]!==z[k+2]||a[k+3]!==z[k+3])mismatch++;
    const bounds=photoFrames.map(f=>PhotoWindows.bounds(f));const outside=bounds.filter(f=>f.left<-.1||f.top<-.1||f.right>c.width+.1||f.bottom>c.height+.1);
    const row={media,orientation,id,logical:[c.width,c.height],physical:[p.width,p.height],frames:bounds.length,mismatch,outside};out.push(row);if(mismatch||outside.length)bad.push(row);
   }
  }return {rows:out,bad};
 }""")
 (ROOT/'paper-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print('AUDIT',len(result['rows']),'layouts;',len(result['bad']),'geometry/pixel findings;',len(errors),'browser errors',flush=True)
 print(json.dumps(result['bad'],ensure_ascii=False),flush=True)
 assert not errors,errors
 browser.close()
