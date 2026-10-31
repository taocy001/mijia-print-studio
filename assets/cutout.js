/* Local native segmentation; cached variants never replace the original photo. */
window.CutoutEditor=(()=>{
 const pending=new Map(),colors=[['','原底色'],['white','白底'],['blue','蓝底'],['red','红底']];
 function path(value){return typeof value==='string'&&/^\/private\/cutouts\/u2netp-v1-[a-f0-9]{64}-(white|blue|red)\.jpg$/.test(value);}
 async function loadVariant(p,color){if(!color)return;const src=p.idCutouts?.[color];if(!path(src))throw Error('抠图结果不可用');await loadPhoto({src});}
 async function applyResult(p,job){let color;do{color=job.wanted;await loadVariant(p,color);}while(color!==job.wanted);p.idBackground=color;}
 const ready=Promise.all(state.photos.map(async p=>{if(!p.idBackground)return;try{await loadVariant(p,p.idBackground);if(!images.has(p.idCutouts?.[p.idBackground]))throw Error('missing cutout');}catch{p.idBackground='';p.idCutouts={};toast('抠图缓存不可用，已恢复原底色，请重新选择底色');}})).then(schedule);
 function source(p){return state.mode==='id'&&!peek&&p.idBackground?images.get(p.idCutouts?.[p.idBackground])||images.get(p.src):images.get(p.src);}
 function update(){if(!$('idBackgroundOptions'))return;const p=active(),job=p&&pending.get(p.src);for(const b of $('idBackgroundOptions').querySelectorAll('button')){b.classList.toggle('selected',b.dataset.idBackground===(job?.wanted??p?.idBackground??''));b.disabled=!p;}if($('cutoutStatus'))$('cutoutStatus').textContent=job?'正在处理照片…':p?.idBackground?'已换底，可切回原底色':'自动识别主体并换底，原照片保留';}
 async function select(color){const p=active();if(!p)return;
  const job=pending.get(p.src);if(job){job.wanted=color;if(!color)p.idBackground='';update();schedule();return;}
  if(!color){p.idBackground='';schedule();update();return;}
  if(path(p.idCutouts?.[color])){const cached={wanted:color};pending.set(p.src,cached);update();try{await applyResult(p,cached);}catch{toast('无法读取抠图缓存，请重新选择底色');p.idCutouts={};}finally{pending.delete(p.src);schedule();update();}return;}
  let result;try{result=JSON.parse(bridge('cutout',p.src)||'{}');}catch{result={};}
  if(!result.ok){toast(result.error||'无法启动本地抠图，请在新版 App 中重试');return;}
  pending.set(p.src,{wanted:color});update();
 }
 const previousLayout=openLayout;openLayout=function(){previousLayout();if(state.mode!=='id')return;const box=document.createElement('div');box.className='field';box.innerHTML='<label>证件照底色</label><div class="segments" id="idBackgroundOptions">'+colors.map(([v,label])=>`<button data-id-background="${v}">${label}</button>`).join('')+'</div><p class="hint" id="cutoutStatus"></p>';$('sheetBody').appendChild(box);box.querySelectorAll('button').forEach(b=>b.onclick=()=>select(b.dataset.idBackground));update();};
 const previousEvent=window.nativeEvent;window.nativeEvent=async event=>{
  if(!['cutout','cutoutError'].includes(event.type))return previousEvent(event);
  const {source:src}=event.value||{},job=pending.get(src);if(!job)return;
  const p=state.photos.find(p=>p.src===src);
  try{if(event.type==='cutoutError')throw Error(event.value.message||'抠图失败');if(p){p.idCutouts=event.value.images;await applyResult(p,job);}}
  catch(e){toast(e.message||'无法加载抠图结果，保留原设置');}
  finally{pending.delete(src);schedule();update();}
 };
 const previousPrepare=preparePrintPages;preparePrintPages=async function(){await ready;if(state.mode==='id'&&pending.size)throw Error('抠图尚未完成，请稍候再预览打印');return previousPrepare();};
 return{ready,source};
})();
