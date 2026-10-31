from pathlib import Path
from urllib.parse import urlparse
import mimetypes,time
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];assets=root/'assets'
with sync_playwright() as p:
 browser=p.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':900});errors=[]
 state={'permission':True,'device':{'connected':True,'media':5012,'checkedAt':int(time.time()*1000)},'history':[],'airprintSplice':False}
 shared={'running':True,'lan':True,'addresses':['http://192.168.1.25:8633'],'current':'http://127.0.0.1:8633','airprint':True}
 def route(r):
  name=urlparse(r.request.url).path
  if name=='/api/state':r.fulfill(json=state);return
  if name=='/api/sharing':r.fulfill(json=shared);return
  if name=='/api/airprint-layout':state['airprintSplice']=r.request.post_data_json['splice'];r.fulfill(json={'ok':True});return
  if name=='/api/release':state['device'].update(connected=False,released=True);r.fulfill(json={'ok':True});return
  if name=='/api/connect':state['device'].update(connected=True,released=False,checkedAt=int(time.time()*1000));r.fulfill(json={'ok':True});return
  file=assets/(name.lstrip('/') or 'index.html')
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing')
 page.on('pageerror',lambda e:errors.append(str(e)));page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.wait_for_function('window.BrowserTransport&&detectedPaper()===5012')
 page.locator('#menuBtn').click();box=page.locator('#sheet').bounding_box();assert box['width']>=780 and box['height']>=700,box
 page.screenshot(path='/tmp/liuying-settings-menu.png')
 page.locator('#menuDevice').click();page.locator('#airprintLayout').click();page.wait_for_function('native.airprintSplice')
 assert page.evaluate("sheetKind==='device'&&!$('sheet').hidden")
 assert '四寸拼接' in page.locator('#airprintLayout').inner_text()
 page.locator('#releaseBluetooth').click();page.wait_for_function('native.device.released')
 assert page.evaluate("sheetKind==='device'&&!$('sheet').hidden")
 page.locator('#connectNow').click();page.wait_for_function('native.device.connected')
 assert page.evaluate("sheetKind==='device'&&!$('sheet').hidden")
 page.locator('#changePaper').click();page.locator('[data-paper="5014"]').click();assert page.evaluate("sheetKind==='paper'&&state.media===5014")
 page.locator('#settingsBack').click();page.locator('#sharingMenu').click();page.wait_for_selector('#shareAddress0');assert page.locator('#shareAddress0').input_value()==shared['addresses'][0]
 shared['addresses']=['http://192.168.1.26:8633'];page.wait_for_function("$('shareAddress0')?.value==='http://192.168.1.26:8633'")
 assert page.evaluate("sheetKind==='sharing'&&!$('sheet').hidden")
 page.screenshot(path='/tmp/liuying-settings-addresses.png')
 page.locator('#shareAddress0').click();page.wait_for_timeout(1400);assert page.locator('#shareAddress0').evaluate('(e)=>e===document.activeElement')
 page.locator('#settingsBack').click();page.locator('#menuPrintOptions').click();page.locator('#extraCopies').fill('3');page.locator('#sheetTitle').click();assert page.evaluate("state.copies===3&&sheetKind==='printOptions'")
 page.locator('#settingsBack').click();page.locator('#menuCoat').click();page.locator('[data-coat="grid"]').click();assert page.evaluate("sheetKind==='coat'")
 assert not errors,errors
 ctx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);mobile=ctx.new_page();mobile.route('https://studio.test/**',route);mobile.goto('https://studio.test/');mobile.wait_for_selector('#fullscreenBtn')
 assert not mobile.evaluate('!!document.fullscreenElement')
 mobile.locator('#fullscreenBtn').click();mobile.wait_for_function('!!document.fullscreenElement');assert mobile.locator('#fullscreenBtn').get_attribute('aria-label')=='退出全屏'
 mobile.locator('#fullscreenBtn').click();mobile.wait_for_function('!document.fullscreenElement')
 assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
 print('PASS: large settings, persistent connection/paper/layout panels, live addresses, copies/coat changes, mobile fullscreen enter/exit')
 browser.close()
