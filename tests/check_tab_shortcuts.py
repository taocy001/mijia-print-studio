"""Five-tab activation shares one pending action and never duplicates layers."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes,time
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for native,width,height in [(True,390,844),(False,390,844),(True,844,390),(False,1280,800)]:
  page=browser.new_page(viewport={'width':width,'height':height},is_mobile=width<1000,has_touch=width<1000);errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  if native:page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{media:5012,checkedAt:Date.now()},history:[]}),landscape:()=>innerWidth>innerHeight}")
  def route(r):
   assert r.request.method=='GET'
   path=urlparse(r.request.url).path
   if path=='/api/state':r.fulfill(json={'permission':True,'device':{'media':5012,'checkedAt':int(time.time()*1000)},'history':[]});return
   f=root/'assets'/(path.lstrip('/') or 'index.html')
   r.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream') if f.is_file() else r.fulfill(status=404,body='Missing')
  page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')
  page.evaluate("async()=>{await addPhotos([{src:'/sample.svg'},{src:'/sample.svg'}]);state.photos.forEach(p=>p.facePending=false);selectPhoto(0);LayerEditor.create({id:'text-one',kind:'text',text:'First'});LayerEditor.create({id:'text-two',kind:'text',text:'Second'});LayerEditor.create({id:'emoji-one',kind:'emoji',text:'😀'});LayerEditor.select('text-one');LayerEditor.select(null);render();}")
  page.wait_for_timeout(100)
  page.locator('#addTextQuick').dblclick();page.wait_for_selector('#layerText')
  assert page.locator('#layerText').input_value()=='First'
  assert page.locator('#layerText').evaluate('e=>e===document.activeElement')
  assert page.evaluate('active().overlays.length')==3
  page.evaluate('closeSheet()');page.locator('#addEmojiQuick').dblclick();page.wait_for_selector('#replaceEmoji')
  assert page.evaluate("LayerEditor.selected().id==='emoji-one'&&active().overlays.length===3")
  page.evaluate('closeSheet()');page.locator('#addTextQuick').click();page.wait_for_selector('#layerText')
  assert page.locator('#layerText').input_value()=='' and page.evaluate('active().overlays.length')==3
  page.locator('#layerText').fill('New text');page.evaluate('closeSheet()')
  page.locator('#addTextQuick').dblclick();page.wait_for_selector('#layerText');assert page.locator('#layerText').input_value()=='New text'
  page.evaluate('closeSheet()');page.locator('#filterBtn').dblclick();page.wait_for_function("EffectBrowser.kind()==='filters'")
  page.locator('#addEmojiQuick').dblclick();page.wait_for_selector('#replaceEmoji');assert page.evaluate('!EffectBrowser.active()')
  page.evaluate('closeSheet()')
  # Programmatic click events retain real pointer click detail while keeping intervals deterministic.
  page.evaluate("()=>{for(const id of ['filterBtn','addTextQuick','addEmojiQuick'])$(id).dispatchEvent(new MouseEvent('click',{bubbles:true,detail:1}));}")
  page.wait_for_timeout(450)
  assert page.evaluate("sheetKind==='layers'&&$('sheetTitle').textContent==='选择表情'"),(native,width,page.evaluate("({sheetKind,title:$('sheetTitle').textContent,mode:EffectBrowser.kind()})"),errors)
  page.wait_for_timeout(350);assert page.evaluate("$('sheetTitle').textContent==='选择表情'&&!EffectBrowser.active()")
  page.evaluate("closeSheet();$('addTextQuick').dispatchEvent(new MouseEvent('click',{bubbles:true,detail:1}));selectPhoto(1)")
  page.wait_for_timeout(350);assert page.locator('#layerText').count()==0,'Old pending text action followed photo switch'
  page.evaluate("$('addTextQuick').dispatchEvent(new MouseEvent('click',{bubbles:true,detail:1}));goBack()")
  page.wait_for_timeout(350);assert page.locator('#layerText').count()==0,'Back failed to cancel pending entry'
  page.locator('#addTextQuick').dblclick();page.wait_for_selector('#layerText')
  assert page.locator('#layerText').input_value()=='' and page.evaluate('active().overlays.length')==0
  page.evaluate("closeSheet();state.mode='label';render()")
  page.locator('#addTextQuick').dblclick();page.wait_for_selector('#labelInput')
  assert page.locator('#layerText').count()==0,'Name label editor was replaced'
  assert not errors,errors
  page.close()
 browser.close()
print('PASS: single-add/double-resume, empty states, shared cancellation, per-photo scope, back and name-label routing; no printing')
