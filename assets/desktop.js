/* Desktop inspector reuses the same editors without opening the mobile effect rail. */
(()=>{
 if(!window.BrowserTransport)return;
 const media=matchMedia('(min-width:1000px) and (pointer:fine)'),sheet=$('sheet');
 const open=openSheet,close=closeSheet;let frame=0,last='templates',photo=null,type='',template='',started=false;
 const settings=new Set(['menu','device','paper','sharing','coat','workType','history','historyDetail','hostQueue','job','models','qr','camera']);
 const tools=document.createElement('div');tools.id='desktopPaperTools';tools.innerHTML=`<button id="desktopPaperSize" title="选择相纸与拼接方式"></button><span id="desktopWorkTarget"></span><div id="desktopDirection" role="group" aria-label="当前作品方向">${[['portrait','竖版'],['landscape','横版']].map(([id,name])=>`<button data-desktop-direction="${id}" aria-pressed="false">${name}</button>`).join('')}</div>`;$('printBtn').before(tools);
 $('desktopPaperSize').onclick=openPaper;
 tools.querySelectorAll('[data-desktop-direction]').forEach(b=>b.onclick=()=>setPaperOrientation(b.dataset.desktopDirection));
 function refreshPaperTools(){
  tools.hidden=!media.matches;const split=!!window.PhotoWorks?.split(),supported=state.media===5012||split;
  $('desktopPaperSize').textContent=state.media===5014?'4 寸拼接':state.media===5009?'3 寸方形':'6 寸相纸';
  $('desktopWorkTarget').textContent=PhotoFlow.enabled()?(split?`${PhotoWorks.splitHorizontal()?(state.active%2?'右':'左'):(state.active%2?'下':'上')}幅 · `:'')+`照片 ${state.photos.length?state.active+1:'未添加'}`:'';
  $('desktopDirection').hidden=!supported;
  tools.querySelectorAll('[data-desktop-direction]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.desktopDirection===(split?state.splitLayout:state.orientation==='auto'?(logicalSize()[0]>logicalSize()[1]?'landscape':'portrait'):state.orientation||'portrait'))));
 }
 const back=$('settingsBack'),family=()=>PhotoFlow.enabled()?'photo':state.mode;
 function mark(){
  const kind=sheet.hidden?'':sheetKind,title=$('sheetTitle').textContent;
  const activeId=kind==='templates'?'templateBtn':kind==='filters'?'filterBtn':kind==='text'?'addTextQuick':kind==='layers'?(title.includes('表情')&&!title.includes('文字')?'addEmojiQuick':'addTextQuick'):'';
  for(const id of ['templateBtn','filterBtn','addTextQuick','addEmojiQuick'])$(id).setAttribute('aria-pressed',String(id===activeId));
 }
 function remember(){photo=active();type=family();template=PhotoFlow.enabled()?TemplateStudio.selectedId():'';}
 function defaultPanel(){if(PhotoFlow.enabled())openTool(last==='filters'&&$('filterBtn').disabled?'templates':last);else{const first=$('contextTools')?.querySelector('button:not(:disabled)');if(first)first.click();else openLayout();}}
 function refresh(){
  if(!started||!media.matches)return;cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{
   if(!media.matches)return;refreshPaperTools();
   if(sheet.hidden){if(!$('typeTabs')?.hidden||window.EffectBrowser?.active()||window.EffectBrowser?.pending())return;defaultPanel();return;}
   if(!sheet.classList.contains('desktop-inspector'))return;
   if(type!==family()){defaultPanel();return;}
   if(photo!==active()){
    if(sheetKind==='templates')TemplateStudio.open();else if(sheetKind==='filters'&&!$('filterBtn').disabled)openFilters();else if(sheetKind==='layers')openTool(last==='emoji'?'emoji':'text');else if(sheetKind==='text')openLegacyText();else if(sheetKind==='layout')openLayout();
    remember();
   }else if(sheetKind==='templates'&&template!==TemplateStudio.selectedId()){template=TemplateStudio.selectedId();TemplateStudio.refreshPanel();}
   mark();
  });
 }
 function openTool(kind){
  if(!media.matches||!['templates','filters','text','emoji'].includes(kind))return false;
  window.EffectBrowser?.exit(false);window.EditHistory?.commit();if(['templates','filters'].includes(kind))LayerEditor.select(null);
  if(kind==='templates'){last=kind;TemplateStudio.open();}
  else if(kind==='filters'){last=kind;openFilters();}
  else if(kind==='text'){last=kind;LayerEditor.openHome('layers');}
  else{last=kind;LayerEditor.activate('emoji',{resume:false});}
  remember();mark();return true;
 }
 window.openSheet=function(kind,...args){
  cancelAnimationFrame(frame);open(kind,...args);
  const inline=media.matches&&['layout','filters','templates','layers','text'].includes(kind);
  sheet.classList.toggle('desktop-inspector',inline);sheet.classList.toggle('desktop-settings',media.matches&&settings.has(kind));
  if(inline){if(['templates','filters'].includes(kind))last=kind;else if(kind==='layers')last=String(args[0]).includes('表情')&&!String(args[0]).includes('文字')?'emoji':'text';else if(kind==='text')last='text';sheet.setAttribute('aria-modal','false');$('scrim').hidden=true;remember();mark();}
 };
 window.closeSheet=function(){close();sheet.classList.remove('desktop-inspector','desktop-settings');back.hidden=true;refresh();};
 function resize(){
  const was=sheet.classList.contains('desktop-inspector');document.body.classList.toggle('desktop-editor',media.matches);refreshPaperTools();
  if(!media.matches){sheet.classList.remove('desktop-inspector','desktop-settings');if(was)close();}
  else{window.EffectBrowser?.exit(false);if(!sheet.hidden&&['layout','filters','templates','layers','text'].includes(sheetKind)){sheet.classList.add('desktop-inspector');sheet.setAttribute('aria-modal','false');$('scrim').hidden=true;remember();}else if(!sheet.hidden&&settings.has(sheetKind))sheet.classList.add('desktop-settings');refresh();}
  requestAnimationFrame(()=>{CropEditor.render();LayerEditor.refresh();});
 }
 // A wheel burst is one trackpad gesture: latch its axis and consume inertia.
 let wheel={at:-Infinity,x:0,y:0,axis:null,fired:false};
 function resetWheel(){wheel={at:-Infinity,x:0,y:0,axis:null,fired:false};}
 function revealSelected(){requestAnimationFrame(()=>requestAnimationFrame(()=>{
  if(!media.matches||sheet.hidden||!sheet.classList.contains('desktop-inspector'))return;
  const body=$('sheetBody'),chosen=body.querySelector(sheetKind==='templates'?'[data-choice].selected':'.filter-card.active');
  if(!chosen||!chosen.offsetParent)return;
  const b=body.getBoundingClientRect(),r=chosen.getBoundingClientRect(),group=body.querySelector('.desktop-template-category');
  const top=group?Math.max(b.top,group.getBoundingClientRect().bottom)+8:b.top+8;
  if(r.top<top)body.scrollTop+=r.top-top;else if(r.bottom>b.bottom-8)body.scrollTop+=r.bottom-b.bottom+8;
 }));}
 function wheelStep(direction){
  const templates=sheetKind==='templates',items=templates?TemplateStudio.browseItems().filter(t=>!t.disabled):FILTERS.map(([id])=>({id}));
  const id=templates?TemplateStudio.selectedId():filter()[0],i=items.findIndex(t=>t.id===id),next=i<0?(direction>0?0:items.length-1):i+direction;
  if(next<0||next>=items.length)return;
  if(templates)TemplateStudio.apply(items[next].id);else{const button=[...$('sheetBody').querySelectorAll('[data-filter]')].find(b=>b.dataset.filter===items[next].id);button?.click();}
  revealSelected();
 }
 $('preview').addEventListener('wheel',e=>{
  if(!media.matches||sheet.hidden||!sheet.classList.contains('desktop-inspector')||!['templates','filters'].includes(sheetKind)||e.ctrlKey||e.metaKey||e.shiftKey||e.buttons||window.OriginalPreview?.active())return;
  const stamp=Number(e.timeStamp),now=Number.isFinite(stamp)&&stamp>0?stamp:performance.now(),owner=sheetKind==='templates'&&window.PhotoWorks?.enabled()?PhotoWorks.owner():active(),group=sheetKind==='templates'?TemplateStudio.currentGroup():'';
  if(now<wheel.at||now-wheel.at>240||wheel.draft!==state||wheel.owner!==owner||wheel.kind!==sheetKind||wheel.group!==group)resetWheel();
  Object.assign(wheel,{at:now,draft:state,owner,kind:sheetKind,group});
  const unit=e.deltaMode===1?16:e.deltaMode===2?$('preview').clientWidth:1;
  wheel.x+=e.deltaX*unit;wheel.y+=e.deltaY*unit;
  if(!wheel.axis&&Math.max(Math.abs(wheel.x),Math.abs(wheel.y))>=12){if(Math.abs(wheel.x)>Math.abs(wheel.y)*1.4)wheel.axis='x';else if(Math.abs(wheel.y)>Math.abs(wheel.x)*1.4)wheel.axis='y';}
  if(wheel.axis!=='x')return;
  e.preventDefault();e.stopImmediatePropagation();
  if(!wheel.fired&&Math.abs(wheel.x)>=48){wheel.fired=true;wheelStep(wheel.x>0?1:-1);}
 },{capture:true,passive:false});
 window.addEventListener('blur',resetWheel);window.addEventListener('resize',resetWheel);
 window.DesktopEditor={refresh,openTool};
 window.addEventListener('editor-activation-cancelled',refresh);
 document.addEventListener('click',()=>{if(started&&media.matches)refresh();});
 media.addEventListener('change',resize);
 document.addEventListener('DOMContentLoaded',()=>{started=true;resize();});
})();
