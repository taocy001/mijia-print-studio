"""Photo-strip page order and per-photo layers; no camera or printing."""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch();page=browser.new_page(viewport={'width':390,'height':844});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script("window.Studio={state:()=>'{\"permission\":true,\"device\":{},\"history\":[]}',printBatch:()=>{throw Error('No printing')}}")
    def route(r):
        assert r.request.method=='GET'
        name=urlparse(r.request.url).path;file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.PhotoStrips&&window.StudioExtras');page.evaluate('LayerEditor.ready')
    page.evaluate('''async()=>{
      window.stripColors=['#e63246','#1eaa46','#2850dc','#e6b428','#963cb4','#14b4be'];window.stripPhotos=[];
      for(const [i,color] of stripColors.entries()){const c=document.createElement('canvas');c.width=i%2?900:600;c.height=i%2?600:900;const x=c.getContext('2d');x.fillStyle=color;x.fillRect(0,0,c.width,c.height);const p={src:c.toDataURL(),filter:'none',zoom:1,x:0,y:0,turn:0,fit:'cover',border:0,overlays:[]};await loadPhoto(p);stripPhotos.push(p);}
    }''')
    for media,orientation in [(5009,'portrait'),(5012,'portrait'),(5012,'landscape'),(5014,'portrait')]:
        for count in range(1,7):
            result=page.evaluate('''async([media,orientation,count])=>{
              state={...defaults,mode:'collage',collageLayout:'strip',media,orientation,sixLayout:media,photos:stripPhotos.slice(0,count),active:count-1,gap:16};render();
              const frames=photoFrames.map(f=>({index:state.photos.indexOf(f.p),x:f.x,y:f.y,w:f.w,h:f.h}));
              const before=compose().toDataURL();selectPhoto(0);render();const unchanged=before===compose().toDataURL();
              const pages=await preparePrintPages(),image=new Image();image.src='data:image/jpeg;base64,'+pages[0].base64;await image.decode();const c=document.createElement('canvas');c.width=image.width;c.height=image.height;const x=c.getContext('2d');x.drawImage(image,0,0);
              const samples=frames.map(f=>{let xx=f.x+f.w/2,yy=f.y+f.h/2;if(media===5009){xx=1040-xx;yy=1040-yy;}else if(orientation==='landscape'){const old=xx;xx=1216-yy;yy=old;}return Array.from(x.getImageData(Math.floor(xx),Math.floor(yy),1,1).data).slice(0,3);});
              return {frames,unchanged,samples,pages:pages.length,size:[image.width,image.height],logical:logicalSize()};
            }''',[media,orientation,count])
            assert result['pages']==1 and len(result['frames'])==count,result
            assert result['unchanged']
            assert result['size']==([1040,1040] if media==5009 else [1216,1824])
            colors=[(230,50,70),(30,170,70),(40,80,220),(230,180,40),(150,60,180),(20,180,190)]
            for i,(frame,actual) in enumerate(zip(result['frames'],result['samples'])):
                assert frame['index']==i and frame['w']>0 and frame['h']>0
                assert abs(frame['w']/frame['h']-4/3)<.001
                assert max(abs(a-b) for a,b in zip(actual,colors[i]))<=12,(media,count,i,actual)
                if media==5014:assert frame['y']+frame['h']<=912.01 or frame['y']>=912,frame
    bounds=page.evaluate('''()=>{const bad=[];for(const [w,h,split] of [[1040,1040,false],[1216,1824,false],[1824,1216,false],[1216,1824,true]])for(let n=1;n<=6;n++)for(const b of [0,200])for(const gap of [0,80])for(const f of PhotoStrips.layout(w,h,n,b,gap,split))if(f.w<=0||f.h<=0||f.x<0||f.y<0||f.x+f.w>w||f.y+f.h>h)bad.push(f);return bad;}''')
    assert not bounds,bounds
    layers=page.evaluate('''async()=>{
      state.media=5014;state.sixLayout=5014;state.photos=stripPhotos.slice(0,4);state.active=0;render();const original=(await preparePrintPages())[0];
      state.photos[0].overlays=[{id:'secret',kind:'text',text:'SECRET',font:'sans',color:'#ffffff',sizePct:20,fx:.5,fy:.5,hidden:true}];render();const page=(await preparePrintPages())[0],mask=compose(true,'mask').getContext('2d');
      return {same:original.base64===page.base64,coat:!!page.ocMask,counts:photoFrames.map(f=>{const d=mask.getImageData(Math.ceil(f.x),Math.ceil(f.y),Math.floor(f.w)-1,Math.floor(f.h)-1).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i]>100)n++;return n;})};
    }''')
    assert layers['same'] and layers['coat'] and layers['counts'][0]>0 and not any(layers['counts'][1:]),layers
    page.evaluate('openLayout()');assert page.locator('[data-setting="collageLayout"]').count()==1
    assert page.locator('[data-value="strip"]').inner_text()=='照片条'
    page.evaluate("state.media=5012;state.sixLayout=5014;native.device={connected:true,media:5012,checkedAt:Date.now()};syncPaper()")
    assert page.evaluate("state.media===5014&&state.mode==='collage'&&state.collageLayout==='strip'")
    integration=page.evaluate("""async()=>{
      selectPhoto(1);render();const before=photoFrames.map(f=>[f.x,f.y,f.w,f.h]);openLayout();
      const slider=$('borderInput');slider.value=200;slider.dispatchEvent(new Event('input',{bubbles:true}));render();
      const changed=JSON.stringify(before)!==JSON.stringify(photoFrames.map(f=>[f.x,f.y,f.w,f.h]));
      selectPhoto(0);openLayout();const restored=$('borderInput').value;
      state.photos[0].coatThreshold=60;state.photos[1].coatThreshold=140;const first=JSON.stringify(await preparePrintPages());selectPhoto(1);const second=JSON.stringify(await preparePrintPages());
      StudioExtras.openCoat();const initial=$('coatThreshold').value;$('coatThreshold').value=90;$('coatThreshold').dispatchEvent(new Event('input'));
      const strengths=state.photos.slice(0,2).map(p=>p.coatThreshold);
      state.photos=state.photos.slice(0,3);native.permission=true;await confirmPrint();
      return {changed,restored,same:first===second,initial,strengths,claimsDuplicate:$('sheetBody').innerText.includes('最后一张照片重复')};
    }""")
    assert integration=={'changed':True,'restored':'200','same':True,'initial':'60','strengths':[90,140],'claimsDuplicate':False},integration
    assert not errors,errors;browser.close()
print('PASS: 1–6 ordered photos, all papers/orientations, no duplication or tear-line crossing, isolated hidden layers')
