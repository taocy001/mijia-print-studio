(async()=>{
 await LayerEditor.ready;const snapshot=JSON.stringify(state),checks=[];function check(v,m){if(!v)throw Error(m);checks.push(m);}
 try{
  closeSheet();state.photos=[{src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0}];state.active=0;state.mode='photo';state.media=5012;state.orientation='portrait';state.caption='保留题字';await loadPhoto(state.photos[0]);render();
  check(Math.abs($('preview').getBoundingClientRect().width-document.documentElement.clientWidth)<2,'Portrait canvas fills phone width');
  LayerEditor.openEditor();document.querySelector('[data-font="happy"]').click();document.querySelector('[data-color="#e65a62"]').click();check(LayerEditor.list().length===0,'Empty text creates no object');
  $('layerText').value='你好 Pixel\n留住这一刻';$('layerText').dispatchEvent(new Event('input'));let text=LayerEditor.selected();check(text.font==='happy'&&text.color==='#e65a62','Style selected before typing is preserved');check(text.text.includes('\n'),'Multiline Chinese text');
  text.sizePct=14;text.angle=28;render();check(+$('out-angle').value===28,'Gesture properties refresh without rebuilding textarea');check($('layerText').value===text.text,'Textarea preserved on render');
  const base=compose(false).toDataURL(),withText=compose().toDataURL();check(base!==withText,'Text included in print composition');
  const emoji=LayerEditor.create({kind:'emoji',text:'🥰',fx:.7,fy:.7,sizePct:20});check($('sheet').hidden,'Selecting another object closes stale editor');check(compose().toDataURL()!==withText,'Color emoji included in composition');
  const [w,h]=logicalSize(),m=LayerEditor.metrics(emoji,w,h);check(LayerEditor.hit(m.x,m.y)?.id===emoji.id,'Hit testing selects top object');emoji.fx=0.99;emoji.fy=0.99;emoji.angle=75;const edge=LayerEditor.metrics(emoji,w,h);check(edge.x+edge.rw/2<=w&&edge.y+edge.rh/2<=h,'Rotated objects stay within paper');
  $('copyLayer').click();check(LayerEditor.list().length===3,'Copy creates independent object');LayerEditor.remove();check(LayerEditor.list().length===2,'Delete removes object');$('layerUndo').querySelector('button').click();check(LayerEditor.list().length===3,'Undo restores object');
  LayerEditor.openEditor(text);state.mode='collage';render();check($('sheet').hidden&&LayerEditor.list().length===0,'Mode change closes stale editor and isolates layers');state.mode='photo';render();check(LayerEditor.list().length===3&&state.caption==='保留题字','Photo layers and legacy caption preserved');
  check(document.fonts.check('20px StudioHappy')&&document.fonts.check('20px StudioBrush'),'Bundled fonts loaded');
  return {passed:checks.length,checks};
 }finally{closeSheet();LayerEditor.select(null);state=JSON.parse(snapshot);render();save();}
})()
