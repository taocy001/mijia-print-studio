/* The dye animation is illustrative; only device state can confirm completion. */
window.PrintProcess=(()=>{
 let view=null,animation=0;
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 function clear(){cancelAnimationFrame(animation);animation=0;if(view){view.closed=true;view.frame.remove();}view=null;}
 function key(job){return [job.token,job.batchIndex||1,(job.previewPage||job).file].join(':');}
 function fresh(job){const t=job.telemetry;return job.phase==='printing'&&t?.stage==='waiting'&&[2,3,4,6].includes(t.device?.['job-state'])&&Date.now()-t.sampleAt>=0&&Date.now()-t.sampleAt<8000;}
 function stages(image){
  const w=360,h=Math.max(1,Math.round(w*image.naturalHeight/image.naturalWidth)),source=document.createElement('canvas');source.width=w;source.height=h;const c=source.getContext('2d');c.drawImage(image,0,0,w,h);const pixels=c.getImageData(0,0,w,h),result=[];
  for(let pass=0;pass<4;pass++){const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const d=new ImageData(new Uint8ClampedArray(pixels.data),w,h);for(let i=0;i<d.data.length;i+=4){if(pass<3)d.data[i]=255;if(pass<2)d.data[i+1]=255;if(pass<1)d.data[i+2]=255;}canvas.getContext('2d').putImageData(d,0,0);result.push(canvas);}
  return result;
 }
 function draw(){
  const v=view;if(!v||v.closed||!v.frames)return;const j=v.job,c=v.canvas.getContext('2d'),w=v.canvas.width,h=v.canvas.height,done=j.phase==='done',active=fresh(j),canAnimate=active&&!document.hidden&&!reduced.matches;
  const now=Date.now();if(canAnimate&&v.wasActive)v.elapsed+=Math.max(0,Math.min(1000,now-v.tick));v.tick=now;v.wasActive=canAnimate;
  if(active&&!reduced.matches)v.started=true;
  const amount=Math.min(3.95,v.elapsed/12000),pass=Math.floor(amount),part=amount-pass;
  if(done||reduced.matches||!v.started){c.drawImage(v.frames[3],0,0);v.label.textContent=done?'打印机已确认完成':j.message||'等待打印';}
  else if(pass<3){c.drawImage(v.frames[pass],0,0);c.save();c.beginPath();c.rect(0,0,w,h*part);c.clip();c.drawImage(v.frames[pass+1],0,0);c.restore();v.label.textContent=['黄染层','品红染层','青染层'][pass]+' · 过程示意';}
  else {c.drawImage(v.frames[3],0,0);const g=c.createLinearGradient(-w+part*w*3,0,part*w*3,0);g.addColorStop(0,'#ffffff00');g.addColorStop(.5,'#ffffff50');g.addColorStop(1,'#ffffff00');c.fillStyle=g;c.fillRect(0,0,w,h);v.label.textContent='覆膜 · 过程示意';}
  if(!done&&!active){const state=j.telemetry?.device?.['job-state'];v.label.textContent=j.phase!=='printing'?j.message||'演示暂停':state===5?'打印机已暂停':state===1?'等待打印机确认照片数据':[7,8,9].includes(state)?'正在核对打印机终态':v.started?'状态待更新，演示暂停':j.message||'等待打印';}
  v.note.hidden=done||!v.started||reduced.matches;
  if(canAnimate&&amount<3.95){animation=requestAnimationFrame(draw);}else animation=0;
 }
 function update(job){
  if(!view)return;
  if(key(job)!==view.key){const container=view.container;clear();mount(container,job);return;}
  view.job=job;
  if(!animation)draw();
 }
 function mount(container,job){
  clear();const page=job.previewPage||job;if(!page.file||!job.token)return;
  const frame=document.createElement('figure');frame.className='print-process';
  const canvas=document.createElement('canvas'),label=document.createElement('figcaption'),note=document.createElement('small');canvas.setAttribute('role','img');canvas.setAttribute('aria-label','当前已提交照片的打印过程参考');label.textContent=job.message||'正在载入预览';note.textContent='过程示意，非设备逐色进度';note.hidden=true;frame.append(canvas,label,note);container.prepend(frame);
  const v={container,frame,key:key(job),job,canvas,label,note,closed:false,elapsed:0,tick:Date.now(),started:false,wasActive:false,frames:null};view=v;
  historyPreview(page).then(async src=>{const image=new Image();image.src=src;await image.decode();if(view!==v||v.closed)return;v.frames=stages(image);canvas.width=v.frames[0].width;canvas.height=v.frames[0].height;draw();}).catch(()=>{if(view===v){frame.remove();clear();}});
 }
 function resume(){if(view){cancelAnimationFrame(animation);animation=0;view.wasActive=false;view.tick=Date.now();draw();}}
 document.addEventListener('visibilitychange',resume);reduced.addEventListener('change',resume);
 return {mount,update,clear};
})();
