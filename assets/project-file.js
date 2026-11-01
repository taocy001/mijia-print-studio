/* Portable editing data only; device state and print jobs never enter files. */
window.ProjectFile=(()=>{
 const LIMIT=32*1024*1024,IMAGE_LIMIT=8*1024*1024;
 const fail=()=>{throw Error('作品文件无效或包含不支持的设置');};
 const number=(min,max,integer=false)=>v=>typeof v==='number'&&Number.isFinite(v)&&v>=min&&v<=max&&(!integer||Number.isInteger(v));
 const text=max=>v=>typeof v==='string'&&[...v].length<=max;
 const one=values=>v=>values.includes(v),bool=v=>typeof v==='boolean';
 const template=v=>v===null||TEMPLATE_CATALOG.some(t=>t.id===v);
 const ref=v=>typeof v==='string'&&/^a(?:[0-9]|1[0-9]|2[0-3])$/.test(v);
 const common={fit:one(['cover','contain','bottom']),border:number(0,200),filter:one(Tone.names.map(t=>t[0])),sharpen:number(0,2,true),caption:text(40),templateId:template,coatTexture:one(['','dots','lines','grid','hearts','diagonal','waves','sparkles','custom']),coatThreshold:number(60,140,true),coatDensity:number(50,150),coatSource:ref};
 const settings={...common,mode:one(MODES.map(m=>m[0])),media:one([5009,5012,5014]),sixLayout:one([5012,5014]),orientation:one(['auto','portrait','landscape']),stripBorder:number(0,200),gap:number(0,80),copies:number(1,10,true),active:number(0,5,true),month:v=>typeof v==='string'&&/^[0-9]{4}-(0[1-9]|1[0-2])$/.test(v)&&+v.slice(0,4)>0,calendarLayout:one(['photo','plain']),lunar:bool,idSize:one(['25x35','35x45','35x49','33x48','51x51','45x45']),idCardOrientation:one(['portrait','landscape']),collageLayout:one(['auto','vertical','horizontal','grid','strip']),labelTitle:text(30),labelSubtitle:text(50),cardTitle:text(30),cardSubtitle:text(50),nameGap:v=>v===null||number(0,5)(v),labelTheme:one(NAME_LABEL_CATALOG.map(x=>x.id.slice(5))),cardStyle:one(CARD_CATALOG.map(x=>x.id.slice(5))),labelBatchEnabled:bool};
 const photo={...common,src:ref,turn:number(0,3,true),zoom:number(1,4),x:number(-1,1),y:number(-1,1),idBackground:one(['','white','blue','red'])};
 const color=v=>typeof v==='string'&&(v===''||/^#(?:[a-f0-9]{3}|[a-f0-9]{6}|[a-f0-9]{8})$/i.test(v));
 const layer={kind:one(['text','emoji','qr']),text:text(512),fx:number(0,1),fy:number(0,1),sizePct:number(2,80),angle:number(-180,180),font:one(['sans','happy','brush','serif']),color,stroke:color,bubble:color,align:one(['left','center','right']),hidden:bool};
 const object=v=>{if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).some(k=>['__proto__','constructor','prototype'].includes(k)))fail();};
 function fields(value,schema){object(value);const out={};for(const [k,valid] of Object.entries(schema))if(value[k]!==undefined){if(!valid(value[k]))fail();out[k]=value[k];}return out;}
 function clean(value){
  const out=fields(value,settings);if(!out.mode||!out.media||!Array.isArray(value.photos)||value.photos.length>6)fail();let total=0;
  const layers=list=>{if(!Array.isArray(list)||list.length>100||(total+=list.length)>300)fail();return list.map((item,i)=>{const l={fx:.5,fy:.5,sizePct:9,angle:0,font:'sans',color:'#ffffff',stroke:'',bubble:'',align:'center',hidden:false,...fields(item,layer)};if(!l.kind||typeof l.text!=='string')fail();if(l.kind==='qr'){if(l.hidden||l.angle!==0||QrSticker.normalize(l.text)!==l.text)fail();QrSticker.code(l.text);}else if(l.sizePct>32||[...l.text].length>160)fail();if(l.kind==='emoji'&&!Object.values(SHARED_EMOJI).flat().some(e=>e.text.replaceAll('\ufe0f','')===l.text.replaceAll('\ufe0f','')))fail();return {...l,id:'project-layer-'+total+'-'+i};});};
  out.photos=value.photos.map(p=>{const v=fields(p,photo);if(!v.src)fail();v.overlays=layers(p.overlays||[]);if(p.idCutouts!==undefined){object(p.idCutouts);v.idCutouts=fields(p.idCutouts,{white:ref,blue:ref,red:ref});}if(v.idBackground&&!v.idCutouts?.[v.idBackground])fail();return v;});
  if((out.active||0)>=Math.max(1,out.photos.length))fail();
  out.sceneLayers={};if(value.sceneLayers!==undefined){object(value.sceneLayers);for(const [k,list] of Object.entries(value.sceneLayers)){if(!MODES.some(m=>m[0]===k))fail();const cleaned=layers(list);if(cleaned.length)out.sceneLayers[k]=cleaned;}}
  if(value.labelBatchItems!==undefined){if(!Array.isArray(value.labelBatchItems)||value.labelBatchItems.length>36)fail();out.labelBatchItems=value.labelBatchItems.map(p=>{object(p);if(!text(30)(p.title)||!p.title.trim()||!text(50)(p.subtitle)||/[\r\n\t]/.test(p.title+p.subtitle))fail();return {title:p.title,subtitle:p.subtitle};});}
  if(out.mode==='collage'&&out.media===5014&&out.collageLayout!=='strip')fail();
  for(const p of [out,...out.photos])if(p.coatTexture==='custom'&&!p.coatSource)fail();
  return out;
 }
 function references(value,fn){for(const p of [value,...value.photos]){for(const key of ['src','coatSource'])if(p[key])p[key]=fn(p[key]);if(p.idCutouts)for(const key of ['white','blue','red'])if(p.idCutouts[key])p.idCutouts[key]=fn(p.idCutouts[key]);}}
 async function encode(){
  const draft=JSON.parse(JSON.stringify(state)),paths=[],assets={};
  if(draft.sceneLayers)for(const key of Object.keys(draft.sceneLayers))if(!MODES.some(m=>m[0]===key))delete draft.sceneLayers[key];
  for(const p of [draft,...draft.photos])if(p.filter==='warm')p.filter='sepia';
  for(const p of draft.photos)if(p.idCutouts)p.idCutouts=p.idBackground?{[p.idBackground]:p.idCutouts[p.idBackground]}:{};
  references(draft,src=>{if(typeof src!=='string'||!(src==='/sample.svg'||/^\/private\/(photos|prints)\/[a-zA-Z0-9-]+\.jpg$/.test(src)||/^\/private\/cutouts\/u2netp-v1-[a-f0-9]{64}-(white|blue|red)\.jpg$/.test(src)))fail();let i=paths.indexOf(src);if(i<0){i=paths.length;paths.push(src);}if(i>=24)fail();return 'a'+i;});
  const editing=clean(draft);let pixels=0;
  for(const [i,src] of paths.entries()){
   if(!images.has(src))await loadPhoto({src});const image=images.get(src),w=image.naturalWidth||image.width,h=image.naturalHeight||image.height;if(!w||!h||w>8192||h>8192||w*h>24000000||(pixels+=w*h)>48000000)throw Error('作品照片尺寸超过保存上限');
   const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;canvas.getContext('2d').drawImage(image,0,0);const data=canvas.toDataURL('image/jpeg',.97).split(',')[1];if(data.length>IMAGE_LIMIT*4/3)throw Error('单张作品图片超过 8 MB');assets['a'+i]=data;
  }
  const result=JSON.stringify({format:'mijia-print-project',version:1,editing,assets});if(new TextEncoder().encode(result).length>LIMIT)throw Error('作品文件超过 32 MB');return result;
 }
 function jpegSize(bytes){
  if(bytes[0]!==255||bytes[1]!==216||bytes[bytes.length-2]!==255||bytes[bytes.length-1]!==217)fail();let i=2;
  while(i+3<bytes.length){if(bytes[i++]!==255)fail();while(bytes[i]===255)i++;const marker=bytes[i++];if(marker===217||marker===218)break;
   const length=(bytes[i]<<8)|bytes[i+1];if(length<2||i+length>bytes.length)fail();
   if([192,193,194].includes(marker)){if(length<8)fail();return [(bytes[i+5]<<8)|bytes[i+6],(bytes[i+3]<<8)|bytes[i+4]];}i+=length;
  }fail();
 }
 async function decode(raw){
  if(typeof raw!=='string'||new TextEncoder().encode(raw).length>LIMIT)fail();const file=JSON.parse(raw);object(file);if(file.format!=='mijia-print-project'||file.version!==1)throw Error('不支持此作品文件版本');
  const editing=clean(file.editing);object(file.assets);const entries=Object.entries(file.assets);if(entries.length>24)fail();const used=new Set();references(editing,id=>{used.add(id);if(!Object.hasOwn(file.assets,id))fail();return id;});if(used.size!==entries.length)fail();
  let pixels=0;const decoded={};for(const [id,data] of entries){if(!ref(id)||typeof data!=='string'||!data||data.length>IMAGE_LIMIT*4/3||!/^\/9j\/[A-Za-z0-9+/]*={0,2}$/.test(data))fail();const bytes=Uint8Array.from(atob(data),c=>c.charCodeAt(0));if(bytes.length>IMAGE_LIMIT)fail();const [w,h]=jpegSize(bytes);if(!w||!h||w>8192||h>8192||w*h>24000000||(pixels+=w*h)>48000000)throw Error('作品图片总尺寸超过上限');const im=new Image();im.src='data:image/jpeg;base64,'+data;await im.decode();if(!im.naturalWidth||!im.naturalHeight||im.naturalWidth>8192||im.naturalHeight>8192||im.naturalWidth*im.naturalHeight>24000000||im.naturalWidth!==w||im.naturalHeight!==h)fail();decoded[id]={data,bytes,width:im.naturalWidth,height:im.naturalHeight};}
  return {editing,assets:decoded};
 }
 async function restore(raw){
  const original=state,snapshot=JSON.stringify(state),{editing,assets}=await decode(raw),paths={};
  for(const [id,item] of Object.entries(assets)){
   let saved;if(window.BrowserTransport)saved=await BrowserTransport.request('upload',new Blob([item.bytes],{type:'image/jpeg'}),true);
   else{if(typeof Studio.importProjectImage!=='function')throw Error('请更新 App 后再打开作品');saved=JSON.parse(Studio.importProjectImage(item.data));}
   if(saved.error)throw Error(saved.error);if(!/^\/private\/photos\/[a-zA-Z0-9-]+\.jpg$/.test(saved.src))fail();paths[id]=saved.src;await loadPhoto(saved);
  }
  if(state!==original||JSON.stringify(state)!==snapshot)throw Error('编辑内容已变化，请重新打开作品');
  references(editing,id=>paths[id]);for(const p of editing.photos){const im=images.get(p.src);p.width=im.naturalWidth||im.width;p.height=im.naturalHeight||im.height;p.facePending=false;}
  const next={...defaults,...editing},oldPending=pendingPrint,oldPeek=peek;
  // Store first: a full browser storage must not silently discard the current draft.
  localStorage.setItem(window.STUDIO_DRAFT_KEY||'liuying-draft',JSON.stringify(next));
  try{state=next;pendingPrint=null;peek=false;syncPaper();LayerEditor.select(null);render();save();closeSheet();}
  catch(e){state=original;pendingPrint=oldPending;peek=oldPeek;localStorage.setItem(window.STUDIO_DRAFT_KEY||'liuying-draft',snapshot);render();throw e;}
 }
 let saving=false;
 function loading(on){$('loading').hidden=!on;}
 async function saveFile(){if(saving)return;saving=true;loading(true);try{const raw=await encode();if(window.BrowserTransport){const url=URL.createObjectURL(new Blob([raw],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='mijia-project.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}else{if(typeof Studio.saveProject!=='function')throw Error('请更新 App 后再保存作品');const result=JSON.parse(Studio.saveProject(raw));if(!result.ok)throw Error(result.error||'无法保存作品');return;}}catch(e){toast(e.message||'作品保存失败');}saving=false;loading(false);}
 function openFile(){const input=document.createElement('input');input.type='file';input.accept='.json,application/json';input.onchange=async()=>{const file=input.files[0];if(!file)return;if(file.size>LIMIT){toast('作品文件超过 32 MB');return;}if(!confirm('打开作品将替换当前编辑内容，是否继续？'))return;loading(true);try{await restore(await file.text());toast('作品已打开，请核对当前相纸和打印预览');}catch(e){toast(e.message||'作品无法打开，当前编辑内容已保留');}finally{loading(false);}};input.click();}
 const previous=$('menuBtn').onclick;$('menuBtn').onclick=()=>{previous();$('sheetBody').insertAdjacentHTML('beforeend',`<div class="menu-row copies-row">${icon('copy')}<span>作品文件</span><div class="copies-stepper"><button id="saveProject" aria-label="导出可编辑作品">导出</button><button id="openProject" aria-label="导入可编辑作品">导入</button></div></div>`);$('saveProject').onclick=saveFile;$('openProject').onclick=openFile;};
 const event=window.nativeEvent;window.nativeEvent=async e=>{if(e.type==='projectSaved'||e.type==='projectError'){saving=false;loading(false);if(e.type==='projectError')toast(e.value?.message||'作品保存失败');else if(!e.value?.cancelled)toast('作品已保存');return;}return event(e);};
 return {encode,decode,restore};
})();
