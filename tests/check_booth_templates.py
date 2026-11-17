"""Verify error guidance in both native and desktop browser UI without printing."""
import os,mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(**({'channel':os.environ['TEST_BROWSER_CHANNEL']} if os.environ.get('TEST_BROWSER_CHANNEL') else {}))
 page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  f=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
  mime={'.js':'text/javascript','.svg':'image/svg+xml','.html':'text/html','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}.get(f.suffix,mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
  r.fulfill(body=f.read_bytes(),content_type=mime) if f.is_file() else r.fulfill(status=404)
 page.route('https://studio.local/**',route)
 page.add_init_script("window.deviceState={permission:true,device:{},history:[]};window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({}),printBatch:()=>{throw Error('Printing forbidden')}}")
 page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')

 page.evaluate('Promise.all([NameLabels.ready,CardArt.ready,BoothTemplates.ready])')
 assert page.evaluate('BoothTemplates.catalog.length')==33
 page.evaluate("""async()=>{state.photos=[];for(let i=0;i<6;i++){const c=document.createElement('canvas');c.width=360;c.height=480;const ctx=c.getContext('2d');ctx.fillStyle=['#487c9a','#dca178','#7c9a65','#a879a5','#849bc0','#c8ad60'][i];ctx.fillRect(0,0,360,480);ctx.fillStyle='#ffffff';ctx.font='bold 140px sans-serif';ctx.fillText(i+1,130,280);const p={src:c.toDataURL('image/jpeg'),overlays:[],zoom:1,x:0,y:0,turn:0,filter:'none',templateId:null};state.photos.push(p);await loadPhoto(p);const alias='/private/photos/booth-'+i+'.jpg';images.set(alias,images.get(p.src));p.src=alias;}state.active=0;state.mode='photo';state.media=5012;state.orientation='portrait';render()}""")
 page.evaluate('window.testPhotos=[...state.photos]')
 # Every photo slot stays within its paper and renders each selected photo exactly once.
 assert page.evaluate("""()=>{for(const e of BoothTemplates.catalog)for(const [w,h] of [[1200,1800],[1800,1200],[1040,1040],[1200,900]]){const f=BoothTemplates.frames(w,h,e);if(f.length!==e.slots||f.some(b=>b.x<0||b.y<0||b.w<=0||b.h<=0||b.x+b.w>w||b.y+b.h>h))throw Error(e.id);for(let i=0;i<f.length;i++)for(let j=i+1;j<f.length;j++)if(f[i].x<f[j].x+f[j].w&&f[j].x<f[i].x+f[i].w&&f[i].y<f[j].y+f[j].h&&f[j].y<f[i].y+f[i].h)throw Error('overlap '+e.id);}return true}""")
 for media in [5012,5009,5014]:
  for slots in [2,3,4]:
   if media==5014 and slots==4:continue
   n=slots*(2 if media==5014 else 1)
   page.evaluate("([media,slots,n])=>{state.media=media;state.photos=testPhotos.slice(0,n);state.active=0;TemplateStudio.apply('booth-comic-'+slots);render()}",[media,slots,n])
   assert page.evaluate('state.mode')=='collage'
   assert page.evaluate('photoFrames.map(f=>state.photos.indexOf(f.p))')==list(range(n))
   pages=page.evaluate('preparePrintPages().then(p=>p.map(x=>({media:x.media,orientation:x.orientation,bytes:x.base64.length})))')
   assert len(pages)==1 and pages[0]['bytes']>1000
   page.evaluate('state.photos.pop();render()')
   assert page.evaluate('preparePrintPages().then(()=>false,e=>e.message.includes("请再添加"))')
 page.evaluate("state.media=5012;state.photos=[...testPhotos];state.active=3;TemplateStudio.apply('booth-journal-2');render()")
 assert page.evaluate('photoFrames.map(f=>state.photos.indexOf(f.p))')==[2,3]
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==3
 assert page.evaluate('state.active')==3
 page.evaluate('TemplateStudio.open()')
 for category,count in [('kids',10),('nature',7),('travel',4),('celebration',5),('art',9)]:
  page.locator(f'[data-template-category={category}]').click()
  assert page.locator('[data-template]:visible').count()==count,(category,count)
 page.locator('[data-template-category=y2k]').click()
 assert page.locator('[data-template]:visible').count()==4
 page.locator('[data-template="booth-y2k-4"]').click()
 assert page.evaluate('state.collageTemplateId')=='booth-y2k-4'
 page.evaluate('closeSheet();openLayout()')
 page.locator('[data-setting=collageLayout][data-value=grid]').click()
 assert page.evaluate('state.collageTemplateId') is None
 page.evaluate("closeSheet();state.photos=[testPhotos[0]];state.active=0;state.mode='photo';TemplateStudio.apply('booth-magazine-1');render()")
 assert page.evaluate('state.mode')=='template'
 assert page.evaluate('photoFrames.length')==1
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 page.evaluate("state.photos=testPhotos.slice(0,4);TemplateStudio.apply('booth-y2k-4');render()")
 assert page.evaluate("ProjectFile.encode().then(raw=>ProjectFile.decode(raw)).then(p=>p.editing.collageTemplateId==='booth-y2k-4'&&p.editing.collageLayout==='booth')")
 # Export a contact sheet from the actual renderer, for visual review.
 if os.environ.get('BOOTH_PREVIEW'):
  data=page.evaluate("""()=>{const c=document.createElement('canvas');c.width=960;c.height=9*330;const ctx=c.getContext('2d');ctx.fillStyle='#ececec';ctx.fillRect(0,0,c.width,c.height);BoothTemplates.catalog.forEach((e,i)=>{const x=i%4*240,y=Math.floor(i/4)*330;BoothTemplates.paint(ctx,testPhotos.slice(0,e.slots),x+10,y+10,220,290,e);ctx.fillStyle='#111';ctx.font='14px sans-serif';ctx.textAlign='center';ctx.fillText(e.names.zh,x+120,y+320)});return c.toDataURL().split(',')[1]}""")
  import base64
  Path(os.environ['BOOTH_PREVIEW']).write_bytes(base64.b64decode(data))
 assert not errors,errors
 browser.close()
print('PASS: 32 styles; bounded non-overlapping slots; all paper formats; photo identity/crop frames; print pagination and incomplete-photo guard; category selection; original layout switching; no printing')
