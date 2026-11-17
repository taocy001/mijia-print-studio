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
 page.evaluate('BoothTemplates.ready')
 assert page.locator('#typeTabs button').all_text_contents()==['照片','证件照','ID 卡贴','月历','姓名贴','卡片']
 # Resume an existing multi-photo template with its full-paper emoji, without moving it.
 page.evaluate("Object.assign(state,{mode:'collage',media:5012,photos:[],active:0,collageLayout:'booth',collageTemplateId:'booth-together-3',paperLayers:{collage:[{id:'keep',kind:'emoji',text:'😍',fx:.81,fy:.84,sizePct:23,angle:0}]}});render()")
 assert page.locator('[data-print-type=photo]').get_attribute('aria-pressed')=='true'
 assert page.locator('#photoTypeTools').is_visible() and not page.locator('#contextTools').is_visible()
 assert page.locator('#photoTypeTools button').all_text_contents()==['排版','色调','模板','文字','表情']
 assert page.evaluate("LayerEditor.paperList()[0].fx===.81&&LayerEditor.paperList()[0].fy===.84")
 page.locator('#templateBtn').click();page.wait_for_selector('[data-template-category]')
 page.locator('[data-template-category=together]').click();page.locator('[data-template=booth-together-2]').click()
 assert page.locator('[data-print-type=photo]').get_attribute('aria-pressed')=='true'
 page.evaluate('closeSheet();openLayout()');page.locator('[data-photo-arrangement=single]').click()
 assert page.evaluate('state.mode')=='photo'
 assert page.evaluate("LayerEditor.paperList().some(o=>o.id==='keep')")
 page.locator('[data-photo-arrangement=multiple]').click();assert page.evaluate('state.mode')=='collage'
 page.evaluate('closeSheet()');page.locator('[data-print-type=id]').click();page.locator('[data-print-type=photo]').click()
 assert page.evaluate("state.mode==='collage'&&state.collageTemplateId==='booth-together-2'")
 page.locator('#templateBtn').click();page.wait_for_selector('[data-template-category=puzzle]');page.locator('[data-template-category=puzzle]').click()
 page.locator('[data-template=booth-puzzle-1]').click();assert page.evaluate('state.mode')=='template'
 assert page.locator('[data-print-type=photo]').get_attribute('aria-pressed')=='true'
 assert page.evaluate('preparePrintPages().then(()=>false,()=>true)')
 page.evaluate("closeSheet();addPhotos([{src:'/sample.svg'}])")
 page.evaluate("TemplateStudio.apply('booth-puzzle-1');render()")
 for media,orientation in [(5012,'portrait'),(5012,'landscape'),(5009,'portrait'),(5014,'portrait')]:
  page.evaluate('([m,o])=>{state.media=m;state.orientation=o;render()}',[media,orientation])
  assert page.evaluate("""()=>{let curves=0;const old=CanvasRenderingContext2D.prototype.bezierCurveTo;CanvasRenderingContext2D.prototype.bezierCurveTo=function(...args){curves++;return old.apply(this,args)};try{compose()}finally{CanvasRenderingContext2D.prototype.bezierCurveTo=old}return curves>=36}""")
  assert page.evaluate('preparePrintPages().then(p=>p.length===1)')
 assert page.evaluate("ProjectFile.encode().then(raw=>ProjectFile.decode(raw)).then(p=>p.editing.photos[0].templateId==='booth-puzzle-1'&&p.editing.paperLayers.photo[0].id)")
 if os.environ.get('PUZZLE_PREVIEW'):
  import base64
  page.evaluate("state.media=5012;state.orientation='portrait';state.paperLayers={};render()")
  data=page.evaluate("compose().toDataURL('image/png').split(',')[1]")
  Path(os.environ['PUZZLE_PREVIEW']).write_bytes(base64.b64decode(data))
 assert not errors,errors
 browser.close()
print('PASS: unified photo tools; multi-photo templates retain photo tab; single/multiple switch and roundtrip; saved emoji coordinates; puzzle curves in 4 formats; real print data and project save; no printing')
