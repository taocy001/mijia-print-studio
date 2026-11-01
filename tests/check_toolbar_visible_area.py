"""Default toolbar stays in the visible editor; manual placement persists."""
import io,mimetypes,time
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
image=Image.new('RGB',(800,1200),'#3285ad');buffer=io.BytesIO();image.save(buffer,'JPEG');jpeg=buffer.getvalue()
with sync_playwright() as runtime:
 browser=runtime.chromium.launch()
 for width,height,mobile in [(390,700,True),(411,828,True),(844,390,True),(1440,900,False)]:
  context=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile);page=context.new_page();errors=[]
  page.on('pageerror',lambda error:errors.append(str(error)))
  def route(request):
   path=urlparse(request.request.url).path
   if path=='/api/state':request.fulfill(json={'permission':True,'host':'desktop','device':{},'history':[]});return
   if path=='/api/upload':request.fulfill(json={'src':'/private/photos/00000000-0000-0000-0000-000000000001.jpg'});return
   if path.startswith('/private/photos/'):request.fulfill(body=jpeg,content_type='image/jpeg');return
   assert request.request.method=='GET',path
   file=ROOT/'assets'/(path.lstrip('/') or 'index.html')
   if file.is_file():request.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:request.fulfill(status=404,body='Missing')
  page.route('**/*',route);page.goto('https://toolbar.test/');page.wait_for_function('window.BrowserTransport&&window.LayerEditor')
  with page.expect_file_chooser() as chooser:page.locator('#addFirst').click()
  chooser.value.set_files({'name':'synthetic.jpg','mimeType':'image/jpeg','buffer':jpeg});page.wait_for_function('state.photos.length===1&&images.has(state.photos[0].src)');page.wait_for_timeout(150)
  def geometry():return page.evaluate("""()=>{const rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom};};const add=$('addMore'),r=add.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return{bar:rect(document.querySelector('.photo-tools')),workspace:rect(document.querySelector('.workspace')),photos:rect($('photos')),hit:!!hit&&!!hit.closest('#addMore'),saved:localStorage.getItem('liuying-toolbar-position')};}""")
  first=geometry();assert first['hit'],(width,height,first)
  assert first['bar']['bottom']<=first['workspace']['bottom']+1 and first['bar']['right']<=first['workspace']['right']+1,(width,height,first)
  with page.expect_file_chooser() as picker:page.locator('#addMore').click()
  picker.value.set_files([])
  page.locator('#layoutBtn').click();page.wait_for_timeout(120)
  opened=geometry();assert opened['bar']['right']<=opened['workspace']['right']+1,(width,height,opened)
  if not mobile:page.locator('#menuBtn').click()
  page.locator('#closeSheet').click();page.wait_for_timeout(100)
  start=page.locator('.photo-tools').bounding_box();x=start['x']+start['width']/2;y=start['y']+start['height']/2
  page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+20,max(80,y-100),steps=12);page.mouse.up();page.wait_for_timeout(120)
  manual=geometry();assert manual['saved'] and manual['hit'],(width,height,manual)
  page.set_viewport_size({'width':width,'height':height-20});page.wait_for_timeout(100);page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
  resized=geometry();assert abs(resized['bar']['x']-manual['bar']['x'])<2 and abs(resized['bar']['y']-manual['bar']['y'])<2,(width,height,manual,resized)
  page.reload();page.wait_for_function('state.photos.length===1&&images.has(state.photos[0].src)');page.wait_for_timeout(150);restored=geometry()
  assert restored['hit'] and restored['saved']==manual['saved'] and abs(restored['bar']['x']-manual['bar']['x'])<2 and abs(restored['bar']['y']-manual['bar']['y'])<2,(width,height,manual,restored)
  page.screenshot(path=f'/tmp/toolbar-visible-{width}.png');assert not errors,errors;context.close()
 browser.close()
print('PASS: visible-area default and plus hit-test, panel resize, manual drag and reload persistence on phone portrait, landscape and desktop')
