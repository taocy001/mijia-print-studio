'use strict';
const $=id=>document.getElementById(id);
const PATHS={plus:'M12 5v14M5 12h14',minus:'M5 12h14',close:'M6 6l12 12M18 6L6 18',chevron:'M9 5l7 7-7 7',arrow:'M4 12h15M13 6l6 6-6 6',printer:'M6 8V3h12v5M6 17H3V9h18v8h-3M6 14h12v7H6zM17 11h1',history:'M3 11a9 9 0 1 1 2 7M3 4v7h7M12 7v6l4 2',photo:'M3 3h18v18H3zM3 17l6-7 5 6 3-3 4 5M16 7h.01',collage:'M3 3h18v18H3zM12 3v18M3 12h18',polaroid:'M4 2h16v20H4zM7 5h10v11H7z',calendar:'M3 5h18v16H3zM3 10h18M7 2v6M17 2v6M7 14h2M14 14h2M7 18h2',id:'M3 4h18v16H3zM14 9h4M14 13h4M6 16q3-5 6 0M9 7a2 2 0 1 0 0 4a2 2 0 1 0 0-4',label:'M3 4h11l7 8-7 8H3zM7 9h.01M7 14h5',layout:'M3 3h18v18H3zM3 9h18M9 9v12',spark:'M12 2l3 7 7 3-7 3-3 7-3-7-7-3 7-3z',text:'M4 4h16M12 4v16M8 20h8',reset:'M4 10a8 8 0 1 1 1 8M4 4v6h6',compare:'M3 3h18v18H3zM12 1v22M5 16l4-5 3 4M15 7h3',rotate:'M15 3h6v6M20 4a9 9 0 0 0-16 7M4 16h9v6H4z',trash:'M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7M14 10v7',check:'M5 12l4 4L19 6'};
Object.assign(PATHS,{card:'M3 4h18v16H3zM7 11l3 3 7-7M7 17h10',idcard:'M3 5h18v14H3zM7 9h4v6H7zM14 10h4M14 14h4',template:'M3 3h18v18H3zM3 15l5-5 5 6 3-3 5 5M15 7h.01',
 reset:'M8 4H5a1 1 0 0 0-1 1v3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3M9 12h6M12 9v6',
 compare:'M12 3v18M8 5H5a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h3M16 5h3a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1h-3M4 15l4-4 4 4M12 15l4-4 4 4',
 rotate:'M19 9a7.5 7.5 0 1 0 .1 6M19 4v5h-5',
 emoji:'M21 12a9 9 0 1 1-18 0a9 9 0 1 1 18 0M8 9h.01M16 9h.01M7.5 14a5 5 0 0 0 9 0',
 resize:'M4 10V4h6M4 4l6 6M20 14v6h-6M20 20l-6-6',
 layers:'M3 8l9-5 9 5-9 5zM3 12l9 5 9-5M3 16l9 5 9-5'
});
const icon=name=>`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${PATHS[name]||PATHS.photo}"/></svg>`;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function icons(root=document){root.querySelectorAll('[data-icon]').forEach(e=>e.innerHTML=icon(e.dataset.icon));}icons();
const MODES=[['photo','照片'],['template','模板'],['collage','拼图'],['polaroid','拍立得'],['calendar','月历'],['id','证件照'],['label','姓名贴'],['card','卡片'],['idcard','ID 卡贴']];
const FILTERS=Tone.names.map(([id,name])=>[id,name,'none']);
const PAPER={5009:['3 寸方形背胶纸','方形照片 · 背胶相纸','3 寸背胶'],5012:['6 寸相纸','102 × 152 mm','6 寸'],5014:['4 寸拼接相纸','整版上下两幅','4 寸拼接']};
const defaults={mode:'photo',media:5012,orientation:'auto',fit:'cover',border:0,gap:16,filter:'none',caption:'',month:new Date().toISOString().slice(0,7),label:'名字，留在喜欢的东西上',subtitle:'THIS BELONGS TO ME',idSize:'35x45',photos:[],active:0};
let state={...defaults},native={},images=new Map(),peek=false,sheetKind='',toastTimer,renderQueued=false,lastJobPhase='',pendingPrint=null;
try{const old=JSON.parse(localStorage.getItem('liuying-draft')||'null');if(old)state={...defaults,...old};}catch(e){}
if(!MODES.some(m=>m[0]===state.mode))state.mode='photo';if(!PAPER[state.media])state.media=5012;
state.photos=(state.photos||[]).filter(p=>p.src==='/sample.svg'||/^\/private\/(photos|prints)\/[a-zA-Z0-9-]+\.jpg$/.test(p.src)).slice(0,6);
state.active=Math.min(Math.max(0,state.active||0),Math.max(0,state.photos.length-1));
for(const p of state.photos){
 if(p.filter==='warm')p.filter='sepia';if(p.fit===undefined)p.fit=state.fit||'cover';if(p.border===undefined)p.border=state.border||0;
 if(p.filter===undefined)p.filter=state.filter||'none';
 if(p.caption===undefined)p.caption=state.caption||'';
 if(p.templateId===undefined)p.templateId=state.mode==='template'?state.templateId:null;
 if(p.overlays===undefined)p.overlays=JSON.parse(JSON.stringify(state.sceneLayers?.[state.mode+(state.media===5014?':split':'')]||[]));
}
function save(){try{localStorage.setItem('liuying-draft',JSON.stringify(state));}catch(e){}}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,3400);}
function bridge(method,...args){if(window.Studio&&typeof Studio[method]==='function')return Studio[method](...args);if(method==='state')return '{}';toast('请在留影工坊 App 中使用此功能');}
function active(){return state.photos[state.active];}
function filter(p=active()){return FILTERS.find(f=>f[0]===(p?.filter??state.filter))||FILTERS[0];}
function selectPhoto(index){state.active=index;if(active()){state.fit=active().fit||'cover';state.border=active().border||0;}if(['photo','template'].includes(state.mode)){state.mode=state.media===5012&&active()?.templateId?'template':'photo';state.templateId=active()?.templateId;}schedule();}
if(state.labelTitle===undefined)state.labelTitle=state.label==='名字，留在喜欢的东西上'?'':state.label||'';
if(state.labelSubtitle===undefined)state.labelSubtitle=state.subtitle==='THIS BELONGS TO ME'?'':state.subtitle||'';
if(state.cardTitle===undefined)state.cardTitle=state.label==='名字，留在喜欢的东西上'?'':state.label||'';
if(state.cardSubtitle===undefined)state.cardSubtitle=state.subtitle==='THIS BELONGS TO ME'?'':state.subtitle||'';
CardArt.ready.then(schedule).catch(()=>toast('卡片素材加载失败，请重新打开 App'));
NameLabels.ready.then(schedule).catch(()=>toast('姓名贴素材加载失败，请重新打开 App'));
function ready(){return ['label','card'].includes(state.mode)||(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014))||state.photos.some(p=>images.has(p.src));}
function logicalSize(){
 if(state.media===5009)return [1040,1040];if(state.media===5014)return [1216,1824];
 let landscape=state.orientation==='landscape';
 if(state.orientation==='auto'&&state.mode==='card')return CardArt.spec().orientation==='landscape'?[1824,1216]:[1216,1824];
 if(state.orientation==='auto'&&state.mode==='idcard')return state.idCardOrientation==='portrait'?[1824,1216]:[1216,1824];
 if(state.orientation==='auto'){const p=active();landscape=['photo','template'].includes(state.mode)&&p&&p.width>p.height;}
 return landscape?[1824,1216]:[1216,1824];
}
function schedule(){if(renderQueued)return;renderQueued=true;requestAnimationFrame(()=>{renderQueued=false;render();save();});}
async function loadPhoto(p){if(images.has(p.src))return;const image=new Image();image.src=p.src;await image.decode();images.set(p.src,image);p.width=image.naturalWidth;p.height=image.naturalHeight;}
async function addPhotos(list){
 const fresh=list.slice(0,6-state.photos.length).map(p=>({...p,turn:0,zoom:1,x:0,y:0,filter:'none',caption:'',templateId:null,overlays:[],fit:'cover',border:0}));
 for(const p of fresh){try{await loadPhoto(p);state.photos.push(p);}catch(e){toast('照片未能载入');}}
 if(fresh.length)selectPhoto(Math.max(0,state.photos.length-fresh.length));
 if(list.length>fresh.length)toast('每次作品最多添加 6 张照片');schedule();
}
window.nativeEvent=async({type,value})=>{
 if(type==='photos')await addPhotos(value);if(type==='toast')toast(value);if(type==='loading')$('loading').hidden=!value;
};
function rounded(ctx,x,y,w,h,r,fill,stroke){ctx.beginPath();ctx.roundRect(x,y,w,h,r);if(fill){ctx.fillStyle=fill;ctx.fill();}if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=1.5;ctx.stroke();}}
function text(ctx,string,x,y,size,color='#354d40',align='center',font='sans-serif',maxWidth){ctx.font=`${size}px ${font}`;ctx.fillStyle=color;ctx.textAlign=align;ctx.textBaseline='middle';ctx.fillText(string,x,y,maxWidth);}
let collectingPhotoFrames=false,photoFrames=[],printPreview=null,composingFrames=null;
function photoGeometry(p,w,h,overrideFit){
 const image=window.CutoutEditor?CutoutEditor.source(p):images.get(p.src),turn=peek?0:((p.turn||0)%4+4)%4;
 const iw=turn%2?image.naturalHeight:image.naturalWidth,ih=turn%2?image.naturalWidth:image.naturalHeight;
 const fit=peek?'contain':overrideFit||p.fit||state.fit,base=fit==='contain'?Math.min(w/iw,h/ih):Math.max(w/iw,h/ih),scale=base*(peek?1:Math.max(1,p.zoom||1));
 const dw=iw*scale,dh=ih*scale,ex=Math.max(0,(dw-w)/2),ey=Math.max(0,(dh-h)/2);
 const dx=(peek?0:Math.max(-1,Math.min(1,p.x||0)))*ex,dy=(peek?0:Math.max(-1,Math.min(1,p.y||0)))*ey;
 return {image,toned:peek?image:Tone.image(image,filter(p)[0]),turn,scale,dw,dh,ex,ey,dx,dy,filterCSS:'none'};
}
function paintPhotoImage(ctx,g,x,y,w,h){
 ctx.save();ctx.filter=peek?'none':g.filterCSS;ctx.translate(x+w/2+g.dx,y+h/2+g.dy);ctx.rotate(g.turn*Math.PI/2);ctx.drawImage(g.toned||g.image,-g.image.naturalWidth*g.scale/2,-g.image.naturalHeight*g.scale/2,g.image.naturalWidth*g.scale,g.image.naturalHeight*g.scale);ctx.restore();
}
function drawPhoto(ctx,p,x,y,w,h,overrideFit){
 if(!p||!images.has(p.src)){ctx.fillStyle='#e8ece2';ctx.fillRect(x,y,w,h);text(ctx,'＋',x+w/2,y+h/2,Math.min(w,h)/7,'#b3bfaa');return;}
 if(collectingPhotoFrames)photoFrames.push({p,x,y,w,h,fit:overrideFit||p.fit||state.fit});if(composingFrames)composingFrames.push({p,x,y,w,h});
 const g=photoGeometry(p,w,h,overrideFit);
 ctx.save();ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();paintPhotoImage(ctx,g,x,y,w,h);ctx.restore();
}
function drawLabel(ctx,x,y,w,h){NameLabels.draw(ctx,x,y,w,h);}
function drawCalendar(ctx,p,x,y,w,h,monthValue=state.month){
 const plain=(state.calendarLayout==='plain'||state.media===5014),landscape=!plain&&w>h,margin=w*.055,px=x+margin,py=y+margin;
 const photoW=landscape?w*.48:w-margin*2,photoH=landscape?h-margin*2:h*.46;
 if(!plain)drawPhoto(ctx,p,px,py,photoW,photoH);
 const cx=landscape?x+w*.56:x+margin,cy=plain?y+h*.12:landscape?y+h*.15:y+h*.55,cw=landscape?w*.38:w-margin*2,ch=plain?h*.8:landscape?h*.7:h*.38;
 const [year,month]=monthValue.split('-').map(Number);const first=(new Date(year,month-1,1).getDay()+6)%7,days=new Date(year,month,0).getDate();
 text(ctx,`${String(month).padStart(2,'0')} / ${year}`,cx+cw/2,cy,ch*.12,'#3d5947','center','serif');
 const cellW=cw/7,cellH=ch*.105,startY=cy+ch*.2;
 ['一','二','三','四','五','六','日'].forEach((s,i)=>text(ctx,s,cx+cellW*(i+.5),startY,cellH*.36,'#9aa78e'));
 for(let day=1;day<=days;day++){
  const n=first+day-1,dateKey=`${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`,info=window.CALENDAR_DAYS?.[dateKey];
  text(ctx,''+day,cx+cellW*(n%7+.5),startY+cellH*(Math.floor(n/7)+1.35),cellH*.53,info?.[3]?'#48604e':info?.[2]||n%7>=5?'#ad8060':'#48604e','center','serif');
  if(info?.[1])text(ctx,info[1],cx+cellW*(n%7+.87),startY+cellH*(Math.floor(n/7)+1.12),cellH*.20,info[2]?'#b66c55':'#6a8170');
  if(state.lunar){const lunar=info?.[0]||new Intl.DateTimeFormat('zh-CN-u-ca-chinese',{day:'numeric'}).format(new Date(year,month-1,day));text(ctx,lunar,cx+cellW*(n%7+.5),startY+cellH*(Math.floor(n/7)+1.70),cellH*.20,'#8e9a89');}
 }
}
function drawId(ctx,p,x,y,w,h){
 const [mw,mh]=state.idSize.split('x').map(Number),iw=Math.round(mw*300/25.4),ih=Math.round(mh*300/25.4),g=28;
 const cols=Math.max(1,Math.floor((w-g)/(iw+g))),rows=Math.max(1,Math.floor((h-g)/(ih+g))),left=x+(w-(cols*iw+(cols-1)*g))/2,top=y+(h-(rows*ih+(rows-1)*g))/2;
 for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){const xx=left+c*(iw+g),yy=top+r*(ih+g);drawPhoto(ctx,p,xx,yy,iw,ih,'cover');ctx.strokeStyle='#c8cfc2';ctx.lineWidth=1;ctx.strokeRect(xx-.5,yy-.5,iw+1,ih+1);}
}
function drawPanel(ctx,x,y,w,h,photos){
 const first=photos[0],margin=first?.border??state.border,gap=state.gap,caption=first?.caption??state.caption;
 if(state.mode==='template'&&window.TemplateStudio&&state.media===5012){TemplateStudio.paint(ctx,first,x,y,w,h);return;}
 if(state.mode==='card'){StudioExtras.drawCard(ctx,x,y,w,h);return;}
 if(state.mode==='label'){drawLabel(ctx,x,y,w,h);return;}
 if(state.mode==='calendar'){drawCalendar(ctx,first,x,y,w,h);return;}
 if(state.mode==='id'){drawId(ctx,first,x,y,w,h);return;}
 if(state.mode==='polaroid'){
  const m=Math.min(w,h)*.08,side=Math.min(w-2*m,h*.75),xx=x+(w-side)/2,yy=y+Math.max(m,(h-side)*.25);
  drawPhoto(ctx,first,xx,yy,side,side);text(ctx,caption||'A little moment to keep.',x+w/2,yy+side+(h-(yy-y)-side)*.48,Math.min(w*.035,48),'#57614f','center','serif',w*.85);return;
 }
 const innerW=w-margin*2,innerH=h-margin*2;
 if(state.mode==='collage'){
  const count=Math.min(6,Math.max(2,photos.length)),cols=state.collageLayout==='vertical'?1:state.collageLayout==='horizontal'?count:state.collageLayout==='grid'?Math.ceil(Math.sqrt(count)):count===2?(w>h?2:1):2,rows=Math.ceil(count/cols),pw=(innerW-gap*(cols-1))/cols,ph=(innerH-gap*(rows-1))/rows;
  for(let i=0;i<count;i++)drawPhoto(ctx,photos[i]||first,x+margin+(i%cols)*(pw+gap),y+margin+Math.floor(i/cols)*(ph+gap),pw,ph);
 }else drawPhoto(ctx,first,x+margin,y+margin,innerW,innerH);
 if(caption){const band=Math.max(65,h*.065);ctx.fillStyle='#fffef5e8';ctx.fillRect(x,y+h-band,w,band);text(ctx,caption,x+w/2,y+h-band/2,Math.min(w*.031,43),'#52624c','center','sans-serif',w*.9);}
}
function compose(includeLayers=true,layerMode='photo'){
 const [w,h]=logicalSize(),canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d');ctx.fillStyle='#ffffff';ctx.fillRect(0,0,w,h);
 if(peek&&active()){drawPhoto(ctx,active(),0,0,w,h,'contain');return canvas;}
 const photos=state.mode==='collage'?state.photos:[active()];
 const frames=[],previousFrames=composingFrames;composingFrames=frames;
 try{if(state.mode==='idcard'){StudioExtras.drawIdCardSheet(ctx,w,h);}else if(state.mode==='calendar'&&state.media===5014){const [year,month]=state.month.split('-').map(Number),next=month===12?`${year+1}-01`:`${year}-${String(month+1).padStart(2,'0')}`;drawCalendar(ctx,null,0,0,w,h/2,state.month);drawCalendar(ctx,null,0,h/2,w,h/2,next);}else if(state.media===5014){drawPanel(ctx,0,0,w,h/2,[state.photos[Math.floor(state.active/2)*2]]);drawPanel(ctx,0,h/2,w,h/2,[state.photos[Math.floor(state.active/2)*2+1]||state.photos[Math.floor(state.active/2)*2]]);}else drawPanel(ctx,0,0,w,h,photos);}finally{composingFrames=previousFrames;}
 if(layerMode==='mask'){ctx.fillStyle='#000';ctx.fillRect(0,0,w,h);}
 if(window.StudioExtras)StudioExtras.paintCoat(ctx,w,h,frames,layerMode);
 if(includeLayers&&window.LayerEditor){if(!['label','card'].includes(state.mode)&&!(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014))&&(state.media===5014||state.mode==='collage')){for(const f of frames){ctx.save();ctx.beginPath();ctx.rect(f.x,f.y,f.w,f.h);ctx.clip();ctx.translate(f.x,f.y);LayerEditor.paint(ctx,f.w,f.h,f.p.overlays||[],layerMode);ctx.restore();}}else LayerEditor.paint(ctx,w,h,undefined,layerMode);}
 return canvas;
}
function physical(logical){
 const canvas=document.createElement('canvas');canvas.width=state.media===5009?1040:1216;canvas.height=state.media===5009?1040:1824;const ctx=canvas.getContext('2d');
 ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);
 if(state.media===5009){ctx.translate(1040,1040);ctx.rotate(Math.PI);ctx.drawImage(logical,0,0);}
 else if(logical.width>logical.height){ctx.translate(1216,0);ctx.rotate(Math.PI/2);ctx.drawImage(logical,0,0);}else ctx.drawImage(logical,0,0);
 return canvas;
}
function render(){
 const has=ready();document.body.classList.toggle('has-work',has);$('paperStage').hidden=!has;$('editorToolbar').hidden=!has;$('decorationActions').hidden=!has;$('originalBadge').hidden=!peek;$('compare').classList.toggle('held',peek);$('intro').hidden=has;$('empty').hidden=has;$('preview').hidden=!has;$('editing').hidden=!state.photos.length;
 $('spliceGuide').hidden=!has||state.media!==5014;
 $('modes').innerHTML=MODES.map(([key,name])=>`<button class="mode ${state.mode===key?'active':''}" data-mode="${key}" aria-pressed="${state.mode===key}">${icon(key)}${name}</button>`).join('');
 $('previewTitle').textContent=has?`${MODES.find(m=>m[0]===state.mode)[1]} · 打印预览`:'你的下一张珍藏';
 $('paperBtn').innerHTML='<span class="paper-long">'+esc(PAPER[state.media][0])+'</span><span class="paper-short" aria-hidden="true">'+(state.media===5009?'3 寸<br>背胶':state.media===5014?'4 寸<br>拼接':'6 寸<br>相纸')+'</span>'+icon('chevron');$('paperBtn').setAttribute('aria-label',PAPER[state.media][0]);$('paperInfo').textContent=`${PAPER[state.media][2]} · ${PAPER[state.media][1]}`;
 $('paperTag').textContent=PAPER[state.media][2];$('gestureHint').textContent=has&&state.mode!=='label'?'上下滑动浏览 · 点文字或表情可编辑':'好照片，值得一张相纸';
 if(has){photoFrames=[];collectingPhotoFrames=true;const output=compose(true,'editor');printPreview=output;collectingPhotoFrames=false;const canvas=$('preview');canvas.width=output.width;canvas.height=output.height;canvas.getContext('2d').drawImage(output,0,0);}
 const photoMarkup=state.photos.map((p,i)=>`<div class="photo-thumb"><button class="photo-item ${i===state.active?'selected':''}" data-photo="${i}" aria-label="选择第 ${i+1} 张照片"><img src="${esc(p.src)}" alt=""></button><button class="remove-photo" data-remove-photo="${i}" aria-label="删除第 ${i+1} 张照片">${icon('close')}</button></div>`).join('')+(state.photos.length<6?`<button class="add-photo" id="addMore" aria-label="添加照片">${icon('plus')}</button>`:'');
 if($('photos').innerHTML!==photoMarkup)$('photos').innerHTML=photoMarkup;
 $('layoutSummary').textContent=state.mode==='label'?NameLabels.count()+' 枚姓名贴':state.mode==='card'?'卡片':state.mode==='calendar'?state.month:state.mode==='id'?state.idSize.replace('x',' × ')+' mm':state.border?'白边 '+(state.border*25.4/300).toFixed(1)+' mm':state.fit==='cover'?'铺满相纸':'完整保留';
 $('filterSummary').textContent=['label','card'].includes(state.mode)?'固定配色':filter()[1];$('filterBtn').disabled=['label','card'].includes(state.mode)||(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014));$('textBtn').disabled=!has;$('textSummary').textContent=['label','card'].includes(state.mode)?'姓名与小字':'自由排版';
 if(window.CropEditor)CropEditor.render();if(window.LayerEditor)LayerEditor.refresh();
 updateStatus();
}
function updateStatus(){
 $('printBtn').disabled=!ready()||native.busy||native.unresolved;
 $('dockTitle').textContent=ready()?'一张，刚刚好。':'准备好你的第一张';
 $('dockMeta').textContent=`${PAPER[state.media][0]} · ${state.mode==='collage'?Math.min(6,state.photos.length)+' 张拼成 1 张':state.media===5014?'上下两幅 · 1 张':'单张打印'}`;
 const d=native.device||{},fresh=d.connected&&(Date.now()-d.checkedAt<60000);
 $('deviceText').textContent=native.busy?native.message:fresh?`已连接${d.alert&&d.alert!=='::0'?' · 设备有告警':d.state==='30'?' · 待机':' · 可以打印'}`:'点击连接 · 蓝牙直连';
 const j=native.job||{};$('jobBanner').hidden=!j.token||(!native.busy&&!native.unresolved);
 if(j.token){$('jobLabel').textContent=j.message||native.message;$('jobProgress').style.width=(j.progress||0)+'%';$('jobAction').textContent=native.unresolved?'检查任务':'详情';}
 if(j.phase==='done'&&lastJobPhase&&lastJobPhase!=='done')toast('打印完成，去取你的照片吧。');lastJobPhase=j.phase;
}
function poll(){try{native=JSON.parse(bridge('state')||'{}');updateStatus();}catch(e){}}
function openSheet(kind,title,html){const samePanel=sheetKind===kind&&!$('sheet').hidden;$('sheet').setAttribute('aria-modal','true');document.body.classList.remove('layer-editing');$('sheet').classList.remove('layer-sheet','emoji-sheet');sheetKind=kind;$('sheetTitle').textContent=title;$('sheetBody').innerHTML=html;$('sheet').hidden=false;$('scrim').hidden=false;document.body.style.overflow='hidden';icons($('sheet'));$('sheet').scrollTop=0;$('sheetBody').scrollTop=0;$('sheetBody').querySelectorAll('[data-close]').forEach(b=>b.remove());if(window.Drawer)Drawer.open(kind,samePanel);}
function closeSheet(){if(window.Drawer)Drawer.reset();document.body.classList.remove('layer-editing');$('sheet').classList.remove('layer-sheet','emoji-sheet');sheetKind='';$('sheet').hidden=true;$('scrim').hidden=true;document.body.style.overflow='';pendingPrint=null;}
window.goBack=()=>{if(sheetKind){closeSheet();return true;}if(window.LayerEditor&&LayerEditor.selected()){LayerEditor.select(null);return true;}return false;};
function segments(key,choices){return `<div class="segments">${choices.map(([v,n])=>`<button data-setting="${key}" data-value="${v}" class="${String(state[key])===String(v)?'selected':''}">${n}</button>`).join('')}</div>`;}
function openWorkType(){openSheet('workType','作品类型',`<div class="mode-grid">${MODES.filter(m=>m[0]!=='template').map(([key,name])=>`<button data-layout-mode="${key}" class="${state.mode===key?'selected':''}">${icon(key)}<span>${name}</span></button>`).join('')}</div>`);}
function openLayout(){
 let html='';html+=['label','id'].includes(state.mode)?'':`<div class="field"><label>照片如何放进相纸</label>${segments('fit',[['cover','铺满相纸'],['contain','完整保留']])}</div>`;
 if(state.media===5012)html+=`<div class="field"><label>相纸方向 <span>旋转照片不会改变相纸方向</span></label>${segments('orientation',[['auto','自动'],['portrait','竖版'],['landscape','横版']])}</div>`;
 if(['photo','collage'].includes(state.mode))html+=`<div class="field"><label>白边 <span id="borderValue">${(state.border*25.4/300).toFixed(1)} mm</span></label><input type="range" id="borderInput" min="0" max="100" step="5" value="${state.border}"></div>`;
 if(state.mode==='collage')html+=`<div class="field"><label>照片间距 <span id="gapValue">${(state.gap*25.4/300).toFixed(1)} mm</span></label><input id="gapInput" type="range" min="0" max="80" step="4" value="${state.gap}"></div><p class="hint">最多 6 张照片拼成一张相纸。点击下方缩略图，可单独调整每张照片的位置。</p>`;
 if(state.mode==='calendar')html+=`<div class="field"><label>选择月份</label><input id="monthInput" type="month" value="${esc(state.month)}"></div>`;
 if(state.mode==='id')html+=`<div class="field"><label>证件照尺寸</label>${segments('idSize',[['25x35','一寸 · 25×35'],['35x45','35×45'],['35x49','二寸 · 35×49'],['33x48','大一寸 · 33×48'],['51x51','美签 · 51×51'],['45x45','日签 · 45×45']])}</div><p class="hint">按 300 dpi 实际尺寸排版。换底仅在本机处理。建议使用人物清晰、背景简单的正面照片。</p>`;
 if(state.mode==='label')html+=`<p class="hint">当前相纸共 ${NameLabels.count()} 枚。内容可在“文字”中修改。</p>`;
 html+='<button class="full-button" data-close>完成调整</button>';
 openSheet('layout','排版',html);
}
function openFilters(){const source=images.get(active()?.src)||images.get('/sample.svg');openSheet('filters','色调',`<div class="filter-grid">${FILTERS.map(([key,name])=>`<button class="filter-card ${filter()[0]===key?'active':''}" data-filter="${key}"><div class="filter-swatch"><img alt="${name}" data-tone="${key}"></div><small>${name}</small></button>`).join('')}</div><div class="field"><label for="toneSharp">锐度</label><select id="toneSharp"><option value="0">标准</option><option value="1">高</option><option value="2">低</option></select></div>`);$('toneSharp').value=state.sharpen||0;$('toneSharp').onchange=e=>{state.sharpen=+e.target.value;save();};if(source)for(const img of $('sheetBody').querySelectorAll('[data-tone]'))img.src=Tone.image(source,img.dataset.tone,true).toDataURL('image/jpeg',.9);}

function openLegacyText(){let html=['label','card'].includes(state.mode)?`<div class="field"><label>姓名或主标题</label><input id="labelInput" type="text" maxlength="30" value="${esc(state.mode==='label'?state.labelTitle:state.cardTitle)}" placeholder="写下名字"></div><div class="field"><label>第二行小字</label><input id="subtitleInput" type="text" maxlength="50" value="${esc(state.mode==='label'?state.labelSubtitle:state.cardSubtitle)}"></div>`:`<div class="field"><label>想留在照片上的话 <span>最多 40 字</span></label><input id="captionInput" type="text" maxlength="40" value="${esc(active()?.caption??state.caption)}" placeholder="比如：和你在一起的每一天"></div><p class="hint">${['calendar','id'].includes(state.mode)?'月历和证件照采用固定版式，不叠加文字。':'文字会显示在照片底部，留空即可隐藏。'}</p>`;
 openSheet('text','不止一张照片',html+'<button class="full-button" data-close>完成</button>');}
function openPaper(){openSheet('paper','相纸类型',Object.entries(PAPER).map(([key,p])=>`<button class="paper-option ${state.media==key?'active':''}" data-paper="${key}"><span class="paper-shape ${key==='5009'?'square':key==='5014'?'split':''}"></span><span><strong>${p[0]}</strong><small>${p[1]}</small></span><span class="check">${state.media==key?icon('check'):''}</span></button>`).join('')+'<p class="hint">普通 6 寸与 4 寸拼接共用同类纸盒，无法自动区分。请选择实际装入的相纸，避免尺寸不匹配。</p>');}
function openDevice(){const d=native.device||{};openSheet('device','你的打印机',`<div class="info-row"><span>设备</span><strong>米家桌面照片机 2</strong></div><div class="info-row"><span>连接</span><strong>${d.connected?'蓝牙直连 · 已读取状态':'尚未读取状态'}</strong></div><div class="info-row"><span>当前选择相纸</span><strong>${PAPER[state.media][0]}</strong></div><div class="info-row"><span>色带余量</span><strong>${d.ribbon>=0?d.ribbon+' 张':'等待设备提供有效读数'}</strong></div>${d.alert&&d.alert!=='::0'?`<p class="hint">设备告警：${esc(d.alert)}</p>`:''}<button class="full-button" id="connectNow">${icon('printer')} 连接并刷新状态</button><button class="full-button secondary-button" id="changePaper">更换相纸类型</button><button class="full-button secondary-button" id="systemBluetooth">打开系统蓝牙设置</button><p class="hint">请保持打印机开机，并关闭米家的打印机页面。仅连接系统中已配对的兼容打印机。</p>`);}
async function historyPreview(job){
 const src='/private/'+job.file,image=new Image();image.src=src;await image.decode();
 const landscape=job.orientation==='landscape',canvas=document.createElement('canvas');
 canvas.width=landscape?450:job.media===5009?360:300;canvas.height=landscape?300:job.media===5009?360:450;
 const ctx=canvas.getContext('2d');
 if(job.media===5009){ctx.translate(canvas.width,canvas.height);ctx.rotate(Math.PI);ctx.drawImage(image,0,0,canvas.width,canvas.height);}
 else if(landscape){ctx.translate(0,canvas.height);ctx.rotate(-Math.PI/2);ctx.drawImage(image,0,0,canvas.height,canvas.width);}
 else ctx.drawImage(image,0,0,canvas.width,canvas.height);
 return canvas.toDataURL('image/jpeg',.85);
}
function fillHistoryPreviews(list){list.forEach(async(job,i)=>{const el=$('sheetBody').querySelector('[data-history-image="'+i+'"]');try{const src=await historyPreview(job);if(el&&el.isConnected)el.src=src;}catch(e){}});}
function openHistory(){const list=native.history||[];openSheet('history','留过的美好',list.length?`<div class="history-grid">${list.map((j,i)=>`<button class="history-card" data-history="${i}"><img data-history-image="${i}" src="/private/${esc(j.file)}" alt="历史作品"><strong>${esc(j.title||'照片')}</strong><small>${new Date(j.createdAt).toLocaleDateString('zh-CN')} · ${j.phase==='done'?'已完成':j.phase==='cancelled'?'已取消':'已中止'}</small></button>`).join('')}</div>`:'<div class="blank-state">这里会收好每一次打印。<br>先做一张喜欢的作品吧。</div>');fillHistoryPreviews(list);}
function openJob(){const j=native.job||{};openSheet('job','打印进度',`<p style="line-height:1.9">${esc(j.message||'暂无任务')}</p><div class="info-row"><span>作品</span><strong>${esc(j.title||'照片')}</strong></div><div class="info-row"><span>任务编号</span><strong>${j.jobId||'尚未获得'}</strong></div><div class="info-row"><span>打印数量</span><strong>${j.batchCount||1} 个作品 · 每个 ${j.copies||1} 份</strong></div>${native.unresolved?`<button class="full-button" id="reconcileJob" ${native.busy?'disabled':''}>重新读取任务状态</button>${!j.jobId&&j.phase!=='prepared'?'<button class="full-button secondary-button" id="resolveUnknown">已检查打印机，结束本次记录</button>':''}<button class="full-button danger-button" id="cancelJob">${j.phase==='prepared'?'取消尚未提交的任务':'请求取消任务'}</button><p class="hint">中断后只检查原任务，不会自动重复提交照片。</p>`:'<button class="full-button" data-close>完成</button>'}`);}
async function preparePrintPages(){
 const original=state.active,originalMode=state.mode,originalTemplate=state.templateId,wasPeek=peek,pages=[];
 const indices=['collage','idcard'].includes(state.mode)||['label','card'].includes(state.mode)||(state.mode==='calendar'&&(state.calendarLayout==='plain'||state.media===5014))?[original]:state.media===5014?state.photos.map((_,i)=>i).filter(i=>i%2===0):state.photos.map((_,i)=>i);
 try{if(['label','card'].includes(state.mode))await NameLabels.ready;if(state.mode==='card')await CardArt.ready;peek=false;for(const index of indices){state.active=index;if(['photo','template'].includes(originalMode)){state.mode=state.media===5012&&active()?.templateId?'template':'photo';state.templateId=active()?.templateId;}if(window.TemplateStudio)await TemplateStudio.ensureCurrent();const logical=compose(),output=physical(logical);let jpeg;
  for(const quality of [.92,.90,.85,.80]){jpeg=output.toDataURL('image/jpeg',quality);if(atob(jpeg.split(',')[1]).length<=1048576)break;}
  if(atob(jpeg.split(',')[1]).length>1048576)throw Error('作品数据较大，请减少拼图照片后重试');
  const oc=physical(compose(true,'mask'));const pixels=oc.getContext('2d').getImageData(0,0,oc.width,oc.height).data;let hasOc=false;for(let i=0;i<pixels.length;i+=4){if(pixels[i]>100){hasOc=true;break;}}
  pages.push({ocMask:hasOc?oc.toDataURL('image/png').split(',')[1]:null,sharpen:+state.sharpen||0,copies:state.copies||1,threshold:active()?.coatThreshold||state.coatThreshold||100,base64:jpeg.split(',')[1],preview:logical.toDataURL('image/jpeg',.72),media:state.media,title:MODES.find(m=>m[0]===state.mode)[1],orientation:logical.width===logical.height?'square':logical.width>logical.height?'landscape':'portrait'});
 }}finally{state.active=original;state.mode=originalMode;state.templateId=originalTemplate;peek=wasPeek;await TemplateStudio?.ensureCurrent();}
 return pages;
}
async function confirmPrint(){
 if(window.LayerEditor)await LayerEditor.ready;
 if(!ready())return;if(!native.permission){toast('请先连接打印机，并允许附近设备权限');openDevice();return;}
 $('printBtn').disabled=true;
 try{const pages=await preparePrintPages();if(!pages.length)return;
  pendingPrint={pages};
  openSheet('confirm','打印预览',`<div class="print-pages">${pages.map((p,i)=>`<figure><div class="confirmation-preview"><img src="${p.preview}" alt="第 ${i+1} 张最终打印效果"></div><figcaption>第 ${i+1} / ${pages.length} 张 · ${p.orientation==='square'?'方形':p.orientation==='landscape'?'横版':'竖版'} · ${p.copies} 份${p.ocMask?' · 含覆膜隐藏内容':''}</figcaption></figure>`).join('')}</div><div class="confirm-summary"><strong>${PAPER[state.media][0]} · 共 ${pages.reduce((n,p)=>n+p.copies,0)} 张相纸</strong><span>${filter()[1]}</span></div><p class="hint">${state.media===5014&&state.photos.length%2?'最后一张照片重复填满上下两格。':''}${state.media===5014?'同页覆膜深浅使用第一张照片的设置。':''}${pages.length>1?'上下滑动查看全部打印页。':''}将依次打印以上全部内容；中断时停止后续照片，不会自动重复打印。</p><button class="full-button" id="confirmSend">${icon('printer')} 确认打印 ${pages.reduce((n,p)=>n+p.copies,0)} 张</button>`);
 }catch(e){toast(e.message||'无法生成打印预览');}finally{updateStatus();}
}
function changeSetting(key,value){if(['filter','fit','border'].includes(key)&&active())active()[key]=value;state[key]=value;render();save();}
$('modes').addEventListener('click',e=>{const b=e.target.closest('[data-mode]');if(!b)return;state.mode=b.dataset.mode;schedule();});
$('photos').addEventListener('click',e=>{const remove=e.target.closest('[data-remove-photo]');if(remove){removePhoto(+remove.dataset.removePhoto);return;}const b=e.target.closest('[data-photo]');if(b){selectPhoto(+b.dataset.photo);}else if(e.target.closest('#addMore'))bridge('pick',Math.max(0,6-state.photos.length));});
function removePhoto(index){const photo=state.photos[index];if(!photo)return;const oldActive=active();state.photos.splice(index,1);state.active=Math.max(0,oldActive===photo?Math.min(index,state.photos.length-1):state.photos.indexOf(oldActive));selectPhoto(state.active);document.getElementById('photoUndo')?.remove();const bar=document.createElement('div');bar.id='photoUndo';bar.className='layer-undo';bar.innerHTML='已移除照片 <button>撤销</button>';document.body.append(bar);bar.querySelector('button').onclick=()=>{if(state.photos.length>=6){toast('最多保留 6 张照片');return;}state.photos.splice(Math.min(index,state.photos.length),0,photo);selectPhoto(state.photos.indexOf(photo));bar.remove();};setTimeout(()=>bar.remove(),6000);}
$('menuBtn').onclick=()=>{openSheet('menu','更多',`<button class="menu-row" id="menuWorkType">${icon('layout')}<span>作品类型</span>${icon('chevron')}</button><button class="menu-row" id="menuDevice">${icon('printer')}<span>打印机与连接</span>${icon('chevron')}</button><button class="menu-row" id="menuHistory">${icon('history')}<span>打印记录</span>${icon('chevron')}</button><p class="hint">未放大时上下滑动页面；放大后可单指拖动照片。虚线框内为打印内容。</p>`);$('menuWorkType').onclick=openWorkType;$('menuDevice').onclick=openDevice;$('menuHistory').onclick=openHistory;};
$('sheetBody').addEventListener('click',async e=>{
 const b=e.target.closest('button');if(!b)return;
 if(b.dataset.layoutMode){state.mode=b.dataset.layoutMode;if(state.mode==='photo'&&active()){active().templateId=null;state.templateId=null;}schedule();openLayout();}
 else if(b.hasAttribute('data-close'))closeSheet();
 else if(b.dataset.setting){changeSetting(b.dataset.setting,b.dataset.value);openLayout();}
 else if(b.dataset.filter){changeSetting('filter',b.dataset.filter);openFilters();}
 else if(b.dataset.paper){state.media=+b.dataset.paper;if(state.mode==='template'&&state.media!==5012){state.mode='photo';toast('当前模板适用 6 寸相纸，已保留照片并切回普通排版');}if(state.media===5014&&state.mode==='collage'){state.mode='photo';toast('拼接纸会将前两张照片分别排在上下两幅');}schedule();closeSheet();}
 else if(b.dataset.history!==undefined){const j=native.history[+b.dataset.history];openSheet('historyDetail','这张，已经留住了',`<div class="confirmation-preview"><img data-history-image="0" src="/private/${esc(j.file)}" alt="打印记录"></div><p class="hint">${esc(j.message)} · ${PAPER[j.media]?.[0]||'相纸'}</p><button class="full-button" id="importHistory" data-src="/private/${esc(j.file)}" data-media="${j.media}" data-orientation="${j.orientation}">作为新照片继续创作</button>`);fillHistoryPreviews([j]);}
 else if(b.id==='importHistory'){
  if(state.photos.length>=6){toast('最多 6 张照片，请先移除一张');return;}
  const img=new Image();img.src=b.dataset.src;await img.decode();
  await addPhotos([{src:img.src.replace(location.origin,''),width:img.naturalWidth,height:img.naturalHeight}]);
  const photo=active();photo.fit='contain';photo.border=0;photo.turn=+b.dataset.media===5009?2:b.dataset.orientation==='landscape'?3:0;
  state.mode='photo';selectPhoto(state.active);closeSheet();schedule();
 }
 else if(b.id==='connectNow'){bridge('connect');closeSheet();poll();}
 else if(b.id==='changePaper')openPaper();else if(b.id==='systemBluetooth')bridge('bluetoothSettings');
 else if(b.id==='confirmSend'){
  if(!pendingPrint)return;b.disabled=true;const p=pendingPrint;let result;
  try{result=JSON.parse(bridge('printBatch',JSON.stringify(p.pages.map(({preview,...page})=>page)))||'{}');}catch(err){result={error:'打印请求未确认，请检查任务'};}
  if(result.ok){closeSheet();poll();toast('正在连接打印机，准备传送照片');}else{b.disabled=false;toast(result.error||'无法提交打印');}
 }else if(b.id==='reconcileJob'){bridge('reconcile');closeSheet();}
 else if(b.id==='resolveUnknown'){bridge('resolveUnknown');closeSheet();}else if(b.id==='cancelJob'){if(native.job?.phase==='prepared')bridge('discardPrepared');else bridge('cancel');closeSheet();}
});
$('sheetBody').addEventListener('input',e=>{
 const map={borderInput:'border',gapInput:'gap',monthInput:'month',captionInput:'caption',labelInput:state.mode==='label'?'labelTitle':'cardTitle',subtitleInput:state.mode==='label'?'labelSubtitle':'cardSubtitle'},key=map[e.target.id];if(!key)return;
 if(key==='month'&&!/^\d{4}-\d{2}$/.test(e.target.value))return;
 if(key==='caption'&&active())active().caption=e.target.value;else state[key]=['border','gap'].includes(key)?+e.target.value:e.target.value;
 if(key==='border'&&active())active().border=state.border;
 if(key==='border')$('borderValue').textContent=(state.border*25.4/300).toFixed(1)+' mm';if(key==='gap')$('gapValue').textContent=(state.gap*25.4/300).toFixed(1)+' mm';schedule();
});
$('addFirst').onclick=()=>bridge('pick',Math.max(0,6-state.photos.length));$('sampleBtn').onclick=()=>addPhotos([{src:'/sample.svg',width:1200,height:800}]);
$('historyBtn').onclick=openHistory;$('deviceBtn').onclick=openDevice;$('paperBtn').onclick=openPaper;$('layoutBtn').onclick=openLayout;$('filterBtn').onclick=openFilters;$('textBtn').onclick=()=>window.LayerEditor&&LayerEditor.openHome('layers');$('printBtn').onclick=confirmPrint;$('jobAction').onclick=openJob;
$('closeSheet').onclick=closeSheet;$('scrim').onclick=closeSheet;
$('rotate').onclick=()=>{if(active()){active().turn=((active().turn||0)+1)%4;active().x=active().y=0;schedule();}};
$('reset').onclick=()=>{if(active()){Object.assign(active(),{turn:0,zoom:1,x:0,y:0});schedule();}};
$('zoomIn').onclick=()=>{if(active()){active().zoom=Math.min(4,(active().zoom||1)*1.12);schedule();}};
$('zoomOut').onclick=()=>{if(active()){active().zoom=Math.max(1,(active().zoom||1)/1.12);schedule();}};
$('compare').onpointerdown=e=>{e.preventDefault();peek=true;schedule();};
for(const name of ['pointerup','pointercancel','pointerleave'])$('compare').addEventListener(name,()=>{peek=false;schedule();});
$('preview').addEventListener('contextmenu',e=>e.preventDefault());
(async()=>{for(const p of state.photos){try{await loadPhoto(p);}catch(e){}}state.photos=state.photos.filter(p=>images.has(p.src));state.active=Math.min(state.active,Math.max(0,state.photos.length-1));if(window.LayerEditor)await LayerEditor.ready;if(window.TemplateStudio)await TemplateStudio.ensureCurrent();poll();render();setInterval(poll,900);})();
