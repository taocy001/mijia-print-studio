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

 page.evaluate('Promise.all([NameLabels.ready,CardArt.ready,LayerEditor.ready])')
 page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});state.photos=[{src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0,fit:'cover',border:0,filter:'none',templateId:null,overlays:[]}];state.media=5012;}")
 page.evaluate("async()=>{const p={src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0,fit:'cover',border:0,filter:'none',templateId:null,overlays:[]};state.photos=[{...p},{...p},{...p}];await loadPhoto(p);state.active=0;state.mode='photo';}")
 for media,ratio in [(5009,1),(5012,2/3),(5014,4/3)]:
  page.evaluate('(m)=>{state.media=m;state.orientation="portrait";selectPhoto(0);render()}',media)
  page.locator('#templateBtn').click();page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===16")
  actual=page.locator('[data-template] img').first.evaluate('(im)=>im.naturalWidth/im.naturalHeight')
  assert abs(actual-ratio)<.01,(media,actual)
  assert page.locator('#templateOrientation').count()==(1 if media==5012 else 0)
  page.locator('[data-template="studio-film"]').click();page.wait_for_function("active().templateId==='studio-film'")
  page.evaluate('render()');assert page.evaluate('photoFrames[0].x')>0
  pages=page.evaluate('async()=>{const ps=await preparePrintPages();return await Promise.all(ps.map(async p=>{const im=new Image();im.src="data:image/jpeg;base64,"+p.base64;await im.decode();return [im.width,im.height,p.media]}))}')
  assert len(pages)==(2 if media==5014 else 3),pages
  assert all(p==([1040,1040,5009] if media==5009 else [1216,1824,media]) for p in pages),pages
 page.evaluate("state.media=5014;selectPhoto(1);render()")
 page.locator('#templateBtn').click();page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===16");page.locator('[data-template="studio-petal"]').click();page.evaluate('render()')
 frames=page.evaluate('photoFrames.map(f=>({x:f.x,y:f.y,w:f.w,h:f.h}))')
 assert len(frames)==2 and frames[0]['y']<912 and frames[1]['y']>=912,frames
 assert frames[1]['y']+frames[1]['h']<=1824,frames
 # Selecting either half must not apply its frame to the other half.
 one=page.evaluate('compose().toDataURL()');page.evaluate('selectPhoto(0);render()');two=page.evaluate('compose().toDataURL()');assert one==two
 page.locator('#templateBtn').click();page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===16");page.locator('#noTemplate').click();page.evaluate('render()')
 assert page.evaluate('state.photos.map(p=>p.templateId)')==[None,'studio-petal',None]
 frames=page.evaluate('photoFrames.map(f=>[f.x,f.y,f.w,f.h])');assert frames[0]==[0,0,1216,912] and frames[1][1]>912,frames
 # Paper changes preserve each photo's choice.
 page.evaluate('native.device={connected:true,checkedAt:Date.now(),media:5009};syncPaper();');page.evaluate('selectPhoto(1);render()');assert page.evaluate('state.mode')=='template'
 assert page.evaluate('TemplateStudio.entry().width===1040&&TemplateStudio.entry().height===1040')
 page.screenshot(path='/tmp/liuying-square-template.png')
 assert not errors,errors
 print('PASS: three paper sizes, correct thumbnail ratios, per-photo splice templates, crop bounds, mixed plain/frame pages and print dimensions; no printing')
 b.close()
