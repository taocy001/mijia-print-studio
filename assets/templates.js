window.TemplateStudio=(()=>{
 let openRequest=0,refreshThumbnails=null;const thumbnails=new Map(),THUMB_LIMIT=108;
 function cached(key){if(!thumbnails.has(key))return null;const value=thumbnails.get(key);thumbnails.delete(key);thumbnails.set(key,value);return value;}
 function retain(key,value){thumbnails.delete(key);thumbnails.set(key,value);while(thumbnails.size>THUMB_LIMIT)thumbnails.delete(thumbnails.keys().next().value);}
 function selectTemplate(id,options){return window.EditHistory?EditHistory.run(()=>applyTemplate(id,options)):applyTemplate(id,options);}
 function applyTemplate(id,{preserveCrop=!!window.EffectBrowser?.active()}={}){if(!['photo','template'].includes(state.mode))return;state.mode=id?'template':'photo';state.templateId=id;if(active())active().templateId=id;if(!preserveCrop&&!id&&['cover','contain'].includes(active()?.fit||state.fit)){state.border=0;if(active()){active().border=0;if((active().fit||state.fit)==='contain')Object.assign(active(),{zoom:1,x:0,y:0});}}$('sheetBody').querySelectorAll('.template-card').forEach(button=>{const selected=(button.dataset.template||null)===id;button.classList.toggle('selected',selected);button.setAttribute('aria-pressed',String(selected));});schedule();refreshThumbnails?.();}
 function panelSize(){const [w,h]=logicalSize();return [w,state.media===5014?h/2:h];}
 function entry(p=active(),w=panelSize()[0],h=panelSize()[1]){const base=TEMPLATE_CATALOG.find(t=>t.id===(p?.templateId||state.templateId))||TEMPLATE_CATALOG[0];return OriginalTemplates.variant(base,w,h);}
 async function ensureCurrent(){}
 function paint(ctx,p,x,y,w,h,e=entry(p,w,h)){OriginalTemplates.paint(ctx,p,x,y,w,h,e);}
 async function open(){
  if(!['photo','template'].includes(state.mode))return;
  const request=++openRequest,selected=active()?active().templateId:state.templateId;const [pw,ph]=panelSize(),wide=pw>ph,orientation=pw===ph?'方形':wide?'横版':'竖版',label=state.media===5009?'3 寸背胶':state.media===5014?'4 寸拼接 · 单幅':'6 寸';
  openSheet('templates','模板',`<div class="template-heading"><span>${label} · ${orientation}</span>${state.media===5012?`<button id="templateOrientation">${wide?'切换竖版':'切换横版'}</button>`:''}</div><div class="template-grid"><button class="template-card plain-template ${!selected?'selected':''}" id="noTemplate" aria-pressed="${!selected}"><img alt="无模板"><span>无模板</span></button>${TEMPLATE_CATALOG.map(t=>`<button class="template-card ${selected===t.id?'selected':''}" aria-pressed="${selected===t.id}" data-template="${t.id}"><img alt="${esc(t.names.zh)}"><span>${esc(t.names.zh)}</span></button>`).join('')}</div>`);
  const grid=$('sheetBody').querySelector('.template-grid'),plain=$('noTemplate'),targets=[...grid.querySelectorAll('[data-template]')];
  const current=()=>request===openRequest&&sheetKind==='templates'&&grid.isConnected&&$('sheetBody').contains(grid);
  // Choices respond immediately, even while their previews are still being painted.
  if($('templateOrientation'))$('templateOrientation').onclick=async()=>{state.orientation=wide?'portrait':'landscape';try{await ensureCurrent();schedule();if(current())open();}catch(e){toast('模板未能载入');}};
  plain.onclick=()=>{if(current())selectTemplate(null);};
  targets.forEach(button=>button.onclick=()=>{if(current())selectTemplate(button.dataset.template);});
  const photo=active()||{src:'/sample.svg'};
  try{await loadPhoto(photo);}catch(e){if(current())toast('照片未能载入');return;}
  const fingerprint=()=>JSON.stringify([photo.src,pw,ph,photo.turn,photo.zoom,photo.x,photo.y,photo.fit||state.fit,photo.border??state.border,filter(photo)[0],peek,!!window.EffectBrowser?.active()]);
  let generation=0,lastSignature=null;
  async function fillThumbnails(){
  if(!current())return;const signature=fingerprint();if(signature===lastSignature)return;lastSignature=signature;
  const token=++generation,valid=()=>current()&&token===generation&&signature===fingerprint();
  const queue=[plain,...targets];
  while(queue.length&&valid()){
   // Yield before each small batch so opening, scrolling and changing tabs remain responsive.
   await new Promise(resolve=>requestAnimationFrame(resolve));
   if(!valid())return;
   const bounds=$('sheetBody').getBoundingClientRect();
   const priority=new Map(queue.map(button=>{const r=button.getBoundingClientRect();return [button,button.classList.contains('selected')?-1:r.bottom>bounds.top&&r.top<bounds.bottom?0:1];}));
   queue.sort((a,b)=>priority.get(a)-priority.get(b));
   const started=performance.now();
   do{
    const button=queue.shift();if(!valid()||!button.isConnected)return;
    try{
     const key=signature+'|'+(button.dataset.template||'plain'),hit=cached(key);if(hit){button.querySelector('img').src=hit;continue;}
     const c=document.createElement('canvas');c.width=Math.round(240*pw/Math.max(pw,ph));c.height=Math.round(240*ph/Math.max(pw,ph));const ctx=c.getContext('2d');
     Tone.preview(()=>{
      if(button===plain){ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);drawPhoto(ctx,!window.EffectBrowser?.active()&&(photo.fit||state.fit)==='contain'?{...photo,zoom:1,x:0,y:0}:photo,0,0,c.width,c.height);}
      else{const base=TEMPLATE_CATALOG.find(t=>t.id===button.dataset.template),e=OriginalTemplates.variant(base,pw,ph);ctx.scale(c.width/e.width,c.height/e.height);paint(ctx,photo,0,0,e.width,e.height,e);}
     },320);
     if(valid()&&button.isConnected){const url=c.toDataURL('image/jpeg',.85);retain(key,url);button.querySelector('img').src=url;}
    }catch(e){if(valid()&&button.isConnected)button.disabled=true;}
   }while(queue.length&&valid()&&performance.now()-started<6);
  }
  }
  refreshThumbnails=fillThumbnails;await fillThumbnails();
 }
 $('templateBtn').onclick=()=>window.EffectBrowser?EffectBrowser.toggle('templates'):open();return {open,paint,ensureCurrent,entry,apply:selectTemplate};
})();
