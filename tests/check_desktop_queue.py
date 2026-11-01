"""Desktop tab identity and queue navigation with delayed mock responses."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
 browser=runtime.chromium.launch()
 for width,height in [(1280,720),(1440,900)]:
  page=browser.new_page(viewport={'width':width,'height':height});pending=[];errors=[]
  page.on('pageerror',lambda error:errors.append(str(error)))
  def route(r):
   assert r.request.method=='GET','Queue UI checks must not print or change jobs'
   path=urlparse(r.request.url).path
   if path=='/api/state':r.fulfill(json={'host':'desktop','permission':True,'canManageQueue':True,'device':{},'history':[]});return
   if path=='/api/admin/queue':pending.append(r);return
   file=ROOT/'assets'/(path.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('native.canManageQueue&&window.LayerEditor');page.evaluate('LayerEditor.ready')
  for mode in ['label','card']:
   page.locator('#menuBtn').click();page.locator('#menuWorkType').click();page.locator('[data-layout-mode="'+mode+'"]').click();page.locator('#addTextQuick').click()
   expect(page.locator('#addTextQuick')).to_have_attribute('aria-pressed','true')
   assert page.locator('.tool-tabs [aria-pressed=true]').count()==1
  def queue():
   if page.locator('#scrim').is_visible():page.locator('#closeSheet').click()
   page.locator('#menuBtn').click();page.locator('#menuHistory').click();page.locator('#hostQueue').click();page.wait_for_function("sheetKind==='hostQueue'")
   assert page.locator('#sheet').evaluate("e=>e.classList.contains('desktop-settings')")
   assert page.locator('#settingsBack').is_visible()
   assert page.locator('#queueBack').count()==0
   assert '正在读取' in page.locator('#sheetBody').inner_text()
  queue();page.wait_for_timeout(50)
  assert pending
  page.locator('#settingsBack').click();assert page.evaluate("sheetKind==='history'")
  pending.pop().fulfill(json={'jobs':[{'title':'迟到任务','phase':'uncertain','message':'合成结果'}]});page.wait_for_timeout(100)
  assert page.evaluate("sheetKind==='history'") and '迟到任务' not in page.locator('#sheetBody').inner_text()
  queue();page.wait_for_timeout(50);pending.pop().fulfill(status=503,json={'error':'合成服务暂不可用'})
  page.wait_for_selector('#retryQueue');assert '合成服务暂不可用' in page.locator('#sheetBody').inner_text()
  page.locator('#retryQueue').click();page.wait_for_timeout(50);pending.pop().fulfill(json={'jobs':[{'title':'合成任务','phase':'uncertain','message':'请检查测试结果'}]})
  page.wait_for_selector('[data-query-job]');assert page.locator('#sheet').evaluate("e=>e.classList.contains('desktop-settings')")
  box=page.locator('#sheet').bounding_box();assert box['width']>=700 and box['y']>=0 and box['y']+box['height']<=height
  page.screenshot(path=f'/tmp/desktop-queue-fixed-{width}.png')
  page.locator('#settingsBack').click();assert page.evaluate("sheetKind==='history'")
  assert not errors,errors;page.close()
 browser.close()
print('PASS: desktop text tabs, queue size/back, loading, retry and stale response isolation; no printing')
