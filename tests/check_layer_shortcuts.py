"""Resume the right existing layer without duplicating or leaking across photos."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width,height in [(390,844),(844,390),(1280,800)]:
  page=browser.new_page(viewport={'width':width,'height':height},has_touch=width<1000);errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script("Object.defineProperty(screen.orientation,'type',{get:()=>innerWidth>innerHeight?'landscape-primary':'portrait-primary'})")
  def route(r):
   assert r.request.method=='GET' and urlparse(r.request.url).hostname=='studio.test'
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'permission':True,'device':{'media':5012,'checkedAt':int(time.time()*1000)},'history':[]});return
   f=ROOT/'assets'/(name.lstrip('/') or 'index.html');r.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream') if f.is_file() else r.fulfill(status=404,body='')
  page.route('**/*',route);page.goto('https://studio.test');page.evaluate('LayerEditor.ready')
  page.evaluate("""async()=>{await addPhotos([{src:'/sample.svg'},{src:'/sample.svg'}]);state.photos.forEach(p=>p.facePending=false);selectPhoto(0);for(const [id,kind,text] of [['t1','text','First'],['t2','text','Second'],['e1','emoji','😀'],['e2','emoji','🌸']])LayerEditor.create({id,kind,text});LayerEditor.select(null);render();}""")
  page.wait_for_timeout(100)
  def resume(kind):page.evaluate("kind=>LayerEditor.activate(kind,{resume:true})",kind)
  page.evaluate("LayerEditor.select('t1');LayerEditor.select(null)");resume('text')
  assert page.locator('#layerText').input_value()=='First' and page.locator('#layerText').evaluate('e=>e===document.activeElement')
  assert page.evaluate('LayerEditor.list().length')==4
  page.evaluate("closeSheet();LayerEditor.select('e1');LayerEditor.select(null)");resume('emoji')
  assert '😀' in page.locator('#replaceEmoji').text_content() and page.evaluate('LayerEditor.list().length')==4
  page.evaluate("closeSheet();LayerEditor.select('t1');LayerEditor.remove()");resume('text')
  assert page.locator('#layerText').input_value()=='Second' and page.evaluate('LayerEditor.list().length')==3
  page.evaluate("closeSheet();LayerEditor.select(null);active().overlays=JSON.parse(JSON.stringify(active().overlays));active().overlays.push({...active().overlays.find(x=>x.id==='t2'),id:'new-top',text:'Top'});")
  resume('text');assert page.locator('#layerText').input_value()=='Second','Stable id should survive an undo-style array replacement'
  page.evaluate("closeSheet();selectPhoto(1);LayerEditor.create({id:'p2',kind:'text',text:'Other photo'});LayerEditor.select(null)");page.wait_for_timeout(80)
  resume('text');assert page.locator('#layerText').input_value()=='Other photo'
  page.evaluate('closeSheet();selectPhoto(0)');page.wait_for_timeout(80);resume('text');assert page.locator('#layerText').input_value()=='Second'
  page.evaluate("LayerEditor.activate('text')");assert page.locator('#layerText').input_value()=='' and page.evaluate('LayerEditor.list().length')==4,'Single entry must remain a new empty editor'
  page.evaluate("closeSheet();selectPhoto(1);active().overlays=[];LayerEditor.select(null);render()");resume('text')
  assert page.locator('#layerText').input_value()=='' and page.evaluate('LayerEditor.list().length')==0
  page.locator('#layerText').fill('New draft');assert page.evaluate('LayerEditor.list().length')==1
  page.evaluate("closeSheet();active().overlays=[];LayerEditor.select(null)");resume('emoji')
  assert page.locator('.emoji-grid').count()>0 and page.evaluate('LayerEditor.list().length')==0
  cdp=page.context.new_cdp_session(page)
  def point():return page.evaluate("()=>{const o=LayerEditor.list()[0],s=LayerEditor.space(),m=LayerEditor.metrics(o,s.w,s.h),v=CropEditor.geometry(),r=$('preview').getBoundingClientRect();return {x:r.left+(m.x+s.x+v.tx)*r.width/$('preview').width,y:r.top+(m.y+s.y+v.ty)*r.height/$('preview').height}}")
  def touch(x,y):
   cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
   cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  for kind in ['text','emoji']:
   for method in ['mouse','touch']:
    page.evaluate("kind=>{closeSheet();selectPhoto(0);active().overlays=[];LayerEditor.create({id:'tap-'+kind,kind,text:kind==='text'?'Double tap':'😀',fx:.5,fy:.3,sizePct:12});LayerEditor.select(null);render();}",kind);page.wait_for_timeout(90)
    pt=point()
    if method=='mouse':page.mouse.dblclick(pt['x'],pt['y'],delay=60)
    else:touch(pt['x'],pt['y']);page.wait_for_timeout(60);touch(pt['x'],pt['y'])
    page.wait_for_selector('#layerText' if kind=='text' else '#replaceEmoji')
    assert page.evaluate('LayerEditor.list().length')==1,(width,kind,method,'double created object')
  page.evaluate("closeSheet();LayerEditor.select(null);render()");page.wait_for_timeout(80);pt=point()
  page.mouse.click(pt['x'],pt['y']);page.mouse.move(pt['x'],pt['y']);page.mouse.down();page.mouse.move(pt['x']+25,pt['y'],steps=4);page.mouse.up();page.mouse.click(pt['x']+25,pt['y'])
  assert not page.evaluate("document.body.classList.contains('layer-editing')"),'Drag followed by one tap must not be a double tap'
  for kind in ['text','emoji']:
   for interruption in ['resize','multi']:
    page.evaluate("kind=>{closeSheet();selectPhoto(0);active().overlays=[];LayerEditor.create({kind,text:kind==='text'?'Gesture':'😀',fx:.5,fy:.3,sizePct:12});LayerEditor.select(null);render();}",kind);page.wait_for_timeout(80)
    pt=point()
    if interruption=='resize':
     page.mouse.click(pt['x'],pt['y'])
     before_size=page.evaluate('LayerEditor.list()[0].sizePct')
     handle=page.locator('#layerResize').bounding_box();hx=handle['x']+handle['width']/2;hy=handle['y']+handle['height']/2
     page.mouse.move(hx,hy);page.mouse.down();page.mouse.move(hx+12,hy,steps=2);page.mouse.up()
     assert page.evaluate('LayerEditor.list()[0].sizePct')!=before_size,'Resize test must actually resize'
     page.mouse.click(pt['x'],pt['y'])
    else:
     touch(pt['x'],pt['y'])
     # No movement: the second pointer itself must cancel the previous tap.
     cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':pt['x']-5,'y':pt['y'],'id':1},{'x':pt['x']+5,'y':pt['y'],'id':2}]})
     cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
     assert not page.evaluate("document.body.classList.contains('layer-editing')"),(width,kind,'multi opened editor')
     touch(pt['x'],pt['y'])
    assert not page.evaluate("document.body.classList.contains('layer-editing')"),(width,kind,interruption,'one tap after gesture is not a double tap')
    assert page.evaluate('LayerEditor.list().length')==1
  page.evaluate("closeSheet();selectPhoto(0);active().overlays=[{id:'same-id',kind:'text',text:'First photo',fx:.5,fy:.3,sizePct:12,angle:0}];state.photos[1].overlays=[{...active().overlays[0],text:'Second photo'}];LayerEditor.select(null);render();");page.wait_for_timeout(80)
  pt=point();page.mouse.click(pt['x'],pt['y']);page.evaluate('selectPhoto(1);render()');page.wait_for_timeout(50);pt=point();page.mouse.click(pt['x'],pt['y'])
  assert not page.evaluate("document.body.classList.contains('layer-editing')"),'Matching ids on different photos are not a double tap'
  assert not errors,errors
  print('PASS layer shortcuts',width,height,flush=True);page.close()
 browser.close()
