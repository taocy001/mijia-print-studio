"""Synthetic camera results; no real camera or printer is invoked."""
import mimetypes
import io
from PIL import Image
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch();page=browser.new_page(viewport={'width':390,'height':844});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script("window.Studio={landscape:()=>innerWidth>innerHeight,state:()=>'{\"device\":{},\"history\":[]}',printBatch:()=>{throw Error('No printing')}}")
    page.add_init_script("window.captureIndex=0;window.acks=[];Studio.capture=()=>JSON.stringify({ok:true,id:'capture-'+(++captureIndex)});Studio.captureReady=()=>{};Studio.captureAck=id=>{acks.push(id);return JSON.stringify({ok:true});};")
    def route(r):
        assert r.request.method=='GET'
        if urlparse(r.request.url).path.startswith('/private/photos/'):
            data=io.BytesIO();Image.new('RGB',(1200,800),'#437fa0').save(data,'JPEG');r.fulfill(body=data.getvalue(),content_type='image/jpeg');return
        file=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.LabelBatch&&window.StudioExtras');page.evaluate('NameLabels.ready');page.evaluate('LayerEditor.ready')
    page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});state={...defaults,mode:'photo',media:5009,photos:[{src:'/sample.svg',overlays:[]}],active:0};render();}")
    page.locator('#menuBtn').click();assert page.locator('#capturePhoto').count()==0;page.evaluate('closeSheet()')
    page.evaluate("window.picks=0;Studio.pick=()=>picks++;void 0")
    page.locator('#addMore').click();assert page.evaluate('picks===1&&captureIndex===0')
    box=page.locator('#addMore').bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
    page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+20,y);page.wait_for_timeout(550);page.mouse.up()
    assert page.evaluate('picks===1&&captureIndex===0')
    for event in ['pointercancel','scroll']:
        page.locator('#addMore').dispatch_event('pointerdown',{'button':0,'pointerId':9,'clientX':x,'clientY':y,'pointerType':'touch'})
        page.locator('#addMore').dispatch_event(event,{'pointerId':9})
        page.wait_for_timeout(550)
        page.locator('#addMore').dispatch_event('pointerup',{'pointerId':9})
        page.locator('#addMore').dispatch_event('click')
        assert page.evaluate('picks===1&&captureIndex===0')
    page.mouse.move(x,y);page.mouse.down();page.wait_for_timeout(550);page.mouse.up()
    assert page.evaluate('picks===1&&captureIndex===1')
    page.evaluate("nativeEvent({type:'captureFinished',value:{id:'capture-1',cancelled:true}})")
    assert page.evaluate("state.mode==='photo'&&state.photos.length===1&&acks.includes('capture-1')")
    page.wait_for_timeout(1100);page.locator('#addMore').dispatch_event('contextmenu');assert page.evaluate('captureIndex===1')
    page.evaluate('PhotoCapture.start()')
    page.evaluate("async()=>{await Promise.all([1,2].map(()=>nativeEvent({type:'photos',value:[{src:'/private/photos/capture-a.jpg',captureId:'capture-2'}]})));await nativeEvent({type:'captureFinished',value:{id:'capture-2'}});}")
    assert page.evaluate("state.mode==='photo'&&state.photos.length===2&&acks.includes('capture-2')")
    page.evaluate("async()=>{await Promise.all([1,2].map(()=>nativeEvent({type:'photos',value:[{src:'/private/photos/capture-a.jpg',captureId:'capture-2'}]})));await nativeEvent({type:'captureFinished',value:{id:'capture-2'}});}")
    assert page.evaluate('state.photos.length===2')
    page.evaluate('PhotoCapture.start()');page.evaluate("closeSheet();state.mode='card';")
    page.evaluate("async()=>{await nativeEvent({type:'photos',value:[{src:'/private/photos/capture-b.jpg',captureId:'capture-3'}]});await nativeEvent({type:'captureFinished',value:{id:'capture-3'}});}")
    assert page.evaluate("state.mode==='card'&&state.photos.length===3")
    quota=page.evaluate("""async()=>{
      PhotoCapture.start();const original=Storage.prototype.setItem;
      Storage.prototype.setItem=()=>{throw Error('quota')};
      try{await nativeEvent({type:'photos',value:[{src:'/private/photos/capture-c.jpg',captureId:'capture-4'}]});await nativeEvent({type:'captureFinished',value:{id:'capture-4'}});}finally{Storage.prototype.setItem=original;}
      return !acks.includes('capture-4')&&state.photos.length===4;
    }""")
    assert quota
    page.evaluate("async()=>{await nativeEvent({type:'photos',value:[{src:'/private/photos/capture-c.jpg',captureId:'capture-4'}]});await nativeEvent({type:'captureFinished',value:{id:'capture-4'}});}")
    assert page.evaluate("state.photos.length===4&&acks.includes('capture-4')")
    capacity=page.evaluate("""async()=>{
      PhotoCapture.start();state.photos.push(...Array.from({length:2},()=>({src:'/sample.svg',overlays:[]})));
      await nativeEvent({type:'photos',value:[{src:'/private/photos/capture-d.jpg',captureId:'capture-5'}]});await nativeEvent({type:'captureFinished',value:{id:'capture-5'}});
      return state.photos.length===6&&!acks.includes('capture-5');
    }""")
    assert capacity
    ack_retry=page.evaluate("""async()=>{
      state.photos.pop();const old=Studio.captureAck;Studio.captureAck=()=>JSON.stringify({error:'Synthetic ack failure'});
      await nativeEvent({type:'photos',value:[{src:'/private/photos/capture-d.jpg',captureId:'capture-5'}]});await nativeEvent({type:'captureFinished',value:{id:'capture-5'}});
      const recover=!!localStorage.getItem((window.STUDIO_DRAFT_KEY||'liuying-draft')+'-capture');Studio.captureAck=old;await nativeEvent({type:'captureFinished',value:{id:'capture-5'}});
      return recover&&acks.includes('capture-5');
    }""")
    assert ack_retry
    late=page.evaluate("""async()=>{
      state.photos=state.photos.slice(0,2);state.mode='photo';PhotoCapture.start();
      const old=loadPhoto;let release;loadPhoto=async p=>{await new Promise(r=>release=r);return old(p)};
      const receive=nativeEvent({type:'photos',value:[{src:'/private/photos/capture-late.jpg',captureId:'capture-6'}]});
      state.mode='card';release();loadPhoto=old;await receive;await nativeEvent({type:'captureFinished',value:{id:'capture-6'}});return state.mode==='card';
    }""")
    assert late
    page.evaluate("state.photos=Array.from({length:6},()=>({src:'/sample.svg',overlays:[]}));render()")
    assert page.locator('#addMore').count()==0
    page.evaluate("state.photos.pop();render()")
    page.wait_for_timeout(200);page.locator('#addMore').focus();page.keyboard.press('Shift+Enter')
    assert page.evaluate('captureIndex===7')
    page.evaluate("nativeEvent({type:'captureFinished',value:{id:'capture-7',cancelled:true}})")
    page.locator('#addMore').click(button='right');assert page.evaluate('captureIndex===8')
    page.evaluate("nativeEvent({type:'captureFinished',value:{id:'capture-8',cancelled:true}})")
    page.screenshot(path='/tmp/capture-mobile.png')
    assert not errors,errors;page.close()
    page=browser.new_page(viewport={'width':1440,'height':1000});stored={};uploads=[]
    image=io.BytesIO();Image.new('RGB',(1000,1500),'#d58a3e').save(image,'JPEG');jpeg=image.getvalue()
    def web_route(r):
        path=urlparse(r.request.url).path;assert urlparse(r.request.url).hostname=='studio.test'
        if path=='/api/state':r.fulfill(json={'host':'desktop','permission':True,'device':{},'history':[]});return
        if path=='/api/upload':
            uploads.append(path);src='/private/photos/captured-'+str(len(uploads))+'.jpg';stored[src]=jpeg;r.fulfill(json={'src':src,'width':1000,'height':1500});return
        assert r.request.method=='GET'
        if path in stored:r.fulfill(body=stored[path],content_type='image/jpeg');return
        file=ROOT/'assets'/(path.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',web_route);page.goto('https://studio.test/');page.wait_for_function('window.PhotoCapture&&window.BrowserTransport');page.evaluate('LayerEditor.ready')
    page.evaluate("localStorage.setItem((window.STUDIO_DRAFT_KEY||'liuying-draft')+'-capture',JSON.stringify({id:'orphan',mode:'add'}))")
    page.reload();page.wait_for_function('window.PhotoCapture&&window.BrowserTransport');page.evaluate('LayerEditor.ready')
    page.evaluate("state.mode='collage';state.collageLayout='strip';render()")
    with page.expect_file_chooser() as chooser:page.locator('#addMore').click(button='right')
    assert chooser.value.element.get_attribute('capture')=='environment'
    chooser.value.set_files({'name':'synthetic.jpg','mimeType':'image/jpeg','buffer':jpeg})
    page.wait_for_function("state.photos.length===1&&state.mode==='collage'")
    assert len(uploads)==1 and page.evaluate("state.collageLayout==='strip'")
    with page.expect_file_chooser() as chooser:page.locator('#addMore').click(button='right')
    chooser.value.set_files([]);page.wait_for_timeout(100)
    assert page.evaluate('state.photos.length===1')
    stored['/private/photos/recovered.jpg']=jpeg
    page.evaluate("""()=>{
      state.mode='photo';state.collageLayout='auto';save();const key=window.STUDIO_DRAFT_KEY||'liuying-draft';
      const id='recovered',before=JSON.stringify({mode:state.mode,layout:state.collageLayout,template:state.templateId,media:state.media,orientation:state.orientation,active:state.active,photos:state.photos.map(p=>p.src)});
      localStorage.setItem(key+'-capture',JSON.stringify({id,mode:'strip',before}));
      localStorage.setItem(key+'-capture-result',JSON.stringify({photos:[{src:'/private/photos/recovered.jpg',captureId:id}],finished:{id}}));
    }""")
    page.reload();page.wait_for_function("state.photos.length===2&&state.mode==='collage'&&state.collageLayout==='strip'")
    page.reload();page.wait_for_function('window.PhotoCapture');page.wait_for_timeout(1500)
    assert page.evaluate('state.photos.length===2')
    browser.close()
print('PASS: tap/long press/slide/keyboard/context menu, layout preservation, duplicate replay, late result, quota retry and six-photo limit')
