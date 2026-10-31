from pathlib import Path
from urllib.parse import urlparse
import mimetypes,time
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch()
 for width,height in [(411,828),(1440,900)]:
  page=b.new_page(viewport={'width':width,'height':height},is_mobile=width<1000,has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'device':{'connected':True,'media':5009,'checkedAt':int(time.time()*1000)},'history':[]});return
   f=root/'assets'/(name.lstrip('/') or 'index.html')
   if name=='/private/photos/test.jpg':f=root/'tests/fixtures/faces/astronaut.jpg'
   if f.is_file():r.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.evaluate('LayerEditor.ready')
  for media in (5009,5012,5014):
   result=page.evaluate("""async media=>{state={...defaults,media,photos:[],active:0,orientation:'portrait'};await addPhotos([{src:'/private/photos/test.jpg',faces:[[.02,.3,.12,.5]]}]);render();return {...active()}}""",media)
   if media==5012:assert result['x']>.9,result
   assert result['fit']=='cover'
  page.evaluate("""async()=>{state={...defaults,media:5012,orientation:'portrait',photos:[],active:0};await addPhotos([{src:'/private/photos/test.jpg',faces:[[.02,.3,.12,.5],[.85,.3,.95,.5]]}]);render()}""")
  assert page.evaluate("active().fit==='contain'")
  page.evaluate("active().x=-.8;active().zoom=1.5;render();save()")
  assert page.evaluate("active().x===-.8&&active().zoom===1.5")
  page.reload();page.evaluate('LayerEditor.ready');page.wait_for_function('active()&&images.has(active().src)')
  assert page.evaluate("active().x===-.8&&active().zoom===1.5")
  before=page.evaluate('JSON.stringify(state)')
  for idx,message in enumerate(['缺纸或进纸失败，请补充相纸并检查纸盒','色带已耗尽，请更换色带','蓝牙通讯中断，请检查原任务，不要重复打印']):
   page.evaluate("""([idx,message])=>{const j={token:'test-'+idx,phase:idx===2?'uncertain':'rejected',message,title:'AirPrint 打印',createdAt:Date.now()};native={job:j,failure:j,history:[j],unresolved:idx===2};updateStatus()}""",[idx,message])
   dialog=page.locator('.print-failure');assert dialog.is_visible();assert message in dialog.inner_text()
   page.evaluate('updateStatus();updateStatus()');assert dialog.count()==1
   page.locator('#failureAcknowledge').click();page.evaluate('updateStatus()');assert page.locator('.print-failure').count()==0
  page.evaluate("native.job={token:'active',phase:'printing',createdAt:1};native.busy=true;native.unresolved=true;native.failure={token:'another',phase:'rejected',message:'另一笔 AirPrint 未接收',createdAt:2};updateStatus()")
  assert '另一笔 AirPrint 未接收' in page.locator('.print-failure').inner_text();page.locator('#failureAcknowledge').click()
  page.evaluate("native.busy=false;native.unresolved=false;native.job={token:'another',phase:'done',createdAt:2};updateStatus()")
  assert page.locator('.print-failure').count()==0 and not page.locator('#jobBanner').is_visible()
  assert page.evaluate('JSON.stringify(state)')==before
  page.evaluate("native.history=[{token:'empty',phase:'rejected',title:'AirPrint 打印',message:'照片未能接收',createdAt:Date.now()}];openHistory()")
  assert page.locator('.history-card img').count()==0
  page.locator('[data-history="0"]').click();assert page.locator('#importHistory').count()==0 and page.locator('#sheetBody img').count()==0
  assert not errors,errors;page.close()
 print('PASS: initial face crop on three papers, group fit, manual edits/reload preserved, modal errors once, unchanged draft, fileless history; phone and desktop')
