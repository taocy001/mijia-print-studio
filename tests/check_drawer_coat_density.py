"""Drawer height persistence and per-photo coating density; no printing."""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch();page=browser.new_page(viewport={'width':390,'height':844});errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.add_init_script("window.Studio={landscape:()=>innerWidth>innerHeight,state:()=>'{\"device\":{},\"history\":[]}',printBatch:()=>{throw Error('No printing')}}")
    def route(request):
        assert request.request.method=='GET'
        file=ROOT/'assets'/(urlparse(request.request.url).path.lstrip('/') or 'index.html')
        request.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream') if file.is_file() else request.fulfill(status=404,body='Missing')
    page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.Drawer&&window.StudioExtras&&window.ProjectFile');page.evaluate('LayerEditor.ready')
    page.locator('#menuBtn').click();half=page.evaluate('Drawer.height()')
    handle=page.locator('#sheetHandle').bounding_box();x=handle['x']+handle['width']/2;y=handle['y']+15
    page.mouse.move(x,y);page.mouse.down();page.mouse.move(x,y-280,steps=12);page.mouse.up();page.wait_for_timeout(220)
    full=page.evaluate('Drawer.height()');assert full>half+150
    page.locator('#menuCoat').click();assert page.evaluate('Drawer.height()')==full
    page.locator('#settingsBack').click();assert page.evaluate('Drawer.height()')==full
    page.locator('#closeSheet').click();page.locator('#menuBtn').click();assert page.evaluate('Drawer.height()')==full
    page.locator('#sheetHandle').evaluate('e=>e.click()');page.wait_for_timeout(220);assert page.evaluate('Drawer.height()')==half
    page.evaluate("openSheet('confirm','Preview','<p>Synthetic preview</p>')");assert page.evaluate('Drawer.height()')==full
    page.evaluate('closeSheet()');page.locator('#menuBtn').click();assert page.evaluate('Drawer.height()')==half
    page.locator('#sheetHandle').evaluate('e=>e.click()');page.set_viewport_size({'width':844,'height':390});page.wait_for_timeout(100);page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100)
    page.locator('#menuBtn').evaluate('e=>e.click()');assert page.evaluate('Drawer.height()')==full
    page.evaluate("Object.defineProperty(window,'visualViewport',{configurable:true,value:{height:350}});dispatchEvent(new Event('resize'))")
    assert page.evaluate('Drawer.height()')==334
    page.evaluate("delete window.visualViewport;dispatchEvent(new Event('resize'))")
    assert page.evaluate('Drawer.height()')==full
    page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});state={...defaults,media:5012,mode:'photo',photos:[{src:'/sample.svg',overlays:[]},{src:'/sample.svg',overlays:[]}],active:0};StudioExtras.openCoat();}")
    assert page.locator('#coatDensityControl').is_hidden() and page.locator('#coatThresholdControl').is_hidden()
    page.locator('[data-coat="dots"]').click();assert page.locator('#coatDensityControl').is_visible()
    unchanged=page.evaluate("""()=>{const slider=$('coatDensity'),node=$('sheetBody').firstElementChild;$('sheetBody').scrollTop=35;const scroll=$('sheetBody').scrollTop;slider.value=150;slider.dispatchEvent(new Event('input',{bubbles:true}));return slider===$('coatDensity')&&node===$('sheetBody').firstElementChild&&scroll===$('sheetBody').scrollTop&&state.photos[0].coatDensity===150&&!state.photos[1].coatDensity;}""")
    assert unchanged
    checks=page.evaluate("""async()=>{
      const result=[];const paint=(kind,amount,mode='mask')=>{const p=state.photos[0];p.coatTexture=kind;if(amount==null)delete p.coatDensity;else p.coatDensity=amount;const c=document.createElement('canvas');c.width=480;c.height=480;StudioExtras.paintCoat(c.getContext('2d'),480,480,[],mode);return c;};
      const pixels=c=>c.getContext('2d').getImageData(0,0,c.width,c.height).data;
      const white=c=>{const d=pixels(c);let n=0;for(let i=3;i<d.length;i+=4)if(d[i])n++;return n;};
      for(const kind of ['dots','lines','grid','hearts','diagonal','waves','sparkles']){
        const old=paint(kind,null),normal=paint(kind,100),sparse=paint(kind,50),dense=paint(kind,150);
        result.push(old.toDataURL()===normal.toDataURL()&&white(sparse)<white(normal)&&white(normal)<white(dense));
        const a=pixels(paint(kind,150)),b=pixels(paint(kind,150,'editor'));let equal=true;for(let i=3;i<a.length;i+=4)if((a[i]>8)!==(b[i]>2)){equal=false;break;}result.push(equal);
      }
      const sparse=paint('dots',50),dense=paint('dots',150);result.push(sparse.getContext('2d').getImageData(10,10,16,16).data.join()===dense.getContext('2d').getImageData(10,10,16,16).data.join());
      state.photos[0].coatTexture='dots';state.photos[0].coatDensity=150;state.photos[1].coatDensity=50;const raw=await ProjectFile.encode(),decoded=await ProjectFile.decode(raw);result.push(decoded.editing.photos[0].coatDensity===150&&decoded.editing.photos[1].coatDensity===50);
      const bad=JSON.parse(raw);bad.editing.photos[0].coatDensity=0;try{await ProjectFile.decode(JSON.stringify(bad));result.push(false);}catch{result.push(true);}
      state.photos[0].coatTexture='custom';state.photos[0].coatSource='/sample.svg';StudioExtras.openCoat();result.push($('coatDensityControl').hidden&&!$('coatThresholdControl').hidden);
      state.active=1;StudioExtras.openCoat();result.push($('coatDensityControl').hidden);state.photos[1].overlays=[{kind:'text',text:'Hidden',hidden:true}];StudioExtras.openCoat();result.push($('coatDensityControl').hidden&&!$('coatThresholdControl').hidden);state.photos[0].coatTexture='';state.active=0;state.media=5014;StudioExtras.openCoat();result.push($('coatDensityControl').hidden&&!$('coatThresholdControl').hidden);return result;
    }""")
    assert all(checks),checks
    texture=page.evaluate("""async()=>{
      state.media=5012;state.active=0;Studio.pickTexture=()=>{};StudioExtras.openCoat();const original=state.photos[0];$('sheetBody').querySelector('[data-coat="custom"]').click();
      state.active=1;StudioExtras.openCoat();const node=$('coatDensity');await nativeEvent({type:'texture',value:[{src:'/sample.svg'}]});
      const isolation=original.coatTexture==='custom'&&!state.photos[1].coatTexture&&node===$('coatDensity')&&$('sheetBody').querySelector('[data-coat=""]').classList.contains('selected');
      $('sheetBody').querySelector('[data-coat="custom"]').click();closeSheet();await nativeEvent({type:'texture',value:[{src:'/sample.svg'}]});return isolation&&$('sheet').hidden&&state.photos[1].coatTexture==='custom';
    }""")
    assert texture
    assert not errors,errors;browser.close()
print('PASS: remembered settings height, independent confirmation, resize bounds, per-photo density, fixed symbol size, mask agreement and project round trip')
