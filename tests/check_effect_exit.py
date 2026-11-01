from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch()
 for width,height,mobile in [(390,844,True),(844,390,True),(1440,900,False)]:
  ctx=b.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile);page=ctx.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   path=urlparse(r.request.url).path
   if path=='/api/state':r.fulfill(json={'permission':True,'host':'desktop','device':{},'history':[]});return
   assert r.request.method=='GET',path
   file=ROOT/'assets'/(path.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('**/*',route);page.goto('https://review.test');page.wait_for_function('window.EffectBrowser&&window.TemplateStudio');page.evaluate('LayerEditor.ready')
  page.locator('#filterBtn').click();assert not page.evaluate('EffectBrowser.active()');assert page.evaluate("sheetKind==='filters'");page.evaluate('closeSheet()')
  page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});const mk=()=>({src:'/sample.svg',width:1200,height:800,fit:'cover',zoom:1.4,x:.2,y:.1,turn:0,filter:'none',overlays:[{id:'sampletext',kind:'text',text:'TEST',font:'sans',sizePct:9,fx:.5,fy:.5,angle:0,color:'#fff'}],templateId:null});state={...defaults,mode:'photo',media:5012,orientation:'portrait',photos:[mk(),mk()],active:0};render();}")
  page.wait_for_timeout(150)

  cdp=ctx.new_cdp_session(page)
  for tab,kind in [('layoutBtn','layout'),('filterBtn','filters'),('templateBtn','templates')]:
   for finish in ['check','double']:
    page.locator('#'+tab).dblclick();page.wait_for_function('(kind)=>EffectBrowser.kind()===kind',arg=kind)
    page.locator('#effectNext').click();page.wait_for_timeout(100)
    selected=page.evaluate('JSON.stringify(state.photos)')
    if finish=='double':page.locator('#'+tab).dblclick()
    else:
     r=page.locator('#effectDone').bounding_box();x,y=r['x']+r['width']/2,r['y']+r['height']/2
     if mobile:
      cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
      cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+9,'y':y,'id':1}]})
      cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
     else:
      page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+9,y);page.mouse.up()
    page.wait_for_function('!EffectBrowser.active()')
    assert page.locator('#effectTools').is_hidden()
    assert page.locator('#photoTools').is_visible()
    assert page.evaluate('JSON.stringify(state.photos)')==selected
    assert page.evaluate("JSON.stringify(JSON.parse(localStorage.getItem(window.STUDIO_DRAFT_KEY||'liuying-draft')).photos)")==selected
    assert page.evaluate('canAdjustPhoto()')
   page.locator('#'+tab).dblclick();page.wait_for_function('(kind)=>EffectBrowser.kind()===kind',arg=kind)
   r=page.locator('#effectDone').bounding_box();x,y=r['x']+r['width']/2,r['y']+r['height']/2
   if mobile:
    cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-40,'y':y-30,'id':1}]})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
   else:
    page.mouse.move(x,y);page.mouse.down();page.mouse.move(x-40,y-30,steps=3);page.mouse.up()
   assert page.evaluate('EffectBrowser.active()'),'Dragging must not apply or exit'
   page.locator('#effectDone').click();page.wait_for_function('!EffectBrowser.active()')
  assert not errors,errors
  ctx.close()
 b.close()
print('PASS: three modes retain and save selection on check or repeated double-click, touch jitter tolerated, deliberate drag retained, editing restored; no printing')
