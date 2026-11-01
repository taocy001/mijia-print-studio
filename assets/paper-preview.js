/* Display-only paper reference. Print pixels and overcoat masks stay untouched. */
window.PaperPreview=(()=>{
 let cleanup=[];
 function clear(){cleanup.forEach(stop=>stop());cleanup=[];}
 async function mask(page){
  if(!page.ocMask)return '';
  const image=new Image();image.src='data:image/png;base64,'+page.ocMask;await image.decode();
  const canvas=document.createElement('canvas'),wide=page.orientation==='landscape';
  canvas.width=page.media===5009?360:wide?450:300;canvas.height=page.media===5009?360:wide?300:450;
  const c=canvas.getContext('2d');
  if(page.media===5009){c.translate(canvas.width,canvas.height);c.rotate(Math.PI);c.drawImage(image,0,0,canvas.width,canvas.height);}
  else if(wide){c.translate(0,canvas.height);c.rotate(-Math.PI/2);c.drawImage(image,0,0,canvas.height,canvas.width);}
  else c.drawImage(image,0,0,canvas.width,canvas.height);
  const pixels=c.getImageData(0,0,canvas.width,canvas.height);
  for(let i=0;i<pixels.data.length;i+=4){const alpha=pixels.data[i]>100?255:0;pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=255;pixels.data[i+3]=alpha;}
  c.putImageData(pixels,0,0);return canvas.toDataURL('image/png');
 }
 function mount(container,pages){
  container.querySelectorAll('.print-pages .confirmation-preview').forEach((frame,index)=>{
   if(frame.dataset.paperReference||!pages[index])return;frame.dataset.paperReference='true';
   let alive=true;const image=frame.querySelector('img'),overlays=[];
   function layout(){const r=frame.getBoundingClientRect(),i=image.getBoundingClientRect(),ratio=image.naturalWidth/image.naturalHeight;if(!ratio||!i.width||!i.height)return;const width=Math.min(i.width,i.height*ratio),height=width/ratio;for(const layer of overlays)Object.assign(layer.style,{inset:'auto',left:(i.left-r.left+(i.width-width)/2)+'px',top:(i.top-r.top+(i.height-height)/2)+'px',width:width+'px',height:height+'px'});}
   const observer=new ResizeObserver(layout);observer.observe(frame);observer.observe(image);image.addEventListener('load',layout);
   cleanup.push(()=>{alive=false;observer.disconnect();image.removeEventListener('load',layout);});
   const controls=document.createElement('div');controls.className='paper-reference-controls';controls.setAttribute('role','group');controls.setAttribute('aria-label','打印预览显示方式');
   const paper=document.createElement('button');paper.type='button';paper.textContent='纸面参考';
   const gloss=document.createElement('span');gloss.className='paper-reference-gloss';gloss.setAttribute('aria-hidden','true');
   function show(enabled){frame.classList.toggle('paper-reference',enabled);paper.setAttribute('aria-pressed',String(enabled));}
   const release=()=>show(false),visibility=()=>{if(document.hidden)release();};
   paper.addEventListener('pointerdown',e=>{if(e.button!==0||!e.isPrimary)return;e.preventDefault();paper.setPointerCapture(e.pointerId);show(true);});
   for(const type of ['pointerup','pointercancel','lostpointercapture','blur'])paper.addEventListener(type,release);
   paper.addEventListener('keydown',e=>{if([' ','Enter'].includes(e.key)){e.preventDefault();show(true);}});
   paper.addEventListener('keyup',e=>{if([' ','Enter'].includes(e.key)){e.preventDefault();release();}});
   paper.addEventListener('contextmenu',e=>e.preventDefault());paper.onclick=e=>e.preventDefault();
   window.addEventListener('blur',release);document.addEventListener('visibilitychange',visibility);
   cleanup.push(()=>{release();window.removeEventListener('blur',release);document.removeEventListener('visibilitychange',visibility);});show(false);
   frame.addEventListener('pointermove',e=>{if(e.pointerType==='touch')return;const r=frame.getBoundingClientRect();frame.style.setProperty('--paper-light',Math.max(0,Math.min(100,(e.clientX-r.left)/r.width*100))+'%');},{passive:true});
   frame.addEventListener('pointerleave',()=>frame.style.removeProperty('--paper-light'));
   controls.append(paper);frame.append(gloss,controls);overlays.push(gloss);layout();
   mask(pages[index]).then(src=>{if(!src||!alive||!frame.isConnected)return;const pattern=document.createElement('span');pattern.className='paper-reference-pattern';pattern.setAttribute('aria-hidden','true');pattern.style.maskImage='url('+src+')';frame.append(pattern);overlays.push(pattern);layout();}).catch(()=>{});
  });
 }
 return {mount,clear};
})();
