"""Save final-page JPEGs without printing or including preview overlays."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes,base64,io
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for native in [True,False]:
  page=browser.new_page(viewport={'width':411,'height':828},has_touch=True);errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  if native:page.add_init_script("window.savedImages=[];window.Studio={landscape:()=>false,state:()=>'{\"device\":{},\"history\":[]}',saveImage:s=>{savedImages.push(s);return '{\"ok\":true}'},printBatch:()=>{throw Error('Printing forbidden')}}")
  def route(r):
   assert r.request.method=='GET'
   name=urlparse(r.request.url).path
   if name=='/api/state':r.fulfill(json={'device':{},'history':[]});return
   file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('**/*',route);page.goto('https://studio.test/')
  page.wait_for_function('window.ImageExport');page.evaluate('poll=()=>{};void 0')
  for media,orientation,size in [(5009,'square',(1040,1040)),(5012,'portrait',(1216,1824)),(5012,'landscape',(1824,1216)),(5014,'portrait',(1216,1824))]:
   data=page.evaluate('''async ({media,orientation,size})=>{
    const c=document.createElement('canvas');c.width=size[0];c.height=size[1];const x=c.getContext('2d');
    x.fillStyle='#fa2020';x.fillRect(0,0,c.width/2,c.height/2);x.fillStyle='#20dc30';x.fillRect(c.width/2,0,c.width/2,c.height/2);
    x.fillStyle='#2030ed';x.fillRect(0,c.height/2,c.width/2,c.height/2);x.fillStyle='#f1d920';x.fillRect(c.width/2,c.height/2,c.width/2,c.height/2);
    state.media=media;const output=physical(c);window.exportPage={media,orientation,base64:output.toDataURL('image/jpeg',.97).split(',')[1],preview:c.toDataURL('image/jpeg',.72)};
    return ImageExport.jpeg(exportPage);
   }''',{'media':media,'orientation':orientation,'size':size})
   image=Image.open(io.BytesIO(base64.b64decode(data.split(',')[1])));assert image.size==size
   colors=[image.getpixel((int(size[0]*x),int(size[1]*y))) for x,y in [(0.25,0.25),(.75,.25),(.25,.75),(.75,.75)]]
   assert colors[0][0]>200 and colors[1][1]>180 and colors[2][2]>180 and colors[3][0]>200,colors
  page.evaluate('''()=>{pendingPrint={pages:[exportPage,exportPage]};openSheet('confirm','打印预览','<div class="print-pages">'+pendingPrint.pages.map(p=>'<figure><div class="confirmation-preview"><img src="'+p.preview+'"></div></figure>').join('')+'</div>');PaperPreview.mount(document.getElementById('sheetBody'),pendingPrint.pages)}''')
  image=page.locator('.print-pages img').first;image.scroll_into_view_if_needed()
  if native:
   image.dispatch_event('pointerdown',{'pointerId':1,'isPrimary':True,'button':0,'clientX':100,'clientY':100})
   image.dispatch_event('pointermove',{'pointerId':1,'clientX':100,'clientY':120})
   page.wait_for_timeout(600);assert page.evaluate('savedImages.length')==0
   image.dispatch_event('pointerup',{'pointerId':1})
   image.dispatch_event('pointerdown',{'pointerId':1,'isPrimary':True,'button':0,'clientX':100,'clientY':100})
   page.wait_for_function('savedImages.length===1');image.dispatch_event('pointerup',{'pointerId':1})
   image.dispatch_event('contextmenu');page.wait_for_timeout(100);assert page.evaluate('savedImages.length')==1
   page.evaluate("nativeEvent({type:'imageSaved',value:'cancelled'})")
   image.focus();page.keyboard.press('Enter');page.wait_for_function('savedImages.length===2')
   page.evaluate("nativeEvent({type:'imageSaved',value:'saved'})")
   assert page.locator('#toast').inner_text()=='图片已保存'
  else:
   with page.expect_download() as download:image.dispatch_event('contextmenu')
   item=download.value;assert item.suggested_filename=='mijia-photo-1.jpg'
   assert Image.open(item.path()).size==(1216,1824)
  assert not errors,errors
  page.close()
 browser.close()
print('PASS: full-size upright JPEG, all papers, long press, scroll cancellation, duplicate suppression, native events and browser download; no printing')
