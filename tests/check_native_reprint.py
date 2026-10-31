from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse,unquote
import mimetypes,io,json,random,sys
from PIL import Image
root=Path(__file__).resolve().parents[1];assets=root/'assets'

with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':411,'height':828},is_mobile=True,has_touch=True);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{},history:[]}),printBatch:()=>{throw Error('Printing is forbidden in tests')}}")
 def route(r):
  path=unquote(urlparse(r.request.url).path);file=assets/(path.lstrip('/') or 'index.html')
  if path.startswith('/private/'):
   buf=io.BytesIO();Image.new('RGB',(800,1200),'#387fa0').save(buf,'JPEG');r.fulfill(body=buf.getvalue(),content_type='image/jpeg');return
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing asset')
 page.route('https://studio.local/**',route);page.goto('https://studio.local/');page.wait_for_function('window.LayerEditor&&window.CropEditor&&window.StudioExtras');page.evaluate('LayerEditor.ready')

 page.evaluate("window.calls=[];Studio.reprint=async payload=>{calls.push(JSON.parse(payload));await new Promise(r=>setTimeout(r,50));return JSON.stringify(calls.length===1?{error:'模拟响应丢失'}:{ok:true})};Object.defineProperty(window,'sessionStorage',{get:()=>{throw Error('Unavailable storage')}});native.history=[{token:'native-complete-1',phase:'done',canReprint:true,copies:2,reprintPages:[{copies:2,media:5009},{copies:1,media:5009}]}];openHistory()")
 page.locator('[data-history="0"]').click();assert '第 1 页 2 份' in page.locator('#sheetBody').inner_text()
 page.once('dialog',lambda d:d.dismiss());page.locator('#reprintOriginal').click();assert page.evaluate('calls.length')==0
 page.once('dialog',lambda d:d.accept());page.evaluate('Promise.all([reprintOriginal(native.history[0]),reprintOriginal(native.history[0])])');assert page.evaluate('calls.length')==1
 page.once('dialog',lambda d:d.accept());page.locator('#reprintOriginal').click();page.wait_for_timeout(100)
 calls=page.evaluate('calls');assert len(calls)==2 and calls[0]==calls[1] and calls[0]['confirmed'] is True
 assert not errors,errors
 print('PASS: native bridge exact reprint confirmation, per-page counts, in-flight guard and request-ID retry without storage; no printing')
 b.close()
