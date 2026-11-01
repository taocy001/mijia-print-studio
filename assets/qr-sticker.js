/* QR links are encoded locally; their targets are never fetched. */
window.QrSticker=(()=>{
 const cache=new Map();let checking=false,tooSmall=false,crossesTear=false;
 function normalize(value){
  if(typeof value!=='string'||/[\x00-\x20]/.test(value.trim()))throw Error('请输入有效的 HTTP 或 HTTPS 链接');
  let url;try{url=new URL(value.trim());}catch{throw Error('请输入完整链接');}
  if(!['http:','https:'].includes(url.protocol)||url.username||url.password)throw Error('只支持不含登录信息的 HTTP 或 HTTPS 链接');
  if(new TextEncoder().encode(url.href).length>512)throw Error('链接过长，请使用较短的分享链接');return url.href;
 }
 function code(value){const url=normalize(value);if(cache.has(url))return cache.get(url);let qr;
  try{qr=qrcodegen.QrCode.encodeSegments(qrcodegen.QrSegment.makeSegments(url),qrcodegen.QrCode.Ecc.MEDIUM,1,10);}catch{throw Error('链接过长，请使用较短的分享链接');}
  if(cache.size>=64)cache.delete(cache.keys().next().value);cache.set(url,qr);return qr;
 }
 function minimum(value){return (code(value).size+8)*4;}
 function paint(ctx,o,size){const qr=code(o.text),count=qr.size+8,scale=Math.max(1,Math.floor(size/count));if(checking&&scale<4)tooSmall=true;
  const side=count*scale,origin=-Math.floor(side/2),t=ctx.getTransform();if(checking&&scale*Math.min(Math.hypot(t.a,t.b),Math.hypot(t.c,t.d))<4)tooSmall=true;
  if(checking&&state.media===5014&&t.f+origin<912&&t.f+origin+side>912)crossesTear=true;
  ctx.save();ctx.setTransform(t.a,t.b,t.c,t.d,Math.round(t.e),Math.round(t.f));ctx.fillStyle='#fff';ctx.fillRect(origin,origin,side,side);ctx.fillStyle='#000';
  for(let y=0;y<qr.size;y++)for(let x=0;x<qr.size;x++)if(qr.getModule(x,y))ctx.fillRect(origin+(x+4)*scale,origin+(y+4)*scale,scale,scale);ctx.restore();
 }
 function edit(item){
  if(!ready()){toast('请先选择照片');return;}const scope=LayerEditor.list();
  openSheet('qr','二维码',`<div class="field"><label for="qrUrl">链接</label><input id="qrUrl" type="text" inputmode="url" maxlength="512" autocomplete="off" placeholder="https://" value="${esc(item?.text||'')}"></div><label class="layer-range">大小<input id="qrSize" type="range" min="15" max="80" value="${item?.sizePct||28}"></label><p class="hint" id="qrStatus" role="status">链接需在扫码设备上可访问；不会上传照片或视频。</p><button class="full-button" id="applyQr">${item?'应用':'添加二维码'}</button>`);
  $('applyQr').onclick=()=>{try{if(LayerEditor.list()!==scope||item&&!scope.includes(item))throw Error('当前照片已变化，请重新编辑');const text=normalize($('qrUrl').value);code(text);const values={kind:'qr',text,sizePct:+$('qrSize').value,angle:0,hidden:false};if(item)Object.assign(item,values);else LayerEditor.create({...values,fy:state.media===5014&&LayerEditor.space().h===1824?.25:.5,stroke:'',color:'#000000'});schedule();closeSheet();}catch(e){$('qrStatus').textContent=e.message;}};
 }
 const prepare=preparePrintPages;preparePrintPages=async function(){if(checking)throw Error('正在生成预览，请稍候');checking=true;tooSmall=false;crossesTear=false;try{const pages=await prepare();if(crossesTear)throw Error('二维码跨过拼接纸撕线，请移动到上半或下半区域');if(tooSmall)throw Error('二维码在当前排版中太小，请减少拼图数量或调整排版');return pages;}finally{checking=false;}};
 PATHS.qr='M3 3h6v6H3zM15 3h6v6h-6zM3 15h6v6H3zM15 15h3v3h3v3h-6zM12 3v9H3M12 15v6M15 12h6';
 schedule();return {normalize,code,minimum,paint,edit};
})();
