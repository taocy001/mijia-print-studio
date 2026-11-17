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


 # More and printer connection must return to their own parents even after refresh.
 page.locator('#menuBtn').click();page.locator('#menuPaper').click();page.evaluate('openPaper();openPaper()')
 page.locator('#settingsBack').click();assert page.evaluate('sheetKind')=='menu'
 page.locator('#menuDevice').click();assert page.locator('#changePaper').count()==0;page.locator('#settingsBack').click()
 assert page.evaluate('sheetKind')=='menu';page.evaluate('closeSheet()')
 page.evaluate("addPhotos(Array.from({length:5},()=>({src:'/sample.svg'})))")
 page.wait_for_function('state.photos.length===6&&ready()')
 page.evaluate("state.photos.forEach((p,i)=>p.caption='ABCDEF'[i]);PhotoFlow.apply('grid4');render()")
 def order():return page.evaluate("state.photos.map(p=>p.caption).join('')")
 def slots():return page.evaluate("PhotoFlow.pagePhotos().map(p=>p.caption).join('')")
 def badges():return page.locator('#photos .photo-use').all_text_contents()
 def drag_mouse(a,b):
  source=page.locator(f'[data-photo="{a}"]').bounding_box();target=page.locator(f'[data-photo="{b}"]').bounding_box()
  page.mouse.move(source['x']+source['width']/2,source['y']+source['height']/2);page.mouse.down()
  page.mouse.move(target['x']+target['width']/2,target['y']+target['height']/2,steps=12);page.mouse.up();page.wait_for_timeout(120)
 cdp=page.context.new_cdp_session(page)
 def drag_touch(a,b):
  source=page.locator(f'[data-photo="{a}"]').bounding_box();target=page.locator(f'[data-photo="{b}"]').bounding_box()
  x,y=source['x']+source['width']/2,source['y']+source['height']/2;tx,ty=target['x']+target['width']/2,target['y']+target['height']/2
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
  for n in range(1,11):
   cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+(tx-x)*n/10,'y':y+(ty-y)*n/10,'id':1}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(150)
 assert badges()==['位置 1','位置 2','位置 3','位置 4','未使用','未使用']
 drag_touch(5,1);assert order()=='AFBCDE',order();assert slots()=='AFBC';assert badges()==['位置 1','位置 2','位置 3','位置 4','未使用','未使用']
 page.locator('#editorUndo').click();assert order()=='ABCDEF';page.locator('#editorRedo').click();assert order()=='AFBCDE'
 drag_mouse(0,5);assert order()=='FBCDEA',order();assert slots()=='FBCD'
 page.locator('#editorUndo').click();assert order()=='AFBCDE';page.locator('#editorUndo').click();assert order()=='ABCDEF'
 # Removing then restoring a photo must preserve strict visible position numbering.
 page.evaluate('removePhoto(1)');page.wait_for_timeout(100);assert order()=='ACDEF';assert slots()=='ACDE'
 page.locator('#photoUndo button').click();page.wait_for_timeout(100);assert order()=='ABCDEF';assert slots()=='ABCD'
 # Legacy slots migrate without losing the template image order or object identity.
 page.evaluate("delete state.photoOrderVersion;state.photoSelection=[3,1,0,2];window.oldRefs=[...state.photos];render()")
 assert order()=='DBACEF';assert slots()=='DBAC'
 assert page.evaluate('oldRefs.every(p=>state.photos.includes(p))')
 assert badges()==['位置 1','位置 2','位置 3','位置 4','未使用','未使用']
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 assert page.evaluate('ProjectFile.encode().then(ProjectFile.decode).then(p=>p.editing.photoOrderVersion)')==1
 page.screenshot(path='photo-order-phone.jpg',type='jpeg',quality=65)
 assert not errors,errors
 browser.close()
 print('PASS More/device return paths; real touch/mouse photo ordering, undo/redo, removal restore, legacy migration, one printed page, project order version')
