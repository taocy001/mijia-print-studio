"""Model drawer state, permissions and native-app exclusion; mocked downloads."""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch()
    for width,height,manage in [(1440,1000,True),(390,844,True),(390,844,False)]:
        page=browser.new_page(viewport={'width':width,'height':height});errors=[];posts=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        result={'runtime':True,'canManage':manage,'models':[{'id':'face','name':'人脸辅助裁切','state':'missing','bytes':0},{'id':'cutout','name':'抠图换底','state':'verified','bytes':0}]}
        def route(r):
            name=urlparse(r.request.url).path
            if name=='/api/state':r.fulfill(json={'permission':True,'host':'desktop','device':{},'history':[]});return
            if name=='/api/models':r.fulfill(json=result);return
            if name=='/api/admin/models':
                posts.append(r.request.post_data_json);result['models'][0].update(state='downloading',bytes=1024);r.fulfill(json={'ok':True},status=202);return
            if r.request.method!='GET':raise AssertionError('Unexpected write: '+name)
            file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
            if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:r.fulfill(status=404,body='Missing')
        page.route('**/*',route);page.goto('https://studio.test/')
        page.wait_for_function("native.host==='desktop'");page.locator('#menuBtn').click();page.locator('#modelsMenu').click()
        page.get_by_text('未下载',exact=True).wait_for();assert page.locator('#settingsBack').is_visible()
        button=page.locator('#model-face button')
        if manage:
            button.click();page.wait_for_function("document.querySelector('#model-face button').disabled")
            assert len(posts)==1
            node=page.locator('#model-face').element_handle()
            page.evaluate("document.querySelector('#model-face').dataset.preserved='yes'")
            result['models'][0].update(state='failed',error='下载失败，请重试')
            page.get_by_role('button',name='重试下载').wait_for()
            assert node.evaluate("e=>e.isConnected&&e.dataset.preserved==='yes'")
            assert page.evaluate("sheetKind==='models'")
            result['models'][0].pop('error');result['models'][0]['state']='verified'
            page.wait_for_function("document.querySelector('#model-face button').hidden")
        else:
            assert button.is_hidden();assert not posts
            assert page.get_by_text('下载或重试请在提供服务的电脑本机打开网页').is_visible()
        result['runtime']=False
        page.get_by_text('推理运行库不可用，请在电脑上重新安装项目依赖').wait_for()
        page.locator('#settingsBack').click();assert page.evaluate("sheetKind==='menu'")
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errors,errors;page.close()
    # Native app: no desktop-only entry, requests, or replacement UI.
    page=browser.new_page();page.add_init_script("window.Studio={state:()=>'{\"device\":{},\"history\":[]}'}")
    requests=[]
    def native_route(r):
        name=urlparse(r.request.url).path
        if name.startswith('/api/'):requests.append(name);r.abort();return
        file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',native_route);page.goto('https://studio.test/');page.locator('#menuBtn').click()
    assert page.locator('#modelsMenu').count()==0;assert not requests
    browser.close()
print('PASS: model states, in-place updates, retry, host-only controls, back navigation and native exclusion')
