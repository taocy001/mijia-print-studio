"""Display-only progress states, with no printer or backend."""
from pathlib import Path
import mimetypes,time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width,height in [(390,844),(844,390),(1440,1000)]:
  page=browser.new_page(viewport={'width':width,'height':height});errors=[]
  page.on('pageerror',lambda error:errors.append(str(error)))
  def route(r):
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'permission':True,'device':{'connected':True,'media':5009,'checkedAt':int(time.time()*1000)},'history':[]});return
   if name.startswith('/api/') and r.request.method!='GET':raise AssertionError('Progress UI must not submit')
   file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('https://studio.test/**',route);page.goto('https://studio.test/')
  page.wait_for_function('window.TemplateStudio&&window.BrowserTransport')
  page.evaluate("poll=()=>{};native.busy=true;native.unresolved=true;native.job={token:'test-only',phase:'queued',message:'等待打印',progress:0};openJob();updateStatus()")
  page.evaluate("window.progressMessageNode=document.getElementById('liveJobMessage')")
  page.evaluate("native.job={...native.job,phase:'printing',message:'照片已发送，等待打印机完成',progress:-1};updateStatus()")
  assert page.evaluate("window.progressMessageNode===document.getElementById('liveJobMessage')")
  assert page.locator('#liveJobMessage').inner_text()=='照片已发送，等待打印机完成'
  assert page.locator('#jobProgress').evaluate("e=>e.classList.contains('indeterminate')")
  page.emulate_media(reduced_motion='reduce')
  assert page.locator('#jobProgress').evaluate('e=>getComputedStyle(e).animationName')=='none'
  for phase in ['held','uncertain','cancelled','aborted','done']:
   page.evaluate('(phase)=>{native.job.phase=phase;updateStatus()}',phase)
   assert not page.locator('#jobProgress').evaluate("e=>e.classList.contains('indeterminate')")
  assert not errors,errors
  page.close()
 browser.close()
print('PASS: progress updates in place, no false completion, reduced motion, mobile/landscape/desktop; no requests submitted')
