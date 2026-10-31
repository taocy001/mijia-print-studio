(async()=>{
 const snapshot=JSON.stringify(state),checks=[];
 const check=(v,m)=>{if(!v)throw Error(m);checks.push(m);};
 const settle=()=>new Promise(r=>setTimeout(r,120));
 const rect=id=>$(id).getBoundingClientRect();
 try{
  check(Studio.landscape()&&document.body.classList.contains('landscape'),'Device uses landscape layout');
  closeSheet();LayerEditor.select(null);await loadPhoto({src:'/sample.svg'});
  state={...defaults,photos:Array.from({length:6},()=>({src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0,filter:'none',overlays:[]})),active:0};render();await settle();
  let c=rect('preview'),b=rect('board'),p=rect('photos');
  check(Math.abs(c.height-b.height)<2,'Landscape photo fills available height');
  check(c.left>=b.left-1&&c.right<=b.right+1,'Photo stays inside viewing region');
  check(p.left>=b.right-1,'Thumbnails sit beside photograph');
  check(document.querySelectorAll('.photo-thumb').length===6&&!$('addMore'),'All six photos present without add tile');
  check(p.right<=document.querySelector('.dock').getBoundingClientRect().left+1,'Thumbnail column sits next to tool column');
  check(document.querySelector('.topbar').getBoundingClientRect().right<=b.left+1,'Paper, preview and menu stay on left');
  check([...document.querySelectorAll('.photo-thumb')].every(el=>{const r=el.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight+1;}),'All six thumbnails fit vertically');
  check(document.documentElement.scrollHeight<=innerHeight+2,'Landscape editor has no vertical page overflow');
  $('addEmojiQuick').click();await settle();
  check(!$('sheet').hidden&&rect('sheet').left>innerWidth/2,'Emoji opens in right panel');
  check(rect('preview').right<=rect('sheet').left+1,'Panel does not cover print preview');
  $('sheetBody').scrollTop=600;check($('sheetBody').scrollTop>100,'Emoji panel scrolls to later emoji');
  closeSheet();
  const object=LayerEditor.create({kind:'text',text:'横屏回归',fx:.35,fy:.4,sizePct:8});render();await settle();
  LayerEditor.openEditor(object);await settle();
  const v=CropEditor.geometry(),r=rect('preview'),s=r.width/$('preview').width,box=rect('layerSelection');
  check(Math.abs((box.left+box.width/2)-(r.left+(logicalSize()[0]*.35+v.tx)*s))<2,'Text selection tracks resized canvas coordinates');
  check(window.scrollY===0,'Text editing does not scroll landscape viewport');
  closeSheet();LayerEditor.select(null);state.orientation='portrait';render();await settle();
  c=rect('preview');b=rect('board');
  check(c.height<=b.height+1&&c.width<c.height,'Portrait paper fits landscape view without distortion');
  return {passed:checks.length,checks};
 }finally{closeSheet();state=JSON.parse(snapshot);LayerEditor.select(null);await TemplateStudio.ensureCurrent();render();save();}
})()
