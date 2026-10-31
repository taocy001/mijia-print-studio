"""Real phone availability and discovery checks; never submits a print job."""
import subprocess,json,time,urllib.request,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from airprint.offline import Message,Attribute,encode_ipp,decode_ipp
adb=str(Path.home()/'Library/Android/sdk/platform-tools/adb');pkg='local.liuying.studio'
def run(*a):return subprocess.check_output([adb,*a],text=True).strip()
def wait(page,expression,seconds=20):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if page.evaluate(expression):return
  time.sleep(.2)
 raise AssertionError('Timed out: '+expression)
def browse(name,expected):
 for service in ['_ipp._tcp','_ipp._tcp,_universal']:
  proc=subprocess.Popen(['/usr/bin/dns-sd','-B',service,'local.'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  try:out,_=proc.communicate(timeout=6)
  except subprocess.TimeoutExpired:proc.terminate();out,_=proc.communicate(timeout=3)
  found=any('Add' in line and name in line for line in out.splitlines())
  assert found==expected,('Unexpected discovery',service,expected,out)
def settle(page):
 wait(page,'!JSON.parse(Studio.state()).busy',50)
 wait(page,'JSON.parse(Studio.sharingState()).airprintAdvertised===JSON.parse(Studio.sharingState()).airprintReady')
 return page.evaluate('JSON.parse(Studio.sharingState())')
run('shell','am','start','-W','-n',pkg+'/.MainActivity')
time.sleep(1)
pid=run('shell','pidof',pkg).split()[0];port=run('forward','tcp:0','localabstract:webview_devtools_remote_'+pid);ipp=run('forward','tcp:0','tcp:8637');web=run('forward','tcp:0','tcp:8634')
def attrs(url):
 raw=encode_ipp(Message((2,0),11,777,(Attribute(1,0x47,'attributes-charset',b'utf-8'),Attribute(1,0x48,'attributes-natural-language',b'en'))))
 with urllib.request.urlopen(urllib.request.Request(url,data=raw,headers={'Content-Type':'application/ipp'}),timeout=8) as r:return decode_ipp(r.read())
try:
 with sync_playwright() as p:
  b=p.chromium.connect_over_cdp('http://127.0.0.1:'+port);page=next(pg for c in b.contexts for pg in c.pages if pg.url=='https://studio.local/');wait(page,'!!(window.Studio&&window.TemplateStudio)')
  wait(page,'!JSON.parse(Studio.state()).busy',50)
  assert not page.evaluate('JSON.parse(Studio.state()).unresolved')
  assert not page.evaluate('JSON.parse(Studio.sharingState()).running||JSON.parse(Studio.sharingState()).airprint')
  baseline=page.evaluate('({...localStorage})');was_released=page.evaluate('JSON.parse(Studio.state()).device.released===true')
  try:
   page.evaluate('Studio.startAirPrint()');wait(page,'JSON.parse(Studio.sharingState()).airprint');info=settle(page)
   response=attrs('http://127.0.0.1:'+ipp+'/ipp/print');assert response.code==0
   ready=bool(info['airprintReady']);assert response.values('printer-is-accepting-jobs')==[bytes([int(ready)])]
   browse(info['airprintName'],ready)
   print('PASS: initial short Bluetooth probe controls AirPrint discovery; ready='+str(ready),flush=True)
   page.evaluate('Studio.release()');wait(page,'!JSON.parse(Studio.sharingState()).airprintReady&&!JSON.parse(Studio.sharingState()).airprintAdvertised')
   response=attrs('http://127.0.0.1:'+ipp+'/ipp/print')
   assert response.values('printer-is-accepting-jobs')==[b'\x00']
   for name in ('media-ready','media-default','media-supported','media-col-default','media-col-database'):assert not response.values(name),name
   browse(info['airprintName'],False)
   assert page.evaluate('JSON.parse(Studio.sharingState()).airprint'),'Release must keep IPP job-query endpoint'
   page.evaluate('Studio.connect()');wait(page,'!JSON.parse(Studio.state()).device.released',50);info=settle(page);browse(info['airprintName'],bool(info['airprintReady']))
   assert attrs('http://127.0.0.1:'+ipp+'/ipp/print').values('printer-is-accepting-jobs')==[bytes([int(info['airprintReady'])])]
   print('PASS: release withdraws discovery and unknown paper defaults; connect restores only after successful probe',flush=True)
   page.evaluate('Studio.startSharing()');wait(page,'JSON.parse(Studio.sharingState()).running')
   info=page.evaluate('JSON.parse(Studio.sharingState())');url=info['addresses'][0];assert urllib.request.urlopen(url,timeout=5).status==200
   ipp_url=url.rsplit(':',1)[0]+':8637/ipp/print';assert attrs(ipp_url).code==0
   run('shell','input','keyevent','3');assert attrs(ipp_url).code==0
   page.evaluate('Studio.stopSharing()');wait(page,'!JSON.parse(Studio.sharingState()).running');assert page.evaluate('JSON.parse(Studio.sharingState()).airprint');assert attrs(ipp_url).code==0
   page.evaluate('Studio.startSharing()');wait(page,'JSON.parse(Studio.sharingState()).running');page.evaluate('Studio.stopAirPrint()');wait(page,'!JSON.parse(Studio.sharingState()).airprint&&!JSON.parse(Studio.sharingState()).airprintAdvertised');assert page.evaluate('JSON.parse(Studio.sharingState()).running')
   assert urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:'+web,headers={'Host':'127.0.0.1:8634'}),timeout=5).status==200
   print('PASS: independent Web/AirPrint switches and background status queries',flush=True)
  finally:
   page.evaluate('Studio.stopAirPrint();Studio.stopSharing()');wait(page,'!JSON.parse(Studio.sharingState()).running&&!JSON.parse(Studio.sharingState()).airprint')
   wait(page,'!JSON.parse(Studio.state()).busy',50)
   if was_released:page.evaluate('Studio.release()')
   assert page.evaluate('({...localStorage})')==baseline
   print('Draft unchanged; services restored off; no print request sent',flush=True)
finally:
 for x in [port,ipp,web]:run('forward','--remove','tcp:'+x)
 run('shell','am','start','-W','-n',pkg+'/.MainActivity')
