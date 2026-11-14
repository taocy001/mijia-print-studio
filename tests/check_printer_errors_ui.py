"""Verify error guidance in both native and desktop browser UI without printing."""
import os,mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(**({'channel':os.environ['TEST_BROWSER_CHANNEL']} if os.environ.get('TEST_BROWSER_CHANNEL') else {}))
 page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  f=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
  mime={'.js':'text/javascript','.svg':'image/svg+xml','.html':'text/html','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}.get(f.suffix,mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
  r.fulfill(body=f.read_bytes(),content_type=mime) if f.is_file() else r.fulfill(status=404)
 page.route('https://studio.local/**',route)
 page.add_init_script("window.deviceState={permission:true,device:{connected:true,media:5012,ribbon:29,checkedAt:Date.now(),alert:'::9008'},history:[]};window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({}),printBatch:()=>{throw Error('Printing forbidden')}}")
 page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')
 for host in ['android','desktop']:
  page.evaluate('(host)=>{deviceState.host=host;poll();openDevice()}',host)
  assert 'Type-C 供电不足' in page.locator('#sheetBody').inner_text()
  assert '9008' in page.locator('#sheetBody').inner_text()
  assert '配套电源' in page.locator('#sheetBody').inner_text()
  page.evaluate("closeSheet();deviceState.job={token:'power',phase:'rejected',message:'打印机告警（9008)。照片尚未提交'};deviceState.unresolved=false;poll()")
  if page.locator('#failureAcknowledge').is_visible():page.locator('#failureAcknowledge').click()
  page.evaluate('openJob()');assert 'Type-C 供电不足' in page.locator('#liveJobMessage').inner_text()
  page.evaluate("closeSheet();deviceState.device.alert='::5402%9008:5402';poll();openDevice()")
  text=page.locator('#sheetBody').inner_text();assert '进纸失败' in text and '供电不足' in text
  page.evaluate("closeSheet();deviceState.device.alert='::9999';poll();openDevice()")
  assert '未识别' in page.locator('#sheetBody').inner_text() and '9999' in page.locator('#sheetBody').inner_text()
  page.evaluate("closeSheet();deviceState.device.alert='::9008';deviceState.job={};poll()")
 assert not errors,errors
 browser.close()
print('PASS: native and desktop error dialogs, device panel, old history, compound and unknown codes; no printing')
