from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse,unquote
import mimetypes,io,json,random,sys
from PIL import Image
root=Path(__file__).resolve().parents[1];assets=root/'assets'

with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':411,'height':828},is_mobile=True,has_touch=True);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 calls=[];admin=[True];reprint_fail=[True];history=[dict(token='done-1',phase='done',title='照片',canReprint=True,reprintPages=[dict(copies=2,media=5012),dict(copies=1,media=5012)])];jobs=[dict(token="unknown-1",title="AirPrint",phase="uncertain",message="需检查打印机")]
 def route(r):
  path=unquote(urlparse(r.request.url).path);file=assets/(path.lstrip('/') or 'index.html')
  if path.startswith('/api/'):
   calls.append((path,r.request.post_data))
   if path=='/api/state':value=dict(permission=True,canManageQueue=admin[0],device={},history=history)
   elif path=='/api/admin/queue':value=dict(jobs=jobs)
   elif path=='/api/reprint':
    if reprint_fail[0]:r.fulfill(status=503,body=json.dumps({'error':'模拟网络中断'}),content_type='application/json');return
    value={'ok':True}
   elif path in ['/api/admin/resolve','/api/admin/reconcile']:value={'ok':True}
   else:raise AssertionError('Unexpected API '+path)
   r.fulfill(body=json.dumps(value),content_type='application/json');return
  if path.startswith('/private/'):
   buf=io.BytesIO();Image.new('RGB',(800,1200),'#387fa0').save(buf,'JPEG');r.fulfill(body=buf.getvalue(),content_type='image/jpeg');return
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing asset')
 page.route('https://studio.local/**',route);page.goto('https://studio.local/');page.wait_for_function('window.LayerEditor&&window.CropEditor&&window.StudioExtras');page.evaluate('LayerEditor.ready')

 page.wait_for_function('native.canManageQueue===true');page.evaluate('openHistory()');page.locator('#hostQueue').click()
 page.locator('#queueBack').wait_for(state='visible')
 page.locator('[data-query-job]').click();page.wait_for_timeout(100)
 assert ('/api/admin/reconcile','{"token":"unknown-1"}') in calls
 page.once('dialog',lambda dialog:dialog.dismiss());page.locator('[data-resolve-job]').click()
 assert not any(path=='/api/admin/resolve' for path,_ in calls)
 page.once('dialog',lambda dialog:dialog.accept());page.locator('[data-resolve-job]').click();page.wait_for_timeout(100)
 assert ('/api/admin/resolve','{"token":"unknown-1","confirmed":true}') in calls
 page.locator('#queueBack').click();assert page.locator('#hostQueue').is_visible()
 admin[0]=False;page.evaluate('BrowserTransport.refresh()');page.evaluate('poll();openHistory()');assert page.locator('#hostQueue').count()==0
 page.evaluate('openHistory()');page.locator('[data-history="0"]').click();assert '第 1 页 2 份' in page.locator('#sheetBody').inner_text()
 page.once('dialog',lambda dialog:dialog.dismiss());page.locator('#reprintOriginal').click();assert not any(path=='/api/reprint' for path,_ in calls)
 page.once('dialog',lambda dialog:dialog.accept());page.locator('#reprintOriginal').click();page.wait_for_timeout(100)
 reprint_fail[0]=False;page.once('dialog',lambda dialog:dialog.accept());page.locator('#reprintOriginal').click();page.wait_for_timeout(100)
 requests=[json.loads(body) for path,body in calls if path=='/api/reprint'];assert len(requests)==2 and requests[0]==requests[1] and requests[0]['confirmed'] is True
 assert not any(path=='/api/print' for path,_ in calls)
 assert not errors,errors
 print('PASS: local-only queue entry, back, status query, explicit confirmation, no print endpoint')
 b.close()
