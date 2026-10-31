// Keep viewing controls independent of the photograph and its print coordinates.
(()=>{
 const bar=document.querySelector('.photo-tools'),board=$('board'),key='liuying-toolbar-position';
 let position=null,drag=null,suppress=false;
 try{const p=JSON.parse(localStorage.getItem(key));if(p&&Number.isFinite(p.x)&&Number.isFinite(p.y))position=p;}catch{}
 const clamp=(v,max)=>Math.max(8,Math.min(v,Math.max(8,max)));
 function place(x,y){
  const maxX=board.clientWidth-bar.offsetWidth-8,maxY=board.clientHeight-bar.offsetHeight-8;
  x=clamp(x,maxX);y=clamp(y,maxY);
  Object.assign(bar.style,{left:x+'px',top:y+'px',bottom:'auto',transform:'none'});
  return{x,y,maxX,maxY};
 }
 function fit(){if(!position||!bar.offsetWidth)return;place(8+position.x*Math.max(0,board.clientWidth-bar.offsetWidth-16),8+position.y*Math.max(0,board.clientHeight-bar.offsetHeight-16));}
 bar.addEventListener('pointerdown',e=>{
  if(!e.isPrimary||e.button!==0)return;
  suppress=false;const r=bar.getBoundingClientRect(),b=board.getBoundingClientRect();
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,left:r.left-b.left,top:r.top-b.top,moved:false};
 },true);
 bar.addEventListener('pointermove',e=>{
  if(!drag||e.pointerId!==drag.id)return;
  const dx=e.clientX-drag.x,dy=e.clientY-drag.y;
  if(!drag.moved&&Math.hypot(dx,dy)<8)return;
  drag.moved=true;suppress=true;bar.setPointerCapture(e.pointerId);e.preventDefault();
  peek=false;schedule();bar.classList.add('dragging');
  const p=place(drag.left+dx,drag.top+dy);
  position={x:(p.x-8)/Math.max(1,p.maxX-8),y:(p.y-8)/Math.max(1,p.maxY-8)};
 });
 function end(e){if(!drag||e.pointerId!==drag.id)return;if(drag.moved){try{localStorage.setItem(key,JSON.stringify(position));}catch{}}drag=null;bar.classList.remove('dragging');peek=false;schedule();}
 bar.addEventListener('pointerup',end);bar.addEventListener('pointercancel',end);bar.addEventListener('lostpointercapture',e=>{if(e.target===bar&&!bar.hasPointerCapture(e.pointerId))end(e);});
 bar.addEventListener('click',e=>{if(suppress){e.preventDefault();e.stopImmediatePropagation();suppress=false;}},true);
 new ResizeObserver(fit).observe(board);new ResizeObserver(fit).observe(bar);
})();
