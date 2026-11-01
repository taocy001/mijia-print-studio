/* Temporary effect browsing; photograph edits remain independent of this view. */
window.EffectBrowser=(()=>{
 const canvas=$('preview'),bar=document.querySelector('.photo-tools'),group=document.createElement('div');
 group.id='effectTools';group.hidden=true;group.setAttribute('role','group');group.setAttribute('aria-label','切换效果');
 group.innerHTML=`<button id="effectPrev" aria-label="上一个效果" title="上一个效果">${icon('chevron')}</button><span id="effectName" role="status" aria-live="polite"></span><button id="effectNext" aria-label="下一个效果" title="下一个效果">${icon('chevron')}</button><button id="effectAll" aria-label="全部效果" title="全部效果">${icon('layout')}</button><button id="effectDone" aria-label="完成效果选择" title="完成">${icon('check')}</button>`;bar.append(group);
 let mode='',photo=null,gesture=null,mouse=null,animation=null,lastEffect='',lastScope='',geometryScope='',lastActivation=null,activationTimer=0;
 function markDrawer(){
  const current=sheetKind==='layers'?($('sheetTitle').textContent.includes('表情')?'addEmojiQuick':'addTextQuick'):{layout:'layoutBtn',filters:'filterBtn',templates:'templateBtn',text:'addTextQuick'}[sheetKind];
  for(const button of document.querySelectorAll('.tool-tabs button'))button.classList.toggle('drawer-selected',!active()&&!$('sheet').hidden&&button.id===current);
 }
 new MutationObserver(markDrawer).observe($('sheet'),{attributes:true,attributeFilter:['hidden','data-kind']});
 new MutationObserver(markDrawer).observe($('sheetTitle'),{childList:true,subtree:true,characterData:true});
 const originalLabel=canvas.getAttribute('aria-label');canvas.tabIndex=0;
 const active=()=>!!mode,kind=()=>mode;
 const buttons={layout:'layoutBtn',filters:'filterBtn',templates:'templateBtn'},labels={layout:'排版',filters:'色调',templates:'模板'};
 const allowed=k=>!!buttons[k]&&!$(buttons[k]).disabled&&(k!=='layout'||['photo','template'].includes(state.mode));
 const openGrid=k=>k==='layout'?openLayout():k==='filters'?openFilters():TemplateStudio.open();
 const items=()=>mode==='layout'?[{id:'cover',name:'铺满相纸'},{id:'contain',name:'完整保留'},{id:'bottom',name:'底部留白'}]:mode==='filters'?FILTERS.map(([id,name])=>({id,name})): [{id:null,name:'无模板'},...TEMPLATE_CATALOG.map(t=>({id:t.id,name:t.names.zh}))];
 const current=()=>mode==='layout'?(activePhoto()?.fit||state.fit||'cover'):mode==='filters'?(activePhoto()?.filter||'none'):(activePhoto()?.templateId||null);
 function activePhoto(){return window.active?window.active():state.photos[state.active];}
 function focus(){canvas.focus({preventScroll:true});}
 function refresh(){
  if(!mode)return;
  if(!activePhoto()||!allowed(mode)){exit(!sheetKind||sheetKind===mode);return;}
  const scope=state.active+'|'+state.media+'|'+state.orientation;
  if(photo!==activePhoto()||geometryScope!==scope){
   const changed=photo!==activePhoto();photo=activePhoto();geometryScope=scope;gesture=mouse=null;CropEditor.lockDisplay();
   if(changed&&sheetKind===mode){const target=photo,k=mode;queueMicrotask(()=>{if(mode===k&&activePhoto()===target&&sheetKind===k)openGrid(k);});}
  }
  const list=items(),index=Math.max(0,list.findIndex(item=>item.id===current()));
  $('effectName').textContent=list[index].name;$('effectName').title=`${index+1} / ${list.length}`;
  $('effectPrev').disabled=index===0;$('effectNext').disabled=index===list.length-1;
  if(mode==='filters'&&sheetKind==='filters')$('sheetBody').querySelectorAll('[data-filter]').forEach(button=>{const selected=button.dataset.filter===current();button.classList.toggle('active',selected);button.setAttribute('aria-pressed',String(selected));});
  group.hidden=false;$('photoTools').hidden=true;$('layerTools').hidden=true;bar.hidden=false;bar.setAttribute('aria-label',labels[mode]+'快捷选择');
  for(const [id,k] of [['layoutBtn','layout'],['filterBtn','filters'],['templateBtn','templates']])$(id).setAttribute('aria-pressed',String(k===mode));
  const signature=mode+'|'+current();
  if(signature!==lastEffect&&scope===lastScope&&!matchMedia('(prefers-reduced-motion:reduce)').matches){animation?.cancel();animation=canvas.animate([{opacity:.85},{opacity:1}],{duration:130,easing:'ease-out'});}
  lastEffect=signature;lastScope=scope;markDrawer();
 }
 function toggle(next){
  clearTimeout(activationTimer);activationTimer=0;
  if(!allowed(next)){if(next==='layout')openLayout();return;}
  if(!activePhoto()){openGrid(next);return;}
  if(mode===next){exit();return;}
  CropEditor.lockDisplay();LayerEditor.select(null);peek=false;photo=activePhoto();mode=next;gesture=mouse=null;
  document.body.classList.add('effect-browsing');canvas.setAttribute('aria-label',labels[mode]+'预览，左右滑动切换效果');
  closeSheet();CropEditor.render();refresh();focus();
 }
 function exit(restore=true){
  clearTimeout(activationTimer);activationTimer=0;lastActivation=null;
  if(!mode)return;const old=mode;save();mode='';photo=null;gesture=mouse=null;animation?.cancel();animation=null;
  document.body.classList.remove('effect-browsing');group.hidden=true;canvas.setAttribute('aria-label',originalLabel);CropEditor.resetGesture();LayerEditor.refresh();
  for(const id of ['layoutBtn','filterBtn','templateBtn'])$(id).setAttribute('aria-pressed','false');
  if(restore&&(sheetKind===old||!sheetKind))closeSheet();
  CropEditor.render();markDrawer();
 }
 function beforeSheet(next){if(lastActivation&&next!==lastActivation.kind){clearTimeout(activationTimer);activationTimer=0;lastActivation=null;}if(mode&&next!==mode)exit(false);}
 function step(delta){
  clearTimeout(activationTimer);activationTimer=0;lastActivation=null;
  if(!mode||!allowed(mode)||!activePhoto())return;
  const list=items(),index=Math.max(0,list.findIndex(item=>item.id===current())),next=index+Math.sign(delta);
  if(next<0||next>=list.length)return;
  if(mode==='layout'){changeSetting('fit',list[next].id);if(sheetKind==='layout')openLayout();}
  else if(mode==='filters')changeSetting('filter',list[next].id);else TemplateStudio.apply(list[next].id,{preserveCrop:true});
  refresh();
 }
 $('effectPrev').onclick=()=>step(-1);$('effectNext').onclick=()=>step(1);$('effectDone').onclick=()=>exit();
 $('effectAll').onclick=()=>{clearTimeout(activationTimer);activationTimer=0;lastActivation=null;if(mode)openGrid(mode);refresh();};
 function activate(next,event){
  clearTimeout(activationTimer);activationTimer=0;
  if(!allowed(next)||!activePhoto()){lastActivation=null;if(next==='layout'||allowed(next))openGrid(next);return;}
  const now=performance.now(),pointer=!!event&&event.detail!==0;
  const double=pointer&&((lastActivation?.kind===next&&now-lastActivation.at<300)||event.detail===2);
  if(double){
   lastActivation=null;
   toggle(next);
   return;
  }
  lastActivation=pointer?{kind:next,at:now}:null;
  const open=()=>{activationTimer=0;lastActivation=null;if(allowed(next)){exit(false);openGrid(next);refresh();}};
  if(pointer)activationTimer=setTimeout(open,300);else open();
 }
 for(const [k,id] of Object.entries(buttons)){$(id).onclick=e=>activate(k,e);$(id).title=labels[k]+' · 单击查看全部，双击左右切换';}
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
 return {active,kind,toggle,activate,step,exit,beforeSheet,refresh};
})();
