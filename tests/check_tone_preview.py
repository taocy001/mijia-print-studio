"""Bound editor processing while retaining full-resolution print composition."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={'width':1100,'height':850})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script("window.Studio={state:()=>JSON.stringify({permission:true,device:{connected:true,media:5012,checkedAt:Date.now()},history:[]}),printBatch:()=>{throw Error('Printing forbidden')}}")
    def route(r):
        assert r.request.method=='GET'
        file=root/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('https://studio.test/**',route)
    page.goto('https://studio.test/')
    page.wait_for_load_state('load')
    page.evaluate('LayerEditor.ready')
    result=page.evaluate('''async()=>{
      const check=(ok,message)=>{if(!ok)throw Error(message);};
      const canvas=document.createElement('canvas');canvas.width=2400;canvas.height=1600;
      const ctx=canvas.getContext('2d'),data=ctx.createImageData(2400,1600);
      for(let y=0;y<1600;y++)for(let x=0;x<2400;x++){const i=(y*2400+x)*4;data.data[i]=(x*7+y*3)%256;data.data[i+1]=(x+y*11)%256;data.data[i+2]=(x*3+y*5)%256;data.data[i+3]=255;}
      ctx.putImageData(data,0,0);const source=new Image();source.src=canvas.toDataURL();await source.decode();
      const source2=new Image();source2.src=source.src+'#second';await source2.decode();
      const first=Tone.preview(()=>Tone.image(source,'cool'));
      check(first.width===1280&&first.height===853,'Preview must preserve aspect ratio at 1280px');
      check(Tone.preview(()=>Tone.image(source,'cool'))===first,'Preview must reuse cached pixels');
      for(const key of ['auto','bw','sepia','dusk','film','fresh','warm'])Tone.preview(()=>Tone.image(source,key));
      check(Tone.preview(()=>Tone.image(source,'cool'))===first,'Eight entries must fit and reads promote LRU');
      Tone.preview(()=>Tone.image(source,'auto'));
      Tone.preview(()=>Tone.image(source,'cool'));
      Tone.preview(()=>Tone.image(source2,'cool'));
      check(Tone.preview(()=>Tone.image(source,'cool'))===first,'Recently used preview must survive eviction');
      // bw is now the least recently used of the eight entries.
      const bw=Tone.preview(()=>Tone.image(source,'bw'));
      for(const key of ['sepia','dusk','film','fresh','warm','auto','cool'])Tone.preview(()=>Tone.image(source2,key));
      Tone.preview(()=>Tone.image(source2,'film'),1000);
      check(Tone.preview(()=>Tone.image(source,'bw'))!==bw,'Preview cache must evict at eight entries');
      check(Tone.image(source,'cool').width===2400,'Preview cache must not contaminate full-resolution cache');
      Tone.preview(()=>{
        check(Tone.image(source,'film').width===1280,'Outer preview limit');
        Tone.preview(()=>check(Tone.image(source,'film').width===640,'Nested smaller limit'),640);
        Tone.preview(()=>check(Tone.image(source,'film').width===1280,'Nested scope cannot enlarge limit'),2000);
        check(Tone.image(source,'film').width===1280,'Nested scope restores outer limit');
        try{Tone.preview(()=>{throw Error('synthetic');},320);}catch(e){}
        check(Tone.image(source,'film').width===1280,'Nested failure restores outer limit');
      });
      try{Tone.preview(()=>{throw Error('synthetic');});}catch(e){}
      check(Tone.image(source,'film').width===2400,'Failure restores full-resolution processing');
      check(Tone.preview(()=>Tone.image(source,'film',true)).width===320,'Thumbnails retain independent 320px path');
      check(Tone.preview(()=>Tone.image(source,'none'))===source,'Unfiltered preview reuses original image without processing');
      // Independent implementation of the existing film coefficients, including byte rounding.
      const expected=new Uint8ClampedArray(data.data),clamp=n=>Math.max(0,Math.min(255,Math.floor(n)));
      for(let i=0;i<expected.length;i+=4){const r=clamp(expected[i]*.92+18),g=clamp(expected[i+1]*.92+18),b=clamp(expected[i+2]*.92+18),l=(r*19595+g*38470+b*7471+32768)>>16;expected[i]=clamp(l+.88*(r-l));expected[i+1]=clamp(l+.88*(g-l));expected[i+2]=clamp(l+.88*(b-l));}
      const full=Tone.image(source,'film'),actual=full.getContext('2d').getImageData(0,0,2400,1600).data;
      check(actual.every((v,i)=>v===expected[i]),'Full-resolution pixels differ from original film formula');
      const reference=document.createElement('canvas');reference.width=2400;reference.height=1600;reference.getContext('2d').putImageData(new ImageData(expected,2400,1600),0,0);
      const photo={src:source.src,width:2400,height:1600,filter:'film',fit:'cover',border:0,turn:1,zoom:1.13,x:.21,y:-.17,facePending:false,overlays:[]};
      images.set(photo.src,source);state={...defaults,photos:[photo],active:0,media:5012,orientation:'portrait',mode:'photo',fit:'cover',border:0};peek=false;
      const originalImage=Tone.image,seen=[];
      Tone.image=(...args)=>{const result=originalImage(...args);if(args[0]===source&&args[1]!=='none')seen.push(result.width);return result;};
      try{
        photoGeometry(photo,1216,1824);check(!seen.length,'Geometry must not process tone pixels');
        render();check(seen.length>0&&seen.every(w=>w<=1280),'Editor render must use bounded previews');
        seen.length=0;CropEditor.render();check(seen.length>0&&seen.every(w=>w<=1280),'Crop renderer must use bounded previews');
        seen.length=0;const output=compose(false);check(seen.length>0&&seen.every(w=>w===2400),'Print composition must use full-resolution pixels');
        Tone.image=(img,key,small)=>img===source&&key==='film'&&!small?reference:originalImage(img,key,small);
        const baseline=compose(false);
        check(output.toDataURL()===baseline.toDataURL(),'Printed crop/rotation/scale must match full-resolution reference');
        check(output.width===1216&&output.height===1824,'Paper output size changed');
        Tone.image=(...args)=>{const result=originalImage(...args);if(args[0]===source&&args[1]!=='none')seen.push(result.width);return result;};seen.length=0;
        const pages=await preparePrintPages();check(pages.length===1&&seen.length>0&&seen.every(w=>w===2400),'Print preparation must remain full resolution');
        const jpeg=new Image();jpeg.src='data:image/jpeg;base64,'+pages[0].base64;await jpeg.decode();check(jpeg.naturalWidth===1216&&jpeg.naturalHeight===1824,'Prepared JPEG paper dimensions changed');
      }finally{Tone.image=originalImage;}
      return {source:[source.naturalWidth,source.naturalHeight],preview:[first.width,first.height],output:[1216,1824]};
    }''')
    assert not errors,errors
    browser.close()
print('PASS: bounded preview/LRU, nested and failed scopes, geometry-only path, full-resolution formula and print composition',result)
