(()=>{
 if(!window.BrowserTransport||!document.fullscreenEnabled)return;
 const menu=$('menuBtn'),group=document.createElement('div');group.className='browser-actions';menu.before(group);group.append(menu);
 const button=document.createElement('button');button.id='fullscreenBtn';group.append(button);
 function update(){const full=!!document.fullscreenElement;button.setAttribute('aria-label',full?'退出全屏':'全屏编辑');button.title=full?'退出全屏':'全屏编辑';button.setAttribute('aria-pressed',String(full));button.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="'+(full?'M3 8h5V3M16 3v5h5M21 16h-5v5M8 21v-5H3':'M8 3H3v5M16 3h5v5M21 16v5h-5M8 21H3v-5')+'"/></svg>';}
 button.onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen({navigationUI:'hide'});}catch(e){toast('浏览器未允许全屏，请点击按钮重试');}update();};
 document.addEventListener('fullscreenchange',()=>{update();window.updateEditorOrientation?.();requestAnimationFrame(()=>{CropEditor.render();LayerEditor.refresh();});});update();
})();
