/* Save the selected print page, without editor or paper-preview overlays. */
window.ImageExport=(()=>{
 let busy=false,press=null,suppressUntil=0;
 const selector='.print-pages .confirmation-preview img';
 async function jpeg(page){
  const image=new Image();image.src='data:image/jpeg;base64,'+page.base64;await image.decode();
  const canvas=document.createElement('canvas'),wide=page.orientation==='landscape';
  canvas.width=wide?image.naturalHeight:image.naturalWidth;canvas.height=wide?image.naturalWidth:image.naturalHeight;
  const ctx=canvas.getContext('2d');
  if(page.media===5009){ctx.translate(canvas.width,canvas.height);ctx.rotate(Math.PI);ctx.drawImage(image,0,0);}
  else if(wide){ctx.translate(0,canvas.height);ctx.rotate(-Math.PI/2);ctx.drawImage(image,0,0);}
  else ctx.drawImage(image,0,0);
  return canvas.toDataURL('image/jpeg',.97);
 }
 async function save(index){
  if(busy||sheetKind!=='confirm'||!pendingPrint?.pages[index])return;
  const page=pendingPrint.pages[index];busy=true;
  try{
   const data=await jpeg(page);
   if(!window.BrowserTransport){
    if(typeof Studio.saveImage!=='function')throw Error('请更新 App 后再保存图片');
    const result=JSON.parse(Studio.saveImage(data.split(',')[1]));if(!result.ok)throw Error(result.error||'无法保存图片');
    return;
   }
   const bytes=Uint8Array.from(atob(data.split(',')[1]),c=>c.charCodeAt(0)),url=URL.createObjectURL(new Blob([bytes],{type:'image/jpeg'}));
   const link=document.createElement('a');link.href=url;link.download='mijia-photo-'+(index+1)+'.jpg';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
   busy=false;
  }catch(e){busy=false;toast(e.message||'图片保存失败，请重试');}
 }
 function index(image){return [...document.querySelectorAll(selector)].indexOf(image);}
 function cancel(){if(press)clearTimeout(press.timer);press=null;}
 document.addEventListener('pointerdown',e=>{
  if(press){cancel();return;}const image=e.target.closest(selector);if(!image||e.button!==0||!e.isPrimary)return;
  press={id:e.pointerId,x:e.clientX,y:e.clientY,timer:setTimeout(()=>{press=null;suppressUntil=Date.now()+1000;save(index(image));},500)};
 });
 document.addEventListener('pointermove',e=>{if(press&&(e.pointerId!==press.id||Math.hypot(e.clientX-press.x,e.clientY-press.y)>10))cancel();});
 for(const event of ['pointerup','pointercancel','scroll'])document.addEventListener(event,cancel,true);
 document.addEventListener('click',e=>{if(Date.now()<suppressUntil&&e.target.closest(selector)){e.preventDefault();e.stopImmediatePropagation();}},true);
 document.addEventListener('contextmenu',e=>{const image=e.target.closest(selector);if(!image)return;e.preventDefault();cancel();if(Date.now()>=suppressUntil){suppressUntil=Date.now()+1000;save(index(image));}});
 document.addEventListener('dragstart',e=>{if(e.target.closest(selector)){e.preventDefault();cancel();}});
 document.addEventListener('keydown',e=>{const image=e.target.closest(selector);if(image&&['Enter',' '].includes(e.key)){e.preventDefault();save(index(image));}});
 const mount=PaperPreview.mount;PaperPreview.mount=(container,pages)=>{mount(container,pages);container.querySelectorAll(selector).forEach((image,i)=>{image.tabIndex=0;image.setAttribute('role','button');image.setAttribute('aria-label','保存第 '+(i+1)+' 张成品图片');image.style.webkitTouchCallout='none';image.draggable=false;});};
 const event=nativeEvent;window.nativeEvent=async e=>{if(e.type==='imageSaved'){busy=false;if(e.value==='saved')toast('图片已保存');else if(e.value==='error')toast('图片保存失败，请重新选择保存位置');return;}return event(e);};
 return {save,jpeg};
})();
