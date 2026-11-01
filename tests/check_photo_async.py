from pathlib import Path
from urllib.parse import urlparse
import mimetypes,json,io
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
buf=io.BytesIO();Image.new('RGB',(120,180),'#5384a9').save(buf,'JPEG');jpeg=buf.getvalue()
with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':1440,'height':1000});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{},history:[]}),landscape:()=>false,cutout:()=>'{\"ok\":true}',printBatch:()=>{throw Error('Printing forbidden')}}")
 def route(r):
  assert r.request.method=='GET';path=urlparse(r.request.url).path
  if path.startswith('/private/'):
   r.fulfill(body=jpeg,content_type='image/jpeg');return
  f=ROOT/'assets'/(path.lstrip('/') or 'index.html')
  if f.is_file():r.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing')
 page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.ProjectFile&&window.CutoutEditor');page.evaluate('LayerEditor.ready');page.evaluate('NameLabels.ready');page.evaluate('poll=()=>{};void 0')
 result={}
 result['concurrent_add']=page.evaluate('''async()=>{state={...defaults,photos:[],active:0};const original=loadPhoto;let release;const wait=new Promise(r=>release=r);loadPhoto=async p=>{await wait;return original(p)};const items=Array.from({length:4},()=>({src:'/sample.svg'}));const a=addPhotos(items),b=addPhotos(items);release();await Promise.all([a,b]);loadPhoto=original;return state.photos.length;}''')
 result['partial_add']=page.evaluate('''async()=>{state={...defaults,photos:[{src:'/sample.svg'},{src:'/sample.svg'}],active:0};const original=loadPhoto;loadPhoto=async p=>{if(p.src==='/bad.jpg')throw Error('mock');return original(p)};await addPhotos([{src:'/bad.jpg'},{src:'/sample.svg'}]);loadPhoto=original;return {count:state.photos.length,active:state.active};}''')
 result['duplicate_cutout']=page.evaluate('''async()=>{const src='/private/photos/12345678-1234-1234-1234-123456789012.jpg';await loadPhoto({src});state={...defaults,mode:'id',photos:[{src,overlays:[]},{src,overlays:[]}],active:1};openLayout();document.querySelector('[data-id-background=white]').click();await nativeEvent({type:'cutout',value:{source:src,images:{white:'/private/photos/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jpg'}}});return state.photos.map(p=>p.idBackground||'original');}''')
 assert result['concurrent_add']==6,result
 assert result['partial_add']=={'count':3,'active':2},result
 assert result['duplicate_cutout']==['original','white'],result
 result['shared_cutout']=page.evaluate('''async()=>{let requests=0;Studio.cutout=()=>{requests++;return '{"ok":true}'};state.photos.forEach(p=>{delete p.idCutouts;delete p.idBackground});state.active=0;openLayout();document.querySelector('[data-id-background=blue]').click();state.active=1;openLayout();document.querySelector('[data-id-background=red]').click();await nativeEvent({type:'cutout',value:{source:state.photos[0].src,images:{blue:'/private/photos/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb.jpg',red:'/private/photos/cccccccc-cccc-cccc-cccc-cccccccccccc.jpg'}}});return {requests,colors:state.photos.map(p=>p.idBackground)};}''')
 assert result['shared_cutout']=={'requests':1,'colors':['blue','red']},result
 result['new_draft']=page.evaluate('''async()=>{const old=loadPhoto;let release;loadPhoto=async p=>{await new Promise(r=>release=r);return old(p)};state={...defaults,photos:[],active:0};const adding=addPhotos([{src:'/sample.svg'}]);state={...defaults,photos:[],active:0};release();await adding;loadPhoto=old;return state.photos.length;}''')
 assert result['new_draft']==0,result
 result['replaced_cutout']=page.evaluate('''async()=>{const src='/private/photos/12345678-1234-1234-1234-123456789012.jpg';state={...defaults,mode:'id',photos:[{src,overlays:[]}],active:0};openLayout();document.querySelector('[data-id-background=white]').click();state={...defaults,mode:'id',photos:[{src,overlays:[]}],active:0};await nativeEvent({type:'cutout',value:{source:src,images:{white:'/private/photos/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jpg'}}});return state.photos[0].idBackground||'original';}''')
 assert result['replaced_cutout']=='original',result
 result['pending_scope']=page.evaluate('''async()=>{const src='/private/photos/12345678-1234-1234-1234-123456789012.jpg';state={...defaults,mode:'id',photos:[{src,overlays:[]}],active:0};openLayout();document.querySelector('[data-id-background=white]').click();const currentBlocked=await preparePrintPages().then(()=>false,e=>e.message.includes('抠图'));state={...defaults,mode:'id',photos:[{src,overlays:[]}],active:0};const newPages=await preparePrintPages();await nativeEvent({type:'cutoutError',value:{source:src,message:'Synthetic old draft completion'}});return {currentBlocked,newPages:newPages.length};}''')
 assert result['pending_scope']=={'currentBlocked':True,'newPages':1},result
 result['failed_cache']=page.evaluate('''async()=>{const src='/private/photos/12345678-1234-1234-1234-123456789012.jpg',cached='/private/photos/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa.jpg';state={...defaults,mode:'id',photos:[{src,overlays:[],idBackground:'white',idCutouts:{white:cached}},{src,overlays:[],idBackground:'red',idCutouts:{red:cached}}],active:0};const old=loadPhoto;loadPhoto=async p=>{if(p.src===cached)throw Error('Synthetic missing cache');return old(p)};openLayout();await document.querySelector('[data-id-background=white]').onclick();loadPhoto=old;return {colors:state.photos.map(p=>p.idBackground),cached:Object.keys(state.photos[0].idCutouts),original:CutoutEditor.source(state.photos[0])===images.get(src)};}''')
 assert result['failed_cache']=={'colors':['','red'],'cached':[],'original':True},result
 assert not errors,errors
 print('PASS: bounded concurrent imports, partial selection, per-photo shared-source cutout, replaced draft guards; no printing')
 b.close()
