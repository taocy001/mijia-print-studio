/* Original edge artwork. The center remains unpainted and no photo is uploaded. */
window.BlendedTemplates=(()=>{
 const designs=[['blend-splash','跃色飞溅'],['blend-watercolor','水彩潮间'],['blend-paper','手撕纸页'],['blend-botanical','风过叶隙'],['blend-ink','墨染微光']];
 const has=style=>designs.some(d=>d[0]===style);
 const shape=(w,h)=>({width:w,height:h,crop:{width:w,height:h},margin:{left:0,top:0}});
 function decorate(ctx,w,h,style){
  const u=Math.min(w,h),paper=style==='blend-ink'?'#f1eee5':style==='blend-botanical'?'#edf0e2':style==='blend-watercolor'?'#edf4ef':'#f5f0e6';
  let seed=has(style)?designs.findIndex(d=>d[0]===style)+317:317;
  const random=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
  const circle=(x,y,r,color,alpha=1)=>{ctx.globalAlpha=alpha;ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();};
  function ring(depth,rough,alpha){
   const pts=[],steps=Math.ceil(w/(u*.018)),side=Math.ceil(h/(u*.018));
   const edge=(t,phase)=>depth+rough*(Math.sin(t*19+phase)*.28+Math.sin(t*53+phase)*.19+random()*.53);
   for(let i=0;i<=steps;i++){const t=i/steps;pts.push([u*.012+t*(w-u*.024),u*edge(t,1)]);}
   for(let i=0;i<=side;i++){const t=i/side;pts.push([w-u*edge(t,4),u*.012+t*(h-u*.024)]);}
   for(let i=steps;i>=0;i--){const t=i/steps;pts.push([u*.012+t*(w-u*.024),h-u*edge(t,2)]);}
   for(let i=side;i>=0;i--){const t=i/side;pts.push([u*edge(t,6),u*.012+t*(h-u*.024)]);}
   ctx.globalAlpha=alpha;ctx.fillStyle=paper;ctx.beginPath();ctx.rect(0,0,w,h);ctx.moveTo(...pts[0]);for(let i=1;i<pts.length;i++)ctx.lineTo(...pts[i]);ctx.closePath();ctx.fill('evenodd');
  }
  function bloom(x,y,r,color,alpha){
   const pts=[];for(let i=0;i<36;i++){const a=i*Math.PI/18,k=.78+random()*.28;pts.push([x+Math.cos(a)*r*k,y+Math.sin(a)*r*k*.76]);}
   ctx.globalAlpha=alpha;ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(...pts[0]);for(let i=0;i<pts.length;i++){const a=pts[i],b=pts[(i+1)%pts.length];ctx.quadraticCurveTo(...a,(a[0]+b[0])/2,(a[1]+b[1])/2);}ctx.closePath();ctx.fill();
  }
  function leaf(x,y,r,a,color,alpha){ctx.save();ctx.translate(x,y);ctx.rotate(a);ctx.globalAlpha=alpha;ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(0,0);ctx.bezierCurveTo(-r*.58,-r*.4,-r*.48,-r*.92,0,-r*1.4);ctx.bezierCurveTo(r*.48,-r*.92,r*.58,-r*.4,0,0);ctx.fill();ctx.strokeStyle='#e4ead4';ctx.lineWidth=u*.0008;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(0,-r*1.19);ctx.stroke();ctx.restore();}
  ctx.save();ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.shadowBlur=0;ctx.shadowOffsetX=ctx.shadowOffsetY=0;ctx.filter='none';ctx.lineCap='round';ctx.lineJoin='round';ctx.textBaseline='alphabetic';ctx.setLineDash([]);
  // This safety aperture is wider than the painted edge: ornaments never reach the subject.
  ctx.beginPath();ctx.rect(0,0,w,h);ctx.rect(u*.15,u*.15,w-u*.3,h-u*.3);ctx.clip('evenodd');
  if(style==='blend-paper'){
   ring(.047,.023,.16);ring(.037,.017,.44);ring(.027,.011,1);
   ctx.strokeStyle='#bcae96';ctx.lineWidth=u*.0007;
   for(let i=0;i<420;i++){const side=i%4,t=random(),d=u*(.025+random()*.023),x=side===0?d:side===1?w-d:t*w,y=side===2?d:side===3?h-d:t*h;ctx.globalAlpha=.12+random()*.25;ctx.beginPath();ctx.moveTo(x,y);const dx=(side<2?1:.28)*(random()-.5)*u*.015,dy=(side<2?.28:1)*(random()-.5)*u*.015;ctx.lineTo(x+dx,y+dy);ctx.stroke();}
   for(let j=0;j<2;j++){ctx.save();if(j){ctx.translate(w,h);ctx.rotate(Math.PI);}ctx.globalAlpha=.32;ctx.fillStyle='#d6c7ad';ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(u*.13,0);ctx.lineTo(u*.078,u*.017);ctx.lineTo(u*.026,u*.055);ctx.lineTo(0,u*.13);ctx.fill();ctx.globalAlpha=.88;ctx.fillStyle='#fbf7ed';ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(u*.11,0);ctx.quadraticCurveTo(u*.024,u*.018,0,u*.108);ctx.fill();ctx.restore();}
  }else if(style==='blend-botanical'){
   // Opposing branches leave the other two edges open.
   for(const flip of [false,true]){ctx.save();if(flip){ctx.translate(w,h);ctx.rotate(Math.PI);}const length=Math.min(h*.8,u*1.1);ctx.globalAlpha=.7;ctx.strokeStyle='#68886a';ctx.lineWidth=u*.0018;ctx.beginPath();ctx.moveTo(u*.012,length);ctx.bezierCurveTo(u*.08,length*.76,u*.015,length*.33,u*.075,u*.025);ctx.stroke();
    for(let i=0;i<10;i++){const y=length*(.08+i*.085),x=u*(.05+Math.sin(i*.9)*.022);leaf(x,y,u*(.044+(i%3)*.009),i%2?1.05:-.8,['#79936c','#a8b69a','#55775f'][i%3],.72+(i%3)*.1);}
    for(let i=0;i<6;i++){const x=u*(.025+i*.05),y=u*(.024+(i%2)*.012);leaf(x,y,u*.027,.95,'#b8bf99',.7);}ctx.restore();}
   for(let i=0;i<20;i++){const side=i%2,x=side?w-u*(.02+random()*.06):u*(.02+random()*.06),y=h*(.13+random()*.74);bloom(x,y,u*.009,'#e5d5a7',.6);circle(x,y,u*.0024,'#c0a864',.8);}
  }else if(style==='blend-ink'){
   // Ink pools occupy two diagonal corners, not a rectangular perimeter.
   for(const flip of [false,true]){ctx.save();if(flip){ctx.translate(w,h);ctx.rotate(Math.PI);}for(let i=0;i<38;i++){const t=i/37,x=t*w*.61+(random()-.5)*u*.045,y=u*(-.012+Math.sin(t*Math.PI)*.025+(random()-.5)*.028),r=u*(.07+random()*.05-t*.045);bloom(x,y,r,['#254c4d','#527a72','#adb29a'][i%3],.24+random()*.25);}for(let i=0;i<14;i++)bloom(u*(random()*.022-.005),h*.32*i/14,u*(.048+random()*.027-i*.0015),'#325a55',.17);ctx.restore();}
   ctx.globalAlpha=.7;ctx.strokeStyle='#b79b57';ctx.lineWidth=u*.0013;ctx.beginPath();ctx.moveTo(w*.35,u*.018);ctx.bezierCurveTo(w*.55,u*.055,w*.76,-u*.025,w*.94,u*.05);ctx.stroke();
   for(let i=0;i<75;i++){const flip=i%2,x=random()*w*.6,y=u*(.015+random()*.065);circle(flip?w-x:x,flip?h-y:y,u*(.0006+random()*.002),'#b6a05e',.3+random()*.45);}
  }else{
   // Localized pigment masses preserve open photo edges between them.
   const hues=style==='blend-splash'?['#e05d67','#edb638','#268e9b','#7862a8']:['#73a8a8','#adc8bd','#6d92a7','#cfbb92'];
   const anchors=style==='blend-splash'?[[u*.025,u*.045,0],[w*.22,u*.014,1],[w-u*.025,h-u*.055,2],[w*.78,h-u*.012,3]]:[[u*.05,h-u*.035,0],[w*.24,h-u*.012,1],[w-u*.035,u*.035,2],[w*.81,u*.012,1]];
   for(const [x,y,k] of anchors){
    const r=u*(style==='blend-splash'?.145:.16);for(let i=0;i<7;i++)bloom(x+(random()-.5)*r*.7,y+(random()-.5)*r*.5,r*(.55+random()*.55),hues[k],.19+random()*.17);
    for(let i=0;i<(style==='blend-splash'?42:22);i++){const a=random()*Math.PI*2,d=r*(.5+random()*.8),xx=x+Math.cos(a)*d,yy=y+Math.sin(a)*d;circle(xx,yy,u*(.0012+Math.pow(random(),3)*.009),hues[k],.25+random()*.45);}
   }
   if(style==='blend-watercolor'){
    for(let j=0;j<4;j++){ctx.globalAlpha=.18+j*.08;ctx.fillStyle=['#519a9e','#8abcb5','#c8d9c6','#eee5c8'][j];ctx.beginPath();ctx.moveTo(0,h);for(let x=0;x<=w+u*.015;x+=u*.015){const t=x/w,y=h-u*((.105-j*.022)*(1-t*.62)+Math.sin(t*12+j*.7)*.012+Math.sin(t*31)*.004);ctx.lineTo(x,y);}ctx.lineTo(w,h);ctx.closePath();ctx.fill();}

    for(let j=0;j<7;j++){ctx.globalAlpha=.12+j*.025;ctx.strokeStyle=['#6f9da0','#b8cebf','#f1ebdb'][j%3];ctx.lineWidth=u*(.001+j%3*.0008);ctx.beginPath();for(let x=0;x<=w;x+=u*.012){const y=h-u*(.022+j*.009)+Math.sin(x/u*17+j)*u*.008;x?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.stroke();}
    for(let i=0;i<85;i++){const x=random()*w,y=h-u*(.015+random()*.065);circle(x,y,u*(.0005+random()*.0013),'#f8f4df',.3+random()*.45);}
   }else{
    for(const [x,y,k] of anchors){ctx.globalAlpha=.64;ctx.strokeStyle=hues[k];ctx.lineWidth=u*.005;ctx.beginPath();ctx.moveTo(x-u*.065,y-u*.012);ctx.bezierCurveTo(x+u*.016,y+u*.037,x-u*.015,y-u*.05,x+u*.095,y+u*.015);ctx.stroke();for(let i=0;i<9;i++){const a=random()*Math.PI*2,d=u*(.08+random()*.045);ctx.lineWidth=u*(.001+random()*.003);ctx.beginPath();ctx.moveTo(x+Math.cos(a)*d,y+Math.sin(a)*d*.6);ctx.lineTo(x+Math.cos(a)*(d+u*.028),y+Math.sin(a)*(d+u*.028)*.6);ctx.stroke();}}
   }
  }
  ctx.restore();
 }
 function paint(ctx,p,x,y,w,h,e){
  ctx.save();try{ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();drawPhoto(ctx,p,x,y,w,h,'cover');ctx.translate(x,y);decorate(ctx,w,h,e.style);}finally{ctx.restore();}
 }
 return {designs,has,shape,paint};
})();
