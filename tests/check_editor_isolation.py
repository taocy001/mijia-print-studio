from pathlib import Path
from urllib.parse import urlparse
import mimetypes,time
from playwright.sync_api import sync_playwright
assets=Path(__file__).resolve().parents[1]/'assets'
with sync_playwright() as p:
 b=p.chromium.launch()
 for width,height in [(411,828),(1440,900)]:
  page=b.new_page(viewport={'width':width,'height':height},is_mobile=width<1000,has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'device':{'connected':True,'media':5009,'checkedAt':int(time.time()*1000)},'history':[]});return
   f=assets/(name.lstrip('/') or 'index.html')
   if f.is_file():r.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')
  page.locator('#filterBtn').click();page.wait_for_function("document.querySelectorAll('[data-tone]').length===8&&[...document.querySelectorAll('[data-tone]')].every(e=>!e.hidden&&e.complete&&e.naturalWidth>0)")
  assert page.evaluate('state.photos.length')==0
  page.evaluate('closeSheet()');page.locator('#menuBtn').click()
  rows=page.locator('#sheetBody>.menu-row');assert rows.count()>=6
  labels=[]
  for i in range(rows.count()):
   row=rows.nth(i);assert row.locator(':scope>svg').count()>=1;labels.append(row.locator(':scope>span').bounding_box()['x'])
  if width<1000:assert max(labels)-min(labels)<1,labels
  else:assert abs(labels[0]-labels[2])<1 and abs(labels[1]-labels[3])<1,labels
  page.evaluate("async()=>{closeSheet();const photo={src:'/sample.svg',turn:0,zoom:1,x:0,y:0,fit:'cover',filter:'none',overlays:[]};await loadPhoto(photo);state={...defaults,media:5009,photos:[photo],active:0};render()}");page.wait_for_timeout(100)
  measure="""()=>{const r=$('preview').getBoundingClientRect(),v=CropEditor.geometry(),f=photoFrames[0],g=photoGeometry(f.p,f.w,f.h,f.fit);return {pw:v.paper.w*r.width/$('preview').width,ph:v.paper.h*r.height/$('preview').height,image:g.dw*r.width/$('preview').width,print:g.dw}}"""
  before=page.evaluate(measure);page.locator('#zoomIn').click();page.wait_for_timeout(100);after=page.evaluate(measure)
  assert abs(before['pw']-after['pw'])<1 and abs(before['ph']-after['ph'])<1,(before,after)
  assert after['image']>before['image']*1.1 and after['print']>before['print']*1.1
  page.locator('#zoomOut').click();page.wait_for_timeout(100);assert abs(page.evaluate(measure)['image']-before['image'])<1
  page.evaluate("()=>{LayerEditor.create({kind:'emoji',text:'🌷',fx:.25,fy:.25,sizePct:12});LayerEditor.create({kind:'emoji',text:'😀',fx:.75,fy:.25,sizePct:12});LayerEditor.openEditor(LayerEditor.list()[0]);}")
  untouched=page.evaluate('JSON.stringify(LayerEditor.list()[1])')
  page.locator('#layerHidden').check();page.locator('[data-layer-range=sizePct]').fill('20');page.locator('[data-layer-range=angle]').fill('30');page.wait_for_timeout(100)
  assert page.evaluate('JSON.stringify(LayerEditor.list()[1])')==untouched
  assert page.evaluate('LayerEditor.list()[0].hidden&&LayerEditor.list()[0].sizePct===20&&LayerEditor.list()[0].angle===30')
  page.evaluate('LayerEditor.select(LayerEditor.list()[1].id)');assert page.locator('#layerHidden').is_visible() and not page.locator('#layerHidden').is_checked()
  assert page.locator('[data-layer-range=sizePct]').input_value()=='12' and page.locator('[data-layer-range=angle]').input_value()=='0'
  saved=page.evaluate('JSON.stringify(LayerEditor.list()[0])');page.locator('[data-layer-range=angle]').fill('-45');assert page.evaluate('JSON.stringify(LayerEditor.list()[0])')==saved
  counts=page.evaluate("""()=>{const c=compose(true,'mask'),ctx=c.getContext('2d');return [.25,.75].map(fx=>{const d=ctx.getImageData(c.width*(fx-.1),c.height*.15,c.width*.2,c.height*.2).data;let count=0;for(let i=0;i<d.length;i+=4)if(d[i]>0)count++;return count})}""")
  assert counts[0]>100 and counts[1]==0,counts
  page.evaluate("closeSheet();LayerEditor.select(null);save()");page.reload();page.evaluate('LayerEditor.ready');page.wait_for_timeout(200)
  assert page.evaluate('LayerEditor.list()[0].hidden&&!LayerEditor.list()[1].hidden&&LayerEditor.list()[1].angle===-45')
  assert not errors,errors;page.close()
 print('PASS: aligned menu icons, empty filter previews, fixed paper scale with real photo zoom, independent object parameters and overcoat mask, reload persistence')
 b.close()
