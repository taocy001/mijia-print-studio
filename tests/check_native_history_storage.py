"""Native cleanup bridge contract with synthetic state; never deletes files."""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch();page=browser.new_page(viewport={'width':390,'height':844});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script('''window.calls=[];window.cleaned=false;window.Studio={landscape:()=>false,state:()=>JSON.stringify({permission:true,capabilities:{historyStorage:true},device:{},history:[]}),historyStorage:payload=>{calls.push(['summary',JSON.parse(payload)]);return JSON.stringify({bytes:cleaned?0:2048,files:cleaned?0:2});},clearHistoryFiles:payload=>{calls.push(['clear',JSON.parse(payload)]);cleaned=true;return JSON.stringify({bytes:2048,files:2,pending:0});}}''')
    def route(r):
        assert r.request.method=='GET' and urlparse(r.request.url).hostname=='studio.test'
        path=urlparse(r.request.url).path;assert not path.startswith('/api/')
        file=ROOT/'assets'/(path.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('native.capabilities?.historyStorage')
    page.evaluate("state.coatSource='/private/prints/11111111-1111-1111-1111-111111111111.jpg';openHistory()")
    button=page.get_by_role('button',name='清理历史打印文件');page.wait_for_function("!document.querySelector('#historyStorage button').disabled")
    page.once('dialog',lambda d:d.dismiss());button.click();assert page.evaluate("calls.every(x=>x[0]==='summary')")
    page.once('dialog',lambda d:d.accept());button.click();page.wait_for_function('cleaned')
    assert page.evaluate("calls.find(x=>x[0]==='clear')[1]")=={'confirmed':True,'keepFiles':['/private/prints/11111111-1111-1111-1111-111111111111.jpg']}
    assert button.is_disabled();assert page.evaluate("sheetKind==='history'")
    page.evaluate('native.capabilities={};openHistory()');assert page.locator('#historyStorage').count()==0
    assert not errors,errors;browser.close()
print('PASS: native cleanup confirmation, protected draft paths, same-panel refresh, capability guard')
