"""New client assets must not expose unsupported APIs on an older service."""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch();page=browser.new_page();calls=[]
    def route(r):
        name=urlparse(r.request.url).path
        if name=='/api/state':r.fulfill(json={'host':'desktop','permission':True,'device':{},'history':[]});return
        if name.startswith('/api/'):
            calls.append(name);r.fulfill(status=404,json={'error':'Unsupported'});return
        file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function("native.host==='desktop'")
    page.evaluate('Studio.state=()=>JSON.stringify(native)')
    for value in [None,{}, {'models':False,'historyStorage':False}, {'models':'true','historyStorage':'true'}]:
        page.evaluate('(value)=>native.capabilities=value',value)
        page.locator('#menuBtn').click();assert page.locator('#modelsMenu').count()==0
        page.locator('#menuHistory').click();assert page.locator('#historyStorage').count()==0
        page.evaluate('closeSheet()')
    assert not calls,calls
    page.evaluate("native.capabilities={models:true};document.getElementById('menuBtn').click()")
    assert page.locator('#modelsMenu').count()==1
    page.locator('#menuHistory').click();assert page.locator('#historyStorage').count()==0
    page.evaluate("closeSheet();native.capabilities={historyStorage:true};document.getElementById('menuBtn').click()")
    assert page.locator('#modelsMenu').count()==0
    page.locator('#menuHistory').click();assert page.locator('#historyStorage').count()==1
    page.wait_for_function("document.querySelector('#historyStorage p').textContent==='Unsupported'")
    assert calls==['/api/history/storage'],calls
    browser.close()
print('PASS: older services expose no unsupported model or history cleanup controls')
