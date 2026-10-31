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
 for width,height in [(1280,720),(1440,900),(1920,1080)]:
  page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
  page.locator('#sampleBtn').click() if page.locator('#sampleBtn').is_visible() else None
  page.wait_for_function('state.photos.length>0');page.evaluate('CropEditor.render()')
  for scheme in ['dark','light']:
   page.emulate_media(color_scheme=scheme)
   workspace=page.locator('.workspace').bounding_box();dock=page.locator('.dock').bounding_box()
   assert workspace['width']>width*.60 and workspace['x']+workspace['width']<dock['x'],(workspace,dock)
   stage=page.locator('#paperStage').bounding_box()
   assert stage['x']>=workspace['x']-1 and stage['y']>=workspace['y']-1 and stage['y']+stage['height']<=workspace['y']+workspace['height']+1,(workspace,stage)
   for tool in ('layoutBtn','filterBtn','templateBtn','addTextQuick','addEmojiQuick'):
    page.locator('#'+tool).click()
    if tool=='templateBtn':page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===16")
    panel=page.locator('#sheet').bounding_box();assert panel['x']>=workspace['x']+workspace['width'],panel
    assert page.locator('#scrim').is_hidden()
    assert page.locator('.dock').is_visible()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.locator('#templateBtn').click();page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===16")
   page.locator('[data-template="studio-petal"]').click();page.wait_for_function("sheetKind==='templates'&&!document.querySelector('#sheet').hidden")
   page.screenshot(path=f'/tmp/liuying-desktop-{width}-{scheme}.png')
   page.locator('#printBtn').click();page.wait_for_function("sheetKind==='confirm'")
   assert not page.locator('#sheet').evaluate('(e)=>e.classList.contains("desktop-inspector")')
   assert page.locator('#scrim').is_visible();page.locator('#closeSheet').click()
   page.wait_for_function("sheetKind==='templates'")
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(150)
 assert not page.locator('body').evaluate('(e)=>e.classList.contains("desktop-editor")')
 assert page.locator('#sheet').is_hidden()
 dock=page.locator('.dock').bounding_box();assert dock['y']>750 and dock['width']<=390
 page.locator('#templateBtn').click();assert page.locator('#scrim').is_visible();assert page.locator('#sheet').get_attribute('aria-modal')=='true'
 assert not errors,errors
 print('PASS: desktop two-column width, stable preview, all five nonmodal tools, templates stay open, print modal, mobile resize; no printing')
 b.close()
