import subprocess,json,time,io,os,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
adb=str(Path(os.environ.get('ANDROID_HOME',str(Path.home()/'Library/Android/sdk')))/'platform-tools/adb')
def run(*args):return subprocess.check_output([adb,*args],text=True).strip()
run('shell','am','start','-W','-n','local.liuying.studio/.MainActivity')
for attempt in range(30):
 try:pid=run('shell','pidof','local.liuying.studio').split()[0];break
 except (subprocess.CalledProcessError,IndexError):
  run('shell','am','start','-W','-n','local.liuying.studio/.MainActivity');time.sleep(.2)
else:raise RuntimeError('App did not start')
run('forward','tcp:9224','localabstract:webview_devtools_remote_'+pid)
run('forward','tcp:8634','tcp:8634')
for attempt in range(30):
 try:urllib.request.urlopen('http://127.0.0.1:9224/json/version',timeout=1).close();break
 except Exception:time.sleep(.2)
with sync_playwright() as p:
 native=p.chromium.connect_over_cdp('http://127.0.0.1:9224');app=next(pg for ctx in native.contexts for pg in ctx.pages if pg.url=='https://studio.local/')
 app.wait_for_function('window.Studio&&window.TemplateStudio')
 assert not app.evaluate('JSON.parse(Studio.state()).unresolved'),'Finish or resolve existing jobs before testing'
 assert not app.evaluate('JSON.parse(Studio.sharingState()).running'),'Stop sharing before testing'
 app.evaluate('Studio.startSharing(false)')
 app.wait_for_function('JSON.parse(Studio.sharingState()).running')
 info=app.evaluate('JSON.parse(Studio.sharingState())')
 browser=p.chromium.launch();ctx=browser.new_context(bypass_csp=True,viewport={'width':411,'height':828});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8634/');page.locator('input[name=code]').fill(info['code']);page.get_by_role('button',name='连接',exact=True).click();page.wait_for_function('window.BrowserTransport&&window.TemplateStudio');page.evaluate('LayerEditor.ready')
 buf=io.BytesIO();Image.new('RGB',(900,1200),'#698d82').save(buf,'PNG')
 with page.expect_file_chooser() as chooser:page.locator('#addFirst').click()
 chooser.value.set_files({'name':'sample.png','mimeType':'image/png','buffer':buf.getvalue()})
 page.wait_for_function('state.photos.length===1')
 src=page.evaluate('active().src');assert page.request.get('http://127.0.0.1:8634'+src).status==200
 other=browser.new_context(bypass_csp=True);other_page=other.new_page();other_page.goto('http://127.0.0.1:8634/');other_page.locator('input[name=code]').fill(info['code']);other_page.get_by_role('button',name='连接',exact=True).click();other_page.wait_for_function('window.BrowserTransport&&window.TemplateStudio')
 assert other_page.request.get('http://127.0.0.1:8634'+src).status==404
 assert other_page.evaluate('state.photos.length')==0
 page.locator('#templateBtn').click();page.wait_for_function("document.querySelectorAll('[data-template] img[src]').length===16");page.locator('[data-template="studio-petal"]').click()
 page.evaluate('confirmPrint()');page.wait_for_selector('#confirmSend');assert page.locator('.print-pages img').count()==1
 page.evaluate('closeSheet()');page.screenshot(path='/tmp/liuying-shared-phone.png')
 page.set_viewport_size({'width':1440,'height':900});page.screenshot(path='/tmp/liuying-shared-desktop.png')
 # Keep the Android app in background while the HTTP endpoint is exercised.
 run('shell','input','keyevent','3');time.sleep(2)
 assert page.request.get('http://127.0.0.1:8634/api/state').status==200
 assert not errors,errors
 app.evaluate('Studio.stopSharing()');app.wait_for_function('!JSON.parse(Studio.sharingState()).running')
 print('PASS Pixel: pairing, upload, shared editor, template preview, per-browser photo isolation, print preview, background HTTP; no print submitted')
 browser.close()
