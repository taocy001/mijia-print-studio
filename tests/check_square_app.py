from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse,unquote
import mimetypes,io,json,random,sys
from PIL import Image
root=Path(__file__).resolve().parents[1];assets=root/'assets'

with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':411,'height':828},is_mobile=True,has_touch=True);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{connected:true,media:5009},history:[]}),printBatch:()=>{throw Error('Printing is forbidden in tests')}}")
 def route(r):
  path=unquote(urlparse(r.request.url).path);file=assets/(path.lstrip('/') or 'index.html')
  if path.startswith('/private/'):
   buf=io.BytesIO();Image.new('RGB',(800,1200),'#387fa0').save(buf,'JPEG');r.fulfill(body=buf.getvalue(),content_type='image/jpeg');return
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing asset')
 page.route('https://studio.local/**',route);page.goto('https://studio.local/');page.wait_for_function('window.LayerEditor&&window.CropEditor&&window.StudioExtras');page.evaluate('LayerEditor.ready')
 page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});state={...defaults,photos:Array.from({length:3},()=>({src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0,fit:'cover',border:0,filter:'none',templateId:null,overlays:[]})),active:0};render();}")

 page.evaluate("state.media=5009;render();openPaper()")
 assert page.locator('[data-paper]').count()==0
 assert '3 寸方形背胶纸' in page.locator('#sheetTitle').inner_text()
 assert page.evaluate("logicalSize()") == [1040,1040]
 page.evaluate("closeSheet()")
 result=page.evaluate("""async()=>{
 const pages=await preparePrintPages();
 const sizes=[];
 for(const p of pages){const im=new Image();im.src='data:image/jpeg;base64,'+p.base64;await im.decode();sizes.push([im.width,im.height,p.media,p.orientation]);}
 const src=document.createElement('canvas');src.width=src.height=1040;const c=src.getContext('2d');c.fillStyle='red';c.fillRect(0,0,1040,520);c.fillStyle='blue';c.fillRect(0,520,1040,520);
 const out=physical(src).getContext('2d');
 return {sizes,top:Array.from(out.getImageData(0,0,1,1).data),bottom:Array.from(out.getImageData(0,1039,1,1).data)};
 }""")
 assert result['sizes']==[[1040,1040,5009,'square']]*3,result
 assert result['top']==[0,0,255,255] and result['bottom']==[255,0,0,255],result
 assert not errors,errors
 print('Square App: paper picker, three-page JPEG dimensions, media ID, square caption and physical rotation passed')
 b.close()
