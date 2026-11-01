"""Bottom tabs exit browsing; floating grid preserves it; photo centers remain selectable."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch()
 for native,width,height in [(False,320,720),(True,390,844),(True,568,320),(True,667,375),(True,844,390),(True,915,412),(False,1280,800)]:
  page=b.new_page(viewport={'width':width,'height':height},is_mobile=width<1000,has_touch=width<1000);errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.add_init_script("Object.defineProperty(screen.orientation,'type',{get:()=>innerWidth>innerHeight?'landscape-primary':'portrait-primary'})")
  if native:page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{media:5012,checkedAt:Date.now()},history:[]}),landscape:()=>innerWidth>innerHeight}")
  def route(r):
   assert r.request.method=='GET','No printing or mutation requests'
   assert urlparse(r.request.url).hostname=='studio.test'
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'permission':True,'device':{'media':5012,'checkedAt':int(time.time()*1000)},'history':[]});return
   f=ROOT/'assets'/(name.lstrip('/') or 'index.html')
   r.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream') if f.is_file() else r.fulfill(status=404,body='')
  page.route('**/*',route);page.goto('https://studio.test');page.evaluate('LayerEditor.ready')
  page.evaluate("async()=>{await addPhotos(Array.from({length:6},()=>({src:'/sample.svg'})));state.photos.forEach(p=>p.facePending=false);selectPhoto(0);render();}")
  page.wait_for_timeout(180)
  if width>height and width<1000:
   for i in range(6):
    page.locator('[data-remove-photo="'+str(i)+'"]').scroll_into_view_if_needed()
    report=page.evaluate("""i=>{const button=document.querySelector('[data-remove-photo="'+i+'"]'),r=button.getBoundingClientRect(),rail=document.querySelector('.editor-controls').getBoundingClientRect(),intersects=(a,b)=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>.1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>.1;return {box:[r.x,r.y,r.right,r.bottom],rail:[rail.left,rail.right],overlap:[...document.querySelectorAll('[data-photo]')].some((e,j)=>j!==i&&intersects(r,e.getBoundingClientRect())),controls:[...document.querySelectorAll('.tool-tabs button,.topbar button')].some(e=>intersects(r,e.getBoundingClientRect())),hits:[[2,2],[38,2],[2,38],[38,38]].every(([x,y])=>document.elementFromPoint(r.x+x,r.y+y)?.closest('[data-remove-photo]')===button)};}""",i)
    x,y,right,bottom=report['box'];assert x>=0 and y>=0 and right<=width and bottom<=height,(width,i,report)
    assert x>=report['rail'][0] and right<=report['rail'][1] and not report['overlap'] and not report['controls'] and report['hits'],(width,i,report)
   for i in range(6):
    item=page.locator('[data-photo="'+str(i)+'"]');item.scroll_into_view_if_needed();box=item.bounding_box()
    page.mouse.click(box['x']+box['width']-3,box['y']+box['height']-3);page.wait_for_timeout(40)
    assert page.evaluate('state.photos.length')==6 and page.evaluate('state.active')==i,(width,'bottom-edge',i)
   board=page.locator('#board').bounding_box();preview=page.locator('#preview').bounding_box()
   assert board['height']>=height-2 and preview['height']<=height+1,(width,'preview bounds',board,preview)
  for i in [1,3,5]:
   box=page.locator('[data-photo="'+str(i)+'"]').bounding_box();page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
   page.wait_for_timeout(60)
   assert page.evaluate('state.photos.length')==6 and page.evaluate('state.active')==i,(native,width,'center',i)
  delete=page.locator('[data-remove-photo="4"]').bounding_box()
  assert delete['width']>=40 and delete['height']>=40
  page.mouse.click(delete['x']+delete['width']/2,delete['y']+delete['height']/2);page.wait_for_timeout(80)
  assert page.evaluate('state.photos.length')==5,(native,width,'corner delete')
  for target in ['layoutBtn','filterBtn','templateBtn','addTextQuick','addEmojiQuick']:
   page.locator('#filterBtn').dblclick(delay=60);page.wait_for_function("EffectBrowser.kind()==='filters'")
   page.wait_for_timeout(130)
   browse_color=page.locator('#filterBtn').evaluate('e=>getComputedStyle(e).color')
   page.locator('#'+target).click();page.wait_for_function("!EffectBrowser.active()&&!document.getElementById('sheet').hidden")
   assert page.locator('#'+target).evaluate("e=>e.classList.contains('drawer-selected')"),(native,width,target,'drawer highlight')
   page.wait_for_timeout(130)
   assert page.locator('#'+target).evaluate('e=>getComputedStyle(e).color')!=browse_color,(native,width,target,'distinct modes')
   if page.locator('#closeSheet').is_visible():page.locator('#closeSheet').click()
   page.wait_for_timeout(80)
  page.locator('#templateBtn').dblclick(delay=60);page.wait_for_function("EffectBrowser.kind()==='templates'")
  assert page.locator('#sheet').is_hidden()
  page.locator('#effectAll').click();page.wait_for_function("sheetKind==='templates'")
  assert page.evaluate('EffectBrowser.active()')
  page.locator('#closeSheet').click();page.wait_for_timeout(100);assert page.evaluate('EffectBrowser.active()') and page.locator('#sheet').is_hidden()
  page.locator('#effectDone').click();page.wait_for_timeout(100)
  page.locator('#filterBtn').click();page.wait_for_function("sheetKind==='filters'&&!EffectBrowser.active()")
  assert not errors,errors
  print('PASS toolbar',native,width,height,flush=True);page.close()
 b.close()
