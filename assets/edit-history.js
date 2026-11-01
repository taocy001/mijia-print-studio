/* Per-photo edit transactions; device and work-level settings are excluded. */
window.EditHistory=(()=>{
 const fields=['fit','border','zoom','x','y','turn','filter','sharpen','templateId','caption','overlays'];
 const stacks=new WeakMap();let pending=null,timer=0,restoring=false;
 const fieldSets={gesture:['zoom','x','y'],wheel:['zoom'],'layer-input':['overlays'],'layer-range':['overlays'],'layer-gesture':['overlays'],caption:['caption'],border:['border'],'border-range':['border']};
 const eligible=p=>p&&state.photos.includes(p)&&!['label','card'].includes(state.mode)&&!(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014));
 const snapshot=p=>Object.fromEntries(fields.map(k=>[k,JSON.stringify(p[k])]));
 function stack(p){if(!stacks.has(p))stacks.set(p,{past:[],future:[]});return stacks.get(p);}
 function begin(kind='edit',p=active()){
  if(restoring||!eligible(p))return;
  if(pending&&(pending.photo!==p||pending.draft!==state.photos))commit();
  if(!pending)pending={photo:p,draft:state.photos,kind,fields:fieldSets[kind]||fields,before:snapshot(p)};
 }
 function commit(){
  clearTimeout(timer);timer=0;const entry=pending;pending=null;if(!entry||restoring)return;
  if(entry.draft!==state.photos||!state.photos.includes(entry.photo))return;
  const after=snapshot(entry.photo),keys=entry.fields.filter(k=>entry.before[k]!==after[k]);if(!keys.length)return;
  const h=stack(entry.photo);const record={keys,before:entry.before,after};h.past.push(record);h.future=[];
  while(h.past.length>40||h.past.length>1&&JSON.stringify(h.past).length>2000000)h.past.shift();
  document.getElementById('layerUndo')?.remove();refresh();return {photo:entry.photo,record};
 }
 function defer(){if(!['layer-input','caption','border','wheel'].includes(pending?.kind))return;clearTimeout(timer);timer=setTimeout(commit,700);}
 function run(work){const own=!pending;begin();try{return work();}finally{if(own)commit();}}
 function status(){const h=active()&&stacks.get(active());return {undo:!!(eligible(active())&&h?.past.length),redo:!!(eligible(active())&&h?.future.length)};}
 function refresh(){const s=status();for(const [id,key] of [['undoEdit','undo'],['redoEdit','redo']])if($(id))$(id).disabled=!s[key];}
 function apply(back){
  commit();const p=active();if(!eligible(p))return;const h=stack(p),from=back?h.past:h.future,to=back?h.future:h.past,entry=from.pop();if(!entry)return;
  restoring=true;
  try{
   window.CropEditor?.resetGesture();window.CropEditor?.unlockDisplay();
   if(document.body.classList.contains('layer-editing'))closeSheet();
   for(const k of entry.keys){const value=(back?entry.before:entry.after)[k];if(value===undefined)delete p[k];else p[k]=JSON.parse(value);}
   if(entry.keys.some(k=>['fit','border','zoom','x','y','turn'].includes(k)))p.facePending=false;
   if(['photo','template'].includes(state.mode)){state.mode=p.templateId?'template':'photo';state.templateId=p.templateId||null;}
   state.fit=p.fit||'cover';state.border=p.border||0;state.filter=p.filter||'none';
   window.LayerEditor?.select(null);document.getElementById('layerUndo')?.remove();to.push(entry);render();save();
   if(sheetKind==='filters')openFilters();else if(sheetKind==='templates')TemplateStudio.open();else if(sheetKind==='layout')openLayout();
  }finally{restoring=false;refresh();}
 }
 const undo=()=>apply(true),redo=()=>apply(false);
 function undoLatest(receipt){commit();if(!receipt||active()!==receipt.photo||stacks.get(receipt.photo)?.past.at(-1)!==receipt.record)return false;undo();return true;}
 const menu=$('menuBtn').onclick;
 $('menuBtn').onclick=()=>{commit();menu();$('sheetBody').insertAdjacentHTML('beforeend',`<div class="menu-row edit-history-row">${icon('history')}<span>撤销与重做</span><button id="undoEdit" aria-label="撤销编辑" title="撤销编辑"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5 4 10l5 5M4 10h10a6 6 0 0 1 0 12"/></svg></button><button id="redoEdit" aria-label="重做编辑" title="重做编辑"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 5 5 5-5 5m5-5H10a6 6 0 0 0 0 12"/></svg></button></div>`);$('undoEdit').onclick=undo;$('redoEdit').onclick=redo;refresh();};
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
 return {begin,commit,defer,run,undo,redo,undoLatest,status};
})();
