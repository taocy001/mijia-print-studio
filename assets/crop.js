/* Original photo and printable composition. */
window.CropEditor=(()=>{
 const canvas=$('preview');let view=null,frame=null,start=null,previous=null,axis=null,scope='';
 const edges=['top','right','bottom','left'].map(side=>{const edge=document.createElement('div');edge.className='crop-frame-edge';edge.dataset.cropEdge=side;edge.hidden=true;edge.setAttribute('aria-hidden','true');$('paperStage').appendChild(edge);return edge;});
 let frameDrag=null,target=null,mouse=null,gestureScale=null,displayLock=null;
 const browsing=()=>!!window.EffectBrowser?.active();
 const workFamily=()=>['photo','template'].includes(state.mode)?'photo':state.mode;
 function lockDisplay(){resetGesture();if(view)displayLock={tx:view.tx,ty:view.ty,cw:canvas.width,ch:canvas.height,w:view.paper.w,h:view.paper.h,photo:active(),family:workFamily(),transform:JSON.stringify([active()?.turn,active()?.fit,active()?.border,active()?.zoom,active()?.x,active()?.y])};}
 function unlockDisplay(){displayLock=null;}
 function resetGesture(){window.EditHistory?.commit();start=previous=null;axis=null;frameDrag=null;target=mouse=gestureScale=null;}
 function placeEdges(enabled){
  for(const edge of edges)edge.hidden=!enabled;
  if(!enabled||!view)return;
  const r=canvas.getBoundingClientRect(),parent=$('paperStage').getBoundingClientRect(),sx=r.width/canvas.width,sy=r.height/canvas.height;
  const x=r.left-parent.left+view.tx*sx,y=r.top-parent.top+view.ty*sy,w=view.paper.w*sx,h=view.paper.h*sy,hit=32;
  const boxes=[[x,y-hit/2,w,hit],[x+w-hit/2,y,hit,h],[x,y+h-hit/2,w,hit],[x-hit/2,y,hit,h]];
  edges.forEach((edge,i)=>{const [left,top,width,height]=boxes[i];Object.assign(edge.style,{left:left+'px',top:top+'px',width:width+'px',height:height+'px'});});
 }
 for(const edge of edges){
  edge.addEventListener('pointerdown',e=>{if(browsing()||!frame||!view||peek||e.button!==0)return;e.preventDefault();e.stopPropagation();
   const rect=canvas.getBoundingClientRect(),g=photoGeometry(frame.p,frame.w,frame.h,frame.fit);
   window.EditHistory?.begin('gesture',frame.p);frameDrag={id:e.pointerId,p:frame.p,x:e.clientX,y:e.clientY,px:frame.p.x||0,py:frame.p.y||0,sx:canvas.width/rect.width,sy:canvas.height/rect.height,ex:g.ex,ey:g.ey};edge.setPointerCapture(e.pointerId);
  });
  edge.addEventListener('pointermove',e=>{const d=frameDrag;if(browsing()||!d||d.id!==e.pointerId||peek)return;e.preventDefault();d.p.facePending=false;
   if(d.ex)d.p.x=Math.max(-1,Math.min(1,d.px-(e.clientX-d.x)*d.sx/d.ex));
   if(d.ey)d.p.y=Math.max(-1,Math.min(1,d.py-(e.clientY-d.y)*d.sy/d.ey));schedule();
  });
  for(const name of ['pointerup','pointercancel','lostpointercapture'])edge.addEventListener(name,()=>{window.EditHistory?.commit();frameDrag=null;});
 }

 function render(){return Tone.preview(renderFrame);}
 function renderFrame(){
  if(!ready()||!printPreview){view=null;canvas.classList.remove('photo-draggable');placeEdges(false);return;}
  const next=[state.mode,state.media,state.orientation,state.active,active()?.src].join('|');if(next!==scope){scope=next;resetGesture();}
  frame=photoFrames.find(f=>f.p===active())||photoFrames[0]||null;const dragGeometry=frame&&photoGeometry(frame.p,frame.w,frame.h,frame.fit);canvas.classList.toggle('photo-draggable',!!dragGeometry&&!peek&&(dragGeometry.ex>.5||dragGeometry.ey>.5));canvas.classList.toggle('photo-zoomed',!!frame&&(frame.p.zoom||1)>1.001);
  const [w,h]=logicalSize(),stage=$('paperStage');if(displayLock&&(displayLock.family!==workFamily()||displayLock.photo!==active()||displayLock.w!==w||displayLock.h!==h||(window.EffectBrowser?.kind()!=='layout'&&displayLock.transform!==JSON.stringify([active()?.turn,active()?.fit,active()?.border,active()?.zoom,active()?.x,active()?.y]))))displayLock=null;
  if(displayLock&&window.EffectBrowser?.kind()==='layout')displayLock.transform=JSON.stringify([active()?.turn,active()?.fit,active()?.border,active()?.zoom,active()?.x,active()?.y]);
  let width,pad,tx,ty,cw,ch;
  const complete=state.mode==='photo'&&[5009,5012].includes(state.media)&&frame;
  if(complete){
   // Fit the original at 1x; zoom changes the photograph, not the paper's display scale.
   const g=photoGeometry({...frame.p,zoom:1},frame.w,frame.h,frame.fit);
   const x=frame.x+(frame.w-g.dw)/2+g.dx,y=frame.y+(frame.h-g.dh)/2+g.dy;
   tx=-Math.min(0,x);ty=-Math.min(0,y);cw=Math.ceil(Math.max(w,x+g.dw)+tx-1e-7);ch=Math.ceil(Math.max(h,y+g.dh)+ty-1e-7);
   if((document.body.classList.contains('landscape')||(!!window.BrowserTransport&&innerWidth>=1000&&matchMedia('(pointer:fine)').matches))){const r=$('board').getBoundingClientRect();width=Math.min(r.width/cw,r.height/ch)*cw;stage.style.width=width+'px';}
   else{stage.style.removeProperty('width');width=stage.clientWidth||411;}
  }else{
   if((document.body.classList.contains('landscape')||(!!window.BrowserTransport&&innerWidth>=1000&&matchMedia('(pointer:fine)').matches))){
    const rect=$('board').getBoundingClientRect(),scale=Math.max(.01,Math.min((rect.width-12)/w,(rect.height-12)/h));
    pad=Math.max(1,Math.round(6/scale));width=(w+pad*2)*scale;stage.style.width=width+'px';
   }else{stage.style.removeProperty('width');width=stage.clientWidth||411;pad=Math.round(w*12/Math.max(1,width-24));}
   tx=ty=pad;cw=w+pad*2;ch=h+pad*2;
  }
  if(displayLock){({tx,ty,cw,ch}=displayLock);if(document.body.classList.contains('landscape')||document.body.classList.contains('desktop-editor')){const rect=$('board').getBoundingClientRect();width=Math.min(rect.width/cw,rect.height/ch)*cw;stage.style.width=width+'px';}else{stage.style.removeProperty('width');width=stage.clientWidth||411;}}
  view={tx,ty,scale:1,paper:{w,h},frame:frame?{x:frame.x,y:frame.y,w:frame.w,h:frame.h}:null};
  canvas.width=cw;canvas.height=ch;const ctx=canvas.getContext('2d');ctx.fillStyle='#282a2e';ctx.fillRect(0,0,cw,ch);ctx.save();ctx.translate(tx,ty);
  if(frame){const {p,x,y,w:fw,h:fh,fit}=frame;paintPhotoImage(ctx,photoGeometry(p,fw,fh,fit),x,y,fw,fh);}
  ctx.fillStyle='#0005';ctx.fillRect(-tx,-ty,canvas.width,canvas.height);
  ctx.drawImage(printPreview,0,0);
  const px=canvas.width/width;ctx.lineWidth=3*px;ctx.strokeStyle='#203d3377';ctx.strokeRect(0,0,w,h);ctx.lineWidth=px;ctx.setLineDash([5*px,4*px]);ctx.strokeStyle='#ffffff';ctx.strokeRect(0,0,w,h);ctx.setLineDash([]);
  if(frame&&(frame.x||frame.y||frame.w!==w||frame.h!==h)){ctx.lineWidth=px;ctx.strokeStyle='#d99832';ctx.strokeRect(frame.x,frame.y,frame.w,frame.h);}
  if(state.media===5014){ctx.beginPath();ctx.setLineDash([7*px,5*px]);ctx.strokeStyle='#d99832';ctx.moveTo(0,h/2);ctx.lineTo(w,h/2);ctx.stroke();}
  ctx.restore();const movable=complete&&!peek&&photoGeometry(frame.p,frame.w,frame.h,frame.fit);placeEdges(!browsing()&&!!movable&&(movable.ex>.5||movable.ey>.5));$('spliceGuide').hidden=true;$('gestureHint').textContent=frame?(canvas.classList.contains('photo-draggable')?'拖动调整打印区域 · 双指缩放':'上下滑动浏览 · 双指缩放'):'上下滑动浏览';
 }
 function toPaper(e){const r=canvas.getBoundingClientRect();return{x:(e.clientX-r.left)*canvas.width/r.width-(view?.tx||0),y:(e.clientY-r.top)*canvas.height/r.height-(view?.ty||0)};}
 function beginGesture(){const r=canvas.getBoundingClientRect();gestureScale={x:canvas.width/r.width,y:canvas.height/r.height};}
 function gesturePoint(e){return {x:e.clientX*gestureScale.x,y:e.clientY*gestureScale.y};}
 function geometry(touches){const p=Array.from(touches,t=>gesturePoint(t));return !p.length?null:p.length===1?{...p[0],d:0,n:1}:{x:(p[0].x+p[1].x)/2,y:(p[0].y+p[1].y)/2,d:Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y),n:2};}
 function choose(p){return photoFrames.find(f=>p.x>=f.x&&p.x<=f.x+f.w&&p.y>=f.y&&p.y<=f.y+f.h)||frame;}
 function move(now,old,multi){if(browsing())return;displayLock=null;if(!target||peek)return;window.EditHistory?.begin('gesture',target.p);target.p.facePending=false;const {p,w,h,fit}=target,g=photoGeometry(p,w,h,fit),direction=state.mode==='photo'&&[5009,5012].includes(state.media)?-1:1;if(g.ex)p.x=Math.max(-1,Math.min(1,(p.x||0)+direction*(now.x-old.x)/g.ex));if(multi&&g.ey)p.y=Math.max(-1,Math.min(1,(p.y||0)+direction*(now.y-old.y)/g.ey));if(multi&&old.d&&now.d)p.zoom=Math.max(1,Math.min(4,(p.zoom||1)*now.d/old.d));schedule();}
 canvas.addEventListener('touchstart',e=>{if(browsing())return;if(!view||peek)return;beginGesture();previous=geometry(e.touches);if(e.touches.length===1){start=previous;target=choose(toPaper(e.touches[0]));axis=target&&canvas.classList.contains('photo-draggable')?'photo':null;if(axis==='photo')e.preventDefault();}else{e.preventDefault();axis='multi';target=target||frame;}},{passive:false});
 canvas.addEventListener('touchmove',e=>{if(browsing())return;if(!previous||!view)return;const now=geometry(e.touches);if(now.n!==previous.n){previous=start=now;return;}if(now.n>1){e.preventDefault();move(now,previous,true);previous=now;axis='multi';return;}
  // Native vertical scrolling wins. Horizontal drags are edited directly, without a mode switch.
  if(!axis&&start){const dx=now.x-start.x,dy=now.y-start.y,threshold=8*canvas.width/canvas.clientWidth;if(Math.hypot(dx,dy)>threshold)axis=Math.abs(dx)>Math.abs(dy)*1.2?'horizontal':'scroll';}
  if(axis==='horizontal'||axis==='photo'){e.preventDefault();move(now,previous,axis==='photo');}previous=now;
 },{passive:false});
 canvas.addEventListener('touchend',e=>{if(!gestureScale){resetGesture();return;}previous=geometry(e.touches);if(!previous)resetGesture();else{start=previous;axis=target&&canvas.classList.contains('photo-draggable')?'photo':null;}},{passive:true});
 canvas.addEventListener('touchcancel',resetGesture,{passive:true});
 // Mouse drag and wheel keep the desktop-style direct editing path.
 canvas.addEventListener('pointerdown',e=>{if(browsing())return;if(e.pointerType==='mouse'&&e.button===0){beginGesture();mouse=gesturePoint(e);target=choose(toPaper(e));canvas.setPointerCapture(e.pointerId);}});
 canvas.addEventListener('pointermove',e=>{if(browsing())return;if(mouse){const p=gesturePoint(e);move(p,mouse,true);mouse=p;}});
 for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,e=>{if(e.pointerType!=='touch')window.EditHistory?.commit();mouse=null;});
 canvas.addEventListener('wheel',e=>{if(browsing()){if(e.ctrlKey)e.preventDefault();return;}displayLock=null;if(!e.ctrlKey||!frame)return;e.preventDefault();window.EditHistory?.begin('wheel',frame.p);frame.p.facePending=false;frame.p.zoom=Math.max(1,Math.min(4,(frame.p.zoom||1)*(e.deltaY>0?.9:1.1)));window.EditHistory?.defer();schedule();},{passive:false});
 window.addEventListener('resize',()=>{resetGesture();render();LayerEditor.refresh();});
 schedule();return {render,geometry:()=>view,toPaper,lockDisplay,unlockDisplay,resetGesture};
})();
