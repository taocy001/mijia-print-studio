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
 rows=page.evaluate("""async()=>{
  EffectBrowser.exit(false);const rows=[];
  for(const media of [5012,5014,5009])for(const orientation of ['portrait','landscape'])for(const [id,fit] of [['single','cover'],['single','contain'],['single','bottom'],['polaroid','cover'],['booth-life-watch','cover'],['grid4','contain']]){
   if(media===5014&&id==='grid4')continue;
   state.media=media;state.splitLayout=orientation;
   for(let i=0;i<state.photos.length;i++){PhotoWorks.select(i);PhotoWorks.apply(id);state.photos[i].fit=fit;state.photos[i].border=fit==='bottom'?78:0;state.photos[i].facePending=false;}
   PhotoWorks.select(0);state.orientation=orientation;PhotoWorks.saveCurrent();
   const expected=media===5014?(id!=='single'||fit!=='cover'):(id==='single'||id==='polaroid')&&(media===5009||id==='polaroid'||fit!=='cover');
   const insets=expected?[12,media===5009?12:35]:[0,0];if(JSON.stringify(printBleedInsets())!==JSON.stringify(insets))throw Error('policy '+[media,orientation,id,fit]);
   const [w,h]=logicalSize(),c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.fillStyle='red';x.fillRect(0,0,w,h);
   const out=physical(c),mask=physical(c,true),[ex,ey]=insets,at=(c,x,y)=>Array.from(c.getContext('2d').getImageData(x,y,1,1).data).slice(0,3).join(',');
   if(out.width!==(media===5009?1040:1216)||out.height!==(media===5009?1040:1824))throw Error('size');
   if(at(out,ex,ey)!=='255,0,0'||at(mask,ex,ey)!=='255,0,0')throw Error('content');
   if(expected){for(const [xx,yy] of [[ex-1,ey],[ex,ey-1],[out.width-ex,ey],[ex,out.height-ey]])if(at(out,xx,yy)!=='255,255,255'||at(mask,xx,yy)!=='0,0,0')throw Error('padding');}
   else if(at(out,0,0)!=='255,0,0'||at(mask,0,0)!=='255,0,0')throw Error('exempt');
   rows.push({media,orientation,id,fit,insets});
  }
  state.media=5014;PhotoWorks.select(0);PhotoWorks.apply('single');state.photos[0].fit='cover';PhotoWorks.select(1);PhotoWorks.apply('single');state.photos[1].fit='contain';
  for(const i of [0,1]){PhotoWorks.select(i);if(JSON.stringify(printBleedInsets())!=='[12,35]')throw Error('mixed order');}
  PhotoWorks.setSplitPrintIndices([0]);if(JSON.stringify(printBleedInsets())!=='[0,0]')throw Error('nonbatch affected');PhotoWorks.setSplitPrintIndices(null);
  for(const media of [5012,5014,5009])for(const mode of ['id','idcard','calendar','label','card']){state.media=media;state.mode=mode;if(JSON.stringify(printBleedInsets())!=='[0,0]')throw Error('fixed mode scaled '+mode);}
  for(const media of [5012,5014,5009]){state.media=media;PhotoWorks.select(0);for(const p of state.photos)p.work.template='single';PhotoWorks.apply('single');state.photos[0].fit='contain';PhotoWorks.activate();const pages=await preparePrintPages([0]);if(pages.length!==1||pages[0].ocMask)throw Error('batch/mask '+media);const im=new Image();im.src='data:image/jpeg;base64,'+pages[0].base64;await im.decode();if(im.width!==(media===5009?1040:1216)||im.height!==(media===5009?1040:1824))throw Error('encoded dimensions');}
  return rows;
 }""")
 (ROOT/'paper-rules-results.json').write_text(json.dumps(rows,indent=2))
 assert not errors,errors
 print('PASS',len(rows),'paper/direction/style cases; photo/mask boundary pixels; mixed and selected batches; 15 fixed-mode exclusions; real JPEGs and no phantom OC; no printing',flush=True)
 browser.close()
