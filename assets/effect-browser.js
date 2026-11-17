/* A reversible preview session: one-finger browsing, two-finger crop, one history record. */
window.EffectBrowser=(()=>{
 const canvas=$('preview'),rail=document.createElement('section');rail.id='effectRail';rail.hidden=true;rail.setAttribute('aria-label','效果预览');$('photos').before(rail);
 rail.innerHTML='<div id="effectChoices" role="group" aria-label="效果缩略图"></div>';
 const heading=document.createElement('div');heading.className='effect-heading';heading.hidden=true;heading.innerHTML='<button id="effectName" aria-haspopup="true"></button><button id="effectAll" aria-label="打开全部模板或色调">全部</button><button id="effectCancel">取消</button>';
 const groupMenu=document.createElement('div');groupMenu.id='effectGroups';groupMenu.hidden=true;groupMenu.setAttribute('role','group');groupMenu.setAttribute('aria-label','模板分组');document.body.append(groupMenu);
 function mountHeading(){const head=$('editorToolbar')?.querySelector('.editor-head');if(head&&heading.parentNode!==head)head.append(heading);}
 function closeGroups(){groupMenu.hidden=true;$('effectName')?.setAttribute('aria-expanded','false');}
 function showGroups(){if(mode!=='templates')return openAll();if(!groupMenu.hidden)return closeGroups();groupMenu.innerHTML=TemplateStudio.groups().map(([id,name])=>`<button data-effect-group="${esc(id)}" aria-pressed="${TemplateStudio.currentGroup()===id}">${esc(name)}</button>`).join('')+'<button id="effectGroupAll">打开全部模板</button>';const rect=heading.getBoundingClientRect();const above=rect.top-12,below=innerHeight-rect.bottom-12;groupMenu.style.maxHeight=Math.max(80,Math.min(innerHeight*.55,Math.max(above,below)))+'px';groupMenu.style.top=above>below?'auto':(rect.bottom+4)+'px';groupMenu.style.bottom=above>below?(innerHeight-rect.top+4)+'px':'auto';groupMenu.style.left=Math.max(8,Math.min(rect.left,innerWidth-344))+'px';groupMenu.hidden=false;$('effectName').setAttribute('aria-expanded','true');groupMenu.querySelectorAll('[data-effect-group]').forEach(b=>b.onclick=()=>{TemplateStudio.setGroup(b.dataset.effectGroup);closeGroups();const list=items();if(!list.some(t=>t.id===current())){const first=list.find(t=>!t.disabled);if(first)choose(first.id);}refresh(true);});$('effectGroupAll').onclick=()=>{closeGroups();openAll();};}
 function fitRail(){const h=$('photos').getBoundingClientRect().height;rail.style.height=h+'px';const track=$('effectChoices'),vertical=verticalStrip(),size=vertical?48:Math.min(64,Math.max(40,($('photos').querySelector('.photo-item')?.getBoundingClientRect().width)||((track.clientWidth-42)/6)));rail.style.setProperty('--effect-size',size+'px');track.style.setProperty('--effect-end-space',Math.max(0,((vertical?track.clientHeight:track.clientWidth)-size)/2)+'px');}
 document.addEventListener('pointerdown',e=>{if(!heading.contains(e.target)&&!groupMenu.contains(e.target))closeGroups();});
 let mode='',draft=null,owner=null,ownerDraft=null,photo=null,gesture=null,mouse=null,railKey='',lastChoice='',generation=0,layerTimer=0,lastLayer=null,thumbRunKey='';
 const choiceNodes=new Map(),thumbnailCache=new Map(),thumbnailSources=new WeakMap();let sourceSequence=0;
 const owners=new Map();const identities=new WeakMap();let serial=0;const token=p=>{if(!identities.has(p))identities.set(p,++serial);return identities.get(p);};
 const keys=['filter','sharpen','zoom','x','y','turn','mirror','fit','border','templateId','facePending'];
 function historyOwner(){if(window.PhotoWorks?.enabled())return PhotoWorks.effectOwner();if(ownerDraft!==state){owners.clear();ownerDraft=state;}const family=PhotoFlow.enabled()?'photo':state.mode;owner=owners.get(family);if(!owner){const source=state;owner={draft:source,sceneKey:'effect-preview',get effectState(){return {layout:PhotoFlow.historyOwner().photoLayoutState,orientation:source.orientation,fit:source.fit,border:source.border,filter:source.filter,photos:source.photos.map(p=>({token:token(p),values:Object.fromEntries(keys.map(k=>[k,p[k]]))}))};},set effectState(v){if(source!==state)return;if(v.partial){const apply=(object,patch)=>{for(const [k,e] of Object.entries(patch))if(e.present)object[k]=e.value;else delete object[k];};if(Object.keys(v.layout).length||v.templates.length){const layout=PhotoFlow.historyOwner().photoLayoutState;apply(layout,v.layout);for(const t of v.templates){const old=layout.templates.find(x=>x.token===t.token);if(old)old.id=t.id;}PhotoFlow.historyOwner().photoLayoutState=layout;}apply(source,v.settings);for(const item of v.photos){const p=source.photos.find(p=>token(p)===item.token);if(p)apply(p,item.values);}return;}PhotoFlow.historyOwner().photoLayoutState=v.layout;for(const k of ['orientation','fit','border','filter'])source[k]=v[k];for(const p of source.photos){const saved=v.photos.find(o=>o.token===token(p));if(saved)for(const k of keys){if(saved.values[k]===undefined)delete p[k];else p[k]=saved.values[k];}}},diffEffects};owners.set(family,owner);}return owner;}
 function diffEffects(a,b){
  const fields=(left,right)=>{const keys=[...new Set([...Object.keys(left),...Object.keys(right)])].filter(k=>JSON.stringify(left[k])!==JSON.stringify(right[k]));const pick=o=>Object.fromEntries(keys.map(k=>[k,{present:Object.hasOwn(o,k),value:o[k]}]));return [pick(left),pick(right)];};
  const [al,bl]=fields(Object.fromEntries(Object.entries(a.layout).filter(([k])=>k!=='templates')),Object.fromEntries(Object.entries(b.layout).filter(([k])=>k!=='templates'))),[as,bs]=fields(Object.fromEntries(['orientation','fit','border','filter'].map(k=>[k,a[k]])),Object.fromEntries(['orientation','fit','border','filter'].map(k=>[k,b[k]])));
  const at=[],bt=[],ap=[],bp=[];for(const t of a.layout.templates){const next=b.layout.templates.find(v=>v.token===t.token);if(next&&t.id!==next.id){at.push(t);bt.push(next);}}
  for(const p of a.photos){const next=b.photos.find(v=>v.token===p.token);if(!next)continue;const [before,after]=fields(p.values,next.values);if(Object.keys(before).length){ap.push({token:p.token,values:before});bp.push({token:p.token,values:after});}}
  return [{partial:true,layout:al,templates:at,settings:as,photos:ap},{partial:true,layout:bl,templates:bt,settings:bs,photos:bp}];
 }
 const active=()=>!!mode,kind=()=>mode;
 const items=()=>mode==='templates'?TemplateStudio.browseItems():mode==='filters'?FILTERS.map(([id,name])=>({id,name})):[];
 const current=()=>mode==='templates'?TemplateStudio.selectedId():photo?.filter||'none';
 function thumbnailSignature(){
  const source=p=>{if(!p)return null;let entry=thumbnailSources.get(p);if(!entry||entry.src!==p.src){entry={src:p.src,id:++sourceSequence};thumbnailSources.set(p,entry);}return entry.id;};
  if(mode==='filters')return String(source(photo));
  return JSON.stringify([window.PhotoWorks?.enabled()?PhotoWorks.signature():null,logicalSize(),state.media,state.fit,state.border,state.filter,state.gap,state.photoSelection,PhotoFlow.multiple(),state.photos.map(p=>[source(p),p.turn,p.mirror,p.zoom,p.x,p.y,p.fit,p.border,p.filter,p.sharpen]),state.photos.indexOf(window.active())]);
 }
 function retainThumbnail(key,url){thumbnailCache.delete(key);thumbnailCache.set(key,url);while(thumbnailCache.size>108)thumbnailCache.delete(thumbnailCache.keys().next().value);}
 function renderThumbnails(list,signature){
  const runKey=mode+'|'+signature+'|'+list.map(t=>t.id).join(',');if(runKey===thumbRunKey)return;thumbRunKey=runKey;const epoch=++generation,renderMode=mode,renderPhoto=photo;
  const currentIndex=Math.max(0,list.findIndex(t=>t.id===current())),queue=[...list].sort((a,b)=>Math.abs(list.indexOf(a)-currentIndex)-Math.abs(list.indexOf(b)-currentIndex));
  (async()=>{for(const t of queue){if(epoch!==generation||!mode)return;const button=choiceNodes.get(renderMode+':'+t.id),img=button?.querySelector('img'),key=renderMode+'|'+signature+'|'+t.id;if(!img||!button.isConnected||img.dataset.thumbnailKey===key)continue;
    const cached=thumbnailCache.get(key);if(cached){img.src=cached;img.dataset.thumbnailKey=key;continue;}
    await new Promise(requestAnimationFrame);if(epoch!==generation||!mode)return;
    try{let url;if(renderMode==='templates')url=await TemplateStudio.thumbnail(t.id);else{await loadPhoto(renderPhoto);if(epoch!==generation)return;url=Tone.image(images.get(renderPhoto.src),t.id,true).toDataURL('image/jpeg',.7);}
     if(epoch!==generation||signature!==thumbnailSignature())return;retainThumbnail(key,url);if(button.isConnected){img.src=url;img.dataset.thumbnailKey=key;}
    }catch{}
   }})();
 }
 function refresh(recenter=false){if(!mode)return;if(draft!==state){exit(false);return;}if(mode==='filters'&&photo!==window.active()){exit(false);return;}
  const list=items(),id=current(),index=list.findIndex(t=>t.id===id),name=mode==='templates'?TemplateStudio.selectedName():list[index]?.name||'原图';mountHeading();heading.hidden=false;rail.hidden=false;$('photos').hidden=false;fitRail();
  $('effectName').textContent=(mode==='filters'?'色调 · ':TemplateStudio.groups().find(([id])=>id===TemplateStudio.currentGroup())?.[1]+' ▾ · ')+name;$('effectName').title=$('effectName').textContent;$('effectName').onclick=showGroups;
  for(const [button,k] of [['templateBtn','templates'],['filterBtn','filters']])$(button).setAttribute('aria-pressed',String(k===mode));
  const key=mode+'|'+list.map(t=>t.id).join(','),changed=key!==railKey;
  const buttons=list.map(t=>{const nodeKey=mode+':'+t.id;let button=choiceNodes.get(nodeKey);if(!button){button=document.createElement('button');button.dataset.effect=t.id;button.innerHTML='<img alt=""><small class="effect-count"></small>';button.onclick=()=>{if(performance.now()<stripClickBlockedUntil)return;stopStrip();choose(t.id);centerChoice(t.id);};choiceNodes.set(nodeKey,button);}button.disabled=!!t.disabled;button.title=t.name;button.setAttribute('aria-label',t.name+(t.slots?'，'+t.slots+' 张照片':'')+(t.disabled?'，大屏可用':''));button.setAttribute('aria-pressed',String(t.id===id));const badge=button.querySelector('small');badge.hidden=!t.slots;badge.textContent=t.slots?String(t.slots):'';return button;});
  if(changed){stopStrip();railKey=key;$('effectChoices').replaceChildren(...buttons);}
  renderThumbnails(list,thumbnailSignature());
  if(!stripUser&&(recenter||changed||lastChoice!==id)){centerChoice(index>=0?id:list.find(t=>!t.disabled)?.id);lastChoice=id;}
 }
 const verticalStrip=()=>document.body.classList.contains('landscape')&&!document.body.classList.contains('desktop-editor');
 let stripUser=false,stripPointer=null,stripTouchCount=0,stripTimer=0,stripClickBlockedUntil=0;
 function stopStrip(){clearTimeout(stripTimer);stripTimer=0;stripUser=false;stripPointer=null;stripTouchCount=0;}
 function centerChoice(id){const track=$('effectChoices'),button=choiceNodes.get(mode+':'+id);if(!button||!track.contains(button))return;const r=track.getBoundingClientRect(),b=button.getBoundingClientRect(),vertical=verticalStrip();track[vertical?'scrollTop':'scrollLeft']+=(vertical?b.top+b.height/2-r.top-r.height/2:b.left+b.width/2-r.left-r.width/2);}
 function settleStrip(){clearTimeout(stripTimer);stripTimer=0;if(!stripUser||stripPointer||stripTouchCount||!mode||sheetKind)return;const track=$('effectChoices'),r=track.getBoundingClientRect(),vertical=verticalStrip(),middle=vertical?r.top+r.height/2:r.left+r.width/2;let best=null,distance=Infinity;
  for(const b of track.querySelectorAll('[data-effect]:not(:disabled)')){const v=b.getBoundingClientRect(),d=Math.abs((vertical?v.top+v.height/2:v.left+v.width/2)-middle);if(d<distance){best=b;distance=d;}}
  stripUser=false;if(best){choose(best.dataset.effect);centerChoice(best.dataset.effect);}
 }
 function queueSettle(){clearTimeout(stripTimer);if(stripUser&&!stripPointer&&!stripTouchCount)stripTimer=setTimeout(settleStrip,160);}
 const track=$('effectChoices');
 track.addEventListener('touchstart',e=>{stripTouchCount=e.touches.length;},{passive:true});
 document.addEventListener('touchstart',e=>{if(stripUser)stripTouchCount=e.touches.length;},{passive:true});
 for(const name of ['touchend','touchcancel'])document.addEventListener(name,e=>{if(stripUser){stripTouchCount=e.touches.length;queueSettle();}},{passive:true});
 track.addEventListener('scroll',queueSettle,{passive:true});track.addEventListener('scrollend',()=>{if(stripUser&&!stripPointer&&!stripTouchCount)settleStrip();},{passive:true});
 track.addEventListener('wheel',()=>{stripUser=true;queueSettle();},{passive:true});
 track.addEventListener('pointerdown',e=>{if(!mode||e.button!==0)return;clearTimeout(stripTimer);stripUser=true;stripPointer={id:e.pointerId,type:e.pointerType,x:e.clientX,y:e.clientY,offset:track[verticalStrip()?'scrollTop':'scrollLeft'],moved:false};});
 track.addEventListener('pointermove',e=>{const p=stripPointer;if(!p||p.id!==e.pointerId||p.type==='touch')return;const delta=verticalStrip()?e.clientY-p.y:e.clientX-p.x;if(!p.moved&&Math.abs(delta)<=6)return;if(!p.moved){p.moved=true;track.setPointerCapture(e.pointerId);}e.preventDefault();track[verticalStrip()?'scrollTop':'scrollLeft']=p.offset-delta;});
 function finishStrip(e){if(!stripPointer||stripPointer.id!==e.pointerId)return;if(stripPointer.moved)stripClickBlockedUntil=performance.now()+350;stripPointer=null;queueSettle();}
 for(const name of ['pointerup','pointercancel','lostpointercapture'])document.addEventListener(name,finishStrip);
 track.addEventListener('dragstart',e=>e.preventDefault());
 track.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();stopStrip();step(['ArrowLeft','ArrowUp'].includes(e.key)?-1:1);}});
 function choose(id){if(!mode)return;const t=items().find(t=>t.id===id);if(!t||t.disabled)return;if(id===current()){refresh();return;}if(mode==='filters'){photo.filter=id;state.filter=id;schedule();}else TemplateStudio.apply(id);refresh();}
 function step(delta){const list=items().filter(t=>!t.disabled),i=list.findIndex(t=>t.id===current()),next=i<0?(delta<0?list.length-1:0):i+Math.sign(delta);if(next>=0&&next<list.length)choose(list[next].id);}
 function start(next){if(!['filters','templates'].includes(next))return;if(next==='filters'&&$('filterBtn').disabled||next==='templates'&&$('templateBtn').disabled)return;
  if(mode===next){exit();return;}dismissClickUntil=0;exit(false);window.EditorChrome?.closeCrop();LayerEditor.select(null);CropEditor.resetGesture();peek=false;draft=state;photo=window.active();mode=next;railKey='';thumbRunKey='';EditHistory.beginGroup(historyOwner());document.body.classList.add('effect-browsing');document.body.classList.toggle('template-browsing',next==='templates');closeSheet();canvas.setAttribute('aria-label',next==='templates'?'照片内拖动取景，背景左右滑动切换模板，底部工具栏下滑收起':'左右滑动切换色调，从下部下滑收起，双指缩放当前照片');refresh(true);schedule();}
 function exit(close=true,cancel=false){dismissGesture=null;cancelPending();stopStrip();if(!mode)return;mode='';gesture=mouse=null;generation++;closeGroups();heading.hidden=true;rail.hidden=true;$('photos').hidden=false;document.body.classList.remove('effect-browsing','template-browsing');EditHistory.endGroup(cancel);draft=photo=null;CropEditor.resetGesture();CropEditor.unlockDisplay();if(close&&['templates','filters'].includes(sheetKind))closeSheet();LayerEditor.refresh();window.EditorChrome?.refresh();schedule();}
 function beforeSheet(next){stopStrip();closeGroups();cancelPending();if(mode&&next!==mode)exit(false);}
 const closeGallery=window.closeSheet;window.closeSheet=function(){const previous=sheetKind;closeGallery();if(mode==='templates'&&previous==='templates'){if(!items().some(t=>t.id===current()))TemplateStudio.setGroup(TemplateStudio.groupFor(current()));refresh(true);}};
 $('closeSheet').onclick=()=>window.closeSheet();$('scrim').onclick=()=>window.closeSheet();
 function openAll(){closeGroups();if(mode==='templates')TemplateStudio.open();else if(mode==='filters')openFilters();}
 heading.querySelector('#effectAll').onclick=openAll;heading.querySelector('#effectCancel').onclick=()=>exit(true,true);
 function cancelPending(){const had=!!layerTimer;clearTimeout(layerTimer);layerTimer=0;lastLayer=null;return had;}
 function activate(next,event){if(window.DesktopEditor?.openTool(next))return;if(['templates','filters'].includes(next))return start(next);exit(false);if(next==='layout')return openLayout();if(!['text','emoji'].includes(next))return;const double=event?.detail&&lastLayer?.kind===next&&performance.now()-lastLayer.at<300;clearTimeout(layerTimer);if(double){lastLayer=null;LayerEditor.activate(next,{resume:true});return;}lastLayer={kind:next,at:performance.now()};const run=()=>{layerTimer=0;lastLayer=null;LayerEditor.activate(next,{resume:false});};if(event?.detail)layerTimer=setTimeout(run,300);else run();}
 for(const [id,k] of [['templateBtn','templates'],['filterBtn','filters'],['addTextQuick','text'],['addEmojiQuick','emoji']]){$(id).onclick=e=>activate(k,e);$(id).title=['templates','filters'].includes(k)?'预览效果 · 左右滑动切换':k==='text'?'添加文字':'添加表情';}
 const back=window.goBack;window.goBack=()=>{if(!groupMenu.hidden){closeGroups();return true;}if(mode&&!sheetKind){exit(true,true);return true;}return cancelPending()||back();};
 // Downward gestures dismiss from the lower preview or its controls; horizontal browsing keeps priority.
 let dismissGesture=null,dismissClickUntil=0;
 function onTemplatePhoto(e){return mode==='templates'&&!!PhotoWindows.find(photoFrames,CropEditor.toPaper(e));}
 function dismissRegion(e){
  if(!mode||sheetKind||!groupMenu.hidden||window.OriginalPreview?.active())return false;
  if(heading.contains(e.target))return true;
  if(rail.contains(e.target))return !verticalStrip(); // The landscape rail already scrolls vertically.
  if(e.target!==canvas||onTemplatePhoto(e))return false;
  const r=canvas.getBoundingClientRect(),board=$('board').getBoundingClientRect(),workspace=canvas.closest('.workspace').getBoundingClientRect(),top=Math.max(r.top,board.top,workspace.top,0),bottom=Math.min(r.bottom,board.bottom,workspace.bottom,innerHeight);
  return bottom>top&&e.clientY>=bottom-Math.min(150,(bottom-top)/3)&&e.clientY<=bottom;
 }
 function dismissStart(e,kind){if(dismissRegion(e))dismissGesture={kind,id:kind==='touch'?e.identifier:e.pointerId,x:e.clientX,y:e.clientY,dx:0,dy:0,mode,draft:state,cancelled:false,locked:false};}
 function dismissBlock(e){if(e.cancelable)e.preventDefault();e.stopImmediatePropagation();}
 function dismissMove(e,event){
  const g=dismissGesture;if(!g||g.cancelled)return;
  if(g.mode!==mode||g.draft!==state||sheetKind||window.OriginalPreview?.active()){g.cancelled=true;return;}
  g.dx=e.clientX-g.x;g.dy=e.clientY-g.y;
  if(!g.locked&&Math.hypot(g.dx,g.dy)>8){
   if(g.dy>Math.abs(g.dx)*1.4){g.locked=true;window.OriginalPreview?.release();gesture=mouse=null;stopStrip();CropEditor.resetGesture();}
   else g.cancelled=true;
  }
  if(g.locked&&!g.cancelled)dismissBlock(event);
 }
 function dismissEnd(event){
  const g=dismissGesture;dismissGesture=null;if(!g||g.cancelled||!g.locked)return;
  dismissBlock(event);dismissClickUntil=performance.now()+500;
  if(g.mode===mode&&g.draft===state&&!sheetKind&&g.dy>=44&&g.dy>Math.abs(g.dx)*1.4)exit();
 }
 document.addEventListener('touchstart',e=>{
  if(dismissGesture){if(e.touches.length!==1)dismissGesture.cancelled=true;return;}
  if(e.touches.length===1){const t=e.touches[0];dismissStart({identifier:t.identifier,clientX:t.clientX,clientY:t.clientY,target:e.target},'touch');}
 },{capture:true,passive:true});
 document.addEventListener('touchmove',e=>{const g=dismissGesture;if(g?.kind!=='touch')return;if(e.touches.length!==1){g.cancelled=true;return;}const t=[...e.touches].find(t=>t.identifier===g.id);if(t)dismissMove(t,e);},{capture:true,passive:false});
 document.addEventListener('touchend',e=>{if(dismissGesture?.kind!=='touch')return;if(e.touches.length){dismissGesture.cancelled=true;return;}dismissEnd(e);},{capture:true,passive:false});
 document.addEventListener('touchcancel',()=>{dismissGesture=null;},{capture:true,passive:true});
 document.addEventListener('pointerdown',e=>{if(e.pointerType!=='touch'&&e.button===0)dismissStart(e,'mouse');},{capture:true});
 document.addEventListener('pointermove',e=>{if(dismissGesture?.kind==='mouse'&&dismissGesture.id===e.pointerId)dismissMove(e,e);},{capture:true});
 document.addEventListener('pointerup',e=>{if(dismissGesture?.kind==='mouse'&&dismissGesture.id===e.pointerId)dismissEnd(e);},{capture:true});
 document.addEventListener('pointercancel',e=>{if(dismissGesture?.kind==='mouse'&&dismissGesture.id===e.pointerId)dismissGesture=null;},{capture:true});
 document.addEventListener('click',e=>{if(performance.now()<dismissClickUntil&&(e.target===canvas||rail.contains(e.target)||heading.contains(e.target)))dismissBlock(e);},{capture:true});
 window.addEventListener('blur',()=>{dismissGesture=null;});window.addEventListener('resize',()=>{dismissGesture=null;});
 function finish(g){if(g&&!g.cancelled&&!g.held&&Math.abs(g.dx)>=34&&Math.abs(g.dx)>Math.abs(g.dy)*1.4)step(g.dx<0?1:-1);}
 canvas.addEventListener('touchstart',e=>{if(!mode)return;if(e.touches.length!==1){if(gesture)gesture.cancelled=true;else gesture={cancelled:true};return;}if(!gesture){const t=e.touches[0];if(onTemplatePhoto(t))return;gesture={id:t.identifier,x:t.clientX,y:t.clientY,dx:0,dy:0};}},{passive:true});
 canvas.addEventListener('touchmove',e=>{if(!mode||!gesture)return;if(e.touches.length!==1){gesture.cancelled=true;return;}const t=[...e.touches].find(t=>t.identifier===gesture.id);if(!t)return;gesture.dx=t.clientX-gesture.x;gesture.dy=t.clientY-gesture.y;if(!gesture.cancelled&&Math.abs(gesture.dx)>Math.abs(gesture.dy)*1.2&&e.cancelable)e.preventDefault();},{passive:false});
 canvas.addEventListener('touchend',e=>{if(!mode)return;if(e.touches.length){if(gesture)gesture.cancelled=true;return;}const g=gesture;gesture=null;finish(g);},{passive:true});
 canvas.addEventListener('touchcancel',()=>{gesture=null;},{passive:true});
 canvas.addEventListener('pointerdown',e=>{if(!mode||e.pointerType==='touch'||e.button!==0||onTemplatePhoto(e))return;mouse={id:e.pointerId,x:e.clientX,y:e.clientY,dx:0,dy:0};canvas.setPointerCapture(e.pointerId);});
 canvas.addEventListener('pointermove',e=>{if(!mode||!mouse||e.pointerId!==mouse.id)return;mouse.dx=e.clientX-mouse.x;mouse.dy=e.clientY-mouse.y;});
 canvas.addEventListener('pointerup',()=>{const g=mouse;mouse=null;finish(g);});
 for(const event of ['pointercancel','lostpointercapture'])canvas.addEventListener(event,()=>{mouse=null;});
 canvas.addEventListener('keydown',e=>{if(!mode||e.target!==canvas||e.ctrlKey||e.metaKey)return;if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();step(e.key==='ArrowLeft'?-1:1);}else if(e.key==='Escape'){e.preventDefault();exit(true,true);}});
 window.addEventListener('blur',()=>{stopStrip();gesture=mouse=null;cancelPending();});
 window.addEventListener('resize',()=>{stopStrip();gesture=mouse=null;closeGroups();if(mode)refresh(true);});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!groupMenu.hidden){e.preventDefault();closeGroups();}});
 return {active,kind,toggle:start,activate,step,exit,beforeSheet,refresh,cancelPending,pending:()=>!!layerTimer,historyOwner,resetGesture:()=>{gesture=mouse=null;},fitRail};
})();
