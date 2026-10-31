(async()=>{
 const snapshot=JSON.stringify(state),permission=native.permission,checks=[];
 const check=(v,m)=>{if(!v)throw Error(m);checks.push(m);};
 try{
  closeSheet();await loadPhoto({src:'/sample.svg'});state={...defaults,photos:Array.from({length:6},(_,i)=>({src:'/sample.svg',width:1200,height:800,turn:0,zoom:1+i*.1,x:i*.1,y:0,overlays:[]})),active:4,orientation:'portrait'};render();
  check(!$('addMore'),'Hide add tile at six photos');removePhoto(5);render();check(!!$('addMore'),'Restore add tile after deletion');$('photoUndo').querySelector('button').click();render();check(state.photos.length===6&&!$('addMore'),'Undo restores six-photo limit');
  check(Object.keys(PAPER).join(',')==='5009,5012,5014','Square, 6-inch and 4-inch split paper');openPaper();check(document.querySelectorAll('[data-paper]').length===3,'Paper chooser has three options');closeSheet();
  let pages=await preparePrintPages();check(pages.length===6,'Six photos produce six output pages');check(new Set(pages.map(p=>p.preview)).size===6,'Each output contains its own crop');check(state.active===5,'Preview generation preserves photo selection');
  native.permission=true;await confirmPrint();check($('sheetBody').querySelectorAll('.print-pages img').length===6&&$('confirmSend').textContent.includes('6 张'),'Confirmation shows every page and correct count');closeSheet();
  state.media=5014;pages=await preparePrintPages();check(pages.length===3,'Six photos produce three split sheets');check(new Set(pages.map(p=>p.preview)).size===3,'Split pages advance through all photo pairs');
  state.media=5012;state.mode='collage';pages=await preparePrintPages();check(pages.length===1,'Collage stays one sheet');state.mode='photo';
  for(const orientation of ['portrait','landscape'])for(const entry of TEMPLATE_CATALOG){state.mode='template';state.orientation=orientation;state.templateId=entry.id;active().templateId=entry.id;await TemplateStudio.ensureCurrent();render();const t=TemplateStudio.entry(),f=photoFrames[0];check(Math.abs(f.w-t.crop.width)<1&&Math.abs(f.h-t.crop.height)<1,'Template geometry '+orientation+'/'+entry.id);const output=physical(compose());if(output.width!==1216||output.height!==1824)throw Error('Invalid print dimensions');}
  await TemplateStudio.open();check(document.querySelectorAll('[data-template]').length===16,'16 original templates available');check([...document.querySelectorAll('[data-template] img')].every(i=>i.src.startsWith('data:image/jpeg')),'All thumbnails generated without old promotional badges');closeSheet();
  state.mode='photo';state.orientation='portrait';render();const o=LayerEditor.create({kind:'emoji',text:'❤️',sizePct:2});render();const a=$('layerSelection').getBoundingClientRect(),b=$('layerResize').getBoundingClientRect();check(a.width>=43&&a.height>=43,'Small emoji retains 44px movement target');check(a.right<=b.left||a.left>=b.right||a.bottom<=b.top||a.top>=b.bottom,'Resize handle does not overlap movement target');
  return {passed:checks.length,templates:TEMPLATE_CATALOG.length*2,checks:checks.filter(c=>!c.startsWith('Template geometry'))};
 }finally{closeSheet();state=JSON.parse(snapshot);native.permission=permission;LayerEditor.select(null);await TemplateStudio.ensureCurrent();render();save();scrollTo(0,0);document.getElementById('photoUndo')?.remove();}
})()
