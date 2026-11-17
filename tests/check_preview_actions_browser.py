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
 page.add_init_script("window.deviceState={permission:true,device:{},history:[]};window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({}),pick:n=>{window.picks=(window.picks||[]).concat(n)},capture:()=>{window.captures=(window.captures||0)+1;return JSON.stringify({ok:true,id:'test-camera'})},captureAck:()=>JSON.stringify({ok:true}),printBatch:()=>{throw Error('Printing forbidden')}}")
 page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')

 page.evaluate('Promise.all([NameLabels.ready,CardArt.ready])')
 page.evaluate('BoothTemplates.ready')
 page.set_viewport_size({'width':390,'height':844})
 page.evaluate("Object.defineProperty(screen,'width',{value:390,configurable:true});Object.defineProperty(screen,'height',{value:844,configurable:true});state.media=5012;state.mode='photo';state.photos=[];addPhotos([{src:'/sample.svg'}])")
 page.evaluate('Studio.landscape=()=>innerWidth>innerHeight;updateEditorOrientation();render()')
 page.wait_for_function('!!printPreview&&canAdjustPhoto()')
 assert not errors,errors



 cdp=page.context.new_cdp_session(page)
 def touch(x,y,dx=0,dy=0):
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
  if dx or dy:
   for i in range(1,11):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+dx*i/10,'y':y+dy*i/10,'id':1}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(150)
 def point(expr):
  return page.evaluate("""()=>{const f="""+expr+""",r=$('preview').getBoundingClientRect(),v=CropEditor.geometry();return {x:r.left+(f.x+v.tx)*r.width/$('preview').width,y:r.top+(f.y+v.ty)*r.height/$('preview').height}}""")
 def background():
  return page.evaluate("""()=>{const r=$('preview').getBoundingClientRect();for(let y=Math.max(65,r.top+8);y<Math.min(r.bottom-8,innerHeight-180);y+=6)for(let x=r.left+r.width*.65;x<r.right-12;x+=6)if(PreviewActions.area({clientX:x,clientY:y})==='background'&&PreviewActions.area({clientX:x-80,clientY:y})==='background')return{x,y};throw Error('No background')}""")
 page.evaluate("PhotoFlow.apply(TEMPLATE_CATALOG.find(t=>t.slots===4).id);TemplateStudio.setGroup('all');render()")
 page.wait_for_timeout(150)
 # Empty slots are hit-tested and open the normal picker exactly once.
 assert page.evaluate('emptyPhotoFrames.length')==3
 p=point('({x:emptyPhotoFrames[0].x+emptyPhotoFrames[0].w/2,y:emptyPhotoFrames[0].y+emptyPhotoFrames[0].h/2})')
 touch(**p);assert page.evaluate('picks')==[5]
 before=page.evaluate('TemplateStudio.selectedId()');b=background();touch(**b,dx=-80)
 after=page.evaluate('TemplateStudio.selectedId()');assert before!=after,(before,after)
 assert not page.evaluate('EffectBrowser.active()')
 page.locator('#editorUndo').click();assert page.evaluate('TemplateStudio.selectedId()')==before
 page.evaluate('TemplateStudio.setGroup(TemplateStudio.groupFor(TemplateStudio.selectedId()));render()')
 group=page.evaluate('TemplateStudio.currentGroup()');b=background();touch(**b,dx=-80)
 assert page.evaluate('TemplateStudio.groupFor(TemplateStudio.selectedId())')==group
 # Swipes inside a photo must never switch the template.
 old=page.evaluate('TemplateStudio.selectedId()');p=point('({x:photoFrames[0].x+photoFrames[0].w*.7,y:photoFrames[0].y+photoFrames[0].h/2})');touch(**p,dx=-40)
 assert page.evaluate('TemplateStudio.selectedId()')==old
 # Plain calendar, year crossing, reverse and photo calendar.
 page.evaluate("state.mode='calendar';state.calendarLayout='plain';state.month='2026-12';render()")
 b=background();touch(**b,dx=-80);assert page.evaluate('state.month')=='2027-01'
 touch(**b,dx=80);assert page.evaluate('state.month')=='2026-12'
 page.evaluate("state.calendarLayout='photo';render()")
 b=background();touch(**b,dx=-80);assert page.evaluate('state.month')=='2027-01'
 p=point('({x:photoFrames[0].x+photoFrames[0].w*.6,y:photoFrames[0].y+photoFrames[0].h/2})');touch(**p,dx=-60)
 assert page.evaluate('state.month')=='2027-01'
 # Vertical swipes and a second finger outside the paper must not turn a month.
 b=background();touch(**b,dy=45);assert page.evaluate('state.month')=='2027-01'
 b=background();a={'x':b['x'],'y':b['y'],'id':1};outside={'x':25,'y':25,'id':2}
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[a]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[a,outside]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[outside]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 b=background();touch(**b,dx=-80);assert page.evaluate('state.month')=='2027-02'
 # A printed text layer keeps priority over month navigation.
 page.evaluate("LayerEditor.create({kind:'text',text:'TEST',fx:.7,fy:.6});LayerEditor.select(null);closeSheet();render()")
 layer=page.evaluate("""()=>{const o=LayerEditor.list().at(-1),s=LayerEditor.space(o),m=LayerEditor.metrics(o,s.w,s.h);return{x:s.x+m.x,y:s.y+m.y}}""")
 p=point(str(layer).replace("'",'"'));touch(**p,dx=-60);assert page.evaluate('state.month')=='2027-02'
 page.evaluate("LayerEditor.paperList().splice(0);LayerEditor.select(null);render()")
 # Camera belongs inside the native picker, never the editor's selected-photo rail.
 assert page.locator('#capturePhoto').count()==0
 page.evaluate("PhotoFlow.apply('grid4');addPhotos(Array.from({length:5},()=>({src:'/sample.svg'})))")
 page.wait_for_function("state.photos.length===6&&document.querySelectorAll('#photos [data-photo]').length===6");assert page.locator('#photos [data-photo]').count()==6
 assert page.locator('#paperStage').bounding_box()['width']>=389
 # Paper and connection have distinct responsibilities, with correct parent return.
 page.evaluate("deviceState.device=native.device={connected:true,media:5012,checkedAt:Date.now()};openDevice()")
 assert page.locator('#connectNow').count()==1 and page.locator('[data-paper]').count()==0
 assert page.locator('#airprintLayout').count()==0
 assert page.locator('#changePaper').count()==0
 page.evaluate("$('menuBtn').click();$('menuPaper').click()");assert page.locator('[data-paper]').count()==2
 assert page.locator('#connectNow').count()==0 and page.locator('#airprintLayout').count()==1
 page.locator('#settingsBack').click();assert page.evaluate('sheetKind')=='menu'
 page.evaluate("$('menuBtn').click();$('menuPaper').click();openPaper()")
 page.locator('#settingsBack').click();assert page.evaluate('sheetKind')=='menu';page.evaluate('closeSheet()')
 assert not errors,errors
 page.screenshot(path='preview-actions-phone.jpg',type='jpeg',quality=70)
 browser.close()
 print('PASS preview actions: real touch templates/group/undo/photo exclusion, calendar year/month/photo, empty slot picker, no editor camera, six photos, width/heights, settings separation and back')
