(async()=>{
 const snapshot=JSON.stringify(state),checks=[];const check=(ok,label)=>{if(!ok)throw Error(label);checks.push(label);};
 try{
  closeSheet();await LayerEditor.ready;await loadPhoto({src:'/sample.svg'});state={...defaults,photos:Array.from({length:3},()=>({src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0,fit:'cover',border:0,filter:'none',overlays:[]})),active:0};render();
  changeSetting('fit','contain');changeSetting('border',60);selectPhoto(1);check(state.fit==='cover'&&state.border===0,'Layout and border isolated per photo');selectPhoto(0);check(state.fit==='contain'&&state.border===60,'Layout restored on selection');changeSetting('fit','cover');changeSetting('border',0);
  for(const zoom of [1,2,4]){active().zoom=zoom;render();const f=photoFrames[0],g=photoGeometry(f.p,f.w,f.h,f.fit),v=CropEditor.geometry(),x=f.x+(f.w-g.dw)/2+g.dx+v.tx,y=f.y+(f.h-g.dh)/2+g.dy+v.ty;check(x>=-1&&y>=-1&&x+g.dw<=$('preview').width+1&&y+g.dh<=$('preview').height+1,'Complete source visible at '+zoom+'x');}
  active().zoom=1;render();await TemplateStudio.open();check(!!document.querySelector('#noTemplate.selected img[src^="data:"]'),'First template is selected real-photo preview');closeSheet();openFilters();check(document.querySelectorAll('[data-tone]').length===8&&!!$('toneSharp'),'Eight rendered tones and sharpness together');closeSheet();LayerEditor.openHome('emoji');check(document.querySelectorAll('.emoji-grid img').length===60,'Shared sixty emoji loaded');check([...document.querySelectorAll('.emoji-grid img')].every(i=>i.complete&&i.naturalWidth),'All emoji images decoded');closeSheet();
  const output=compose().toDataURL();render();check(output===compose().toDataURL(),'Editor guides do not alter print');
  if(document.body.classList.contains('landscape')){await new Promise(r=>setTimeout(r,150));const c=$('preview').getBoundingClientRect(),b=$('board').getBoundingClientRect();check(c.height<=b.height+1&&c.width<=b.width+1,'Full source fits landscape board');check(document.querySelector('.topbar').getBoundingClientRect().right<=b.left+1,'Header stays left');check($('photos').getBoundingClientRect().left>=b.right-1,'Thumbnails stay right');}
  return {passed:checks.length,checks};
 }finally{closeSheet();state=JSON.parse(snapshot);LayerEditor.select(null);await TemplateStudio.ensureCurrent();render();save();scrollTo(0,0);}
})()
