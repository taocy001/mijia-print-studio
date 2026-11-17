"""Verify calendar dates and full-resolution output without printing."""
import base64,io,os,mimetypes
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(**({'channel':os.environ['TEST_BROWSER_CHANNEL']} if os.environ.get('TEST_BROWSER_CHANNEL') else {}))
 for timezone in ['America/Los_Angeles','Asia/Shanghai']:
  page=browser.new_page(timezone_id=timezone);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def route(r):
   f=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
   mime={'.js':'text/javascript','.svg':'image/svg+xml','.html':'text/html','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}.get(f.suffix,mimetypes.guess_type(str(f))[0] or 'application/octet-stream')
   r.fulfill(body=f.read_bytes(),content_type=mime) if f.is_file() else r.fulfill(status=404)
  page.route('https://studio.local/**',route)
  page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{},history:[]}),sharingState:()=>JSON.stringify({}),printBatch:()=>{throw Error('Printing forbidden')}}")
  page.goto('https://studio.local/');page.evaluate('LayerEditor.ready')
  assert page.evaluate('state.lunar') is True
  for date,label,badge in [([2027,1,31],'廿四','班'),([2027,2,5],'除夕','休'),([2027,2,6],'春节','休'),([2027,2,14],'初九','班'),([2027,6,9],'端午节','休'),([2027,9,15],'中秋节','休'),([2027,9,26],'廿六','班'),([2028,1,1],'元旦',''),([2036,1,28],'春节','')]:
   info=page.evaluate('(d)=>CalendarInfo.get(...d)',date);assert (info['label'],info['badge'])==(label,badge),(date,info)
  page.evaluate("Object.assign(state,{mode:'calendar',calendarLayout:'plain',media:5012,month:'2027-02',lunar:false})")
  def recorded():
   return page.evaluate("""()=>{const old=CanvasRenderingContext2D.prototype.fillText,seen=[];CanvasRenderingContext2D.prototype.fillText=function(s,x,y,m){seen.push({s,x,y,font:this.font,color:this.fillStyle,width:Math.min(this.measureText(s).width,m||Infinity)});return old.call(this,s,x,y,m)};try{compose()}finally{CanvasRenderingContext2D.prototype.fillText=old}return seen}""")
  labels=[x['s'] for x in recorded()];assert '春节' in labels and '初九' not in labels
  page.evaluate("state.month='2026-11';state.lunar=false")
  labels=recorded();snow=next(x for x in labels if x['s']=='小雪');assert snow['color']=='#ffffff'
  assert page.evaluate('CalendarInfo.get(2026,11,22).solarTerm')
  page.evaluate('state.lunar=true');aligned=recorded()
  assert next(x['y'] for x in aligned if x['s']=='小雪')==next(x['y'] for x in aligned if x['s']=='十一')
  assert page.evaluate("new Set(Array.from({length:12},(_,i)=>{const c=document.createElement('canvas');c.width=160;c.height=160;CalendarArt.paint(c.getContext('2d'),i+1,[{x:0,y:0,w:160,h:160}]);return c.toDataURL()})).size")==12
  assert page.evaluate("(()=>{const a=compose().toDataURL(),b=compose().toDataURL();return a===b})()")
  safe=page.evaluate("""()=>{const original=CalendarArt.paint;let zones=[];CalendarArt.paint=(ctx,m,z)=>{zones=z;original(ctx,m,z)};try{compose()}finally{CalendarArt.paint=original}return zones}""")
  for item in aligned:
   assert not any(z['x']<=item['x']<=z['x']+z['w'] and z['y']<=item['y']<=z['y']+z['h'] for z in safe),(item,safe)
  page.evaluate("state.month='2027-02';state.lunar=true");assert '初九' in [x['s'] for x in recorded()]
  for media,layout,orientation,month in [(5012,'photo','portrait','2026-11'),(5012,'photo','landscape','2027-05'),(5012,'plain','portrait','2027-02'),(5014,'plain','portrait','2026-12'),(5009,'photo','portrait','2027-05')]:
   page.evaluate("([media,layout,orientation,month])=>Object.assign(state,{media,calendarLayout:layout,orientation,month})",[media,layout,orientation,month])
   labels=recorded();w,h=page.evaluate('logicalSize()')
   for item in labels:
    assert 0<=item['x']-item['width']/2 and item['x']+item['width']/2<=w,(item,w)
    assert 0<item['y']<h,(item,h)
   if media==5012:
    annotation=next(x for x in labels if x['s']=='初二')
    day=next(x for x in labels if x['x']==annotation['x'] and x['y']<annotation['y'] and x['s'].isdigit() and annotation['y']-x['y']<100)
    assert annotation['y']-day['y']<75,(day,annotation)
   if media==5014:assert [x['s'] for x in labels if ' 年 ' in x['s']]==['2026 年 12 月','2027 年 1 月']
   if media==5012 and layout=='photo':
    sizes=[float(x['font'].split('px')[0].split()[-1]) for x in labels if x['s'] in ['初二','初三','十一','十二']]
    assert sizes and min(sizes)>=28,sizes
   if os.environ.get('CALENDAR_PREVIEW_DIR') and timezone=='Asia/Shanghai':
    out=Path(os.environ['CALENDAR_PREVIEW_DIR']);out.mkdir(parents=True,exist_ok=True)
    (out/f'{media}-{layout}-{orientation}-{month}.png').write_bytes(base64.b64decode(page.evaluate("compose().toDataURL('image/png').split(',')[1]")))
  page.evaluate("Object.assign(state,{media:5014,month:'2026-12',calendarLayout:'plain'})")
  pages=page.evaluate('preparePrintPages()');assert len(pages)==1
  assert Image.open(io.BytesIO(base64.b64decode(pages[0]['base64']))).size==(1216,1824)
  assert not errors,errors
  page.close()
 browser.close()
print('PASS: dates, holidays/workdays, toggle, two timezones, 5 layouts, 6-week months, year rollover and final JPEG; no printing')
