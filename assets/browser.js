(()=>{
 if(window.Studio)return;
 document.documentElement.classList.add("browser-client");
 document.getElementById("photoStorageHint").textContent="照片保存在提供打印服务的设备";
 let cached={permission:true,device:{},history:[],message:'正在连接共享服务'},refreshing=false;
 const emit=(type,value)=>window.nativeEvent?.({type,value});
 async function request(path,data,raw=false){const options=data===undefined?{}:{method:'POST',headers:{'Content-Type':raw?'application/octet-stream':'application/json'},body:raw?data:JSON.stringify(data)};const r=await fetch('/api/'+path,{...options,credentials:'same-origin'});if(r.status===401){location.reload();throw Error('请重新配对');}const value=await r.json();if(!r.ok||value.error)throw Error(value.error||'共享服务请求失败');return value;}
 async function refresh(fresh=false){if(refreshing){if(fresh){await refreshing;return refresh();}return refreshing;}refreshing=(async()=>{try{cached=await request('state');}catch(e){cached={...cached,device:{...cached.device,connected:false},busy:true,message:'共享服务已断开，请检查提供服务的设备'};}finally{refreshing=false;}})();return refreshing;}
 function action(name){return request(name,{}).then(refresh).catch(e=>emit('toast',e.message));}
 function pick(limit,texture=false){const input=document.createElement('input');input.type='file';input.accept='image/*';input.multiple=!texture&&limit>1;input.onchange=async()=>{if(input.files.length>limit){emit('toast','本次最多选择 '+limit+' 张照片');return;}emit('loading',true);const items=[];try{for(const file of input.files){if(file.size>25*1024*1024)throw Error('单张照片不能超过 25 MB');items.push(await request('upload',file,true));}}catch(e){emit('toast',e.message);}finally{emit(texture?'texture':'photos',items);emit('loading',false);}};input.click();}
 const captureKey=()=> (window.STUDIO_DRAFT_KEY||'liuying-draft')+'-capture-result';let captureResult=null,capturePicking=false;
 try{captureResult=JSON.parse(localStorage.getItem(captureKey())||'null');}catch{}
 async function captureReady(){const result=captureResult;if(!result)return capturePicking;try{if(result.photos.length)await emit('photos',result.photos);}finally{await emit('captureFinished',result.finished);}return true;}
 function captureAck(id){if(captureResult?.finished.id!==id)return JSON.stringify({ok:true});try{localStorage.removeItem(captureKey());}catch{return JSON.stringify({error:'拍摄记录确认失败，可稍后恢复'});}captureResult=null;return JSON.stringify({ok:true});}
 function capture(limit){
  if(limit<1)return JSON.stringify({error:'最多保留 6 张照片'});
  if(capturePicking||captureResult)return JSON.stringify({error:'请先完成或恢复上次拍摄'});
  const id=randomId(),input=document.createElement('input');input.type='file';input.accept='image/*';input.setAttribute('capture','environment');let finished=false;capturePicking=true;
  const finish=async(value,photos=[])=>{if(finished)return;finished=true;capturePicking=false;captureResult={photos,finished:{id,...value}};try{localStorage.setItem(captureKey(),JSON.stringify(captureResult));}catch{}await captureReady();};
  input.oncancel=()=>finish({cancelled:true});input.onchange=async()=>{const file=input.files[0];if(!file){await finish({cancelled:true});return;}
   try{if(file.size>25*1024*1024)throw Error('单张照片不能超过 25 MB');const photo=await request('upload',file,true);await finish({},[{...photo,captureId:id}]);}
   catch(e){await finish({error:e.message||'无法读取拍摄照片'});}
  };try{input.click();}catch{capturePicking=false;return JSON.stringify({error:'无法打开相机或图片选择器'});}return JSON.stringify({ok:true,id});
 }
 window.Studio={
  state:()=>JSON.stringify(cached),landscape:()=>innerWidth>innerHeight&&innerWidth<1000,
  capture,captureReady,captureAck,pick:n=>pick(n),pickTexture:()=>pick(1,true),connect:()=>action('connect'),release:()=>action('release'),airprintLayout:splice=>request('airprint-layout',{splice}).then(refresh).catch(e=>emit('toast',e.message)),
  bluetoothSettings:()=>emit('toast','请在提供服务的设备上打开蓝牙设置'),
  cutout:source=>{setTimeout(()=>request('cutout',{source}).then(v=>emit('cutout',{source,images:v.images})).catch(e=>emit('cutoutError',{source,message:e.message})),0);return '{"ok":true}';},
  printBatch:async payload=>{try{const pages=JSON.parse(payload);const key=pendingPrint.requestId||(pendingPrint.requestId=randomId());const result=await request('print',{requestId:key,pages});await refresh();return JSON.stringify(result);}catch(e){return JSON.stringify({error:e.message});}},
  reprint:async payload=>{try{const result=await request('reprint',JSON.parse(payload));await refresh();return JSON.stringify(result);}catch(e){return JSON.stringify({error:e.message});}},
  reconcile:()=>action('reconcile'),cancel:()=>{if(confirm('取消自己的当前打印任务？'))action('cancel');},discardPrepared:()=>action('cancel'),resolveUnknown:()=>emit('toast','请在提供服务的设备上检查并处理未知任务')
 };
 function randomId(){const b=new Uint8Array(16);crypto.getRandomValues(b);return Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');}
 let queueRequest=0;
 async function openQueue(){
  if(!native.canManageQueue)return;
  const serial=++queueRequest,current=()=>serial===queueRequest&&sheetKind==='hostQueue'&&!$('sheet').hidden;
  openSheet('hostQueue','本机打印队列','<p class="hint" role="status">正在读取打印队列…</p>');
  try{const value=await request('admin/queue');if(!current())return;if(!native.canManageQueue)throw Error('当前设备无法管理打印队列');
   const labels={queued:'等待打印',printing:'正在打印',uncertain:'待检查',done:'已完成',cancelled:'已取消',aborted:'未完成',rejected:'未接受'};
   openSheet('hostQueue','本机打印队列',(value.jobs.length?value.jobs.map((j,i)=>`<div class="field"><strong>${esc(j.title||'打印任务')}</strong><p>${esc(labels[j.phase]||j.phase)} · ${esc(j.message||'')}</p>${j.phase==='uncertain'?`<button class="full-button secondary-button" data-query-job="${i}">查询打印机状态</button><button class="full-button secondary-button" data-resolve-job="${i}">已检查打印机，结束记录</button>`:''}</div>`).join(''):'<p class="hint">暂无打印任务</p>'));
   $('sheetBody').querySelectorAll('[data-query-job],[data-resolve-job]').forEach(button=>{button.onclick=async()=>{const resolve=button.hasAttribute('data-resolve-job'),job=value.jobs[+(resolve?button.dataset.resolveJob:button.dataset.queryJob)];if(resolve&&!confirm('确认已在打印机旁检查本次输出？此操作只结束未知记录，不会重新打印。'))return;button.disabled=true;try{await request(resolve?'admin/resolve':'admin/reconcile',{token:job.token,...(resolve?{confirmed:true}:{})});await refresh();if(sheetKind==='hostQueue')await openQueue();}catch(e){emit('toast',e.message);}finally{button.disabled=false;}};});
  }catch(e){if(current()){openSheet('hostQueue','本机打印队列','<p class="hint" role="status">'+esc(e.message||'打印队列暂时无法读取')+'</p><button class="full-button secondary-button" id="retryQueue">重新读取</button>');$('retryQueue').onclick=openQueue;}}
 }
 window.BrowserTransport={request,refresh,openQueue};refresh();setInterval(refresh,1200);
})();
