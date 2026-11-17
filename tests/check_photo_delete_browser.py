"""Verify photo deletion updates the editor and saved draft, without printing."""
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
 # Delete all photos through actual buttons, including the last one.
 page.evaluate("PhotoWorks.select(0);state.photos.forEach(p=>p.work.template='single');PhotoWorks.activate();render();save()")
 for remaining in range(5,-1,-1):
  page.locator('[data-remove-photo="0"]').click()
  page.wait_for_function('(n)=>state.photos.length===n',arg=remaining)
  page.wait_for_function('(n)=>document.querySelectorAll("[data-photo]").length===n',arg=remaining,timeout=3000)
  assert page.evaluate('JSON.parse(localStorage.getItem(window.STUDIO_DRAFT_KEY||"liuying-draft")).photos.length')==remaining
 assert page.locator('#printBtn').is_disabled()
 assert page.locator('#preview').is_visible()
 assert page.evaluate('emptyPhotoFrames.length')>0
 # Undo restores the same photo, then deleting it and reloading keeps the empty draft.
 page.locator('#photoUndo button').click()
 page.wait_for_function('state.photos.length===1&&document.querySelectorAll("[data-photo]").length===1')
 page.locator('[data-remove-photo="0"]').click()
 page.wait_for_function('document.querySelectorAll("[data-photo]").length===0')
 page.reload()
 page.evaluate('Promise.all([LayerEditor.ready,BoothTemplates.ready,NameLabels.ready,CardArt.ready])')
 assert page.evaluate('state.photos.length')==0
 # Last templated photo: retain an empty template preview and allow undo/add again.
 page.evaluate("addPhotos([{src:'/sample.svg'}])")
 page.wait_for_function('state.photos.length===1&&ready()')
 page.evaluate("PhotoFlow.apply('booth-life-watch')")
 page.wait_for_function('PhotoWorks.currentId()==="booth-life-watch"')
 page.locator('[data-remove-photo="0"]').click()
 page.wait_for_function('document.querySelectorAll("[data-photo]").length===0')
 assert page.evaluate('PhotoWorks.currentId()')=='booth-life-watch'
 assert page.locator('#printBtn').is_disabled()
 page.locator('#photoUndo button').click()
 page.wait_for_function('state.photos.length===1&&document.querySelectorAll("[data-photo]").length===1')
 assert page.evaluate('PhotoWorks.currentId()')=='booth-life-watch'
 page.locator('[data-remove-photo="0"]').click()
 page.wait_for_function('document.querySelectorAll("[data-photo]").length===0')
 page.evaluate("addPhotos([{src:'/sample.svg'}])")
 page.wait_for_function('state.photos.length===1&&ready()')
 assert page.evaluate('PhotoWorks.currentId()')=='booth-life-watch'
 assert not errors,errors
 browser.close()
 print('PASS actual delete clicks, last plain/template photo, draft persistence, undo, reload and add again; no printing')
