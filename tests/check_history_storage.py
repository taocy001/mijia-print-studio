"""Synthetic history cleanup UI; no files or print jobs are deleted."""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch()
    for width,height in [(1440,1000),(390,844)]:
        page=browser.new_page(viewport={'width':width,'height':height});posts=[];errors=[];cleaned=[False];hold=[False];pending=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def route(r):
            name=urlparse(r.request.url).path
            if name=='/api/state':
                job={'token':'test','phase':'done','createdAt':1,'media':5009,'message':'已完成','canReprint':not cleaned[0],'filesCleared':cleaned[0]}
                if not cleaned[0]:job['file']='prints/22222222-2222-2222-2222-222222222222.jpg'
                value={'host':'desktop','permission':True,'device':{},'history':[job]}
                if hold[0]:pending.append((r,value));hold[0]=False;return
                r.fulfill(json=value);return
            if name=='/api/history/storage':r.fulfill(json={'bytes':0 if cleaned[0] else 1048576,'files':0 if cleaned[0] else 2,'jobs':1});return
            if name=='/api/history/clear':posts.append(r.request.post_data_json);cleaned[0]=True;r.fulfill(json={'ok':True,'bytes':1048576,'files':2,'pending':0});return
            if r.request.method!='GET':raise AssertionError(name)
            file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
            if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:r.fulfill(status=404,body='Missing')
        page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function("native.host==='desktop'")
        page.evaluate("state.photos=[{src:'/private/prints/11111111-1111-1111-1111-111111111111.jpg'}];")
        page.locator('#menuBtn').click();page.locator('#menuHistory').click()
        button=page.get_by_role('button',name='清理历史打印文件')
        page.get_by_text('可清理 1.0 MB · 2 个打印文件').wait_for()
        page.once('dialog',lambda d:d.dismiss());button.click();assert not posts
        hold[0]=True;page.evaluate('void BrowserTransport.refresh()')
        page.wait_for_timeout(50);assert pending
        page.once('dialog',lambda d:d.accept());button.click()
        page.wait_for_timeout(100)
        request,value=pending.pop();request.fulfill(json=value)
        page.get_by_text('可清理 0.0 MB · 0 个打印文件').wait_for()
        assert posts==[{'confirmed':True,'keepFiles':['/private/prints/11111111-1111-1111-1111-111111111111.jpg']}]
        assert button.is_disabled();assert page.evaluate("sheetKind==='history'")
        page.locator('[data-history]').click()
        assert '打印文件已清理' in page.locator('#sheetBody').inner_text()
        assert page.locator('#reprintOriginal').count()==0;assert page.locator('#importHistory').count()==0
        assert not errors,errors;page.close()
    browser.close()
print('PASS: history cleanup scope, draft references, confirmation, in-place completion, desktop/mobile')
