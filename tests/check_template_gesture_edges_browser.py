"""Verify full-original hold gestures and stable editor bounds without printing."""
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
 page.add_init_script("window.deviceState={permission:true,device:{},history:[]};window.Studio={state:()=>JSON.stringify(deviceState),sharingState:()=>JSON.stringify({}),pick:n=>{window.picks=(window.picks||[]).concat(n)},capture:()=>{window.captures=(window.captures||0)+1;return JSON.stringify({ok:true,id:'test-camera'})},captureAck:()=>JSON.stringify({ok:true}),printBatch:()=>{throw Error('Printing forbidden')}}")
 page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')

 page.evaluate('Promise.all([NameLabels.ready,CardArt.ready])')
 page.evaluate('BoothTemplates.ready')
 page.set_viewport_size({'width':390,'height':844})
 page.evaluate("Object.defineProperty(screen,'width',{value:390,configurable:true});Object.defineProperty(screen,'height',{value:844,configurable:true});state.media=5012;state.mode='photo';state.photos=[];addPhotos(Array.from({length:6},()=>({src:'/sample.svg'})))")
 page.evaluate('Studio.landscape=()=>innerWidth>innerHeight;updateEditorOrientation();render()')
 page.wait_for_function('!!printPreview&&canAdjustPhoto()')
 assert not errors,errors



 cdp=page.context.new_cdp_session(page)
 def swipe(x,y,dx=0,dy=0):
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
  for i in range(1,7):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+dx*i/6,'y':y+dy*i/6,'id':1}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(70)
 def point(index=0,fx=.5,fy=.5,empty=False):
  return page.evaluate("""([i,fx,fy,empty])=>{const f=(empty?emptyPhotoFrames:photoFrames)[i],p=PhotoWindows.point(f,{x:f.x+f.w*fx,y:f.y+f.h*fy}),r=$('preview').getBoundingClientRect(),v=CropEditor.geometry();return{x:r.left+(p.x+v.tx)*r.width/$('preview').width,y:r.top+(p.y+v.ty)*r.height/$('preview').height}}""",[index,fx,fy,empty])
 # The previously active slot has no overflow; the first drag on a different slot must work.
 page.evaluate("""()=>{PhotoFlow.apply('booth-life-teatime');render();const c=document.createElement('canvas');c.width=1100;c.height=1000;c.getContext('2d').fillRect(0,0,1100,1000);const p=state.photos[0];p.src='/private/photos/ratio-match.jpg';images.set(p.src,c);for(const f of photoFrames){f.p.zoom=1;f.p.x=f.p.y=0;}photoFrames[1].p.zoom=2;render();EffectBrowser.toggle('templates');render();}""")
 assert not page.evaluate("$('preview').classList.contains('photo-draggable')")
 swipe(**point(1),dy=-40)
 assert page.evaluate("PhotoWorks.focus()===state.photos[1].photoId&&active().y!==0&&EffectBrowser.kind()==='templates'")
 # Two-finger zoom remains available in template preview.
 p=point(1);before=page.evaluate('active().zoom')
 a={'x':p['x']-20,'y':p['y'],'id':1};b={'x':p['x']+20,'y':p['y'],'id':2}
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[a]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[a,b]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{**a,'x':a['x']-15},{**b,'x':b['x']+15}]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(100)
 assert page.evaluate('active().zoom')>before
 # Long press compares and release restores, without modifying the work.
 p=point(1);before=page.evaluate('JSON.stringify(PhotoWorks.work())')
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{**p,'id':1}]});page.wait_for_timeout(550)
 assert page.evaluate('OriginalPreview.active()')
 cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 assert not page.evaluate('OriginalPreview.active()')
 assert page.evaluate('JSON.stringify(PhotoWorks.work())')==before
 # Dismissal is still available on the rail after a crop session.
 r=page.locator('#effectChoices').bounding_box();swipe(x=r['x']+r['width']/2,y=r['y']+r['height']/2,dy=65)
 assert not page.evaluate('EffectBrowser.active()')
 assert not errors,errors
 browser.close()
 print('PASS first-drag mixed slots, template pinch zoom, original hold/release and rail dismissal')
