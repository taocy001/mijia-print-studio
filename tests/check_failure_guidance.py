"""Readable failures, acknowledgement and persistent unresolved warnings."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for transport in ['native','web']:
  page=browser.new_page(viewport={'width':411,'height':828})
  if transport=='native':page.add_init_script("window.Studio={landscape:()=>false,state:()=>'{\"device\":{},\"history\":[]}'}")
  def route(r):
   assert r.request.method=='GET','No printing in notification tests'
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'device':{},'history':[]});return
   file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('**/*',route);page.goto('https://studio.test/')
  page.wait_for_function('window.TemplateStudio')
  page.evaluate("poll=()=>{};window.notices=[];toast=s=>notices.push(s);void 0")
  failure={'token':'paper-test','phase':'rejected','stage':'validation','message':'AirPrint 相纸设置与实际纸盒不一致','createdAt':2}
  def status(f,unresolved=False):
   page.evaluate('(v)=>{native={job:v.unresolved?v.f:{},failure:v.f,history:[v.f],unresolved:v.unresolved};updateStatus()}',{'f':f,'unresolved':unresolved})
  status(failure)
  assert page.locator('#jobBanner').is_visible()
  assert '重新选择打印机' in page.locator('dialog.print-failure').inner_text()
  page.locator('#failureAcknowledge').click()
  assert page.locator('#jobBanner').is_hidden()
  assert page.evaluate('native.history.length')==1
  assert page.evaluate('native.failure.message')==failure['message']
  page.evaluate('openHistory()');page.locator('[data-history="0"]').click()
  assert '重新选择打印机' in page.locator('#sheetBody').inner_text()
  page.evaluate('closeSheet()')
  page.reload();page.wait_for_function('window.TemplateStudio');page.evaluate('poll=()=>{};void 0')
  status(failure)
  assert page.locator('#jobBanner').is_hidden()
  assert page.locator('dialog.print-failure[open]').count()==0
  changed={**failure,'message':'AirPrint 请求不支持：One copy per job'}
  status(changed)
  assert page.locator('#jobBanner').is_visible()
  assert '每页多张' in page.locator('dialog.print-failure').inner_text()
  page.locator('#failureAcknowledge').click()
  assert page.locator('#jobBanner').is_hidden()
  for phase in ['uncertain','blocked','held']:
   status({**failure,'token':phase,'phase':phase,'message':'结果尚未确认，请检查打印机'},True)
   page.locator('#failureAcknowledge').click()
   assert page.locator('#jobBanner').is_visible(),phase
  status({**failure,'token':'aborted','phase':'aborted','message':'任务已中止，请检查打印机'})
  page.locator('#failureAcknowledge').click()
  assert page.locator('#jobBanner').is_hidden()
  for code in ['One copy per job','Unsupported scaling','Page ranges unsupported','Photographic media required','Unsupported collection']:
   message=page.evaluate("code=>printMessage({message:'AirPrint 请求不支持：'+code})",code)
   assert code not in message and '请' in message,message
  page.close()
 browser.close()
print('PASS: actionable errors, raw history retained, acknowledgement survives reload, changed and unresolved failures remain visible; no printing')
