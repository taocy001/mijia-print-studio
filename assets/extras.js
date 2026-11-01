/* Additional tools stay inside the existing drawers. */
window.StudioExtras=(()=>{
 const cards=[['reading','阅读打卡'],['habit','积分卡'],['todo','每日计划'],['schedule','课程表'],['luggage','行李牌'],['praise','鼓励卡'],['invite','邀请卡']];
 const textures=[['','高亮覆膜'],['dots','微点'],['lines','细纹'],['grid','格纹'],['hearts','爱心'],['diagonal','斜纹'],['waves','波纹'],['sparkles','星芒'],['custom','自选图片']];
 const setting=()=>['label','card'].includes(state.mode)||(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014))?state:active()||state;
 function openCoat(){const p=setting(),strength=state.mode==='collage'?(state.photos[0]||p):p;openSheet('coat','覆膜',`<div class="mode-grid">${textures.map(([id,name])=>`<button data-coat="${id}" class="${(p.coatTexture||'')===id?'selected':''}" aria-pressed="${(p.coatTexture||'')===id}"><canvas width="96" height="64" style="width:48px;height:32px;border-radius:4px" aria-hidden="true"></canvas><span>${name}</span></button>`).join('')}</div><label class="layer-range">${state.mode==='collage'?'整页纹理深浅':'纹理深浅'}<output id="coatValue">${strength.coatThreshold||100}</output><input id="coatThreshold" type="range" min="60" max="140" value="${strength.coatThreshold||100}"></label>`);
 $('sheetBody').querySelectorAll('[data-coat]').forEach(b=>{const ctx=b.querySelector('canvas').getContext('2d'),kind=b.dataset.coat;ctx.fillStyle='#34363b';if(!kind){const g=ctx.createLinearGradient(0,0,96,64);g.addColorStop(0,'#34363b');g.addColorStop(.45,'#8b9097');g.addColorStop(1,'#34363b');ctx.fillStyle=g;}ctx.fillRect(0,0,96,64);if(kind==='custom'&&!images.has(p.coatSource)){ctx.strokeStyle='#ddd';ctx.lineWidth=2.5;ctx.strokeRect(27.5,15,41,34);ctx.beginPath();ctx.moveTo(27.5,44);ctx.lineTo(40,30);ctx.lineTo(52.5,40);ctx.lineTo(60,33);ctx.lineTo(68.5,42.5);ctx.stroke();}else pattern(ctx,96,64,{...p,coatTexture:kind});});
 $('sheetBody').querySelectorAll('[data-coat]').forEach(b=>b.onclick=()=>{if(b.dataset.coat==='custom'){bridge('pickTexture');return;}p.coatTexture=b.dataset.coat;schedule();openCoat();});$('coatThreshold').oninput=e=>{strength.coatThreshold=+e.target.value;$('coatValue').value=e.target.value;save();};}
 function pattern(ctx,w,h,p){const kind=p?.coatTexture;if(!kind)return;ctx.save();ctx.fillStyle='white';ctx.strokeStyle='white';ctx.lineWidth=3;
  if(kind==='custom'&&images.has(p.coatSource)){const c=document.createElement('canvas');c.width=w;c.height=h;const m=c.getContext('2d');m.drawImage(images.get(p.coatSource),0,0,w,h);const d=m.getImageData(0,0,w,h);for(let i=0;i<d.data.length;i+=4){const v=.299*d.data[i]+.587*d.data[i+1]+.114*d.data[i+2]>=100?255:0;d.data[i]=d.data[i+1]=d.data[i+2]=255;d.data[i+3]=v;}m.putImageData(d,0,0);ctx.drawImage(c,0,0);}
  else if(kind==='diagonal'){ctx.lineWidth=2;for(let x=-h;x<w;x+=48){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x+h,h);ctx.stroke();}}
  else if(kind==='waves'){ctx.lineWidth=2;for(let y=24;y<h+16;y+=64){ctx.beginPath();ctx.moveTo(-48,y);for(let x=-48;x<w;x+=96)ctx.bezierCurveTo(x+24,y-14,x+72,y+14,x+96,y);ctx.stroke();}}
  else if(kind==='sparkles'){for(let row=0,y=28;y<h;y+=72,row++)for(let x=28+(row%2)*36;x<w;x+=72){const r=7;ctx.beginPath();for(const [i,[dx,dy]] of [[0,-1],[.22,-.22],[1,0],[.22,.22],[0,1],[-.22,.22],[-1,0],[-.22,-.22]].entries()){if(i)ctx.lineTo(x+dx*r,y+dy*r);else ctx.moveTo(x+dx*r,y+dy*r);}ctx.closePath();ctx.fill();}}
  else for(let y=18;y<h;y+=48)for(let x=18;x<w;x+=48){if(kind==='dots'){ctx.beginPath();ctx.arc(x,y,4,0,Math.PI*2);ctx.fill();}else if(kind==='hearts'){ctx.font='18px sans-serif';ctx.fillText('♥',x,y);}else if(kind==='lines'||kind==='grid'){ctx.fillRect(x,y,2,48);if(kind==='grid')ctx.fillRect(x,y,48,2);}}
  ctx.restore();
 }
 function paintCoat(ctx,w,h,frames,mode){if(!['mask','editor'].includes(mode))return;ctx.save();if(mode==='editor'){ctx.globalAlpha=.3;ctx.globalCompositeOperation='screen';}
  if(!['label','card'].includes(state.mode)&&!(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014))&&(state.media===5014||state.mode==='collage'))for(const f of frames){ctx.save();ctx.beginPath();ctx.rect(f.x,f.y,f.w,f.h);ctx.clip();ctx.translate(f.x,f.y);pattern(ctx,f.w,f.h,f.p);ctx.restore();}
  else pattern(ctx,w,h,setting());ctx.restore();
 }

 function drawCard(ctx,x,y,w,h){CardArt.draw(ctx,x,y,w,h);}
 function idCardCapacity(){const [w,h]=logicalSize(),vertical=state.idCardOrientation==='portrait';return state.media===5014||(vertical&&w>h)||(!vertical&&h>w)?2:1;}
 function drawIdCardSheet(ctx,w,h){
  const vertical=state.idCardOrientation==='portrait',ow=vertical?686:1059,oh=vertical?1059:686;
  const start=Math.floor(state.active/idCardCapacity())*idCardCapacity(),first=state.photos[start]||active(),last=state.photos[start+1]||first;
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
  if(state.mode==='collage')body.insertAdjacentHTML('beforeend',`<div class="field"><label>拼图布局</label>${segments('collageLayout',state.media===5014?[['strip','照片条']]:[['auto','自动'],['vertical','上下'],['horizontal','左右'],['grid','网格'],['strip','照片条']])}</div>`);
  if(state.mode==='label')body.insertAdjacentHTML('beforeend',`<div class="field"><label>姓名贴间隙 <span id="nameGapValue">${state.nameGap==null?'默认':state.nameGap+' mm'}</span></label><input id="nameGapInput" type="range" min="0" max="5" step="0.1" value="${state.nameGap??1.5}"><button id="resetNameGap" class="secondary-button">恢复默认间隙</button></div><div class="field"><label>姓名贴风格</label><div id="nameTemplateChoices">${NameLabels.options()}</div></div><button id="extraText" class="full-button secondary-button">编辑姓名与小字</button>`);
  if(state.mode==='card')body.insertAdjacentHTML('beforeend',`<div class="field"><label>卡片类型</label>${CardArt.options()}</div><button id="extraText" class="full-button secondary-button">编辑标题与副文字</button>`);

  if(state.mode==='idcard')body.insertAdjacentHTML('beforeend',`<div class="field"><label>卡片方向</label>${segments('idCardOrientation',[['portrait','竖版'],['landscape','横版']])}</div><p class="hint">成品 85.6 × 53.98 mm，实线外预留 2 mm 出血。</p>`);
  if(state.mode==='calendar')body.insertAdjacentHTML('beforeend','<p class="hint">调休标记数据覆盖 2004–2026 年；其他年份不推测法定休息日。</p>');
  if($('nameGapInput'))$('nameGapInput').oninput=e=>{state.nameGap=+e.target.value;$('nameGapValue').textContent=state.nameGap+' mm';schedule();clearTimeout(window.nameChoiceTimer);window.nameChoiceTimer=setTimeout(()=>{if($('nameTemplateChoices'))$('nameTemplateChoices').innerHTML=NameLabels.options();},150);};
  if($('resetNameGap'))$('resetNameGap').onclick=()=>{delete state.nameGap;schedule();openLayout();};
  if($('extraText'))$('extraText').onclick=openLegacyText;if($('lunarToggle'))$('lunarToggle').onchange=e=>{state.lunar=e.target.checked;schedule();};

 };
 const originalMenu=$('menuBtn').onclick;$('menuBtn').onclick=()=>{originalMenu();$('sheetBody').insertAdjacentHTML('beforeend',`<div class="menu-row copies-row">${icon('copy')}<span>打印份数</span><div class="copies-stepper"><button id="copiesMinus" aria-label="减少打印份数">${icon('minus')}</button><output id="copiesValue" aria-live="polite"></output><button id="copiesPlus" aria-label="增加打印份数">${icon('plus')}</button></div></div><button class="menu-row" id="menuCoat">${icon('spark')}<span>覆膜纹理</span>${icon('chevron')}</button>`);
  const update=()=>{const n=Math.max(1,Math.min(10,Math.round(+state.copies)||1));$('copiesValue').value=n;$('copiesMinus').disabled=n===1;$('copiesPlus').disabled=n===10;};
  for(const [id,step] of [['copiesMinus',-1],['copiesPlus',1]])$(id).onclick=()=>{state.copies=Math.max(1,Math.min(10,(Math.round(+state.copies)||1)+step));update();schedule();};update();$('menuCoat').onclick=openCoat;};
 const oldNative=window.nativeEvent;window.nativeEvent=async e=>{if(e.type==='texture'){const p=e.value[0];if(p){await loadPhoto(p);Object.assign(setting(),{coatTexture:'custom',coatSource:p.src});schedule();openCoat();}}else await oldNative(e);};
 for(const p of [...state.photos,state])if(p.coatSource)loadPhoto({src:p.coatSource}).then(schedule).catch(()=>{});
 const photoTemplates=$('templateBtn').onclick,photoText=$('addTextQuick').onclick;
 $('templateBtn').onclick=()=>['label','card'].includes(state.mode)?openLayout():photoTemplates();
 $('addTextQuick').onclick=()=>['label','card'].includes(state.mode)?openLegacyText():photoText();
 return {paintCoat,drawCard,drawIdCardSheet,idCardCapacity,openCoat};
})();
