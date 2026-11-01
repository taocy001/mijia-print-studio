"""Paper reference never changes print pixels or drawer geometry."""
import json,mimetypes,time
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width,height,theme in [(390,844,'dark'),(844,390,'light'),(1440,1000,'light')]:
  page=browser.new_page(viewport={'width':width,'height':height},color_scheme=theme,has_touch=True);errors=[];media=[5009]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'permission':True,'device':{'connected':True,'media':5012 if media[0]==5014 else media[0],'checkedAt':int(time.time()*1000)},'history':[]});return
   if name.startswith('/api/') and r.request.method!='GET':raise AssertionError('Preview must not submit')
   file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('https://studio.test/**',route);page.goto('https://studio.test/')
  page.wait_for_function('window.PaperPreview&&window.TemplateStudio&&window.StudioExtras')
  page.evaluate('LayerEditor.ready');page.locator('#sampleBtn').click();page.wait_for_function('ready()')
  page.evaluate("window.fixtureMedia=5009;Studio.state=()=>JSON.stringify({permission:true,device:{connected:true,media:window.fixtureMedia===5014?5012:window.fixtureMedia,checkedAt:Date.now()},history:[]})")
  for paper,orientation in [(5009,'portrait'),(5012,'portrait'),(5012,'landscape'),(5014,'portrait')]:
   media[0]=paper
   page.evaluate('([paper,orientation])=>{closeSheet();window.fixtureMedia=paper;state.media=paper;state.sixLayout=paper;state.orientation=orientation;native.device={connected:true,media:paper===5014?5012:paper,checkedAt:Date.now()};active().coatTexture="grid";render()}',[paper,orientation])
   page.evaluate('confirmPrint()');page.locator('.paper-reference-controls').first.wait_for()
   original=page.evaluate('JSON.stringify(pendingPrint.pages)');frame=page.locator('.confirmation-preview').first;bounds=frame.bounding_box()
   button=page.get_by_role('button',name='纸面参考',exact=True).first;button.hover();page.mouse.down()
   page.wait_for_function("document.querySelector('.paper-reference .paper-reference-pattern')")
   assert page.locator('.paper-reference-note').count()==0 and page.get_by_role('button',name='原稿',exact=True).count()==0
   assert page.evaluate('JSON.stringify(pendingPrint.pages)')==original
   assert page.evaluate('preparePrintPages().then(p=>JSON.stringify(p))')==original
   after=frame.bounding_box();assert all(abs(bounds[k]-after[k])<1 for k in ['width','height']), (bounds,after)
   layer=page.locator('.paper-reference-pattern').first.bounding_box();assert layer['width']<=after['width']+1 and layer['height']<=after['height']+1
   if paper==5009:page.screenshot(path=f'/tmp/paper-preview-{width}.png')
   page.mouse.move(1,1);page.mouse.up();assert page.locator('.paper-reference').count()==0
   assert page.evaluate('JSON.stringify(pendingPrint.pages)')==original
  button.focus();page.keyboard.down('Space');assert page.locator('.paper-reference').count()==1
  page.keyboard.up('Space');assert page.locator('.paper-reference').count()==0
  button.hover();page.mouse.down();button.dispatch_event('pointercancel');assert page.locator('.paper-reference').count()==0;page.mouse.up()
  button.hover();page.mouse.down();page.evaluate("window.dispatchEvent(new Event('blur'))");assert page.locator('.paper-reference').count()==0;page.mouse.up()
  # Real touch capture must release outside the button or on OS cancellation.
  client=page.context.new_cdp_session(page)
  for end in ['touchEnd','touchCancel']:
   button.scroll_into_view_if_needed();box=button.bounding_box()
   client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':box['x']+box['width']/2,'y':box['y']+box['height']/2,'id':1}]})
   page.wait_for_timeout(650)
   assert page.locator('.paper-reference').count()==1
   assert not page.locator('#imageSaveDialog').is_visible(),'Holding paper reference must not save the image'
   client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':2,'y':2,'id':1}]})
   client.send('Input.dispatchTouchEvent',{'type':end,'touchPoints':[]})
   assert page.locator('.paper-reference').count()==0,end
   assert not page.locator('#imageSaveDialog').is_visible()
   assert page.evaluate('JSON.stringify(pendingPrint.pages)')==original
  assert not errors,errors;page.close()
 browser.close()
print('PASS: paper reference preserves JPEG/OC and layout for square, portrait, landscape, splice across three viewports; no printing')
