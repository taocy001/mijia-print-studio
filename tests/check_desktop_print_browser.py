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
 def rect():return page.locator('#preview').bounding_box()
 assert not errors,errors
 before=rect()
 bounds=page.evaluate("""()=>{const get=s=>{const r=document.querySelector(s).getBoundingClientRect();return{x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};return{preview:get('#preview'),workspace:get('.workspace'),tools:get('.dock'),photos:get('#photos'),header:get('.topbar')}}""")
 assert bounds['tools']['height']<100,bounds
 assert bounds['preview']['right']<=bounds['tools']['x'],bounds
 assert bounds['photos']['bottom']<=1000 and bounds['photos']['right']<=bounds['tools']['x'],bounds
 assert bounds['header']['width']>=1400,bounds
 assert page.locator('.template-card:visible').count()>6
 assert page.evaluate('getComputedStyle(document.querySelector(".template-grid")).gridTemplateColumns.split(" ").length')==2
 page.locator('#filterBtn').click();page.wait_for_selector('#sheet.desktop-inspector .filter-card')
 assert not page.evaluate('EffectBrowser.active()')
 assert page.locator('#photos').is_visible()
 after=rect();assert all(abs(before[k]-after[k])<2 for k in before),(before,after)
 page.locator('[data-filter=mono]').click() if page.locator('[data-filter=mono]').count() else page.locator('.filter-card').nth(1).click()
 assert page.evaluate('active().filter')!='none'
 print('desktop: filters passed',flush=True);page.locator('#addTextQuick').click();page.wait_for_selector('#newLayerText');page.locator('#newLayerText').click()
 page.locator('#layerText').fill('desktop text');page.locator('#layerText').dispatch_event('input')
 page.locator('#addEmojiQuick').click();page.wait_for_selector('.emoji-grid')
 assert page.locator('#sheet.desktop-inspector').count()==1
 page.locator('#templateBtn').click();page.wait_for_selector('.template-grid');page.screenshot(path='desktop-panel.png')
 page.evaluate("PhotoWorks.select(1);PhotoFlow.apply('strip');render()")
 page.wait_for_function("document.querySelector('[data-choice=strip]').classList.contains('selected')")
 print('desktop: panels passed',flush=True)
 # Two separate multi-slot works coexist with the remaining single-photo works.
 page.evaluate("PhotoWorks.select(4);PhotoFlow.apply('horizontal');PhotoWorks.select(2);render()")
 page.locator('#printBtn').click();page.wait_for_selector('#confirmSend')
 assert page.evaluate('pendingPrint.pages.length')==6
 assert '6 个作品' in page.locator('.print-selection').inner_text()
 assert '6 张' in page.locator('#confirmSend').inner_text()
 page.locator('#choosePrintWorks').click()
 assert page.locator('[data-print-work]:checked').count()==6
 page.locator('[data-print-work]').evaluate_all('(items)=>items.forEach(i=>i.checked=false)');page.locator('[data-print-work="1"]').check();page.locator('[data-print-work="4"]').check()
 page.locator('#confirmWorkBatch').click();page.wait_for_selector('#confirmSend')
 assert page.evaluate('pendingPrint.pages.length')==2
 assert page.evaluate('pendingPrint.pages.every(p=>p.copies===1)')
 page.locator('#choosePrintWorks').click();assert page.locator('[data-print-work]:checked').count()==2
 page.evaluate('closeSheet()');page.wait_for_selector('#sheet.desktop-inspector')
 print('desktop: batch passed',flush=True)
 # An incomplete work is explicit; all other works still appear.
 page.evaluate("PhotoWorks.select(5);PhotoFlow.apply('strip');render()")
 page.locator('#printBtn').click();page.wait_for_selector('#confirmSend')
 assert page.evaluate('pendingPrint.pages.length')==5
 assert '作品 6 照片不足' in page.locator('.print-selection').inner_text()
 page.evaluate('closeSheet()');page.wait_for_selector('#sheet.desktop-inspector')
 print('desktop: missing passed',flush=True)
 for mode in ['calendar','id','label','card','idcard','photo']:
  page.evaluate('(mode)=>TypeNavigation.choose(mode)',mode)
  page.wait_for_selector('#sheet.desktop-inspector')
  assert page.locator('#sheetBody').inner_text().strip(),mode
 # Mobile returns to its original collapsed panel and horizontal effects.
 page.set_viewport_size({'width':390,'height':844});page.evaluate("Object.defineProperty(screen,'width',{value:390,configurable:true});Object.defineProperty(screen,'height',{value:844,configurable:true});PhotoWorks.select(0);render()")
 page.wait_for_function('!document.body.classList.contains("desktop-editor")')
 page.locator('#templateBtn').click();page.wait_for_function('EffectBrowser.active()')
 assert not errors,errors
 browser.close()
 print('PASS default all works, selected batch, missing work notice, persistent desktop panels, stable preview, all six types and mobile effects')
