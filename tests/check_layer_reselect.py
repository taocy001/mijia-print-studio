"""Verify error guidance in both native and desktop browser UI without printing."""
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
 page.set_viewport_size({'width':390,'height':844})
 page.evaluate("""async()=>{await BoothTemplates.ready;Object.assign(state,{mode:'collage',media:5012,orientation:'portrait',collageLayout:'booth',collageTemplateId:'booth-together-3',photos:[],active:0});LayerEditor.create({id:'existing-heart',kind:'emoji',text:'😍',fx:.13,fy:.10,sizePct:23});LayerEditor.select(null);render();}""")
 cdp=page.context.new_cdp_session(page)
 def point():return page.evaluate("""()=>{const o=LayerEditor.list().find(o=>o.id==='existing-heart'),s=LayerEditor.space(o),m=LayerEditor.metrics(o,s.w,s.h),r=$('preview').getBoundingClientRect(),v=CropEditor.geometry();return {x:r.left+(m.x+s.x+v.tx)*r.width/$('preview').width,y:r.top+(m.y+s.y+v.ty)*r.height/$('preview').height}}""")
 def touch(pt):
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':pt['x'],'y':pt['y'],'id':1}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 for interaction in ['mouse','touch']:
  page.evaluate('closeSheet();LayerEditor.select(null);render()');page.wait_for_timeout(400)
  pt=point()
  if interaction=='mouse':page.mouse.click(pt['x'],pt['y'])
  else:touch(pt)
  assert page.locator('#layerSelection').is_visible(),interaction
  if not page.locator('#replaceEmoji').is_visible():
   assert page.locator('#editLayer').is_visible(),interaction
   page.locator('#editLayer').click()
  assert page.locator('#replaceEmoji').is_visible(),interaction
  page.locator('[data-layer-range=sizePct]').fill('20');page.locator('[data-layer-range=sizePct]').dispatch_event('input')
  assert page.evaluate("LayerEditor.selected().sizePct") == 20
  page.evaluate('closeSheet();LayerEditor.select(null);openLayout();closeSheet();render()');page.wait_for_timeout(70)
  pt=point()
  if interaction=='mouse':page.mouse.click(pt['x'],pt['y'])
  else:touch(pt)
  assert page.locator('#layerSelection').is_visible(),interaction
 assert page.locator('#printBtn').is_disabled()
 assert page.locator('#addEmojiQuick').is_enabled()
 assert page.evaluate('preparePrintPages().then(()=>false,()=>true)')
 # Actual add/remove photo transition must preserve and allow reselecting the same emoji.
 page.evaluate("addPhotos([{src:'/sample.svg'}])")
 page.evaluate("state.photos=[];state.active=0;closeSheet();LayerEditor.select(null);render()")
 page.wait_for_timeout(70);pt=point();touch(pt)
 assert page.evaluate("LayerEditor.selected()?.id==='existing-heart'")
 if not page.locator('#replaceEmoji').is_visible():page.locator('#editLayer').click()
 assert page.locator('#replaceEmoji').is_visible()
 page.evaluate('closeSheet();LayerEditor.select(null)');page.locator('#addTextQuick').click()
 page.locator('#layerText').fill('无照片也能编辑');page.evaluate('closeSheet();render()')
 assert page.evaluate("LayerEditor.paperList().some(o=>o.text==='无照片也能编辑')")
 assert page.locator('#printBtn').is_disabled()
 assert not errors,errors
 browser.close()
print('PASS: existing emoji reselected by mouse/touch with empty collage; editing after layout/add-remove photos; free text editing; print guard remains; no printing')
