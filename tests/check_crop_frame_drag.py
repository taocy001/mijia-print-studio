from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse,unquote
import mimetypes,io,json,random,sys
from PIL import Image,ImageDraw
media=int(sys.argv[1]) if len(sys.argv)>1 else 5012
assert media in (5009,5012)
root=Path(__file__).resolve().parents[1];assets=root/'assets'

with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':411,'height':828},is_mobile=True,has_touch=True);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.testMedia="+str(media)+";window.Studio={state:()=>JSON.stringify({permission:true,device:{connected:true,checkedAt:Date.now(),media:testMedia},history:[]}),printBatch:()=>{throw Error('Printing is forbidden in tests')}}")
 def route(r):
  path=unquote(urlparse(r.request.url).path);file=assets/(path.lstrip('/') or 'index.html')
  if path.startswith('/private/'):
   buf=io.BytesIO();im=Image.new('RGB',(900,1800));draw=ImageDraw.Draw(im)
   for y in range(1800):draw.line((0,y,899,y),fill=(y*255//1800,80,255-y*255//1800))
   im.save(buf,'JPEG',quality=97);r.fulfill(body=buf.getvalue(),content_type='image/jpeg');return
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing asset')
 page.route('https://studio.local/**',route);page.goto('https://studio.local/');page.wait_for_function('window.LayerEditor&&window.CropEditor&&window.StudioExtras');page.evaluate('LayerEditor.ready')
 page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});state={...defaults,photos:Array.from({length:3},()=>({src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0,fit:'cover',border:0,filter:'none',templateId:null,overlays:[]})),active:0};render();}")


 page.evaluate("async()=>{const photo={src:'/private/photos/crop-test.jpg',turn:0,zoom:1,x:0,y:0,fit:'cover',filter:'none',overlays:[]};await loadPhoto(photo);state={...defaults,media:testMedia,photos:[photo],active:0};render();}")
 client=page.context.new_cdp_session(page)
 def touch(kind,x=None,y=None):
  client.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if x is None else [{'x':x,'y':y,'id':1}]})
 def drag(x,y,dx,dy):
  touch('touchStart',x,y)
  for i in range(1,9):touch('touchMove',x+dx*i/8,y+dy*i/8);page.wait_for_timeout(20)
  touch('touchEnd');page.wait_for_timeout(100)
 frame=page.evaluate("()=>{const c=$('preview').getBoundingClientRect(),v=CropEditor.geometry();return {x:c.x+v.tx*c.width/$('preview').width,y:c.y+v.ty*c.height/$('preview').height,h:v.paper.h*c.height/$('preview').height}}")
 color=lambda:page.evaluate("()=>{const c=compose();return c.getContext('2d').getImageData(c.width/2,c.height/2,1,1).data[0]}")
 old_color=color()
 before=page.evaluate("({y:active().y,scroll:document.querySelector('.workspace').scrollTop})")
 drag(frame['x']+6,frame['y']+frame['h']*.25,0,35)
 assert page.evaluate('active().y')<-.1,'Frame drag did not change crop at 1x'
 assert abs(page.evaluate("document.querySelector('.workspace').scrollTop")-before['scroll'])<2,'Frame drag scrolled workspace'
 after=page.evaluate("()=>{const c=$('preview').getBoundingClientRect(),v=CropEditor.geometry();return c.y+v.ty*c.height/$('preview').height}")
 assert abs(after-frame['y']-35)<3,(after,frame)
 assert color()>old_color+5,'Exported photo must follow the moved print region'
 # The crop uses the same offset as the exported composition.
 assert page.evaluate("photoGeometry(active(),photoFrames[0].w,photoFrames[0].h).dy")<0
 page.evaluate("active().zoom=2;active().x=0;active().y=0;render()")
 rect=page.locator('[data-crop-edge=top]').bounding_box()
 drag(rect['x']+rect['width']*.4,rect['y']+16,25,25)
 assert page.evaluate('active().x')<0 and page.evaluate('active().y')<0,'Zoomed frame needs both axes'
 # Drag the photo interior at 1x as well as the frame edge.
 page.evaluate("active().zoom=1;active().y=0;render();document.querySelector('.workspace').scrollTop=0")
 rect=page.locator('#preview').bounding_box();old=page.evaluate('active().y')
 drag(rect['x']+rect['width']/2,rect['y']+rect['height']*.45,0,-80)
 assert page.evaluate("document.querySelector('.workspace').scrollTop")==0,'Photo drag must not scroll'
 assert page.evaluate('active().y')>old,'Photo interior must move the crop at 1x'
 page.evaluate("state.mode='template';active().templateId=state.templateId='studio-confetti';active().x=active().y=0;render()")
 rect=page.locator('#preview').bounding_box();drag(rect['x']+rect['width']*.5,rect['y']+rect['height']*.4,0,-35)
 assert page.evaluate('active().y')<0,'Template photo must drag at 1x'
 page.evaluate("state.mode='photo';active().templateId=null;active().fit='contain';active().zoom=1;render();document.querySelector('.workspace').scrollTop=0")
 assert page.locator('#preview').evaluate("e=>getComputedStyle(e).touchAction")=='pan-y'
 assert not errors,errors
 print('PASS: real touch frame dragging at 1x and 2x, frame follows finger, crop offset changes, photo interior and template drag at 1x; uncropped photo keeps native scroll')
 b.close()
