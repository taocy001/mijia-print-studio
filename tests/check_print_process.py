"""Synthetic job playback only; no printer or print endpoint."""
import io,mimetypes,time
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
im=Image.new('RGB',(1040,1040),'#32976b');d=ImageDraw.Draw(im);d.rectangle((0,0,520,520),fill='#e24732');d.rectangle((520,520,1040,1040),fill='#2e63cb');buffer=io.BytesIO();im.save(buffer,'JPEG');photo=buffer.getvalue()
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width,height in [(390,844),(844,390),(1440,1000)]:
  page=browser.new_page(viewport={'width':width,'height':height});errors=[];reads=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   name=urlparse(r.request.url).path
   if name.startswith('/private/'):
    assert name in ['/private/prints/a.jpg','/private/prints/b.jpg'],name
    reads.append(name);r.fulfill(body=photo,content_type='image/jpeg');return
   if name=='/api/state':r.fulfill(json={'permission':True,'device':{},'history':[]});return
   if name.startswith('/api/') and r.request.method!='GET':raise AssertionError('Animation must not submit')
   file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('https://studio.test/**',route);page.goto('https://studio.test/')
  page.wait_for_function('window.PrintProcess&&window.TemplateStudio')
  page.evaluate("window.testTime=Date.now();Date.now=()=>window.testTime;window.testJob={token:'synthetic',phase:'printing',message:'正在发送照片',progress:50,media:5009,file:'prints/a.jpg',orientation:'square',batchIndex:1,telemetry:{stage:'transfer',sampleAt:Date.now()}};Studio.state=()=>JSON.stringify({permission:true,busy:true,unresolved:true,job:testJob,history:[],device:{}});poll();openJob()")
  page.wait_for_function("document.querySelector('.print-process canvas').width===360")
  canvas=page.locator('.print-process canvas');full=canvas.evaluate('c=>c.toDataURL()')
  assert page.locator('.print-process figcaption').inner_text()=='正在发送照片'
  page.evaluate("testJob.message='照片已发送，等待打印机完成';testJob.telemetry={stage:'waiting',sampleAt:Date.now(),device:{'job-state':2,'job-sub-state':1234}};poll()")
  page.wait_for_timeout(35);assert '黄染层' in page.locator('.print-process figcaption').inner_text()
  for phase in ['品红染层','青染层','覆膜']:
   for _ in range(13):
    page.evaluate('testTime+=1000;testJob.telemetry.sampleAt=Date.now();PrintProcess.update(testJob)');page.wait_for_timeout(25)
   assert phase in page.locator('.print-process figcaption').inner_text(),page.locator('.print-process figcaption').inner_text()
  assert page.locator('.print-process small').is_visible()
  status=page.locator('.print-process figcaption').bounding_box();sheet=page.locator('#sheet').bounding_box();assert status['y']+status['height']<=sheet['y']+sheet['height'],(status,sheet)
  page.screenshot(path=f'/tmp/print-process-{width}.png')
  for state in [1,5,7,8,9]:
   page.evaluate('(state)=>{testJob.telemetry.device["job-state"]=state;testJob.telemetry.sampleAt=Date.now();PrintProcess.update(testJob)}',state)
   page.wait_for_timeout(35)
   stopped=canvas.evaluate('c=>c.toDataURL()');page.evaluate('testTime+=1000;testJob.telemetry.sampleAt=Date.now();PrintProcess.update(testJob)');page.wait_for_timeout(35)
   assert canvas.evaluate('c=>c.toDataURL()')==stopped
   if state==5:assert '暂停' in page.locator('.print-process figcaption').inner_text()
   assert page.locator('.print-process figcaption').inner_text()!='打印机已确认完成'
  page.evaluate('testJob.telemetry.device["job-state"]=2;PrintProcess.update(testJob)');page.wait_for_timeout(35)
  assert page.evaluate('testJob.phase')=='printing'
  page.evaluate('testTime+=10000;PrintProcess.update(testJob)');page.wait_for_timeout(35)
  assert '暂停' in page.locator('.print-process figcaption').inner_text()
  paused=canvas.evaluate('c=>c.toDataURL()');page.wait_for_timeout(100);assert paused==canvas.evaluate('c=>c.toDataURL()')
  page.emulate_media(reduced_motion='reduce');page.wait_for_timeout(30);assert canvas.evaluate('c=>c.toDataURL()')==full
  page.evaluate("testJob.phase='done';testJob.message='打印完成';poll()")
  assert page.locator('.print-process figcaption').inner_text()=='打印机已确认完成'
  assert canvas.evaluate('c=>c.toDataURL()')==full
  page.emulate_media(reduced_motion='no-preference')
  for media,orientation in [(5012,'landscape'),(5014,'portrait')]:
   page.evaluate("([media,orientation])=>{testJob.phase='printing';testJob.batchIndex++;testJob.previewPage={file:'prints/b.jpg',media,orientation};testJob.telemetry.sampleAt=Date.now();poll()}",[media,orientation])
   page.wait_for_function("document.querySelector('.print-process canvas').width===360")
   assert page.locator('.print-process').count()==1
  page.evaluate('closeSheet()');assert page.locator('.print-process').count()==0
  assert not errors,errors;assert set(reads)=={'/private/prints/a.jpg','/private/prints/b.jpg'}
  page.close()
 browser.close()
print('PASS: submitted-page playback, illustrative dyes, stale pause, reduced motion, device-only completion, page switch and cleanup; no printing')
