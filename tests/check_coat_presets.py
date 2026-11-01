"""Coating presets never alter photo JPEGs or another photo's coating."""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch();page=browser.new_page(viewport={'width':390,'height':844});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script("window.Studio={landscape:()=>innerWidth>innerHeight,state:()=>'{\"device\":{},\"history\":[]}',printBatch:()=>{throw Error('No printing')}}")
    def route(r):
        assert r.request.method=='GET'
        name=urlparse(r.request.url).path
        if name=='/api/state':r.fulfill(json={'permission':True,'host':'desktop','device':{},'history':[]});return
        file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.StudioExtras');page.evaluate('LayerEditor.ready')
    result=page.evaluate('''async()=>{
      await loadPhoto({src:'/sample.svg'});const results=[];
      for(const [media,orientation] of [[5009,'portrait'],[5012,'portrait'],[5012,'landscape'],[5014,'portrait']]){
        state={...defaults,mode:'photo',media,orientation,photos:Array.from({length:2},()=>({src:'/sample.svg',width:1200,height:800,filter:'none',turn:0,zoom:1,x:0,y:0,border:0,fit:'cover',overlays:[]})),active:0};
        const baseline=await preparePrintPages(),masks=[];
        for(const kind of ['dots','lines','grid','hearts','diagonal','waves','sparkles']){
          state.photos[0].coatTexture=kind;const pages=await preparePrintPages(),mask=compose(true,'mask'),ctx=mask.getContext('2d'),d=ctx.getImageData(0,0,mask.width,mask.height).data;let white=0,bottom=0;
          for(let i=0;i<d.length;i+=4)if(d[i]>=100){white++;if(i>=mask.width*mask.height*2)bottom++;}
          results.push({media,orientation,kind,same:pages.every((p,i)=>p.base64===baseline[i].base64),coat:!!pages[0].ocMask,other:media===5014?bottom===0:pages[1].ocMask===null,density:white/(mask.width*mask.height)});
          masks.push(pages[0].ocMask);
        }
        if(new Set(masks).size!==7)throw Error('Presets must be distinct');
        state.photos[0].coatTexture='';if((await preparePrintPages())[0].ocMask!==null)throw Error('Gloss should have no mask');
      }
      return results;
    }''')
    assert all(r['same'] and r['coat'] and r['other'] and .0005<r['density']<.2 for r in result),result
    for width,height,scheme in [(390,844,'dark'),(390,844,'light'),(1440,1000,'light')]:
        if width>=1000:
            page.close();page=browser.new_page(viewport={'width':width,'height':height},color_scheme=scheme);page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.StudioExtras&&window.BrowserTransport')
            page.evaluate("async()=>{await loadPhoto({src:'/sample.svg'});state.photos=Array.from({length:2},()=>({src:'/sample.svg',overlays:[],filter:'none'}));}")
        else:page.set_viewport_size({'width':width,'height':height});page.emulate_media(color_scheme=scheme)
        page.evaluate('state.active=0;StudioExtras.openCoat()')
        assert page.locator('[data-coat]').count()==9
        sheet=page.locator('#sheet').bounding_box()
        for box in page.locator('[data-coat]').evaluate_all('(items)=>items.map(e=>{const r=e.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}})'):
            assert box['left']>=sheet['x'] and box['right']<=sheet['x']+sheet['width']+1,box
            assert box['top']>=sheet['y'] and box['bottom']<=sheet['y']+sheet['height']+1,box
        if width>=1000:assert page.locator('#sheet').evaluate('e=>e.classList.contains("desktop-settings")')
        else:assert not page.locator('body').evaluate('e=>e.classList.contains("landscape")')
        assert page.locator('[data-coat] canvas[aria-hidden=true]').count()==9
        page.locator('[data-coat="waves"]').click()
        assert page.locator('[data-coat="waves"]').get_attribute('aria-pressed')=='true'
        assert page.evaluate("sheetKind==='coat'&&state.photos[0].coatTexture==='waves'&&!state.photos[1].coatTexture")
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.evaluate('state.active=1;StudioExtras.openCoat()')
        assert page.locator('[data-coat=""]').get_attribute('aria-pressed')=='true'
        page.screenshot(path=f'/tmp/coat-presets-{width}-{scheme}.png')
    assert not errors,errors;browser.close()
print('PASS: seven distinct masks across all papers, JPEG unchanged, per-photo isolation, nine accessible previews')
