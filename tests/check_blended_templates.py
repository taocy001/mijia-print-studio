"""Organic template edges preserve the subject and shared photo geometry."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes,base64
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch();page=browser.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={state:()=>'{\"device\":{},\"history\":[]}',landscape:()=>false}")
 def route(r):
  assert r.request.method=='GET'
  url=urlparse(r.request.url);assert url.hostname=='studio.test'
  file=ROOT/'assets'/(url.path.lstrip('/') or 'index.html')
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing')
 page.route('**/*',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')
 result=page.evaluate('''async()=>{
  const source=document.createElement('canvas');source.width=1200;source.height=1000;const sx=source.getContext('2d');
  for(let y=0;y<1000;y+=40)for(let x=0;x<1200;x+=40){sx.fillStyle=['#19364d','#e16b49','#368581','#e5bc55'][(x/40+y/40)%4];sx.fillRect(x,y,40,40);}
  sx.fillStyle='#faf3df';sx.beginPath();sx.arc(600,500,150,0,Math.PI*2);sx.fill();sx.fillStyle='#253249';sx.font='bold 80px sans-serif';sx.textAlign='center';sx.fillText('CENTER',600,525);
  const photo={src:source.toDataURL(),fit:'cover',zoom:1,x:0,y:0,turn:0,filter:'none',overlays:[]};await loadPhoto(photo);
  const entries=TEMPLATE_CATALOG.filter(t=>t.style.startsWith('blend-'));if(entries.length!==5)throw Error('Expected five blended designs');
  if(!TEMPLATE_CATALOG.slice(0,10).every(t=>t.style.startsWith('kids-'))||!TEMPLATE_CATALOG.slice(10,15).every(t=>t.style.startsWith('blend-')))throw Error('Catalog order');
  const tiles=[],failures=[];
  for(const t of entries)for(const [w,h] of [[1216,1824],[1824,1216],[1040,1040],[1216,912]]){
   const c=document.createElement('canvas');c.width=w;c.height=h;const ctx=c.getContext('2d'),entry=OriginalTemplates.variant(t,w,h);
   const reference=document.createElement('canvas');reference.width=w;reference.height=h;drawPhoto(reference.getContext('2d'),photo,0,0,w,h,'cover');
   photoFrames=[];collectingPhotoFrames=true;try{OriginalTemplates.paint(ctx,photo,0,0,w,h,entry);}finally{collectingPhotoFrames=false;}
   if(photoFrames.length!==1||photoFrames[0].x!==0||photoFrames[0].y!==0||photoFrames[0].w!==w||photoFrames[0].h!==h)failures.push(t.style+' frame');
   const a=ctx.getImageData(0,0,w,h).data,b=reference.getContext('2d').getImageData(0,0,w,h).data,margin=Math.ceil(Math.min(w,h)*.151);let changed=0;
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=(y*w+x)*4,d=Math.abs(a[i]-b[i])+Math.abs(a[i+1]-b[i+1])+Math.abs(a[i+2]-b[i+2]);if(d>3){changed++;if(x>margin&&x<w-margin&&y>margin&&y<h-margin)throw Error(t.style+' altered subject');}}
   if(changed<w*h*.025||changed>w*h*.5)failures.push(t.style+' edge coverage '+changed/(w*h));
   const before=c.toDataURL();ctx.textBaseline='middle';ctx.globalAlpha=.43;ctx.strokeStyle='#ff0000';OriginalTemplates.paint(ctx,photo,0,0,w,h,entry);
   if(ctx.textBaseline!=='middle'||ctx.globalAlpha<.429||ctx.globalAlpha>.431||ctx.strokeStyle!=='#ff0000')failures.push(t.style+' state leak');
   ctx.globalAlpha=1;ctx.clearRect(0,0,w,h);OriginalTemplates.paint(ctx,photo,0,0,w,h,entry);if(c.toDataURL()!==before)failures.push(t.style+' nondeterminism');
   const thumb=document.createElement('canvas');thumb.width=Math.round(w*320/Math.max(w,h));thumb.height=Math.round(h*320/Math.max(w,h));thumb.getContext('2d').drawImage(c,0,0,thumb.width,thumb.height);tiles.push({name:t.names.zh+' '+w+'×'+h,src:thumb.toDataURL()});
  }
  // Drawing the lower splice panel must not change or decorate the upper one.
  const c=document.createElement('canvas');c.width=1216;c.height=1824;const ctx=c.getContext('2d');ctx.fillStyle='#e24a38';ctx.fillRect(0,0,1216,912);const before=ctx.getImageData(0,0,1216,912).data;
  photoFrames=[];collectingPhotoFrames=true;try{OriginalTemplates.paint(ctx,photo,0,912,1216,912,OriginalTemplates.variant(entries[0],1216,912));}finally{collectingPhotoFrames=false;}
  const after=ctx.getImageData(0,0,1216,912).data;if(before.some((v,i)=>v!==after[i]))failures.push('Splice leak');if(photoFrames.length!==1||photoFrames[0].y!==912)failures.push('Splice coordinates');
  return {failures,tiles};
 }''')
 assert not result['failures'],result['failures']
 assert not errors,errors
 atlas=browser.new_page(viewport={'width':1440,'height':1000})
 atlas.set_content('<style>body{font:16px sans-serif;background:#dadbd8}main{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}figure{margin:0;text-align:center}img{max-width:100%;height:300px;object-fit:contain}</style><main>'+''.join('<figure><img src="'+tile['src']+'"><figcaption>'+tile['name']+'</figcaption></figure>' for tile in result['tiles'])+'</main>')
 atlas.screenshot(path='/tmp/blended-template-atlas.png',full_page=True)
 browser.close()
print('PASS: five organic templates × four paper shapes, unchanged center, deterministic edges, frame collection and splice isolation; no printing')
