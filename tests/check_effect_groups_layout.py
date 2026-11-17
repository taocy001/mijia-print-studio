"""Verify fixed preview geometry and grouped effect switching in native-style layouts."""
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
 # Entering/exiting browsing changes controls, never the paper or picker rectangle.
 for width,height in [(390,844),(844,390)]:
  page.set_viewport_size({'width':width,'height':height})
  page.evaluate('updateEditorOrientation();render()');page.wait_for_timeout(150)
  for mode,button in [('templates','templateBtn'),('filters','filterBtn')]:
   before=page.locator('#preview').bounding_box();photos=page.locator('#photos').bounding_box()
   if width<height:
    assert abs(before['width']-width)<1.5,(width,before)
    assert abs(before['x'])<1.5,(width,before)
   page.locator('#'+button).click();page.wait_for_timeout(150)
   after=page.locator('#preview').bounding_box();rail=page.locator('#effectRail').bounding_box()
   for key in ['x','y','width','height']:
    assert abs(before[key]-after[key])<1.5,(width,mode,key,before,after)
   assert abs(photos['height']-rail['height'])<1.5,(width,photos,rail)
   assert page.locator('#effectName').is_visible() and page.locator('#effectCancel').is_visible()
   assert page.locator('#effectChoices button>span').count()==0
   if mode=='templates':
    page.locator('#effectName').click();page.locator('[data-effect-group="nature"]').click()
    assert page.evaluate("TemplateStudio.browseItems().every(t=>t.group==='nature')")
    page.evaluate('EffectBrowser.step(1)');selected=page.evaluate('TemplateStudio.selectedId()')
    page.locator('#templateBtn').click();page.locator('#templateBtn').click()
    assert page.evaluate('TemplateStudio.currentGroup()')=='nature'
    assert page.evaluate('TemplateStudio.selectedId()')==selected
    page.locator('#effectAll').click();assert page.locator('#sheet').is_visible();page.locator('#closeSheet').click()
   page.locator('#'+button).click();page.wait_for_timeout(150)
   assert page.locator('#photos').is_visible()
 assert not errors,errors
 browser.close()
print('PASS: group selection, mode toggling, fixed preview and rail rectangles')
