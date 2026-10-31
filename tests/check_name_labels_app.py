from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse,unquote
import mimetypes,io,json,random,sys
from PIL import Image
root=Path(__file__).resolve().parents[1];assets=root/'assets'

with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':411,'height':828},is_mobile=True,has_touch=True);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{},history:[]}),printBatch:()=>{throw Error('Printing is forbidden in tests')}}")
 def route(r):
  path=unquote(urlparse(r.request.url).path);file=assets/(path.lstrip('/') or 'index.html')
  if path.startswith('/private/'):
   buf=io.BytesIO();Image.new('RGB',(800,1200),'#387fa0').save(buf,'JPEG');r.fulfill(body=buf.getvalue(),content_type='image/jpeg');return
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing asset')
 page.route('https://studio.local/**',route);page.goto('https://studio.local/');page.wait_for_function('window.LayerEditor&&window.CropEditor&&window.StudioExtras');page.evaluate('LayerEditor.ready')

 page.evaluate('NameLabels.ready')
 page.evaluate("state.mode='label';state.photos=[];state.labelTitle='小明';state.labelSubtitle='一年级';render()")
 for media,orientation,count in [(5009,'auto',4),(5012,'portrait',6),(5012,'landscape',2),(5014,'auto',4)]:
  page.evaluate("([m,o])=>{state.media=m;state.orientation=o;render()}",[media,orientation])
  assert page.evaluate('NameLabels.count()')==count
  for theme in ['rainbow','space','panda','flower','minimal','unicorn']:
   page.evaluate('(t)=>{state.labelTheme=t;render()}',theme)
   result=page.evaluate("async()=>{const p=await preparePrintPages();const im=new Image();im.src='data:image/jpeg;base64,'+p[0].base64;await im.decode();return [p.length,im.width,im.height,p[0].media]}")
   dim=[1040,1040] if media==5009 else [1216,1824]
   assert result==[1,*dim,media],result
 page.locator('#templateBtn').click();assert page.locator('[data-setting="labelTheme"]').count()==6
 page.locator('[data-setting="labelTheme"][data-value="panda"]').click();assert page.evaluate('state.labelTheme')=='panda'
 page.evaluate('closeSheet()');page.locator('#addTextQuick').click();page.locator('#labelInput').fill('新的姓名');page.locator('#subtitleInput').fill('新的班级')
 assert page.evaluate('state.labelTitle')=='新的姓名'
 assert page.evaluate('state.label')=='名字，留在喜欢的东西上'
 assert page.locator('#labelInput').get_attribute('maxlength')=='30'
 assert page.locator('#subtitleInput').get_attribute('maxlength')=='50'
 page.evaluate("closeSheet();state.media=5009;state.mode='label';render()")
 page.screenshot(path='/tmp/mijia-name-label-app.png')
 assert not errors,errors
 print('24 label outputs passed: six themes, square/portrait/landscape/split counts and dimensions; picker, text editing and card isolation passed')
 b.close()
