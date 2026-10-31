(async()=>{
 const check=(ok,message)=>{if(!ok)throw Error(message);};
 const initial=JSON.parse(JSON.stringify(state)),results=[];
 await loadPhoto({src:'/sample.svg'});
 const photo={src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0};
 try{
  state={...defaults,photos:[{...photo},{...photo},{...photo},{...photo}],active:0};
  for(const mode of MODES.map(m=>m[0]))for(const media of [5012,5014,5009])for(const orientation of ['portrait','landscape']){
   Object.assign(state,{mode,media,orientation});
   const logical=compose(),out=physical(logical),size=media===5009?[1040,1040]:[1216,1824];
   check(out.width===size[0]&&out.height===size[1],`Wrong output size: ${mode}/${media}/${orientation}`);
   const bytes=atob(out.toDataURL('image/jpeg',.9).split(',')[1]).length;
   check(bytes<1048576,'Sample JPEG exceeded budget');
   // Sample the whole output: its center line may legitimately be a collage gap.
   const thumb=document.createElement('canvas');thumb.width=64;thumb.height=64;
   thumb.getContext('2d').drawImage(out,0,0,64,64);
   const pixels=thumb.getContext('2d').getImageData(0,0,64,64).data;
   let nonWhite=0;for(let i=0;i<pixels.length;i+=4)if(pixels[i]<248||pixels[i+1]<248||pixels[i+2]<248)nonWhite++;
   check(nonWhite>50,`Blank output: ${mode}/${media}/${orientation}`);
   results.push({mode,media,orientation,width:out.width,height:out.height,bytes});
  }
  Object.assign(state,{mode:'photo',media:5012,orientation:'landscape',photos:[{...photo}],filter:'none'});
  const original=compose().toDataURL();state.filter='bw';check(original!==compose().toDataURL(),'Filter has no effect');
  state.filter='none';state.photos[0].turn=1;check(original!==compose().toDataURL(),'Rotation has no effect');
  state.photos[0].turn=0;state.photos[0].zoom=2;state.photos[0].x=.5;check(original!==compose().toDataURL(),'Crop has no effect');
  state.photos[0]={...photo};state.caption='中文排版测试';check(original!==compose().toDataURL(),'Caption has no effect');
  state.orientation='auto';state.photos.push({...photo,width:800,height:1200});state.active=1;
  check(logicalSize()[0]===1216,'Auto orientation used the wrong selected photo');state.active=0;
  const marks=document.createElement('canvas');marks.width=1824;marks.height=1216;
  const markContext=marks.getContext('2d');markContext.fillStyle='white';markContext.fillRect(0,0,1824,1216);markContext.fillStyle='red';markContext.fillRect(0,0,60,60);
  state.media=5012;
  const rotated=physical(marks).getContext('2d').getImageData(1200,10,1,1).data;
  check(rotated[0]===255&&rotated[1]===0,'Landscape export did not rotate clockwise');
  marks.width=1040;marks.height=1040;markContext.fillStyle='red';markContext.fillRect(0,0,60,60);state.media=5009;
  const flipped=physical(marks).getContext('2d').getImageData(1030,1030,1,1).data;
  check(flipped[0]===255&&flipped[1]===0,'Square backing rotation is wrong');
  const before=Studio.state();
  check(JSON.parse(Studio.print('AAAA',JSON.stringify({media:9999}))).error,'Invalid media accepted');
  check(JSON.parse(Studio.print('AAAA',JSON.stringify({media:5012}))).error,'Invalid JPEG accepted');
  check(JSON.parse(before).job.token===JSON.parse(Studio.state()).job.token,'Validation created a job');
  return {passed:true,renderCases:results.length,cases:results,filter:true,rotation:true,crop:true,caption:true,nativeInputValidation:true};
 }finally{state=initial;render();save();}
})()
