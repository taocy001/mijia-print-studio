/* Selected foreground details extend their existing scene across the photo edge. */
window.TemplateEdges=(()=>{
 const styles=new Set(['botanical','petal','orchard','tide','ripple','kids-dino','kids-ocean','kids-picnic','kids-ducks','kids-art']);
 function paint(ctx,w,h,style,box){
  if(!styles.has(style))return;
  const u=Math.min(w,h),l=box.margin.left,t=box.margin.top,r=l+box.crop.width,b=t+box.crop.height,d=u*.038;
  ctx.save();try{
   ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.shadowBlur=0;ctx.shadowOffsetX=ctx.shadowOffsetY=0;ctx.filter='none';ctx.lineCap='round';ctx.lineJoin='round';ctx.setLineDash([]);
   // Keep titles, subjects and the original photo-frame geometry untouched.
   ctx.beginPath();
   if(style==='tide'||style==='ripple'){
    const pts=[[l-u*.024,t-u*.024],[r+u*.024,t-u*.024],[r+u*.024,b+u*.072],[r-u*.2,b+u*.072],[r-u*.2,b+u*.024],[l+u*.2,b+u*.024],[l+u*.2,b+u*.072],[l-u*.024,b+u*.072]];
    pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();
   }else ctx.rect(l-u*.024,t-u*.024,r-l+u*.048,b-t+u*.048);
   ctx.rect(l+d,t+d,r-l-d*2,b-t-d*2);ctx.clip('evenodd');
   const line=(pts,color,width=.002)=>{ctx.strokeStyle=color;ctx.lineWidth=u*width;ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.stroke();};
   const dot=(x,y,rx,ry,color,a=0)=>{ctx.fillStyle=color;ctx.beginPath();ctx.ellipse(x,y,rx,ry,a,0,Math.PI*2);ctx.fill();};
   const leaf=(x,y,len,angle,color)=>{ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(0,0);ctx.bezierCurveTo(-len*.42,-len*.32,-len*.4,-len*.8,0,-len);ctx.bezierCurveTo(len*.42,-len*.8,len*.4,-len*.32,0,0);ctx.fill();line([[0,0],[0,-len*.82]],'#eff0d080',.0009);ctx.restore();};
   const flower=(x,y,rad,color)=>{for(let j=0;j<5;j++){const a=j*Math.PI*2/5;dot(x+Math.cos(a)*rad*.6,y+Math.sin(a)*rad*.6,rad*.5,rad*.34,color,a);}dot(x,y,rad*.25,rad*.25,'#e6c586');};
   function branch(side,y,color,fern=false){
    const x=side? r+u*.013:l-u*.013,dir=side?-1:1;
    ctx.save();ctx.translate(x,y);ctx.scale(dir,1);
    line([[0,u*.058],[u*.013,0],[0,-u*.065]],color,.0018);
    for(let i=0;i<5;i++){const yy=u*(.04-i*.021),xx=u*(.008+Math.sin(i*.7)*.005);leaf(xx,yy,u*(fern?.025:.033),.95,color);if(fern)leaf(xx,yy-u*.005,u*.019,-.85,'#a2bc7c');}
    ctx.restore();
   }
   if(['botanical','kids-dino','kids-picnic'].includes(style)){
    const color=style==='botanical'?'#52745b':style==='kids-dino'?'#87a975':'#94ae78';
    branch(false,h*(style==='botanical'?.4:style==='kids-dino'?.45:.75),color,style==='kids-dino');
    branch(true,h*(style==='botanical'?.23:style==='kids-dino'?.65:.66),color,style==='kids-dino');
    if(style==='kids-picnic')for(const x of [l+u*.015,r-u*.02]){line([[x,b+u*.018],[x-u*.003,b-u*.012]],'#94ae78');flower(x-u*.003,b-u*.013,u*.008,'#f3e5b3');}
   }
   if(style==='petal'){
    for(const [x,y,dir] of [[l-u*.008,t+u*.018,1],[r+u*.008,h*.23,-1]]){
     line([[x-dir*u*.012,y+u*.035],[x+dir*u*.012,y-u*.015]],'#7e9472');
     leaf(x,y+u*.024,u*.027,dir*.8,'#7e9472');flower(x+dir*u*.012,y-u*.004,u*.017,'#ba627c');flower(x-dir*u*.009,y+u*.025,u*.012,'#e3a08b');
    }
   }
   if(style==='orchard'){
    for(const [x,y,dir] of [[l-u*.007,t+u*.04,1],[r+u*.007,h*.52,-1]]){
     line([[x-dir*u*.01,y-u*.035],[x+dir*u*.009,y+u*.026]],'#638349');leaf(x,y-u*.018,u*.03,dir*.95,'#8a9b60');leaf(x+dir*u*.005,y+u*.01,u*.027,dir*.8,'#638349');dot(x+dir*u*.011,y+u*.024,u*.014,u*.015,'#e69a31');dot(x+dir*u*.006,y+u*.019,u*.002,u*.004,'#f7cd72',.3);
    }
   }
   if(['tide','kids-ocean','kids-ducks'].includes(style)){
    const colors=style==='tide'?['#b1d0c8','#b1d0c8']:style==='kids-ocean'?['#b3dbd4','#94cbc8']:['#bed8d8','#aacbd1'];
    // Two short wave crests join the scene below, leaving the middle edge visible.
    for(const side of [0,1]){ctx.save();ctx.translate(side?r:l,b);if(side)ctx.scale(-1,1);if(style==='tide')ctx.scale(side?.64:1,side?.62:1);
     for(let j=0;j<2;j++){ctx.fillStyle=colors[j];ctx.beginPath();ctx.moveTo(-u*.02,u*.019);ctx.bezierCurveTo(u*.014,-u*(.022-j*.009),u*.052,-u*(.032-j*.011),u*.086,-u*.004);ctx.bezierCurveTo(u*.12,u*.018,u*.15,-u*.01,u*.18,u*.017);if(style==='tide'){const depth=u*(side?.108:.068);ctx.bezierCurveTo(u*.12,u*.022,u*.025,u*.018,u*.025,depth);ctx.lineTo(-u*.02,depth);}else ctx.lineTo(u*.18,u*.024);ctx.closePath();ctx.fill();}
     line([[u*.009,-u*.01],[u*.026,-u*.015],[u*.045,-u*.013]],'#f6f5e2',.0015);ctx.restore();}
    if(style==='kids-ocean'){branch(false,h*.64,'#7fb09a');branch(true,h*.72,'#7fb09a');for(const [x,y] of [[l+u*.009,h*.32],[r-u*.009,h*.18]]){ctx.strokeStyle='#7abac0';ctx.lineWidth=u*.0015;ctx.beginPath();ctx.arc(x,y,u*.007,0,Math.PI*2);ctx.stroke();}}
    if(style==='kids-ducks')for(const [x,y] of [[l+u*.009,h*.25],[r-u*.009,h*.4],[r-u*.012,h*.55]])line([[x+u*.003,y],[x-u*.003,y+u*.013]],'#8fb6c5',.002);
   }
   if(style==='ripple')for(const [x,y,dir] of [[l+u*.026,b-u*.003,1],[r-u*.035,b+u*.002,-1]]){
    ctx.fillStyle='#b6d2c3';ctx.beginPath();ctx.moveTo(x-u*.055,b+u*.05);ctx.bezierCurveTo(x-u*.06,b-u*.006,x+u*.04,b-u*.023,x+u*.065,b+u*.05);ctx.closePath();ctx.fill();
    ctx.strokeStyle='#87a9a2';ctx.lineWidth=u*.0012;ctx.beginPath();ctx.ellipse(x,y+u*.006,u*.034,u*.012,0,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#74967d';ctx.beginPath();ctx.moveTo(x,y);ctx.ellipse(x,y,u*.025,u*.018,0,dir>0?.23:Math.PI+.23,dir>0?Math.PI*2-.23:Math.PI*3-.23);ctx.closePath();ctx.fill();
   }
   if(style==='kids-art'){
    for(const [x,y,dir,c] of [[l,h*.17,1,'#dda89a'],[r,h*.59,-1,'#aac4b0'],[l+u*.11,b,1,'#b7abd0']]){
     line([[x-dir*u*.018,y+u*.012],[x+dir*u*.008,y-u*.007],[x+dir*u*.027,y-u*.002]],c,.009);dot(x+dir*u*.03,y+u*.013,u*.003,u*.004,c);dot(x-dir*u*.012,y-u*.017,u*.004,u*.003,c);
    }
   }
  }finally{ctx.restore();}
 }
 return {paint,styles,has:style=>styles.has(style)};
})();
