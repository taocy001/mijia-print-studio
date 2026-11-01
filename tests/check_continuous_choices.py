"""Keep choice panels open while comparing visual options."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
assets=Path(__file__).resolve().parents[1]/'assets'
with sync_playwright() as p:
 browser=p.chromium.launch()
 for native in [True,False]:
  for width,height in [(390,700),(844,390),(1440,900)]:
   page=browser.new_page(viewport={'width':width,'height':height});errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   def close_panel():
    if page.locator('#closeSheet').is_visible():page.locator('#closeSheet').click()
   if native:page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{},history:[]}),printBatch:()=>{throw Error('Printing forbidden')}}")
   def route(r):
    assert r.request.method=='GET'
    path=urlparse(r.request.url).path
    if path=='/api/state':r.fulfill(json={'permission':True,'device':{},'history':[]});return
    file=assets/(path.lstrip('/') or 'index.html')
    if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
    else:r.fulfill(status=404,body='Missing')
   page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')
   page.evaluate("async()=>{await addPhotos([{src:'/sample.svg'}]);render()}")
   print('Checking',native,width,height,flush=True);page.locator('#templateBtn').click();page.wait_for_function("typeof $('noTemplate')?.onclick==='function'&&typeof document.querySelector('[data-template]')?.onclick==='function'")
   assert page.locator('#scrim').evaluate("e=>{const s=getComputedStyle(e);return s.backdropFilter==='none'&&s.backgroundColor==='rgba(0, 0, 0, 0)'}")
   assert page.locator('#sheet').evaluate("e=>getComputedStyle(e).boxShadow==='none'")
   for index in [29,20,19,0]:
    choice=page.locator('[data-template]').nth(index);choice.scroll_into_view_if_needed();scroll=page.locator('#sheetBody').evaluate('(e)=>e.scrollTop');panel=page.locator('#sheet').bounding_box();key=choice.get_attribute('data-template');choice.click();page.wait_for_timeout(100)
    assert page.evaluate("sheetKind==='templates'&&!$('sheet').hidden")
    assert page.locator('#sheet').bounding_box()==panel
    assert abs(page.locator('#sheetBody').evaluate('(e)=>e.scrollTop')-scroll)<1
    assert page.evaluate('active().templateId')==key and choice.get_attribute('aria-pressed')=='true'
    assert page.locator('.template-card.selected').count()==1
   page.locator('#noTemplate').click();assert page.evaluate("sheetKind==='templates'&&state.mode==='photo'&&!active().templateId")
   close_panel();page.locator('#filterBtn').click();page.locator('[data-filter]').nth(1).click();assert page.evaluate("sheetKind==='filters'")
   close_panel();page.locator('#menuBtn').click();page.locator('#menuCoat').click();page.locator('[data-coat=grid]').click();assert page.evaluate("sheetKind==='coat'")
   page.evaluate("closeSheet();LayerEditor.create({kind:'emoji',text:Object.values(SHARED_EMOJI)[0][0].text,fx:.3,fy:.4,sizePct:17,angle:15});LayerEditor.openEditor(LayerEditor.selected())")
   identity=page.evaluate('JSON.stringify(active().overlays.map(({id,fx,fy,sizePct,angle})=>({id,fx,fy,sizePct,angle})))')
   page.locator('#replaceEmoji').click()
   for i in [1,2,3]:
    choice=page.locator('[data-emoji]').nth(i);choice.click();assert page.evaluate("sheetKind==='layers'&&!$('sheet').hidden")
    assert choice.get_attribute('aria-pressed')=='true' and page.locator('[data-emoji][aria-pressed=true]').count()==1
    assert page.evaluate('JSON.stringify(active().overlays.map(({id,fx,fy,sizePct,angle})=>({id,fx,fy,sizePct,angle})))')==identity
   page.locator('#emojiHidden').check();assert page.evaluate('active().overlays[0].hidden')
   close_panel();page.locator('#addEmojiQuick').click();page.locator('[data-emoji]').first.click();assert page.evaluate("sheetKind!=='layers'&&active().overlays.length===2")
   assert not errors,errors
   page.close()
 browser.close()
print('PASS: native/web portrait, landscape and desktop continuous template/filter/coat choices; emoji replacement retains object; additions return to canvas; no printing')
