from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse,unquote
import mimetypes,io,json,random,sys
from PIL import Image
root=Path(__file__).resolve().parents[1];assets=root/'assets'

with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':411,'height':828},is_mobile=True,has_touch=True);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{connected:true,checkedAt:Date.now(),media:5009},history:[]}),printBatch:()=>{throw Error('Printing is forbidden in tests')}}")
 def route(r):
  path=unquote(urlparse(r.request.url).path);file=assets/(path.lstrip('/') or 'index.html')
  if path.startswith('/private/'):
   buf=io.BytesIO();Image.new('RGB',(800,1200),'#387fa0').save(buf,'JPEG');r.fulfill(body=buf.getvalue(),content_type='image/jpeg');return
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing asset')
 page.route('https://studio.local/**',route);page.goto('https://studio.local/');page.wait_for_function('window.LayerEditor&&window.CropEditor&&window.StudioExtras');page.evaluate('LayerEditor.ready')
 page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});state={...defaults,photos:Array.from({length:3},()=>({src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0,fit:'cover',border:0,filter:'none',templateId:null,overlays:[]})),active:0};render();}")


 for width,height in [(411,828),(1440,900)]:
  page.set_viewport_size({'width':width,'height':height})
  page.evaluate("window.testDevice={};Studio.state=()=>JSON.stringify({permission:true,device:testDevice});poll();openPaper()")
  assert page.locator('[data-paper]').count()==0
  assert page.locator('#paperBtn').inner_text()=='识别相纸'
  page.evaluate("testDevice={connected:true,checkedAt:Date.now(),media:5009};poll();render()")
  assert page.evaluate('state.media')==5009
  assert page.locator('[data-paper]').count()==0
  page.evaluate("testDevice={connected:true,checkedAt:Date.now(),media:5012};poll();render();openPaper()")
  assert page.locator('[data-paper]').count()==2
  page.locator('[data-paper="5014"]').click()
  assert page.evaluate('state.media')==5014
  page.evaluate('poll()');assert page.evaluate('state.media')==5014
  page.evaluate('confirmPrint()');assert page.locator('#confirmSend').is_enabled()
  page.evaluate("testDevice={connected:true,checkedAt:Date.now(),media:5009};poll()")
  assert page.evaluate('state.media')==5009
  assert page.evaluate('pendingPrint') is None
  assert page.evaluate("sheetKind!=='confirm'")
  page.evaluate("testDevice={connected:true,checkedAt:Date.now(),media:5012};poll();render()")
  assert page.evaluate('state.media')==5014
  page.evaluate('confirmPrint()')
  page.evaluate('testDevice={connected:false,media:5012};poll()')
  assert page.locator('#confirmSend').is_disabled()
  page.evaluate('closeSheet();testDevice={connected:true,media:5009,checkedAt:Date.now()-151000};poll();openPaper()')
  assert page.locator('[data-paper]').count()==0
  assert page.locator('#paperBtn').inner_text()=='识别相纸'
  page.evaluate('closeSheet()')
 assert not errors,errors
 print('Detected paper: unknown, square, six/splice, tray changes and disconnected confirmation passed at mobile and desktop sizes')
 b.close()
