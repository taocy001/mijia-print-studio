"""Verify editor controls across print types, desktop browser and phone landscape."""
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
 page.set_viewport_size({'width':390,'height':844});page.evaluate('Studio.landscape=()=>innerWidth>innerHeight;updateEditorOrientation()')
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
 assert not page.locator('#layoutBtn').is_visible()
 page.evaluate("addPhotos([{src:'/sample.svg'}])")
 page.wait_for_function('!!printPreview&&canAdjustPhoto()')
 desktop_before=page.locator('#preview').bounding_box();desktop_photos=page.locator('#photos').bounding_box()
 page.locator('#filterBtn').click();assert page.locator('#effectRail').is_visible()
 page.wait_for_timeout(150)
 desktop_after=page.locator('#preview').bounding_box();desktop_rail=page.locator('#effectRail').bounding_box()
 for key in ['x','y','width','height']:assert abs(desktop_before[key]-desktop_after[key])<1.5,(key,desktop_before,desktop_after)
 assert abs(desktop_photos['height']-desktop_rail['height'])<1.5
 assert not page.locator('#sheet').is_visible()
 page.locator('#effectAll').click();assert page.locator('#sheet').is_visible()
 page.locator('[data-filter=sepia]').click();assert not page.locator('#sheet').is_visible()
 page.evaluate("$(EffectBrowser.kind()==='templates'?'templateBtn':'filterBtn').click()");assert page.locator('#photos').is_visible()
 page.locator('#templateBtn').click();page.locator('#effectAll').click();page.wait_for_selector('[data-basic=grid4]')
 page.locator('[data-basic=grid4]').click();page.evaluate("$(EffectBrowser.kind()==='templates'?'templateBtn':'filterBtn').click()")
 assert page.evaluate("state.photoLayout==='grid4'")
 page.locator('#filterBtn').click();page.wait_for_timeout(200)
 for selector in ['#effectRail','#editorToolbar','#preview']:
  box=page.locator(selector).bounding_box();assert box and box['x']>=0 and box['x']+box['width']<=1281,(selector,box)
 page.screenshot(path='editor-desktop.jpg',type='jpeg',quality=70)
 page.evaluate("$(EffectBrowser.kind()==='templates'?'templateBtn':'filterBtn').click()")
 # Browser small-screen landscape replaces the existing vertical photo rail in place.
 page.set_viewport_size({'width':844,'height':390});page.evaluate('Studio.landscape=()=>innerWidth>innerHeight;updateEditorOrientation();render()')
 before=page.locator('#preview').bounding_box();photos=page.locator('#photos').bounding_box()
 page.locator('#filterBtn').click();page.wait_for_timeout(200)
 rail=page.locator('#effectRail').bounding_box();canvas=page.locator('#preview').bounding_box()
 assert rail['width']<=65 and rail['height']>300,rail
 for key in ['x','y','width','height']:assert abs(canvas[key]-before[key])<1.5,(key,before,canvas)
 assert abs(rail['width']-photos['width'])<1.5
 for name in ['#effectCancel','#effectAll','#effectName']:
  box=page.locator(name).bounding_box();assert box['x']>=0 and box['x']+box['width']<=844 and box['y']+box['height']<=390,(name,box)
 assert canvas['x']+canvas['width']<=rail['x']+2,(canvas,rail)
 page.screenshot(path='editor-landscape.jpg',type='jpeg',quality=70)
 assert not errors,errors
 browser.close()
print(f'PASS: {cases} other-type/media/photo combinations; desktop rail/gallery/return; responsive landscape rail, all controls and preview bounds; no printing')
