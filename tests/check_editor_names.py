"""Verify accessible names and scrollable template thumbnails in the phone rail."""
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
 page.set_viewport_size({'width':844,'height':390})
 page.evaluate("Studio.landscape=()=>innerWidth>innerHeight;updateEditorOrientation();state.mode='photo';state.photos=[];addPhotos([{src:'/sample.svg'}])")
 page.evaluate("TemplateStudio.setGroup('all');EffectBrowser.toggle('templates')");page.wait_for_timeout(300)
 rail=page.locator('.editor-controls').bounding_box()
 for button in page.locator('[data-effect]').all():
  assert button.get_attribute('aria-label') and button.get_attribute('title')
  box=button.bounding_box();assert box and box['width']<=rail['width'],(button.get_attribute('aria-label'),box,rail)
 assert page.locator('#effectChoices button>span').count()==0
 page.evaluate("const c=$('effectChoices');c.scrollTop=c.scrollHeight")
 last=page.locator('[data-effect]').last.bounding_box();assert last['y']+last['height']<=rail['y']+rail['height']+1
 page.locator('#effectCancel').click();assert page.locator('#photos').is_visible()
 assert not errors,errors
 browser.close()
print('PASS: all templates retain accessible names; vertical rail scrolls to final choice; cancel restores photo strip')
