(()=>{
 if(!window.Studio?.sharingState)return;
 async function open(){const s=JSON.parse(Studio.sharingState()||'{}');const urls=s.running?(s.addresses||[]):[];
  openSheet('sharing','共享打印',s.running?`<p class="hint">同一 Wi-Fi 下的浏览器可访问。关闭共享后，配对失效。</p>${urls.map(u=>`<div class="field"><input readonly value="${esc(u)}" aria-label="访问地址"></div>`).join('')}<p class="hint">配对码</p><p style="font-size:32px;letter-spacing:6px;margin:12px 0">${esc(s.code)}</p>${s.paused?'<p class="hint">队列已暂停，请先检查打印结果。</p><button class="full-button" id="resumeSharing">继续等待中的任务</button>':''}<button class="full-button secondary-button" id="stopSharing">停止共享</button>`:'<p class="hint">浏览器使用同一套编辑器，由这台手机通过蓝牙打印。开启后请保留运行通知。</p><button class="full-button secondary-button" id="startLan">同一 Wi-Fi 共享</button>');
  $('sheetBody').insertAdjacentHTML('beforeend',`<div class="field"><label>AirPrint</label><p class="hint">${s.airprint?esc(s.airprintName)+' · 已开启':'让同一 Wi-Fi 的 iPhone、Mac 从系统打印菜单选择这台手机。仅在可信网络开启。'}${s.airprintError?' · '+esc(s.airprintError):''}</p><button class="full-button secondary-button" id="${s.airprint?'stopAirPrint':'startAirPrint'}">${s.airprint?'关闭 AirPrint':'开启 AirPrint'}</button></div>`);
  if(s.paused&&!s.running)$('sheetBody').insertAdjacentHTML('beforeend','<p class="hint">队列已暂停，请先检查打印结果。</p><button class="full-button" id="resumeSharing">继续等待中的任务</button>');
  for(const input of $('sheetBody').querySelectorAll('input[readonly]'))input.onclick=()=>input.select();
  for(const [id,fn] of [['startAirPrint',()=>Studio.startAirPrint()],['stopAirPrint',()=>Studio.stopAirPrint()],['startLan',()=>Studio.startSharing()],['stopSharing',()=>Studio.stopSharing()],['resumeSharing',()=>Studio.resumeSharing()]])if($(id))$(id).onclick=()=>{fn();closeSheet();toast(id==='stopSharing'?'已停止接收浏览器请求':'正在更新共享服务，请稍后打开查看地址');};
 }
 const menu=$('menuBtn').onclick;$('menuBtn').onclick=()=>{menu();$('sheetBody').insertAdjacentHTML('beforeend','<button class="menu-row" id="sharingMenu">共享打印</button>');$('sharingMenu').onclick=open;};
})();
