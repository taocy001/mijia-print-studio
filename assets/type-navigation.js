/* Navigation only: reuse the existing editor panels and settings handlers. */
window.TypeNavigation=(()=>{
 const family=()=>['photo','template','polaroid','collage'].includes(state.mode)?'photo':state.mode;
 const types=['photo','id','idcard','calendar','label','card'].map(id=>MODES.find(m=>m[0]===id));
 const tabs=document.createElement('nav');tabs.id='typeTabs';tabs.setAttribute('aria-label','打印类型');
 tabs.innerHTML=types.map(([id,name])=>`<button type="button" data-print-type="${id}" aria-pressed="false">${name}</button>`).join('');
 const trigger=document.createElement('button');trigger.id='typeMenuBtn';trigger.type='button';trigger.setAttribute('aria-haspopup','true');trigger.setAttribute('aria-expanded','false');trigger.setAttribute('aria-controls','typeTabs');$('paperBtn').before(trigger);$('paperBtn').hidden=true;tabs.hidden=true;document.body.append(tabs);
 function closeTypes(){tabs.hidden=true;trigger.setAttribute('aria-expanded','false');}
 trigger.onclick=()=>{if(!tabs.hidden){closeTypes();return;}EffectBrowser.exit(false);closeSheet();const r=trigger.getBoundingClientRect();tabs.style.top=Math.max(8,Math.min(r.bottom+6,innerHeight-180))+'px';tabs.style.left=Math.max(8,Math.min(r.left+r.width/2-140,innerWidth-288))+'px';tabs.hidden=false;trigger.setAttribute('aria-expanded','true');};
 document.addEventListener('pointerdown',e=>{if(!tabs.contains(e.target)&&!trigger.contains(e.target))closeTypes();});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!tabs.hidden){e.preventDefault();closeTypes();trigger.focus();}});
 window.addEventListener('resize',closeTypes);window.addEventListener('blur',closeTypes);
 const previousBack=window.goBack;window.goBack=()=>{if(!tabs.hidden){closeTypes();return true;}return previousBack();};
 const originalTools=document.querySelector('.tool-tabs');originalTools.id='photoTypeTools';
 const tools=document.createElement('nav');tools.id='contextTools';tools.className='tool-tabs';tools.setAttribute('aria-label','当前类型的工具');originalTools.after(tools);
 let photoMode=family()==='photo'?state.mode:'photo',scope=null,lastFamily='',signature='';
 const routes={
  month:['月份','calendar','#monthInput'],
  calendarLayout:['版式','layout','[data-setting=calendarLayout],[data-setting=fit],[data-setting=orientation]'],
  lunar:['农历','calendar','#lunarToggle'],
  size:['尺寸','id','[data-setting=idSize]'],
  background:['底色','photo','#idBackgroundOptions'],
  page:['排版','layout','[data-setting=orientation],[data-setting=fit],#nameGapInput'],
  style:['样式','template','#nameTemplateChoices,[data-setting=cardStyle]'],
  direction:['方向','rotate','[data-setting=idCardOrientation]'],
  content:['内容','text'],tone:['色调','spark'],text:['文字','text'],emoji:['表情','emoji'],decoration:['装饰','text']
 };
 const menus={calendar:['month','calendarLayout','lunar','tone','decoration'],id:['size','background','page','tone','decoration'],label:['style','content','page','decoration'],card:['style','content','page','decoration'],idcard:['direction','page','tone','text','emoji']};
 function choose(type){
  closeTypes();if(type===family())return;
  EffectBrowser.exit(false);LayerEditor.select(null);closeSheet();scope=null;
  if(family()==='photo'){window.PhotoWorks?.saveCurrent();photoMode=state.mode;}
  state.mode=type==='photo'?photoMode:type;if(type==='photo')window.PhotoWorks?.activate();
  if(state.mode==='photo'&&active()?.templateId)state.mode='template';
  if(state.mode==='collage'&&state.media===5014&&!state.collageTemplateId&&!state.photoLayout)state.collageLayout='strip';
  peek=false;refresh();schedule();
 }
 tabs.onclick=e=>{const b=e.target.closest('[data-print-type]');if(b)choose(b.dataset.printType);};
 tabs.onkeydown=e=>{const buttons=[...tabs.children],i=buttons.indexOf(document.activeElement);if(i<0)return;let next;if(e.key==='ArrowRight')next=(i+1)%buttons.length;else if(e.key==='ArrowLeft')next=(i-1+buttons.length)%buttons.length;else if(e.key==='Home')next=0;else if(e.key==='End')next=buttons.length-1;else return;e.preventDefault();buttons[next].focus();};
 function filterPanel(){
  if(!scope||scope.mode!==state.mode||sheetKind!=='layout')return;
  const body=$('sheetBody'),rule=routes[scope.key],selected=new Set();
  for(const node of body.querySelectorAll(rule[2])){let top=node;while(top.parentElement!==body)top=top.parentElement;selected.add(top);}
  for(const child of body.children)child.hidden=!selected.has(child);
  if(!selected.size){const hint=document.createElement('p');hint.className='hint';hint.textContent=state.mode==='calendar'&&state.media===5014?'拼接相纸固定为上下两个月。':'当前相纸采用固定版式，无需调整。';body.append(hint);}
  $('sheetTitle').textContent=rule[0];
  for(const b of tools.children)b.setAttribute('aria-pressed',String(b.dataset.typeTool===scope.key));
 }
 const originalLayout=openLayout;
 openLayout=function(){if(sheetKind!=='layout'||$('sheet').hidden)scope=null;originalLayout();$('sheetBody').querySelectorAll('[data-photo-arrangement]').forEach(b=>b.classList.toggle('selected',b.getAttribute('aria-pressed')==='true'));filterPanel();};
 function panel(key){scope=null;EffectBrowser.exit(false);originalLayout();scope={key,mode:state.mode};filterPanel();}
 function action(key){
  if(routes[key][2])return panel(key);
  scope=null;
  if(key==='tone')return $('filterBtn').click();
  if(key==='text')return $('addTextQuick').click();
  if(key==='emoji')return $('addEmojiQuick').click();
  EffectBrowser.exit(false);
  if(key==='content')openLegacyText();else LayerEditor.openHome('layers');
 }
 tools.onclick=e=>{const b=e.target.closest('[data-type-tool]');if(b&&!b.disabled)action(b.dataset.typeTool);};
 function markTools(){
  let key=scope&&scope.mode===state.mode&&sheetKind==='layout'&&!$('sheet').hidden?scope.key:'';
  if(EffectBrowser.kind()==='filters'||sheetKind==='filters'&&!$('sheet').hidden)key='tone';
  else if(sheetKind==='text'&&!$('sheet').hidden)key='content';
  else if(sheetKind==='layers'&&!$('sheet').hidden){const preferred=$('sheetTitle').textContent.includes('表情')?'emoji':'text';key=(menus[family()]||[]).includes(preferred)?preferred:'decoration';}
  for(const b of tools.children)b.setAttribute('aria-pressed',String(b.dataset.typeTool===key));
 }
 function refresh(){
  const type=family();originalTools.hidden=type!=='photo';tools.hidden=type==='photo';
  for(const b of tabs.children)b.setAttribute('aria-pressed',String(b.dataset.printType===type));
  const label=types.find(t=>t[0]===type)?.[1]||'照片';trigger.innerHTML=esc(label)+icon('chevron');trigger.setAttribute('aria-label','打印类型：'+label);
  if(type!==lastFamily){lastFamily=type;scope=null;}
  const keys=menus[type]||[],next=keys.join('|');
  if(signature!==next){tools.innerHTML=keys.map(key=>`<button type="button" data-type-tool="${key}" aria-pressed="false">${icon(routes[key][1])}<span>${routes[key][0]}</span></button>`).join('');signature=next;}
  for(const b of tools.children){const key=b.dataset.typeTool;b.disabled=key==='tone'?$('filterBtn').disabled:['content','text','emoji','decoration'].includes(key)?!previewReady():key==='background'?!active():key==='page'&&['id','card','idcard'].includes(type)&&state.media!==5012;}
  if(state.mode==='polaroid')$('templateBtn').disabled=false;
  $('addTextQuick').querySelector('span:last-child').textContent=state.mode==='polaroid'?'题字':'文字';markTools();
 }
 for(const [id,run] of [['addTextQuick',()=>{openLegacyText();const b=document.createElement('button');b.className='full-button secondary-button';b.textContent='自由文字与表情';b.onclick=()=>LayerEditor.openHome('layers');$('sheetBody').append(b);}]])$(id).addEventListener('click',e=>{if(state.mode!=='polaroid')return;e.stopImmediatePropagation();EffectBrowser.exit(false);run();},true);
 const menu=$('menuBtn').onclick;$('menuBtn').onclick=()=>{closeTypes();menu();$('menuWorkType')?.remove();$('sheetBody').insertAdjacentHTML('afterbegin',`<button class="menu-row" id="menuPaper">${icon('layout')}<span>相纸与方向 · ${esc(PAPER[state.media][0])}</span>${icon('chevron')}</button>`);$('menuPaper').onclick=()=>$('paperBtn').click();};
 new MutationObserver(()=>{if($('sheet').hidden||sheetKind!=='layout')scope=null;markTools();}).observe($('sheet'),{attributes:true,attributeFilter:['hidden','data-kind']});
 new MutationObserver(markTools).observe($('sheetTitle'),{childList:true,subtree:true,characterData:true});
 refresh();return {refresh,choose};
})();
