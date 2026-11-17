window.TemplateStudio=(()=>{
 let category="all",openRequest=0,refreshThumbnails=null;const thumbnails=new Map(),THUMB_LIMIT=108;
 const legacyCategories=[['kids','童趣卡通'],['nature','自然花草'],['travel','旅行日常'],['celebration','浪漫庆典'],['art','艺术边框']];
 function groupOf(t){if(TemplateCollection.group(t.id))return TemplateCollection.group(t.id);if(t.group)return t.group;if(t.style.startsWith('kids-'))return 'kids';if(['air','tide','botanical','petal','ripple','orchard','alpine'].includes(t.style))return 'nature';if(['sunset','terrace','cafe','postcard'].includes(t.style))return 'travel';if(['glow','constellation','ribbon','confetti','festival'].includes(t.style))return 'celebration';return 'art';}
 function candidateSize(id){
  if(state.media!==5012||state.orientation!=='auto')return panelSize();
  const n=PhotoFlow.basics.find(t=>t.id===id)?.slots||BoothTemplates.get(id)?.slots||1,p=window.PhotoWorks?.owner()||active();
  return n===1&&p&&p.width>p.height?[1824,1216]:[1216,1824];
 }
 function offered(id){
  if(state.media===5014&&(PhotoFlow.basics.find(t=>t.id===id)?.slots||BoothTemplates.get(id)?.slots||1)>1)return false;
  if(id==='polaroid'||id==='strip'||id==='grid6'||BoothTemplates.retired(id))return false;
  const [w,h]=candidateSize(id),b=PhotoFlow.basics.find(t=>t.id===id);
  if(!b&&!TemplateCollection.includes(id))return false;
  if(b){if(b.slots===1)return true;const cols=id==='vertical'?1:id==='horizontal'?2:id==='grid6-roomy'?(w>h?3:2):2,rows=Math.ceil(b.slots/cols),margin=state.collageBorder??state.border??0,fw=(w-margin*2-(cols-1)*state.gap)/cols,fh=(h-margin*2-(rows-1)*state.gap)/rows;return Math.min(fw,fh)>=310&&Math.max(fw/fh,fh/fw)<=1.8;}
  return BoothTemplates.available(id,w,h);
 }
 function cached(key){if(!thumbnails.has(key))return null;const value=thumbnails.get(key);thumbnails.delete(key);thumbnails.set(key,value);return value;}
 function retain(key,value){thumbnails.delete(key);thumbnails.set(key,value);while(thumbnails.size>THUMB_LIMIT)thumbnails.delete(thumbnails.keys().next().value);}
 function selectTemplate(id){PhotoFlow.apply(id||'single');markSelection();if(window.EffectBrowser?.kind()==='templates'){closeSheet();EffectBrowser.refresh();}}
 function selectedId(){if(window.PhotoWorks?.enabled())return PhotoWorks.currentId();return state.mode==='collage'?state.collageTemplateId||state.photoLayout:state.mode==='polaroid'?'polaroid':active()?.templateId||state.templateId||'single';}
 function markSelection(){const id=selectedId();$('sheetBody').querySelectorAll('[data-choice]').forEach(b=>{const yes=b.dataset.choice===id;b.classList.toggle('selected',yes);b.setAttribute('aria-pressed',String(yes));});if($('templatePhotoHint'))$('templatePhotoHint').textContent=PhotoFlow.summary()+` · 当前屏幕最多 ${photoBatchLimit()} 张`;settings();}
 function settings(){const host=$('templateSettings');if(!host)return;const fixed=state.mode==='template'||!!BoothTemplates.current(),collage=state.mode==='collage',p=active();host.innerHTML=fixed?'<p class="hint">照片窗口与装饰由模板固定，可在照片上拖动、缩放调整取景。</p>':`<details><summary>调整当前模板</summary><div class="field"><label>当前照片适配</label><div class="segments">${[['cover','铺满'],['contain','完整保留'],...(!collage&&state.mode!=='polaroid'?[['bottom','底部留白']]:[])].map(([v,n])=>`<button data-template-fit="${v}" class="${(p?.fit||state.fit)===v?'selected':''}">${n}</button>`).join('')}</div></div>${collage||state.fit==='bottom'?`<label class="field">${collage?'整页白边':'底部留白'}<input id="templateBorder" type="range" min="0" max="200" value="${state.collageLayout==='strip'?state.stripBorder??0:collage?state.collageBorder??state.border:state.border||0}"></label>`:''}${collage?`<label class="field">照片间距<input id="templateGap" type="range" min="0" max="80" step="4" value="${state.gap}"></label>`:''}</details>`;host.querySelectorAll('[data-template-fit]').forEach(b=>b.onclick=()=>{changeSetting('fit',b.dataset.templateFit);settings();host.querySelector('details').open=true;});if($('templateBorder'))$('templateBorder').oninput=e=>{EditHistory.begin(collage?'photo-layout':'border',collage?PhotoFlow.historyOwner():active());if(state.mode==='collage'){if(state.collageLayout==='strip')state.stripBorder=+e.target.value;else state.collageBorder=+e.target.value;}state.border=+e.target.value;if(!collage&&active())active().border=state.border;EditHistory.commit();schedule();};if($('templateGap'))$('templateGap').oninput=e=>{EditHistory.run(()=>{state.gap=+e.target.value;},'photo-layout',PhotoFlow.historyOwner());schedule();};}
 function plainPreview(){
  const [w,h]=candidateSize('single'),c=document.createElement('canvas'),p=(window.PhotoWorks?.enabled()?PhotoWorks.owner():active());
  c.width=Math.round(240*w/Math.max(w,h));c.height=Math.round(240*h/Math.max(w,h));const ctx=c.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);
  const old={mode:state.mode,templateId:state.templateId},collect=collectingPhotoFrames,frames=composingFrames,matrix=photoFrameTransform;
  try{state.mode='photo';state.templateId=null;collectingPhotoFrames=false;composingFrames=null;photoFrameTransform=null;Tone.preview(()=>{ctx.scale(c.width/w,c.height/h);drawPanel(ctx,0,0,w,h,[{...p,templateId:null}]);},320);}
  finally{Object.assign(state,old);collectingPhotoFrames=collect;composingFrames=frames;photoFrameTransform=matrix;}
  return c.toDataURL('image/jpeg',.85);
 }

 function basicPreview(t){if(t.id==='single')return plainPreview();const c=document.createElement('canvas');c.width=160;c.height=120;const ctx=c.getContext('2d');ctx.fillStyle='#fffdf7';ctx.fillRect(0,0,160,120);const cols=t.id==='horizontal'?2:t.id==='grid6'?3:t.id==='grid6-roomy'?(candidateSize(t.id)[0]>candidateSize(t.id)[1]?3:2):t.id.startsWith('grid')?2:1,rows=Math.ceil(t.slots/cols);for(let i=0;i<t.slots;i++){const x=8+(i%cols)*144/cols,y=8+Math.floor(i/cols)*104/rows,w=144/cols-5,h=104/rows-5;ctx.fillStyle=['#b6c9c0','#e0c4a8','#bbc7dc'][i%3];ctx.fillRect(x,y,w,h);ctx.fillStyle='#34453d';ctx.font='16px sans-serif';ctx.textAlign='center';ctx.fillText(String(i+1),x+w/2,y+h/2+5);}return c.toDataURL();}
 function panelSize(){if(window.PhotoWorks?.split())return PhotoWorks.panelSize();const [w,h]=logicalSize();return [w,state.media===5014?h/2:h];}
 function entry(p=active(),w=panelSize()[0],h=panelSize()[1]){const base=TEMPLATE_CATALOG.find(t=>t.id===(p?.templateId||state.templateId))||TEMPLATE_CATALOG[0];return OriginalTemplates.variant(base,w,h);}
 async function ensureCurrent(){if(BoothTemplates.current()||BoothTemplates.get(active()?.templateId||state.templateId))await BoothTemplates.ready;}
 function paint(ctx,p,x,y,w,h,e=entry(p,w,h)){if(BoothTemplates.get(e.id))return BoothTemplates.paint(ctx,e.slots>1?(window.PhotoWorks?PhotoWorks.photos(e.slots,true):(PhotoFlow.multiple()?[...PhotoFlow.pagePhotos(),...state.photos.filter((_,i)=>!PhotoFlow.selection().includes(i))]:state.photos).slice(0,e.slots)):[p],x,y,w,h,e);OriginalTemplates.paint(ctx,p,x,y,w,h,e);}
 async function open(){
  if(!['photo','template','polaroid','collage'].includes(state.mode))return;
  const request=++openRequest,selected=selectedId(),catalog=TEMPLATE_CATALOG.filter(t=>offered(t.id)),basics=PhotoFlow.basics.filter(t=>offered(t.id));const [pw,ph]=panelSize(),wide=window.PhotoWorks?.split()?state.splitLayout==='landscape':pw>ph,orientation=pw===ph?'方形':wide?'横版':'竖版',label=state.media===5009?'3 寸背胶':state.media===5014?'4 寸拼接':'6 寸';
  openSheet('templates','模板',`<div class="template-heading"><span>${label} · ${orientation}</span>${state.media===5012||window.PhotoWorks?.split()?`<button id="templateOrientation">${wide?'切换竖版':'切换横版'}</button>`:''}</div><label class="desktop-template-category" for="desktopTemplateGroup"><span>分类</span><select id="desktopTemplateGroup">${groups().map(([id,name])=>`<option value="${esc(id)}" ${category===id?'selected':''}>${esc(name)}</option>`).join('')}</select></label><div class="template-categories" aria-label="模板风格">${groups().map(([key,name])=>`<button data-template-category="${key}" aria-pressed="${category===key}">${name}<small>${key==='all'?catalog.length+basics.length:key==='basic'?basics.length:catalog.filter(t=>groupOf(t)===key).length}</small></button>`).join('')}</div><p class="hint" id="templatePhotoHint"></p><div id="templateSettings"></div><div class="template-grid">${basics.map(t=>{const n=t.slots,blocked=n>photoBatchLimit();return `<button class="template-card" data-basic="${t.id}" data-choice="${t.id}" ${t.id==='single'?'id="noTemplate"':''} ${blocked?'disabled':''}><img src="${basicPreview(t)}" alt="${t.name}"><span>${t.name} · ${state.media===5014?"每幅":"每页"} ${n} 张${blocked?'（大屏可用）':''}</span></button>`;}).join('')}${catalog.map(t=>{const n=(t.slots||1),blocked=n>photoBatchLimit();return `<button class="template-card" data-choice="${t.id}" data-template="${t.id}" ${blocked?'disabled':''}><img alt="${esc(t.names.zh)}"><span>${esc(t.names.zh)} · ${state.media===5014?"每幅":"每页"} ${n} 张${blocked?'（大屏可用）':''}</span></button>`;}).join('')}</div>`);
  const grid=$('sheetBody').querySelector('.template-grid'),plain=$('noTemplate'),targets=[...grid.querySelectorAll('[data-template]')];
  function filterCategory(){if($('desktopTemplateGroup'))$('desktopTemplateGroup').value=category;for(const button of grid.querySelectorAll('[data-basic]:not([data-basic=single])'))grid.append(button);for(const button of grid.querySelectorAll('[data-basic]'))button.hidden=button.dataset.basic!=='single'&&!['all','basic'].includes(category);for(const button of targets){const t=TEMPLATE_CATALOG.find(t=>t.id===button.dataset.template);button.hidden=category!=='all'&&(groupOf(t)!==category);}for(const b of $('sheetBody').querySelectorAll('[data-template-category]'))b.setAttribute('aria-pressed',String(b.dataset.templateCategory===category));}
  $('sheetBody').querySelectorAll('[data-template-category]').forEach(b=>b.onclick=()=>{category=b.dataset.templateCategory;filterCategory();window.EffectBrowser?.refresh(true);});filterCategory();
  $('desktopTemplateGroup').onchange=e=>{category=e.target.value;filterCategory();$('sheetBody').scrollTop=0;};
  const current=()=>request===openRequest&&sheetKind==='templates'&&grid.isConnected&&$('sheetBody').contains(grid);
  // Choices respond immediately, even while their previews are still being painted.
  if($('templateOrientation'))$('templateOrientation').onclick=async()=>{try{setPaperOrientation(wide?'portrait':'landscape');await ensureCurrent();schedule();}catch(e){toast('模板未能载入');}};
  grid.querySelectorAll('[data-basic]').forEach(b=>b.onclick=()=>selectTemplate(b.dataset.basic));markSelection();
  targets.forEach(button=>button.onclick=()=>{if(current())selectTemplate(button.dataset.template);});
  const photo=(window.PhotoWorks?.enabled()?PhotoWorks.owner():active())||{src:'/sample.svg'};
  try{await Promise.all([loadPhoto(photo),BoothTemplates.ready]);}catch(e){if(current())toast('照片未能载入');return;}
  const fingerprint=()=>JSON.stringify([window.PhotoWorks?.enabled()?PhotoWorks.signature():null,state.photoSelection,photo.src,state.photos.map(p=>[p.src,p.zoom,p.x,p.y,p.turn,p.mirror,p.filter]),pw,ph,photo.turn,photo.mirror,photo.zoom,photo.x,photo.y,photo.fit||state.fit,photo.border??state.border,filter(photo)[0],peek,!!window.EffectBrowser?.active()]);
  let generation=0,lastSignature=null;
  async function fillThumbnails(){
  if(!current())return;const signature=fingerprint();if(signature===lastSignature)return;lastSignature=signature;if(plain)plain.querySelector('img').src=plainPreview();
  const token=++generation,valid=()=>current()&&token===generation&&signature===fingerprint();
  const queue=[...targets];
  while(queue.length&&valid()){
   // Yield before each small batch so opening, scrolling and changing tabs remain responsive.
   await new Promise(resolve=>requestAnimationFrame(resolve));
   if(!valid())return;
   const bounds=$('sheetBody').getBoundingClientRect();
   const priority=new Map(queue.map(button=>{const r=button.getBoundingClientRect();return [button,button.classList.contains('selected')?-1:r.bottom>bounds.top&&r.top<bounds.bottom?0:1];}));
   queue.sort((a,b)=>priority.get(a)-priority.get(b));
   const started=performance.now();
   do{
    const button=queue.shift();if(!valid()||!button.isConnected)return;
    try{
     const key=signature+'|'+(button.dataset.template||'plain'),hit=cached(key);if(hit){button.querySelector('img').src=hit;continue;}
     const [tw,th]=candidateSize(button.dataset.template||'single'),c=document.createElement('canvas');c.width=Math.round(240*tw/Math.max(tw,th));c.height=Math.round(240*th/Math.max(tw,th));const ctx=c.getContext('2d');
     Tone.preview(()=>{
      if(button===plain){ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);drawPhoto(ctx,!window.EffectBrowser?.active()&&(photo.fit||state.fit)==='contain'?{...photo,zoom:1,x:0,y:0}:photo,0,0,c.width,c.height);}
      else{const base=TEMPLATE_CATALOG.find(t=>t.id===button.dataset.template),e=OriginalTemplates.variant(base,tw,th);ctx.scale(c.width/e.width,c.height/e.height);paint(ctx,photo,0,0,e.width,e.height,e);}
     },320);
     if(valid()&&button.isConnected){const url=c.toDataURL('image/jpeg',.85);retain(key,url);button.querySelector('img').src=url;}
    }catch(e){if(valid()&&button.isConnected)button.disabled=true;}
   }while(queue.length&&valid()&&performance.now()-started<6);
  }
  }
  refreshThumbnails=fillThumbnails;await fillThumbnails();
 }
 $('templateBtn').onclick=()=>window.EffectBrowser?EffectBrowser.toggle('templates'):open();function browseItems(){return [...PhotoFlow.basics.filter(t=>t.id==='single').map(t=>({...t,group:'basic'})),...TEMPLATE_CATALOG.filter(t=>offered(t.id)).map(t=>({id:t.id,name:t.names.zh,slots:t.slots||1,group:groupOf(t)})),...PhotoFlow.basics.filter(t=>t.id!=='single'&&offered(t.id)).map(t=>({...t,group:'basic'}))].filter(t=>t.id==='single'||category==='all'||t.group===category).map(t=>({...t,disabled:t.slots>photoBatchLimit()}));}
 async function thumbnail(id){const b=PhotoFlow.basics.find(t=>t.id===id);if(b)return basicPreview(b);const p=(window.PhotoWorks?.enabled()?PhotoWorks.owner():active())||{src:'/sample.svg'};await Promise.all([loadPhoto(p),BoothTemplates.ready]);const [w,h]=candidateSize(id),c=document.createElement('canvas');c.width=Math.round(100*w/Math.max(w,h));c.height=Math.round(100*h/Math.max(w,h));const ctx=c.getContext('2d');Tone.preview(()=>{if(id==='polaroid'){ctx.fillStyle='#fffdf6';ctx.fillRect(0,0,c.width,c.height);drawPhoto(ctx,p,8,8,c.width-16,c.height*.7,'cover');}else{const e=OriginalTemplates.variant(TEMPLATE_CATALOG.find(t=>t.id===id),w,h);ctx.scale(c.width/e.width,c.height/e.height);paint(ctx,p,0,0,e.width,e.height,e);}},160);return c.toDataURL('image/jpeg',.75);}
 function groups(){return [['all','全部'],...TemplateCollection.groups,['basic','基础排列']];}
 function setGroup(value){if(groups().some(([id])=>id===value))category=value;}
 function groupFor(id){return PhotoFlow.basics.some(t=>t.id===id)?'basic':id==='polaroid'?'celebration':groupOf(TEMPLATE_CATALOG.find(t=>t.id===id)||TEMPLATE_CATALOG[0]);}
 function selectedName(){const id=selectedId();return PhotoFlow.basics.find(t=>t.id===id)?.name||(id==='polaroid'?'拍立得':TEMPLATE_CATALOG.find(t=>t.id===id)?.names.zh)||'当前模板';}
 return {offered,candidateSize,refreshPanel:()=>{if(sheetKind==='templates'){markSelection();refreshThumbnails?.();}},browseItems,thumbnail,selectedId,selectedName,groups,groupFor,setGroup,currentGroup:()=>category,open,paint,ensureCurrent,entry,apply:selectTemplate};
})();
