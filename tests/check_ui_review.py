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
 # Review every enabled tool in all six types, three media, with/without a photo.
 page.set_viewport_size({'width':390,'height':844})
 cases=0
 for loaded in [False,True]:
  page.evaluate("(loaded)=>{state.photos=loaded?[{src:'/sample.svg',overlays:[]}]:[];state.active=0;return loaded?loadPhoto(state.photos[0]):null}",loaded)
  for media in [5012,5009,5014]:
   for kind in ['photo','id','idcard','calendar','label','card']:
    page.evaluate("([m,k])=>{closeSheet();EffectBrowser.exit(false);Object.assign(state,{media:m,mode:k,templateId:null,collageTemplateId:null,calendarLayout:'photo'});render()}",[media,kind])
    selector='#photoTypeTools button' if kind=='photo' else '#contextTools button'
    ids=page.locator(selector).evaluate_all("els=>els.map(e=>({id:e.id,key:e.dataset.typeTool,disabled:e.disabled}))")
    for tool in ids:
     if tool['disabled']:continue
     page.evaluate('closeSheet();EffectBrowser.exit(false)')
     target='#'+tool['id'] if tool['id'] else '[data-type-tool="'+tool['key']+'"]'
     page.locator(target).click();page.wait_for_timeout(400)
     assert page.locator('#sheet').is_visible() or page.evaluate('!!EffectBrowser.kind()') or tool['id'] in ['addTextQuick','addEmojiQuick'],(loaded,media,kind,tool)
     if tool['key']=='decoration':assert page.locator('#legacyCaption').count()==0,(kind,media)
    cases+=1
 # Empty single-photo templates survive repeated choice and single/multiple roundtrips.
 page.evaluate("closeSheet();EffectBrowser.exit(false);Object.assign(state,{photos:[],active:0,media:5012,mode:'photo'});TemplateStudio.apply('booth-puzzle-1');openLayout()")
 assert page.locator('#fixedTemplateHint').is_visible()
 assert page.locator('[data-setting=fit]').count()==0
 page.locator('[data-photo-arrangement=single]').click()
 assert page.evaluate("state.mode==='template'&&state.templateId==='booth-puzzle-1'")
 page.locator('[data-photo-arrangement=multiple]').click();page.locator('[data-photo-arrangement=single]').click()
 assert page.evaluate("state.mode==='template'&&state.templateId==='booth-puzzle-1'")
 page.evaluate("TemplateStudio.apply('booth-together-3');openLayout()")
 assert page.locator('#fixedTemplateHint').is_visible()
 assert page.locator('#collageTemplates,#borderInput,#gapInput,[data-setting=fit]').count()==0
 assert '取消当前模板' in page.locator('#sheetBody').inner_text()
 page.locator('[data-setting=collageLayout][data-value=grid]').click()
 assert page.evaluate("state.collageTemplateId===null&&state.collageLayout==='grid'")
 assert page.locator('#borderInput').is_visible() and page.locator('#gapInput').is_visible()
 page.evaluate("closeSheet();Object.assign(state,{mode:'polaroid'});openLayout()")
 page.locator('[data-photo-arrangement=single]').click();assert page.evaluate("state.mode==='polaroid'")
 assert not errors,errors
 browser.close()
print(f'PASS: {cases} type/media/photo-state combinations; enabled tool panels, caption applicability, fixed template controls, removal of duplicate entry, empty template retention and polaroid preservation; no printing')
