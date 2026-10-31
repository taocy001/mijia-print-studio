(async()=>{
 const saved=JSON.stringify(state),results=[];
 function check(ok,message){if(!ok)throw Error(message);}
 try{
  closeSheet();await loadPhoto({src:'/sample.svg'});const photo={src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0};
  for(const settings of [
   {mode:'photo',orientation:'portrait',border:60},
   {mode:'photo',orientation:'landscape',fit:'contain'},
   {mode:'photo',orientation:'portrait',fit:'contain',turn:1},
   {mode:'polaroid',caption:'底部题字'},
   {mode:'calendar'}, {mode:'id'}, {mode:'collage'}, {mode:'photo',media:5014,active:1}
  ]){
   state={...defaults,photos:[{...photo,turn:settings.turn||0,zoom:settings.zoom||1},{...photo}],active:0,orientation:'portrait',...settings};render();const exported=compose().toDataURL();
   check(!document.getElementById('cropToggle')&&!document.getElementById('cropDone'),'No crop mode controls');check(exported===compose().toDataURL(),'Guide does not enter printed image');
   const g=CropEditor.geometry(),[w,h]=logicalSize();check(g.paper.w===w&&g.paper.h===h,'Guide includes entire paper, not only photo aperture');
   const expected=document.createElement('canvas');expected.width=$('preview').width;expected.height=$('preview').height;const ec=expected.getContext('2d');ec.translate(g.tx,g.ty);ec.scale(g.scale,g.scale);ec.drawImage(compose(),0,0);
   const actual=$('preview').getContext('2d');let checked=0;
   for(const fx of [.23,.43,.71])for(const fy of [.19,.47,.77]){const x=Math.round(g.tx+w*fx*g.scale),y=Math.round(g.ty+h*fy*g.scale);if(x<0||y<0||x>=expected.width||y>=expected.height)continue;const a=actual.getImageData(x,y,1,1).data,b=ec.getImageData(x,y,1,1).data;check([...a].every((v,i)=>Math.abs(v-b[i])<3),'Printed pixels match guide '+JSON.stringify(settings));checked++;}
   check(checked>0,'Samples within guide');results.push(settings);
  }
  state.mode='label';render();check(CropEditor.geometry().frame===null,'Label paper remains visible without a photo');
  return {passed:true,cases:results.length,results};
 }finally{closeSheet();state=JSON.parse(saved);render();save();}
})()
