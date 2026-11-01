"""Keep mobile thumbnails above changing print status banners."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for native in [True,False]:
  page=browser.new_page(viewport={'width':411,'height':828});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  if native:page.add_init_script("window.Studio={landscape:()=>innerWidth>innerHeight,state:()=>'{\"device\":{},\"history\":[]}'}")
  def route(r):
   assert r.request.method=='GET','Layout tests must not print'
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'device':{},'history':[]});return
   file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('**/*',route);page.goto('https://studio.test/')
  page.wait_for_function('window.TemplateStudio&&window.CropEditor')
  page.evaluate("poll=()=>{};closeSheet()")
  for width,height in [(411,828),(828,411),(411,828),(390,700),(1440,900)]:
   page.set_viewport_size({'width':width,'height':height})
   for count in [0,1,6]:
    page.evaluate("async n=>{await loadPhoto({src:'/sample.svg'});state={...defaults,photos:Array.from({length:n},()=>({src:'/sample.svg',overlays:[]})),active:0};render()}",count)
    for message in ['', '正在打印', '打印完成，留住这一刻。', '通讯中断，请检查打印机状态后重试。'*5, '']:
     page.evaluate("s=>{document.getElementById('jobBanner').hidden=!s;document.getElementById('jobLabel').textContent=s}",message)
     page.wait_for_timeout(80)
     if width<height:
      bounds=page.evaluate("""()=>{const d=document.querySelector('.dock').getBoundingClientRect();return {dock:d.toJSON(),nodes:[...document.querySelectorAll('#photos,.photo-thumb,.add-photo')].map(e=>e.getBoundingClientRect().toJSON()),height:innerHeight}}""")
      assert all(r['bottom']<=bounds['dock']['top']+1 for r in bounds['nodes']),(native,count,message,bounds)
      assert bounds['dock']['bottom']<=height+1,bounds
     for id in ['layoutBtn','filterBtn','templateBtn','addTextQuick','addEmojiQuick']:
      box=page.locator('#'+id).bounding_box()
      assert box and box['y']>=0 and box['y']+box['height']<=height+1,(native,width,count,message,id,box)
  assert not errors,errors
  page.close()
 browser.close()
print('PASS: native/web dock banners, 0/1/6 photos, portrait/landscape/desktop; no printing')
