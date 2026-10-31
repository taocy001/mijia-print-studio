(()=>{
 const controls=!!window.Studio?.sharingState;if(!controls&&!window.BrowserTransport)return;
 let signature='',loading=false;
 function render(s){
  const urls=[...new Set([...(s.addresses||[]),s.current].filter(u=>{try{return new URL(u).protocol==='http:';}catch(e){return false;}}))];
  let html=s.running?`<p class="hint">${s.lan?'同一 Wi-Fi 下的浏览器可访问。':'服务仅允许本机访问。'}${controls?'关闭共享后，配对失效。':''}</p>`:'<p class="hint">浏览器使用同一套编辑器，由这台手机通过蓝牙打印。开启后请保留运行通知。</p>';
  html+=urls.map((u,i)=>`<div class="share-address"><label for="shareAddress${i}">${/\/\/(127\.|localhost)/.test(u)?'本机地址':'共享打印 HTTP 地址'}</label><input id="shareAddress${i}" readonly value="${esc(u)}" aria-label="共享打印 HTTP 地址"><button data-copy-address="${i}">复制</button></div>`).join('');
  if(s.running&&!urls.length)html+='<p class="hint">暂未获取到 Wi-Fi 地址，请检查服务设备的网络连接。</p>';
  if(controls){
   if(s.running)html+=`<p class="hint">配对码</p><p style="font-size:32px;letter-spacing:6px;margin:12px 0">${esc(s.code)}</p><button class="full-button secondary-button" id="stopSharing">停止 Wi-Fi 共享</button>`;
   else html+='<button class="full-button secondary-button" id="startLan">开启同一 Wi-Fi 共享</button>';
   html+=`<div class="field"><label>AirPrint</label><p class="hint">${s.airprint?esc(s.airprintName)+' · 已开启':'让同一 Wi-Fi 的 iPhone、Mac 从系统打印菜单选择这台手机。仅在可信网络开启。'}${s.airprintError?' · '+esc(s.airprintError):''}</p><button class="full-button secondary-button" id="${s.airprint?'stopAirPrint':'startAirPrint'}">${s.airprint?'关闭 AirPrint':'开启 AirPrint'}</button></div>`;
   if(s.paused)html+='<p class="hint">队列已暂停，请先检查打印结果。</p><button class="full-button" id="resumeSharing">继续等待中的任务</button>';
  }else html+=`<p class="hint">其他设备打开共享地址后，输入服务设备显示的配对码。${s.airprint?'AirPrint 已开启。':''}共享开关由服务设备管理。</p>`;
  openSheet('sharing','共享打印',html);
  for(const input of $('sheetBody').querySelectorAll('input[readonly]'))input.onclick=()=>input.select();
  $('sheetBody').querySelectorAll('[data-copy-address]').forEach(button=>button.onclick=async()=>{const input=$('shareAddress'+button.dataset.copyAddress);try{if(navigator.clipboard?.writeText)await navigator.clipboard.writeText(input.value);else{input.select();if(!document.execCommand('copy'))throw Error();}toast('地址已复制');}catch(e){input.focus();input.select();toast('地址已选中，可长按或使用复制快捷键');}});
  if(controls)for(const [id,fn] of [['startAirPrint',()=>Studio.startAirPrint()],['stopAirPrint',()=>Studio.stopAirPrint()],['startLan',()=>Studio.startSharing()],['stopSharing',()=>Studio.stopSharing()],['resumeSharing',()=>Studio.resumeSharing()]])if($(id))$(id).onclick=async()=>{const button=$(id);button.disabled=true;try{await fn();await refresh(true);}catch(e){toast('设置未完成，请重试');}finally{if(button.isConnected)button.disabled=false;}};
 }
 async function refresh(force=false){if(loading||sheetKind!=='sharing')return;loading=true;try{const s=controls?JSON.parse(Studio.sharingState()||'{}'):await BrowserTransport.request('sharing');if(sheetKind!=='sharing')return;const next=JSON.stringify(s);if(force||next!==signature){signature=next;render(s);}}catch(e){if(sheetKind==='sharing'&&force)openSheet('sharing','共享打印','<p class="hint">共享状态读取失败，请检查服务连接后重新打开。</p>');}finally{loading=false;}}
 function open(){signature='';openSheet('sharing','共享打印','<p class="hint">正在读取共享地址…</p>');refresh(true);}
 const menu=$('menuBtn').onclick;$('menuBtn').onclick=()=>{menu();$('sheetBody').insertAdjacentHTML('beforeend','<button class="menu-row" id="sharingMenu">共享打印与地址</button>');$('sharingMenu').onclick=open;};
 setInterval(()=>refresh(),1200);
})();
