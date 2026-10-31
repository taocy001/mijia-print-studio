/* Additional tools stay inside the existing drawers. */
window.StudioExtras=(()=>{
 const cards=[['reading','阅读打卡'],['habit','积分卡'],['todo','每日计划'],['schedule','课程表'],['luggage','行李牌'],['praise','鼓励卡'],['invite','邀请卡']];
 const textures=[['','无纹理'],['dots','微点'],['lines','细纹'],['grid','格纹'],['hearts','爱心'],['custom','自选图片']];
 const setting=()=>['label','card'].includes(state.mode)||(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014))?state:active()||state;
 function openCoat(){const p=setting();openSheet('coat','覆膜',`<div class="mode-grid">${textures.map(([id,name])=>`<button data-coat="${id}" class="${(p.coatTexture||'')===id?'selected':''}">${name}</button>`).join('')}</div><label class="layer-range">纹理深浅<output id="coatValue">${p.coatThreshold||100}</output><input id="coatThreshold" type="range" min="60" max="140" value="${p.coatThreshold||100}"></label><p class="hint">纹理与隐藏文字、表情一起印入覆膜，侧光下可见。编辑画面以金色示意，最终照片颜色层不包含这些内容。覆膜会增加耗材用量。</p>`);
 $('sheetBody').querySelectorAll('[data-coat]').forEach(b=>b.onclick=()=>{if(b.dataset.coat==='custom'){bridge('pickTexture');return;}p.coatTexture=b.dataset.coat;schedule();openCoat();});$('coatThreshold').oninput=e=>{p.coatThreshold=+e.target.value;$('coatValue').value=e.target.value;save();};}
 function pattern(ctx,w,h,p){const kind=p?.coatTexture;if(!kind)return;ctx.save();ctx.fillStyle='white';ctx.strokeStyle='white';ctx.lineWidth=3;
  if(kind==='custom'&&images.has(p.coatSource)){const c=document.createElement('canvas');c.width=w;c.height=h;const m=c.getContext('2d');m.drawImage(images.get(p.coatSource),0,0,w,h);const d=m.getImageData(0,0,w,h);for(let i=0;i<d.data.length;i+=4){const v=.299*d.data[i]+.587*d.data[i+1]+.114*d.data[i+2]>=100?255:0;d.data[i]=d.data[i+1]=d.data[i+2]=255;d.data[i+3]=v;}m.putImageData(d,0,0);ctx.drawImage(c,0,0);}
  else for(let y=18;y<h;y+=48)for(let x=18;x<w;x+=48){if(kind==='dots'){ctx.beginPath();ctx.arc(x,y,4,0,Math.PI*2);ctx.fill();}else if(kind==='hearts'){ctx.font='18px sans-serif';ctx.fillText('♥',x,y);}else if(kind==='lines'||kind==='grid'){ctx.fillRect(x,y,2,48);if(kind==='grid')ctx.fillRect(x,y,48,2);}}
  ctx.restore();
 }
 function paintCoat(ctx,w,h,frames,mode){if(!['mask','editor'].includes(mode))return;ctx.save();if(mode==='editor'){ctx.globalAlpha=.3;ctx.globalCompositeOperation='screen';}
  if(!['label','card'].includes(state.mode)&&!(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014))&&(state.media===5014||state.mode==='collage'))for(const f of frames){ctx.save();ctx.beginPath();ctx.rect(f.x,f.y,f.w,f.h);ctx.clip();ctx.translate(f.x,f.y);pattern(ctx,f.w,f.h,f.p);ctx.restore();}
  else pattern(ctx,w,h,setting());ctx.restore();
 }
 function openPrintOptions(){openSheet('printOptions','打印设置',`<div class="field"><label>每个作品的份数</label><input id="extraCopies" type="number" min="1" max="10" value="${state.copies||1}"></div><p class="hint">预览时会列出作品和实际相纸总数，确认后才打印。</p>`);$('extraCopies').onchange=e=>{state.copies=Math.max(1,Math.min(10,Math.round(+e.target.value)||1));e.target.value=state.copies;save();};}
 function drawCard(ctx,x,y,w,h){CardArt.draw(ctx,x,y,w,h);}
 function drawIdCardSheet(ctx,w,h){
  const vertical=state.idCardOrientation==='portrait',ow=vertical?686:1059,oh=vertical?1059:686;
  const first=active(),last=first;
  function place(p,x,y,scale=1,bottom=h){const pw=Math.round(ow*scale),ph=Math.round(oh*scale),bleed=Math.round(24*scale),cw=Math.round((vertical?638:1011)*scale),ch=Math.round((vertical?1011:638)*scale);
   drawPhoto(ctx,p,x,y,pw,ph,'cover');ctx.strokeStyle='#475569';ctx.lineWidth=2;ctx.strokeRect(x+bleed,y+bleed,cw-1,ch-1);
   if(y+ph+42<=bottom)text(ctx,vertical?'竖版成品 · 实线裁切':'实线内成品85.6×53.98mm · 四边2mm出血',x+pw/2,y+ph+27,19,'#64748B');
  }
  function single(p,y,areaH){const scale=vertical?Math.min(1,(w-20)/ow,(areaH-20)/oh):1;place(p,Math.floor((w-Math.round(ow*scale))/2),y+Math.floor((areaH-Math.round(oh*scale))/2),scale,y+areaH);}
  if(state.media===5014){single(first,0,h/2);single(last,h/2,h/2);}
  else if(vertical&&w>h){const x=Math.floor((w-ow*2-90)/2),y=Math.max(20,Math.floor((h-oh-50)/2));place(first,x,y);place(last,x+ow+90,y);}
  else if(!vertical&&h>w){const x=Math.floor((w-ow)/2),y=Math.floor((h-oh*2-90)/2);place(first,x,y);place(last,x,y+oh+90);}
  else single(first,0,h);
 }
 const originalLayout=openLayout;
 openLayout=function(){originalLayout();const body=$('sheetBody');
  if(state.mode==='calendar')body.insertAdjacentHTML('beforeend',`<div class="field"><label>月历版式</label>${state.media===5014?'上半本月、下半下月':segments('calendarLayout',[['photo','照片月历'],['plain','纯月历']])}</div><label class="coat-switch"><span>农历与节气</span><input id="lunarToggle" type="checkbox" ${state.lunar?'checked':''}></label>`);
  if(state.mode==='collage')body.insertAdjacentHTML('beforeend',`<div class="field"><label>拼图布局</label>${segments('collageLayout',[['auto','自动'],['vertical','上下'],['horizontal','左右'],['grid','网格']])}</div>`);
  if(state.mode==='label')body.insertAdjacentHTML('beforeend',`<div class="field"><label>姓名贴间隙 <span id="nameGapValue">${state.nameGap==null?'默认':state.nameGap+' mm'}</span></label><input id="nameGapInput" type="range" min="0" max="5" step="0.1" value="${state.nameGap??1.5}"><button id="resetNameGap" class="secondary-button">恢复默认间隙</button></div><div class="field"><label>姓名贴风格</label><div id="nameTemplateChoices">${NameLabels.options()}</div></div><button id="extraText" class="full-button secondary-button">编辑姓名与小字</button>`);
  if(state.mode==='card')body.insertAdjacentHTML('beforeend',`<div class="field"><label>卡片类型</label>${CardArt.options()}</div><button id="extraText" class="full-button secondary-button">编辑标题与副文字</button>`);

  if(state.mode==='idcard')body.insertAdjacentHTML('beforeend',`<div class="field"><label>卡片方向</label>${segments('idCardOrientation',[['portrait','竖版'],['landscape','横版']])}</div><p class="hint">成品 85.6 × 53.98 mm，实线外预留 2 mm 出血。</p>`);
  if(state.mode==='calendar')body.insertAdjacentHTML('beforeend','<p class="hint">调休标记数据覆盖 2004–2026 年；其他年份不推测法定休息日。</p>');
  if($('nameGapInput'))$('nameGapInput').oninput=e=>{state.nameGap=+e.target.value;$('nameGapValue').textContent=state.nameGap+' mm';schedule();clearTimeout(window.nameChoiceTimer);window.nameChoiceTimer=setTimeout(()=>{if($('nameTemplateChoices'))$('nameTemplateChoices').innerHTML=NameLabels.options();},150);};
  if($('resetNameGap'))$('resetNameGap').onclick=()=>{delete state.nameGap;schedule();openLayout();};
  if($('extraText'))$('extraText').onclick=openLegacyText;if($('lunarToggle'))$('lunarToggle').onchange=e=>{state.lunar=e.target.checked;schedule();};

 };
 const originalMenu=$('menuBtn').onclick;$('menuBtn').onclick=()=>{originalMenu();$('sheetBody').insertAdjacentHTML('beforeend','<button class="menu-row" id="menuPrintOptions">打印设置</button><button class="menu-row" id="menuCoat">覆膜纹理</button>');$('menuPrintOptions').onclick=openPrintOptions;$('menuCoat').onclick=openCoat;};
 const oldNative=window.nativeEvent;window.nativeEvent=async e=>{if(e.type==='texture'){const p=e.value[0];if(p){await loadPhoto(p);Object.assign(setting(),{coatTexture:'custom',coatSource:p.src});schedule();openCoat();}}else await oldNative(e);};
 for(const p of [...state.photos,state])if(p.coatSource)loadPhoto({src:p.coatSource}).then(schedule).catch(()=>{});
 const photoTemplates=$('templateBtn').onclick,photoText=$('addTextQuick').onclick;
 $('templateBtn').onclick=()=>['label','card'].includes(state.mode)?openLayout():photoTemplates();
 $('addTextQuick').onclick=()=>['label','card'].includes(state.mode)?openLegacyText():photoText();
 return {paintCoat,drawCard,drawIdCardSheet,openCoat,openPrintOptions};
})();

{
 const menu=$('menuBtn').onclick;
 $('menuBtn').onclick=()=>{menu();$('sheetBody').insertAdjacentHTML('beforeend','<button class="menu-row" id="artCredits">素材与许可</button>');$('artCredits').onclick=()=>openSheet('credits','素材与许可','<p>原创模板、姓名贴和卡片：留影工坊，MIT。</p><p>表情：Twemoji 14.0.2，Twitter, Inc. and other contributors，CC BY 4.0，使用未修改的上游图形。</p><p>github.com/twitter/twemoji · creativecommons.org/licenses/by/4.0/</p><p>字体：ZCOOL KuaiLe、Ma Shan Zheng，SIL OFL 1.1。</p><p>协议参考：xiaomi-photo-printer，MIT。抠图：U2NetP（Apache-2.0）、rembg 与 ONNX Runtime（MIT）。</p><p>完整许可随源码和安装包 assets 目录提供。本项目与设备厂商无隶属或背书关系。</p>');};
}
