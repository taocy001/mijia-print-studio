window.TemplateStudio=(()=>{
 let selectionRequest=0;
 function entry(){const base=TEMPLATE_CATALOG.find(t=>t.id===(active()?.templateId||state.templateId))||TEMPLATE_CATALOG[0];return logicalSize()[0]>logicalSize()[1]?{...base,...base.landscape}:base;}
 async function ensureCurrent(){}
 function paint(ctx,p,x,y,w,h,e=entry()){OriginalTemplates.paint(ctx,p,x,y,w,h,e);}
 async function open(){
  if(state.media!==5012){openSheet('templates','模板',`<p class="hint">这组模板适用 6 寸相纸。请先选择 6 寸相纸，再选模板。</p><button class="full-button" id="templatePaper">选择相纸</button>`);$('templatePaper').onclick=openPaper;return;}
  const wide=logicalSize()[0]>logicalSize()[1];openSheet('templates','模板',`<div class="template-heading"><span>6 寸 · ${wide?'横版':'竖版'}</span><button id="templateOrientation">${wide?'切换竖版':'切换横版'}</button></div><div class="template-grid"><button class="template-card plain-template ${state.mode!=='template'?'selected':''}" id="noTemplate" aria-pressed="${state.mode!=='template'}"><img alt="无模板"><span>无模板</span></button>${TEMPLATE_CATALOG.map(t=>`<button class="template-card ${state.mode==='template'&&entry().id===t.id?'selected':''}" data-template="${t.id}"><img alt="${esc(t.names.zh)}"><span>${esc(t.names.zh)}</span></button>`).join('')}</div>`);
  const photo=active()||{src:'/sample.svg'};await loadPhoto(photo);if(sheetKind!=='templates'||!$('noTemplate'))return;
  if(photo){const c=document.createElement('canvas');c.width=wide?240:160;c.height=wide?160:240;const ctx=c.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);drawPhoto(ctx,photo,0,0,c.width,c.height);$('noTemplate').querySelector('img').src=c.toDataURL('image/jpeg',.85);}
  const targets=[...$('sheetBody').querySelectorAll('[data-template]')];
  await Promise.all(targets.map(async button=>{const base=TEMPLATE_CATALOG.find(t=>t.id===button.dataset.template),e=wide?{...base,...base.landscape}:base;try{const c=document.createElement('canvas');c.width=wide?240:160;c.height=wide?160:240;const ctx=c.getContext('2d');ctx.scale(c.width/e.width,c.height/e.height);paint(ctx,photo,0,0,e.width,e.height,e);if(button.isConnected)button.querySelector('img').src=c.toDataURL('image/jpeg',.85);}catch{if(button.isConnected)button.disabled=true;}}));
  if(sheetKind!=='templates'||!$('templateOrientation'))return;
  $('templateOrientation').onclick=async()=>{state.orientation=wide?'portrait':'landscape';try{await ensureCurrent();schedule();open();}catch(e){toast('模板未能载入');}};
  $('noTemplate').onclick=()=>{selectionRequest++;state.mode='photo';state.templateId=null;if(active())active().templateId=null;schedule();closeSheet();};
  $('sheetBody').querySelectorAll('[data-template]').forEach(button=>button.onclick=async()=>{const token=++selectionRequest,id=button.dataset.template,e=TEMPLATE_CATALOG.find(t=>t.id===id);button.disabled=true;try{if(token!==selectionRequest||sheetKind!=='templates')return;state.templateId=id;if(active())active().templateId=id;state.mode='template';schedule();closeSheet();}catch(e){toast('模板未能载入');}finally{button.disabled=false;}});
 }
 $('templateBtn').onclick=open;return {open,paint,ensureCurrent,entry};
})();
