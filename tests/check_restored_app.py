from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse,unquote
import mimetypes,io,json,random,sys
from PIL import Image
root=Path(__file__).resolve().parents[1];assets=root/'assets'

with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':411,'height':828},is_mobile=True,has_touch=True);errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{},history:[]}),printBatch:()=>{throw Error('Printing is forbidden in tests')}}")
 def route(r):
  path=unquote(urlparse(r.request.url).path);file=assets/(path.lstrip('/') or 'index.html')
  if path.startswith('/private/'):
   buf=io.BytesIO();Image.new('RGB',(800,1200),'#387fa0').save(buf,'JPEG');r.fulfill(body=buf.getvalue(),content_type='image/jpeg');return
  if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
  else:r.fulfill(status=404,body='Missing asset')
 page.route('https://studio.local/**',route);page.goto('https://studio.local/');page.wait_for_function('window.LayerEditor&&window.CropEditor&&window.StudioExtras');page.evaluate('LayerEditor.ready')


 page.evaluate('Promise.all([NameLabels.ready,CardArt.ready])')
 def name_sheet_geometry(w,h,value=None):
  rows=2 if w==h else 1 if w>h else 3;margin=max(8,min(w,h)//65);gap=margin if value is None else int(value*300/25.4+.5)
  return 2,rows,margin,gap,(w-2*margin-gap)//2,(h-2*margin-gap*(rows-1))//rows
 for w,h in [(1040,1040),(1216,1824),(1824,1216),(1216,912)]:
  for gap in [None,0,.1,1.5,5]:
   g=page.evaluate('([w,h,g])=>{state.nameGap=g;return NameLabels.geometry(w,h)}',[w,h,gap])
   cols,rows,margin,px,cw,ch=name_sheet_geometry(w,h,gap)
   assert g==dict(rows=rows,margin=margin,gap=px,cw=cw,ch=ch),g
 page.evaluate("state.mode='label';state.media=5009;state.photos=[];render();openLayout()")
 page.locator('#nameGapInput').fill('0');page.locator('#nameGapInput').dispatch_event('input')
 assert page.evaluate('state.nameGap')==0
 page.locator('#resetNameGap').click();assert page.evaluate('state.nameGap==null')
 assert '2 列 × 4 行' not in page.locator('#sheetBody').inner_text()
 page.evaluate("closeSheet();state.mode='calendar';state.month='2026-12';state.calendarLayout='photo';state.media=5014;render()")
 assert page.evaluate('ready()')
 assert page.locator('#filterBtn').is_disabled()
 months=page.evaluate(r"""()=>{const old=text,seen=[];text=(...a)=>{if(/^(12 \/ 2026|01 \/ 2027)$/.test(a[1]))seen.push(a[1]);old(...a)};try{compose()}finally{text=old}return seen}""")
 assert months==['12 / 2026','01 / 2027'],months
 assert page.evaluate('(async()=> (await preparePrintPages()).length)()')==1
 page.evaluate('openLayout()');assert page.locator('[data-setting=calendarLayout]').count()==0
 page.evaluate("closeSheet();state.mode='card';state.orientation='auto';state.media=5012;state.cardTitle='';state.cardSubtitle='';render()")
 for media in [5009,5012,5014]:
  for kind,landscape in [('reading',True),('habit',False),('todo',False),('schedule',True),('luggage',True),('praise',False),('invite',False)]:
   page.evaluate('([m,k])=>{state.media=m;state.cardStyle=k;render()}',[media,kind])
   expected=[1040,1040] if media==5009 else [1824,1216] if media==5012 and landscape else [1216,1824]
   assert page.evaluate('logicalSize()')==expected
   assert page.evaluate('(async()=> (await preparePrintPages()).length)()')==1
 page.evaluate("state.media=5012;state.cardStyle='habit';render();openLayout()")
 assert page.locator('[data-setting=cardStyle]').count()==7
 page.evaluate("closeSheet();state.photos=[{src:'/sample.svg',width:1200,height:800,zoom:1,fit:'cover',overlays:[]},{src:'/sample.svg',width:1200,height:800,zoom:1,fit:'cover',overlays:[]}];state.mode='idcard';")
 page.evaluate("loadPhoto({src:'/sample.svg'})")
 for media,orientation,direction,count in [(5012,'portrait','landscape',2),(5012,'landscape','portrait',2),(5012,'landscape','landscape',1),(5009,'auto','portrait',1),(5014,'auto','portrait',2),(5014,'auto','landscape',2)]:
  page.evaluate('([m,o,d])=>{state.media=m;state.orientation=o;state.idCardOrientation=d;render()}',[media,orientation,direction])
  assert page.evaluate('photoFrames.length')==count,(media,direction,page.evaluate('photoFrames.length'))
  assert page.evaluate('(async()=> (await preparePrintPages()).length)()')==1
 page.evaluate("state.mode='card';state.cardStyle='habit';state.media=5012;state.orientation='auto';render()")
 page.screenshot(path='/tmp/mijia-restored-card.png')
 assert not errors,errors
 print('PASS: Web/App gap geometry, zero/reset controls, calendar year rollover, 21 card combinations, six ID-card layouts and one-sheet pagination; no printing')
 b.close()
