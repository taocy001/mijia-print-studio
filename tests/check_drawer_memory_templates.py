"""Remember choice drawers and reuse only current, bounded template thumbnails."""
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

 page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});const p={src:'/sample.svg',filter:'fresh',fit:'cover',zoom:1,x:0,y:0,turn:0,overlays:[],templateId:'studio-festival'};state={...defaults,mode:'template',media:5012,orientation:'portrait',photos:[{...p},{...p}],active:0};render();}")
 page.evaluate('TemplateStudio.open()')
 assert page.evaluate("(()=>{const r=document.querySelector('[data-template=studio-festival]').getBoundingClientRect(),b=$('sheetBody').getBoundingClientRect();return r.top>=b.top-1&&r.bottom<=b.bottom+1})()"),'First selected template must be visible'
 page.locator('#sheetHandle').click();page.wait_for_timeout(220)
 page.evaluate("$('sheetBody').scrollTop=330")
 height=page.evaluate('Drawer.height()');scroll=page.evaluate("$('sheetBody').scrollTop")
 page.evaluate('openFilters()');page.wait_for_timeout(60)
 assert page.evaluate('Drawer.height()')<height
 page.evaluate('closeSheet();TemplateStudio.open()');page.wait_for_timeout(60)
 assert abs(page.evaluate('Drawer.height()')-height)<1
 assert abs(page.evaluate("$('sheetBody').scrollTop")-scroll)<1
 page.evaluate("state.active=1;active().templateId='studio-kids-dino';TemplateStudio.open()")
 assert page.locator('[data-template=studio-kids-dino]').get_attribute('aria-pressed')=='true'
 assert abs(page.evaluate("$('sheetBody').scrollTop")-scroll)<1,'Switching photo must not jump to selection'
 page.evaluate('closeSheet();openLayout()');page.wait_for_timeout(60)
 assert page.evaluate('Drawer.height()')<height
 page.locator('#sheetHandle').click();page.wait_for_timeout(200)
 layoutheight=page.evaluate('Drawer.height()');page.evaluate('closeSheet();openFilters()');page.wait_for_timeout(60)
 assert page.evaluate('Drawer.height()')<layoutheight
 page.evaluate('closeSheet();openLayout()');assert abs(page.evaluate('Drawer.height()')-layoutheight)<1
 # Only unchanged thumbnails are reused; a crop change invalidates all cards.
 result=page.evaluate("""async()=>{
  closeSheet();await TemplateStudio.open();let paints=[];const original=OriginalTemplates.paint;OriginalTemplates.paint=function(...args){paints.push(args[7]?.style||args[6]?.style);return original.apply(this,args);};
  await TemplateStudio.open();const warm=paints.length;paints=[];active().x=.27;await TemplateStudio.open();const changed=paints.length,first=paints[0];
  for(const x of [.1,.2,.3,.4]){active().x=x;await TemplateStudio.open();}
  paints=[];active().x=.27;await TemplateStudio.open();const evicted=paints.length;
  paints=[];active().x=.57;const obsolete=TemplateStudio.open();requestAnimationFrame(()=>active().x=.58);await obsolete;const cancelled=paints.length;
  const order=[...$('sheetBody').querySelectorAll('[data-template]')].map(b=>b.dataset.template);OriginalTemplates.paint=original;
  return {warm,changed,first,evicted,cancelled,order:order.join()===TEMPLATE_CATALOG.map(t=>t.id).join()};
 }""")
 assert result['warm']==0,result
 assert result['changed']==35 and result['first']=='kids-dino' and result['order'],result
 assert result['evicted']==35 and result['cancelled']==0,result
 assert not errors,errors
 browser.close()
print('PASS: per-panel height/scroll, first selected card reveal, no photo-switch jump, bounded thumbnail cache reuse/invalidation and selected-first painting without reordering')
