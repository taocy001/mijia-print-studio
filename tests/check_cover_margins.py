"""Full bleed ignores legacy margins without changing other photo layouts."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
assets=Path(__file__).resolve().parents[1]/'assets'
with sync_playwright() as p:
 browser=p.chromium.launch();page=browser.new_page(viewport={'width':411,'height':828});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{},history:[]}),landscape:()=>false}")
 def route(r):
  assert r.request.method=='GET'
  file=assets/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing')
 page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')
 page.evaluate('''async()=>{const c=document.createElement('canvas');c.width=1200;c.height=800;const ctx=c.getContext('2d');ctx.fillStyle='#236ba4';ctx.fillRect(0,0,c.width,c.height);window.fixture={src:c.toDataURL(),turn:0,zoom:1,x:0,y:0,fit:'cover',border:78,filter:'none',overlays:[]};await loadPhoto(fixture);}''')
 def edges():return page.evaluate('''()=>{const c=compose(),ctx=c.getContext('2d'),h=state.media===5014?c.height/2:c.height,y=state.media===5014?state.active*h:0;return [[1,y+1],[c.width-2,y+1],[1,y+h-2],[c.width-2,y+h-2]].map(([x,y])=>Array.from(ctx.getImageData(x,y,1,1).data).slice(0,3));}''')
 for media in [5009,5012,5014]:
  page.evaluate('(media)=>{closeSheet();state={...defaults,mode:"photo",media,sixLayout:media,fit:"cover",border:78,photos:[{...fixture},{...fixture,border:96}],active:0};render();openLayout()}',media)
  assert all(color==[35,107,164] for color in edges()),(media,edges())
  assert page.locator('#layoutSummary').inner_text()=='铺满相纸' and page.locator('#borderInput').count()==0
  page.locator('[data-setting=fit][data-value=bottom]').click();assert page.evaluate('active().border')==78
  assert all(color==[255,255,255] for color in edges())
  page.locator('[data-setting=fit][data-value=cover]').click();assert page.evaluate('active().border===0&&state.border===0&&state.photos[1].border===96')
  assert all(color==[35,107,164] for color in edges())
  page.evaluate("async()=>{closeSheet();active().templateId=state.templateId=TEMPLATE_CATALOG[0].id;active().border=state.border=96;state.mode='template';await TemplateStudio.open()}")
  page.locator('#noTemplate').click();assert page.evaluate('active().border===0&&state.border===0')
  assert all(color==[35,107,164] for color in edges())
  page.evaluate("closeSheet();active().fit=state.fit='contain';active().border=state.border=78;render()")
  assert all(color==[255,255,255] for color in edges())
 page.evaluate("state.media=5014;state.mode='template';state.photos[0].templateId=TEMPLATE_CATALOG[0].id;state.photos[1].templateId=null;state.photos[1].fit='cover';state.active=1;render()")
 assert all(color==[35,107,164] for color in edges())
 page.evaluate("state.media=5012;state.mode='collage';state.border=78;state.photos.forEach(p=>{p.fit='cover';p.border=78;p.templateId=null});state.active=0;render();openLayout()")
 assert page.locator('#borderInput').count()==1 and all(color==[255,255,255] for color in edges())
 assert not errors,errors
 browser.close()
print('PASS: legacy full bleed, bottom-to-cover, no-template, per-photo margins, splice mixed templates and retained contain/collage margins; no printing')
