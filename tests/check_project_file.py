"""Portable synthetic projects, editing round trips and atomic failures; no printing."""
import mimetypes
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch();page=browser.new_page(viewport={'width':390,'height':844});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script("window.Studio={landscape:()=>innerWidth>innerHeight,state:()=>'{\"device\":{},\"history\":[]}',printBatch:()=>{throw Error('No printing')}}")
    def route(r):
        assert r.request.method=='GET'
        file=ROOT/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.LabelBatch&&window.StudioExtras');page.evaluate('NameLabels.ready');page.evaluate('LayerEditor.ready')
    page.evaluate("""async()=>{
      await loadPhoto({src:'/sample.svg'});
      state={...defaults,mode:'photo',media:5009,photos:[{src:'/sample.svg',zoom:1.5,x:.2,y:-.3,turn:1,filter:'none',fit:'cover',border:20,overlays:[{id:'old',kind:'text',text:'Synthetic project',sizePct:8,fx:.5,fy:.4,angle:20,hidden:true}]}],active:0,coatTexture:'waves',copies:2};
      window.packageText=await ProjectFile.encode();
    }""")
    result=page.evaluate("""async()=>{const p=JSON.parse(packageText);const d=await ProjectFile.decode(packageText);return {format:p.format,version:p.version,photo:p.editing.photos[0],refs:Object.keys(p.assets),paths:packageText.includes('/private/')||packageText.includes('/sample.svg'),size:[d.assets.a0.width,d.assets.a0.height]};}""")
    assert result['format']=='mijia-print-project' and result['version']==1 and result['refs']==['a0'] and not result['paths'],result
    assert result['photo']['zoom']==1.5 and result['photo']['overlays'][0]['hidden'],result
    invalid=page.evaluate("""async()=>{
      const edits=[p=>p.version=99,p=>p.editing.photos[0].src='https://untrusted.test/x',p=>p.editing.photos[0].zoom=100,p=>p.editing.photos[0].templateId='unknown',p=>p.editing.photos[0].overlays[0].kind='html',p=>p.editing.photos[0].overlays[0].text='x'.repeat(161),p=>p.editing.photos.push(...Array(6).fill(p.editing.photos[0])),p=>p.assets.a0='notjpeg',p=>p.editing.photos[0].idBackground='blue',p=>p.editing.sceneLayers={'__bad':[]}];
      const before=JSON.stringify(state),results=[];for(const edit of edits){const p=JSON.parse(packageText);edit(p);try{await ProjectFile.restore(JSON.stringify(p));results.push(false);}catch{results.push(JSON.stringify(state)===before);}}return results;
    }""")
    assert all(invalid),invalid
    restored=page.evaluate("""async()=>{
      const source=JSON.parse(packageText).assets.a0;let uploads=0;
      Studio.importProjectImage=data=>{if(data!==source)throw Error('Changed asset');uploads++;return JSON.stringify({src:'/private/photos/11111111-1111-1111-1111-111111111111.jpg'});};
      const im=new Image();im.src='data:image/jpeg;base64,'+source;await im.decode();images.set('/private/photos/11111111-1111-1111-1111-111111111111.jpg',im);
      pendingPrint={pages:['old']};await ProjectFile.restore(packageText);
      const recovered=JSON.parse(await ProjectFile.encode());return {uploads,pending:pendingPrint,photo:recovered.editing.photos[0],persisted:JSON.parse(localStorage.getItem(window.STUDIO_DRAFT_KEY||'liuying-draft')).photos[0].src};
    }""")
    assert restored['uploads']==1 and restored['pending'] is None and restored['persisted'].startswith('/private/photos/'),restored
    assert restored['photo']==result['photo'],(restored,result)
    failed=page.evaluate("""async()=>{const before=JSON.stringify(state);Studio.importProjectImage=()=>JSON.stringify({error:'Synthetic storage failure'});try{await ProjectFile.restore(packageText);return false;}catch{return JSON.stringify(state)===before;}}""")
    assert failed
    quota=page.evaluate("""async()=>{
      const before=JSON.stringify(state),old=Storage.prototype.setItem;
      const image=new Image();image.src='data:image/jpeg;base64,'+JSON.parse(packageText).assets.a0;await image.decode();
      Studio.importProjectImage=()=>{const src='/private/photos/44444444-4444-4444-4444-444444444444.jpg';images.set(src,image);return JSON.stringify({src});};
      Storage.prototype.setItem=function(){throw Error('Synthetic quota');};
      try{await ProjectFile.restore(packageText);return false;}catch{return JSON.stringify(state)===before;}finally{Storage.prototype.setItem=old;}
    }""")
    assert quota
    modes=page.evaluate("""async()=>{
      const results=[];const path='/private/photos/22222222-2222-2222-2222-222222222222.jpg';
      Studio.importProjectImage=data=>{const im=new Image();im.src='data:image/jpeg;base64,'+data;images.set(path,im);return JSON.stringify({src:path});};
      for(const mode of MODES.map(m=>m[0])){
        state={...defaults,mode,media:5014,photos:[{src:'/sample.svg',filter:'none',zoom:1,turn:0,x:0,y:0,overlays:[],idBackground:'blue',idCutouts:{blue:'/sample.svg'},coatTexture:'custom',coatSource:'/sample.svg'}],active:0,sceneLayers:{label:[{kind:'text',text:'Test',hidden:true,fx:.5,fy:.5,sizePct:9}]},labelBatchEnabled:true,labelBatchItems:[{title:'Test A',subtitle:''},{title:'Test B',subtitle:'Example'}],nameGap:2,cardStyle:'reading',labelTheme:'rainbow',collageLayout:'strip',coatThreshold:80};
        const raw=await ProjectFile.encode(),expected=JSON.parse(raw).editing;
        const image=new Image();image.src='data:image/jpeg;base64,'+JSON.parse(raw).assets.a0;await image.decode();
        Studio.importProjectImage=()=>{images.set(path,image);return JSON.stringify({src:path});};
        await ProjectFile.restore(raw);const actual=JSON.parse(await ProjectFile.encode()).editing;
        results.push(JSON.stringify(actual)===JSON.stringify(expected)&&state.photos[0].idCutouts.blue===path&&state.photos[0].coatSource===path);
      }return results;
    }""")
    assert all(modes),modes
    page.locator('#menuBtn').click();assert page.locator('#saveProject').count()==1 and page.locator('#openProject').count()==1
    assert not errors,errors
    payload=page.evaluate('packageText');page.close()
    page=browser.new_page(viewport={'width':1440,'height':1000});uploads=[];stored={}
    def web_route(r):
        name=urlparse(r.request.url).path
        if name=='/api/state':r.fulfill(json={'host':'desktop','permission':True,'device':{},'history':[]});return
        if name=='/api/upload':
            assert r.request.method=='POST';uploads.append(name)
            path='/private/photos/33333333-3333-3333-3333-333333333333.jpg';stored[path]=r.request.post_data_buffer
            r.fulfill(json={'src':path});return
        assert r.request.method=='GET',name
        if name in stored:r.fulfill(body=stored[name],content_type='image/jpeg');return
        file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',web_route);page.goto('https://studio.test/');page.wait_for_function('window.ProjectFile&&window.BrowserTransport');page.evaluate('LayerEditor.ready')
    page.locator('#menuBtn').click()
    with page.expect_file_chooser() as chooser:page.locator('#openProject').click()
    page.once('dialog',lambda d:d.accept())
    chooser.value.set_files({'name':'example.json','mimeType':'application/json','buffer':payload.encode()})
    page.wait_for_function("state.photos[0]?.src.includes('33333333')")
    assert uploads==['/api/upload'] and len(stored)==1
    page.locator('#menuBtn').click()
    with page.expect_download() as download:page.locator('#saveProject').click()
    file=download.value;assert file.suggested_filename=='mijia-project.json'
    saved=json.loads(Path(file.path()).read_text())
    assert saved['editing']['photos'][0]['src']=='a0' and '/private/' not in json.dumps(saved)
    assert page.evaluate("!pendingPrint&&document.getElementById('loading').hidden")
    browser.close()
print('PASS: portable assets, edit settings, hidden layers, malformed input rejection, atomic failure, no printing')
