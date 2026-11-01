"""Effect gestures change only the active photo; no printer calls."""
from pathlib import Path
from urllib.parse import urlparse
import json,mimetypes,time
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch()
    for native,width,height in [(True,390,844),(False,390,844),(True,844,390),(False,844,390),(False,1440,900)]:
        print('Effect mode',native,width,height,flush=True)
        page=browser.new_page(viewport={'width':width,'height':height},is_mobile=width<1000,has_touch=width<1000)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        if native:page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{connected:true,media:5012,checkedAt:Date.now()},history:[]}),landscape:()=>innerWidth>innerHeight,printBatch:()=>{throw Error('Printing forbidden')}}")
        def route(r):
            assert r.request.method=='GET','No mutation requests in gesture tests'
            name=urlparse(r.request.url).path
            if name=='/api/state':r.fulfill(json={'permission':True,'device':{'connected':True,'media':5012,'checkedAt':int(time.time()*1000)},'history':[]});return
            file=root/'assets'/(name.lstrip('/') or 'index.html')
            if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:r.fulfill(status=404,body='Missing')
        page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.wait_for_load_state('load');page.evaluate('LayerEditor.ready')
        page.evaluate("""async()=>{await addPhotos([{src:'/sample.svg'},{src:'/sample.svg'}]);state.photos.forEach(p=>p.facePending=false);selectPhoto(0);Object.assign(active(),{fit:'contain',border:37,zoom:1.5,x:.23,y:-.17,filter:'none',sharpen:2});LayerEditor.create({kind:'text',text:'SAMPLE',fx:.5,fy:.35,sizePct:12});LayerEditor.select(null);render();}""")
        page.wait_for_timeout(80)
        stable=lambda:page.evaluate("JSON.stringify(state.photos.map(({filter,templateId,...p})=>p))")
        original=stable()
        rects=lambda:page.evaluate("()=>Object.fromEntries(['paperStage','photos'].map(id=>{const r=$(id).getBoundingClientRect();return [id,[r.x,r.y,r.width,r.height]]}).concat([['dock',(()=>{const r=document.querySelector('.dock').getBoundingClientRect();return [r.x,r.y,r.width,r.height]})()]]))")
        before=rects()
        page.locator('#filterBtn').click();page.wait_for_function("EffectBrowser.kind()==='filters'")
        assert page.locator('#effectTools').is_visible()
        assert page.locator('#sheet').is_hidden()
        assert page.locator('#filterBtn').get_attribute('aria-pressed')=='true'
        current=rects()
        for key in before:
            assert max(abs(a-b) for a,b in zip(before[key],current[key]))<1.5,(native,width,key,before,current)
        assert page.locator('#effectPrev').is_disabled()
        cdp=page.context.new_cdp_session(page)
        def points():
            return page.evaluate("()=>{const r=$('preview').getBoundingClientRect(),v=document.querySelector('.workspace').getBoundingClientRect();const l=Math.max(r.left,v.left,0),rr=Math.min(r.right,v.right,innerWidth),t=Math.max(r.top,v.top,0),b=Math.min(r.bottom,v.bottom,innerHeight);return [l+(rr-l)*.7,t+(b-t)*.36,(rr-l)*.4]}")
        def swipe(dx=None,dy=0):
            x,y,d=points();dx=-d if dx is None else dx
            if width<1000:
                cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
                for i in range(1,7):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+dx*i/6,'y':y+dy*i/6,'id':1}]})
                cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
            else:
                page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+dx,y+dy,steps=6);page.mouse.up()
            page.wait_for_timeout(100)
        swipe();assert page.evaluate('active().filter===FILTERS[1][0]'),'Left swipe advances one tone'
        assert stable()==original,'Effect changed crop/layers/sharpness'
        swipe(3,2);assert page.evaluate('active().filter===FILTERS[1][0]'),'Tap changed effect'
        swipe(0,45);assert page.evaluate('active().filter===FILTERS[1][0]'),'Vertical drag changed effect'
        assert stable()==original,[(i,{k:(a.get(k),b.get(k)) for k in set(a)|set(b) if a.get(k)!=b.get(k)}) for i,(a,b) in enumerate(zip(json.loads(original),json.loads(stable())))]
        if width<1000:
            x,y,d=points()
            cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1},{'x':x-30,'y':y,'id':2}]})
            cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-30,'y':y,'id':1},{'x':x-80,'y':y,'id':2}]})
            cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(80)
            assert page.evaluate('active().filter===FILTERS[1][0]') and stable()==original,'Pinch changed effect or crop'
        page.locator('#effectAll').click();page.locator('[data-filter=bw]').click();assert page.evaluate("sheetKind==='filters'&&EffectBrowser.active()&&active().filter==='bw'")
        page.locator('#closeSheet').click();assert page.locator('#sheet').is_hidden() and page.locator('#effectTools').is_visible()
        page.locator('[data-photo="1"]').click(position={'x':5,'y':40});page.wait_for_timeout(80)
        assert page.evaluate("EffectBrowser.kind()==='filters'&&active().filter==='none'")
        page.locator('#effectNext').click();page.wait_for_timeout(80)
        assert page.evaluate("state.photos[0].filter==='bw'&&state.photos[1].filter===FILTERS[1][0]")
        page.locator('[data-photo="0"]').click(position={'x':5,'y':40});page.wait_for_timeout(80)
        page.locator('#templateBtn').click();page.wait_for_function("EffectBrowser.kind()==='templates'")
        original=stable();before=rects()
        for _ in range(3):page.locator('#effectNext').click()
        page.wait_for_timeout(150)
        assert page.evaluate('active().templateId===TEMPLATE_CATALOG[2].id')
        for key,values in before.items():assert max(abs(a-b) for a,b in zip(values,rects()[key]))<1.5,(native,width,key,'template moved layout')
        assert stable()==original,[(i,{k:(a.get(k),b.get(k)) for k in set(a)|set(b) if a.get(k)!=b.get(k)}) for i,(a,b) in enumerate(zip(json.loads(original),json.loads(stable())))]
        page.locator('#effectAll').click();page.locator('#noTemplate').click();assert page.evaluate('!active().templateId')
        assert stable()==original,'No-template selection reset saved crop'
        page.locator('#closeSheet').click();page.locator('#effectDone').click();page.wait_for_timeout(80)
        assert page.evaluate('!EffectBrowser.active()')
        page.locator('#filterBtn').click();page.wait_for_timeout(50);page.locator('#filterBtn').click();assert page.evaluate('!EffectBrowser.active()')
        page.locator('#templateBtn').click();page.locator('#layoutBtn').click();assert page.evaluate("!EffectBrowser.active()&&sheetKind==='layout'")
        page.screenshot(path=f'/tmp/effect-browser-{native}-{width}.png')
        assert not errors,errors
        page.close()
    browser.close()
print('PASS: native/browser effects, touch/mouse gestures, crop/layer isolation, stable layout, per-photo settings, grids and exits; no printing')
