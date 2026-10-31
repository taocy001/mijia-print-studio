(async()=>{
 const snapshot=JSON.stringify(state),checks=[];
 const check=(v,m)=>{if(!v)throw Error(m);checks.push(m);};
 try{
  closeSheet();await loadPhoto({src:'/sample.svg'});
  state={...defaults,photos:Array.from({length:6},()=>({src:'/sample.svg',width:1200,height:800,turn:0,zoom:1,x:0,y:0,filter:'none',templateId:null,overlays:[]})),active:0};render();
  const rects=()=>[...document.querySelectorAll('.photo-thumb')].map(el=>el.getBoundingClientRect());
  const six=rects();check(six.length===6&&!$('addMore'),'Six photos hide add button');
  document.querySelector('[data-remove-photo="5"]').click();await new Promise(r=>setTimeout(r,100));
  const five=rects();check(five.length===5,'Delete button removes one photo');
  check(five.every((r,i)=>Math.abs(r.width-six[i].width)<0.1&&Math.abs(r.height-six[i].height)<0.1),'Five and six photos have identical dimensions');
  check(five.every((r,i)=>Math.abs(r.left-six[i].left)<0.1),'Existing photos do not shift horizontally');
  const add=$('addMore').getBoundingClientRect();check(Math.abs(add.width-six[5].width)<0.1,'Add tile occupies the sixth cell');
  return {passed:checks.length,sixWidth:six[0].width,fiveWidth:five[0].width,checks};
 }finally{document.getElementById('photoUndo')?.remove();closeSheet();state=JSON.parse(snapshot);LayerEditor.select(null);await TemplateStudio.ensureCurrent();render();save();}
})()
