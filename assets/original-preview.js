/* Transient full-original comparison. Never enters composition, printing or history. */
window.OriginalPreview=(()=>{
 const canvas=$('preview'),stage=$('paperStage'),overlay=document.createElement('div'),image=document.createElement('canvas'),label=document.createElement('span');
 overlay.id='originalPreview';overlay.hidden=true;overlay.setAttribute('aria-label','完整原图');
 Object.assign(overlay.style,{position:'absolute',pointerEvents:'none',zIndex:'50',background:'#282a2e',overflow:'hidden'});
 Object.assign(image.style,{display:'block',width:'100%',height:'100%'});
 label.textContent='原图 · 松手返回';Object.assign(label.style,{position:'absolute',left:'50%',bottom:'12px',transform:'translateX(-50%)',whiteSpace:'nowrap',borderRadius:'14px',padding:'5px 10px',background:'#000a',color:'#fff',fontSize:'12px'});
 overlay.append(image,label);stage.append(overlay);
 let gesture=null,timer=0,held=false,suppressClickUntil=0;
 const active=()=>held,pending=()=>!!timer;
 function stopTimer(){clearTimeout(timer);timer=0;}
 function release(){stopTimer();if(held){suppressClickUntil=performance.now()+400;CropEditor.resetGesture();}held=false;gesture=null;overlay.hidden=true;document.body.classList.remove('original-comparing');}
 function block(e){if(e.cancelable)e.preventDefault();e.stopImmediatePropagation();}
 function photoAt(e){if(!previewReady()||(sheetKind&&!$('sheet').classList.contains('desktop-inspector')))return null;const p=CropEditor.toPaper(e);if(!window.EffectBrowser?.active()&&LayerEditor.hit(p.x,p.y))return null;const f=PhotoWindows.find(photoFrames,p);return f?.p||null;}
 function show(){timer=0;if(!gesture||gesture.state!==state||!(state.photos.includes(gesture.photo)||window.PhotoWorks?.owns(gesture.photo)))return;const source=images.get(gesture.photo.src);if(!source)return;held=true;CropEditor.resetGesture();window.EffectBrowser?.resetGesture?.();
  const r=canvas.getBoundingClientRect(),s=stage.getBoundingClientRect();Object.assign(overlay.style,{left:r.left-s.left+'px',top:r.top-s.top+'px',width:r.width+'px',height:r.height+'px'});
  image.width=canvas.width;image.height=canvas.height;const ctx=image.getContext('2d'),w=source.naturalWidth||source.width,h=source.naturalHeight||source.height,k=Math.min(image.width/w,image.height/h);ctx.fillStyle='#282a2e';ctx.fillRect(0,0,image.width,image.height);ctx.drawImage(source,(image.width-w*k)/2,(image.height-h*k)/2,w*k,h*k);overlay.hidden=false;document.body.classList.add('original-comparing');try{navigator.vibrate?.(10);}catch{}
 }
 function begin(e,kind){const photo=photoAt(e);if(!photo)return;gesture={kind,id:e.identifier??e.pointerId,x:e.clientX,y:e.clientY,photo,state};timer=setTimeout(show,450);}
 function moved(e){if(gesture&&Math.hypot(e.clientX-gesture.x,e.clientY-gesture.y)>8){stopTimer();gesture=null;}}
 canvas.addEventListener('touchstart',e=>{if(held){block(e);return;}if(e.touches.length!==1){stopTimer();gesture=null;return;}if(!gesture)begin(e.touches[0],'touch');},{capture:true,passive:false});
 canvas.addEventListener('touchmove',e=>{if(held){block(e);return;}if(e.touches.length!==1){stopTimer();gesture=null;return;}moved(e.touches[0]);},{capture:true,passive:false});
 canvas.addEventListener('touchend',e=>{if(held){block(e);if(!e.touches.length)release();return;}stopTimer();gesture=null;},{capture:true,passive:false});
 canvas.addEventListener('touchcancel',e=>{if(held)block(e);release();},{capture:true,passive:false});
 canvas.addEventListener('pointerdown',e=>{if(held){block(e);return;}if(e.pointerType==='touch'||e.button!==0)return;begin(e,'pointer');},{capture:true});
 canvas.addEventListener('pointermove',e=>{if(held){block(e);return;}if(gesture?.kind==='pointer'&&gesture.id===e.pointerId)moved(e);},{capture:true});
 canvas.addEventListener('pointerup',e=>{if(held){block(e);if(e.pointerType!=='touch')release();return;}if(e.pointerType!=='touch'){stopTimer();gesture=null;}},{capture:true});
 canvas.addEventListener('pointercancel',e=>{if(held)block(e);release();},{capture:true});
 canvas.addEventListener('lostpointercapture',e=>{if(e.pointerType!=='touch')release();},{capture:true});
 canvas.addEventListener('contextmenu',e=>{if(held||timer)block(e);},{capture:true});
 canvas.addEventListener('click',e=>{if(performance.now()<suppressClickUntil)block(e);},{capture:true});
 window.addEventListener('blur',release);window.addEventListener('resize',release);document.addEventListener('visibilitychange',()=>{if(document.hidden)release();});
 document.addEventListener('pointerup',e=>{if(e.pointerType!=='touch'&&e.target!==canvas){if(held)block(e);release();}},{capture:true});
 document.addEventListener('pointercancel',e=>{if(e.pointerType!=='touch'&&e.target!==canvas)release();},{capture:true});
 document.addEventListener('pointermove',e=>{if(e.pointerType!=='touch'&&e.target!==canvas){if(held)block(e);else if(gesture?.kind==='pointer')moved(e);}},{capture:true});
 document.addEventListener('pointerdown',e=>{if(e.target!==canvas&&!canvas.contains(e.target))release();},{capture:true});
 return {active,pending,release};
})();
