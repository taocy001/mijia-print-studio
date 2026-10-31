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

 page.evaluate("async()=>{await loadPhoto({src:'/private/photos/a.jpg'});state.photos=[{src:'/private/photos/a.jpg',width:800,height:1200,turn:0,zoom:2,x:.4,y:.3,fit:'cover',border:0,overlays:[]},{src:'/private/photos/a.jpg',width:800,height:1200,turn:0,zoom:1,x:0,y:0,fit:'cover',border:0,overlays:[]}];state.active=0;state.mode='photo';}")
 page.evaluate('openLayout()')
 page.locator('[data-setting="fit"][data-value="bottom"]').click()
 assert page.evaluate("active().fit==='bottom'&&active().zoom===1&&active().border===78&&!active().x&&!active().y")
 assert page.evaluate("state.photos[1].fit==='cover'&&state.photos[1].border===0")
 assert page.locator('#borderInput').get_attribute('max')=='200'
 for media in [5009,5012,5014]:
  for orientation in ['portrait','landscape']:
   for margin in [0,78,200]:
    result=page.evaluate("""([media,orientation,margin])=>{
     state.media=media;state.orientation=orientation;state.mode='photo';state.active=0;active().border=state.border=margin;state.fit=active().fit='bottom';
     render();const [w,h]=logicalSize(),areaH=media===5014?h/2:h,f=photoFrames[0],g=photoGeometry(f.p,f.w,f.h,f.fit),c=compose(false),ctx=c.getContext('2d');
     const bottom=Array.from(ctx.getImageData(0,areaH-1,w,1).data);return {w,h,areaH,frame:[f.x,f.y,f.w,f.h],dw:g.dw,dh:g.dh,bottom:bottom.every((v,i)=>i%4===3||v===255)};
    }""",[media,orientation,margin])
    assert result['frame']==[0,0,result['w'],result['areaH']-margin],result
    assert result['dw']<=result['w']+.001 and result['dh']<=result['areaH']-margin+.001,result
    if margin:assert result['bottom'],result
    pages=page.evaluate("async()=>{const ps=await preparePrintPages();return await Promise.all(ps.map(async p=>{const im=new Image();im.src='data:image/jpeg;base64,'+p.base64;await im.decode();return [im.width,im.height,p.media]}))}")
    assert len(pages)==(1 if media==5014 else 2),pages
    assert all(p==([1040,1040,5009] if media==5009 else [1216,1824,media]) for p in pages),pages
 page.evaluate("state.media=5012;state.orientation='portrait';selectPhoto(0);state.mode='template';active().templateId='studio-film';openLayout()")
 page.locator('[data-setting=fit][data-value=bottom]').click()
 assert page.evaluate("state.mode==='photo'&&!active().templateId")
 assert page.locator('#borderInput').count()==1
 assert '底部留白' in page.locator('#layoutSummary').inner_text()
 page.locator('#borderInput').fill('200');page.locator('#borderInput').dispatch_event('input')
 assert page.evaluate('active().border===200&&state.photos[1].border===0')
 page.evaluate("changeSetting('fit','contain');render()")
 assert page.evaluate('photoFrames[0].x===200&&photoFrames[0].y===200')
 page.evaluate("selectPhoto(1);openLayout()")
 assert page.locator('#borderInput').input_value()=='0'
 page.evaluate("selectPhoto(0);changeSetting('fit','bottom');save()")
 page.reload();page.wait_for_function("images.size>0&&state.photos.length===2")
 assert page.evaluate("state.photos[0].fit==='bottom'&&state.photos[0].border===200&&state.photos[1].fit==='cover'")
 assert not errors,errors
 print('PASS: full-photo bottom margin, 0–200px, three papers, orientations, per-photo isolation, export dimensions and draft reload; no printing')
 b.close()
