"""Contain preserves every image corner and touches at least one pair of paper edges."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
assets=Path(__file__).resolve().parents[1]/'assets'
with sync_playwright() as p:
 browser=p.chromium.launch();page=browser.new_page(viewport={'width':411,'height':828});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={landscape:()=>false,state:()=>JSON.stringify({permission:true,device:{},history:[]})}")
 def route(r):
  assert r.request.method=='GET'
  file=assets/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing')
 page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')
 page.evaluate('''async()=>{window.fixtures=[];for(const [w,h] of [[800,1200],[1200,800],[800,800]]){const c=document.createElement('canvas');c.width=w;c.height=h;const ctx=c.getContext('2d');ctx.fillStyle='#236ba4';ctx.fillRect(0,0,w,h);for(const [x,y,color] of [[0,0,'#dc1e1e'],[w-40,0,'#14aa32'],[0,h-40,'#e6c814'],[w-40,h-40,'#8c28b4']]){ctx.fillStyle=color;ctx.fillRect(x,y,40,40);}const photo={src:c.toDataURL(),turn:0,fit:'bottom',border:78,zoom:2,x:.3,y:-.2,filter:'none',overlays:[]};await loadPhoto(photo);fixtures.push(photo);}}''')
 for shape in range(3):
  for media,orientation in [(5009,'portrait'),(5012,'portrait'),(5012,'landscape'),(5014,'portrait')]:
   page.evaluate('''({shape,media,orientation})=>{closeSheet();state={...defaults,mode:'photo',media,sixLayout:media,orientation,fit:'bottom',border:78,photos:[{...fixtures[shape]},{...fixtures[shape],border:96}],active:0};render();openLayout();}''',{'shape':shape,'media':media,'orientation':orientation})
   page.locator('[data-setting=fit][data-value=contain]').click()
   assert page.evaluate('active().border===0&&active().zoom===1&&active().x===0&&active().y===0&&state.photos[1].border===96')
   assert page.locator('#borderInput').count()==0
   result=page.evaluate('''()=>{const c=compose(),w=c.width,h=state.media===5014?c.height/2:c.height,data=c.getContext('2d').getImageData(0,0,w,h).data;let l=w,t=h,r=-1,b=-1;const colors=[[220,30,30],[20,170,50],[230,200,20],[140,40,180]],counts=[0,0,0,0];for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=(y*w+x)*4;if(data[i]<245||data[i+1]<245||data[i+2]<245){l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y);}colors.forEach((color,k)=>{if(color.every((v,j)=>data[i+j]===v))counts[k]++;});}return {w,h,l,t,r,b,counts};}''')
   assert result['counts'] and min(result['counts'])>0,(shape,media,result)
   assert (result['l']<=1 and result['w']-1-result['r']<=1) or (result['t']<=1 and result['h']-1-result['b']<=1),result
   assert abs(result['l']-(result['w']-1-result['r']))<=1 and abs(result['t']-(result['h']-1-result['b']))<=1,result
   page.evaluate("active().border=state.border=96;render()")
   assert page.locator('#layoutSummary').inner_text()=='完整保留'
   frame=page.evaluate('({x:photoFrames[0].x,y:photoFrames[0].y})');assert frame=={'x':0,'y':0}
 page.evaluate("async()=>{closeSheet();state.mode='template';active().templateId=state.templateId=TEMPLATE_CATALOG[0].id;active().zoom=2;active().x=.3;active().y=.2;await TemplateStudio.open()}")
 page.locator('#noTemplate').click();assert page.evaluate('active().border===0&&active().zoom===1&&active().x===0&&active().y===0')
 assert not errors,errors;browser.close()
print('PASS: contain fits all corners, touches paper edges, centers image, ignores legacy margins and resets explicit selection; 12 photo/paper combinations; no printing')
