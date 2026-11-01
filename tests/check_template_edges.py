"""Selective scene details preserve crop geometry, subjects and structured frames."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch();page=browser.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.add_init_script("window.Studio={state:()=>'{\"device\":{},\"history\":[]}',printBatch:()=>{throw Error('No physical printing')}}")
    def route(r):
        assert r.request.method=='GET'
        file=root/'assets'/(urlparse(r.request.url).path.lstrip('/') or 'index.html')
        if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='Missing')
    page.route('https://studio.test/**',route);page.goto('https://studio.test/');page.wait_for_load_state('load');page.evaluate('LayerEditor.ready')
    result=page.evaluate('''async()=>{
      const p={src:'/sample.svg',fit:'cover',filter:'none',zoom:1,x:0,y:0,turn:0,overlays:[]};await loadPhoto(p);
      const expected=['botanical','petal','orchard','tide','ripple','kids-dino','kids-ocean','kids-picnic','kids-ducks','kids-art'];
      if(expected.length!==TemplateEdges.styles.size||!expected.every(t=>TemplateEdges.has(t)))throw Error('Scope changed');
      let rendered=0;
      for(const template of TEMPLATE_CATALOG)for(const [w,h] of [[608,912],[912,608],[520,520],[608,456]]){
        const e=OriginalTemplates.variant(template,w,h),render=()=>{const c=document.createElement('canvas');c.width=w;c.height=h;OriginalTemplates.paint(c.getContext('2d'),p,0,0,w,h,e);return c;};
        const paint=TemplateEdges.paint;let original;
        try{TemplateEdges.paint=()=>{};original=render();}finally{TemplateEdges.paint=paint;}
        photoFrames=[];collectingPhotoFrames=true;let c;try{c=render();}finally{collectingPhotoFrames=false;}
        const frame=photoFrames[0];if(photoFrames.length!==1||frame.x!==e.margin.left||frame.y!==e.margin.top||frame.w!==e.crop.width||frame.h!==e.crop.height)throw Error(template.style+' crop moved');
        const a=c.getContext('2d').getImageData(0,0,w,h).data,b=original.getContext('2d').getImageData(0,0,w,h).data,u=Math.min(w,h),l=e.margin.left,t=e.margin.top,r=l+e.crop.width,bottom=t+e.crop.height,d=u*.04+1;let changed=0,inPhoto=0;
        for(let y=0;y<h;y++)for(let x=0;x<w;x++){
          const i=(y*w+x)*4;if(a[i]===b[i]&&a[i+1]===b[i+1]&&a[i+2]===b[i+2]&&a[i+3]===b[i+3])continue;
          changed++;if(!TemplateEdges.has(template.style))throw Error(template.style+' should remain unchanged');
          if(x>l+d&&x<r-d&&y>t+d&&y<bottom-d)throw Error(template.style+' changed subject');
          if(y>bottom+u*.095||y<t-u*.025-1||x<l-u*.025-1||x>r+u*.025+1)throw Error(template.style+' changed title or scene');
          if(x>=l&&x<r&&y>=t&&y<bottom)inPhoto++;
        }
        if(TemplateEdges.has(template.style)&&(!changed||!inPhoto))throw Error(template.style+' did not cross the edge');
        if(c.toDataURL()!==render().toDataURL())throw Error(template.style+' unstable artwork');
        rendered++;
      }
      const c=document.createElement('canvas');c.width=1216;c.height=1824;const ctx=c.getContext('2d');ctx.fillStyle='#d43c52';ctx.fillRect(0,0,1216,912);const before=ctx.getImageData(0,0,1216,912).data;
      const selected=TEMPLATE_CATALOG.find(t=>t.style==='tide');OriginalTemplates.paint(ctx,p,0,912,1216,912,OriginalTemplates.variant(selected,1216,912));
      const after=ctx.getImageData(0,0,1216,912).data;if(before.some((v,i)=>v!==after[i]))throw Error('Splice leaked');
      return rendered;
    }''')
    assert result==140,result
    assert not errors,errors
    browser.close()
print('PASS: 10 selected scenes, 25 untouched templates, 140 renders, protected centers/titles, stable crop coordinates and isolated splice')
