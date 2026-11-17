"""Small-paper regression; TEMPLATE_BASELINE may point to pre-change asset files."""
import os,mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASELINE=Path(os.environ.get('TEMPLATE_BASELINE',str(ROOT/'before-assets' if (ROOT/'before-assets').exists() else ROOT/'before/assets')))
with sync_playwright() as p:
 browser=p.chromium.launch(**({'channel':os.environ['TEST_BROWSER_CHANNEL']} if os.environ.get('TEST_BROWSER_CHANNEL') else {}))
 page=browser.new_page();page.add_init_script("Object.defineProperty(crypto,'randomUUID',{value:undefined})");errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  f=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
  mime={'.js':'text/javascript','.svg':'image/svg+xml','.html':'text/html','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}.get(f.suffix,mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
  r.fulfill(body=f.read_bytes(),content_type=mime) if f.is_file() else r.fulfill(status=404)
 page.route('https://studio.local/**',route)
 page.add_init_script("window.deviceState={permission:true,device:{},history:[]};window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({}),pick:n=>{window.picks=(window.picks||[]).concat(n)},capture:()=>{window.captures=(window.captures||0)+1;return JSON.stringify({ok:true,id:'test-camera'})},captureAck:()=>JSON.stringify({ok:true}),printBatch:()=>{throw Error('Printing forbidden')}}")
 page.add_init_script("window.BrowserTransport={};document.addEventListener('DOMContentLoaded',()=>document.documentElement.classList.add('browser-client'))")
 page.set_viewport_size({'width':1440,'height':1000})
 page.goto('https://studio.local/')
 page.evaluate('Promise.all([LayerEditor.ready,BoothTemplates.ready,NameLabels.ready,CardArt.ready])')
 page.evaluate("Object.defineProperty(screen,'width',{value:1440,configurable:true});Object.defineProperty(screen,'height',{value:1000,configurable:true});state.media=5012;state.mode='photo';state.photos=[];addPhotos(Array.from({length:6},()=>({src:'/sample.svg'})))")
 page.wait_for_function('state.photos.length===6&&ready()')
 page.evaluate("state.photos.forEach((p,i)=>{const src='/private/photos/everyday-'+i+'.jpg';images.set(src,images.get(p.src));p.src=src;});render()")
 page.wait_for_selector('#sheet.desktop-inspector .template-card')
 assert not errors,errors
 # Capture geometry before/after using isolated old painter APIs, without changing saved works.
 def geometry():
  return page.evaluate("""()=>{const rows={};for(const media of [5009,5014,5012]){state.media=media;for(const id of TemplateCollection.byGroup?Object.values(TemplateCollection.byGroup).flat():[]){const e=BoothTemplates.get(id);if(media===5014&&e?.slots>1)continue;const [w,h]=media===5009?[1040,1040]:media===5014?[1216,912]:[1216,1824];let fs;if(e)fs=BoothTemplates.frames(w,h,e);else{const v=OriginalTemplates.variant(TEMPLATE_CATALOG.find(t=>t.id===id),w,h);fs=[{x:v.margin.left,y:v.margin.top,w:v.crop.width,h:v.crop.height}];}rows[media+':'+id]=fs.map(f=>[f.x,f.y,f.w,f.h,f.angle||0]);}}return rows;}""")
 after=geometry()
 page.evaluate('window.newPainters={EverydayTemplates,PlayfulTemplates,BoothTemplates,OriginalTemplates}')
 for name in ['everyday-templates.js','playful-templates.js','booth-templates.js','original-templates.js']:
  source=(BASELINE/name).read_text(encoding='utf-8').split('TEMPLATE_CATALOG.unshift')[0]
  page.evaluate(source)
 before=geometry()
 page.evaluate('Object.assign(window,newPainters)')
 gains=[]
 for key,frames in after.items():
  if key.startswith('5012:'):
   assert frames==before[key],key
  else:
   for a,b in zip(frames,before[key]):
    assert a[2]*a[3]>=b[2]*b[3]-.01,key
    if a[2]*a[3]>b[2]*b[3]*1.01:gains.append(a[2]*a[3]/(b[2]*b[3]))
 assert gains
 print('PHOTO_AREA_GAIN',round(min(gains),3),round(max(gains),3),'windows',len(gains),flush=True)
 # No-template stays first for every paper/group, including the desktop chooser.
 for media in [5009,5014,5012]:
  page.evaluate('(m)=>{state.media=m;PhotoWorks.select(0);render()}',media)
  for group in page.evaluate('TemplateStudio.groups().map(g=>g[0])'):
   page.evaluate('(g)=>TemplateStudio.setGroup(g)',group)
   assert page.evaluate('TemplateStudio.browseItems()[0].id')=='single'
  page.evaluate("TemplateStudio.setGroup('all');TemplateStudio.open()")
  page.wait_for_selector('#noTemplate')
  assert page.evaluate("document.querySelector('.template-grid .template-card:not([hidden])').id")=='noTemplate'
  assert '无模板' in page.locator('#noTemplate').inner_text()
 # Newly added photos default to no template, even when an existing photo has one.
 page.evaluate("closeSheet();state.media=5012;PhotoWorks.select(0);PhotoFlow.apply('booth-life-watch');state.photos.splice(1);render()")
 page.evaluate("addPhotos([{src:'/sample.svg'}])")
 page.wait_for_function('state.photos.length===2')
 assert page.evaluate('state.photos[1].work.template')=='single'
 # Small-paper visual contact sheet; all content comes from the same actual painter.
 data=page.evaluate("""()=>{const ids=['booth-fun-pork','booth-fun-volcano','booth-life-watch','booth-life-plate','booth-life-tea','booth-life-computer','studio-tide','studio-kids-dino','booth-v2-purikura-1','booth-v2-together-1','booth-v2-comic-1','studio-blend-watercolor'];const out=document.createElement('canvas');out.width=960;out.height=960;const c=out.getContext('2d');c.fillStyle='#ddd';c.fillRect(0,0,out.width,out.height);for(let row=0;row<2;row++){state.media=row?5014:5009;for(let i=0;i<ids.length;i++){PhotoWorks.select(0);PhotoFlow.apply(ids[i]);const pic=compose(false),h=row?912:1040,x=(i%6)*160,y=row*480+Math.floor(i/6)*240;c.drawImage(pic,0,0,pic.width,h,x+4,y+24,152,152*h/pic.width);c.fillStyle='#222';c.font='11px sans-serif';c.fillText((row?'4寸 ':'3寸 ')+ids[i].replace('booth-',''),x+4,y+14,152);}}return out.toDataURL('image/png').split(',')[1];}""")
 import base64
 (ROOT/'small-paper-contact.png').write_bytes(base64.b64decode(data))
 assert not errors,errors
 browser.close()
 print('PASS small-paper geometry enlargement, unchanged 6-inch geometry, no-template first in groups/desktop, new photo default and contact sheet; no printing')
