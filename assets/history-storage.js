/* Explicit cleanup of this browser owner's completed desktop print files. */
(()=>{
 if(!window.BrowserTransport)return;
 const keep=()=>[...new Set([...state.photos.flatMap(p=>[p.src,p.coatSource]),state.coatSource].filter(v=>typeof v==='string'&&/^\/private\/prints\/[a-f0-9-]+\.jpg$/.test(v)))];
 const previous=openHistory;
 window.openHistory=function(){previous();if(native.host!=='desktop')return;
  $('sheetBody').insertAdjacentHTML('afterbegin','<div class="field" id="historyStorage"><p class="hint" role="status">正在计算可清理空间…</p><button class="full-button secondary-button" disabled>清理历史打印文件</button></div>');
  const row=$('historyStorage'),button=row.querySelector('button'),status=row.querySelector('p');
  BrowserTransport.request('history/storage',{keepFiles:keep()}).then(value=>{if(!row.isConnected)return;status.textContent=`可清理 ${(value.bytes/1048576).toFixed(1)} MB · ${value.files} 个打印文件`;button.disabled=!value.files;}).catch(e=>{if(row.isConnected)status.textContent=e.message;});
  button.onclick=async()=>{
   if(!confirm('清理本人已结束作品的打印图片及覆膜文件？简要记录和原始导入照片保留，但作品预览、原样重印及其他页面对这些历史图片的引用将失效。当前页面正在使用的图片会跳过。'))return;
   button.disabled=true;
   try{const result=await BrowserTransport.request('history/clear',{confirmed:true,keepFiles:keep()});await BrowserTransport.refresh(true);poll();if(sheetKind==='history')openHistory();toast(`已释放 ${(result.bytes/1048576).toFixed(1)} MB`+(result.pending?'，部分文件未能清理，可稍后重试':''));}
   catch(e){status.textContent=e.message;button.disabled=false;}
  };
 };
})();
