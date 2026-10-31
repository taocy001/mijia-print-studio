from pathlib import Path
import json,mimetypes
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];assets=root/'assets'
with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':1440,'height':900});errors=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  name=urlparse(r.request.url).path
  if name=='/api/state':r.fulfill(json={'permission':True,'device':{},'history':[]});return
  if name=='/api/print':
   requests.append(json.loads(r.request.post_data))
   if len(requests)==1:r.abort('connectionreset')
   else:r.fulfill(json={'ok':True,'duplicate':True})
   return
  file=assets/(name.lstrip('/') or 'index.html')
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing')
 page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.wait_for_function('window.BrowserTransport&&window.TemplateStudio');page.evaluate('LayerEditor.ready');page.locator('#sampleBtn').click();page.wait_for_function('state.photos.length===1');page.evaluate('BrowserTransport.refresh()');page.evaluate('CropEditor.render()')
 frame=page.locator('#preview').bounding_box();dock=page.locator('.dock').bounding_box();assert frame['y']+frame['height']<=dock['y']+1,(frame,dock)
 page.locator('#printBtn').click();page.locator('#confirmSend').click();page.wait_for_function("!document.querySelector('#confirmSend').disabled");page.locator('#confirmSend').click();page.wait_for_function("document.querySelector('#sheet').hidden")
 assert len(requests)==2 and requests[0]['requestId']==requests[1]['requestId']
 assert requests[0]['pages']==requests[1]['pages'] and 'preview' not in requests[0]['pages'][0]
 assert not errors,errors
 print('PASS: browser transport preserves request ID and payload after lost response; desktop photo and fixed toolbar fit one screen; no printing')
 b.close()
