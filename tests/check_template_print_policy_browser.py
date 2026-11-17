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
 # The batch is either all plain works, or only template owners, never their plain sources.
 page.evaluate("PhotoWorks.select(0);state.media=5012;state.photos.forEach(p=>p.work.template='single');PhotoWorks.activate();render()")
 assert page.evaluate('PhotoWorks.printableIndices()')==[0,1,2,3,4,5]
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==6
 page.evaluate("PhotoWorks.select(0);PhotoFlow.apply('booth-life-teatime');PhotoWorks.select(3);PhotoFlow.apply('booth-life-watch');render()")
 assert page.evaluate('PhotoWorks.printableIndices()')==[0,3]
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==2
 assert page.evaluate('preparePrintPages([0,1,2,3,4,5]).then(p=>p.length)')==2
 assert page.evaluate('preparePrintPages([1]).then(p=>p.length)')==0
 page.evaluate('confirmPrint()');page.wait_for_selector('#confirmSend')
 assert page.evaluate('pendingPrint.workIndices')==[0,3]
 assert '无模板照片仅作为素材' in page.locator('#sheetBody').inner_text()
 page.locator('#choosePrintWorks').click()
 assert page.locator('[data-print-work]').count()==2
 assert page.locator('[data-print-work="1"]').count()==0
 # An incomplete template never falls back to printing its plain source photographs.
 page.evaluate("closeSheet();state.photos.forEach(p=>p.work.template='single');PhotoWorks.select(5);PhotoFlow.apply('booth-life-teatime');render()")
 assert page.evaluate('PhotoWorks.candidateIndices()')==[5]
 assert page.evaluate('PhotoWorks.printableIndices()')==[]
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==0
 page.evaluate('confirmPrint()');page.wait_for_selector('#confirmWorkBatch')
 assert page.locator('[data-print-work]').count()==1 and page.locator('[data-print-work]').is_disabled()
 # A source with its own template remains an independent printed work even when also used in another.
 page.evaluate("closeSheet();PhotoWorks.select(5);PhotoFlow.apply('single');PhotoWorks.select(0);PhotoFlow.apply('booth-life-teatime');PhotoWorks.select(1);PhotoFlow.apply('booth-life-watch');render()")
 assert page.evaluate('PhotoWorks.printableIndices()')==[0,1]
 page.evaluate("PhotoWorks.select(0);PhotoFlow.apply('single');PhotoWorks.select(1);PhotoFlow.apply('single');render()")
 assert page.evaluate('PhotoWorks.printableIndices()')==[0,1,2,3,4,5]
 # Basic multi-photo arrangements count as templates; ordinary photo edits alone do not.
 page.evaluate("PhotoWorks.select(2);PhotoFlow.apply('grid4');render()")
 assert page.evaluate('PhotoWorks.printableIndices()')==[2]
 page.evaluate("PhotoFlow.apply('single');active().filter='sepia';render()")
 assert page.evaluate('PhotoWorks.printableIndices().length')==6
 assert not errors,errors
 browser.close()
 print('PASS plain-all / mixed-template-only batch policy, explicit selections, preview/list consistency, incomplete templates and source owners; no actual printing')
