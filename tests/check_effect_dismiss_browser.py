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
 def swipe(x,y,dx=0,dy=0):
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
  for i in range(1,11):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+dx*i/10,'y':y+dy*i/10,'id':1}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(200)
 def center(selector):
  r=page.locator(selector).bounding_box();return {'x':r['x']+r['width']/2,'y':r['y']+r['height']/2}
 def value(kind):return page.evaluate('TemplateStudio.selectedId()' if kind=='templates' else 'active().filter||"none"')
 def lower():return page.evaluate("""()=>{const r=$('preview').getBoundingClientRect(),w=$('preview').closest('.workspace').getBoundingClientRect();return{x:r.left+r.width/2,y:Math.min(r.bottom,w.bottom)-45}}""")
 for kind,button in [('templates','#templateBtn'),('filters','#filterBtn')]:
  page.evaluate("PhotoFlow.apply('single');render()")
  before=value(kind);page.locator(button).click()
  page.evaluate('EffectBrowser.step(-1)' if kind=='templates' else 'EffectBrowser.step(1)');page.wait_for_timeout(150)
  selected=value(kind);assert selected!=before,(kind,selected,before)
  swipe(**center('#effectChoices'),dy=65)
  assert not page.evaluate('EffectBrowser.active()'),kind+' rail must dismiss'
  assert value(kind)==selected,kind+' down dismiss must commit'
  page.locator('#editorUndo').click();assert value(kind)==before,kind+' one undo'
  page.locator('#editorRedo').click();assert value(kind)==selected
  page.locator(button).click();swipe(**lower(),dy=65)
  assert not page.evaluate('EffectBrowser.active()'),kind+' lower preview dismiss'
  page.locator(button).click();swipe(**center('#effectChoices'),dy=-45)
  assert page.evaluate('EffectBrowser.active()'),kind+' upward swipe must not dismiss'
  page.evaluate('EffectBrowser.exit()')
 # A horizontal rail swipe must still browse and settle on its center.
 page.evaluate("PhotoFlow.apply('single');render()")
 page.locator('#filterBtn').click();before=value('filters');swipe(**center('#effectChoices'),dx=-120)
 page.wait_for_timeout(600);assert page.evaluate('EffectBrowser.active()') and value('filters')!=before
 # Short downward movement must neither dismiss nor click a different effect.
 before=value('filters');swipe(**center('#effectChoices'),dy=20)
 assert page.evaluate('EffectBrowser.active()') and value('filters')==before
 # Second finger outside the effect rail cancels dismissal, even when released last.
 point=center('#effectChoices');a={**point,'id':1};b={'x':25,'y':25,'id':2}
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[a]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[a,b]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{**a,'y':a['y']+60},b]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[b]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 assert page.evaluate('EffectBrowser.active()')
 # Next clean gesture after all fingers leave works normally.
 swipe(**center('#effectChoices'),dy=65);assert not page.evaluate('EffectBrowser.active()')
 # Existing cancel still restores the entry value.
 before=value('filters');page.locator('#filterBtn').click();page.evaluate('EffectBrowser.step(1)');page.locator('#effectCancel').click()
 assert not page.evaluate('EffectBrowser.active()') and value('filters')==before
 # Landscape vertical rail retains scrolling; the bottom heading still dismisses.
 page.set_viewport_size({'width':844,'height':390});page.evaluate('updateEditorOrientation();render()');page.locator('#filterBtn').click()
 swipe(**center('#effectChoices'),dy=55);assert page.evaluate('EffectBrowser.active()')
 r=page.locator('.effect-heading').bounding_box();swipe(x=r['x']+r['width']/2,y=r['y']+5,dy=47)
 assert not page.evaluate('EffectBrowser.active()')
 # Printer connectivity exposes no duplicate paper entry or paper controls.
 page.set_viewport_size({'width':390,'height':844});page.evaluate("updateEditorOrientation();deviceState.device=native.device={connected:true,checkedAt:Date.now(),media:5012};render()")
 page.locator('#menuBtn').click();assert page.locator('#menuPaper').count()==1;page.locator('#menuDevice').click()
 assert page.locator('#changePaper').count()==0 and page.locator('[data-paper]').count()==0
 assert page.locator('#connectNow').count()==1 and '相纸与方向' not in page.locator('#sheetBody').inner_text()
 page.locator('#settingsBack').click();page.locator('#menuPaper').click()
 assert page.locator('[data-paper]').count()==2 and page.locator('#airprintLayout').count()==1
 page.evaluate('openPaper();openPaper()');page.locator('#settingsBack').click();assert page.evaluate('sheetKind')=='menu'
 assert not errors,errors
 browser.close()
 print('PASS downward dismiss commits/undo/redo, both modes and surfaces, horizontal/upward/multitouch/cancel/landscape preserved; unique paper menu with full controls')
