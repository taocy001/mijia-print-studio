/* One user-triggered camera result at a time; completed photos remain editable. */
window.PhotoCapture=(()=>{
 let pending=null,busy=false,readySent=false;const saved=new Set(),inFlight=new Map();
 const signature=()=>JSON.stringify({mode:state.mode,layout:state.collageLayout,template:state.templateId,media:state.media,orientation:state.orientation,active:state.active,photos:state.photos.map(p=>p.src)});
 const key=()=> (window.STUDIO_DRAFT_KEY||'liuying-draft')+'-capture';
 try{pending=JSON.parse(localStorage.getItem(key())||'null');}catch{}
 function clear(){pending=null;try{localStorage.removeItem(key());}catch{}}
 async function start(){
  if(busy||state.photos.length>=6)return;
  if(pending){if(typeof Studio.captureReady!=='function')return;if(!window.BrowserTransport){Studio.captureReady();return;}if(await Studio.captureReady())return;clear();}
  try{if(typeof Studio.capture!=='function')throw Error('请更新 App 后再拍摄');const result=JSON.parse(Studio.capture(1)||'{}');if(!result.ok)throw Error(result.error||'无法打开相机');pending={id:result.id,mode:'add',before:signature()};busy=true;try{localStorage.setItem(key(),JSON.stringify(pending));}catch{}}
  catch(e){busy=false;toast(e.message);}
 }
 const previous=window.nativeEvent;window.nativeEvent=async e=>{
  if(e.type==='photos'&&Array.isArray(e.value)&&e.value.some(p=>p.captureId)){
   const id=e.value[0].captureId;if(inFlight.has(id))return inFlight.get(id);
   const task=(async()=>{const before=signature(),eligible=pending?.before===before;
   try{for(const p of e.value)await loadPhoto(p);}catch{toast('拍摄照片未能载入，可稍后恢复');return;}
   const unchanged=before===signature(),fresh=e.value.filter(p=>!state.photos.some(old=>old.src===p.src));
   if(fresh.length>6-state.photos.length){toast('照片已满，请移除一张后恢复上次拍摄');return;}
   await previous({...e,value:fresh});
   if(!e.value.every(p=>state.photos.some(old=>old.src===p.src))){toast('拍摄照片未能载入，可稍后恢复');return;}
   if(pending?.id===id&&eligible&&unchanged){
    if(pending.mode==='strip'){state.mode='collage';state.collageLayout='strip';}
    else if(pending.mode==='single'){state.mode='photo';state.templateId=null;}
   }
   try{localStorage.setItem(window.STUDIO_DRAFT_KEY||'liuying-draft',JSON.stringify(state));saved.add(id);}catch{toast('草稿保存失败，拍摄照片仍保留，可稍后恢复');}
   schedule();})();inFlight.set(id,task);try{await task;}finally{inFlight.delete(id);}return;
  }
  if(e.type==='captureFinished'){
   const result=e.value||{};busy=false;
   if(result.error)toast(result.error);
   if(result.cancelled||result.error||saved.has(result.id)){
    try{if(typeof Studio.captureAck==='function'){const ack=JSON.parse(Studio.captureAck(result.id)||'{}');if(!ack.ok)throw Error(ack.error||'拍摄记录确认失败');}}catch(e){toast(e.message);return;}
    saved.delete(result.id);if(pending?.id===result.id)clear();
   }
   return;
  }
  return previous(e);
 };
 let gesture=null,suppressClick=false,consumedGesture=false;
 const target=e=>e.target.closest?.('#addMore,#addFirst');
 function cancel(){if(gesture){clearTimeout(gesture.timer);gesture.cancelled=true;suppressClick=true;}}
 document.addEventListener('pointerdown',e=>{
  if(gesture){cancel();return;}
  if(!target(e)||typeof Studio.capture!=='function')return;consumedGesture=false;if(e.button!==0)return;
  suppressClick=false;gesture={id:e.pointerId,x:e.clientX,y:e.clientY,cancelled:false};
  gesture.timer=setTimeout(()=>{if(!gesture||gesture.cancelled)return;suppressClick=true;gesture.cancelled=true;consumedGesture=true;start();},500);
 },true);
 document.addEventListener('pointermove',e=>{if(gesture&&gesture.id===e.pointerId&&Math.hypot(e.clientX-gesture.x,e.clientY-gesture.y)>10)cancel();},true);
 document.addEventListener('pointerup',e=>{if(gesture?.id===e.pointerId){clearTimeout(gesture.timer);gesture=null;}},true);
 document.addEventListener('pointercancel',()=>{cancel();gesture=null;},true);
 document.addEventListener('scroll',cancel,true);
 window.addEventListener('blur',()=>{cancel();gesture=null;});
 document.addEventListener('click',e=>{if(target(e)&&suppressClick){e.preventDefault();e.stopImmediatePropagation();suppressClick=false;}},true);
 document.addEventListener('contextmenu',e=>{if(!target(e)||typeof Studio.capture!=='function')return;e.preventDefault();const held=gesture?.cancelled;cancel();gesture=null;suppressClick=true;if(!held&&!consumedGesture){consumedGesture=true;start();}},true);
 document.addEventListener('keydown',e=>{if(!target(e))return;if(e.key==='ContextMenu'||(e.shiftKey&&e.key==='F10'))consumedGesture=false;else if(e.shiftKey&&e.key==='Enter'){e.preventDefault();if(!e.repeat)start();}else if(e.key==='Enter'||e.key===' ')suppressClick=false;},true);
 window.addEventListener('studio-state',()=>{if(!readySent&&typeof Studio.captureReady==='function'){readySent=true;Studio.captureReady();}});
 return {start};
})();
