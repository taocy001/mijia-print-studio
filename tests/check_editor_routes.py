from effect_choices import open_effect_choices
"""Audit real editor entry points, empty states and offline preview."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width,height in [(390,700),(411,828),(1280,720)]:
  page=browser.new_page(viewport={'width':width,'height':height});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  server={'permission':True,'device':{'connected':True,'media':5012,'checkedAt':int(time.time()*1000)},'history':[]}
  def route(r):
   assert r.request.method=='GET','Audit must not print'
   path=urlparse(r.request.url).path
   if path=='/api/state':r.fulfill(json=server);return
   file=ROOT/'assets'/(path.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.ImageExport&&window.CropEditor');page.evaluate('LayerEditor.ready')
  page.evaluate("async()=>{closeSheet();const photo={src:'/sample.svg',turn:0,zoom:1,x:0,y:0,fit:'cover',filter:'none',overlays:[]};await loadPhoto(photo);state={...defaults,photos:[photo],active:0};render()}")
  cases={'polaroid':'[data-setting=fit]','label':'#nameGapInput','id':'#idBackgroundOptions','collage':'[data-setting=collageLayout]','calendar':'#lunarToggle','card':'#extraText','idcard':'[data-setting=idCardOrientation]'}
  for mode,control in cases.items():
   page.evaluate('closeSheet()')
   page.locator('#menuBtn').click();page.locator('#menuWorkType').click();page.locator('[data-layout-mode='+mode+']').click()
   assert page.locator(control).count()>0,(width,mode,'initial')
   page.evaluate('closeSheet()');open_effect_choices(page,'#layoutBtn')
   assert page.locator(control).count()>0,(width,mode,'reopened')
   assert page.locator('#templateBtn').is_disabled(),mode
   if mode in ['label','card']:
    before=page.evaluate('JSON.stringify(active())')
    assert page.locator('.photo-tools').is_hidden()
    page.evaluate("['zoomIn','zoomOut','rotate','reset'].forEach(id=>document.getElementById(id).click())")
    assert page.evaluate('JSON.stringify(active())')==before
   if mode in ['card','idcard']:
    assert page.locator('[data-setting=fit]').count()==0
  page.evaluate("closeSheet();state.mode='calendar';state.calendarLayout='plain';render()")
  open_effect_choices(page,'#layoutBtn');assert page.locator('[data-setting=fit]').count()==0
  assert page.locator('.photo-tools').is_hidden()
  page.evaluate("closeSheet();state.mode='photo';render()")
  open_effect_choices(page,'#layoutBtn');assert page.locator('[data-setting=orientation]').count()>0
  server['device'].update(media=5009,checkedAt=int(time.time()*1000))
  page.evaluate("native.device.media=5009;native.device.checkedAt=Date.now();syncPaper()")
  assert page.locator('[data-setting=orientation]').count()==0
  page.evaluate('closeSheet();openPaper()')
  page.evaluate('goBack()');assert page.evaluate("sheetKind==='device'")
  page.evaluate('goBack()');assert page.evaluate("sheetKind==='menu'")
  page.evaluate('goBack()');assert page.evaluate("sheetKind!=='menu'")
  for theme in ['light','dark']:
   page.evaluate('closeSheet()');page.emulate_media(color_scheme=theme);page.locator('#menuBtn').click()
   contrast=page.evaluate('''()=>{const h=document.querySelector('#sheet>header'),t=document.getElementById('sheetTitle');const lum=s=>{const c=s.match(/[\\d.]+/g).slice(0,3).map(Number).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4});return c[0]*.2126+c[1]*.7152+c[2]*.0722};let bg=h;while(bg.parentElement&&getComputedStyle(bg).backgroundColor==='rgba(0, 0, 0, 0)')bg=bg.parentElement;const a=lum(getComputedStyle(bg).backgroundColor),b=lum(getComputedStyle(t).color);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)}''')
   assert contrast>=4.5,(width,theme,contrast)
  page.evaluate("closeSheet();state.mode='photo';state.photos=[];render()")
  assert page.locator('#addTextQuick').is_disabled() and page.locator('#addEmojiQuick').is_disabled()
  page.locator('#filterBtn').click();assert page.locator('#toneSharp').is_disabled()
  page.evaluate("async()=>{closeSheet();const photo={src:'/sample.svg',turn:0,zoom:1,x:0,y:0,fit:'cover',filter:'none',overlays:[]};await loadPhoto(photo);state={...defaults,media:5009,photos:[photo],active:0};render()}")
  page.wait_for_timeout(150)
  before=page.locator('#preview').bounding_box();page.locator('#addTextQuick').click();page.locator('#layerText').fill('Audit');page.wait_for_timeout(200)
  after=page.locator('#preview').bounding_box()
  if width<1000:assert abs(before['y']-after['y'])<2,(width,before,after)
  page.evaluate('closeSheet();LayerEditor.select(null)')
  server.update(permission=False,device={})
  page.evaluate('async()=>{await BrowserTransport.refresh();poll()}')
  page.locator('#printBtn').click();page.wait_for_selector('.print-pages img')
  assert page.locator('#confirmSend').is_disabled()
  assert page.locator('#connectBeforePrint').is_visible()
  assert page.locator('.print-pages img').first.get_attribute('role')=='button'
  for busy,unresolved in [(True,False),(False,True)]:
   server.update(permission=True,busy=busy,unresolved=unresolved,job={'token':'test-active','phase':'printing'},device={'connected':True,'media':5009,'checkedAt':int(time.time()*1000)})
   page.evaluate('async()=>{closeSheet();await BrowserTransport.refresh();poll()}')
   assert page.locator('#printBtn').is_enabled()
   page.locator('#printBtn').click();page.wait_for_selector('.print-pages img')
   assert page.locator('#confirmSend').is_disabled()
   page.locator('#confirmSend').dispatch_event('click')
   assert '当前任务尚未结束' in page.locator('#toast').text_content()
  server.update(busy=False,unresolved=False,job={})
  page.evaluate('closeSheet()')
  missing={'token':'missing-file','phase':'done','file':'prints/missing.jpg','media':5009,'message':'打印完成'}
  server['history']=[missing]
  page.evaluate('(job)=>{native.history=[job];openHistory()}',missing)
  page.locator('[data-history="0"]').click();page.locator('#importHistory').click()
  page.wait_for_function("document.getElementById('toast').textContent.includes('历史照片无法读取')")
  assert page.locator('#importHistory').is_enabled()
  assert not errors,errors
  page.close()
 browser.close()
print('PASS: actual layout routes, contextual tools, empty states, paper changes, theme contrast, stable text editing, offline preview and history failure; no printing')
