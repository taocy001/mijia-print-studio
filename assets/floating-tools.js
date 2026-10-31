// Keep viewing controls independent of the photograph and its print coordinates.
(()=>{
 const bar=document.querySelector('.photo-tools'),board=$('board'),key='liuying-toolbar-position';
 let position=null,drag=null,suppress=false;
 try{const p=JSON.parse(localStorage.getItem(key));if(p&&Number.isFinite(p.x)&&Number.isFinite(p.y))position=p;}catch{}
 function bounds(){
  const top=document.querySelector('.topbar').getBoundingClientRect(),dock=document.querySelector('.dock').getBoundingClientRect(),desktop=document.body.classList.contains('desktop-editor'),landscape=document.body.classList.contains('landscape')&&!desktop;
  const left=landscape?top.right+8:8,right=landscape||desktop?dock.left-8:innerWidth-8,upper=landscape?8:top.bottom+8,bottom=!landscape&&!desktop?Math.min(innerHeight,dock.top)-8:innerHeight-8;
  return {left,top:upper,maxX:Math.max(left,right-bar.offsetWidth),maxY:Math.max(upper,bottom-bar.offsetHeight)};
 }
 function place(x,y){const b=bounds();x=Math.max(b.left,Math.min(x,b.maxX));y=Math.max(b.top,Math.min(y,b.maxY));Object.assign(bar.style,{left:x+'px',top:y+'px',bottom:'auto',transform:'none'});return{x,y,...b};}
 function fit(){if(!bar.offsetWidth)return;const b=bounds(),r=board.getBoundingClientRect();if(position)place(b.left+position.x*(b.maxX-b.left),b.top+position.y*(b.maxY-b.top));else place(r.left+(r.width-bar.offsetWidth)/2,r.bottom-bar.offsetHeight-16);}
 bar.addEventListener('pointerdown',e=>{
  if(!e.isPrimary||e.button!==0)return;
  suppress=false;const r=bar.getBoundingClientRect();
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,left:r.left,top:r.top,moved:false};
 },true);
 bar.addEventListener('pointermove',e=>{
  if(!drag||e.pointerId!==drag.id)return;
  const dx=e.clientX-drag.x,dy=e.clientY-drag.y;
  if(!drag.moved&&Math.hypot(dx,dy)<8)return;
  drag.moved=true;suppress=true;bar.setPointerCapture(e.pointerId);e.preventDefault();
  peek=false;schedule();bar.classList.add('dragging');
  const p=place(drag.left+dx,drag.top+dy);
  position={x:(p.x-p.left)/Math.max(1,p.maxX-p.left),y:(p.y-p.top)/Math.max(1,p.maxY-p.top)};
 });
 function end(e){if(!drag||e.pointerId!==drag.id)return;if(drag.moved){try{localStorage.setItem(key,JSON.stringify(position));}catch{}}drag=null;bar.classList.remove('dragging');peek=false;schedule();}
 bar.addEventListener('pointerup',end);bar.addEventListener('pointercancel',end);bar.addEventListener('lostpointercapture',e=>{if(e.target===bar&&!bar.hasPointerCapture(e.pointerId))end(e);});
 bar.addEventListener('click',e=>{if(suppress){e.preventDefault();e.stopImmediatePropagation();suppress=false;}},true);
 window.addEventListener('resize',fit);document.querySelector('.workspace').addEventListener('scroll',()=>{if(!position)fit();});
 new ResizeObserver(fit).observe(document.querySelector('.app'));new ResizeObserver(fit).observe(board);new ResizeObserver(fit).observe(bar);requestAnimationFrame(fit);
})();
