(()=>{
 if(window.Studio)return;
 document.documentElement.classList.add("browser-client");
 new ResizeObserver(()=>{document.documentElement.style.setProperty("--browser-dock-height",document.querySelector(".dock").getBoundingClientRect().height+"px");window.CropEditor?.render();}).observe(document.querySelector(".dock"));
 let cached={permission:true,device:{},history:[],message:'正在连接共享服务'},refreshing=false;
 const emit=(type,value)=>window.nativeEvent?.({type,value});
 async function request(path,data,raw=false){const options=data===undefined?{}:{method:'POST',headers:{'Content-Type':raw?'application/octet-stream':'application/json'},body:raw?data:JSON.stringify(data)};const r=await fetch('/api/'+path,{...options,credentials:'same-origin'});if(r.status===401){location.reload();throw Error('请重新配对');}const value=await r.json();if(!r.ok||value.error)throw Error(value.error||'共享服务请求失败');return value;}
 async function refresh(){if(refreshing)return;refreshing=true;try{cached=await request('state');}catch(e){cached={...cached,device:{...cached.device,connected:false},busy:true,message:'共享服务已断开，请检查提供服务的设备'};}finally{refreshing=false;}}
 function action(name){request(name,{}).then(refresh).catch(e=>emit('toast',e.message));}
 function pick(limit,texture=false){const input=document.createElement('input');input.type='file';input.accept='image/*';input.multiple=!texture&&limit>1;input.onchange=async()=>{if(input.files.length>limit){emit('toast','本次最多选择 '+limit+' 张照片');return;}emit('loading',true);const items=[];try{for(const file of input.files){if(file.size>25*1024*1024)throw Error('单张照片不能超过 25 MB');items.push(await request('upload',file,true));}}catch(e){emit('toast',e.message);}finally{emit(texture?'texture':'photos',items);emit('loading',false);}};input.click();}
 window.Studio={
  state:()=>JSON.stringify(cached),landscape:()=>innerWidth>innerHeight&&innerWidth<1000,
  pick:n=>pick(n),pickTexture:()=>pick(1,true),connect:()=>action('connect'),release:()=>action('release'),airprintLayout:splice=>request('airprint-layout',{splice}).then(refresh).catch(e=>emit('toast',e.message)),
  bluetoothSettings:()=>emit('toast','请在提供服务的设备上打开蓝牙设置'),
  cutout:source=>{setTimeout(()=>request('cutout',{source}).then(v=>emit('cutout',{source,images:v.images})).catch(e=>emit('cutoutError',{source,message:e.message})),0);return '{"ok":true}';},
  printBatch:async payload=>{try{const pages=JSON.parse(payload);const key=pendingPrint.requestId||(pendingPrint.requestId=randomId());const result=await request('print',{requestId:key,pages});await refresh();return JSON.stringify(result);}catch(e){return JSON.stringify({error:e.message});}},
  reconcile:()=>action('reconcile'),cancel:()=>{if(confirm('取消自己的当前打印任务？'))action('cancel');},discardPrepared:()=>action('cancel'),resolveUnknown:()=>emit('toast','请在提供服务的设备上检查并处理未知任务')
 };
 function randomId(){const b=new Uint8Array(16);crypto.getRandomValues(b);return Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');}
 window.BrowserTransport={request,refresh};refresh();setInterval(refresh,1200);
})();
