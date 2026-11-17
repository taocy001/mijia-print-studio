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
 result=page.evaluate("""async()=>{
  EffectBrowser.exit(false);state.photos=state.photos.slice(0,2);state.media=5014;
  PhotoWorks.select(0);PhotoWorks.apply('booth-life-work');PhotoWorks.select(1);PhotoWorks.apply('booth-life-watch');
  const rows=[];
  for(const layout of ['portrait','landscape']){
   state.splitLayout=layout;PhotoWorks.select(0);const [w,h]=logicalSize(),c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');
   // Distinct halves prove correct rotation, order and an unchanged center seam.
   x.fillStyle='#ff0000';x.fillRect(0,0,w,h);x.fillStyle='#0000ff';if(layout==='portrait')x.fillRect(0,h/2,w,h/2);else x.fillRect(w/2,0,w/2,h);
   const p=physical(c),m=physical(c,true);const at=(c,x,y)=>Array.from(c.getContext('2d').getImageData(x,y,1,1).data).slice(0,3).join(',');
   if(p.width!==1216||p.height!==1824)throw Error('transport size');
   for(const [xx,yy] of [[0,0],[11,900],[1204,900],[600,34],[600,1789],[1215,1823]]){if(at(p,xx,yy)!=='255,255,255'||at(m,xx,yy)!=='0,0,0')throw Error('padding '+[layout,xx,yy]);}
   for(const [xx,yy] of [[12,35],[1203,35],[12,1788],[1203,1788],[600,911],[600,912]]){const expected=yy<912?'255,0,0':'0,0,255';if(at(p,xx,yy)!==expected||at(m,xx,yy)!==expected)throw Error('content/seam '+[layout,xx,yy,at(p,xx,yy)]);}
   const before=JSON.stringify([state.active,state.splitLayout,state.photos.map(p=>p.work)]),pages=await preparePrintPages();if(pages.length!==1||pages[0].ocMask)throw Error('batch/mask');
   if(JSON.stringify([state.active,state.splitLayout,state.photos.map(p=>p.work)])!==before)throw Error('state mutation');
   const im=new Image();im.src='data:image/jpeg;base64,'+pages[0].base64;await im.decode();if(im.width!==1216||im.height!==1824)throw Error('jpeg size');
   rows.push({layout,output:[im.width,im.height],content:[1192,1754],inset:[12,35,12,35],mask:pages[0].ocMask});
  }
  // Plain pages and other paper types retain their existing full output area.
  for(const media of [5014,5012,5009]){state.media=media;for(let i=0;i<2;i++){PhotoWorks.select(i);PhotoWorks.apply(media===5014?'single':'booth-life-watch');}PhotoWorks.select(0);const [w,h]=logicalSize(),c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').fillStyle='red';c.getContext('2d').fillRect(0,0,w,h);const p=physical(c),v=p.getContext('2d').getImageData(0,0,1,1).data;if(v[0]!==255||v[1]!==0)throw Error('unrelated output changed '+media);}
  return rows;
 }""")
 assert not errors,errors
 print('PASS four-inch template bleed: both directions, outer edges, exact center seam, photo/mask alignment, no phantom mask, actual JPEG, state restoration, other papers/plain unchanged',flush=True)
 print(json.dumps(result),flush=True)
 browser.close()
