// Use device orientation, not keyboard height, to choose the editor layout.
(()=>{
 let frame=0;
 const refresh=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{CropEditor.render();LayerEditor.refresh();});};
 window.updateEditorOrientation=()=>{
  const landscape=window.Studio?.landscape?Studio.landscape():screen.orientation?.type.startsWith('landscape')??(innerWidth>innerHeight);
  const changed=document.body.classList.contains('landscape')!==landscape;
  document.body.classList.toggle('landscape',landscape);
  if(changed){window.scrollTo(0,0);if(!landscape)$('paperStage').style.removeProperty('width');}
  refresh();
 };
 new ResizeObserver(refresh).observe(document.querySelector('.workspace'));
 new MutationObserver(refresh).observe($('sheet'),{attributes:true,attributeFilter:['hidden']});
 window.addEventListener('resize',updateEditorOrientation);
 window.screen.orientation?.addEventListener('change',updateEditorOrientation);
 updateEditorOrientation();
})();
