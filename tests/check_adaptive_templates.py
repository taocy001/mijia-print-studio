"""Original template geometry and color adaptation, synthetic photos only."""
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as runtime:
    browser=runtime.chromium.launch();page=browser.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_init_script("window.Studio={state:()=>'{\"device\":{},\"history\":[]}',printBatch:()=>{throw Error('No printing')}}")
    def route(r):
        assert r.request.method=='GET'
        name=urlparse(r.request.url).path;file=ROOT/'assets'/(name.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.OriginalTemplates&&window.StudioExtras');page.evaluate('LayerEditor.ready')
    result=page.evaluate('''async()=>{
      const photo=async(color)=>{const c=document.createElement('canvas');c.width=600;c.height=900;const x=c.getContext('2d');x.fillStyle=color;x.fillRect(0,0,600,900);const p={src:c.toDataURL(),filter:'none',zoom:1,x:0,y:0,turn:0,fit:'cover',border:0,overlays:[]};await loadPhoto(p);return p;};
      const red=await photo('#d22d3c'),blue=await photo('#2864c8');state.photos=[red,blue];state.active=0;
      const render=(p,t,w,h,baseline='alphabetic')=>{const e=OriginalTemplates.variant(t,w,h),c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').textBaseline=baseline;OriginalTemplates.paint(c.getContext('2d'),p,0,0,w,h,e);return {e,c};};
      const edge=p=>Array.from(render(p,TEMPLATE_CATALOG.find(t=>t.id==='studio-air'),1040,1040).c.getContext('2d').getImageData(1,1,1,1).data).slice(0,3);
      const mixCanvas=document.createElement('canvas');mixCanvas.width=600;mixCanvas.height=900;const mx=mixCanvas.getContext('2d');
      for(const [x,w,color] of [[0,240,'#d22d3c'],[240,220,'#dddddd'],[460,140,'#2864c8']]){mx.fillStyle=color;mx.fillRect(x,0,w,900);}
      const mixed={...red,src:mixCanvas.toDataURL()};await loadPhoto(mixed);const mixedEdge=edge(mixed);
      const redEdge=edge(red),blueEdge=edge(blue);red.filter='bw';const bw=edge(red);red.filter='sepia';const sepia=edge(red);red.filter='none';
      const restored=edge(red);red.zoom=2;red.x=.7;red.y=-.5;const moved=edge(red);red.zoom=1;red.x=red.y=0;
      if(TEMPLATE_CATALOG.length!==30)throw Error('Expected 30 original templates');
      if(TEMPLATE_CATALOG.slice(0,10).map(t=>t.style).join()!==KidsTemplates.designs.map(d=>d[0]).join())throw Error('Children templates must come first');
      const failures=[],tiles=[];
      for(const template of TEMPLATE_CATALOG){
        const a=OriginalTemplates.variant(template,1216,1824),b=OriginalTemplates.variant(template,1824,1216);
        if(a.margin.left!==b.margin.left||a.margin.top!==b.margin.top||a.height-a.margin.top-a.crop.height!==b.height-b.margin.top-b.crop.height)failures.push([template.id,'orientation margins']);
        for(const [w,h] of [[1216,1824],[1824,1216],[1040,1040],[1216,912]]){
          const {e,c}=render(blue,template,w,h),{left,top}=e.margin,{width:pw,height:ph}=e.crop;
          if(left<0||top<0||left+pw>w||top+ph>h||pw*ph<w*h*.60)failures.push([template.id,w,h,'bounds']);
          if(render(blue,template,w,h,'middle').c.toDataURL()!==c.toDataURL())failures.push([template.id,w,h,'inherited text baseline']);
          const ctx=c.getContext('2d');
          for(const fx of [.01,.05,.5,.95,.99])for(const fy of [.01,.05,.5,.95,.99]){
            const pixel=ctx.getImageData(Math.floor(left+pw*fx),Math.floor(top+ph*fy),1,1).data;
            if(pixel[0]!==40||pixel[1]!==100||pixel[2]!==200)failures.push([template.id,w,h,fx,fy,Array.from(pixel)]);
          }
          const thumb=document.createElement('canvas');thumb.width=Math.round(w*200/h);thumb.height=200;thumb.getContext('2d').drawImage(c,0,0,thumb.width,thumb.height);
          tiles.push(`<figure><img src="${thumb.toDataURL()}"><figcaption>${template.names.zh} · ${w}×${h}</figcaption></figure>`);
        }
      }
      return {mixedEdge,redEdge,blueEdge,bw,sepia,restored,moved,failures,atlas:tiles.join('')};
    }''')
    assert not result['failures'],result['failures'][:10]
    assert result['mixedEdge'][0]-result['mixedEdge'][2]>15,result['mixedEdge']
    assert result['redEdge'][0]>result['redEdge'][2]
    assert result['blueEdge'][2]>result['blueEdge'][0]
    assert len(set(result['bw']))==1,result['bw']
    assert result['sepia']!=result['redEdge']
    assert result['restored']==result['redEdge']==result['moved']
    atlas=browser.new_page(viewport={'width':1500,'height':1000})
    atlas.set_content('<style>body{background:#e9e8e4;font:12px sans-serif}main{display:grid;grid-template-columns:repeat(8,1fr);gap:8px}figure{margin:0;background:white;padding:8px;text-align:center}img{height:150px;max-width:100%;object-fit:contain}</style><main>'+result['atlas']+'</main>')
    atlas.screenshot(path='/tmp/adaptive-template-atlas.png',full_page=True)
    assert not errors,errors;browser.close()
print('PASS: 30 templates × 4 canvases, photo pixels protected, filter-aware palette, stable crop colors')
