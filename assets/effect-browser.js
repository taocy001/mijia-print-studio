/* Temporary effect browsing; photograph edits remain independent of this view. */
window.EffectBrowser=(()=>{
 const canvas=$('preview'),bar=document.querySelector('.photo-tools'),group=document.createElement('div');
 group.id='effectTools';group.hidden=true;group.setAttribute('role','group');group.setAttribute('aria-label','切换效果');
 group.innerHTML=`<button id="effectPrev" aria-label="上一个效果" title="上一个效果">${icon('chevron')}</button><span id="effectName" role="status" aria-live="polite"></span><button id="effectNext" aria-label="下一个效果" title="下一个效果">${icon('chevron')}</button><button id="effectAll" aria-label="全部效果" title="全部效果">${icon('layout')}</button><button id="effectDone" aria-label="完成效果选择" title="完成">${icon('check')}</button>`;bar.append(group);
 let mode='',photo=null,gesture=null,mouse=null,animation=null,lastEffect='',lastScope='',geometryScope='';
 const originalLabel=canvas.getAttribute('aria-label');canvas.tabIndex=0;
 const active=()=>!!mode,kind=()=>mode;
 const allowed=k=>!$(k==='filters'?'filterBtn':'templateBtn').disabled;
 const items=()=>mode==='filters'?FILTERS.map(([id,name])=>({id,name})): [{id:null,name:'无模板'},...TEMPLATE_CATALOG.map(t=>({id:t.id,name:t.names.zh}))];
 const current=()=>mode==='filters'?(activePhoto()?.filter||'none'):(activePhoto()?.templateId||null);
 function activePhoto(){return window.active?window.active():state.photos[state.active];}
 function focus(){canvas.focus({preventScroll:true});}
 function refresh(){
  if(!mode)return;
  if(!activePhoto()||!allowed(mode)){exit(!sheetKind||sheetKind===mode);return;}
  const scope=state.active+'|'+state.media+'|'+state.orientation;
  if(photo!==activePhoto()||geometryScope!==scope){
   const changed=photo!==activePhoto();photo=activePhoto();geometryScope=scope;gesture=mouse=null;CropEditor.lockDisplay();
   if(changed&&sheetKind===mode){const target=photo,k=mode;queueMicrotask(()=>{if(mode===k&&activePhoto()===target&&sheetKind===k)k==='filters'?openFilters():TemplateStudio.open();});}
  }
  const list=items(),index=Math.max(0,list.findIndex(item=>item.id===current()));
  $('effectName').textContent=list[index].name;$('effectName').title=`${index+1} / ${list.length}`;
  $('effectPrev').disabled=index===0;$('effectNext').disabled=index===list.length-1;
  if(mode==='filters'&&sheetKind==='filters')$('sheetBody').querySelectorAll('[data-filter]').forEach(button=>{const selected=button.dataset.filter===current();button.classList.toggle('active',selected);button.setAttribute('aria-pressed',String(selected));});
  group.hidden=false;$('photoTools').hidden=true;$('layerTools').hidden=true;bar.hidden=false;bar.setAttribute('aria-label',mode==='filters'?'色调快捷选择':'模板快捷选择');
  for(const [id,k] of [['filterBtn','filters'],['templateBtn','templates']])$(id).setAttribute('aria-pressed',String(k===mode));
  const signature=mode+'|'+current();
  if(signature!==lastEffect&&scope===lastScope&&!matchMedia('(prefers-reduced-motion:reduce)').matches){animation?.cancel();animation=canvas.animate([{opacity:.85},{opacity:1}],{duration:130,easing:'ease-out'});}
  lastEffect=signature;lastScope=scope;
 }
 function toggle(next){
  if(!allowed(next))return;
  if(!activePhoto()){next==='filters'?openFilters():TemplateStudio.open();return;}
  if(mode===next){exit();return;}
  CropEditor.lockDisplay();LayerEditor.select(null);peek=false;photo=activePhoto();mode=next;gesture=mouse=null;
  document.body.classList.add('effect-browsing');canvas.setAttribute('aria-label',(mode==='filters'?'色调':'模板')+'预览，左右滑动切换效果');
  closeSheet();CropEditor.render();refresh();focus();
 }
 function exit(restore=true){
  if(!mode)return;const old=mode;mode='';photo=null;gesture=mouse=null;animation?.cancel();animation=null;
  document.body.classList.remove('effect-browsing');group.hidden=true;canvas.setAttribute('aria-label',originalLabel);CropEditor.resetGesture();LayerEditor.refresh();
  for(const id of ['filterBtn','templateBtn'])$(id).setAttribute('aria-pressed','false');
  if(restore&&(sheetKind===old||!sheetKind))closeSheet();
  CropEditor.render();
 }
 function beforeSheet(next){if(mode&&next!==mode)exit(false);}
 function step(delta){
  if(!mode||!allowed(mode)||!activePhoto())return;
  const list=items(),index=Math.max(0,list.findIndex(item=>item.id===current())),next=index+Math.sign(delta);
  if(next<0||next>=list.length)return;
  if(mode==='filters')changeSetting('filter',list[next].id);else TemplateStudio.apply(list[next].id,{preserveCrop:true});
  refresh();
 }
 $('effectPrev').onclick=()=>step(-1);$('effectNext').onclick=()=>step(1);$('effectDone').onclick=()=>exit();
 $('effectAll').onclick=()=>{if(mode==='filters')openFilters();else if(mode==='templates')TemplateStudio.open();refresh();};
 function finish(g){if(g&&!g.cancelled&&Math.abs(g.dx)>=34&&Math.abs(g.dx)>Math.abs(g.dy)*1.4)step(g.dx<0?1:-1);}
 canvas.addEventListener('touchstart',e=>{if(!mode)return;focus();if(e.touches.length!==1){if(gesture)gesture.cancelled=true;return;}if(!gesture){const t=e.touches[0];gesture={id:t.identifier,x:t.clientX,y:t.clientY,dx:0,dy:0,cancelled:false};}},{passive:true});
 canvas.addEventListener('touchmove',e=>{if(!mode)return;if(e.touches.length!==1){if(gesture)gesture.cancelled=true;if(e.cancelable)e.preventDefault();return;}const t=[...e.touches].find(t=>t.identifier===gesture?.id);if(!t)return;gesture.dx=t.clientX-gesture.x;gesture.dy=t.clientY-gesture.y;if(Math.abs(gesture.dx)>Math.abs(gesture.dy)*1.2&&e.cancelable)e.preventDefault();},{passive:false});
 canvas.addEventListener('touchend',e=>{if(!mode)return;if(e.touches.length){if(gesture)gesture.cancelled=true;return;}const g=gesture;gesture=null;finish(g);},{passive:true});
 canvas.addEventListener('touchcancel',()=>gesture=null,{passive:true});
 canvas.addEventListener('pointerdown',e=>{if(!mode||e.pointerType==='touch'||e.button!==0)return;focus();mouse={id:e.pointerId,x:e.clientX,y:e.clientY,dx:0,dy:0};canvas.setPointerCapture(e.pointerId);});
 canvas.addEventListener('pointermove',e=>{if(!mode||!mouse||mouse.id!==e.pointerId)return;mouse.dx=e.clientX-mouse.x;mouse.dy=e.clientY-mouse.y;});
 canvas.addEventListener('pointerup',e=>{if(!mode||!mouse||mouse.id!==e.pointerId)return;const g=mouse;mouse=null;finish(g);});
 for(const event of ['pointercancel','lostpointercapture'])canvas.addEventListener(event,()=>mouse=null);
 canvas.addEventListener('keydown',e=>{if(!mode||e.target!==canvas||e.altKey||e.ctrlKey||e.metaKey||e.isComposing)return;if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();step(e.key==='ArrowLeft'?-1:1);}else if(e.key==='Escape'){e.preventDefault();exit();}});
 window.addEventListener('blur',()=>{gesture=mouse=null;});
 window.addEventListener('resize',()=>{gesture=mouse=null;});
 return {active,kind,toggle,step,exit,beforeSheet,refresh};
})();
