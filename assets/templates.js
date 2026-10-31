window.TemplateStudio=(()=>{
 let selectionRequest=0;
 function panelSize(){const [w,h]=logicalSize();return [w,state.media===5014?h/2:h];}
 function entry(p=active(),w=panelSize()[0],h=panelSize()[1]){const base=TEMPLATE_CATALOG.find(t=>t.id===(p?.templateId||state.templateId))||TEMPLATE_CATALOG[0];return OriginalTemplates.variant(base,w,h);}
 async function ensureCurrent(){}
 function paint(ctx,p,x,y,w,h,e=entry(p,w,h)){OriginalTemplates.paint(ctx,p,x,y,w,h,e);}
 async function open(){
  const [pw,ph]=panelSize(),wide=pw>ph,orientation=pw===ph?'方形':wide?'横版':'竖版',label=state.media===5009?'3 寸背胶':state.media===5014?'4 寸拼接 · 单幅':'6 寸';
  openSheet('templates','模板',`<div class="template-heading"><span>${label} · ${orientation}</span>${state.media===5012?`<button id="templateOrientation">${wide?'切换竖版':'切换横版'}</button>`:''}</div><div class="template-grid"><button class="template-card plain-template ${!active()?.templateId?'selected':''}" id="noTemplate" aria-pressed="${!active()?.templateId}"><img alt="无模板"><span>无模板</span></button>${TEMPLATE_CATALOG.map(t=>`<button class="template-card ${active()?.templateId===t.id?'selected':''}" data-template="${t.id}"><img alt="${esc(t.names.zh)}"><span>${esc(t.names.zh)}</span></button>`).join('')}</div>`);
  const photo=active()||{src:'/sample.svg'};await loadPhoto(photo);if(sheetKind!=='templates'||!$('noTemplate'))return;
  if(photo){const c=document.createElement('canvas');c.width=Math.round(240*pw/Math.max(pw,ph));c.height=Math.round(240*ph/Math.max(pw,ph));const ctx=c.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);drawPhoto(ctx,photo,0,0,c.width,c.height);$('noTemplate').querySelector('img').src=c.toDataURL('image/jpeg',.85);}
  const targets=[...$('sheetBody').querySelectorAll('[data-template]')];
  await Promise.all(targets.map(async button=>{const base=TEMPLATE_CATALOG.find(t=>t.id===button.dataset.template),e=OriginalTemplates.variant(base,pw,ph);try{const c=document.createElement('canvas');c.width=Math.round(240*pw/Math.max(pw,ph));c.height=Math.round(240*ph/Math.max(pw,ph));const ctx=c.getContext('2d');ctx.scale(c.width/e.width,c.height/e.height);paint(ctx,photo,0,0,e.width,e.height,e);if(button.isConnected)button.querySelector('img').src=c.toDataURL('image/jpeg',.85);}catch{if(button.isConnected)button.disabled=true;}}));
  if(sheetKind!=='templates')return;
  if($('templateOrientation'))$('templateOrientation').onclick=async()=>{state.orientation=wide?'portrait':'landscape';try{await ensureCurrent();schedule();open();}catch(e){toast('模板未能载入');}};
  $('noTemplate').onclick=()=>{selectionRequest++;state.mode='photo';state.templateId=null;if(active())active().templateId=null;schedule();closeSheet();};
  $('sheetBody').querySelectorAll('[data-template]').forEach(button=>button.onclick=async()=>{const token=++selectionRequest,id=button.dataset.template,e=TEMPLATE_CATALOG.find(t=>t.id===id);button.disabled=true;try{if(token!==selectionRequest||sheetKind!=='templates')return;state.templateId=id;if(active())active().templateId=id;state.mode='template';schedule();closeSheet();}catch(e){toast('模板未能载入');}finally{button.disabled=false;}});
 }
 $('templateBtn').onclick=open;return {open,paint,ensureCurrent,entry};
})();
