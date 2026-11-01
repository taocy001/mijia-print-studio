from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
assets=Path(__file__).resolve().parents[1]/'assets'
with sync_playwright() as p:
 b=p.chromium.launch()
 for width,height in [(411,828),(844,390),(1440,900)]:
  page=b.new_page(viewport={'width':width,'height':height},has_touch=width<1000,is_mobile=width<1000)
  def route(r):
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'device':{},'history':[]});return
   f=assets/(name.lstrip('/') or 'index.html')
   if f.is_file():r.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')
  page.evaluate("async()=>{const photo={src:'/sample.svg',turn:0,zoom:1,x:0,y:0,fit:'cover',filter:'none',overlays:[]};await loadPhoto(photo);state={...defaults,media:5009,photos:[photo],active:0};render();}")
  page.wait_for_timeout(200);before=page.locator('#preview').bounding_box();toolbar=page.locator('.photo-tools').bounding_box()
  for kind in ['emoji','text']:
   page.evaluate("kind=>{LayerEditor.create({kind,text:kind==='text'?'hello':'🌷'});render();}",kind);page.wait_for_timeout(100)
   selected=page.locator('#preview').bounding_box();tools=page.locator('.photo-tools').bounding_box()
   assert all(abs(toolbar[k]-tools[k])<1 for k in ['x','y','width','height']),(toolbar,tools)
   assert page.locator('#photoTools').is_hidden() and page.locator('#layerTools').is_visible()
   assert page.locator('#editLayer').get_attribute('aria-label')=='编辑' and page.locator('#layerTools button svg').count()==5
   assert all(abs(before[k]-selected[k])<1 for k in ['x','y','width','height']),(width,before,selected)
   page.evaluate('LayerEditor.select(null);render()');page.wait_for_timeout(100)
   assert abs(page.locator('#preview').bounding_box()['y']-before['y'])<1
  page.evaluate("LayerEditor.select(LayerEditor.list()[0].id)")
  rect=page.locator('#deleteLayer').bounding_box();x=rect['x']+rect['width']/2;y=rect['y']+rect['height']/2
  count=page.evaluate('LayerEditor.list().length')
  session=page.context.new_cdp_session(page)
  session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
  for i in range(1,9):session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-20*i/8,'y':y-35*i/8,'id':1}]});page.wait_for_timeout(20)
  session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(100)
  moved=page.locator('.photo-tools').bounding_box();assert moved['y']<toolbar['y']-10
  assert page.evaluate('LayerEditor.list().length')==count,'Dragging from delete icon must not delete'
  page.evaluate('LayerEditor.select(null)');page.wait_for_timeout(100)
  assert abs(page.locator('.photo-tools').bounding_box()['y']-moved['y'])<1
  assert abs(page.locator('#preview').bounding_box()['y']-before['y'])<1
  if width==411:
   rect=page.locator('#zoomIn').bounding_box();x=rect['x']+rect['width']/2;y=rect['y']+rect['height']/2
   session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
   for i in range(1,9):session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y+(height-90-y)*i/8,'id':1}]});page.wait_for_timeout(20)
   session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(100)
   moved=page.locator('.photo-tools').bounding_box();photo=page.locator('#preview').bounding_box()
   assert moved['y']>photo['y']+photo['height'],'Toolbar must move below the photo'
   assert moved['y']+moved['height']<=page.locator('.dock').bounding_box()['y']
   page.evaluate('LayerEditor.select(LayerEditor.list()[0].id)');assert abs(page.locator('.photo-tools').bounding_box()['y']-moved['y'])<1
  page.locator('#menuBtn').click();page.locator('#menuDevice').click();assert page.locator('#changePaper').count()==0;assert page.locator('#sheetTitle').inner_text()=='打印机与连接'
  page.locator('#settingsBack').click();assert page.evaluate("sheetKind==='menu'")
  page.close()
 page=b.new_page(viewport={'width':1200,'height':1000});page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')
 page.evaluate("""async()=>{const photo={src:'/sample.svg',turn:0,zoom:1,x:0,y:0,fit:'cover',filter:'none'};await loadPhoto(photo);const out=document.createElement('canvas');out.width=1200;out.height=1100;const ctx=out.getContext('2d');ctx.fillStyle='#ddd';ctx.fillRect(0,0,1200,1100);const styles=['botanical','film','postcard','petal','constellation','confetti'];for(let i=0;i<6;i++){const t=TEMPLATE_CATALOG.find(t=>t.style===styles[i]);for(let j=0;j<3;j++){const sizes=[[340,220],[220,300],[220,220]], [w,h]=sizes[j],x=i%3*400+30,y=Math.floor(i/3)*550+j*170;ctx.save();ctx.translate(x,y);const scale=150/h;ctx.scale(scale,scale);OriginalTemplates.paint(ctx,photo,0,0,w,h,OriginalTemplates.variant(t,w,h));ctx.restore();}}document.body.replaceChildren(out);document.body.style='margin:0;background:#ddd';}""")
 page.screenshot(path='/tmp/liuying-template-126.png',full_page=True)
 print('PASS: shared draggable icon toolbar, no accidental delete, stable selection on phone, landscape and desktop; nested settings return; 18 template variants rendered')
 b.close()
