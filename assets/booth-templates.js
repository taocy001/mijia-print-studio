/* Original scalable artwork. Photo windows remain in paper coordinates for crop/layers. */
window.BoothTemplates=(()=>{
 const series=[
  ['purikura','草莓兔兔',['心动贴纸','双倍可爱','甜心日记','闪亮四连拍'],'#ffe7f0','#912953','#fa73a6'],
  ['studio','奶油汪汪',['汪汪照相馆','一起笑一个','小狗抓拍簿','汪汪四连拍'],'#f1ede5','#282b2d','#8b7765'],
  ['y2k','星际猫咪',['数码甜心','气泡来电','像素回忆','未来四连'],'#dce6ff','#292467','#8775ef'],
  ['comic','恐龙漫画',['主角登场','双人对话','故事三幕','欢乐分镜'],'#ffe164','#242224','#e84c4a'],
  ['journal','小熊手帐',['旅行手记','两张车票','周末剪贴','回忆拼贴簿'],'#e9ddbf','#514533','#b27148'],
  ['magazine','猫咪画报',['猫咪主编','喵喵双封面','猫步特辑','喵星生活志'],'#f4f0e8','#202325','#bf322f'],
  ['together','贴贴朋友',['心意留念','我们的合影','朋友小聚','生日派对'],'#f6e2d8','#7c3641','#d87566'],
  ['season','鸭鸭派对',['新年留影','圣诞双人','毕业时刻','夏日四格'],'#fbe5cf','#94382a','#df6840'],
  ['puzzle','拼块拼图',['快乐拼块'],'#f8f1e7','#334155','#96b5ba']
 ];
 const catalog=series.flatMap(([group,category,names,bg,ink,accent])=>names.map((name,i)=>({id:`booth-${group}-${i+1}`,style:`booth-${group}-${i+1}`,names:{zh:name},category,group,slots:i+1,bg,ink,accent})));
 const refreshed=catalog.filter(t=>t.group!=='puzzle').map(t=>({...t,id:t.id.replace('booth-','booth-v2-'),style:t.style.replace('booth-','booth-v2-'),version:2,names:{zh:t.names.zh.replace('四连拍','四格').replace('四连','四格')}}));catalog.push(...refreshed);
 catalog.push(...PlayfulTemplates.catalog,...EverydayTemplates.catalog);series.push(...PlayfulTemplates.series,...EverydayTemplates.series);
 const atlas=new Image();
 const ready=new Promise((resolve,reject)=>{atlas.onload=()=>{window.schedule?.();resolve();};atlas.onerror=()=>reject(Error('卡通贴纸未能加载，请重新打开页面'));atlas.src='booth-mascots.webp';});ready.catch(()=>{});
 function sticker(ctx,index,cx,cy,height,angle=0){if(!atlas.complete||!atlas.naturalWidth)return;const sw=atlas.naturalWidth/4,sh=atlas.naturalHeight*.35,sx=index%4*sw,sy=atlas.naturalHeight*(index<4?.13:.53),width=height*sw/sh;ctx.save();ctx.translate(cx,cy);ctx.rotate(angle);ctx.drawImage(atlas,sx,sy,sw,sh,-width/2,-height/2,width,height);ctx.restore();}
 const get=id=>catalog.find(t=>t.id===id),current=()=>state.mode==='collage'?get(state.collageTemplateId):null;
 function frames(w,h,e){
  if(e.version===4)return EverydayTemplates.frames(w,h,e);
  if(e.version===3)return PlayfulTemplates.frames(w,h,e);
  if(e.version===2)return creativeFrames(w,h,e);
  if(e.group==='puzzle'){const m=Math.min(w,h)*.045;return [{x:m,y:m,w:w-2*m,h:h-2*m}];}
  const m=Math.min(w,h)*.065,g=Math.min(w,h)*.025,top=h*.13,bottom=h*.27,W=w-2*m,H=h-top-bottom,n=e.slots;
  const map=rows=>rows.map(([xx,yy,ww,hh])=>({x:m+xx*W,y:top+yy*H,w:ww*W,h:hh*H}));
  if(e.group==='magazine'&&n===2)return map([[0,0,.64,1],[.68,.18,.32,.64]]);
  if(e.group==='magazine'&&n===3)return map([[0,0,.62,1],[.66,0,.34,.48],[.66,.52,.34,.48]]);
  if(e.group==='magazine'&&n===4)return map([[0,0,1,.64],[0,.68,.31,.32],[.345,.68,.31,.32],[.69,.68,.31,.32]]);
  if(e.group==='comic'&&n===3)return map([[0,0,.58,.43],[.62,0,.38,.43],[0,.47,1,.53]]);
  if(e.group==='comic'&&n===4)return map([[0,0,.58,.38],[.62,0,.38,.57],[0,.42,.58,.58],[.62,.61,.38,.39]]);
  if(e.group==='journal'&&n===3)return map([[0,0,.65,.47],[.35,.53,.65,.47],[.69,.03,.31,.42]]);
  if(e.group==='journal'&&n===4)return map([[0,0,.46,.43],[.52,.09,.48,.43],[.02,.49,.46,.43],[.54,.57,.46,.43]]);
  if(e.group==='purikura'&&n===4)return map([[0,.04,.46,.43],[.54,0,.46,.43],[0,.55,.46,.43],[.54,.51,.46,.43]]);
  if(e.group==='y2k'&&n===3)return map([[0,0,1,.3],[.1,.35,.9,.3],[0,.7,.9,.3]]);
  if(e.group==='together'&&n===3)return map([[0,.04,.47,.44],[.53,.04,.47,.44],[.15,.54,.7,.46]]);
  if(n===1)return [{x:m,y:top,w:W,h:H}];
  if(n===2){if(w>h||['journal','together'].includes(e.group))return [{x:m,y:top,w:(W-g)/2,h:H*.86},{x:m+(W+g)/2,y:top+H*.14,w:(W-g)/2,h:H*.86}];return [{x:m,y:top,w:W,h:(H-g)/2},{x:m,y:top+(H+g)/2,w:W,h:(H-g)/2}];}
  if(n===3)return [{x:m,y:top,w:W,h:(H-g)*.56},{x:m,y:top+(H-g)*.56+g,w:(W-g)/2,h:(H-g)*.44},{x:m+(W+g)/2,y:top+(H-g)*.56+g,w:(W-g)/2,h:(H-g)*.44}];
  if(e.group==='studio'&&h>w*1.2){const fw=Math.min(W,H*.68),fh=(H-3*g)/4;return Array.from({length:4},(_,i)=>({x:(w-fw)/2,y:top+i*(fh+g),w:fw,h:fh}));}
  return Array.from({length:4},(_,i)=>({x:m+(i%2)*(W+g)/2,y:top+Math.floor(i/2)*(H+g)/2,w:(W-g)/2,h:(H-g)/2}));
 }
 function puzzle(ctx,photos,x,y,w,h,e){
  const b=frames(w,h,e)[0],u=Math.min(w,h),cols=w>h?4:3,rows=h>w?4:3,cw=b.w/cols,ch=b.h/rows,r=Math.min(cw,ch)*.17;
  ctx.save();ctx.fillStyle='#fffaf1';ctx.fillRect(x,y,w,h);drawPhoto(ctx,photos[0],x+b.x,y+b.y,b.w,b.h,'cover');
  ctx.translate(x+b.x,y+b.y);ctx.lineJoin='round';ctx.lineCap='round';
  function seam(length,count,unit,flip){
   ctx.beginPath();ctx.moveTo(0,0);
   for(let i=0;i<count;i++){const c=(i+.5)*unit,d=(i%2?1:-1)*flip;
    ctx.lineTo(c-r*.58,0);ctx.bezierCurveTo(c-r*.45,-r*.28*d,c-r,-r*.3*d,c-r,-r*.8*d);
    ctx.bezierCurveTo(c-r,-r*1.65*d,c+r,-r*1.65*d,c+r,-r*.8*d);
    ctx.bezierCurveTo(c+r,-r*.3*d,c+r*.45,-r*.28*d,c+r*.58,0);ctx.lineTo((i+1)*unit,0);
   }
   ctx.strokeStyle='#fffef7';ctx.lineWidth=u*.007;ctx.stroke();ctx.strokeStyle='#38434b99';ctx.lineWidth=u*.0018;ctx.stroke();
  }
  for(let row=1;row<rows;row++){ctx.save();ctx.translate(0,row*ch);seam(b.w,cols,cw,row%2?1:-1);ctx.restore();}
  for(let col=1;col<cols;col++){ctx.save();ctx.translate(col*cw,0);ctx.rotate(Math.PI/2);seam(b.h,rows,ch,col%2?-1:1);ctx.restore();}
  ctx.strokeStyle='#47515b';ctx.lineWidth=u*.0025;ctx.strokeRect(0,0,b.w,b.h);ctx.restore();
 }
 function paint(ctx,photos,x,y,w,h,e){
  if(e.version===4)return EverydayTemplates.paint(ctx,photos,x,y,w,h,e);
  if(e.version===3)return PlayfulTemplates.paint(ctx,photos,x,y,w,h,e);
  if(e.version===2)return paintCreative(ctx,photos,x,y,w,h,e);
  if(e.group==='puzzle')return puzzle(ctx,photos,x,y,w,h,e);
  const u=Math.min(w,h),boxes=frames(w,h,e),group=e.group;
  let bg=e.bg,ink=e.ink,accent=e.accent;
  if(group==='season'){[bg,ink,accent]=[['#fbe5cf','#94382a','#df6840'],
  ['puzzle','拼块拼图',['快乐拼块'],'#f8f1e7','#334155','#96b5ba'],['#e5eee5','#244f3d','#b9493f'],['#e6eafa','#283551','#c19a44'],['#dff4ed','#235e64','#ef9647']][e.slots-1];}
  ctx.save();ctx.translate(x,y);ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);ctx.lineCap='round';ctx.lineJoin='round';
  const rect=(xx,yy,ww,hh,c)=>{ctx.fillStyle=c;ctx.fillRect(xx,yy,ww,hh);};
  const line=(a,b,c,d,color,width)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(a,b);ctx.lineTo(c,d);ctx.stroke();};
  const circle=(xx,yy,r,c)=>{ctx.fillStyle=c;ctx.beginPath();ctx.arc(xx,yy,r,0,Math.PI*2);ctx.fill();};
  const textAt=(s,xx,yy,size,c=ink,font='sans-serif')=>{ctx.font=`700 ${size}px ${font}`;ctx.fillStyle=c;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(s,xx,yy,w*.84);};
  function star(xx,yy,r,color){ctx.fillStyle=color;ctx.beginPath();for(let i=0;i<10;i++){const a=i*Math.PI/5-Math.PI/2,rr=i%2?r*.42:r;const px=xx+Math.cos(a)*rr,py=yy+Math.sin(a)*rr;i?ctx.lineTo(px,py):ctx.moveTo(px,py);}ctx.closePath();ctx.fill();}
  function heart(xx,yy,r,color){ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(xx,yy+r);ctx.bezierCurveTo(xx-r*2,yy-r*.3,xx-r,yy-r*1.5,xx,yy-r*.5);ctx.bezierCurveTo(xx+r,yy-r*1.5,xx+r*2,yy-r*.3,xx,yy+r);ctx.fill();}
  // Artwork is clipped out of every photo window, including the staggered layouts.
  ctx.save();ctx.beginPath();ctx.rect(0,0,w,h);for(const b of boxes)ctx.rect(b.x,b.y,b.w,b.h);ctx.clip('evenodd');
  const theme=series.findIndex(v=>v[0]===group),v=e.slots-1;
  const palettes=[['#fff0f6','#f5b8d2'],['#fff8df','#f7d77f'],['#eeeaff','#c6c4f6'],['#eff7c5','#c5de75'],['#f3eadb','#d2bd96'],['#fff0e8','#efb6a4'],['#ffeef1','#edb6c4'],['#e7f8f1','#a9deca']];
  [bg,accent]=palettes[theme];ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
  // Large soft shapes and irregular sticker clusters replace the old formal borders.
  circle(w*.08,h*.09,u*.23,accent);circle(w*.96,h*.95,u*.32,accent);
  ctx.globalAlpha=.4;for(let i=0;i<10;i++)circle(w*((i*37+11)%101)/100,h*((i*53+7)%97)/100,u*(.008+(i%3)*.003),'#fff');ctx.globalAlpha=1;
  if(group==='comic'){for(let yy=0;yy<h;yy+=u*.032)for(let xx=0;xx<w;xx+=u*.032)circle(xx,yy,u*.0028,'#9bbb6380');}
  if(group==='journal'){for(let yy=u*.03;yy<h;yy+=u*.04)line(0,yy,w,yy,'#bc9d6c30',u*.001);}
  if(group==='y2k'){for(let i=0;i<9;i++){const xx=w*((i*43+13)%100)/100,yy=h*((i*29+9)%100)/100;ctx.strokeStyle='#ffffffb0';ctx.lineWidth=u*.006;ctx.beginPath();ctx.arc(xx,yy,u*.04,0,Math.PI*2);ctx.stroke();}}
  for(let i=0;i<8;i++){const xx=i%2?w*.97:w*.025,yy=h*(.15+i*.09);i%3===0?heart(xx,yy,u*.021,'#ee9aaf'):star(xx,yy,u*.019,'#e5b34f');}
  ctx.save();ctx.translate(w*.5,h*.065);ctx.rotate((v%2?1:-1)*.022);ctx.fillStyle='#fffaf3';ctx.beginPath();ctx.roundRect(-w*.32,-u*.032,w*.64,u*.064,u*.025);ctx.fill();textAt(series[theme][1],0,0,u*.04,ink);ctx.restore();
  ctx.restore();
  for(let i=0;i<boxes.length;i++){
   const b=boxes[i],rim=u*(group==='comic'?.009:.012);
   rect(b.x-rim,b.y-rim,b.w+rim*2,b.h+rim*2,group==='comic'?ink:'#fffdf8');
   if(group==='journal'){rect(b.x+b.w*.12,b.y-u*.022,b.w*.3,u*.035,'#d4b77bd9');rect(b.x+b.w*.68,b.y+b.h-u*.008,b.w*.23,u*.03,'#d4b77bd9');}
   ctx.save();ctx.beginPath();ctx.roundRect(b.x,b.y,b.w,b.h,u*.012);ctx.clip();ctx.translate(-x,-y);drawPhoto(ctx,photos[i],x+b.x,y+b.y,b.w,b.h,'cover');ctx.translate(x,y);ctx.restore();
  }
  const left=v%2===0,heroX=w*(left?.20:.80),labelX=w*(left?.63:.37),heroH=Math.min(h*.245,u*.40);
  sticker(ctx,theme,heroX,h*.865,heroH,left?-.075:.075);
  textAt(e.names.zh,labelX,h*.83,u*.037,ink);
  ctx.save();ctx.translate(labelX,h*.90);ctx.rotate(left?-.035:.035);ctx.fillStyle='#fffaf4';ctx.beginPath();ctx.roundRect(-w*.20,-u*.027,w*.40,u*.054,u*.019);ctx.fill();textAt(['把可爱装进口袋','今天也要一起笑','收藏这份小快乐','我们的快乐合照'][v],0,0,u*.022,ink);ctx.restore();
  heart(labelX-w*.13,h*.96,u*.015,'#df7894');star(labelX+w*.13,h*.958,u*.018,'#dfb047');
  ctx.restore();
 }
 function creativeFrames(w,h,e){
  const compact=typeof state!=='undefined'&&[5009,5014].includes(state.media),u=Math.min(w,h),m=u*(compact?.03:.055),g=u*(compact?.025:.035),top=h*(compact?.055:.10),W=w-m*2,H=h*(compact?.89:.81),n=e.slots,wide=w>h*1.15;
  let cells;
  if(n===1)cells=[[m,top,W,H]];
  else if(n===2)cells=wide||w===h?[[m,top,(W-g)/2,H],[m+(W+g)/2,top,(W-g)/2,H]]:[[m,top,W,(H-g)/2],[m,top+(H+g)/2,W,(H-g)/2]];
  else if(n===3)cells=wide?[[m,top,W*.57,H],[m+W*.57+g,top,W*.43-g,(H-g)/2],[m+W*.57+g,top+(H+g)/2,W*.43-g,(H-g)/2]]:[[m,top,W,(H-g)*.53],[m,top+(H-g)*.53+g,(W-g)/2,(H-g)*.47],[m+(W+g)/2,top+(H-g)*.53+g,(W-g)/2,(H-g)*.47]];
  else cells=Array.from({length:4},(_,i)=>[m+i%2*(W+g)/2,top+Math.floor(i/2)*(H+g)/2,(W-g)/2,(H-g)/2]);
  return cells.map(([x,y,cw,ch],i)=>{
   const group=e.group,heart=group==='together'&&n<=2;
   const shape=heart?'heart':group==='comic'?(i%2?'comicRight':'comicLeft'):group==='magazine'&&n===1?'arch':group==='y2k'&&n<=2?'ellipse':(group==='season'||group==='studio')&&n<=2?'wave':'round';
   const degrees=group==='journal'?[-5,6,-4,5][i]:group==='purikura'?[-3,4,-4,3][i]:n>1&&['together','season','studio'].includes(group)?[-3,3,-3,3][i]:0;
   const angle=degrees*Math.PI/180,ratio=heart?1:shape==='ellipse'?Math.min(1.25,Math.max(.8,cw/ch)):Math.min(1.6,Math.max(1/1.6,cw/ch));
   let fw=Math.min(cw,ch*ratio),fh=fw/ratio;
   // Fit the rotated corners inside their cell; adjacent photos never cover faces.
   const c=Math.abs(Math.cos(angle)),s=Math.abs(Math.sin(angle)),scale=Math.min(1,cw/(fw*c+fh*s),ch/(fw*s+fh*c))*.97;fw*=scale;fh*=scale;
   return {x:x+(cw-fw)/2,y:y+(ch-fh)/2,w:fw,h:fh,shape,angle};
  });
 }
 function available(id,w,h){
  const e=get(id);if(!e||!e.version)return !e||e.group==='puzzle';
  if(e.version===4)return EverydayTemplates.available(e,w,h);
  if(e.version===3)return PlayfulTemplates.available(e,w,h);
  return creativeFrames(w,h,e).every(f=>{
   const effective=Math.min(f.w,f.h)*(f.shape==='heart'?.78:f.shape==='ellipse'?.85:1);
   return effective>=310&&Math.max(f.w/f.h,f.h/f.w)<=1.8;
  });
 }
 function paintCreative(ctx,photos,x,y,w,h,e){
  const compact=typeof state!=='undefined'&&[5009,5014].includes(state.media),u=Math.min(w,h),boxes=creativeFrames(w,h,e),theme=series.findIndex(s=>s[0]===e.group);
  ctx.save();ctx.translate(x,y);ctx.fillStyle=e.bg;ctx.fillRect(0,0,w,h);
  const dot=(cx,cy,r,color)=>{ctx.fillStyle=color;ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.fill();};
  ctx.globalAlpha=.22;dot(w*.03,h*.04,u*.24,e.accent);dot(w*.97,h*.96,u*.23,e.accent);ctx.globalAlpha=1;
  if(e.group==='journal'){ctx.strokeStyle='#9f825422';ctx.lineWidth=u*.001;for(let yy=u*.02;yy<h;yy+=u*.032){ctx.beginPath();ctx.moveTo(0,yy);ctx.lineTo(w,yy);ctx.stroke();}}
  if(e.group==='comic'){for(let yy=u*.02;yy<h;yy+=u*.035)for(let xx=u*.02;xx<w;xx+=u*.035)dot(xx,yy,u*.002,e.accent+'66');}
  if(e.group==='y2k'){ctx.strokeStyle='#ffffffbb';ctx.lineWidth=u*.003;for(let i=0;i<6;i++){ctx.beginPath();ctx.ellipse(w*(i%2?.96:.04),h*(.15+i*.13),u*.03,u*.04,.4,0,Math.PI*2);ctx.stroke();}}
  ctx.fillStyle=e.ink;ctx.textAlign='center';ctx.textBaseline='middle';ctx.font=`700 ${u*(compact?.028:.037)}px sans-serif`;ctx.fillText(e.names.zh,w*.5,h*(compact?.027:.05),w*.72);
  ctx.restore();
  for(const b of boxes){
   const f={...b,x:x+b.x,y:y+b.y};ctx.save();PhotoWindows.transform(ctx,f);ctx.shadowColor='#00000024';ctx.shadowBlur=u*.012;ctx.shadowOffsetY=u*.004;ctx.fillStyle='#fffdf9';ctx.strokeStyle=e.group==='comic'?e.ink:'#fffdf9';ctx.lineWidth=u*(e.group==='comic'?.009:.017);ctx.lineJoin='round';const p=PhotoWindows.trace(ctx,f);ctx.fill(p);ctx.stroke(p);ctx.restore();
   drawPhoto(ctx,photos[boxes.indexOf(b)],f.x,f.y,f.w,f.h,'cover',{shape:f.shape,angle:f.angle});
   if(e.group==='journal'){
    ctx.save();PhotoWindows.transform(ctx,f);ctx.fillStyle='#d5bd86bb';ctx.translate(f.x+f.w*.23,f.y);ctx.rotate(-.08);ctx.fillRect(-f.w*.16,-u*.013,f.w*.32,u*.026);ctx.restore();
   }
  }
  ctx.save();ctx.translate(x,y);sticker(ctx,theme,w*.08,h*(compact?.972:.95),u*(compact?.045:.115),-.08);ctx.fillStyle=e.ink;ctx.globalAlpha=.72;ctx.font=`500 ${u*(compact?.016:.019)}px sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(e.category+' · 留住这一刻',w*.5,h*(compact?.975:.955),w*.68);ctx.restore();
 }

 function paintCurrent(ctx,w,h){const e=current();if(!e)return false;const capacity=e.slots*(state.media===5014?2:1),start=Math.floor(state.active/capacity)*capacity,photos=window.PhotoWorks?.enabled()?PhotoWorks.photos():window.PhotoFlow?.multiple()?PhotoFlow.pagePhotos():state.photos.slice(start,start+capacity);if(state.media===5014){paint(ctx,photos.slice(0,e.slots),0,0,w,h/2,e);paint(ctx,photos.slice(e.slots),0,h/2,w,h/2,e);}else paint(ctx,photos,0,0,w,h,e);return true;}
 function capacity(){const e=current();return e?e.slots*(state.media===5014?2:1):0;}
 function validate(){const n=capacity();if(n>6)throw Error('此模板在拼接相纸上需要超过 6 张照片，请改选双张或三张模板');if(n&&state.photos.length%n)throw Error(`此模板每页需要 ${n} 张照片，已选 ${state.photos.length} 张，请再添加 ${n-state.photos.length%n} 张，或选择照片更少的模板`);}
 return {catalog,series,ready,get,frames,paint,current,paintCurrent,capacity,validate,available,retired:id=>{const e=get(id);return !!e&&!e.version&&e.group!=='puzzle';}};
})();
TEMPLATE_CATALOG.push(...BoothTemplates.catalog);
