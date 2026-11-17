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

 page.set_viewport_size({'width':390,'height':844})
 page.evaluate('Promise.all([NameLabels.ready,CardArt.ready])')
 assert page.locator('#typeTabs button').all_text_contents()==['照片','证件照','ID 卡贴','月历','姓名贴','卡片']
 assert page.locator('#photoTypeTools button').all_text_contents()==['排版','色调','模板','文字','表情']
 page.locator('#menuBtn').click();assert page.locator('#menuWorkType').count()==0;page.evaluate('closeSheet()')
 widths=[]
 for kind,tool,target in [('calendar','month','#monthInput'),('id','size','[data-setting=idSize]'),('label','style','#nameTemplateChoices'),('card','content','#labelInput'),('idcard','direction','[data-setting=idCardOrientation]')]:
  page.locator(f'[data-print-type="{kind}"]').click();page.wait_for_function('(k)=>state.mode===k',arg=kind)
  assert not page.locator('#photoTypeTools').is_visible()
  assert page.locator('#contextTools').is_visible()
  buttons=page.locator('#contextTools button');assert 3<=buttons.count()<=5
  widths.append(buttons.first.bounding_box()['width'])
  page.locator(f'[data-type-tool="{tool}"]').click();assert page.locator(target).first.is_visible(),(kind,tool)
  page.evaluate('closeSheet()')
 assert max(widths)-min(widths)<1,widths
 page.locator('[data-print-type="calendar"]').click();page.locator('[data-type-tool="month"]').click()
 page.locator('#monthInput').fill('2027-02');page.locator('#monthInput').dispatch_event('input')
 assert page.evaluate('state.month')=='2027-02'
 assert not page.locator('#lunarToggle').is_visible()
 page.evaluate('closeSheet()');page.locator('[data-type-tool="calendarLayout"]').click()
 page.locator('[data-setting=calendarLayout][data-value=plain]').click()
 assert page.locator('[data-setting=calendarLayout]').first.is_visible()
 assert not page.locator('#monthInput').is_visible()
 assert page.locator('[data-type-tool="tone"]').is_disabled()
 before=page.locator('#contextTools button').count()
 page.locator('[data-setting=calendarLayout][data-value=photo]').click()
 assert page.locator('#contextTools button').count()==before
 page.evaluate('closeSheet()');page.locator('[data-print-type="photo"]').click()
 page.evaluate("state.photos=[{src:'/sample.svg',overlays:[]}];state.active=0;loadPhoto(state.photos[0])");page.evaluate('render()')
 page.locator('#templateBtn').click();page.wait_for_selector('#polaroidTemplate');page.locator('#polaroidTemplate').click()
 page.wait_for_function("state.mode==='polaroid'")
 assert page.locator('[data-print-type=photo]').get_attribute('aria-pressed')=='true'
 assert page.locator('#photoTypeTools').is_visible()
 page.locator('#addTextQuick').click();assert page.locator('#captionInput').is_visible()
 page.locator('#captionInput').fill('Keep this moment');page.locator('#captionInput').dispatch_event('input')
 assert page.evaluate("active().caption")=='Keep this moment'
 page.evaluate('closeSheet()');page.locator('#templateBtn').click();page.wait_for_selector('#polaroidTemplate')
 page.locator('#noTemplate').click();page.wait_for_function("state.mode==='photo'")
 page.evaluate('closeSheet()');page.wait_for_function("document.querySelector('#addTextQuick span:last-child').textContent==='文字'")
 page.locator('[data-print-type=calendar]').click();assert page.evaluate('state.month')=='2027-02'
 page.locator('[data-print-type=photo]').click();assert page.evaluate('active().caption')=='Keep this moment'
 # A single imported photo must not be duplicated by collage; each layout keeps photo order.
 page.evaluate("TypeNavigation.choose('collage');openLayout()")
 assert page.locator('[data-setting=collageLayout]').first.is_visible()
 page.locator('[data-setting=collageLayout][data-value=grid]').click()
 assert page.locator('[data-setting=collageLayout]').first.is_visible()
 result=page.evaluate("""()=>{
  const saved=state.photos,original=drawPhoto,layout=state.collageLayout,seen=[];
  try{for(const kind of ['auto','vertical','horizontal','grid'])for(let n=0;n<=6;n++){
   state.collageLayout=kind;state.photos=Array.from({length:n},(_,i)=>({...saved[0],index:i}));
   const calls=[];drawPhoto=(ctx,p,x,y,w,h)=>calls.push({index:p?.index??null,x,y,w,h});compose();
   seen.push({kind,n,calls});
  }}finally{drawPhoto=original;state.photos=saved;state.collageLayout=layout;}return seen;
 }""")
 for case in result:
  assert [c['index'] for c in case['calls']]==(list(range(case['n'])) if case['n'] else [None,None]),case
  assert all(c['w']>0 and c['h']>0 for c in case['calls']),case
 page.evaluate('openLayout()');page.locator('[data-photo-arrangement=single]').click();page.evaluate('closeSheet()')
 # Editor navigation must not change print pixels.
 before=page.evaluate("compose().toDataURL()")
 page.evaluate("TypeNavigation.choose('collage');openLayout()");page.locator('[data-photo-arrangement=single]').click();page.evaluate('closeSheet()')
 assert page.evaluate("compose().toDataURL()")==before
 for width,height,mode in [(390,844,'portrait'),(844,390,'landscape')]:
  page.set_viewport_size({'width':width,'height':height})
  page.evaluate("Studio.landscape=()=>innerWidth>innerHeight;updateEditorOrientation();render()")
  page.locator('[data-print-type=calendar]').click()
  tabs=page.locator('#typeTabs').bounding_box();bar=page.locator('#contextTools').bounding_box();canvas=page.locator('#preview').bounding_box()
  assert tabs and bar and canvas,(mode,tabs,bar,canvas)
  assert tabs['x']>=0 and tabs['x']+tabs['width']<=width+1,(mode,tabs)
  assert bar['x']>=0 and bar['x']+bar['width']<=width+1,(mode,bar)
  if os.environ.get('NAV_PREVIEW_DIR'):
   out=Path(os.environ['NAV_PREVIEW_DIR']);out.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(out/(mode+'.png')))
 assert not errors,errors
 page.close();page=browser.new_page(viewport={'width':1280,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def webroute(r):
  if urlparse(r.request.url).path=='/api/state':r.fulfill(json={'permission':True,'host':'desktop','device':{},'history':[]});return
  assert r.request.method=='GET','Navigation must not submit requests'
  route(r)
 page.route('https://studio.local/**',webroute);page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')
 page.wait_for_function('document.body.classList.contains("desktop-editor")')
 page.locator('[data-print-type=calendar]').click();page.locator('[data-type-tool=month]').click()
 assert page.locator('#monthInput').is_visible()
 assert not page.locator('#lunarToggle').is_visible()
 page.wait_for_timeout(150)
 tabs=page.locator('#typeTabs').bounding_box();bar=page.locator('#contextTools').bounding_box();canvas=page.locator('#preview').bounding_box()
 assert tabs['x']+tabs['width']<=bar['x'],(tabs,bar)
 assert canvas['x']+canvas['width']<=bar['x']+2,(canvas,bar)
 assert bar['height']<90,bar
 if os.environ.get('NAV_PREVIEW_DIR'):page.screenshot(path=str(Path(os.environ['NAV_PREVIEW_DIR'])/'desktop.png'))
 assert not errors,errors
 browser.close()
print('PASS: first-level types, scoped tools, fixed widths, disabled states, polaroid caption, retained settings, unchanged photo pixels and portrait/landscape/desktop layouts; no printing')
