/* Desktop models are shared by paired clients; only the host can download. */
(()=>{
 if(!window.BrowserTransport)return;
 const labels={missing:'未下载',invalid:'文件校验失败',unreadable:'文件无法读取',verified:'文件已校验',downloading:'正在下载',failed:'下载失败'};
 let loading=false;
 async function refresh(){
  if(loading||sheetKind!=='models'||native.capabilities?.models!==true)return;loading=true;
  try{
   const value=await BrowserTransport.request('models');if(sheetKind!=='models')return;
   $('modelRuntime').textContent=value.runtime?'模型在提供服务的电脑上离线运行':'推理运行库不可用，请在电脑上重新安装项目依赖';
   $('modelAccess').textContent=value.canManage?'':'下载或重试请在提供服务的电脑本机打开网页';
   for(const model of value.models){
    let row=$('model-'+model.id);
    if(!row){row=document.createElement('div');row.className='field';row.id='model-'+model.id;row.innerHTML=`<strong>${esc(model.name)}</strong><p class="hint" role="status"></p><button class="full-button secondary-button"></button>`;$('modelList').appendChild(row);}
    row.querySelector('p').textContent=model.error||((labels[model.state]||'状态未知')+(model.state==='downloading'?' · '+(model.bytes/1048576).toFixed(1)+' MB':''));
    const button=row.querySelector('button');button.hidden=!value.canManage||model.state==='verified';button.disabled=model.state==='downloading';button.textContent=model.state==='downloading'?'下载中…':model.state==='failed'||model.state==='invalid'?'重试下载':'下载模型';
    button.onclick=async()=>{button.disabled=true;try{await BrowserTransport.request('admin/models',{id:model.id});}catch(e){toast(e.message);}finally{await refresh();}};
   }
  }catch(e){if(sheetKind==='models')$('modelRuntime').textContent=e.message||'模型状态读取失败';}
  finally{loading=false;}
 }
 function available(){return native.host==='desktop'&&native.capabilities?.models===true;}
 function open(){if(!available())return;openSheet('models','离线模型','<p class="hint" id="modelRuntime">正在读取…</p><div id="modelList"></div><p class="hint" id="modelAccess"></p>');refresh();}
 window.ModelManager={available,open};
 const back=$('settingsBack').onclick;$('settingsBack').onclick=()=>{if(sheetKind==='models')openLayout();else back();};
 setInterval(refresh,1200);
})();
