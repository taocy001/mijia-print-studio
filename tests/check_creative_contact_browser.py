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
 data=page.evaluate("""()=>{const ids=['journal-2','journal-3','purikura-4','together-1','together-2','comic-3','comic-4','magazine-1','magazine-4','studio-4','season-2','y2k-2'];const c=document.createElement('canvas');c.width=1200;c.height=1800;const ctx=c.getContext('2d');ctx.fillStyle='#ddd';ctx.fillRect(0,0,c.width,c.height);PhotoWorks.select(0);state.media=5012;for(let i=0;i<ids.length;i++){PhotoFlow.apply('booth-v2-'+ids[i]);state.orientation='portrait';const image=compose(false);ctx.drawImage(image,(i%4)*300+8,Math.floor(i/4)*600+24,284,426);ctx.fillStyle='#222';ctx.font='18px sans-serif';ctx.fillText(ids[i],(i%4)*300+8,Math.floor(i/4)*600+480);}return c.toDataURL('image/jpeg',.85).split(',')[1]}""")
 import base64
 (ROOT/'creative-contact.jpg').write_bytes(base64.b64decode(data))
 assert not errors,errors
 browser.close()
 print('PASS creative contact sheet rendered')
