"""Selecting plain during an unfinished template preview must not strand empty cards."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch();page=browser.new_page(viewport={"width":390,"height":844},is_mobile=True,has_touch=True);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={state:()=>'{\"device\":{},\"history\":[]}',landscape:()=>false}")
 def route(r):
  assert r.request.method=='GET'
  url=urlparse(r.request.url);assert url.hostname=='studio.test'
  file=ROOT/'assets'/(url.path.lstrip('/') or 'index.html')
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing')
 page.route('**/*',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')


 page.context.new_cdp_session(page).send('Emulation.setCPUThrottlingRate',{'rate':4})
 page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});state={...defaults,mode:'template',fit:'contain',border:60,photos:[{src:'/sample.svg',fit:'contain',border:60,zoom:2,x:.3,y:.2,filter:'none',turn:0,overlays:[],templateId:'studio-kids-dino'}],active:0};render();}")
 page.evaluate('window.loadingTemplates=TemplateStudio.open();void 0')
 page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length>0")
 page.evaluate("window.originalGrid=$('sheetBody').querySelector('.template-grid');$('sheetBody').scrollTop=120;window.originalScroll=$('sheetBody').scrollTop;window.originalHeight=Drawer.height();$('noTemplate').click()")
 page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===35")
 result=page.evaluate("({count:document.querySelectorAll('[data-template] img[src]').length,selected:$('noTemplate').getAttribute('aria-pressed'),same:originalGrid===$('sheetBody').querySelector('.template-grid'),scroll:[$('sheetBody').scrollTop,originalScroll],height:[Drawer.height(),originalHeight],crop:[active().zoom,active().x,active().y,active().border]})")
 assert result['count']==35 and result['selected']=='true' and result['same'],result
 assert result['scroll'][0]==result['scroll'][1] and result['height'][0]==result['height'][1],result
 assert result['crop']==[1,0,0,0],result
 assert not errors,errors
 browser.close()
print('PASS: selecting plain during thumbnail loading restarts only thumbnail work; all cards complete, selection, grid, scroll and height retained')
