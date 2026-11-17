"""Verify full-original hold gestures and stable editor bounds without printing."""
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
 page.evaluate("Object.defineProperty(screen,'width',{value:390,configurable:true});Object.defineProperty(screen,'height',{value:844,configurable:true});state.media=5012;state.mode='photo';state.photos=[];addPhotos([{src:'/sample.svg'}])")
 page.evaluate('Studio.landscape=()=>innerWidth>innerHeight;updateEditorOrientation();render()')
 page.wait_for_function('!!printPreview&&canAdjustPhoto()')
 assert not errors,errors

 assert page.locator('#typeMenuBtn').is_visible()
 assert not page.locator('#paperBtn').is_visible()
 assert not page.locator('#typeTabs').is_visible()
 assert page.locator('#photoPages').count()==0
 assert page.evaluate("$('editorToolbar').parentElement.classList.contains('editor-controls')")
 for kind in ['calendar','id','idcard','label','card','photo']:
  page.locator('#typeMenuBtn').click()
  assert page.locator('#typeTabs').is_visible()
  assert page.locator('#typeTabs button').all_text_contents()==['照片','证件照','ID 卡贴','月历','姓名贴','卡片']
  page.locator(f'[data-print-type="{kind}"]').click();page.wait_for_timeout(100)
  assert not page.locator('#typeTabs').is_visible()
  assert page.evaluate('state.mode')==kind
 page.locator('#menuBtn').click();assert page.locator('#menuPaper').is_visible()
 page.locator('#menuPaper').click();assert page.evaluate('sheetKind')=='paper'
 page.evaluate('closeSheet()')
 for width,height in [(390,844),(430,932),(844,390)]:
  page.set_viewport_size({'width':width,'height':height});page.evaluate('updateEditorOrientation();render()');page.wait_for_timeout(200)
  toolbar=page.locator('#editorToolbar').bounding_box();photos=page.locator('#photos').bounding_box();canvas=page.locator('#preview').bounding_box()
  if width<height:
   assert abs(canvas['width']-width)<1.5 and abs(canvas['x'])<1.5,canvas
   assert toolbar['y']+toolbar['height']<=photos['y']+1.5,(toolbar,photos)
  else:
   assert toolbar['x']>=64 and toolbar['x']+toolbar['width']<=width-124+1.5,toolbar
   assert canvas['y']+canvas['height']<=toolbar['y']+1.5,(canvas,toolbar)
  page.locator('#composeToggle').click();page.wait_for_timeout(150)
  if width>height:
   crop_toolbar=page.locator('#editorToolbar').bounding_box();crop_canvas=page.locator('#preview').bounding_box()
   assert crop_canvas['y']+crop_canvas['height']<=crop_toolbar['y']+1.5,(crop_canvas,crop_toolbar)
  page.locator('#composeToggle').click();page.wait_for_timeout(100)
  page.locator('#templateBtn').click();page.wait_for_timeout(100)
  rail=page.locator('#effectRail').bounding_box();toolbar=page.locator('#editorToolbar').bounding_box()
  if width<height:assert rail['y']>=toolbar['y']+toolbar['height']-1.5,(rail,toolbar)
  page.locator('#effectName').click();menu=page.locator('#effectGroups').bounding_box()
  assert menu['y']>=0 and menu['y']+menu['height']<=height,(width,menu)
  page.locator('[data-effect-group="basic"]').click();page.locator('#effectCancel').click()
  assert page.locator('#photoPages').count()==0
  if width==390:page.screenshot(path='compact-phone.jpg',type='jpeg',quality=65)
 assert not errors,errors
 page.close();page=browser.new_page(viewport={'width':1280,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def webroute(r):
  if urlparse(r.request.url).path=='/api/state':r.fulfill(json={'permission':True,'host':'desktop','device':{},'history':[]});return
  assert r.request.method=='GET','No print calls allowed'
  route(r)
 page.route('https://studio.local/**',webroute);page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')
 page.wait_for_function('document.body.classList.contains("desktop-editor")')
 page.evaluate("addPhotos([{src:'/sample.svg'}]);render()")
 page.wait_for_timeout(300)
 page.locator('#typeMenuBtn').click();page.locator('[data-print-type="calendar"]').click()
 page.locator('#typeMenuBtn').click();page.locator('[data-print-type="photo"]').click()
 for compose in [False,True]:
  if compose:page.locator('#composeToggle').click()
  page.wait_for_timeout(200)
  toolbar=page.locator('#editorToolbar').bounding_box();photos=page.locator('#photos').bounding_box();canvas=page.locator('#preview').bounding_box()
  assert toolbar['y']+toolbar['height']<=photos['y']+1.5,(toolbar,photos)
  assert canvas['y']+canvas['height']<=toolbar['y']+1.5,(canvas,toolbar)
 page.locator('#composeToggle').click();page.locator('#templateBtn').click();page.locator('#effectName').click()
 menu=page.locator('#effectGroups').bounding_box();assert menu['y']>=0 and menu['y']+menu['height']<=900,menu
 page.locator('[data-effect-group="basic"]').click();page.locator('#effectCancel').click()
 page.screenshot(path='compact-desktop.jpg',type='jpeg',quality=65)
 assert not errors,errors
 browser.close()
 print('PASS compact editor: type dropdown, paper menu, full-width preview, toolbar/rail/popover bounds')
