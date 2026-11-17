"""Hold the first startup image until legacy order migration runs; no real printer calls."""
import os,json,base64,mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(**({'channel':os.environ['TEST_BROWSER_CHANNEL']} if os.environ.get('TEST_BROWSER_CHANNEL') else {}))
 maker=browser.new_page()
 jpeg=base64.b64decode(maker.evaluate("()=>{const c=document.createElement('canvas');c.width=32;c.height=48;const x=c.getContext('2d');x.fillStyle='#4599aa';x.fillRect(0,0,32,48);return c.toDataURL('image/jpeg').split(',')[1]}"))
 maker.close();page=browser.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 held=[];requested=[];hold_first=True
 def route(r):
  path=urlparse(r.request.url).path
  if path.startswith('/private/photos/order-'):
   requested.append(path)
   if path=='/private/photos/order-A.jpg' and hold_first:
    held.append(r);return
   r.fulfill(body=jpeg,content_type='image/jpeg');return
  file=ROOT/'assets'/(path.lstrip('/') or 'index.html')
  mime={'.js':'text/javascript','.html':'text/html','.css':'text/css','.svg':'image/svg+xml'}.get(file.suffix,mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  r.fulfill(body=file.read_bytes(),content_type=mime) if file.is_file() else r.fulfill(status=404)
 page.route('https://studio.local/**',route)
 draft={'mode':'collage','media':5012,'orientation':'portrait','photoLayout':'grid4','collageLayout':'grid','photoSelection':[3,1,0,2],'active':0,'photos':[{'src':f'/private/photos/order-{c}.jpg','caption':c,'turn':0,'zoom':1,'x':0,'y':0,'filter':'none','fit':'cover','border':0,'overlays':[]} for c in 'ABCDEF']}
 page.add_init_script("window.deviceState={permission:true,device:{},history:[]};window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({}),printBatch:()=>{throw Error('Printing forbidden')}};if(!localStorage.getItem('order-test-seeded')){localStorage.setItem('liuying-draft',"+json.dumps(json.dumps(draft))+ ");localStorage.setItem('order-test-seeded','1')}")
 page.goto('https://studio.local/',wait_until='domcontentloaded')
 assert held,'The first image must be suspended while other scripts and migration execute'
 assert page.evaluate('state.photos.map(p=>p.caption).join("")')=='DBACEF'
 assert page.evaluate('state.photoOrderVersion')==1
 hold_first=False
 for r in held:r.fulfill(body=jpeg,content_type='image/jpeg')
 page.wait_for_function('state.photos.length===6&&state.photos.every(p=>images.has(p.src))&&!!printPreview')
 assert set(requested)=={f'/private/photos/order-{c}.jpg' for c in 'ABCDEF'},requested
 assert page.evaluate('state.photos.map(p=>p.caption).join("")')=='DBACEF'
 assert page.evaluate('PhotoFlow.pagePhotos().map(p=>p.caption).join("")')=='DBAC'
 assert page.evaluate('active().caption')=='A'
 assert page.locator('#photos .photo-use').all_text_contents()==['位置 1','位置 2','位置 3','位置 4','未使用','未使用']
 page.evaluate('save()')
 assert page.evaluate("JSON.parse(localStorage.getItem('liuying-draft')).photoOrderVersion") == 1
 # A new-version reload retains the array, instead of repeatedly reapplying the old mapping.
 page.reload();page.wait_for_function('state.photos.length===6&&state.photos.every(p=>images.has(p.src))&&!!printPreview')
 assert page.evaluate('state.photos.map(p=>p.caption).join("")')=='DBACEF'
 # Session cancel/undo may alter capacity, but never replace the physical photo order by old slots.
 page.evaluate("EffectBrowser.toggle('templates');TemplateStudio.apply('horizontal');EffectBrowser.exit(true,true)")
 assert page.evaluate('state.photos.map(p=>p.caption).join("")')=='DBACEF'
 assert page.evaluate('PhotoFlow.pagePhotos().map(p=>p.caption).join("")')=='DBAC'
 page.evaluate("EffectBrowser.toggle('templates');TemplateStudio.apply('horizontal');EffectBrowser.exit();EditHistory.undo()")
 assert page.evaluate('state.photos.map(p=>p.caption).join("")')=='DBACEF'
 assert page.evaluate('PhotoFlow.pagePhotos().map(p=>p.caption).join("")')=='DBAC'
 assert page.evaluate('ProjectFile.encode().then(ProjectFile.decode).then(v=>v.editing.photoOrderVersion)')==1
 assert not errors,errors
 browser.close()
print('PASS legacy startup: suspended first image, all six assets retained, one-time migration, reload, effect cancel/undo and project marker')
