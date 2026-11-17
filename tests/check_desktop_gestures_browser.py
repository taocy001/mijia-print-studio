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
 # A modeless inspector must leave the big preview usable.
 point=page.evaluate("""()=>{const f=photoFrames[0],r=$('preview').getBoundingClientRect(),v=CropEditor.geometry();return{x:r.left+(f.x+f.w/2+v.tx)*r.width/$('preview').width,y:r.top+(f.y+f.h/2+v.ty)*r.height/$('preview').height}}""")
 page.mouse.move(**point);page.mouse.down();page.wait_for_timeout(600)
 assert page.evaluate('OriginalPreview.active()');page.mouse.up();assert not page.evaluate('OriginalPreview.active()')
 page.evaluate("PhotoWorks.select(5);PhotoFlow.apply('strip');render()")
 page.wait_for_timeout(150)
 point=page.evaluate("""()=>{const f=emptyPhotoFrames[0],r=$('preview').getBoundingClientRect(),v=CropEditor.geometry();return{x:r.left+(f.x+f.w/2+v.tx)*r.width/$('preview').width,y:r.top+(f.y+f.h/2+v.ty)*r.height/$('preview').height}}""")
 page.mouse.click(**point);assert page.evaluate('(window.picks||[]).length')==1
 page.evaluate("state.photos[0].caption='first';state.photos[1].caption='second';PhotoWorks.select(0);render();openLegacyText()")
 page.wait_for_selector('#captionInput');assert page.locator('#captionInput').input_value()=='first'
 page.locator('[data-photo="1"]').click();page.wait_for_function("document.getElementById('captionInput')?.value==='second'")
 page.locator('#addTextQuick').click();page.wait_for_selector('#newLayerText')
 assert page.locator('#addTextQuick').get_attribute('aria-pressed')=='true'
 page.locator('[data-photo="2"]').click();page.wait_for_selector('#newLayerText')
 page.locator('#addEmojiQuick').click();page.wait_for_selector('.emoji-grid')
 page.locator('[data-photo="3"]').click();page.wait_for_selector('.emoji-grid')
 assert page.locator('#addEmojiQuick').get_attribute('aria-pressed')=='true'
 page.evaluate("LayerEditor.create({kind:'text',text:'test'});render()")
 page.locator('#filterBtn').click();page.wait_for_selector('.filter-grid');assert page.evaluate('LayerEditor.selected()||null') is None
 assert not errors,errors
 browser.close()
 print('PASS desktop original hold, empty-slot pick, caption ownership, text/emoji persistence and selection clearing')
