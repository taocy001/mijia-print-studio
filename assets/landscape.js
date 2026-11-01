// Use device orientation, not keyboard height, to choose the editor layout.
(()=>{
 let frame=0;
 const dock=document.querySelector('.dock');
 const dockHeights={portrait:62,desktop:68};
 function measureDock(){
  const mode=document.body.classList.contains('desktop-editor')?'desktop':document.body.classList.contains('landscape')?'landscape':'portrait';
  const measured=dock.getBoundingClientRect().height;if(measured)dockHeights[mode]=measured;
  const height=(dockHeights[mode]||62)+'px';
  if(document.documentElement.style.getPropertyValue('--browser-dock-height')!==height)
   document.documentElement.style.setProperty('--browser-dock-height',height);
 }
 new ResizeObserver(measureDock).observe(dock);
 new MutationObserver(measureDock).observe(document.body,{attributes:true,attributeFilter:['class']});
 const refresh=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{CropEditor.render();LayerEditor.refresh();});};
 window.updateEditorOrientation=()=>{
  const landscape=window.Studio?.landscape?Studio.landscape():screen.orientation?.type.startsWith('landscape')??(innerWidth>innerHeight);
  const changed=document.body.classList.contains('landscape')!==landscape;
  document.body.classList.toggle('landscape',landscape);
  if(changed){window.scrollTo(0,0);if(!landscape)$('paperStage').style.removeProperty('width');}
  measureDock();refresh();
 };
 new ResizeObserver(refresh).observe(document.querySelector('.workspace'));
 new MutationObserver(refresh).observe($('sheet'),{attributes:true,attributeFilter:['hidden']});
 window.addEventListener('resize',updateEditorOrientation);
 window.screen.orientation?.addEventListener('change',updateEditorOrientation);
 updateEditorOrientation();
})();
