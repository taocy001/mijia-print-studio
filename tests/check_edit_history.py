"""Per-photo edit history, grouped gestures and editor closure safety; no printing."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes,re
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={'width':1100,'height':900},has_touch=True)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{connected:true,media:5012,checkedAt:Date.now()},history:[]}),printBatch:()=>{throw Error('No printing')}}")
    def route(r):
        assert r.request.method=='GET'
        f=root/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
        r.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(str(f))[0] or 'application/octet-stream') if f.is_file() else r.fulfill(status=404,body='Missing')
    page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.wait_for_load_state('load');page.evaluate('LayerEditor.ready')
    assert page.evaluate('!!window.EditHistory'),'Editor must load its history module'
    page.evaluate("""async()=>{await addPhotos([{src:'/sample.svg'},{src:'/sample.svg'}]);for(const p of state.photos)Object.assign(p,{facePending:false,fit:'cover',zoom:2,x:0,y:0});selectPhoto(0);render();}""")
    page.wait_for_timeout(100)
    page.evaluate("""()=>{
      const check=(v,m)=>{if(!v)throw Error(m);};const p=active(),other=state.photos[1],src=p.src;
      check(!EditHistory.status().undo,'Initial image load must not create history');
      changeSetting('filter','bw');p.x=.17;EditHistory.undo();check(p.filter==='none'&&p.x===.17,'Undo must change only edited fields, not automatic crop');EditHistory.redo();check(p.filter==='bw','Redo filter');
      selectPhoto(1);check(!EditHistory.status().undo,'Same source photos must have independent stacks');changeSetting('filter','cool');EditHistory.undo();check(other.filter==='none'&&p.filter==='bw','Other photo isolation');
      selectPhoto(0);changeSetting('fit','contain');EditHistory.undo();check(p.fit==='cover'&&p.zoom===2&&p.x===.17,'Fit must restore compound crop edits');EditHistory.redo();check(p.fit==='contain'&&p.zoom===1,'Redo fit');EditHistory.undo();
      const id=TEMPLATE_CATALOG[0].id;TemplateStudio.apply(id,{preserveCrop:true});check(p.templateId===id,'Template applied');EditHistory.undo();check(!p.templateId&&state.mode==='photo','Undo template mirrors current mode');EditHistory.redo();check(p.templateId===id&&state.mode==='template','Redo template');EditHistory.undo();
      const crop=JSON.stringify([p.zoom,p.x,p.y,p.turn]);$('rotate').click();EditHistory.undo();check(JSON.stringify([p.zoom,p.x,p.y,p.turn])===crop,'Rotation one compound edit');
      check(p.src===src&&p===active(),'Restore must retain original photo object and source');
      changeSetting('filter','fresh');EditHistory.undo();check(EditHistory.status().redo,'Redo available');changeSetting('filter','film');check(!EditHistory.status().redo,'New edit invalidates redo');
    }""")
    page.evaluate('openFilters()');page.locator('#toneSharp').select_option('2')
    assert page.evaluate('active().sharpen===2')
    page.evaluate('EditHistory.undo()');assert page.evaluate('active().sharpen===0')
    page.evaluate('EditHistory.redo()');assert page.evaluate('active().sharpen===2')
    # Real mouse drag creates one entry despite many move events and render frames.
    page.evaluate("closeSheet();Object.assign(active(),{templateId:null,fit:'cover',zoom:2,x:0,y:0});state.mode='photo';render()")
    page.wait_for_timeout(80)
    box=page.locator('#preview').bounding_box();x=box['x']+box['width']*.5;y=box['y']+box['height']*.4
    page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+60,y+30,steps=12);page.mouse.up();page.wait_for_timeout(80)
    assert page.evaluate('active().x!==0||active().y!==0'),'Drag should edit crop'
    page.evaluate('EditHistory.undo()')
    assert page.evaluate('active().x===0&&active().y===0'),'One undo should revert entire drag'
    page.evaluate('EditHistory.redo()')
    assert page.evaluate('active().x!==0||active().y!==0')
    # Two fingers, then one continuing finger, must remain a single crop transaction.
    page.evaluate("Object.assign(active(),{zoom:1.5,x:0,y:0});render()")
    page.wait_for_timeout(80)
    before=page.evaluate('JSON.stringify([active().zoom,active().x,active().y])')
    cdp=page.context.new_cdp_session(page)
    x,y=page.evaluate("()=>{const r=$('preview').getBoundingClientRect();return [(Math.max(r.left,0)+Math.min(r.right,innerWidth))/2,(Math.max(r.top,0)+Math.min(r.bottom,innerHeight))/2]}")
    cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x-30,'y':y,'id':1},{'x':x+30,'y':y,'id':2}]})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-65,'y':y,'id':1},{'x':x+65,'y':y,'id':2}]})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[{'x':x-65,'y':y,'id':1}]})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-90,'y':y+15,'id':1}]})
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
    after=page.evaluate('JSON.stringify([active().zoom,active().x,active().y])')
    assert before!=after,'Real pinch should change crop'
    page.evaluate('EditHistory.undo()')
    assert page.evaluate('JSON.stringify([active().zoom,active().x,active().y])')==before,'2→1→0 touch gesture must undo in one step'
    page.evaluate('EditHistory.redo()')
    assert page.evaluate('JSON.stringify([active().zoom,active().x,active().y])')==after
    page.evaluate("LayerEditor.create({kind:'text',text:'First'});LayerEditor.openEditor(LayerEditor.selected())")
    page.locator('#layerText').fill('Changed text')
    page.evaluate('active().x=.42;active().y=-.23;render()')
    page.locator('#menuBtn').click();page.locator('#undoEdit').click()
    assert page.evaluate("active().overlays[0].text==='First'&&active().x===.42&&active().y===-.23"),'Text undo must retain automatic face crop while input was pending'
    page.locator('#redoEdit').click()
    assert page.evaluate("active().overlays[0].text==='Changed text'")
    # Undo invalidates existing object-edit closures before another edit can target stale objects.
    page.evaluate("LayerEditor.openEditor(active().overlays[0])")
    page.locator('#layerText').fill('Third');page.evaluate('EditHistory.undo()')
    assert page.evaluate("!document.body.classList.contains('layer-editing')&&active().overlays[0].text==='Changed text'")
    page.evaluate("LayerEditor.select(active().overlays[0].id);LayerEditor.remove()")
    assert page.evaluate("active().overlays.length===0&&!!document.getElementById('layerUndo')"),'Deletion keeps immediate undo'
    page.locator('#layerUndo button').click();page.evaluate('EditHistory.redo();EditHistory.undo()')
    assert page.evaluate('active().overlays.length===1'),'Deletion must restore exactly one object'
    page.evaluate("LayerEditor.select(active().overlays[0].id);LayerEditor.remove();window.staleUndo=$('layerUndo').querySelector('button');changeSetting('filter','cool');staleUndo.click()")
    assert page.evaluate("active().overlays.length===0&&active().filter==='cool'"),'Stale deletion button must not undo a newer edit'
    page.evaluate('EditHistory.undo();EditHistory.undo()')

    page.evaluate("LayerEditor.openEditor(active().overlays[0])")
    assert page.evaluate("()=>{const e=new KeyboardEvent('keydown',{key:'z',ctrlKey:true,bubbles:true,cancelable:true});$('layerText').dispatchEvent(e);return !e.defaultPrevented}")
    page.locator('#layerText').fill('Keyboard protected');page.locator('#menuBtn').click()
    page.keyboard.press('Control+z')
    assert page.evaluate("active().overlays[0].text==='Changed text'")
    page.keyboard.press('Control+Shift+z')
    assert page.evaluate("active().overlays[0].text==='Keyboard protected'")
    page.evaluate("""()=>{
      const photo=active();const initial=EditHistory.status();native.device={media:5009,checkedAt:Date.now()};render();save();if(JSON.stringify(EditHistory.status())!==JSON.stringify(initial))throw Error('Device/render created history');
      state.photos=[{...photo,overlays:[]}];state.active=0;render();if(EditHistory.status().undo||EditHistory.status().redo)throw Error('New project inherited history');
      for(let i=0;i<45;i++)EditHistory.run(()=>active().filter=i%2?'cool':'bw');let count=0;while(EditHistory.status().undo){EditHistory.undo();count++;}if(count!==40)throw Error('History bound '+count);
    }""")
    for theme in ['light','dark']:
        page.emulate_media(color_scheme=theme);page.evaluate('closeSheet()');page.locator('#menuBtn').click()
        style=page.evaluate("()=>{const b=$('redoEdit'),r=b.closest('.edit-history-row'),s=getComputedStyle(b),bg=getComputedStyle(r);return {color:s.color,background:bg.backgroundColor,width:b.getBoundingClientRect().width,height:b.getBoundingClientRect().height,disabled:b.disabled}}")
        def luminance(value):
            rgb=[int(n)/255 for n in re.findall(r'\d+',value)[:3]]
            values=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
            return sum(v*w for v,w in zip(values,[.2126,.7152,.0722]))
        a,b=sorted([luminance(style['color']),luminance(style['background'])])
        assert (b+.05)/(a+.05)>=3,(theme,style)
        assert style['width']>=44 and style['height']>=44 and not style['disabled'],style
    assert not errors,errors
    browser.close()
print('PASS: per-photo undo/redo, same-source isolation, crop gestures, templates, text, deletion, native text shortcuts, new drafts and bounded history; no printing')
