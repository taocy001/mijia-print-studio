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

 page.evaluate("state.photos=[];state.mode='photo';native.device={};state.media=5012")
 page.evaluate("addPhotos([{src:'/private/photos/a.jpg',faces:[[.3,.02,.5,.1]]},{src:'/private/photos/b.jpg',faces:[[.3,.02,.5,.1]]}])")
 assert page.evaluate('state.photos.every(p=>p.facePending&&p.y===0)')
 page.evaluate("selectPhoto(1);$('zoomIn').click();native.device={connected:true,checkedAt:Date.now(),media:5009};syncPaper()")
 assert page.evaluate('state.photos[0].y>0.5&&!state.photos[0].facePending'),page.evaluate('state.photos')
 assert page.evaluate('state.photos[1].zoom>1&&state.photos[1].y===0&&!state.photos[1].facePending')
 page.evaluate("selectPhoto(0);openFilters();$('toneSharp').value=1;$('toneSharp').dispatchEvent(new Event('change'))")
 assert page.evaluate('state.photos[0].sharpen===1&&state.photos[1].sharpen===0')
 assert page.evaluate('(async()=> (await preparePrintPages()).map(p=>p.sharpen))()')==[1,0]
 page.evaluate("state.media=5014;openFilters()")
 assert '第一幅' in page.locator('#sheetBody').inner_text()
 assert page.evaluate('(async()=> (await preparePrintPages()).map(p=>p.sharpen))()')==[1]
 page.evaluate("state.media=5012;state.mode='collage'")
 assert page.evaluate('(async()=> (await preparePrintPages()).map(p=>p.sharpen))()')==[1]
 page.evaluate("state.mode='idcard';state.photos.push({...state.photos[0],src:'/private/photos/c.jpg',sharpen:2});loadPhoto(state.photos[2])")
 assert page.evaluate('(async()=> (await preparePrintPages()).map(p=>p.sharpen))()')==[1,2]
 page.evaluate("state.media=5009")
 assert page.evaluate('(async()=> (await preparePrintPages()).map(p=>p.sharpen))()')==[1,0,2]
 page.evaluate("state.sharpen=2;state.photos.forEach(p=>delete p.sharpen);save()")
 page.reload();page.wait_for_function('state.photos.length===3&&images.size===3')
 assert page.evaluate('state.photos.every(p=>p.sharpen===2)')
 assert not errors,errors
 print('PASS: per-photo sharpness, pair export, legacy migration, deferred face crop and manual crop protection; no printing')
 b.close()
