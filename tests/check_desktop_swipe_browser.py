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
 assert not page.locator('.template-categories').is_visible()
 assert page.locator('.desktop-template-category').bounding_box()['height']<=60
 page.locator('#desktopTemplateGroup').select_option('basic')
 assert page.evaluate("TemplateStudio.currentGroup()")=='basic'
 assert page.locator('#desktopTemplateGroup option').last.inner_text()=='基础排列'
 items=page.evaluate('TemplateStudio.browseItems().filter(t=>!t.disabled).map(t=>t.id)')
 page.evaluate('(id)=>TemplateStudio.apply(id)',items[0]);page.wait_for_timeout(150)
 def center():
  box=page.locator('#preview').bounding_box();page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2)
 def swipe(dx,dy=0):
  page.wait_for_timeout(300);center();page.mouse.wheel(dx,dy);page.wait_for_timeout(120)
 center();page.mouse.wheel(26,1);page.mouse.wheel(28,1);page.wait_for_timeout(120)
 assert page.evaluate('TemplateStudio.selectedId()')==items[1]
 for delta in [80,55,25,8,-60]:page.mouse.wheel(delta,1)
 page.wait_for_timeout(120);assert page.evaluate('TemplateStudio.selectedId()')==items[1], 'inertia must not skip'
 swipe(-70);assert page.evaluate('TemplateStudio.selectedId()')==items[0]
 swipe(-90);assert page.evaluate('TemplateStudio.selectedId()')==items[0], 'no wrap at first'
 swipe(0,180);assert page.evaluate('TemplateStudio.selectedId()')==items[0]
 # A vertical-start gesture stays vertical when a horizontal tail arrives.
 page.mouse.wheel(100,0);page.wait_for_timeout(100);assert page.evaluate('TemplateStudio.selectedId()')==items[0]
 # The right panel scrolls without choosing a different template.
 right=page.locator('#sheetBody').bounding_box();page.mouse.move(right['x']+right['width']/2,right['y']+right['height']/2)
 page.mouse.wheel(120,0);page.mouse.wheel(0,200);page.wait_for_timeout(100)
 assert page.evaluate('TemplateStudio.selectedId()')==items[0]
 # Pinch (control-wheel) preserves crop zoom and does not select templates.
 center();zoom=page.evaluate('active().zoom');page.keyboard.down('Control');page.mouse.wheel(0,-60);page.keyboard.up('Control');page.wait_for_timeout(100)
 assert page.evaluate('active().zoom')>zoom
 assert page.evaluate('TemplateStudio.selectedId()')==items[0]
 # A new category only filters choices; swipes remain inside it.
 page.locator('#desktopTemplateGroup').select_option('nature')
 group=page.evaluate('TemplateStudio.browseItems().filter(t=>!t.disabled).map(t=>t.id)')
 swipe(75);assert page.evaluate('TemplateStudio.selectedId()')==group[0]
 swipe(75);assert page.evaluate('TemplateStudio.selectedId()')==group[1]
 page.locator('#filterBtn').click();page.wait_for_selector('.filter-card')
 page.evaluate("window.wheelLog=[];window.addEventListener('wheel',e=>wheelLog.push({at:performance.now(),ts:e.timeStamp,x:e.deltaX,filter:filter()[0]}),true)")
 before=page.evaluate('filter()[0]');expected=page.evaluate('FILTERS[FILTERS.findIndex(f=>f[0]===filter()[0])+1][0]');page.wait_for_timeout(300);center()
 for delta in [90,45,10]:page.mouse.wheel(delta,0)
 page.wait_for_timeout(120);after=page.evaluate('filter()[0]');assert after==expected,page.evaluate('wheelLog')
 page.locator('#editorUndo').click();assert page.evaluate('filter()[0]')==before
 page.locator('#editorRedo').click();assert page.evaluate('filter()[0]')==after
 # Auto-reveal the current filter without moving/resizing the left preview.
 beforeRect=page.locator('#preview').bounding_box()
 last=page.evaluate('FILTERS[FILTERS.length-1][0]');page.evaluate('(id)=>changeSetting("filter",id)',last)
 swipe(-90)
 result=page.locator('.filter-card.active').evaluate('(e)=>{const r=e.getBoundingClientRect(),b=document.getElementById("sheetBody").getBoundingClientRect();return r.top>=b.top&&r.bottom<=b.bottom}')
 assert result,'selected filter must be visible'
 afterRect=page.locator('#preview').bounding_box();assert all(abs(beforeRect[k]-afterRect[k])<2 for k in beforeRect)
 # Modal settings suppress preview effect changes.
 current=page.evaluate('filter()[0]');page.locator('#menuBtn').click();swipe(120);assert page.evaluate('filter()[0]')==current
 page.evaluate('closeSheet()');page.wait_for_selector('#sheet.desktop-inspector');page.locator('#templateBtn').click();page.wait_for_selector('#desktopTemplateGroup')
 page.screenshot(path='desktop-swipe.png')
 page.set_viewport_size({'width':390,'height':844});page.evaluate("Object.defineProperty(screen,'width',{value:390,configurable:true});Object.defineProperty(screen,'height',{value:844,configurable:true});render()")
 page.locator('#templateBtn').click();page.wait_for_function('EffectBrowser.active()')
 page.evaluate('TemplateStudio.open()');assert page.locator('.template-categories').is_visible();assert not page.locator('.desktop-template-category').is_visible()
 assert not errors,errors
 browser.close()
 print('PASS compact groups, scoped wheel thresholds/axis/inertia/boundaries, group switches, tone undo/redo, pinch, auto-reveal, modal and mobile isolation')
