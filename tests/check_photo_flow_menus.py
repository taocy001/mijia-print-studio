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

 page.evaluate('Promise.all([NameLabels.ready,CardArt.ready])')
 page.evaluate('BoothTemplates.ready')
 page.set_viewport_size({'width':390,'height':844})
 cases=0
 for loaded in [False,True]:
  page.evaluate("(yes)=>{state.photos=yes?[{src:'/sample.svg',overlays:[]}]:[];state.active=0;return yes?loadPhoto(state.photos[0]):null}",loaded)
  for media in [5012,5009,5014]:
   for kind in ['id','idcard','calendar','label','card']:
    page.evaluate("([m,k])=>{closeSheet();state.media=m;TypeNavigation.choose(k);state.calendarLayout='photo';render()}",[media,kind])
    assert not page.locator('#photoPages').is_visible()
    for tool in page.locator('#contextTools button').evaluate_all("els=>els.filter(e=>!e.disabled).map(e=>e.dataset.typeTool)"):
     page.evaluate('closeSheet();EffectBrowser.exit(false)')
     page.locator('[data-type-tool="'+tool+'"]').click()
     page.wait_for_function("!document.querySelector('#sheet').hidden||!!EffectBrowser.kind()")
     assert page.evaluate('state.photos.length')==int(loaded)
    cases+=1
 assert not errors,errors
 page.close();page=browser.new_page(viewport={'width':1280,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def webroute(r):
  if urlparse(r.request.url).path=='/api/state':r.fulfill(json={'permission':True,'host':'desktop','device':{},'history':[]});return
  assert r.request.method=='GET','No printing or backend mutations'
  route(r)
 page.route('https://studio.local/**',webroute);page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')
 page.wait_for_function('document.body.classList.contains("desktop-editor")')
 page.wait_for_selector('[data-basic=grid4]')
 assert page.evaluate("sheetKind==='templates'")
 assert not page.locator('#layoutBtn').is_visible()
 page.locator('[data-basic=grid4]').click();page.evaluate("addPhotos(Array.from({length:6},()=>({src:'/sample.svg'})))")
 page.wait_for_function("document.querySelectorAll('.unused-photo').length===2")
 assert page.evaluate('PhotoFlow.count()')==1
 assert page.locator('#photoTypeTools button:visible').all_text_contents()==['模板','色调','文字','表情']
 # Drag an unused thumbnail directly onto the desired used thumbnail.
 source=page.locator('[data-photo="5"]').bounding_box();target=page.locator('[data-photo="0"]').bounding_box()
 page.mouse.move(source['x']+source['width']/2,source['y']+source['height']/2);page.mouse.down()
 page.mouse.move(target['x']+target['width']/2,target['y']+target['height']/2,steps=10);page.mouse.up()
 assert not page.locator('[data-replace-slot]').count()
 assert page.evaluate('PhotoFlow.selection()[0]')==5
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 page.screenshot(path='flow-desktop.jpg',type='jpeg',quality=65)
 page.set_viewport_size({'width':390,'height':844});page.evaluate('closeSheet();render()')
 page.screenshot(path='flow-phone.jpg',type='jpeg',quality=70)
 assert not errors,errors
 browser.close()
print(f'PASS: {cases} other-type/media/photo combinations; enabled menu tools and photo preservation; desktop starts in templates, replacement and single-sheet output; phone/desktop screenshots; no printing')
