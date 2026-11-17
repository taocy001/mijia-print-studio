"""Verify full-original hold gestures and stable editor bounds without printing."""
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
 page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')

 page.evaluate('Promise.all([NameLabels.ready,CardArt.ready])')
 page.evaluate('BoothTemplates.ready')
 page.set_viewport_size({'width':390,'height':844})
 page.evaluate("Object.defineProperty(screen,'width',{value:390,configurable:true});Object.defineProperty(screen,'height',{value:844,configurable:true});state.media=5012;state.mode='photo';state.photos=[];addPhotos([{src:'/sample.svg'}])")
 page.evaluate('Studio.landscape=()=>innerWidth>innerHeight;updateEditorOrientation();render()')
 page.wait_for_function('!!printPreview&&canAdjustPhoto()')
 assert not errors,errors




 page.evaluate("addPhotos(Array.from({length:5},()=>({src:'/sample.svg'})))")
 page.wait_for_function('state.photos.length===6&&ready()');page.evaluate("state.photos.forEach((p,i)=>p.caption='ABCDEF'[i]);PhotoFlow.choosePhoto(1);PhotoFlow.apply('strip');render()")
 # Undo/redo across creation of slot objects preserves the original crop history.
 page.evaluate("PhotoWorks.select(0);PhotoFlow.apply('vertical');window.firstSlot=PhotoFlow.pagePhotos()[1];PhotoWorks.selectSlot(firstSlot);EditHistory.run(()=>{firstSlot.zoom=2},'gesture',firstSlot);render()")
 page.locator('#editorUndo').click();page.locator('#editorUndo').click()
 assert page.evaluate('PhotoWorks.currentId()')=='single'
 page.locator('#editorRedo').click();page.locator('#editorRedo').click()
 assert page.evaluate('PhotoFlow.pagePhotos()[1].zoom')==2
 page.evaluate("PhotoFlow.apply('single');PhotoWorks.select(1);render()")
 assert page.evaluate('state.active')==1
 assert page.evaluate('PhotoFlow.selection()')==[1,2,3]
 assert page.evaluate("PhotoFlow.pagePhotos().map(p=>p.caption).join('')")=='BCD'
 page.evaluate("window.slotC=PhotoFlow.pagePhotos()[1];PhotoWorks.selectSlot(slotC);EditHistory.run(()=>{slotC.x=.4;slotC.zoom=2},'gesture',slotC);render()")
 assert page.evaluate('active()===slotC')
 assert page.evaluate('state.photos[2].x')==0
 page.evaluate("PhotoFlow.choosePhoto(2);PhotoFlow.apply('horizontal');render()")
 assert page.evaluate('state.active')==2 and page.evaluate('PhotoWorks.currentId()')=='horizontal'
 assert page.evaluate('PhotoFlow.selection()')==[2,3]
 assert page.evaluate('PhotoFlow.pagePhotos()[0].x')==0
 page.evaluate('PhotoFlow.choosePhoto(1);render()')
 assert page.evaluate('PhotoWorks.currentId()')=='strip'
 assert page.evaluate('PhotoFlow.pagePhotos()[1].x')==.4
 # A's single-photo design is not touched by B/C multi-photo choices.
 assert page.evaluate('state.photos[0].work.template')=='single'
 # Every thumbnail remains selectable, including unused photos before/after this work.
 page.evaluate("PhotoFlow.choosePhoto(4);PhotoFlow.apply('strip');render()")
 assert page.evaluate('PhotoFlow.selection()')==[4,5] and page.evaluate('PhotoFlow.missing()')==1
 assert page.evaluate('emptyPhotoFrames.length')==1
 page.evaluate('PhotoFlow.choosePhoto(1);render()')
 # Template cancel and undo affect only this work, with slot crop retained.
 before=page.evaluate('JSON.stringify(state.photos.map(p=>p.work))')
 page.locator('#templateBtn').click();page.evaluate("PhotoFlow.apply('grid4');render()")
 page.locator('#effectCancel').click();assert page.evaluate('JSON.stringify(state.photos.map(p=>p.work))')==before
 page.evaluate("PhotoFlow.apply('horizontal');render()")
 page.locator('#editorUndo').click();assert page.evaluate('PhotoWorks.currentId()')=='strip'
 page.locator('#editorRedo').click();assert page.evaluate('PhotoWorks.currentId()')=='horizontal'
 page.locator('#editorUndo').click()
 # Actual touch of C's slot changes focus without switching B's work.
 cdp=page.context.new_cdp_session(page)
 point=page.evaluate("""()=>{const f=photoFrames[1],r=$('preview').getBoundingClientRect(),v=CropEditor.geometry();return{x:r.left+(f.x+f.w/2+v.tx)*r.width/$('preview').width,y:r.top+(f.y+f.h/2+v.ty)*r.height/$('preview').height}}""")
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{**point,'id':1}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 assert page.evaluate('active().caption')=='C' and page.evaluate('state.active')==1
 # Reorder preserves the owner and recomputes subsequent source positions without wrapping.
 page.evaluate('PhotoFlow.reorder(1,4);render()')
 assert page.evaluate("state.photos[state.active].caption")=='B' and page.evaluate('state.active')==4
 assert page.evaluate("PhotoFlow.pagePhotos().map(p=>p.caption).join('')")=='BF'
 assert page.evaluate('PhotoFlow.missing()')==1
 page.locator('#editorUndo').click();assert page.evaluate("state.photos.map(p=>p.caption).join('')")=='ABCDEF'
 assert page.evaluate('state.active')==1 and page.evaluate('PhotoFlow.pagePhotos()[1].x')==.4
 # Printing current work gives one page; explicit batch preserves all edit state.
 page.evaluate('render();PhotoWorks.saveCurrent()')
 before=page.evaluate('JSON.stringify(state)')
 assert page.evaluate('preparePrintPages().then(p=>p.length)')==page.evaluate('PhotoWorks.printableIndices().length')
 assert page.evaluate('JSON.stringify(state)')==before
 assert page.evaluate('preparePrintPages([0,1,2]).then(p=>p.length)')==3
 assert page.evaluate('JSON.stringify(state)')==before
 page.evaluate("state.photos[1].work.slots['p-removed']={coatTexture:'custom',coatSource:'/private/photos/missing-texture.jpg'}")
 # Project codec preserves per-photo designs and independent slot crops.
 decoded=page.evaluate('ProjectFile.encode().then(ProjectFile.decode).then(p=>p.editing)')
 assert 'p-removed' not in decoded['photos'][1]['work']['slots']
 assert decoded['photoWorkVersion']==1 and decoded['photos'][1]['work']['template']=='strip'
 cid=decoded['photos'][2]['photoId'];assert decoded['photos'][1]['work']['slots'][cid]['x']==.4
 assert decoded['photos'][2]['work']['template']=='horizontal'
 # Delete / restore does not replace the newly active work's layout.
 page.evaluate('removePhoto(1);render()')
 assert page.evaluate('PhotoWorks.currentId()')=='horizontal'
 page.locator('#photoUndo button').click();page.wait_for_timeout(100)
 assert page.evaluate('PhotoWorks.currentId()')=='strip' and page.evaluate('PhotoFlow.pagePhotos()[1].x')==.4
 # A normal draft reload restores the chosen work and its sources.
 page.evaluate('save()');page.reload();page.wait_for_function('state.photos.length===6&&ready()&&window.PhotoWorks');page.evaluate('render()')
 assert page.evaluate('PhotoWorks.currentId()')=='strip'
 assert page.evaluate('PhotoFlow.selection()')==[1,2,3]
 assert page.evaluate('PhotoFlow.pagePhotos()[1].x')==.4
 # Non-photo editor types retain their original effect history schema.
 for mode in ['calendar','id']:
  page.evaluate("PhotoWorks.saveCurrent();state.mode='"+mode+"';state.calendarLayout='photo';render()")
  page.locator('#contextTools [data-type-tool="tone"]').click();page.evaluate('EffectBrowser.step(1)');page.locator('#effectCancel').click()
  assert page.evaluate('state.mode')==mode
 # Split-paper slot undo must keep the owning decorative template.
 page.evaluate("state.mode='photo';PhotoWorks.activate();state.media=5014;PhotoWorks.select(0);PhotoFlow.apply(TEMPLATE_CATALOG.find(t=>(t.slots||1)===1).id);render();window.splitTemplate=PhotoWorks.currentId();window.splitSlot=PhotoFlow.pagePhotos()[1];PhotoWorks.selectSlot(splitSlot);EditHistory.run(()=>{splitSlot.zoom=1.7},'gesture',splitSlot);render()")
 page.locator('#editorUndo').click();assert page.evaluate('PhotoWorks.currentId()===splitTemplate&&state.mode==="template"')
 assert not errors,errors
 browser.close();print('PASS independent photo works, forward-only slots, crop focus/isolation, history, reorder/delete/restore, current and explicit batch printing, project codec and reload')
