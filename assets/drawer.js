/* Shared snap drawer: header drags resize, content scrolls independently. */
window.Drawer=(()=>{
 const sheet=$('sheet'),body=$('sheetBody'),handle=$('sheetHandle'),header=sheet.querySelector('header');
 let drag=null,current=0,level='half',ignoreClick=false,contentStart=null,glide=0;
 const bounds=()=>{const viewport=innerHeight;return {half:Math.min(viewport-16,Math.max(220,viewport*.46)),full:Math.max(160,viewport-16)};};
 function apply(h,animate=false){const {full}=bounds();current=Math.max(92,Math.min(full,h));sheet.classList.toggle('drawer-animate',animate);sheet.style.setProperty('--drawer-height',current+'px');handle.setAttribute('aria-expanded',String(current>bounds().half+30));}
 function open(kind,same){drag=null;contentStart=null;sheet.classList.remove('drawer-dragging');if(!same){level=kind==='confirm'?'full':'half';}apply(bounds()[level],false);}
 function reset(){cancelAnimationFrame(glide);drag=null;contentStart=null;sheet.classList.remove('drawer-animate','drawer-dragging');sheet.style.removeProperty('--drawer-height');}
 function begin(y){drag={startY:y,lastY:y,startHeight:current||sheet.getBoundingClientRect().height,lastAt:performance.now(),velocity:0,moved:false};sheet.classList.add('drawer-dragging');sheet.classList.remove('drawer-animate');}
 function move(y){if(!drag)return;const now=performance.now(),dt=Math.max(1,now-drag.lastAt);drag.velocity=(y-drag.lastY)/dt;drag.lastAt=now;drag.lastY=y;drag.moved ||=Math.abs(y-drag.startY)>5;apply(drag.startHeight+drag.startY-y);}
 function end(cancel=false){if(!drag)return;const d=drag;drag=null;sheet.classList.remove('drawer-dragging');ignoreClick=d.moved;setTimeout(()=>ignoreClick=false,0);const {half,full}=bounds(),delta=d.lastY-d.startY;
  if(cancel){apply(d.startHeight,true);return;}
  if(!d.moved)return;
  if(current<half*.62||(d.startHeight<=half+20&&delta>70&&d.velocity>.65)){closeSheet();return;}
  if(delta>48)level='half';else if(delta< -40)level='full';else level=current>(half+full)/2?'full':'half';apply(bounds()[level],true);
 }
 for(const el of [handle,header]){
  el.addEventListener('pointerdown',e=>{if(document.body.classList.contains('landscape')||e.target.closest('#closeSheet')||e.button!==0)return;e.preventDefault();begin(e.clientY);el.setPointerCapture(e.pointerId);});
  el.addEventListener('pointermove',e=>{if(drag){e.preventDefault();move(e.clientY);}});
  el.addEventListener('pointerup',()=>end());el.addEventListener('pointercancel',()=>end(true));el.addEventListener('lostpointercapture',()=>end(true));
 }
 handle.onclick=()=>{if(ignoreClick)return;level=level==='half'?'full':'half';apply(bounds()[level],true);};
 // Pull down on content only when its scroll position is already at the top.
 // Inputs and sliders retain their own editing gestures.
 body.addEventListener('touchstart',e=>{cancelAnimationFrame(glide);contentStart=e.touches.length===1&&!e.target.closest('input,textarea,select')?{y:e.touches[0].clientY,last:e.touches[0].clientY,at:performance.now(),velocity:0,top:body.scrollTop<=0}:null;},{passive:true});
 body.addEventListener('touchmove',e=>{if(!contentStart||e.touches.length!==1)return;const y=e.touches[0].clientY;if(!document.body.classList.contains('landscape')&&!drag&&!contentStart.scrolling&&contentStart.top&&y-contentStart.y>8&&e.cancelable){begin(contentStart.y);contentStart.dragging=true;}if(contentStart.dragging&&drag){e.preventDefault();move(y);}else if(e.cancelable&&(contentStart.scrolling||Math.abs(y-contentStart.y)>8)){e.preventDefault();const now=performance.now();contentStart.scrolling=true;contentStart.velocity=(contentStart.last-y)/Math.max(1,now-contentStart.at);body.scrollTop+=contentStart.last-y;contentStart.last=y;contentStart.at=now;}},{passive:false});
 body.addEventListener('touchend',()=>{if(contentStart?.dragging)end();else if(contentStart?.scrolling){let v=performance.now()-contentStart.at<100?contentStart.velocity:0,last=performance.now();const step=now=>{const dt=Math.min(32,now-last);last=now;const before=body.scrollTop;body.scrollTop+=v*dt;v*=Math.pow(.94,dt/16);if(Math.abs(v)>.02&&Math.abs(body.scrollTop-before)>.1)glide=requestAnimationFrame(step);};glide=requestAnimationFrame(step);}contentStart=null;},{passive:true});
 body.addEventListener('touchcancel',()=>{if(contentStart?.dragging)end(true);contentStart=null;},{passive:true});
 window.addEventListener('resize',()=>{if(!sheet.hidden){drag=null;contentStart=null;apply(bounds()[level]);}});
 return {open,reset,bounds,height:()=>current};
})();
