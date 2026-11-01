"""Layout thumbnails match the selected composition without changing the draft."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
assets=Path(__file__).resolve().parents[1]/'assets'
with sync_playwright() as p:
 browser=p.chromium.launch()
 for native,width,height in [(True,390,700),(False,390,700),(False,844,390),(False,1440,900)]:
  page=browser.new_page(viewport={'width':width,'height':height});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script("Object.defineProperty(screen.orientation,'type',{get:()=>innerWidth>innerHeight?'landscape-primary':'portrait-primary'})")
  if native:page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{},history:[]})}")
  def route(r):
   assert r.request.method=='GET'
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'permission':True,'device':{},'history':[]});return
   file=assets/(name.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')
  page.evaluate("async()=>{closeSheet();state={...defaults,photos:[],active:0};openLayout();await paintLayoutFitChoices();}")
  assert page.evaluate('state.photos.length')==0
  assert page.evaluate("()=>{const c=document.querySelector('.layout-fit-grid canvas');return new Set(c.getContext('2d').getImageData(0,0,c.width,c.height).data).size>10}")
  for media,orientation in [(5009,'portrait'),(5012,'portrait'),(5012,'landscape'),(5014,'portrait')]:
   for fit in ['cover','contain','bottom']:
    page.evaluate('''async({media,orientation})=>{closeSheet();const photo={src:'/sample.svg',turn:0,zoom:1.2,x:.1,y:-.1,fit:'cover',border:0,filter:'sepia',overlays:[{id:'fixture',kind:'text',text:'TEST',fx:.5,fy:.5,sizePct:32,angle:0,font:'sans',color:'#ffffff',bubble:'#ff0000',stroke:'',align:'center',hidden:false}]};await loadPhoto(photo);state={...defaults,mode:'photo',media,sixLayout:media,orientation,photos:[photo],active:0};render();window.beforeLayout=JSON.stringify(state);window.beforeFrames=photoFrames;window.beforeComposing=composingFrames;openLayout();await paintLayoutFitChoices();}''',{'media':media,'orientation':orientation})
    assert page.evaluate('JSON.stringify(state)===beforeLayout&&photoFrames===beforeFrames&&composingFrames===beforeComposing')
    buttons=page.locator('.layout-fit-grid button');assert buttons.count()==3
    boxes=[buttons.nth(i).bounding_box() for i in range(3)];assert max(r['y'] for r in boxes)-min(r['y'] for r in boxes)<1
    selector='.layout-fit-grid [data-value='+fit+']'
    page.locator(selector).evaluate("b=>{const c=b.querySelector('canvas');window.expectedFit={w:c.width,h:c.height,pixels:c.getContext('2d').getImageData(0,0,c.width,c.height).data}}")
    page.locator(selector).click();page.wait_for_timeout(70)
    assert page.evaluate("sheetKind==='layout'") and page.locator(selector).get_attribute('aria-pressed')=='true'
    error=page.evaluate('''()=>{const full=compose(),c=document.createElement('canvas');c.width=expectedFit.w;c.height=expectedFit.h;const ctx=c.getContext('2d');ctx.drawImage(full,0,0,full.width,state.media===5014?full.height/2:full.height,0,0,c.width,c.height);const pixels=ctx.getImageData(0,0,c.width,c.height).data;let error=0;for(let i=0;i<pixels.length;i++)error+=Math.abs(pixels[i]-expectedFit.pixels[i]);const box=data=>{let x0=c.width,y0=c.height,x1=-1,y1=-1;for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const i=(y*c.width+x)*4;if(data[i]>200&&data[i+1]<60&&data[i+2]<60){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}}return [x0,y0,x1,y1];};return {mean:error/pixels.length,expected:box(expectedFit.pixels),actual:box(pixels)};}''')
    assert error['mean']<10 and all(abs(a-b)<=1 for a,b in zip(error['expected'],error['actual'])),(native,width,media,orientation,fit,error)
   if media==5012 and orientation=='landscape':page.screenshot(path='/tmp/layout-previews-'+str(width)+'-'+str(native)+'.png')
  before=page.locator('.layout-fit-grid [data-value=bottom] canvas').evaluate('(c)=>c.toDataURL()')
  page.locator('#borderInput').focus();page.keyboard.press('End');page.wait_for_timeout(100)
  assert page.evaluate('active().border')==200
  assert page.locator('.layout-fit-grid [data-value=bottom] canvas').evaluate('(c)=>c.toDataURL()')!=before
  assert page.evaluate("sheetKind==='layout'")
  page.evaluate("async()=>{active().templateId=TEMPLATE_CATALOG[0].id;active().border=96;state.mode='template';state.templateId=active().templateId;render();openLayout();await paintLayoutFitChoices()}")
  page.locator('.layout-fit-grid [data-value=bottom]').click();assert page.evaluate("state.mode==='photo'&&!active().templateId&&active().border===96&&active().zoom===1")
  assert not errors,errors;page.close()
 browser.close()
print('PASS: three-column layout previews match composition across papers, orientation, filter, zoom and empty state; no printing')
