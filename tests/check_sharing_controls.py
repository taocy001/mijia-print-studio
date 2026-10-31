from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse,unquote
import mimetypes,io,json,random,sys
from PIL import Image
root=Path(__file__).resolve().parents[1];assets=root/'assets'

with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':411,'height':828},is_mobile=True,has_touch=True);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.shared={airprint:true,airprintName:'Test printer',paused:true};window.calls=[];window.Studio={sharingState:()=>JSON.stringify(shared),resumeSharing:()=>calls.push('resume'),startAirPrint:()=>calls.push('start'),stopAirPrint:()=>calls.push('stop'),release:()=>calls.push('release'),state:()=>JSON.stringify({permission:true,device:{connected:true,checkedAt:Date.now(),media:5009},history:[]}),printBatch:()=>{throw Error('Printing is forbidden in tests')}}")
 def route(r):
  path=unquote(urlparse(r.request.url).path);file=assets/(path.lstrip('/') or 'index.html')
  if path.startswith('/private/'):
   buf=io.BytesIO();Image.new('RGB',(800,1200),'#387fa0').save(buf,'JPEG');r.fulfill(body=buf.getvalue(),content_type='image/jpeg');return
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing asset')
 page.route('https://studio.local/**',route);page.goto('https://studio.local/');page.wait_for_function('window.LayerEditor&&window.CropEditor&&window.StudioExtras');page.evaluate('LayerEditor.ready')
 page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});state={...defaults,photos:Array.from({length:3},()=>({src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0,fit:'cover',border:0,filter:'none',templateId:null,overlays:[]})),active:0};render();}")


 page.locator('#menuBtn').click();page.locator('#sharingMenu').click()
 assert page.locator('#stopAirPrint').count()==1
 assert page.locator('#resumeSharing').count()==1
 page.locator('#resumeSharing').click();assert page.evaluate('calls')==['resume']
 page.evaluate('shared={running:false,airprint:false,paused:false}')
 page.locator('#menuBtn').click();page.locator('#sharingMenu').click()
 assert page.locator('#startAirPrint').count()==1
 assert page.locator('#startLocal').count()==1 and page.locator('#startLan').count()==1
 page.locator('#startAirPrint').click();assert page.evaluate('calls')==['resume','start']
 page.evaluate('native.device={connected:false,released:false};openDevice()')
 assert page.locator('#releaseBluetooth').count()==1
 page.locator('#releaseBluetooth').click();assert page.evaluate('calls')[-1]=='release'
 page.evaluate('native.device={connected:false,released:true};openDevice()')
 assert page.locator('#releaseBluetooth').count()==0
 assert not errors,errors
 print('PASS: independent sharing controls, AirPrint-only queue resume, release after connection failure')
 b.close()
