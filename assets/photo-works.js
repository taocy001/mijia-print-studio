/* A thumbnail owns one work; its multi-photo slots refer to following source photos. */
window.PhotoWorks=(()=>{
 const family=()=>['photo','template','polaroid','collage'].includes(state.mode);
 const owner=()=>state.photos[state.active];
 const clone=v=>v===undefined?undefined:JSON.parse(JSON.stringify(v));
 const layoutKeys=['orientation','splitOrientation','gap','collageBorder','stripBorder'];
 const editKeys=['turn','mirror','zoom','x','y','fit','border','filter','sharpen','caption','overlays','facePending','coatTexture','coatThreshold','coatDensity','coatSource'];
 const meta=new WeakMap(),histories=new WeakMap(),slotPools=new WeakMap();let initialized=null,focused=null,lastMedia=null,splitPrintIndices=null,canonicalView=false;
 const freshLayout=()=>({orientation:'auto',splitOrientation:'auto',gap:16,collageBorder:0,stripBorder:0});
 const valid=id=>id==='polaroid'||PhotoFlow.basics.some(t=>t.id===id)||TEMPLATE_CATALOG.some(t=>t.id===id);
 const slots=id=>PhotoFlow.basics.find(t=>t.id===id)?.slots||BoothTemplates.get(id)?.slots||1;
 const split=()=>family()&&state.media===5014;
 const templateFor=p=>{const id=p?.work?.template||(!p?state.emptyPhotoWork?.template:null)||'single';return split()&&slots(id)>1?'single':id;};
 const currentId=()=>templateFor(owner());
 const capacity=(id=currentId())=>split()?1:slots(id);
 const multiple=()=>family()&&!split()&&slots(currentId())>1;
 const splitIndices=()=>splitPrintIndices||[Math.floor(state.active/2)*2,Math.floor(state.active/2)*2+1];
 const splitHorizontal=()=>split()&&state.splitLayout==='landscape'&&!canonicalView;
 function canonical(callback){const before=canonicalView;canonicalView=true;try{return callback();}finally{canonicalView=before;}}
 function panelSize(){return state.splitLayout==='landscape'?[912,1216]:[1216,912];}

 function panelTransform(half,p=owner()){
  const [w,h]=panelSize(p),m=splitHorizontal()?new DOMMatrix().translate(0,1216).rotate(-90):new DOMMatrix();
  m.translateSelf(w>h?0:1216,half*912);if(w<h)m.rotateSelf(90);return m;
 }
 function splitSpace(){const [w,h]=panelSize(),m=panelTransform(Math.max(0,splitIndices().indexOf(state.active)));return PhotoWindows.mapFrame({x:0,y:0,w,h},m);}
 function inPanel(ctx,half,p,callback){
  const [w,h]=panelSize(p),m=panelTransform(half,p),previous=photoFrameTransform;
  ctx.save();try{ctx.transform(m.a,m.b,m.c,m.d,m.e,m.f);ctx.beginPath();ctx.rect(0,0,w,h);ctx.clip();photoFrameTransform=m;callback(w,h);}finally{photoFrameTransform=previous;ctx.restore();}
 }

 function eachHalf(callback){
  const original=state.active,focus=focused,view={fit:state.fit,border:state.border,filter:state.filter};
  try{splitIndices().forEach((index,half)=>{state.active=index;activate();callback(state.photos[index],half);});}
  finally{state.active=original;activate();focused=focus;Object.assign(state,view);}
 }
 function paintSplit(ctx,w,h){eachHalf((p,half)=>{if(!p&&splitPrintIndices)return;inPanel(ctx,half,p,(pw,ph)=>drawPanel(ctx,0,0,pw,ph,[p]));});}
 function paintSplitLayers(ctx,w,h,mode){eachHalf((p,half)=>{if(p)inPanel(ctx,half,p,(pw,ph)=>LayerEditor.paint(ctx,pw,ph,p.work.layers,mode));});}


 let idSequence=0;
 const uid=()=>{const bytes=new Uint8Array(16);if(globalThis.crypto?.getRandomValues){crypto.getRandomValues(bytes);return 'p-'+Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');}return 'p-'+Date.now().toString(36)+'-'+(++idSequence).toString(36)+'-'+Math.random().toString(36).slice(2);};
 function makeWork(template='single',layout=freshLayout(),layers=[]){return {template:valid(template)?template:'single',layout:clone(layout),slots:{},layers:clone(layers)};}
 function initialize(){
  if(!['portrait','landscape'].includes(state.splitLayout))state.splitLayout=state.splitView==='landscape'?'landscape':'portrait';
  if(initialized===state){if(lastMedia!==state.media){lastMedia=state.media;if(family())activate();}return;}initialized=state;lastMedia=state.media;focused=null;
  const legacy=!state.photoWorkVersion,oldId=state.mode==='collage'?state.collageTemplateId||state.photoLayout||(state.collageLayout==='strip'?'strip':'grid4'):state.mode==='polaroid'?'polaroid':state.templateId||'single';
  const layout=Object.fromEntries(layoutKeys.map(k=>[k,state[k]??freshLayout()[k]])),layers=state.paperLayers?.photo||state.paperLayers?.collage||[];
  const seen=new Set();for(const p of state.photos){if(!p.photoId||seen.has(p.photoId))p.photoId=uid();seen.add(p.photoId);if(!p.work)p.work=makeWork(p.templateId||(legacy&&state.mode==='polaroid'?'polaroid':'single'),layout,layers);}
  if(legacy&&family()&&slots(oldId)>1&&state.photos.length){state.active=0;state.photos[0].work=makeWork(oldId,layout,layers);}
  if(!state.emptyPhotoWork)state.emptyPhotoWork=makeWork(!state.photos.length&&family()?oldId:'single',layout,layers);
  state.photoWorkVersion=1;if(family())activate();
 }
 function ensurePhoto(p,work){if(!p.photoId)p.photoId=uid();if(!p.work)p.work=work||makeWork();return p;}
 function work(){initialize();return owner()?ensurePhoto(owner()).work:state.emptyPhotoWork;}
 function saveCurrent(){if(initialized!==state){initialize();return;}if(!family())return;const w=work();for(const k of layoutKeys)w.layout[k]=state[k]??freshLayout()[k];}
 function activate(){
  const w=owner()?ensurePhoto(owner()).work:state.emptyPhotoWork||makeWork(),id=templateFor(owner()),b=PhotoFlow.basics.find(t=>t.id===id),booth=BoothTemplates.get(id);
  state.photoLayout=b?.id||null;state.collageTemplateId=booth?.slots>1?id:null;state.photoBatchTemplate=null;
  state.templateId=!b&&id!=='polaroid'&&!(booth?.slots>1)?id:null;
  state.mode=slots(id)>1?'collage':id==='polaroid'?'polaroid':state.templateId?'template':'photo';
  if(state.mode==='collage')state.collageLayout=booth?'booth':b?.id.startsWith('grid')?'grid':b?.id||'grid';
  Object.assign(state,freshLayout(),w.layout);if(owner()){owner().templateId=state.templateId;state.fit=owner().fit||'cover';state.border=owner().border||0;state.filter=owner().filter||'none';}
  state.photoSelection=indices();
 }
 function indices(){return family()?state.photos.slice(state.active,state.active+capacity()).map((p,i)=>state.active+i):[];}
 function pool(p){let value=slotPools.get(p);if(!value){value=new Map();slotPools.set(p,value);}return value;}
 function slot(p){
  const root=owner(),w=work();ensurePhoto(p);
  let value=w.slots[p.photoId];if(!value){value=Object.fromEntries(editKeys.filter(k=>p[k]!==undefined).map(k=>[k,clone(p[k])]));value.templateId=null;const existing=pool(root).get(p.photoId);if(existing){for(const k of Object.keys(existing))delete existing[k];Object.assign(existing,value);value=existing;}w.slots[p.photoId]=value;}
  pool(root).set(p.photoId,value);
  if(!meta.has(value)){for(const k of ['src','width','height','faces','idBackground','idCutouts'])Object.defineProperty(value,k,{configurable:true,get:()=>p[k]});meta.set(value,{root,source:p,draft:state});}
  return value;
 }
 function photos(count=capacity(),preview=false){
  initialize();const list=state.photos.slice(state.active,state.active+count);
  if(preview)return list.map(p=>({...p,...clone(work().slots[p.photoId]||{}),templateId:null,work:undefined}));
  return capacity()>1?list.map(slot):list;
 }
 function active(){if(!family())return null;initialize();if(capacity()<2)return owner();const list=photos();return list.find(p=>meta.get(p)?.source.photoId===focused)||list[0]||owner();}
 function selectSlot(p){if(split()){const index=state.photos.indexOf(p);if(index>=0&&index!==state.active){select(index);CropEditor.render();window.LayerEditor?.refresh();window.EditorChrome?.refresh();}return;}const m=meta.get(p);if(!m||m.root!==owner()||focused===m.source.photoId)return;EditHistory.commit();focused=m.source.photoId;CropEditor.render();window.LayerEditor?.refresh();window.EditorChrome?.refresh();}
 function select(index){
  if(!state.photos[index])return;window.EffectBrowser?.exit(false);window.EditHistory?.commit();saveCurrent();state.active=index;focused=null;initialize();activate();document.getElementById('layerUndo')?.remove();window.LayerEditor?.select(null);schedule();
 }
 function apply(id){initialize();if(!valid(id))return;if(split()&&slots(id)>1){toast('4 寸拼接每幅只支持一张照片，请选择单图模板');return;}if(capacity(id)>photoBatchLimit()){toast('此模板需要更多照片，请在电脑或平板大屏上使用');return;}if(window.EffectBrowser?.kind()!=='templates')window.EffectBrowser?.exit(false);window.LayerEditor?.select(null);saveCurrent();const change=()=>{work().template=id;focused=null;activate();if(capacity()>1)photos();};if(window.EditHistory)EditHistory.run(change,'photo-layout',historyOwner());else change();schedule();}
 function owns(p){const m=meta.get(p);return !!m&&m.draft===state&&family()&&m.root===owner()&&state.photos.includes(m.root)&&state.photos.includes(m.source);}
 function snapshot(p){if(p===owner()||p===emptyHolder)saveCurrent();return {work:clone(p.work),values:Object.fromEntries(editKeys.filter(k=>p[k]!==undefined).map(k=>[k,clone(p[k])]))};}
 function restore(p,value){
  const old=p.work||makeWork(),saved=clone(value.work);for(const [id,data] of Object.entries(saved.slots||{})){const stable=pool(p).get(id)||old.slots[id]||{};for(const k of Object.keys(stable))delete stable[k];Object.assign(stable,data);saved.slots[id]=stable;pool(p).set(id,stable);}
  Object.assign(old,saved);p.work=old;for(const k of editKeys){if(value.values[k]===undefined)delete p[k];else p[k]=clone(value.values[k]);}if((p===owner()||p===emptyHolder)&&family()){focused=null;activate();}
 }
 let emptyHolder=null;
 function owners(){if(!emptyHolder||emptyHolder.draft!==state){const draft=state;emptyHolder={draft,get work(){return draft.emptyPhotoWork;},set work(v){draft.emptyPhotoWork=v;}};}const p=owner()||emptyHolder;let all=histories.get(p);if(!all){const draft=state;all={layout:{draft,sceneKey:'work-layout',get photoLayoutState(){return snapshot(p);},set photoLayoutState(v){restore(p,v);}},effect:{draft,sceneKey:'work-effect',get effectState(){return snapshot(p);},set effectState(v){restore(p,v);},diffEffects:(a,b)=>[a,b]},layers:{draft,sceneKey:'work-layers',get overlays(){return p.work.layers;},set overlays(v){p.work.layers=v;}}};histories.set(p,all);}return all;}
 function historyOwner(){return owners().layout;}
 function historyPhotos(){return family()?[owner(),...(owner()?[...pool(owner()).values()].filter(owns):[])].filter(Boolean):[];}
 function added(list,previous){for(let i=0;i<list.length;i++)ensurePhoto(list[i],!previous&&!state.photos.slice(0,-list.length).length&&i===0?clone(state.emptyPhotoWork):undefined);}
 function missing(index=state.active){const p=state.photos[index],id=p?.work?.template||currentId();if(split())return p?0:1;return Math.max(0,capacity(id)-(state.photos.length-index));}
 function hasPendingFaceCrop(){if(!family())return false;return state.photos.some((p,i)=>{const n=capacity(templateFor(p));return n===1?!!p.facePending:state.photos.slice(i,i+n).some(source=>!!(p.work?.slots?.[source.photoId]?.facePending??source.facePending));});}
 function renderAt(index){state.active=index;focused=null;activate();}
 function candidateIndices(){initialize();const all=state.photos.map((p,i)=>i),templates=all.filter(i=>templateFor(state.photos[i])!=='single');return templates.length?templates:all;}
 function printableIndices(){return candidateIndices().filter(i=>!missing(i));}
 function selectPrintIndices(requested){const allowed=candidateIndices();return requested===undefined?printableIndices():[...new Set(requested)].filter(i=>allowed.includes(i));}
 function openBatch(){
  const selected=selectPrintIndices(pendingPrint?.workIndices);
  saveCurrent();openSheet('photoBatch','选择打印作品',candidateIndices().map(i=>{const p=state.photos[i],n=missing(i);return `<label class="field"><span><input type="checkbox" data-print-work="${i}" ${n?'disabled':selected.includes(i)?'checked':''}> 照片 ${i+1} · ${esc(name(templateFor(p)))}${n?' · 缺 '+n+' 张照片':''}</span></label>`;}).join('')+'<button class="full-button" id="confirmWorkBatch">预览所选作品</button>');
  $('confirmWorkBatch').onclick=()=>{const list=[...$('sheetBody').querySelectorAll('[data-print-work]:checked')].map(b=>+b.dataset.printWork);if(!list.length){toast('请先选择要打印的作品');return;}confirmPrint(list);};
 }
 const name=id=>PhotoFlow.basics.find(t=>t.id===id)?.name||(id==='polaroid'?'拍立得':TEMPLATE_CATALOG.find(t=>t.id===id)?.names.zh)||'单张';
 document.addEventListener('click',e=>{if(e.target.closest('#choosePrintWorks'))openBatch();});
 return {split,canonical,splitHorizontal,panelSize,templateFor,splitSpace,splitIndices,paintSplit,paintSplitLayers,setSplitPrintIndices:value=>{splitPrintIndices=value;},initialize,enabled:family,owner,active,work,saveCurrent,activate,select,selectSlot,apply,indices,photos,currentId,capacity,multiple,owns,historyOwner,historyPhotos,effectOwner:()=>owners().effect,layersOwner:()=>owners().layers,added,missing,hasPendingFaceCrop,renderAt,candidateIndices,selectPrintIndices,printableIndices,openBatch,name,signature:()=>JSON.stringify([owner()?.photoId,work()]),focus:()=>focused,restoreFocus:v=>{focused=v;}};
})();
PhotoWorks.initialize();
