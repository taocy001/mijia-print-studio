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
 page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.wait_for_function('window.BrowserTransport&&window.TemplateStudio');page.evaluate('LayerEditor.ready')
 for width,height in [(1440,900),(1280,720),(411,828),(390,700)]:
  page.set_viewport_size({'width':width,'height':height})
  for scheme in ['dark','light']:
   page.emulate_media(color_scheme=scheme)
   page.evaluate("closeSheet();state.photos=[];state.mode='photo';state.media=5012;render()")
   page.wait_for_timeout(100)
   before=page.locator('#photos').bounding_box();dock=page.locator('.dock').bounding_box()
   if width<1000:assert abs(before['y']+before['height']-dock['y'])<3,(width,scheme,before,dock)
   page.locator('#sampleBtn').click();page.wait_for_function('state.photos.length===1');page.wait_for_timeout(100)
   after=page.locator('#photos').bounding_box();assert abs(after['y']-before['y'])<2,(width,before,after)
   for id in ['layoutBtn','filterBtn','templateBtn','addTextQuick','addEmojiQuick']:
    box=page.locator('#'+id).bounding_box();assert box and box['y']>=0 and box['y']+box['height']<=height+1,(id,box)
   page.locator('#templateBtn').click();page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===16")
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.evaluate('closeSheet()');page.locator('#addTextQuick').click()
   assert page.evaluate('active().overlays.length')==0
   page.locator('#layerText').fill('测试文字');page.keyboard.press('Backspace');assert page.locator('#layerText').input_value()=='测试文';page.wait_for_timeout(100);page.evaluate('closeSheet()');page.locator('body').click(position={'x':2,'y':2});page.keyboard.press('Delete')
   # Clicking the header does not select another photo or object.
   assert page.evaluate('active().overlays.length')==0
   page.locator('#addEmojiQuick').click();assert '添加文字' not in page.locator('#sheetBody').inner_text()
   assert page.locator('.emoji-grid img').count()==60
   scroll=page.locator('#sheetBody').evaluate('(e)=>{e.scrollTop=e.scrollHeight;return [e.scrollTop,e.scrollHeight,e.clientHeight]}');assert scroll[0]>0,scroll
   page.locator('#sheetBody').evaluate('(e)=>e.scrollTop=0');page.locator('[data-emoji]').first.click();page.keyboard.press('Delete');assert page.evaluate('active().overlays.length')==0
   page.evaluate('closeSheet()');page.screenshot(path=f'/tmp/liuying-layout-{width}-{scheme}.png')
 assert not errors,errors
 print('PASS: four viewport sizes, dark/light themes, fixed picker/dock, five visible tools, text starts empty, Delete and scrollable emoji; no printing')
 b.close()
