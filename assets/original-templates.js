/* Original, resolution-independent frames: most of the paper remains photographic. */
window.OriginalTemplates=(()=>{
 const colors=new Map();
 const designs=[['air','留白'],['glow','柔光'],['linen','亚麻'],['tide','潮汐'],['botanical','林间手记'],['gallery','画廊'],['film','电影散场'],['sunset','暮光'],['arch','拱窗'],['postcard','远方来信'],['petal','花园来信'],['constellation','星夜漫游'],['ripple','涟漪'],['ribbon','丝带'],['terrace','阶影'],['confetti','快乐收藏']];
 function shape(w,h,kind){
  const rich=['botanical','film','postcard','petal','constellation','confetti'].includes(kind),m=rich?.09:kind==='glow'||kind==='sunset'?.025:.065;
  const left=Math.round(w*m),top=Math.round(h*(rich?.075:m)),bottom=Math.round(h*(rich?.13:m));
  return {width:w,height:h,crop:{width:w-left*2,height:h-top-bottom},margin:{left,top}};
 }
 function ornament(ctx,w,h,style){
  const u=Math.min(w,h),ink={botanical:'#32534a',film:'#f0ba60',postcard:'#b44736',petal:'#a94f70',constellation:'#e5c788',confetti:'#264b91'}[style];if(!ink)return;
  const box=shape(w,h,style),px=box.margin.left,py=box.margin.top,pw=box.crop.width,ph=box.crop.height;
  ctx.save();ctx.strokeStyle=ink;ctx.fillStyle=ink;
  // Decoration stays near the paper edge; the subject remains unobstructed.
  function flower(x,y,r,color){ctx.save();ctx.translate(x,y);ctx.fillStyle=color;for(let i=0;i<7;i++){ctx.rotate(Math.PI*2/7);ctx.beginPath();ctx.ellipse(r*.6,0,r*.7,r*.36,0,0,Math.PI*2);ctx.fill();}ctx.fillStyle='#f5ce70';ctx.beginPath();ctx.arc(0,0,r*.3,0,Math.PI*2);ctx.fill();ctx.restore();}
  function leaf(x,y,angle,size,color){ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(0,0);ctx.bezierCurveTo(-size,-size*.5,-size*.3,-size*1.6,0,-size*1.8);ctx.bezierCurveTo(size*.7,-size,size*.8,-size*.3,0,0);ctx.fill();ctx.restore();}
  if(style==='botanical'||style==='petal')for(const flip of [false,true]){
   ctx.save();if(flip){ctx.translate(w,h);ctx.rotate(Math.PI);}ctx.lineWidth=u*.002;ctx.beginPath();ctx.moveTo(w*.02,h*.25);ctx.bezierCurveTo(w*.06,h*.17,w*.02,h*.04,w*.23,h*.03);ctx.stroke();
   for(let i=0;i<7;i++){const x=w*(.025+i*.024),y=h*(.13-i*.014);leaf(x,y,i%2?.8:-.7,u*(.024+i%3*.005),style==='botanical'?(i%2?'#668878':'#96a786'):'#8da38a');}
   if(style==='petal'){flower(w*.055,h*.055,u*.063,'#d4869a');flower(w*.13,h*.025,u*.038,'#f0b8a4');flower(w*.025,h*.13,u*.042,'#b75d7a');}
   ctx.restore();
  }
  if(style==='postcard'){
   ctx.save();ctx.strokeStyle='#4c7785';ctx.lineWidth=u*.009;ctx.setLineDash([u*.02,u*.025]);ctx.strokeRect(w*.021,h*.017,w*.958,h*.966);ctx.restore();
   ctx.save();ctx.translate(w*.83,h*.9);ctx.rotate(-.14);ctx.fillStyle='#e6d9b8';ctx.fillRect(-u*.055,-u*.045,u*.11,u*.09);ctx.strokeStyle=ink;ctx.lineWidth=u*.002;ctx.strokeRect(-u*.048,-u*.038,u*.096,u*.076);ctx.beginPath();ctx.arc(0,0,u*.027,0,Math.PI*2);ctx.stroke();ctx.font=`${u*.016}px sans-serif`;ctx.textAlign='center';ctx.fillStyle=ink;ctx.fillText('POST',0,u*.005);ctx.restore();
   ctx.strokeStyle='#6a756c';ctx.lineWidth=u*.0015;for(let i=0;i<3;i++){ctx.beginPath();ctx.moveTo(w*.57,h*(.91+i*.012));ctx.bezierCurveTo(w*.65,h*(.895+i*.012),w*.73,h*(.93+i*.012),w*.81,h*(.91+i*.012));ctx.stroke();}
   ctx.fillStyle='#cfb77e99';ctx.save();ctx.translate(px+pw*.1,py);ctx.rotate(-.13);ctx.fillRect(-u*.06,-u*.016,u*.12,u*.032);ctx.restore();
  }
  if(style==='constellation'){
   let seed=13;const random=()=>((seed=(seed*1664525+1013904223)>>>0)/4294967296);
   for(let i=0;i<100;i++){const x=random()*w,y=random()*h;if(x>px-u*.01&&x<px+pw+u*.01&&y>py-u*.01&&y<py+ph+u*.01)continue;ctx.globalAlpha=.25+random()*.65;ctx.beginPath();ctx.arc(x,y,u*(.0008+random()*.0018),0,Math.PI*2);ctx.fill();}ctx.globalAlpha=1;
   ctx.save();ctx.translate(w*.9,h*.065);ctx.fillStyle='#eed9a3';ctx.beginPath();ctx.arc(0,0,u*.038,0,Math.PI*2);ctx.fill();ctx.fillStyle='#1c304a';ctx.beginPath();ctx.arc(u*.017,-u*.012,u*.033,0,Math.PI*2);ctx.fill();ctx.restore();
   ctx.strokeStyle='#ddc890';ctx.lineWidth=u*.0015;ctx.strokeRect(px-u*.012,py-u*.009,pw+u*.024,ph+u*.018);
  }
  if(style==='confetti'){
   for(let i=0;i<26;i++){ctx.save();const x=w*(.03+(i%13)*.077),y=i<13?h*.035:h*.965;ctx.translate(x,y);ctx.rotate(i*.83);ctx.fillStyle=['#df7059','#edbc52','#658cad','#778e66','#b2768d'][i%5];if(i%3){ctx.fillRect(-u*.007,-u*.017,u*.014,u*.034);}else{ctx.beginPath();ctx.arc(0,0,u*.01,0,Math.PI*2);ctx.fill();}ctx.restore();}
   for(const [x,y] of [[w*.07,h*.07],[w*.93,h*.86]]){ctx.save();ctx.translate(x,y);ctx.rotate(.3);ctx.fillStyle='#e9ba4b';ctx.fillRect(-u*.04,-u*.015,u*.08,u*.03);ctx.restore();}
  }
  const title={botanical:'FIELD NOTES',film:'A MOMENT IN MOTION',postcard:'SOMEWHERE, WITH YOU',petal:'LET THE DAYS BLOOM',constellation:'UNDER THE SAME SKY',confetti:'LITTLE THINGS, BIG JOY'}[style];
  ctx.fillStyle=ink;ctx.textAlign='left';ctx.font=`600 ${u*.025}px sans-serif`;ctx.fillText(title,px,h*.925);
  if(style==='film'){ctx.font=`${u*.012}px monospace`;ctx.fillText('01  /  COLOR STUDY',px,h*.957);ctx.strokeStyle='#c29448';ctx.lineWidth=u*.001;ctx.beginPath();ctx.moveTo(px,h*.89);ctx.lineTo(px+pw,h*.89);ctx.stroke();}
  else{ctx.globalAlpha=.55;ctx.font=`italic ${u*.013}px Georgia,serif`;ctx.fillText('Collected moments',px,h*.951);}
  ctx.restore();
 }

 const catalog=designs.map(([style,name])=>({id:'studio-'+style,style,original:true,names:{zh:name},...shape(1216,1824,style),landscape:shape(1824,1216,style)}));
 function palette(p){
  if(!p||!images.has(p.src))return [132,153,141];if(colors.has(p.src))return colors.get(p.src);
  const c=document.createElement('canvas');c.width=c.height=12;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(images.get(p.src),0,0,12,12);const d=ctx.getImageData(0,0,12,12).data;let sums=[0,0,0];for(let i=0;i<d.length;i+=4)for(let j=0;j<3;j++)sums[j]+=d[i+j];const rgb=sums.map(x=>Math.round(x/144));colors.set(p.src,rgb);return rgb;
 }
 function paint(ctx,p,x,y,w,h,e){
  const rgb=palette(p),mix=(white,a)=>`rgb(${rgb.map(v=>Math.round(v*a+white*(1-a))).join(',')})`,sx=w/e.width,sy=h/e.height;
  ctx.save();ctx.translate(x,y);const style=e.style;
  let bg=style==='film'?'#252625':style==='linen'?'#e9e3d9':style==='gallery'?'#f6f4ee':mix(250,.13);
  bg=({botanical:'#e3e9da',petal:'#fae9e2',postcard:'#eee4cf',constellation:'#1c304a',confetti:'#f6edcf',film:'#22282d'})[style]||bg;ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
  if(['glow','tide','sunset'].includes(style)){
   const g=ctx.createLinearGradient(0,0,w,h);g.addColorStop(0,mix(255,.08));g.addColorStop(.6,mix(240,.27));g.addColorStop(1,style==='sunset'?'#edd3bd':mix(180,.4));ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
  }
  ctx.save();
  if(style==='petal'){const tile=Math.min(w,h)*.035;ctx.fillStyle='#bb6c7b12';for(let row=0;row<h/tile;row++)for(let col=0;col<w/tile;col++)if((row+col)%2===0)ctx.fillRect(col*tile,row*tile,tile,tile);}
  if(style==='confetti'){const tile=Math.min(w,h)*.035;for(let row=0;row<h/tile;row++){ctx.fillStyle=row%2?'#edbc52':'#e58e6c';ctx.fillRect(0,row*tile,w*.027,tile);ctx.fillStyle=row%2?'#658cad':'#8ca281';ctx.fillRect(w*.973,row*tile,w*.027,tile);}}
  if(style==='postcard'||style==='botanical'){ctx.strokeStyle=style==='postcard'?'#806c4b15':'#52735b10';ctx.lineWidth=Math.max(1,w*.0007);for(let row=0;row<h;row+=Math.min(w,h)*.016){ctx.beginPath();ctx.moveTo(0,row);ctx.lineTo(w,row);ctx.stroke();}}
  ctx.restore();
  const px=e.margin.left*sx,py=e.margin.top*sy,pw=e.crop.width*sx,ph=e.crop.height*sy;
  if(style==='glow'||style==='sunset'){ctx.shadowColor=mix(40,.45);ctx.shadowBlur=w*.025;}
  ctx.translate(-x,-y);drawPhoto(ctx,p,x+px,y+py,pw,ph,'cover');ctx.translate(x,y);ctx.shadowBlur=0;
  if(style==='gallery'||style==='air'){ctx.strokeStyle=mix(200,.3);ctx.lineWidth=Math.max(1,w*.001);ctx.strokeRect(px-w*.009,py-h*.006,pw+w*.018,ph+h*.012);}
  if(style==='linen'){ctx.strokeStyle='#8d7f6920';ctx.lineWidth=1;for(let i=0;i<w;i+=7){ctx.beginPath();ctx.moveTo(i,0);ctx.lineTo(i,py*.72);ctx.moveTo(i,py+ph+h*.012);ctx.lineTo(i,h);ctx.stroke();}}
  if(style==='film'){ctx.fillStyle='#e9e4d9';const step=h/16;for(let i=0;i<16;i++){ctx.beginPath();ctx.roundRect(w*.017,i*step+step*.25,w*.018,step*.42,w*.003);ctx.roundRect(w*.965,i*step+step*.25,w*.018,step*.42,w*.003);ctx.fill();}}
  if(style==='tide'){ctx.strokeStyle=mix(120,.6);ctx.globalAlpha=.4;ctx.lineWidth=w*.0015;for(let i=0;i<3;i++){ctx.beginPath();ctx.moveTo(0,h*(.975+i*.009));ctx.bezierCurveTo(w*.3,h*(.96+i*.01),w*.65,h*(.99+i*.005),w,h*(.97+i*.009));ctx.stroke();}}
  if(style==='botanical'){
   for(const flip of [false,true]){ctx.save();if(flip){ctx.translate(w,h);ctx.rotate(Math.PI);}ctx.translate(w*.026,h*.055);ctx.strokeStyle=mix(70,.6);ctx.fillStyle=mix(110,.5);ctx.lineWidth=w*.002;ctx.beginPath();ctx.moveTo(0,0);ctx.quadraticCurveTo(w*.025,h*.08,w*.015,h*.18);ctx.stroke();for(let i=0;i<5;i++){ctx.save();ctx.translate(w*.014,h*(.02+i*.03));ctx.rotate(i%2?-.65:.6);ctx.globalAlpha=.65;ctx.beginPath();ctx.ellipse(i%2?w*.012:-w*.009,0,w*.014,h*.007,0,0,Math.PI*2);ctx.fill();ctx.restore();}ctx.restore();}
  }
  if(style==='arch'||style==='ripple'){
   ctx.strokeStyle=mix(110,.45);ctx.lineWidth=w*.0015;
   for(let i=0;i<3;i++){ctx.beginPath();ctx.ellipse(w*.5,h*.5,pw*.5+w*(.012+i*.009),ph*.5+h*(.01+i*.008),0,0,Math.PI*2);ctx.save();ctx.beginPath();ctx.rect(0,0,w,h);ctx.rect(px,py,pw,ph);ctx.clip('evenodd');ctx.beginPath();if(style==='arch'){const dx=w*(.012+i*.009),dy=h*(.01+i*.008);ctx.roundRect(px-dx,py-dy,pw+dx*2,ph+dy*2,w*.025);}else ctx.ellipse(w*.5,h*.5,pw*.5+w*(.012+i*.009),ph*.5+h*(.01+i*.008),0,0,Math.PI*2);ctx.stroke();ctx.restore();}
  }
  if(style==='postcard'){ctx.strokeStyle=mix(110,.5);ctx.lineWidth=w*.002;ctx.setLineDash([w*.012,w*.008]);ctx.strokeRect(w*.025,h*.018,w*.95,h*.964);ctx.setLineDash([]);}
  if(style==='petal'){StudioArtwork.flower(ctx,w*.043,h*.04,Math.min(w,h)*.023);StudioArtwork.flower(ctx,w*.957,h*.96,Math.min(w,h)*.023);}
  if(style==='constellation'){ctx.strokeStyle=mix(130,.45);ctx.lineWidth=w*.001;for(const y of [h*.03,h*.97]){ctx.beginPath();ctx.moveTo(w*.17,y);ctx.lineTo(w*.36,y-h*.008);ctx.lineTo(w*.61,y+h*.006);ctx.lineTo(w*.82,y);ctx.stroke();for(const x of [.17,.36,.61,.82])StudioArtwork.star(ctx,w*x,y,w*.005,mix(100,.7));}}
  if(style==='ribbon'){ctx.fillStyle=mix(150,.45);ctx.fillRect(px,py-h*.019,pw*.22,h*.004);ctx.fillRect(px+pw*.78,py+ph+h*.015,pw*.22,h*.004);}
  if(style==='terrace'){ctx.strokeStyle=mix(100,.55);ctx.lineWidth=w*.002;for(let i=0;i<3;i++){const dx=w*(.012+i*.008),dy=h*(.008+i*.005);ctx.beginPath();ctx.moveTo(px-dx,py+ph*.12);ctx.lineTo(px-dx,py-dy);ctx.lineTo(px+pw*.18,py-dy);ctx.moveTo(px+pw+dx,py+ph*.88);ctx.lineTo(px+pw+dx,py+ph+dy);ctx.lineTo(px+pw*.82,py+ph+dy);ctx.stroke();}}
  if(style==='confetti'){for(let i=0;i<20;i++){ctx.save();ctx.translate(w*(.08+i*.044),h*(i%2?.978:.022));ctx.rotate(i*1.7);ctx.fillStyle=['#c99582','#94afa0','#d9bc79','#9eabc3'][i%4];ctx.fillRect(-w*.003,-w*.007,w*.006,w*.014);ctx.restore();}}
  ornament(ctx,w,h,style);ctx.restore();
 }
 function variant(base,w,h){return {...base,...shape(w,h,base.style)};}
 return {catalog,paint,variant};
})();
TEMPLATE_CATALOG.unshift(...OriginalTemplates.catalog);

{
 const valid=new Set(TEMPLATE_CATALOG.map(t=>t.id));let removed=false;
 for(const p of state.photos)if(p.templateId&&!valid.has(p.templateId)){p.templateId=null;removed=true;}
 if(state.templateId&&!valid.has(state.templateId)){state.templateId=null;removed=true;}
 if(removed){if(state.mode==='template'&&!active()?.templateId)state.mode='photo';save();schedule();setTimeout(()=>toast('原模板已移除，照片和编辑内容已保留，请重新选择模板'),0);}
}
