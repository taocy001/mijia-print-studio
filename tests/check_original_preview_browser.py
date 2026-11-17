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
 page.evaluate("active().zoom=2;active().turn=1;active().mirror=true;active().filter='sepia';state.paperLayers={photo:[{id:'keep',kind:'emoji',text:'😍',fx:.8,fy:.8,sizePct:10,angle:0}]};render()")
 page.wait_for_timeout(100)
 before=page.evaluate('JSON.stringify(state)')
 printed=page.evaluate('compose().toDataURL()')
 box=page.locator('#preview').bounding_box()
 page.mouse.move(box['x']+box['width']*.3,box['y']+box['height']*.3)
 page.mouse.down();page.wait_for_timeout(500)
 assert page.evaluate('OriginalPreview.active()')
 assert page.locator('#originalPreview').is_visible()
 assert page.evaluate('JSON.stringify(state)')==before
 assert page.evaluate('compose().toDataURL()')==printed
 assert page.evaluate("()=>{const actual=$('originalPreview').querySelector('canvas'),c=document.createElement('canvas');c.width=actual.width;c.height=actual.height;const x=c.getContext('2d'),im=images.get(active().src),k=Math.min(c.width/im.naturalWidth,c.height/im.naturalHeight);x.fillStyle='#282a2e';x.fillRect(0,0,c.width,c.height);x.drawImage(im,(c.width-im.naturalWidth*k)/2,(c.height-im.naturalHeight*k)/2,im.naturalWidth*k,im.naturalHeight*k);return c.toDataURL()===actual.toDataURL()}")
 page.mouse.move(box['x']+box['width']*.6,box['y']+box['height']*.6)
 assert page.evaluate('OriginalPreview.active()')
 assert page.evaluate('JSON.stringify(state)')==before
 page.mouse.up();assert not page.evaluate('OriginalPreview.active()')
 assert page.evaluate('JSON.stringify(state)')==before
 # Mode transitions must preserve the preview canvas position and dimensions.
 baseline=page.locator('#preview').bounding_box()
 for button in ['templateBtn','filterBtn']:
  page.locator('#'+button).click();page.wait_for_timeout(150)
  r=page.locator('#preview').bounding_box()
  assert all(abs(r[k]-baseline[k])<1 for k in baseline),(button,baseline,r)
  page.locator('#'+button).click();page.wait_for_timeout(150)
  r=page.locator('#preview').bounding_box()
  assert all(abs(r[k]-baseline[k])<1 for k in baseline),(button,baseline,r)
 assert not errors,errors
 browser.close()
 print('PASS: full original pixels, hold-move locking, unchanged state/print, stable mode bounds')
