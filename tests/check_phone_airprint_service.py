"""Real phone discovery and service checks; no print jobs are sent."""
import subprocess,json,time,urllib.request,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from airprint.offline import Message,Attribute,encode_ipp,decode_ipp
adb=str(Path.home()/'Library/Android/sdk/platform-tools/adb');pkg='local.liuying.studio'
def run(*a):return subprocess.check_output([adb,*a],text=True).strip()
run('shell','am','start','-W','-n',pkg+'/.MainActivity')
time.sleep(1)
pid=run('shell','pidof',pkg).split()[0];port=run('forward','tcp:0','localabstract:webview_devtools_remote_'+pid);ipp=run('forward','tcp:0','tcp:8637');web=run('forward','tcp:0','tcp:8634')
def attrs(url):
 raw=encode_ipp(Message((2,0),11,777,(Attribute(1,0x47,'attributes-charset',b'utf-8'),Attribute(1,0x48,'attributes-natural-language',b'en'))))
 with urllib.request.urlopen(urllib.request.Request(url,data=raw,headers={'Content-Type':'application/ipp'}),timeout=8) as r:return decode_ipp(r.read())
try:
 with sync_playwright() as p:
  b=p.chromium.connect_over_cdp('http://127.0.0.1:'+port);page=next(pg for c in b.contexts for pg in c.pages if pg.url=='https://studio.local/');page.wait_for_function('window.Studio&&window.TemplateStudio')
  assert not page.evaluate('JSON.parse(Studio.state()).busy||JSON.parse(Studio.state()).unresolved')
  assert not page.evaluate('JSON.parse(Studio.sharingState()).running||JSON.parse(Studio.sharingState()).airprint')
  baseline=page.evaluate('({...localStorage})')
  try:
   page.evaluate('Studio.startAirPrint()');page.wait_for_function('JSON.parse(Studio.sharingState()).airprint')
   response=attrs('http://127.0.0.1:'+ipp+'/ipp/print');assert response.code==0
   assert response.values('printer-is-accepting-jobs')==[b'\x00'];assert response.values('media-ready')==[]
   name=page.evaluate('JSON.parse(Studio.sharingState()).airprintName')
   for service in ['_ipp._tcp','_ipp._tcp,_universal']:
    proc=subprocess.Popen(['/usr/bin/dns-sd','-B',service,'local.'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    try:out,_=proc.communicate(timeout=6)
    except subprocess.TimeoutExpired:proc.terminate();out,_=proc.communicate(timeout=3)
    assert name in out,'Phone not discovered: '+service
   assert not page.evaluate('JSON.parse(Studio.sharingState()).airprintError')
   print('PASS: Mac discovers phone AirPrint; IPP reports unavailable until Bluetooth detection',flush=True)
   page.evaluate('Studio.startSharing(true)');page.wait_for_function('JSON.parse(Studio.sharingState()).running')
   info=page.evaluate('JSON.parse(Studio.sharingState())');url=info['addresses'][0];assert urllib.request.urlopen(url,timeout=5).status==200
   ipp_url=url.rsplit(':',1)[0]+':8637/ipp/print';assert attrs(ipp_url).code==0
   run('shell','input','keyevent','3');assert attrs(ipp_url).code==0
   page.evaluate('Studio.stopSharing()');page.wait_for_function('!JSON.parse(Studio.sharingState()).running');assert page.evaluate('JSON.parse(Studio.sharingState()).airprint');assert attrs(ipp_url).code==0
   page.evaluate('Studio.startSharing(false)');page.wait_for_function('JSON.parse(Studio.sharingState()).running');page.evaluate('Studio.stopAirPrint()');page.wait_for_function('!JSON.parse(Studio.sharingState()).airprint');assert page.evaluate('JSON.parse(Studio.sharingState()).running')
   assert urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:'+web,headers={'Host':'127.0.0.1:8634'}),timeout=5).status==200
   print('PASS: Wi-Fi HTTP and IPP, background operation, independent Web/AirPrint start and stop',flush=True)
  finally:
   page.evaluate('Studio.stopAirPrint();Studio.stopSharing()');page.wait_for_function('!JSON.parse(Studio.sharingState()).running&&!JSON.parse(Studio.sharingState()).airprint')
   assert page.evaluate('({...localStorage})')==baseline
   print('Draft unchanged; both services restored off; no print request sent',flush=True)
finally:
 for x in [port,ipp,web]:run('forward','--remove','tcp:'+x)
 run('shell','am','start','-W','-n',pkg+'/.MainActivity')
