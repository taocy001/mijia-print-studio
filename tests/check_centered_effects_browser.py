"""Verify centred effect selection and thumbnail reuse without printer access."""
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
 # First/last effects can reach the fixed centre, and clicks retain decoded thumbnails.
 page.locator('#filterBtn').click()
 def centred():
  return page.evaluate("()=>{const t=$('effectChoices').getBoundingClientRect(),b=$('effectChoices').querySelector('[aria-pressed=true]').getBoundingClientRect();return Math.abs(b.x+b.width/2-t.x-t.width/2)<2}")
 assert centred()
 last=page.locator('#effectChoices button').last
 last.click();page.wait_for_timeout(200);assert centred()
 first=page.locator('#effectChoices button').first
 first.click();page.wait_for_timeout(200);assert centred()
 # Native scroll settle applies the nearest enabled centre item.
 page.locator('#effectChoices').hover()
 page.mouse.wheel(150,0);page.wait_for_timeout(600)
 assert centred()
 assert page.evaluate("$('effectChoices').querySelector('[aria-pressed=true]').dataset.effect===active().filter")
 page.locator('#filterBtn').click()
 page.locator('#templateBtn').click();page.locator('#effectName').click();page.locator('[data-effect-group="nature"]').click()
 page.wait_for_function("[...$('effectChoices').querySelectorAll('img')].every(i=>i.src&&i.complete)")
 page.evaluate("window.beforeNodes=[...$('effectChoices').children];window.beforeSrc=beforeNodes.map(b=>b.querySelector('img').src)")
 page.evaluate('EffectBrowser.step(1)')
 assert page.evaluate("beforeNodes.every((b,i)=>$('effectChoices').children[i]===b&&b.querySelector('img').src)")
 assert centred()
 # Browse another category without choosing: both close-button and backdrop keep actual selection.
 for close_id in ['closeSheet','scrim']:
  current=page.evaluate('TemplateStudio.selectedId()')
  page.locator('#effectAll').click();page.locator('[data-template-category="basic"]').click()
  page.evaluate("document.getElementById('%s').click()" % close_id)
  assert page.evaluate('TemplateStudio.selectedId()')==current
  assert page.evaluate('TemplateStudio.browseItems().some(t=>t.id===TemplateStudio.selectedId())')
  assert centred()
 # Cancel while a settle callback is pending cannot reapply an effect afterwards.
 page.evaluate("$('effectChoices').dispatchEvent(new WheelEvent('wheel'));$('effectChoices').scrollLeft=0")
 page.locator('#effectCancel').click();before=page.evaluate('JSON.stringify(state)');page.wait_for_timeout(350)
 assert page.evaluate('JSON.stringify(state)')==before
 assert not errors,errors
 browser.close()
print('PASS: carousel centre, end cards, scroll selection, thumbnail reuse, gallery close, cancel')
