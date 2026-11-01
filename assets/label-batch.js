/* Local-only label lists; no network upload or inference. */
window.LabelBatch=(()=>{
 const enabled=()=>state.mode==='label'&&state.labelBatchEnabled===true;
 const items=()=>Array.isArray(state.labelBatchItems)?state.labelBatchItems:[];
 const pages=()=>Math.ceil(items().length/NameLabels.count());
 function parse(text,csv=false){
  text=String(text).replace(/^\uFEFF/,'').replace(/\r\n?/g,'\n');if(text.length>65536)throw Error('名单文件过大');
  const lines=text.split('\n').filter(line=>line.trim());if(lines.length>36)throw Error('最多导入 36 个姓名');
  const result=lines.map(line=>{
   let fields;
   if(!csv)fields=line.split('\t');
   else{fields=[];let value='',quoted=false,closed=false;
    for(let i=0;i<line.length;i++){const c=line[i];if(quoted){if(c==='"'){if(line[i+1]==='"'){value+='"';i++;}else{quoted=false;closed=true;}}else value+=c;}
     else if(c===','){fields.push(value);value='';closed=false;}
     else if(c==='"'&&!value&&!closed)quoted=true;
     else{if(closed||c==='"')throw Error('CSV 引号格式无效');value+=c;}}
    if(quoted)throw Error('CSV 不支持跨行字段');fields.push(value);
   }
   if(fields.length>2)throw Error('每行只接受姓名和第二行小字两列');
   const title=fields[0].trim(),subtitle=(fields[1]||'').trim();
   if(!title||[...title].length>30||[...subtitle].length>50)throw Error('姓名需 1–30 字，小字最多 50 字');
   return {title,subtitle};
  });
  if(!result.length)throw Error('请先输入姓名');return result;
 }
 function validate(){
  if(!enabled())return;
  if(!items().length||items().length>36||items().some(p=>!p||typeof p.title!=='string'||typeof p.subtitle!=='string'||!p.title.trim()||/[\r\n\t]/.test(p.title+p.subtitle)||[...p.title].length>30||[...p.subtitle].length>50))throw Error('请重新检查批量名单');
  if(pages()>6)throw Error('当前相纸或方向需要超过 6 张，请减少名单或调整排版');
 }
 function summary(){if(!items().length)return '请导入或输入名单';return `${items().length} 枚 · ${pages()} 张相纸 · 当前预览第 1 张`;}
 function apply(list){const old=state.labelBatchItems;state.labelBatchItems=list;try{validate();}catch(e){state.labelBatchItems=old;throw e;}save();render();}
 function open(){
  const batch=state.labelBatchEnabled===true;
  const tabs='<div class="segments"><button data-label-kind="single" class="'+(!batch?'selected':'')+'">单个姓名</button><button data-label-kind="batch" class="'+(batch?'selected':'')+'">批量名单</button></div>';
  const html=batch?`<div class="field"><label for="batchNames">每行一个姓名，可用 Tab 分隔小字</label><textarea id="batchNames" rows="6" maxlength="4096"  spellcheck="false">${esc(items().map(p=>p.title+(p.subtitle?'\t'+p.subtitle:'')).join('\n'))}</textarea></div><div class="segments"><button id="importNames">导入 TXT / CSV</button><button id="applyNames">应用名单</button></div><p class="hint" id="batchStatus" role="status">${esc(summary())}</p>`:`<div class="field"><label>姓名或主标题</label><input id="labelInput" type="text" maxlength="30" value="${esc(state.labelTitle)}" placeholder="写下名字"></div><div class="field"><label>第二行小字</label><input id="subtitleInput" type="text" maxlength="50" value="${esc(state.labelSubtitle)}"></div>`;
  openSheet('text','姓名与小字',tabs+html);
  $('sheetBody').querySelectorAll('[data-label-kind]').forEach(button=>button.onclick=()=>{state.labelBatchEnabled=button.dataset.labelKind==='batch';save();render();open();});
  if(!batch)return;
  const status=$('batchStatus');
  $('applyNames').onclick=()=>{try{apply(parse($('batchNames').value));status.textContent=summary();}catch(e){status.textContent=e.message;}};
  $('importNames').onclick=()=>{const input=document.createElement('input');input.type='file';input.accept='.txt,.csv,text/plain,text/csv';input.onchange=async()=>{
   const file=input.files[0];if(!file)return;
   try{if(file.size>65536)throw Error('名单文件不能超过 64 KB');const text=new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer()),list=parse(text,/\.csv$/i.test(file.name));
    if(!status.isConnected||state.mode!=='label'||!state.labelBatchEnabled)return;
    apply(list);open();
   }catch(e){if(status.isConnected)status.textContent=e.message||'无法读取名单，请使用 UTF-8 文件';}
  };input.click();};
 }
 return {enabled,items,pages,parse,validate,summary,open};
})();
