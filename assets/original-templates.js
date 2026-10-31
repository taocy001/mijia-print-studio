/* Original, resolution-independent frames: most of the paper remains photographic. */
window.OriginalTemplates=(()=>{
 const colors=new Map();
 const designs=[['air','留白'],['glow','柔光'],['linen','亚麻'],['tide','潮汐'],['botanical','枝叶'],['gallery','画廊'],['film','胶片'],['sunset','暮光'],['arch','拱窗'],['postcard','旅途'],['petal','花笺'],['constellation','星轨'],['ripple','涟漪'],['ribbon','丝带'],['terrace','阶影'],['confetti','小庆祝']];
 function shape(w,h,kind){const m=kind==='glow'||kind==='sunset'?.025:kind==='film'?.055:.065;return{width:w,height:h,crop:{width:Math.round(w*(1-m*2)),height:Math.round(h*(1-m*2))},margin:{left:Math.round(w*m),top:Math.round(h*m)}};}
 const catalog=designs.map(([style,name])=>({id:'studio-'+style,style,original:true,names:{zh:name},...shape(1216,1824,style),landscape:shape(1824,1216,style)}));
 function palette(p){
  if(!p||!images.has(p.src))return [132,153,141];if(colors.has(p.src))return colors.get(p.src);
  const c=document.createElement('canvas');c.width=c.height=12;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(images.get(p.src),0,0,12,12);const d=ctx.getImageData(0,0,12,12).data;let sums=[0,0,0];for(let i=0;i<d.length;i+=4)for(let j=0;j<3;j++)sums[j]+=d[i+j];const rgb=sums.map(x=>Math.round(x/144));colors.set(p.src,rgb);return rgb;
 }
 function paint(ctx,p,x,y,w,h,e){
  const rgb=palette(p),mix=(white,a)=>`rgb(${rgb.map(v=>Math.round(v*a+white*(1-a))).join(',')})`,sx=w/e.width,sy=h/e.height;
  ctx.save();ctx.translate(x,y);const style=e.style;
  let bg=style==='film'?'#252625':style==='linen'?'#e9e3d9':style==='gallery'?'#f6f4ee':mix(250,.13);
  ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
  if(['glow','tide','sunset'].includes(style)){
   const g=ctx.createLinearGradient(0,0,w,h);g.addColorStop(0,mix(255,.08));g.addColorStop(.6,mix(240,.27));g.addColorStop(1,style==='sunset'?'#edd3bd':mix(180,.4));ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
  }
  const px=e.margin.left*sx,py=e.margin.top*sy,pw=e.crop.width*sx,ph=e.crop.height*sy;
  if(style==='glow'||style==='sunset'){ctx.shadowColor=mix(40,.45);ctx.shadowBlur=w*.025;}
  drawPhoto(ctx,p,px,py,pw,ph,'cover');ctx.shadowBlur=0;
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
  ctx.restore();
 }
 return {catalog,paint};
})();
TEMPLATE_CATALOG.unshift(...OriginalTemplates.catalog);

{
 const valid=new Set(TEMPLATE_CATALOG.map(t=>t.id));let removed=false;
 for(const p of state.photos)if(p.templateId&&!valid.has(p.templateId)){p.templateId=null;removed=true;}
 if(state.templateId&&!valid.has(state.templateId)){state.templateId=null;removed=true;}
 if(removed){if(state.mode==='template'&&!active()?.templateId)state.mode='photo';save();schedule();setTimeout(()=>toast('原模板已移除，照片和编辑内容已保留，请重新选择模板'),0);}
}
