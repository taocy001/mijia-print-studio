"""Verify independent single-photo split works and physical page batching, without printing."""
import os,mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(**({'channel':os.environ['TEST_BROWSER_CHANNEL']} if os.environ.get('TEST_BROWSER_CHANNEL') else {}))
 page=browser.new_page();page.add_init_script("Object.defineProperty(crypto,'randomUUID',{value:undefined})");errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 def route(r):
  f=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
  mime={'.js':'text/javascript','.svg':'image/svg+xml','.html':'text/html','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}.get(f.suffix,mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
  r.fulfill(body=f.read_bytes(),content_type=mime) if f.is_file() else r.fulfill(status=404)
 page.route('https://studio.local/**',route)
 page.add_init_script("window.deviceState={permission:true,device:{},history:[]};window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({}),pick:n=>{window.picks=(window.picks||[]).concat(n)},capture:()=>{window.captures=(window.captures||0)+1;return JSON.stringify({ok:true,id:'test-camera'})},captureAck:()=>JSON.stringify({ok:true}),printBatch:()=>{throw Error('Printing forbidden')}}")
 page.add_init_script("window.BrowserTransport={};document.addEventListener('DOMContentLoaded',()=>document.documentElement.classList.add('browser-client'))")
 page.set_viewport_size({'width':1440,'height':1000})
 page.goto('https://studio.local/')
 page.evaluate('Promise.all([LayerEditor.ready,BoothTemplates.ready,NameLabels.ready,CardArt.ready])')
 page.evaluate("Object.defineProperty(screen,'width',{value:1440,configurable:true});Object.defineProperty(screen,'height',{value:1000,configurable:true});state.media=5012;state.mode='photo';state.photos=[];addPhotos(Array.from({length:6},()=>({src:'/sample.svg'})))")
 page.wait_for_function('state.photos.length===6&&ready()')
 page.evaluate("state.photos.forEach((p,i)=>{const src='/private/photos/everyday-'+i+'.jpg';images.set(src,images.get(p.src));p.src=src;});render()")
 page.wait_for_selector('#sheet.desktop-inspector .template-card')
 assert not errors,errors
 page.evaluate("state.media=5014;state.sixLayout=5014;state.photos.forEach(p=>{p.work.template='single';p.work.layout.splitOrientation='landscape'});PhotoWorks.select(0);render()")
 assert page.evaluate('PhotoWorks.capacity()')==1
 assert page.evaluate('TemplateStudio.browseItems().every(t=>t.slots===1)')
 # Every source is a work, two distinct works become one physical print page.
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==3
 page.evaluate("PhotoFlow.apply('booth-life-watch');PhotoWorks.select(1);PhotoFlow.apply('booth-life-plate');render()")
 assert page.evaluate('state.photos.slice(0,2).map(p=>p.work.template)')==['booth-life-watch','booth-life-plate']
 assert page.evaluate('photoFrames.map(f=>state.photos.indexOf(f.p))')==[0,1]
 assert page.evaluate('photoFrames[0].y<912&&photoFrames[1].y>=912')
 before=page.evaluate('compose(false).toDataURL()')
 page.evaluate('PhotoWorks.select(0);render()')
 assert page.evaluate('compose(false).toDataURL()')==before,'Selecting upper/lower work must not change rendered content'
 page.evaluate("PhotoFlow.apply('grid4')")
 assert page.evaluate('PhotoWorks.currentId()')=='booth-life-watch','Multi-photo template rejected even via direct call'
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==1
 page.evaluate('confirmPrint()');page.wait_for_selector('#confirmSend')
 assert page.evaluate('pendingPrint.pages.length')==1
 assert page.evaluate('pendingPrint.workIndices')==[0,1]
 assert '上幅：照片 1 · 下幅：照片 2' in page.locator('#sheetBody').inner_text()
 # Cropping the other half selects its photo without sharing the crop.
 page.evaluate('closeSheet();PhotoWorks.selectSlot(state.photos[1]);active().x=.4;active().zoom=1.6;render()')
 assert page.evaluate('state.active')==1
 assert page.evaluate('state.photos[0].zoom')!=1.6
 # Odd selected works leave lower half white instead of repeating any photograph.
 page.evaluate("PhotoWorks.select(4);PhotoFlow.apply('booth-life-watch');render()")
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==2
 assert page.evaluate("async()=>{const p=await preparePrintPages();const img=new Image();img.src=p[1].preview;await img.decode();const c=document.createElement('canvas');c.width=1216;c.height=1824;const g=c.getContext('2d');g.drawImage(img,0,0);const d=g.getImageData(0,950,1216,850).data;return d.every((v,i)=>i%4===3||v>248);}")
 assert page.evaluate('PhotoWorks.splitIndices()')==[4,5],'Printing restores editor pair'
 # Existing large-paper multi-photo work survives switching to/from split paper.
 page.evaluate("state.media=5012;PhotoWorks.select(2);PhotoFlow.apply('grid4');render()")
 assert page.evaluate('PhotoWorks.currentId()')=='grid4'
 page.evaluate('state.media=5014;render()')
 assert page.evaluate('PhotoWorks.currentId()')=='single'
 assert page.evaluate('state.photos[2].work.template')=='grid4'
 page.evaluate('state.media=5012;render()')
 assert page.evaluate('PhotoWorks.currentId()')=='grid4'
 # 3-inch and 6-inch selection policies remain the same.
 assert page.evaluate('PhotoWorks.capacity()')==4
 # Decorations belong to each half and use its coordinate space.
 page.evaluate('state.media=5014;PhotoWorks.select(0);render()')
 assert page.evaluate('LayerEditor.space().y')==0
 page.evaluate('PhotoWorks.select(1);render()')
 assert page.evaluate('LayerEditor.space().y')==912
 # Native browser touch input on a phone viewport: selection must not cancel the drag.
 page.set_viewport_size({'width':390,'height':844})
 cdp=page.context.new_cdp_session(page)
 cdp.send('Emulation.setTouchEmulationEnabled',{'enabled':True,'maxTouchPoints':2})
 page.evaluate("state.photos.forEach(p=>{p.work.template='single';p.work.layers=[];p.zoom=2;p.x=0;p.y=0});PhotoWorks.select(0);render()")
 page.wait_for_timeout(100)
 point=page.evaluate("""()=>{const c=$('preview'),r=c.getBoundingClientRect(),f=photoFrames.find(f=>f.p===state.photos[1]),v=CropEditor.geometry();return {x:r.left+(f.x+f.w/2+v.tx)*r.width/c.width,y:r.top+(f.y+f.h/2+v.ty)*r.height/c.height};}""")
 def touch(kind,dx=0):
  cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind=='touchEnd' else [{'x':point['x']+dx,'y':point['y'],'id':1}]})
 touch('touchStart')
 page.wait_for_timeout(60)
 touch('touchMove',10)
 page.wait_for_timeout(60)
 first=page.evaluate('state.photos[1].x')
 touch('touchMove',20)
 page.wait_for_timeout(60)
 second=page.evaluate('state.photos[1].x')
 touch('touchEnd')
 assert page.evaluate('state.active')==1
 assert first!=0 and second!=first,(first,second)
 assert page.evaluate('state.photos[0].x')==0
 # Distinct decorations render only in their own half and remain selectable there.
 page.evaluate("PhotoWorks.select(0);LayerEditor.create({text:'TOP',color:'#ff0000',stroke:'',sizePct:20});PhotoWorks.select(1);LayerEditor.create({text:'BOTTOM',color:'#0000ff',stroke:'',sizePct:20});render()")
 counts=page.evaluate("""()=>{const c=document.createElement('canvas');c.width=1216;c.height=1824;PhotoWorks.paintSplitLayers(c.getContext('2d'),1216,1824,'photo');const d=c.getContext('2d').getImageData(0,0,1216,1824).data,n=[0,0,0,0];for(let i=0;i<d.length;i+=4){if(!d[i+3])continue;const half=i/4<1216*912?0:1;if(d[i]>200&&d[i+2]<30)n[half*2]++;if(d[i+2]>200&&d[i]<30)n[half*2+1]++;}return n;}""")
 assert counts[0]>100 and counts[1]==0 and counts[2]==0 and counts[3]>100,counts
 assert page.evaluate("LayerEditor.hit(608,1368)?.text")=='BOTTOM'
 page.evaluate('PhotoWorks.select(0);render()')
 assert page.evaluate("LayerEditor.hit(608,456)?.text")=='TOP'
 assert not errors,errors
 browser.close()
 print('PASS independent split templates, single-photo restriction, frame/crop ownership, 2-per-page batching, mixed filtering, odd blank, restore and 6-inch preservation; no printing')
