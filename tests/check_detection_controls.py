"""Detection controls share appearance, locking and navigation behavior."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright

assets=Path(__file__).resolve().parents[1]/'assets'
with sync_playwright() as p:
 browser=p.chromium.launch();page=browser.new_page(viewport={'width':411,'height':828});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script('''window.deviceState={permission:true,device:{},history:[]};window.calls=0;
 window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({airprint:true,airprintReady:false}),
 connect:()=>{calls++;return new Promise(resolve=>window.finishDetection=resolve)},printBatch:()=>{throw Error('Printing forbidden')}};''')
 def route(r):
  file=assets/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing')
 page.route('https://studio.local/**',route);page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')
 for theme in ['light','dark']:
  page.emulate_media(color_scheme=theme);styles=[]
  for panel in ['device','paper','sharing']:
   page.evaluate('closeSheet();deviceState.busy=false;deviceState.unresolved=false;poll()')
   if panel=='sharing':page.locator('#menuBtn').click();page.locator('#sharingMenu').click()
   else:page.evaluate('open'+panel.title()+'()')
   button=page.locator('#connectSharedPrinter' if panel=='sharing' else '#connectNow')
   assert button.inner_text().strip()=='检测打印机'
   styles.append(button.evaluate('(b)=>[getComputedStyle(b).backgroundColor,getComputedStyle(b).color,b.querySelector("svg").outerHTML]'))
   before=page.evaluate('calls');button.click();assert button.is_disabled()
   page.evaluate('poll()');assert button.is_disabled()
   button.dispatch_event('click');assert page.evaluate('calls')==before+1
   page.evaluate('deviceState.busy=true;finishDetection();poll()');page.wait_for_timeout(350)
   assert button.is_disabled() and button.inner_text().strip()=='正在处理…'
   page.evaluate('deviceState.busy=false;deviceState.device={connected:true,media:5009,checkedAt:Date.now()};poll()')
   assert button.is_enabled() and page.evaluate('detectedPaper()')==5009
   page.evaluate('deviceState.unresolved=true;poll()');assert button.is_disabled()
   button.dispatch_event('click');assert page.evaluate('calls')==before+1
   page.evaluate('deviceState.unresolved=false;poll()');button.click()
   page.locator('#closeSheet').click();page.evaluate('finishDetection()');page.wait_for_timeout(350)
   assert page.evaluate("sheetKind===''")
  assert styles[0]==styles[1]==styles[2],styles
 page.evaluate("()=>{openPaper();Studio.connect=()=>Promise.reject(Error('连接失败'));}")
 page.locator('#connectNow').click();page.wait_for_timeout(100)
 assert page.locator('#connectNow').is_enabled()
 page.evaluate('''()=>{Studio.connect=()=>{calls++;setTimeout(()=>{deviceState.busy=true},80)};openPaper();}''')
 before=page.evaluate('calls');page.locator('#connectNow').click();assert page.locator('#connectNow').is_disabled()
 page.wait_for_timeout(300);assert page.locator('#connectNow').is_disabled()
 page.locator('#connectNow').dispatch_event('click');assert page.evaluate('calls')==before+1
 page.evaluate('deviceState.busy=false;poll()');assert page.locator('#connectNow').is_enabled()
 page.evaluate('''async()=>{closeSheet();deviceState={permission:true,device:{},history:[]};state.media=5009;Studio.connect=()=>{calls++;deviceState.device={connected:true,media:5009,checkedAt:Date.now()};};poll();await addPhotos([{src:'/sample.svg'}]);await confirmPrint();}''')
 assert page.locator('#connectBeforePrint').is_visible()
 before=page.evaluate('calls');page.locator('#connectBeforePrint').click();page.wait_for_timeout(350)
 assert page.evaluate("sheetKind==='confirm'") and page.locator('#confirmSend').is_enabled()
 assert not page.locator('#connectBeforePrint').is_visible() and page.evaluate('calls')==before+1
 page.evaluate('closeSheet();confirmPrint()');assert page.locator('#confirmSend').is_enabled()
 assert not page.locator('#connectBeforePrint').is_visible() and page.evaluate('calls')==before+1
 assert not errors,errors
 browser.close();print('PASS: three detection entries, light/dark styles, pending/busy locks, retry and navigation; no printing')
