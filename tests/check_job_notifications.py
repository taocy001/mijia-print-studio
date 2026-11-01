"""Exercise status sequences without contacting a printer."""
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
  def status(job=None,**kwargs):
   page.evaluate('(s)=>{native=s;updateStatus()}',dict(job=job or {},**kwargs))
  def job(token,phase,**kwargs):return dict(token=token,phase=phase,**kwargs)
  def count(n):assert page.evaluate('notices.length')==n,(transport,page.evaluate('notices'))
  old=job('old','done',createdAt=1)
  failure=job('failure','rejected',createdAt=2,message='测试失败')
  for busy in [False,True,False,True,False]:
   status(old,busy=busy,failure=failure);count(0)
   assert page.evaluate('displayJob().token')=='failure'
   if busy:assert page.locator('#deviceText').text_content()=='正在读取打印机状态'
  status(old,busy=True);count(0)
  assert page.locator('#jobBanner').is_hidden()
  for phase in ['queued','printing','done','done','printing','done']:
   status(job('a',phase))
  count(1)
  status(job('b','printing'));status(old);count(1)
  status();status(job('b','done'));count(2)
  for phase in ['cancelled','aborted','rejected']:
   status(job(phase,'printing'));status(job(phase,phase));status(job(phase,'done'));count(2)
  for i,phase in enumerate(['held','uncertain','blocked']):
   status(job(phase,phase));status(job(phase,'done'));count(3+i)
  for index in [1,2]:
   status(job('page'+str(index),'printing',batchIndex=index,batchCount=2))
   status(job('page'+str(index),'done',batchIndex=index,batchCount=2))
   count(5+(index==2))
  status(job('stopped','printing',batchIndex=2,batchCount=2))
  status(job('stopped','done',batchIndex=2,batchCount=2,batchStopped=True));count(6)
  status(job('queued-next','queued'))
  status(old);count(6)
  status(job('history-only','printing'))
  for _ in range(3):status(job('next','queued'),history=[old,job('history-only','done')])
  count(7)
  status(job('simulation','printing',batchIndex=1,batchCount=3),simulation=True)
  status(job('simulation','done',batchIndex=1,batchCount=3),simulation=True);count(8)
  assert page.evaluate('notices.at(-1)')=='模拟打印已完成，不会实际出纸。'
  status(job('desktop-batch','printing',batchIndex=1,batchCount=2))
  status(job('desktop-batch','printing',batchIndex=2,batchCount=2));count(8)
  status(job('desktop-batch','done',batchIndex=2,batchCount=2));count(9)
  # A new page must treat terminal records as history, not new completions.
  page.reload();page.wait_for_function('window.TemplateStudio')
  page.evaluate("poll=()=>{};window.notices=[];toast=s=>notices.push(s);void 0")
  status(job('a','done'),history=[job('history-only','done')]);count(0)
  page.close()
 browser.close()
print('PASS: native/web detection, task identity, repeated snapshots, recovery, batches, queue history, simulation and reload; no printing')
