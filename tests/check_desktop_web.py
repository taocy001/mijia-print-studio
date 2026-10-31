"""Exercise the desktop backend in explicit simulation mode."""
from pathlib import Path
import base64,io,json,os,socket,subprocess,sys,tempfile,time,urllib.request
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='liuying-desktop-test-') as folder:
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 process=subprocess.Popen([sys.executable,str(root/'web/serve.py'),'--simulate','--data',folder,'--port',str(port)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  code=process.stdout.readline().strip().split('：')[-1];url=f'http://127.0.0.1:{port}'
  for _ in range(100):
   try:urllib.request.urlopen(url,timeout=.2).close();break
   except Exception:time.sleep(.05)
  with sync_playwright() as p:
   b=p.chromium.launch();ctx=b.new_context(bypass_csp=True,viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url);page.locator('[name=code]').fill(code);page.get_by_role('button',name='连接',exact=True).click();page.wait_for_function('window.TemplateStudio&&window.BrowserTransport');page.evaluate('LayerEditor.ready')
   photo=Image.new('RGB',(800,1200),'#dce8e6');draw=ImageDraw.Draw(photo);draw.ellipse((270,180,530,440),fill='#e4b98c');draw.rounded_rectangle((190,440,610,1050),70,fill='#356690');buf=io.BytesIO();photo.save(buf,'PNG')
   with page.expect_file_chooser() as choice:page.locator('#addFirst').click()
   choice.value.set_files({'name':'portrait.png','mimeType':'image/png','buffer':buf.getvalue()});page.wait_for_function('state.photos.length===1')
   src=page.evaluate('active().src');assert ctx.request.get(url+src).status==200
   other=b.new_context();assert other.request.get(url+src).status==401
   response=other.request.post(url+'/api/pair',form={'code':code},headers={'Origin':url});assert response.ok
   assert other.request.get(url+src).status==404
   assert ctx.request.post(url+'/api/cancel',data='{}',headers={'Origin':'http://evil.invalid'}).status==403
   assert ctx.request.get(url+'/README.md').status==404
   page.locator('#templateBtn').click();page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===16");page.locator('[data-template="studio-petal"]').click();page.evaluate('BrowserTransport.refresh()');page.locator('#printBtn').click();page.locator('#confirmSend').click();page.wait_for_function('document.querySelector("#sheet").hidden')
   for _ in range(40):
    state=ctx.request.get(url+'/api/state').json()
    if state['job'].get('phase')=='done':break
    time.sleep(.1)
   assert state['job']['phase']=='done' and '未打印' in state['job']['message'],state
   pages=page.evaluate('preparePrintPages().then(p=>p.map(({preview,...rest})=>rest))');request={'requestId':'test-request-0000001','pages':pages}
   one=ctx.request.post(url+'/api/print',data=json.dumps(request),headers={'Content-Type':'application/json','Origin':url}).json();two=ctx.request.post(url+'/api/print',data=json.dumps(request),headers={'Content-Type':'application/json','Origin':url}).json();assert one['ok'] and two['duplicate']
   request['pages'][0]['copies']=2;assert ctx.request.post(url+'/api/print',data=json.dumps(request),headers={'Content-Type':'application/json','Origin':url}).status==409
   result=ctx.request.post(url+'/api/cutout',data=json.dumps({'source':src}),headers={'Content-Type':'application/json','Origin':url},timeout=60000);assert result.status==200,result.text()
   for output in result.json()['images'].values():assert ctx.request.get(url+output).status==200 and other.request.get(url+output).status==404
   page.screenshot(path='/tmp/liuying-desktop-unified.png');assert not errors,errors;b.close()
  sys.path.insert(0,str(root/'web'));from images import page_files
  mask=Image.new('RGB',(1040,1040),'black');ImageDraw.Draw(mask).rectangle((0,0,519,1039),fill='white');coat=io.BytesIO();mask.save(coat,'PNG');jpeg=io.BytesIO();mask.save(jpeg,'JPEG')
  _,data=page_files({'media':5009,'base64':base64.b64encode(jpeg.getvalue()).decode(),'ocMask':base64.b64encode(coat.getvalue()).decode(),'threshold':100})
  import struct,zlib
  assert data[:12]==b'ocpattern1\0\0' and struct.unpack('>IIII',data[12:28])==(1040,1040,len(data)-32,1)
  raw=zlib.decompress(data[32:],-15);assert raw[:520]==b'\xff'*520 and raw[520:1040]==b'\0'*520
  print('PASS: desktop real HTTP, pairing, uploads, shared templates, simulated queue, retry deduplication, owner isolation, CPU cutout and overcoat format; no Bluetooth connection')
 finally:
  process.terminate()
  try:process.wait(timeout=5)
  except subprocess.TimeoutExpired:process.kill();process.wait()
  if process.returncode not in (0,-15):print(process.stderr.read(),file=sys.stderr)
