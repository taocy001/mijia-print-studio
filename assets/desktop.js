/* Desktop inspector shares the mobile editor's controls and rendering. */
(()=>{
 if(!window.BrowserTransport)return;
 const media=matchMedia('(min-width:1000px) and (pointer:fine)'),sheet=$('sheet');
 const open=openSheet,close=closeSheet;let restore=0,last='layout';
 const settings=new Set(['menu','device','paper','sharing','printOptions','coat','credits','workType','history','historyDetail','job']);
 const back=$('settingsBack');
 const panels={layout:()=>openLayout(),filters:()=>openFilters(),templates:()=>TemplateStudio.open()};
 function refresh(){cancelAnimationFrame(restore);restore=requestAnimationFrame(()=>{if(media.matches&&sheet.hidden)panels[last]?.();});}
 window.openSheet=function(kind,...args){
  cancelAnimationFrame(restore);open(kind,...args);
  const inline=media.matches&&['layout','filters','templates','layers','text'].includes(kind);
  sheet.classList.toggle('desktop-inspector',inline);sheet.classList.toggle('desktop-settings',media.matches&&settings.has(kind));
  if(inline){if(panels[kind])last=kind;sheet.setAttribute('aria-modal','false');$('scrim').hidden=true;}
  document.querySelectorAll('.tool-tabs button').forEach(b=>b.setAttribute('aria-pressed',String(inline&&({layoutBtn:'layout',filterBtn:'filters',templateBtn:'templates',addTextQuick:'文字',addEmojiQuick:'表情'}[b.id]===kind||b.id==='addTextQuick'&&kind==='layers'&&args[0].includes('文字')||b.id==='addEmojiQuick'&&kind==='layers'&&args[0].includes('表情')))));
 };
 window.closeSheet=function(){const kind=sheetKind;close();sheet.classList.remove('desktop-inspector','desktop-settings');back.hidden=true;if(media.matches){if(panels[kind])last=kind;refresh();}};
 $('closeSheet').onclick=()=>closeSheet();$('scrim').onclick=()=>closeSheet();
 const select=selectPhoto;
 window.selectPhoto=function(index){select(index);if(media.matches&&sheet.classList.contains('desktop-inspector')&&panels[sheetKind])panels[sheetKind]();};
 function resize(){document.body.classList.toggle('desktop-editor',media.matches);cancelAnimationFrame(restore);sheet.classList.remove('desktop-inspector','desktop-settings');back.hidden=true;if(media.matches){if(sheet.hidden)openLayout();else if(panels[sheetKind])panels[sheetKind]();else if(settings.has(sheetKind)){sheet.classList.add('desktop-settings');back.hidden=sheetKind==='menu';}}else if(!sheet.hidden){close();}requestAnimationFrame(()=>{CropEditor.render();LayerEditor.refresh();});}
 media.addEventListener('change',resize);resize();
})();
