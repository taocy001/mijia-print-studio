/* Photo and paper-layer edit transactions; device settings are excluded. */
window.EditHistory=(()=>{
 const fields=['photoOrderState','effectState','photoLayoutState','mirror','fit','border','zoom','x','y','turn','mirror','filter','sharpen','templateId','caption','overlays'];
 const stacks=new WeakMap();let pending=null,timer=0,restoring=false,sequence=0,group=null;
 const fieldSets={'photo-order':['photoOrderState'],'effect-session':['effectState'],'photo-layout':['photoLayoutState'],'layer-edit':['overlays'],gesture:['zoom','x','y'],wheel:['zoom'],'layer-input':['overlays'],'layer-range':['overlays'],'layer-gesture':['overlays'],caption:['caption'],border:['border'],'border-range':['border']};
 const eligible=p=>!!p&&(window.PhotoWorks?.owns(p)|| (p.sceneKey?p.draft===state:state.photos.includes(p)&&!['label','card'].includes(state.mode)&&!(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014))));
 const snapshot=p=>Object.fromEntries(fields.map(k=>[k,JSON.stringify(p[k])]));
 function stack(p){if(!stacks.has(p))stacks.set(p,{past:[],future:[]});return stacks.get(p);}
 function begin(kind='edit',p){
  p ||= kind.startsWith('layer-')?window.LayerEditor?.historyOwner():active();
  if(group||restoring||!eligible(p))return;
  if(pending&&(pending.photo!==p||pending.draft!==state.photos))commit();
  if(!pending)pending={photo:p,draft:state.photos,kind,fields:fieldSets[kind]||fields,before:snapshot(p)};
 }
 function commit(){
  if(group)return;
  clearTimeout(timer);timer=0;const entry=pending;pending=null;if(!entry||restoring)return;
  if(entry.draft!==state.photos||!eligible(entry.photo))return;
  const after=snapshot(entry.photo);if(entry.kind==='effect-session'){const pair=entry.photo.diffEffects(JSON.parse(entry.before.effectState),JSON.parse(after.effectState));entry.before.effectState=JSON.stringify(pair[0]);after.effectState=JSON.stringify(pair[1]);}const keys=entry.fields.filter(k=>entry.before[k]!==after[k]);if(!keys.length)return;
  for(const owner of candidates())if(owner!==entry.photo&&stacks.has(owner))stacks.get(owner).future=[];
  const h=stack(entry.photo);const record={keys,before:entry.before,after,sequence:++sequence};h.past.push(record);h.future=[];
  while(h.past.length>40||h.past.length>1&&JSON.stringify(h.past).length>2000000)h.past.shift();
  document.getElementById('layerUndo')?.remove();refresh();return {photo:entry.photo,record};
 }
 function defer(){if(!['layer-input','caption','border','wheel'].includes(pending?.kind))return;clearTimeout(timer);timer=setTimeout(commit,700);}
 function run(work,kind='edit',p){const own=!pending;begin(kind,p);try{return work();}finally{if(own)commit();}}
 function candidates(){return [active(),...(window.PhotoWorks?.historyPhotos()||[]),window.LayerEditor?.historyOwner(null),window.PhotoFlow?.enabled()?PhotoFlow.historyOwner():null,window.PhotoFlow?.enabled()?PhotoFlow.orderOwner():null,window.EffectBrowser?.historyOwner()].filter(eligible);}
 function nextOwner(back){const key=back?'past':'future';return candidates().filter(p=>stacks.get(p)?.[key].length).sort((a,b)=>{const d=stacks.get(a)[key].at(-1).sequence-stacks.get(b)[key].at(-1).sequence;return back?-d:d;})[0];}
 function status(){return {undo:!!nextOwner(true),redo:!!nextOwner(false)};}
 function refresh(){const s=status();for(const [id,key] of [['undoEdit','undo'],['redoEdit','redo'],['editorUndo','undo'],['editorRedo','redo']])if($(id))$(id).disabled=!s[key];}
 function apply(back,owner){
  commit();const p=owner||nextOwner(back);if(!eligible(p))return;const h=stack(p),from=back?h.past:h.future,to=back?h.future:h.past,entry=from.pop();if(!entry)return;
  restoring=true;
  try{
   window.CropEditor?.resetGesture();window.CropEditor?.unlockDisplay();
   if(document.body.classList.contains('layer-editing'))closeSheet();
   for(const k of entry.keys){const value=(back?entry.before:entry.after)[k];if(value===undefined)delete p[k];else p[k]=JSON.parse(value);}
   if(!p.sceneKey&&!window.PhotoWorks?.owns(p)){
   if(entry.keys.some(k=>['fit','border','zoom','x','y','turn','mirror'].includes(k)))p.facePending=false;
   if(['photo','template'].includes(state.mode)){state.mode=p.templateId?'template':'photo';state.templateId=p.templateId||null;}
   state.fit=p.fit||'cover';state.border=p.border||0;state.filter=p.filter||'none';
   }
   window.LayerEditor?.select(null);document.getElementById('layerUndo')?.remove();to.push(entry);render();save();
   if(sheetKind==='filters')openFilters();else if(sheetKind==='templates')TemplateStudio.open();else if(sheetKind==='layout')openLayout();
  }finally{restoring=false;refresh();}
 }
 const undo=()=>{if(window.EffectBrowser?.active())EffectBrowser.exit(false);apply(true);},redo=()=>{if(window.EffectBrowser?.active())EffectBrowser.exit(false);apply(false);};
 function beginGroup(owner){commit();begin('effect-session',owner);group=owner;}
 function endGroup(cancel=false){if(!group)return;const owner=group;group=null;if(cancel){const entry=pending;pending=null;clearTimeout(timer);if(entry&&owner.draft===state)owner.effectState=JSON.parse(entry.before.effectState);refresh();}else commit();}
 function undoLatest(receipt){commit();if(!receipt||!eligible(receipt.photo)||nextOwner(true)!==receipt.photo||stacks.get(receipt.photo)?.past.at(-1)!==receipt.record)return false;apply(true,receipt.photo);return true;}
 const menu=$('menuBtn').onclick;
 $('menuBtn').onclick=()=>{commit();menu();};
 document.addEventListener('keydown',e=>{
  if(e.defaultPrevented||e.isComposing||e.altKey||!(e.ctrlKey||e.metaKey)||e.target.closest?.('input,textarea,select,[contenteditable]'))return;
  if(sheetKind&&!['menu','layout','filters','templates','layers'].includes(sheetKind))return;
  const key=e.key.toLowerCase();if(key==='z'||key==='y'&&e.ctrlKey){e.preventDefault();key==='y'||e.shiftKey?redo():undo();}
 });
 document.addEventListener('pointerdown',e=>{if(['layer-input','caption','border','wheel'].includes(pending?.kind))commit();if(e.target.matches?.('[data-layer-range]'))begin('layer-range');else if(e.target.id==='borderInput')begin('border-range');},true);
 for(const event of ['pointerup','pointercancel'])document.addEventListener(event,()=>{if(['layer-range','border-range'].includes(pending?.kind))commit();});
 document.addEventListener('focusout',()=>{if(['layer-input','caption','border'].includes(pending?.kind))commit();});
 window.addEventListener('blur',commit);
 for(const id of ['zoomIn','zoomOut','rotate','reset']){const action=$(id).onclick;$(id).onclick=e=>run(()=>action(e));}
 return {refresh,beginGroup,endGroup,begin,commit,defer,run,undo,redo,undoLatest,status};
})();
