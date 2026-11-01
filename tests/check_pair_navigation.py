import tempfile,subprocess,socket,time,urllib.request,sys
from playwright.sync_api import sync_playwright
from pathlib import Path
root=str(Path(__file__).resolve().parents[1])
with tempfile.TemporaryDirectory() as d:
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 proc=subprocess.Popen([root+'/build/venv/bin/python',root+'/web/serve.py','--simulate','--data',d,'--port',str(port)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  code=proc.stdout.readline().strip().split('：')[-1];url=f'http://127.0.0.1:{port}'
  for _ in range(60):
   try:urllib.request.urlopen(url,timeout=.2);break
   except Exception:time.sleep(.1)
  with sync_playwright() as p:
   b=p.chromium.launch();c=b.new_context();page=c.new_page();page.goto(url);page.locator('[name=code]').fill(code);page.locator('button').click();page.wait_for_function('window.BrowserTransport')
   cookies=c.cookies();old=next(cookie for cookie in cookies if cookie['name']=='liuying');old['sameSite']='Strict';c.add_cookies([old])
   c.route('http://outside.test/',lambda r:r.fulfill(content_type='text/html',body=f'<a href="{url}">Open</a>'))
   page.goto('http://outside.test/');page.locator('a').click();page.wait_for_function('window.BrowserTransport')
   assert page.locator('[name=code]').count()==0
   renewed=next(cookie for cookie in c.cookies() if cookie['name']=='liuying')
   assert renewed['sameSite']=='Lax' and renewed['value']==old['value']
   assert renewed['expires']<=old['expires']+1
   page.goto('http://outside.test/');page.locator('a').click();page.wait_for_function('window.BrowserTransport')
   fresh=b.new_context();anonymous=fresh.new_page();anonymous.goto(url);anonymous.wait_for_timeout(300)
   assert anonymous.locator('[name=code]').count()==1
   assert fresh.request.get(url+'/session.js').status==401
   b.close();print('PASS: external links, old grants restored, expiry preserved, unpaired browser remains unauthorized; no printing')
 finally:proc.terminate();proc.wait()
