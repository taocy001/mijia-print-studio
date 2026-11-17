/* Composition tools stay off the photograph; object tools retain their existing behavior. */
window.EditorChrome=(()=>{
 let crop=false,lastMode=state.mode;
 Object.assign(PATHS,{undo:'M9 4 4 9l5 5M4 9h10a6 6 0 0 1 0 12',redo:'m15 4 5 5-5 5m5-5H10a6 6 0 0 0 0 12',mirror:'M12 2v20M9 5 3 19h6zM15 5l6 14h-6z'});
 const host=$('editorToolbar');document.querySelector('.editor-controls').prepend(host);host.innerHTML=`<div class="editor-head"><button id="editorUndo" aria-label="撤销">${icon('undo')}</button><button id="editorRedo" aria-label="重做">${icon('redo')}</button><span id="editorContext">照片编辑</span><button id="composeToggle">构图</button></div><div id="composeTools" hidden></div>`;
 $('composeTools').append($('photoTools'));$('compare').hidden=true;$('zoomIn').hidden=$('zoomOut').hidden=true;$('reset').querySelector('small').textContent='重置构图';$('reset').setAttribute('aria-label','重置当前照片构图');
 const mirror=document.createElement('button');mirror.id='mirrorPhoto';mirror.innerHTML=icon('mirror')+'<small>水平镜像</small>';mirror.setAttribute('aria-label','水平镜像当前照片');$('rotate').after(mirror);
 mirror.onclick=()=>{if(!canAdjustPhoto())return;EditHistory.run(()=>{active().mirror=!active().mirror;active().facePending=false;CropEditor.unlockDisplay();schedule();});};
 $('editorUndo').onclick=()=>EditHistory.undo();$('editorRedo').onclick=()=>EditHistory.redo();
 function closeCrop(){crop=false;refresh();}
 function refresh(){if(state.mode!==lastMode||EffectBrowser.active()){crop=false;lastMode=state.mode;}$('composeTools').hidden=!crop;$('editorContext').hidden=$('composeToggle').hidden=EffectBrowser.active();$('composeToggle').textContent=crop?'完成':'构图';$('composeToggle').disabled=!canAdjustPhoto();$('editorContext').textContent=EffectBrowser.active()?'预览效果':crop?'调整当前照片':LayerEditor.selected()?'编辑装饰':'编辑';EditHistory.refresh();}
 $('composeToggle').onclick=()=>{if(!canAdjustPhoto())return;LayerEditor.select(null);crop=!crop;refresh();};
 const menu=$('menuBtn').onclick;$('menuBtn').onclick=()=>{menu();if(state.mode==='id'){$('sheetBody').insertAdjacentHTML('beforeend',`<label class="coat-switch"><span>证件照标注制作日期</span><input id="idDateToggle" type="checkbox" ${state.idPrintDate?'checked':''}></label>`);$('idDateToggle').onchange=e=>{state.idPrintDate=e.target.checked?new Date().toLocaleDateString('sv-SE'):null;schedule();};}};
 let layoutFrame=0,lastHeight=-1;new ResizeObserver(()=>{const height=host.hidden?0:host.getBoundingClientRect().height;if(height===lastHeight)return;lastHeight=height;document.documentElement.style.setProperty('--editor-action-height',height+'px');cancelAnimationFrame(layoutFrame);layoutFrame=requestAnimationFrame(()=>{CropEditor.render();LayerEditor.refresh();});}).observe(host);
 refresh();return {refresh,closeCrop};
})();
