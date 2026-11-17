/* Blank photo slots and swipes on the printed background, never on a photo. */
window.PreviewActions=(()=>{
 const canvas=$('preview');let gesture=null,suppressUntil=0;
 const enabled=()=>state.mode==='calendar'||!!window.PhotoFlow?.enabled()&&TemplateStudio.selectedId()!=='single';
 const signature=()=>JSON.stringify([state.mode,state.media,state.orientation,state.month,TemplateStudio.selectedId(),state.photos.map(p=>p.src)]);
 const contains=(f,p)=>PhotoWindows.contains(f,p);
 function area(e){
  if((sheetKind&&!$('sheet').classList.contains('desktop-inspector'))||!previewReady()||(window.EffectBrowser?.active()&&EffectBrowser.kind()!=='templates')||window.OriginalPreview?.active())return null;
  const p=CropEditor.toPaper(e),[w,h]=logicalSize();
  if(p.x<0||p.y<0||p.x>w||p.y>h||LayerEditor.hit(p.x,p.y)||photoFrames.some(f=>contains(f,p)))return null;
  if(emptyPhotoFrames.some(f=>contains(f,p)))return 'empty';
  if(window.EffectBrowser?.active())return null;
  return enabled()?'background':null;
 }
 function begin(e,kind){const a=area(e);if(!a)return false;gesture={kind,id:e.pointerId,x:e.clientX,y:e.clientY,area:a,signature:signature(),axis:null,cancelled:false};return true;}
 function move(e){if(!gesture)return;const dx=e.clientX-gesture.x,dy=e.clientY-gesture.y;if(!gesture.axis&&Math.hypot(dx,dy)>8)gesture.axis=Math.abs(dx)>Math.abs(dy)*1.4?'horizontal':'vertical';}
 function step(direction){
  if(state.mode==='calendar'){
   const match=/^(\d{4})-(\d{2})$/.exec(state.month);if(!match)return;
   const total=Number(match[1])*12+Number(match[2])-1+direction,year=Math.floor(total/12),month=total%12+1;
   if(year<1||year>9999)return;state.month=String(year).padStart(4,'0')+'-'+String(month).padStart(2,'0');schedule();return;
  }
  const items=TemplateStudio.browseItems().filter(t=>!t.disabled),index=items.findIndex(t=>t.id===TemplateStudio.selectedId());
  if(index<0||items.length<2)return;const next=items[index+direction];if(next)TemplateStudio.apply(next.id);
 }
 function finish(e){
  const g=gesture;gesture=null;if(!g||g.cancelled||g.signature!==signature())return;
  const dx=e.clientX-g.x,dy=e.clientY-g.y;
  if(g.area==='empty'&&!g.axis&&Math.hypot(dx,dy)<8){
   suppressUntil=performance.now()+500;const room=photoBatchLimit()-state.photos.length;if(room>0)bridge('pick',room);else toast('照片已满，请先移除一张照片');
  }else if(g.area==='background'&&g.axis==='horizontal'&&Math.abs(dx)>=36&&Math.abs(dx)>Math.abs(dy)*1.4){suppressUntil=performance.now()+500;step(dx<0?1:-1);}
 }
 function stop(e){e.stopImmediatePropagation();}
 canvas.addEventListener('touchstart',e=>{
  if(gesture){if(e.touches.length>1)gesture.cancelled=true;stop(e);return;}
  if(e.touches.length===1&&begin(e.touches[0],'touch'))stop(e);
 },{capture:true,passive:true});
 canvas.addEventListener('touchmove',e=>{if(gesture?.kind!=='touch')return;stop(e);if(e.touches.length!==1){gesture.cancelled=true;return;}move(e.touches[0]);if(!gesture.cancelled&&gesture.axis==='horizontal'&&e.cancelable)e.preventDefault();},{capture:true,passive:false});
 canvas.addEventListener('touchend',e=>{if(gesture?.kind!=='touch')return;stop(e);if(!e.touches.length)finish(e.changedTouches[0]);},{capture:true,passive:true});
 canvas.addEventListener('touchcancel',()=>{gesture=null;},{capture:true,passive:true});
 canvas.addEventListener('pointerdown',e=>{if(e.pointerType==='touch'||e.button!==0)return;if(begin(e,'mouse')){stop(e);canvas.setPointerCapture(e.pointerId);}},{capture:true});
 canvas.addEventListener('pointermove',e=>{if(gesture?.kind==='mouse'&&gesture.id===e.pointerId){move(e);stop(e);}},{capture:true});
 canvas.addEventListener('pointerup',e=>{if(gesture?.kind==='mouse'&&gesture.id===e.pointerId){stop(e);finish(e);}},{capture:true});
 canvas.addEventListener('pointercancel',e=>{if(gesture?.kind==='mouse'&&gesture.id===e.pointerId)gesture=null;},{capture:true});
 canvas.addEventListener('lostpointercapture',e=>{if(gesture?.kind==='mouse'&&gesture.id===e.pointerId)gesture=null;},{capture:true});
 canvas.addEventListener('click',e=>{if(performance.now()<suppressUntil){e.preventDefault();stop(e);}},{capture:true});
 document.addEventListener('touchstart',e=>{if(gesture?.kind==='touch'&&e.touches.length>1)gesture.cancelled=true;},{capture:true,passive:true});
 document.addEventListener('touchend',e=>{if(e.target!==canvas&&!e.touches.length&&gesture?.kind==='touch')gesture=null;},{capture:true,passive:true});
 document.addEventListener('touchcancel',()=>{gesture=null;},{capture:true,passive:true});
 window.addEventListener('blur',()=>{gesture=null;});window.addEventListener('resize',()=>{gesture=null;});
 return {enabled,area};
})();
