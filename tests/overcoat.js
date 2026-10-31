(async()=>{
 const snapshot=JSON.stringify(state),checks=[];const check=(v,m)=>{if(!v)throw Error(m);checks.push(m);};
 try{await loadPhoto({src:'/sample.svg'});state={...defaults,mode:'photo',orientation:'portrait',photos:[{src:'/sample.svg',width:1200,height:800,filter:'none',overlays:[]}],active:0};peek=false;render();await LayerEditor.ready;
 const base=compose().toDataURL();const o=LayerEditor.create({kind:'text',text:'SECRET',hidden:true,sizePct:16});
 check(compose().toDataURL()===base,'Hidden text is absent from RGB photo');
 check(compose(true,'mask').getContext('2d').getImageData(0,0,1216,1824).data.some((v,i)=>i%4===0&&v===255),'Hidden text reaches coating mask');
 check(compose(true,'editor').toDataURL()!==base,'Hidden text is visible as editing guide');
 LayerEditor.openEditor(o);check($('layerHidden').checked,'Editor restores hidden switch');$('layerHidden').checked=false;$('layerHidden').dispatchEvent(new Event('change'));check(!o.hidden&&compose().toDataURL()!==base,'Switch returns text to RGB layer');
 o.hidden=true;LayerEditor.create({kind:'emoji',text:'❤️',hidden:true,fx:.3,fy:.3});closeSheet();
 let pages=await preparePrintPages();check(pages.length===1&&!!pages[0].ocMask,'Print export contains separate coating PNG');check(pages[0].copies===1,'Default one copy remains');
 state.photos.push({src:'/sample.svg',width:1200,height:800,filter:'none',overlays:[]});pages=await preparePrintPages();check(!!pages[0].ocMask&&!pages[1].ocMask,'Coating belongs only to its own photo');
 state.media=5014;pages=await preparePrintPages();check(pages.length===1&&!!pages[0].ocMask,'Split layout includes coating in its own half');
 state.media=5012;state.mode='card';state.photos=[];state.label='READ';check(ready(),'Cards require no photo');pages=await preparePrintPages();check(pages.length===1,'Card exports without photos');
 state.mode='calendar';state.calendarLayout='plain';state.month='2026-10';state.lunar=true;check(ready(),'Plain calendar needs no photo');pages=await preparePrintPages();check(pages.length===1,'Plain calendar exports with lunar dates');
 state.mode='label';state.labelTheme='rainbow';const a=compose().toDataURL();state.labelTheme='panda';check(compose().toDataURL()!==a,'Label themes change actual output');
 return {passed:checks.length,checks};
 }finally{closeSheet();state=JSON.parse(snapshot);LayerEditor.select(null);await TemplateStudio.ensureCurrent();render();save();}
})()
