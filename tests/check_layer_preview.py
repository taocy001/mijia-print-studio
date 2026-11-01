"""Synthetic editor mask caching and byte-identical full resolution print regression."""
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
 browser=pw.chromium.launch(); outputs=[]
 for old in [True,False]:
  page=browser.new_page()
  page.add_init_script("""window.Studio={state:()=>'{"device":{},"history":[]}',landscape:()=>false};
   const decode=HTMLImageElement.prototype.decode;window.releaseEmoji=[];
   HTMLImageElement.prototype.decode=function(){return decode.call(this).then(value=>this.src.includes('/emoji/')?new Promise(resolve=>releaseEmoji.push(()=>resolve(value))):value);};
   const load=document.fonts.load.bind(document.fonts);window.releaseFonts=[];
   document.fonts.load=(...args)=>load(...args).then(result=>new Promise(resolve=>releaseFonts.push(()=>resolve(result))));""")
  def route(r):
   assert r.request.method=='GET'
   path=urlparse(r.request.url).path
   file=ROOT/'assets'/(path.lstrip('/') or 'index.html')
   if file.is_file():r.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
   else:r.fulfill(status=404,body='Missing')
  page.route('**/*',route);page.goto('https://studio.test/');page.wait_for_function('window.LayerEditor&&releaseFonts.length===2')
  if old:
   # Reference keeps the original full-size mask raster/threshold geometry independent
   # of the production mask branch; ordinary text/emoji drawing is shared.
   page.evaluate("""()=>{const paint=LayerEditor.paint;
    LayerEditor.paint=function(ctx,w,h,objects,mode){
     if(mode!=='mask')return paint(ctx,w,h,objects,mode);
     const hidden=objects.filter(o=>o.hidden&&o.kind!=='qr');if(!hidden.length)return;
     const mask=document.createElement('canvas');mask.width=w;mask.height=h;
     const mc=mask.getContext('2d');
     paint(mc,w,h,hidden.map(o=>({...o,hidden:false,color:'#fff',stroke:'',bubble:''})),'photo');
     const pixels=mc.getImageData(0,0,w,h);let bright=0;
     const light=i=>.299*pixels.data[i]+.587*pixels.data[i+1]+.114*pixels.data[i+2];
     for(let i=0;i<pixels.data.length;i+=4)if(pixels.data[i+3]&&light(i)>=40)bright++;
     for(let i=0;i<pixels.data.length;i+=4){
      if(bright&&light(i)<40)pixels.data[i+3]=0;
      pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=255;
     }
     mc.putImageData(pixels,0,0);ctx.save();ctx.globalAlpha=1;ctx.drawImage(mask,0,0);ctx.restore();
    };
   }""")
  page.evaluate("""()=>{window.objects=[{id:'a',kind:'text',text:'快乐 Hello',font:'happy',sizePct:8,fx:.4,fy:.3,angle:22,hidden:true},{id:'b',kind:'emoji',text:'😊',sizePct:16,fx:.6,fy:.6,hidden:true}];
   window.draw=(mode,w=1216,h=1824,items=objects)=>{const c=document.createElement('canvas');c.width=w;c.height=h;LayerEditor.paint(c.getContext('2d'),w,h,items,mode);return c;};
   window.reads=0;const get=CanvasRenderingContext2D.prototype.getImageData;CanvasRenderingContext2D.prototype.getImageData=function(...a){reads++;window.lastRead=a;return get.apply(this,a);};draw('editor');}""")
  if not old:
   result=page.evaluate("""()=>{reads=0;draw('editor');const hit=reads;objects.push({kind:'text',text:'visible',fx:.5,fy:.4});draw('editor');const visible=reads;objects[0].fx=.44;draw('editor');const changed=reads;draw('editor',1824,1216);const paper=reads;draw('editor',1216,1824,[{...objects[0],text:'another photo'}]);const photo=reads;return {hit,visible,changed,paper,photo,lastRead};}""")
   assert result['hit']==0 and result['visible']==0 and result['changed']==1 and result['paper']==2 and result['photo']==3,result
   assert max(result['lastRead'][2:])==1024,result
   page.evaluate("objects[0].fx=.4;objects.length=2;draw('editor');window.beforeReady=reads")
  page.evaluate('releaseFonts.forEach(resolve=>resolve())');page.wait_for_timeout(20)
  if not old:
   assert page.evaluate("()=>{draw('editor');return reads>beforeReady}")
  page.evaluate('window.beforeEmoji=reads;releaseEmoji.forEach(resolve=>resolve())');page.evaluate('LayerEditor.ready')
  if not old:
   assert page.evaluate("()=>{draw('editor');return reads>beforeEmoji}")
  outputs.append(page.evaluate("[draw('mask').toDataURL(),draw('mask',1824,1216).toDataURL(),draw('mask',608,912).toDataURL(),draw('mask',607.7,911.6).toDataURL()]"))
  page.close()
 assert outputs[0]==outputs[1], 'Print masks differ from original pixels'
 browser.close()
print('PASS: editor cached/rebuilt correctly, 1024 limit, visible changes reuse, paper/photo separation, font and emoji readiness invalidate; four full print masks (including fractional dimensions) identical to original')
