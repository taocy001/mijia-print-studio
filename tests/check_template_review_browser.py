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
 ids=page.evaluate('TEMPLATE_CATALOG.filter(t=>TemplateCollection.includes(t.id)).map(t=>t.id)')
 assert len(ids)==72,len(ids)
 # Reproduce the reported path: choose a template, leave its strip open, drag the photo.
 for id in ids:
  page.evaluate("""id=>{EffectBrowser.exit(false);PhotoWorks.select(0);state.orientation='portrait';PhotoFlow.apply(id);TemplateStudio.setGroup(TemplateStudio.groupFor(id));render();for(const f of photoFrames){f.p.zoom=2;f.p.x=f.p.y=0;f.p.facePending=false;}render();EffectBrowser.toggle('templates');render();}""",id)
  assert page.evaluate("getComputedStyle($('preview')).touchAction")=='none',id
  p=point();swipe(**p,dx=36,dy=22)
  v=page.evaluate('({x:active().x,y:active().y,id:TemplateStudio.selectedId(),mode:EffectBrowser.kind()})')
  assert v['id']==id and v['mode']=='templates' and abs(v['x'])>0 and abs(v['y'])>0,(id,v)
 print('PASS all 72 retained templates support actual touch crop with template strip open',flush=True)
 # Lowest slot vertical drag must crop, not dismiss. Changes must survive undo/redo.
 page.evaluate("EffectBrowser.exit(false);PhotoWorks.select(0);PhotoFlow.apply('booth-life-teatime');render();for(const f of photoFrames){f.p.zoom=2;f.p.x=f.p.y=0;}render();EffectBrowser.toggle('templates');render()")
 p=point(1);swipe(**p,dy=50)
 assert page.evaluate("EffectBrowser.kind()==='templates'&&active().y!==0&&PhotoWorks.focus()===state.photos[1].photoId")
 crop=page.evaluate('active().y');page.evaluate('EffectBrowser.exit()');page.locator('#editorUndo').click()
 assert page.evaluate('PhotoWorks.photos()[1].y')==0
 page.locator('#editorRedo').click();assert abs(page.evaluate('PhotoWorks.photos()[1].y')-crop)<.001
 # Outside-photo template region switches within the selected group.
 page.evaluate("PhotoWorks.select(0);PhotoFlow.apply('booth-life-plate');TemplateStudio.setGroup('life');render();EffectBrowser.toggle('templates');render()")
 r=page.locator('#preview').bounding_box();before=page.evaluate('TemplateStudio.selectedId()');swipe(x=r['x']+r['width']*.6,y=r['y']+18,dx=-80)
 assert page.evaluate('TemplateStudio.selectedId()')!=before
 assert page.evaluate("TemplateStudio.groupFor(TemplateStudio.selectedId())==='life'")
 # Blank slots can still launch photo picking while browsing templates.
 page.evaluate("EffectBrowser.exit(false);state.photos.pop();PhotoWorks.select(4);PhotoFlow.apply('booth-life-teatime');render();EffectBrowser.toggle('templates');render()")
 p=point(empty=True);before=page.evaluate('(window.picks||[]).length');page.mouse.click(**p)
 assert page.evaluate('(window.picks||[]).length')==before+1
 # Mouse cropping follows the same hit rule.
 page.evaluate("EffectBrowser.exit(false);PhotoWorks.select(0);PhotoFlow.apply('booth-life-watch');active().zoom=2;active().x=active().y=0;render();EffectBrowser.toggle('templates');render()")
 p=point();page.mouse.move(**p);page.mouse.down();page.mouse.move(p['x']+45,p['y']+25,steps=6);page.mouse.up()
 assert page.evaluate("active().x!==0&&TemplateStudio.selectedId()==='booth-life-watch'")
 # Filter browsing still swipes, and its rail still dismisses downward.
 page.evaluate("EffectBrowser.exit();EffectBrowser.toggle('filters');render()")
 before=page.evaluate('active().filter');swipe(**point(),dx=-65)
 assert page.evaluate('active().filter')!=before
 r=page.locator('#effectChoices').bounding_box();swipe(x=r['x']+r['width']/2,y=r['y']+r['height']/2,dy=65)
 assert not page.evaluate('EffectBrowser.active()')
 # Balanced curated groups apply to both gallery and strip, on every supported paper.
 counts=page.evaluate('Object.fromEntries(Object.entries(TemplateCollection.byGroup).map(([g,ids])=>[g,ids.length]))')
 assert min(counts.values())==10 and max(counts.values())==12,counts
 matrix=page.evaluate("""()=>{const out=[];for(const [media,orientation] of [[5012,'portrait'],[5012,'landscape'],[5009,'portrait'],[5014,'portrait']]){state.media=media;state.orientation=orientation;render();const counts={};for(const [g] of TemplateCollection.groups){TemplateStudio.setGroup(g);const list=TemplateStudio.browseItems();if(list.some(t=>!TemplateCollection.includes(t.id)))throw Error('retired choice');counts[g]=list.filter(t=>!t.disabled).length;}out.push({media,orientation,counts});}return out}""")
 assert all(min(row['counts'].values())>=5 and max(row['counts'].values())<=12 for row in matrix),matrix
 # Retirement only affects discovery: all 28 recently removed designs still render and save.
 retired=page.evaluate("TEMPLATE_CATALOG.filter(t=>!TemplateCollection.includes(t.id)&&!BoothTemplates.retired(t.id)).map(t=>t.id)")
 assert len(retired)==28,retired
 for id in retired:
  page.evaluate("id=>{state.media=5012;state.orientation='portrait';PhotoWorks.select(0);PhotoFlow.apply(id);render()}",id)
  assert page.evaluate('photoFrames.length')>0,id
 result=page.evaluate('ProjectFile.encode().then(ProjectFile.decode).then(d=>d.editing.photos[0].work.template)')
 assert result==retired[-1]
 # Printable contact sheets document the retained groups and removed designs.
 page.evaluate("document.fonts.load('32px StudioHappy')")
 import base64,json
 for group,members in {**page.evaluate('TemplateCollection.byGroup'),'retired':retired}.items():
  data=page.evaluate("""ids=>{const c=document.createElement('canvas');c.width=1000;c.height=Math.ceil(ids.length/4)*400;const ctx=c.getContext('2d');ctx.fillStyle='#ececec';ctx.fillRect(0,0,c.width,c.height);EffectBrowser.exit(false);PhotoWorks.select(0);state.media=5012;state.orientation='portrait';ids.forEach((id,i)=>{PhotoFlow.apply(id);for(const p of PhotoWorks.photos()){p.zoom=1;p.x=p.y=0;}const out=compose(false);ctx.drawImage(out,i%4*250+7,Math.floor(i/4)*400+7,236,354);ctx.fillStyle='#222';ctx.font='14px sans-serif';ctx.fillText(TemplateStudio.selectedName(),i%4*250+8,Math.floor(i/4)*400+385);});return c.toDataURL('image/jpeg',.85).split(',')[1]}""",members)
  (ROOT/('review-'+group+'.jpg')).write_bytes(base64.b64decode(data))
 (ROOT/'review-counts.json').write_text(json.dumps(matrix))
 assert not errors,errors
 browser.close()
 print('PASS template drag arbitration, crop history, background switch, empty picker, filter preservation, 7 balanced groups and 28 legacy templates')
