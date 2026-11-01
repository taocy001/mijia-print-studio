/* One user-triggered camera result at a time; completed photos remain editable. */
window.PhotoCapture=(()=>{
 let mode='single',pending=null,busy=false,readySent=false;const saved=new Set(),inFlight=new Map();
 const signature=()=>JSON.stringify({mode:state.mode,layout:state.collageLayout,template:state.templateId,media:state.media,orientation:state.orientation,active:state.active,photos:state.photos.map(p=>p.src)});
 const key=()=> (window.STUDIO_DRAFT_KEY||'liuying-draft')+'-capture';
 try{pending=JSON.parse(localStorage.getItem(key())||'null');if(pending)mode=pending.mode==='strip'?'strip':'single';}catch{}
 function clear(){pending=null;try{localStorage.removeItem(key());}catch{}}
 function open(){
  openSheet('camera','拍摄照片',`<div class="segments"><button data-capture-mode="single" class="${mode==='single'?'selected':''}" ${busy?'disabled':''}>单张照片</button><button data-capture-mode="strip" class="${mode==='strip'?'selected':''}" ${busy?'disabled':''}>照片条</button></div><p class="hint">当前 ${state.photos.length} / 6 张 · 保留已有照片</p><button class="full-button" id="captureNext" ${busy||state.photos.length>=6?'disabled':''}>${busy?'正在处理…':state.photos.length?'拍下一张':'拍摄照片'}</button>${pending&&!busy?'<button class="full-button secondary-button" id="recoverCapture">恢复上次拍摄</button>':''}`);
  $('sheetBody').querySelectorAll('[data-capture-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.captureMode;open();});
  $('captureNext').onclick=start;if($('recoverCapture'))$('recoverCapture').onclick=()=>{if(typeof Studio.captureReady==='function')Studio.captureReady();};
 }
 function start(){
  if(busy||state.photos.length>=6)return;
  try{if(typeof Studio.capture!=='function')throw Error('请更新 App 后再拍摄');const result=JSON.parse(Studio.capture(6-state.photos.length)||'{}');if(!result.ok)throw Error(result.error||'无法打开相机');pending={id:result.id,mode,before:signature()};busy=true;try{localStorage.setItem(key(),JSON.stringify(pending));}catch{}open();}
  catch(e){busy=false;toast(e.message);}
 }
 const previous=window.nativeEvent;window.nativeEvent=async e=>{
  if(e.type==='photos'&&Array.isArray(e.value)&&e.value.some(p=>p.captureId)){
   const id=e.value[0].captureId;if(inFlight.has(id))return inFlight.get(id);
   const task=(async()=>{const before=signature(),eligible=pending?.before===before||sheetKind==='camera';
   try{for(const p of e.value)await loadPhoto(p);}catch{toast('拍摄照片未能载入，可稍后恢复');return;}
   const unchanged=before===signature(),fresh=e.value.filter(p=>!state.photos.some(old=>old.src===p.src));
   if(fresh.length>6-state.photos.length){toast('照片已满，请移除一张后恢复上次拍摄');return;}
   await previous({...e,value:fresh});
   if(!e.value.every(p=>state.photos.some(old=>old.src===p.src))){toast('拍摄照片未能载入，可稍后恢复');return;}
   if(pending?.id===id&&eligible&&unchanged){
    if(pending.mode==='strip'){state.mode='collage';state.collageLayout='strip';}
    else{state.mode='photo';state.templateId=null;}
   }
   try{localStorage.setItem(window.STUDIO_DRAFT_KEY||'liuying-draft',JSON.stringify(state));saved.add(id);}catch{toast('草稿保存失败，拍摄照片仍保留，可稍后恢复');}
   schedule();})();inFlight.set(id,task);try{await task;}finally{inFlight.delete(id);}return;
  }
  if(e.type==='captureFinished'){
   const result=e.value||{};busy=false;
   if(result.error)toast(result.error);
   if(result.cancelled||result.error||saved.has(result.id)){
    try{if(typeof Studio.captureAck==='function'){const ack=JSON.parse(Studio.captureAck(result.id)||'{}');if(!ack.ok)throw Error(ack.error||'拍摄记录确认失败');}}catch(e){toast(e.message);if(sheetKind==='camera')open();return;}
    saved.delete(result.id);if(pending?.id===result.id)clear();
   }
   if(sheetKind==='camera')open();return;
  }
  return previous(e);
 };
 const menu=$('menuBtn').onclick;$('menuBtn').onclick=()=>{menu();if(typeof Studio.capture!=='function')return;$('sheetBody').insertAdjacentHTML('beforeend',`<button class="menu-row" id="capturePhoto">${icon('camera')}<span>拍摄照片</span>${icon('chevron')}</button>`);$('capturePhoto').onclick=open;};
 PATHS.camera='M3 6h5l2-3h4l2 3h5v15H3zM16 13a4 4 0 1 1-8 0a4 4 0 0 1 8 0';
 window.addEventListener('studio-state',()=>{if(!readySent&&typeof Studio.captureReady==='function'){readySent=true;Studio.captureReady();}});
 return {open};
})();
