(()=>{
 const controls=!!window.Studio?.sharingState;if(!controls&&!window.BrowserTransport)return;
 let signature='',loading=false;
 function render(s){
  const urls=[...new Set([...(s.addresses||[]),s.current].filter(u=>{try{return new URL(u).protocol==='http:';}catch(e){return false;}}))];
  let html=s.running?`<p class="hint">${s.lan?'同一 Wi-Fi 下的浏览器可访问。':'服务仅允许本机访问。'}已配对浏览器会记住连接，服务重启后无需重新配对。</p>`:'<p class="hint">浏览器使用同一套编辑器，由这台手机通过蓝牙打印。开启后请保留运行通知。</p>';
  if(s.name||s.airprintName)html+=`<div class="info-row"><span>共享服务</span><strong>${esc(s.name||s.airprintName)}</strong></div>`;
  if(s.running&&/^\d{6}$/.test(String(s.code||'')))html+=`<div class="share-address"><label for="sharePairingCode">配对码 · 可转告其他设备</label><input id="sharePairingCode" readonly value="${esc(s.code)}" aria-label="配对码"><button id="copyPairingCode">复制配对码</button></div>`;
  html+=urls.map((u,i)=>`<div class="share-address"><label for="shareAddress${i}">${/\/\/(127\.|localhost)/.test(u)?'本机地址':'共享打印 HTTP 地址'}</label><input id="shareAddress${i}" readonly value="${esc(u)}" aria-label="共享打印 HTTP 地址"><button data-copy-address="${i}">复制</button></div>`).join('');
  if(s.running&&!urls.length)html+='<p class="hint">暂未获取到 Wi-Fi 地址，请检查服务设备的网络连接。</p>';
  if(controls){
   if(s.running)html+=`<button class="full-button secondary-button" id="stopSharing">停止 Wi-Fi 共享</button>`;
   else html+='<button class="full-button secondary-button" id="startLan">开启同一 Wi-Fi 共享</button>';
   html+=`<div class="field"><label>AirPrint</label><p class="hint">${s.airprint?esc(s.airprintName)+(s.airprintReady?' · 可以接收打印':' · 暂不可用'):'让同一 Wi-Fi 的 iPhone、Mac 从系统打印菜单选择这台手机。仅在可信网络开启。'}${s.airprintError?' · '+esc(s.airprintError):''}</p><button class="full-button secondary-button" id="${s.airprint?'stopAirPrint':'startAirPrint'}">${s.airprint?'关闭 AirPrint':'开启 AirPrint'}</button></div>`;
   if(s.airprint&&!s.airprintReady&&!s.paused)html+=printerDetectionButton('connectSharedPrinter');
   if(s.paused)html+='<p class="hint">队列已暂停，请先检查打印结果。</p><button class="full-button" id="resumeSharing">继续等待中的任务</button>';
  }else html+=`<p class="hint">其他设备打开共享地址后，输入配对码即可连接。${s.airprint?(s.airprintReady?'AirPrint 可以接收打印。':'AirPrint 暂不可用。'):''}共享开关由服务设备管理。</p>`;
  if(s.canManagePairing&&(!controls||typeof Studio.resetPairing==='function'))html+='<button class="full-button secondary-button" id="resetPairing">重置配对</button>';
  openSheet('sharing','共享打印',html);
  for(const input of $('sheetBody').querySelectorAll('input[readonly]'))input.onclick=()=>input.select();
  async function copy(input,label){try{if(navigator.clipboard?.writeText)await navigator.clipboard.writeText(input.value);else{input.focus();input.select();if(!document.execCommand('copy'))throw Error();}toast(label+'已复制');}catch(e){input.focus();input.select();toast(label+'已选中，可长按或使用复制快捷键');}}
  $('sheetBody').querySelectorAll('[data-copy-address]').forEach(button=>button.onclick=()=>copy($('shareAddress'+button.dataset.copyAddress),'地址'));
  if($('copyPairingCode'))$('copyPairingCode').onclick=()=>copy($('sharePairingCode'),'配对码');
  if($('resetPairing'))$('resetPairing').onclick=async()=>{if(!confirm('更换配对码并取消其他浏览器的访问授权？照片和打印记录会保留。'))return;const button=$('resetPairing');button.disabled=true;try{const result=controls?await Studio.resetPairing():await BrowserTransport.request('admin/pairing/reset',{});const value=typeof result==='string'?JSON.parse(result||'{}'):result;if(value?.error)throw Error(value.error);await refresh(true);toast('配对已重置，请使用新的配对码');}catch(e){toast(e.message||'重置未完成，请重试');}finally{if(button.isConnected)button.disabled=false;}};
  if($('connectSharedPrinter'))$('connectSharedPrinter').onclick=event=>detectPrinter(event.currentTarget);
  if(controls)for(const [id,fn] of [['startAirPrint',()=>Studio.startAirPrint()],['stopAirPrint',()=>Studio.stopAirPrint()],['startLan',()=>Studio.startSharing()],['stopSharing',()=>Studio.stopSharing()],['resumeSharing',()=>Studio.resumeSharing()]])if($(id))$(id).onclick=async()=>{const button=$(id);button.disabled=true;try{await fn();await refresh(true);}catch(e){toast('设置未完成，请重试');}finally{if(button.isConnected)button.disabled=false;}};
 }
 async function refresh(force=false){if(loading||sheetKind!=='sharing')return;loading=true;try{const s=controls?JSON.parse(Studio.sharingState()||'{}'):await BrowserTransport.request('sharing');if(sheetKind!=='sharing')return;const next=JSON.stringify([s,!!native.busy,!!native.unresolved,detectionPending]);if(force||next!==signature){signature=next;render(s);}}catch(e){if(sheetKind==='sharing'&&force)openSheet('sharing','共享打印','<p class="hint">共享状态读取失败，请检查服务连接后重新打开。</p>');}finally{loading=false;}}
 function open(){signature='';openSheet('sharing','共享打印','<p class="hint">正在读取共享地址…</p>');refresh(true);}
 const menu=$('menuBtn').onclick;$('menuBtn').onclick=()=>{menu();$('sheetBody').insertAdjacentHTML('beforeend',`<button class="menu-row" id="sharingMenu">${icon('share')}<span>共享打印</span>${icon('chevron')}</button>`);$('sharingMenu').onclick=open;};
 window.addEventListener('studio-state',()=>refresh());
 setInterval(()=>refresh(),1200);
})();
