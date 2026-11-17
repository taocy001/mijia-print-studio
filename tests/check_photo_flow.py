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
 page.set_viewport_size({'width':390,'height':844})
 page.evaluate("Object.defineProperty(screen,'width',{value:390,configurable:true});Object.defineProperty(screen,'height',{value:844,configurable:true})")
 assert page.evaluate('photoBatchLimit()')==6
 page.set_viewport_size({'width':844,'height':390});assert page.evaluate('photoBatchLimit()')==6
 page.set_viewport_size({'width':390,'height':844})
 page.evaluate("Object.assign(state,{mode:'photo',photos:[],active:0,media:5012});render()")
 assert page.locator('#photoTypeTools button:visible').all_text_contents()==['模板','色调','文字','表情']
 page.locator('#templateBtn').click();page.wait_for_selector('[data-basic=grid4]')
 assert page.locator('[data-photo-arrangement]').count()==0
 page.locator('[data-template-category=basic]').click();assert page.locator('[data-basic=vertical]').is_visible()
 assert not page.locator('[data-template=booth-together-3]').is_visible()
 page.locator('[data-basic=grid4]').click();assert page.evaluate("state.photoLayout==='grid4'&&state.mode==='collage'")
 assert page.locator('[data-choice][aria-pressed=true]').count()==1
 page.evaluate("closeSheet();addPhotos(Array.from({length:7},()=>({src:'/sample.svg'})))")
 assert page.evaluate('state.photos.length')==6
 assert page.evaluate('PhotoFlow.capacity()===4&&PhotoFlow.count()===1&&PhotoFlow.missing()===0')
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 page.evaluate('render()');assert page.locator('.unused-photo').count()==2
 # Drag an unused thumbnail directly onto the desired used thumbnail.
 source=page.locator('[data-photo="5"]').bounding_box();target=page.locator('[data-photo="1"]').bounding_box()
 page.mouse.move(source['x']+source['width']/2,source['y']+source['height']/2);page.mouse.down()
 page.mouse.move(target['x']+target['width']/2,target['y']+target['height']/2,steps=10);page.mouse.up()
 assert not page.locator('[data-replace-slot]').count()
 assert page.evaluate('PhotoFlow.selection()')==[0,5,2,3]
 assert page.evaluate('state.photos.length')==6
 page.evaluate('EditHistory.undo()');assert page.evaluate('PhotoFlow.selection()')==[0,1,2,3]
 page.evaluate('EditHistory.redo()');assert page.evaluate('PhotoFlow.selection()')==[0,5,2,3]
 # Every basic template uses exactly its slots, never unused photos or duplicate filling.
 result=page.evaluate("""()=>{const old=drawPhoto,rows=[];try{for(const t of PhotoFlow.basics){state.media=5012;PhotoFlow.apply(t.id);for(const media of [5012,5009,5014]){state.media=media;state.active=0;const n=PhotoFlow.capacity(),seen=[];drawPhoto=(ctx,p,x,y,w,h)=>seen.push({i:p?state.photos.indexOf(p):null,x,y,w,h});compose(false);rows.push({id:t.id,media,n,selected:PhotoFlow.multiple()?PhotoFlow.selection():Array.from({length:n},(_,i)=>i),seen});}}}finally{drawPhoto=old;state.media=5012;}return rows;}""")
 for row in result:
  assert [s['i'] for s in row['seen'] if s['i'] is not None]==row['selected'],row
  assert all(s['w']>0 and s['h']>0 for s in row['seen']),row
 # Styled template selection changes the batch; newly added photos inherit it.
 page.evaluate("state.media=5012;state.photos=[];state.active=0;TemplateStudio.apply('booth-puzzle-1');addPhotos([{src:'/sample.svg'},{src:'/sample.svg'}])")
 assert page.evaluate("state.photos.every(p=>p.templateId==='booth-puzzle-1')")
 page.evaluate("PhotoFlow.apply('grid4');EditHistory.undo()")
 assert page.evaluate("state.mode==='template'&&state.photos.every(p=>p.templateId==='booth-puzzle-1')")
 page.evaluate('EditHistory.redo()');assert page.evaluate("state.photoLayout==='grid4'")
 page.evaluate("state.media=5014;TemplateStudio.open()")
 page.wait_for_selector('[data-basic=grid6]');assert page.locator('[data-basic=grid6]').is_disabled()
 assert page.locator('[data-template=booth-together-4]').is_disabled()
 # Desktop/tablet can import twelve without changing the phone limit.
 page.set_viewport_size({'width':1280,'height':900})
 page.evaluate("Object.defineProperty(screen,'width',{value:1280,configurable:true});Object.defineProperty(screen,'height',{value:900,configurable:true});closeSheet();state.photos=[];state.active=0;state.media=5012;PhotoFlow.apply('single')")
 assert page.evaluate('photoBatchLimit()')==12
 import base64
 jpg=page.evaluate("()=>{const c=document.createElement('canvas');c.width=480;c.height=320;const g=c.getContext('2d');g.fillStyle='#94b8a3';g.fillRect(0,0,480,320);return c.toDataURL('image/jpeg').split(',')[1]}")
 page.route('https://studio.local/private/photos/*',lambda route:route.fulfill(body=base64.b64decode(jpg),content_type='image/jpeg'))
 page.evaluate("addPhotos(Array.from({length:13},(_,i)=>({src:'/private/photos/flow-'+i+'.jpg'})))")
 assert page.evaluate('state.photos.length')==12
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==12
 page.evaluate("state.media=5014;PhotoFlow.apply('grid6')")
 assert page.evaluate('PhotoFlow.capacity()')==12
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 page.evaluate("TemplateStudio.apply('booth-together-4')")
 assert page.evaluate('PhotoFlow.capacity()===8&&PhotoFlow.missing()===0')
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 assert page.evaluate('state.photos.length')==12
 page.evaluate("state.media=5012;PhotoFlow.apply('grid4');state.active=11;render()")
 assert page.evaluate("ProjectFile.encode().then(raw=>ProjectFile.decode(raw)).then(p=>p.editing.photos.length===12&&p.editing.active===11&&p.editing.photoLayout==='grid4')")
 # Resizing never truncates existing work; existing complete batch remains printable.
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('photoBatchLimit()')==6
 assert page.evaluate('state.photos.length')==12
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 # Print settings follow the first USED photo; unused photos never enter output.
 page.evaluate("state.photos.forEach((p,i)=>{p.sharpen=i%3;p.coatThreshold=80+i});state.photoSelection=[5,2,3,4];state.active=0;state.copies=3")
 assert page.evaluate('preparePrintPages().then(p=>p.map(x=>[x.sharpen,x.threshold,x.copies]))')==[[2,85,1]]
 page.evaluate('removePhoto(0)');page.locator('#photoUndo button').click();assert page.evaluate('state.photos.length')==12
 # Incomplete selected template cannot print, but existing extra photos are never removed.
 page.evaluate("state.photos=state.photos.slice(0,2);state.photoSelection=[];state.media=5012;state.active=0;PhotoFlow.apply('grid4');render()")
 assert page.evaluate('PhotoFlow.missing()')==2
 assert page.evaluate('preparePrintPages().then(()=>false,()=>true)')
 page.evaluate('PhotoFlow.openMissing()');assert page.locator('#fillPhotoPage').is_visible()
 page.evaluate("closeSheet();addPhotos([{src:'/sample.svg'},{src:'/sample.svg'}])")
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 # After adding surplus photos, controls must still address a used photo.
 page.evaluate("addPhotos([{src:'/sample.svg'},{src:'/sample.svg'}])")
 assert page.evaluate('PhotoFlow.selection().includes(state.active)')
 page.evaluate("state.photoSelection=[5,1,2,3];state.active=5;state.photos[5].coatTexture='dots';StudioExtras.openCoat()")
 page.locator('#coatThreshold').evaluate("e=>{e.value=120;e.dispatchEvent(new Event('input',{bubbles:true}))}")
 assert page.evaluate('state.photos[5].coatThreshold')==120
 assert page.evaluate('preparePrintPages().then(p=>p[0].threshold)')==120
 page.evaluate("closeSheet();openFilters()")
 page.locator('#toneSharp').select_option('2');assert page.evaluate('state.photos[5].sharpen')==2
 # A history print imported as a new photo must not inherit a multi-photo template.
 assert page.evaluate('PhotoFlow.inheritedTemplate()') is None
 # Deleting a different source between template edits cannot shift restored slots.
 page.evaluate("closeSheet();state.photos=Array.from({length:6},()=>({...state.photos[0]}));state.active=0;state.media=5012;PhotoFlow.apply('grid4');state.photoSelection=[4,1,2,3];window.keepSelection=PhotoFlow.pagePhotos();PhotoFlow.apply('horizontal');removePhoto(0);EditHistory.undo()")
 assert page.evaluate('PhotoFlow.pagePhotos().every((p,i)=>p===keepSelection[i])')
 page.evaluate("PhotoFlow.apply('single');selectPhoto(state.photos.length-1);PhotoFlow.apply('grid4');removePhoto(state.photos.length-1);EditHistory.undo()")
 assert page.evaluate('state.active>=0&&state.active<state.photos.length')
 assert not errors,errors
 browser.close()
print('PASS: phone6/tablet12; four tools; unified templates; multi-template ONE sheet; unused photo badges/replacement/undo; all paper slots; template inheritance; single-photo12 batch; splice8/12 slots; project roundtrip; resize preservation; used-photo settings and one copy; missing photos guard; no printing')
