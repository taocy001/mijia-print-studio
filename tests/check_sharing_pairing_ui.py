"""Shared drawer pairing UI, isolated from printers and native devices."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
script = Path(os.environ.get('SHARING_SCRIPT', str(root/'assets/sharing.js')))
bootstrap = r'''
window.$=id=>document.getElementById(id);window.esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
window.icon=()=>'';window.sheetKind='';window.native={};window.detectionPending=false;window.messages=[];window.toast=s=>messages.push(s);
window.openSheet=(kind,title,html)=>{sheetKind=kind;$('sheetBody').innerHTML=html;};
$('menuBtn').onclick=()=>{$('sheetBody').innerHTML='';};
window.BrowserTransport={request:async(path,data)=>{if(window.denied)throw Error('Unauthorized');if(path==='admin/pairing/reset'){calls.push({path,data});shared={...shared,code:'654321'};}return shared;}};
window.calls=[];if(window.host)window.Studio={sharingState:()=>JSON.stringify(shared),resetPairing:()=>{calls.push('reset');shared={...shared,code:'654321'};return JSON.stringify(shared);},stopSharing:()=>calls.push('stop'),startSharing:()=>calls.push('start')};
Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{if(window.copyFails)throw Error('Denied');window.copied=text;}}});
'''
with sync_playwright() as p:
    browser=p.chromium.launch()
    def open_drawer(shared,host=False,denied=False,width=411):
        page=browser.new_page(viewport={'width':width,'height':828})
        page.set_content('<button id="menuBtn">菜单</button><div id="sheetBody"></div>')
        page.evaluate('s=>{window.shared=s.shared;window.host=s.host;window.denied=s.denied;}',{'shared':shared,'host':host,'denied':denied})
        page.add_script_tag(content=bootstrap)
        page.add_script_tag(path=str(script))
        page.locator('#menuBtn').click();page.locator('#sharingMenu').click()
        page.wait_for_function("!document.getElementById('sheetBody').textContent.includes('正在读取')")
        return page
    state={'running':True,'lan':True,'code':'012345','addresses':['http://192.168.1.20:8634/'],'name':'留影工坊'}
    for width in [411,1440]:
        page=open_drawer(state,width=width)
        assert page.locator('#sharePairingCode').input_value()=='012345'
        assert page.locator('#sharePairingCode').get_attribute('readonly') is not None
        assert page.locator('#stopSharing,#startLan,#startAirPrint,#stopAirPrint,#resumeSharing,#resetPairing').count()==0
        assert '已配对浏览器会记住' in page.locator('#sheetBody').inner_text()
        assert '配对失效' not in page.locator('#sheetBody').inner_text()
        page.locator('#copyPairingCode').click();assert page.evaluate('copied')=='012345'
        page.locator('[data-copy-address]').click();assert page.evaluate('copied')==state['addresses'][0]
        page.evaluate('window.copyFails=true');page.locator('#copyPairingCode').click()
        assert page.evaluate("document.activeElement.id==='sharePairingCode'&&$('sharePairingCode').selectionEnd-$('sharePairingCode').selectionStart===6")
        assert page.evaluate('messages.at(-1)').startswith('配对码已选中')
        page.close()
    for code in ['',None,'12345','1234567','<script>','１２３４５６']:
        page=open_drawer({**state,'code':code});assert page.locator('#sharePairingCode').count()==0;page.close()
    page=open_drawer({**state,'running':False});assert page.locator('#sharePairingCode').count()==0;page.close()
    page=open_drawer(state,denied=True);assert page.locator('#sharePairingCode').count()==0;assert '读取失败' in page.locator('#sheetBody').inner_text();page.close()
    page=open_drawer(state,host=True);assert page.locator('#stopSharing').count()==1;assert page.locator('#sharePairingCode').input_value()=='012345';page.close()
    for host in [False,True]:
        page=open_drawer({**state,'canManagePairing':True},host=host)
        assert page.locator('#resetPairing').count()==1
        page.once('dialog',lambda dialog:dialog.dismiss());page.locator('#resetPairing').click();assert page.evaluate('calls')==[]
        page.once('dialog',lambda dialog:dialog.accept());page.locator('#resetPairing').click()
        page.wait_for_function("$('sharePairingCode').value==='654321'")
        assert page.evaluate('calls')==(['reset'] if host else [{'path':'admin/pairing/reset','data':{}}])
        assert page.evaluate("sheetKind==='sharing'")
        if not host:assert page.locator('#stopSharing,#startLan,#startAirPrint').count()==0
        page.close()
    browser.close()
print('PASS: paired browser and host show valid codes; copy and selection fallback; controls remain host-only; invalid/stopped/denied states reveal no code')
