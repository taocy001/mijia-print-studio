"""Preserve scroll while comparing extended layout choices."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width,height in [(390,700),(411,828),(1280,720)]:
  page=browser.new_page(viewport={'width':width,'height':height});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  server={'permission':True,'device':{'connected':True,'media':5012,'checkedAt':int(time.time()*1000)},'history':[]}
  def route(r):
   assert r.request.method=='GET','Audit must not print'
   path=urlparse(r.request.url).path
   if path=='/api/state':r.fulfill(json=server);return
   file=ROOT/'assets'/(path.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.ImageExport&&window.CropEditor');page.evaluate('LayerEditor.ready')
  page.evaluate("async()=>{closeSheet();const photo={src:'/sample.svg',turn:0,zoom:1,x:0,y:0,fit:'cover',filter:'none',overlays:[]};await loadPhoto(photo);state={...defaults,photos:[photo],active:0};render()}")
  for mode,key in [('label','labelTheme'),('card','cardStyle')]:
   page.evaluate("mode=>{closeSheet();state.mode=mode;render();openLayout()}",mode)
   button=page.locator('[data-setting='+key+']').last
   button.scroll_into_view_if_needed()
   before=page.locator('#sheetBody').evaluate('(e)=>e.scrollTop')
   value=button.get_attribute('data-value')
   button.click();page.wait_for_timeout(100)
   after=page.locator('#sheetBody').evaluate('(e)=>e.scrollTop')
   assert abs(after-before)<=1,(width,mode,before,after)
   assert page.evaluate('(key)=>state[key]',key)==value
   assert page.evaluate("sheetKind==='layout'&&!$('sheet').hidden")
   if width<1000:assert before>0,(width,mode)
  assert not errors,errors
  page.close()
 browser.close()
print('PASS: label/card choices retain scroll on phone and desktop; no printing')
