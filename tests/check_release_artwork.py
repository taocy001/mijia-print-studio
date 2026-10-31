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
 assert page.evaluate('TEMPLATE_CATALOG.length')==16
 assert page.evaluate('TEMPLATE_CATALOG.every(t=>t.original&&!t.bg&&!t.landscape.bg)')
 for direction in ['portrait','landscape']:
  page.evaluate('(d)=>{state.orientation=d;state.mode="photo";render()}',direction)
  page.locator('#templateBtn').click()
  page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===16")
  assert page.locator('#noTemplate').get_attribute('aria-pressed')=='true'
  page.locator('[data-template="studio-petal"]').click()
  assert page.evaluate('active().templateId')=='studio-petal'
  output=page.evaluate('async()=>{const p=await preparePrintPages();return [p.length,p[0].base64.length]}')
  assert output[0]==1 and output[1]>10000,output
  page.evaluate('TemplateStudio.open()')
  page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===16")
  page.locator('#noTemplate').click();assert page.evaluate('active().templateId') is None
 page.locator('#addEmojiQuick').click();assert page.locator('.emoji-grid img').count()==60
 assert page.evaluate("[...document.querySelectorAll('.emoji-grid img')].every(i=>i.complete&&i.naturalWidth>0)")
 page.evaluate('closeSheet()')
 page.locator('#menuBtn').click();page.locator('#artCredits').click();assert 'CC BY 4.0' in page.locator('#sheetBody').inner_text();page.evaluate('closeSheet()')
 # A removed template must not silently turn into another frame.
 page.evaluate("()=>{state.mode='template';state.templateId='legacy-frame';active().templateId='legacy-frame';active().overlays=[{id:'retained',text:'hello',kind:'text'}];save()}")
 page.reload();page.wait_for_function('window.TemplateStudio&&window.LayerEditor');page.evaluate('LayerEditor.ready')
 assert page.evaluate('state.mode')=='photo'
 assert page.evaluate('active().overlays[0].text')=='hello'
 assert page.evaluate('active().templateId') is None
 page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});await NameLabels.ready;}")
 atlas=page.evaluate("""()=>{
  const tiles=[];const tile=(label,w,h,paint)=>{const c=document.createElement('canvas');c.width=w;c.height=h;paint(c.getContext('2d'));tiles.push(`<figure><img src="${c.toDataURL()}"><figcaption>${label}</figcaption></figure>`);};
  for(const t of TEMPLATE_CATALOG)for(const wide of [false,true]){const e=wide?{...t,...t.landscape}:t;tile(t.names.zh+(wide?' · 横':' · 竖'),wide?300:200,wide?200:300,c=>OriginalTemplates.paint(c,active(),0,0,c.canvas.width,c.canvas.height,e));}
  state.labelTitle='小明';state.labelSubtitle='一年级';for(const s of NAME_LABEL_CATALOG)tile(s.name,300,200,c=>{c.scale(300/1040,200/1040);NameLabels.draw(c,0,0,1040,1040,s)});
  for(const s of CARD_CATALOG)tile(s.name,300,200,c=>{c.scale(300/1824,200/1216);CardArt.draw(c,0,0,1824,1216,s)});
  return '<main class="atlas">'+tiles.join('')+'</main>'+ '<style>body{overflow:visible!important;background:#ecece8!important}.atlas{display:grid;grid-template-columns:repeat(8,1fr);gap:12px;padding:16px}figure{margin:0;background:white;padding:8px;display:flex;flex-direction:column;align-items:center;justify-content:center}figure img{max-width:100%;height:190px;object-fit:contain}figcaption{font:14px sans-serif;color:#333;margin-top:8px}</style>';
 }""")
 preview=b.new_page(viewport={'width':1600,'height':1200});preview.set_content(atlas);preview.screenshot(path='/tmp/liuying-release-artwork.png',full_page=True)
 assert not errors,errors
 print('PASS: 16 original frames in both directions, print composition, 60 vector emoji, attribution, old-draft migration; no printing')
 b.close()
