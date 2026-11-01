/* Original canvas illustrations, with an unobstructed photographic window. */
window.OriginalTemplates=(()=>{
 const colors=new Map();
 const designs=[['air','风的来信'],['glow','灯火可亲'],['linen','针脚日常'],['tide','海风经过'],['botanical','山野采集'],['gallery','生活展览室'],['film','散场以后'],['sunset','落日公路'],['arch','晴日小院'],['postcard','远方来信'],['petal','花开有时'],['constellation','一起看星星'],['ripple','一池春水'],['ribbon','把此刻打包'],['terrace','街角漫游'],['confetti','快乐收藏夹'],['orchard','橘子晴天'],['alpine','去山里吧'],['cafe','下午三点'],['festival','今夜有庆典'],...KidsTemplates.designs];
 function shape(w,h,kind){
  const u=Math.min(w,h),left=Math.round(u*(kind==='film'?.07:.065)),top=Math.round(u*.06),bottom=Math.round(u*.215);
  return {width:w,height:h,crop:{width:w-left*2,height:h-top-bottom},margin:{left,top}};
 }
 function ornament(ctx,w,h,style,box,accent){
  const u=Math.min(w,h),px=box.margin.left,py=box.margin.top,pw=box.crop.width,ph=box.crop.height,foot=py+ph;
  const themes={air:['#edf2ec','#385c60','#cc724c','风的来信','LET THE DAY WANDER'],glow:['#273747','#f7d59d','#df966a','灯火可亲','A LITTLE LIGHT'],linen:['#eee1cd','#685348','#a85840','针脚里的日常','SLOW DAYS'],tide:['#dce9e5','#265c73','#d17d54','海风经过','BY THE SEA'],botanical:['#e2e8d5','#365547','#809561','山野采集','FIELD NOTES'],gallery:['#f2e7d8','#2c4041','#bb533d','生活展览室','THE EVERYDAY EDITION'],film:['#242b30','#e8ce9d','#d49a52','散场以后','KEEP THIS SCENE'],sunset:['#f0cbb5','#8e493c','#cc714b','落日公路','TAKE THE LONG WAY'],arch:['#e6d6c1','#315c7a','#c58c52','晴日小院','SOMEWHERE IN THE SUN'],postcard:['#eee4cf','#5a6658','#b94c3d','从远方寄来','WISH YOU WERE HERE'],petal:['#f3dfdc','#794458','#b85573','花开有时','THE FLOWER MARKET'],constellation:['#172c46','#eed6a0','#758fa4','一起看星星','UNDER THE SAME SKY'],ripple:['#e1e9df','#38676a','#c86b47','一池春水','SLOW RIPPLE'],ribbon:['#eadadf','#754455','#c27b89','把此刻打包','A GIFT OF TODAY'],terrace:['#e4d8c6','#4c5c5b','#bc6c47','街角漫游','AROUND THE CORNER'],confetti:['#f5e5b7','#325779','#d65f4d','快乐收藏夹','SMALL JOYS CLUB'],orchard:['#f4e7c7','#4e6940','#e29836','橘子晴天','FRESHLY PICKED'],alpine:['#dde8e5','#365d66','#c18160','去山里吧','OUT OF OFFICE'],cafe:['#e9ddca','#684b3c','#aa7250','下午三点','COFFEE & COMPANY'],festival:['#30304b','#efd4a1','#c57e89','今夜有庆典','MAKE A LITTLE MAGIC']};
  const [bg,ink,pop,title,subtitle]=themes[style];
  const circle=(x,y,r,color)=>{ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();};
  const line=(points,color=ink,width=u*.002)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.stroke();};
  const polygon=(points,color)=>{ctx.fillStyle=color;ctx.beginPath();points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();ctx.fill();};
  const rect=(x,y,w,h,color,r=0)=>{ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill();};
  const star=(x,y,r,color,n=5)=>{const pts=[];for(let i=0;i<n*2;i++){const a=-Math.PI/2+i*Math.PI/n,k=i%2?.4:1;pts.push([x+Math.cos(a)*r*k,y+Math.sin(a)*r*k]);}polygon(pts,color);};
  const leaf=(x,y,r,angle,color)=>{ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.fillStyle=color;ctx.beginPath();ctx.ellipse(0,-r*.6,r*.36,r*.8,0,0,Math.PI*2);ctx.fill();ctx.restore();};
  const flower=(x,y,r,color,n=6)=>{for(let i=0;i<n;i++){const a=i*Math.PI*2/n;ctx.save();ctx.translate(x,y);ctx.rotate(a);ctx.fillStyle=color;ctx.beginPath();ctx.ellipse(0,-r*.52,r*.35,r*.58,0,0,Math.PI*2);ctx.fill();ctx.restore();}circle(x,y,r*.24,'#e9b94e');};
  const arch=(x,y,r,height,color)=>{ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(x-r,y+height);ctx.lineTo(x-r,y);ctx.arc(x,y,r,Math.PI,0);ctx.lineTo(x+r,y+height);ctx.closePath();ctx.fill();};
  ctx.save();ctx.textBaseline='alphabetic';ctx.lineCap='round';ctx.lineJoin='round';
  // Each theme has its own illustration; all drawing is clipped outside the photo.
  const fy=foot+u*.105,artX=w-u*.25;
  const panoramic=new Set(['tide','petal','sunset','alpine','ripple','festival','cafe','ribbon','gallery','arch','constellation','confetti','terrace']);
  const wave=(y,amplitude,period,color)=>{ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(0,h);for(let x=0;x<=w+u*.02;x+=u*.008)ctx.lineTo(x,y+Math.sin(x/u*period)*amplitude);ctx.lineTo(w,h);ctx.closePath();ctx.fill();};
  if(style==='tide'){
   wave(foot+u*.043,u*.018,12,'#b1d0c8');wave(foot+u*.09,u*.014,16,'#72a5ae');wave(foot+u*.145,u*.014,20,'#36758a');
   const x=u*.14;polygon([[x-u*.035,foot+u*.12],[x-u*.022,foot-u*.002],[x+u*.022,foot-u*.002],[x+u*.035,foot+u*.12]],'#faf0d6');rect(x-u*.026,foot+u*.038,u*.052,u*.022,'#c36d50');rect(x-u*.026,foot-u*.005,u*.052,u*.025,ink);polygon([[x-u*.04,foot-u*.005],[x,foot-u*.028],[x+u*.04,foot-u*.005]],pop);circle(x,foot+u*.008,u*.007,'#f3cd74');
   for(let j=0;j<3;j++){ctx.strokeStyle='#f8f0d999';ctx.lineWidth=u*.002;ctx.beginPath();ctx.moveTo(u*.25,foot+u*(.06+j*.04));ctx.bezierCurveTo(w*.45,foot+u*(.025+j*.04),w*.6,foot+u*(.1+j*.04),w-u*.04,foot+u*(.055+j*.04));ctx.stroke();}
  }
  if(style==='petal'){
   for(let i=0;i<12;i++){const x=w*(.025+i*.088),y=foot+u*(.065+(i%3)*.035);line([[x,h],[x,y]],'#6e8b68',u*.003);leaf(x,y+u*.045,u*.03,i%2?.8:-.7,'#94a87f');flower(x,y,u*(.035+(i%3)*.007),['#ba577a','#d58786','#efbc91'][i%3]);}
   for(let j=0;j<4;j++)for(const x of [u*.02,w-u*.018]){const y=h*(.16+j*.2);leaf(x,y,u*.05,x<w/2?-.3:.3,'#79956c');flower(x,y+u*.04,u*.038,j%2?'#c87791':'#e9b09b');}
  }
  if(style==='sunset'){
   circle(w*.64,foot+u*.018,u*.075,'#f2b85b');
   for(let i=0;i<3;i++){ctx.fillStyle=['#d89b71','#b56c50','#88514b'][i];ctx.beginPath();ctx.moveTo(0,h);ctx.lineTo(0,foot+u*(.06+i*.037));ctx.bezierCurveTo(w*.3,foot+u*(.18-i*.02),w*.53,foot-u*.055+i*u*.07,w,foot+u*(.09+i*.035));ctx.lineTo(w,h);ctx.fill();}
   polygon([[w*.25,h],[w*.34,h],[w*.43,foot+u*.095],[w*.4,foot+u*.095]],'#e6c3a1');line([[w*.294,h],[w*.417,foot+u*.11]],'#f5e3bc',u*.002);
   for(const [x,y] of [[u*.035,h*.31],[w-u*.028,h*.6]]){line([[x,y+u*.08],[x,y-u*.03]],'#815d4b',u*.009);line([[x,y+u*.025],[x-u*.018,y+u*.025],[x-u*.018,y]],'#815d4b',u*.007);}
  }
  if(style==='alpine'){
   polygon([[0,h],[0,foot+u*.1],[w*.16,foot-u*.025],[w*.31,foot+u*.1],[w*.48,foot-u*.015],[w*.64,foot+u*.12],[w*.81,foot+u*.015],[w,foot+u*.11],[w,h]],'#84a49c');
   polygon([[0,h],[0,foot+u*.15],[w*.29,foot+u*.028],[w*.5,foot+u*.17],[w*.73,foot+u*.035],[w,foot+u*.16],[w,h]],'#4d7779');
   for(const [x,y] of [[w*.16,foot-u*.025],[w*.48,foot-u*.015],[w*.73,foot+u*.035]])polygon([[x-u*.045,y+u*.045],[x,y],[x+u*.045,y+u*.045],[x+u*.012,y+u*.03],[x-u*.007,y+u*.043],[x-u*.023,y+u*.027]],'#f2f0de');
   for(let i=0;i<12;i++){const x=w*(i/11),y=foot+u*(.145+(i%3)*.014);polygon([[x,y-u*.06],[x-u*.023,y+u*.02],[x+u*.023,y+u*.02]],'#36584d');}
  }
  if(style==='ripple'){
   wave(foot+u*.025,u*.008,13,'#b6d2c3');
   for(let j=0;j<5;j++){ctx.strokeStyle=['#8ab7b0','#d3e3d0'][j%2];ctx.lineWidth=u*.004;ctx.beginPath();ctx.ellipse(w*(.15+j*.2),foot+u*.105,u*.13,u*.04,j*.2,0,Math.PI*2);ctx.stroke();}
   for(const [x,y] of [[w*.16,foot+u*.1],[w*.45,foot+u*.15],[w*.76,foot+u*.065]]){circle(x,y,u*.042,'#6b9981');polygon([[x,y],[x+u*.045,y-u*.012],[x+u*.039,y+u*.014]],'#b6d2c3');flower(x-u*.01,y-u*.015,u*.024,'#e5b0ad');}
  }
  if(style==='festival'){
   for(let j=0;j<4;j++){const x=w*(.13+j*.245),y=foot+u*(.07+(j%2)*.06),r=u*(j%2?.055:.08);for(let i=0;i<14;i++){const a=i*Math.PI/7;line([[x+Math.cos(a)*r*.28,y+Math.sin(a)*r*.28],[x+Math.cos(a)*r,y+Math.sin(a)*r]],j%2?'#cf9e9e':'#dbc887',u*.0025);}star(x,y,u*.014,'#f6dfab',4);}
   for(let i=0;i<8;i++)for(const x of [u*.028,w-u*.028])star(x,h*(.1+i*.11),u*(i%2?.008:.013),i%2?'#b5c7cb':'#ead09c',4);
  }
  if(style==='cafe'){
   rect(0,foot+u*.02,w,u*.2,'#c39c76');ctx.strokeStyle='#94704b44';ctx.lineWidth=u*.001;for(let i=0;i<5;i++)line([[0,foot+u*(.04+i*.04)],[w,foot+u*(.04+i*.04)]],'#94704b44',u*.001);
   ctx.save();ctx.translate(w*.22,foot+u*.12);ctx.rotate(-.11);rect(-u*.16,-u*.08,u*.32,u*.16,'#f4ead1');for(let i=-5;i<6;i++){line([[i*u*.027,-u*.08],[i*u*.027,u*.08]],'#9ba88b55',u*.006);line([[-u*.16,i*u*.027],[u*.16,i*u*.027]],'#9ba88b55',u*.006);}ctx.restore();
   for(let i=0;i<8;i++){const x=w*(.48+i*.035),y=foot+u*(.07+(i%3)*.035);ctx.save();ctx.translate(x,y);ctx.rotate(i*.8);ctx.fillStyle=ink;ctx.beginPath();ctx.ellipse(0,0,u*.009,u*.015,0,0,Math.PI*2);ctx.fill();line([[0,-u*.01],[0,u*.01]],'#b18e69',u*.001);ctx.restore();}
   ctx.strokeStyle='#bd895d';ctx.lineWidth=u*.018;ctx.beginPath();ctx.arc(w*.22,foot+u*.12,u*.048,.35,Math.PI*1.8);ctx.stroke();line([[w*.18,foot+u*.1],[w*.185,foot+u*.14]],'#f6d8a2',u*.004);
  }
  if(style==='ribbon'){
   rect(u*.012,0,u*.035,h,'#bd8096');rect(0,foot+u*.065,w,u*.043,'#bd8096');line([[u*.029,0],[u*.029,h]],'#e6b8c4',u*.003);line([[0,foot+u*.084],[w,foot+u*.084]],'#e6b8c4',u*.003);
   for(let y=0;y<h;y+=u*.035)line([[u*.016,y],[u*.043,y+u*.018]],'#e9bcc633',u*.001);
   ctx.save();ctx.translate(w*.31,foot+u*.085);ctx.strokeStyle='#8c526d';ctx.lineWidth=u*.018;ctx.beginPath();ctx.moveTo(0,0);ctx.bezierCurveTo(-u*.17,-u*.11,-u*.17,u*.09,0,0);ctx.bezierCurveTo(u*.17,-u*.11,u*.17,u*.09,0,0);ctx.stroke();circle(0,0,u*.018,'#754455');ctx.restore();
  }
  if(style==='gallery'){
   rect(0,foot+u*.03,w*.29,u*.2,'#c75940');circle(w*.34,foot+u*.14,u*.11,'#d6b65d');rect(w*.52,foot+u*.07,w*.15,u*.15,'#47625e');polygon([[w*.69,h],[w*.91,foot+u*.01],[w*.91,h]],'#be7a5c');
   for(let i=0;i<4;i++)rect(w-u*.036,h*(.12+i*.19),u*.022,u*.09,['#c75940','#d6b65d','#47625e',accent][i]);
  }
  if(style==='arch'){
   for(let i=0;i<Math.ceil(w/(u*.07));i++){const x=i*u*.07;arch(x+u*.035,foot+u*.08,u*.025,u*.07,'#4a758c');arch(x+u*.035,foot+u*.083,u*.018,u*.063,'#deb77f');}
   for(let i=0;i<w/(u*.035);i++)polygon([[i*u*.035,h-u*.025],[i*u*.035+u*.0175,h-u*.043],[i*u*.035+u*.035,h-u*.025],[i*u*.035+u*.0175,h-u*.007]],i%2?'#738f9b':'#b48b60');
  }
  if(style==='constellation'){
   const pts=Array.from({length:8},(_,i)=>[w*(.04+i*.13),foot+u*(.065+(i*7%3)*.045)]);line(pts,'#8aabb3',u*.0018);pts.forEach(([x,y],i)=>{star(x,y,u*(i%2?.012:.017),'#f1dba1',4);circle(x,y,u*.003,'#fff4cf');});
   for(const x of [u*.027,w-u*.027]){const side=Array.from({length:6},(_,i)=>[x+(i%2?1:-1)*u*.012,h*(.13+i*.14)]);line(side,'#6e8c9a',u*.0012);side.forEach(([x,y])=>star(x,y,u*.008,'#e8d39e',4));}
  }
  if(style==='confetti'){
   for(let j=0;j<4;j++){ctx.strokeStyle=['#d65f4d','#467e96','#d6a437','#77996d'][j];ctx.lineWidth=u*.007;ctx.beginPath();const x=w*(.08+j*.22);ctx.moveTo(x,foot+u*.055);ctx.bezierCurveTo(x+u*.12,foot-u*.01,x-u*.06,h+u*.02,x+u*.1,h-u*.035);ctx.stroke();}
   for(let i=0;i<20;i++){const x=(i*137%997)/997*w,y=foot+u*(.025+(i*17%13)*.012);if(i%3)star(x,y,u*.012,['#d65f4d','#467e96','#d6a437'][i%3]);else circle(x,y,u*.009,'#789b68');}
  }
  if(style==='botanical'||style==='linen')for(const side of [1,-1]){
   const x=side===1?u*.03:w-u*.03;line([[x,h*.12],[x,h*.87]],style==='linen'?'#7f8a69':'#657e58',u*.002);
   for(let i=0;i<9;i++){const y=h*(.15+i*.08);leaf(x,y,u*(i%2?.045:.035),side*(i%2?.85:-.85),i%2?'#9bac7d':'#64855e');if(style==='linen'&&i%3===0)flower(x,y,u*.025,'#ba7856',4);}
  }
  if(style==='orchard')for(const side of [0,1])for(let i=0;i<5;i++){
   const x=side?w-u*.02:u*.02,y=h*(.15+i*.16);circle(x,y,u*(i%2?.035:.045),'#e4a344');leaf(x,y-u*.03,u*.04,side?.8:-.8,'#7d945b');
  }
  if(style==='air'){
   for(const [x,y,r] of [[w*.58,foot+u*.14,u*.044],[w*.8,u*.015,u*.055],[u*.018,h*.35,u*.042]]){circle(x,y,r,'#f6f4e9');circle(x+r*.8,y+r*.15,r*.7,'#f6f4e9');circle(x-r*.7,y+r*.2,r*.6,'#f6f4e9');}
   ctx.strokeStyle='#7da2a0';ctx.lineWidth=u*.002;ctx.setLineDash([u*.006,u*.009]);ctx.beginPath();ctx.moveTo(w*.4,h-u*.025);ctx.bezierCurveTo(w*.62,foot-u*.12,w*.4,foot+u*.23,w*.8,foot+u*.09);ctx.stroke();ctx.setLineDash([]);
  }
  if(style==='glow'){
   for(let i=0;i<4;i++){const x=w*(.42+i*.14),y=foot+u*(.065+(i%2)*.065),r=u*(i%2?.022:.035);const g=ctx.createRadialGradient(x,y,0,x,y,r*2.3);g.addColorStop(0,'#eebc7488');g.addColorStop(1,'#eebc7400');ctx.fillStyle=g;ctx.fillRect(x-r*2.3,y-r*2.3,r*4.6,r*4.6);rect(x-r*.65,y-r,r*1.3,r*1.7,'#e0a25d',r*.2);line([[x,y-r*.9],[x,y+r*.6]],'#f8ce8d',u*.002);line([[x,y+r*.75],[x,y+r*1.05]],'#d68b58',u*.002);}
  }
  if(style==='postcard'){
   ctx.strokeStyle='#9b9c7b44';ctx.lineWidth=u*.002;
   for(let i=0;i<4;i++){const y=foot+u*(.04+i*.04);line([[w*.48,y],[w*.6,y-u*.03],[w*.72,y+u*.02],[w*.9,y]],'#9b9c7b44',u*.002);}
   for(let i=0;i<4;i++)line([[w*(.48+i*.12),foot],[w*(.55+i*.1),h]],'#9b9c7b44',u*.002);
   ctx.strokeStyle='#b9594b';ctx.lineWidth=u*.002;ctx.setLineDash([u*.004,u*.005]);ctx.beginPath();ctx.moveTo(w*.47,h-u*.025);ctx.bezierCurveTo(w*.49,foot-u*.02,w*.6,h+u*.03,w*.67,foot+u*.055);ctx.stroke();ctx.setLineDash([]);circle(w*.67,foot+u*.055,u*.009,'#b9594b');circle(w*.67,foot+u*.055,u*.003,bg);
  }
  if(style==='terrace'){
   for(let i=0;i<12;i++){const bw=w/12,x=i*bw,bh=u*(.07+(i%4)*.025),y=h-bh;rect(x+u*.002,y,bw-u*.004,bh,['#c38966','#82988a','#d2b687','#b47766'][i%4]);polygon([[x,y],[x+bw/2,y-u*.024],[x+bw,y]],'#596666');for(let j=0;j<2;j++)rect(x+bw*(.2+j*.4),y+u*.018,bw*.17,u*.022,'#f2dfb2');rect(x+bw*.4,h-u*.035,bw*.2,u*.035,'#65776d');}
   for(let i=0;i<4;i++){const x=u*.025,y=h*(.2+i*.18);rect(x-u*.013,y,u*.026,u*.06,'#c38966');polygon([[x-u*.018,y],[x,y-u*.018],[x+u*.018,y]],'#65776d');}
  }
  if(style==='air'){
   ctx.setLineDash([u*.005,u*.009]);ctx.strokeStyle=pop;ctx.lineWidth=u*.002;ctx.beginPath();ctx.moveTo(w*.46,h-u*.045);ctx.bezierCurveTo(w*.7,foot-u*.03,w*.72,h+u*.04,w-u*.08,foot+u*.075);ctx.stroke();ctx.setLineDash([]);
   polygon([[w-u*.17,foot+u*.09],[w-u*.055,foot+u*.04],[w-u*.09,foot+u*.14],[w-u*.118,foot+u*.105]],ink);
   line([[w-u*.118,foot+u*.105],[w-u*.055,foot+u*.04]],'#f3ede0',u*.0015);
   for(let i=0;i<3;i++){const x=u*(.1+i*.035),y=u*.027;line([[x,y+u*.006],[x+u*.012,y],[x+u*.025,y+u*.006]],ink,u*.0015);}
  }
  if(style==='glow'){
   for(const [x,y,r] of [[u*.035,u*.055,u*.018],[w-u*.035,h*.32,u*.023],[w-u*.17,fy,u*.048],[w-u*.065,foot+u*.06,u*.03]]){
    const g=ctx.createRadialGradient(x,y,r*.2,x,y,r*2.4);g.addColorStop(0,'#f4c77c55');g.addColorStop(1,'#f4c77c00');ctx.fillStyle=g;ctx.fillRect(x-r*2.4,y-r*2.4,r*4.8,r*4.8);
    line([[x,y-r*1.4],[x,y-r]],ink,u*.0015);rect(x-r*.62,y-r*.8,r*1.24,r*1.6,'#e7b46d',r*.25);line([[x,y-r*.72],[x,y+r*.72]],'#9f633f');line([[x-r*.5,y-r*.3],[x+r*.5,y-r*.3]],'#f9dda7');
   }
   for(let i=0;i<24;i++)circle((i*137%997)/997*w,(i*97%991)/991*h,u*.0014,'#f8d99b');
  }
  if(style==='linen'){
   ctx.strokeStyle='#8f7660';ctx.lineWidth=u*.0015;ctx.setLineDash([u*.004,u*.005]);ctx.strokeRect(u*.02,u*.02,w-u*.04,h-u*.04);ctx.setLineDash([]);
   for(let i=0;i<4;i++){const x=artX+u*(i*.045),y=foot+u*(.06+(i%2)*.055);line([[x,y+u*.05],[x,y]],'#668066');flower(x,y,u*.02,i%2?'#d4ae71':'#ad6652',4);leaf(x+u*.005,y+u*.035,u*.016,.8,'#6d896a');}
   for(let i=0;i<8;i++){const x=u*(.11+i*.027),y=u*.027;line([[x-u*.005,y-u*.005],[x+u*.005,y+u*.005]],pop);line([[x-u*.005,y+u*.005],[x+u*.005,y-u*.005]],pop);}
  }
  if(style==='tide'){
   for(let j=0;j<3;j++){ctx.strokeStyle=['#80a8ac','#4e8598','#b1c9bc'][j];ctx.lineWidth=u*.003;ctx.beginPath();for(let x=0;x<=w;x+=u*.008){const y=h-u*(.025+j*.016)+Math.sin(x/u*20+j)*u*.006;x?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.stroke();}
   const x=w-u*.15,y=foot+u*.13;polygon([[x-u*.067,y],[x+u*.067,y],[x+u*.04,y+u*.025],[x-u*.042,y+u*.025]],ink);line([[x,y],[x,y-u*.1]],ink);polygon([[x-u*.005,y-u*.1],[x-u*.005,y-u*.012],[x-u*.06,y-u*.012]],'#faf3de');polygon([[x+u*.005,y-u*.08],[x+u*.005,y-u*.012],[x+u*.052,y-u*.012]],pop);
   for(let i=0;i<3;i++){const x=u*(.18+i*.06);line([[x,u*.035],[x+u*.014,u*.027],[x+u*.028,u*.035]],ink,u*.0015);}
  }
  if(style==='botanical'){
   for(const [x,y,angle] of [[u*.03,h*.4,-.15],[w-u*.027,h*.23,.15],[w-u*.14,foot+u*.17,-.55]]){ctx.save();ctx.translate(x,y);ctx.rotate(angle);line([[0,u*.02],[0,-u*.13]],ink);for(let i=0;i<5;i++){const yy=-u*i*.024;leaf(-u*.003,yy,u*.022,-.8,i%2?'#829868':'#52745b');leaf(u*.003,yy-u*.012,u*.018,.8,'#9cad7c');}ctx.restore();}
   rect(w-u*.27,foot+u*.045,u*.07,u*.09,'#c4cead',u*.003);line([[w-u*.26,foot+u*.065],[w-u*.21,foot+u*.065]],ink,u*.001);line([[w-u*.26,foot+u*.08],[w-u*.225,foot+u*.08]],ink,u*.001);
  }
  if(style==='gallery'){
   circle(w-u*.09,foot+u*.1,u*.06,pop);rect(w-u*.23,foot+u*.04,u*.09,u*.12,ink);polygon([[w-u*.18,foot+u*.17],[w-u*.08,foot+u*.17],[w-u*.08,foot+u*.065]],'#d4b260');
   for(let i=0;i<4;i++)rect(u*(.07+i*.04),u*.022,u*.028,u*.009,[ink,pop,'#d4b260',accent][i]);
   line([[px,foot+u*.025],[px+pw*.5,foot+u*.025]],ink,u*.0012);
  }
  if(style==='film'){
   const x=w*.59,y=foot+u*.11;ctx.strokeStyle='#a98b5c';ctx.lineWidth=u*.002;ctx.beginPath();ctx.arc(x,y,u*.043,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.arc(x,y,u*.034,0,Math.PI*2);ctx.stroke();star(x,y,u*.018,'#c9a66f',5);
   ctx.fillStyle='#c6aa7b';ctx.font=`${u*.014}px monospace`;ctx.textAlign='center';ctx.fillText('35 mm  /  FRAME 01',w*.5,u*.035);ctx.textAlign='left';

   for(const x of [u*.018,w-u*.035])for(let y=u*.02;y<h;y+=u*.058)rect(x,y,u*.017,u*.026,'#c9c2ac',u*.003);
   rect(w-u*.27,foot+u*.04,u*.19,u*.11,'#c59b62',u*.007);for(let i=0;i<2;i++)circle(w-u*(.27-i*.19),foot+u*.095,u*.009,bg);
   ctx.strokeStyle=bg;ctx.lineWidth=u*.0012;ctx.setLineDash([u*.003,u*.004]);ctx.beginPath();ctx.moveTo(w-u*.13,foot+u*.05);ctx.lineTo(w-u*.13,foot+u*.14);ctx.stroke();ctx.setLineDash([]);
   ctx.fillStyle=bg;ctx.font=`bold ${u*.027}px monospace`;ctx.fillText('01',w-u*.11,foot+u*.105);line([[w-u*.25,foot+u*.075],[w-u*.15,foot+u*.075]],bg);line([[w-u*.25,foot+u*.1],[w-u*.18,foot+u*.1]],bg);
  }


  if(style==='postcard'){
   ctx.strokeStyle='#5e8190';ctx.lineWidth=u*.005;ctx.setLineDash([u*.018,u*.026]);ctx.strokeRect(u*.017,u*.017,w-u*.034,h-u*.034);ctx.setLineDash([]);
   rect(w-u*.15,foot+u*.035,u*.075,u*.105,'#c6aa76',u*.002);rect(w-u*.143,foot+u*.042,u*.061,u*.091,'#efe4bf');polygon([[w-u*.139,foot+u*.115],[w-u*.112,foot+u*.063],[w-u*.088,foot+u*.115]],'#658b7e');circle(w-u*.1,foot+u*.062,u*.009,pop);
   ctx.strokeStyle=ink;ctx.lineWidth=u*.0015;for(let i=0;i<3;i++){ctx.beginPath();ctx.moveTo(w-u*.28,foot+u*(.065+i*.02));ctx.bezierCurveTo(w-u*.23,foot+u*(.04+i*.02),w-u*.21,foot+u*(.09+i*.02),w-u*.17,foot+u*(.065+i*.02));ctx.stroke();}
  }
  if(style==='petal'){
   rect(w-u*.22,foot+u*.11,u*.11,u*.065,'#9b6672',u*.006);line([[w-u*.22,foot+u*.135],[w-u*.11,foot+u*.135]],'#e6b39c',u*.003);
   for(let i=0;i<5;i++){const x=w-u*(.21-i*.025),y=foot+u*(.06+(i%2)*.018);line([[x,foot+u*.12],[x,y]],'#6b8867');flower(x,y,u*(i%2?.028:.023),['#b75978','#e69d94','#f2bd87'][i%3]);}
   flower(u*.03,u*.03,u*.034,'#ba627c');flower(w-u*.022,h*.23,u*.025,'#e3a08b');leaf(u*.03,u*.09,u*.03,.3,'#7e9472');
  }
  if(style==='constellation'){
   for(let i=0;i<80;i++){const x=(i*173%997)/997*w,y=(i*271%991)/991*h;circle(x,y,u*(i%3?.001:.002),'#c6d3cf');}
   circle(w-u*.11,foot+u*.075,u*.04,ink);circle(w-u*.093,foot+u*.062,u*.036,bg);
   const pts=[[w-u*.29,foot+u*.13],[w-u*.23,foot+u*.055],[w-u*.19,foot+u*.12],[w-u*.12,foot+u*.16]];line(pts,'#708c9b',u*.0015);pts.forEach(([x,y])=>star(x,y,u*.007,ink,4));
   ctx.strokeStyle='#e4cc9555';ctx.lineWidth=u*.001;ctx.strokeRect(px-u*.009,py-u*.009,pw+u*.018,ph+u*.018);
  }
  if(style==='ripple'){
   const x=w-u*.16,y=foot+u*.105;ctx.strokeStyle='#87a9a2';ctx.lineWidth=u*.0015;for(let i=0;i<4;i++){ctx.beginPath();ctx.ellipse(x,y,u*(.045+i*.02),u*(.025+i*.012),-.15,0,Math.PI*2);ctx.stroke();}
   for(const [dx,dy,a] of [[-.04,0,.4],[.05,.025,3.4]]){ctx.save();ctx.translate(x+dx*u,y+dy*u);ctx.rotate(a);ctx.fillStyle=pop;ctx.beginPath();ctx.ellipse(0,0,u*.027,u*.011,0,0,Math.PI*2);ctx.fill();polygon([[u*.02,0],[u*.04,-u*.017],[u*.04,u*.017]],pop);circle(-u*.015,-u*.002,u*.002,ink);ctx.restore();}
   for(const [x,y] of [[u*.035,h*.2],[w-u*.03,h*.4]]){circle(x,y,u*.028,'#74967d');polygon([[x,y],[x+u*.03,y-u*.01],[x+u*.025,y+u*.015]],bg);}
  }


  if(style==='confetti'){
   for(let i=0;i<30;i++){const x=(i*137%997)/997*w,y=i%2?u*.025:h-u*.025;ctx.save();ctx.translate(x,y);ctx.rotate(i);rect(-u*.004,-u*.009,u*.008,u*.018,['#d65f4d','#467e96','#dcac3b','#789360'][i%4]);ctx.restore();}
   const x=w-u*.17,y=foot+u*.11;polygon([[x-u*.07,y+u*.06],[x+u*.04,y+u*.04],[x-u*.045,y-u*.07]],pop);line([[x-u*.04,y-u*.02],[x+u*.004,y+u*.035]],'#eabe57',u*.01);for(let i=0;i<4;i++)star(x+u*(.02+i*.025),y-u*(.02+(i%2)*.055),u*.012,['#467e96','#d9a430'][i%2]);
  }
  if(style==='orchard'){
   for(const [dx,dy,r] of [[-.07,.015,.038],[0,-.005,.048],[.065,.025,.032]]){const x=w-u*.17+u*dx,y=fy+u*dy;circle(x,y,u*r,'#e69a31');leaf(x,y-u*r,u*.025,-.65,'#638349');line([[x,y-u*r],[x+u*.008,y-u*(r+.012)]],ink,u*.003);}
   for(let i=0;i<7;i++){const x=u*(.04+i*.045);leaf(x,u*.035,u*.014,(i%2?1:-1)*.6,'#8a9b60');}
   ctx.strokeStyle='#dfbd6e';ctx.lineWidth=u*.002;for(let x=0;x<w;x+=u*.03)line([[x,h-u*.015],[x+u*.015,h-u*.015]],'#dfbd6e',u*.002);
  }

  if(style==='cafe'){
   const x=w-u*.16,y=foot+u*.12;ctx.strokeStyle=pop;ctx.lineWidth=u*.006;ctx.beginPath();ctx.ellipse(x+u*.06,y-u*.023,u*.025,u*.02,0,0,Math.PI*2);ctx.stroke();rect(x-u*.055,y-u*.06,u*.11,u*.065,'#f8f0da',u*.016);ctx.fillStyle='#775441';ctx.beginPath();ctx.ellipse(x,y-u*.055,u*.05,u*.012,0,0,Math.PI*2);ctx.fill();line([[x-u*.075,y+u*.015],[x+u*.08,y+u*.015]],pop,u*.005);
   for(let i=0;i<2;i++){const xx=x+u*(i*.03-.015);ctx.strokeStyle=pop;ctx.lineWidth=u*.002;ctx.beginPath();ctx.moveTo(xx,y-u*.08);ctx.bezierCurveTo(xx-u*.015,y-u*.1,xx+u*.015,y-u*.11,xx,y-u*.13);ctx.stroke();}
   for(let i=0;i<5;i++){const x=u*(.08+i*.032);ctx.save();ctx.translate(x,u*.028);ctx.rotate(.6);ctx.fillStyle=pop;ctx.beginPath();ctx.ellipse(0,0,u*.006,u*.01,0,0,Math.PI*2);ctx.fill();line([[0,-u*.007],[0,u*.007]],bg,u*.001);ctx.restore();}
  }
  if(style==='festival'){
   for(const [x,y,r,color] of [[w-u*.15,foot+u*.085,u*.065,'#d7979d'],[w-u*.29,foot+u*.12,u*.037,'#dbbd78'],[u*.032,u*.045,u*.038,'#9bafbf']]){for(let i=0;i<12;i++){const a=i*Math.PI/6;line([[x+Math.cos(a)*r*.35,y+Math.sin(a)*r*.35],[x+Math.cos(a)*r,y+Math.sin(a)*r]],color,u*.002);circle(x+Math.cos(a)*r*1.18,y+Math.sin(a)*r*1.18,u*.002,color);}star(x,y,r*.14,ink,4);}
   for(let i=0;i<12;i++)star((i*73%997)/997*w,h-u*.027,u*.004,ink,4);
  }
  if(panoramic.has(style)){ctx.fillStyle=ink;ctx.textAlign='center';ctx.font=`500 ${u*.025}px sans-serif`;ctx.fillText(title,w/2,u*.038,w-u*.2);ctx.restore();return;}
  // Editorial label lives in the footer, separate from the illustration.
  ctx.fillStyle=ink;ctx.textAlign='left';ctx.textBaseline='alphabetic';ctx.font=`500 ${u*.032}px sans-serif`;ctx.fillText(title,px,foot+u*.09,w-u*.47);
  ctx.globalAlpha=.72;ctx.font=`${u*.0105}px monospace`;ctx.fillText(subtitle,px,foot+u*.126,w-u*.47);ctx.globalAlpha=1;
  ctx.fillStyle=pop;ctx.fillRect(px,foot+u*.155,u*.028,u*.004);ctx.fillStyle=ink;ctx.font=`${u*.009}px monospace`;ctx.fillText('STUDIO  /  '+String(designs.findIndex(d=>d[0]===style)+1).padStart(2,'0'),px+u*.04,foot+u*.161);
  ctx.restore();
 }

 const catalog=designs.map(([style,name])=>({id:'studio-'+style,style,original:true,names:{zh:name},...shape(1216,1824,style),landscape:shape(1824,1216,style)}));
 function palette(p){
  if(!p||!images.has(p.src))return [132,153,141];
  const tone=filter(p)[0],key=p.src+'|'+tone;if(colors.has(key))return colors.get(key);
  const c=document.createElement('canvas');c.width=c.height=24;
  const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(Tone.image(images.get(p.src),tone,true),0,0,24,24);
  const data=ctx.getImageData(0,0,24,24).data,bins=Array.from({length:12},()=>({count:0,sum:[0,0,0]})),sum=[0,0,0];
  for(let i=0;i<data.length;i+=4){
   const rgb=[data[i],data[i+1],data[i+2]],hi=Math.max(...rgb),lo=Math.min(...rgb),delta=hi-lo,light=(hi+lo)/2;
   rgb.forEach((v,j)=>sum[j]+=v);if(delta<28||light<28||light>226)continue;
   let hue=hi===rgb[0]?(rgb[1]-rgb[2])/delta:hi===rgb[1]?2+(rgb[2]-rgb[0])/delta:4+(rgb[0]-rgb[1])/delta;
   const bin=bins[Math.floor(((hue+6)%6)*2)];bin.count++;rgb.forEach((v,j)=>bin.sum[j]+=v);
  }
  const dominant=bins.reduce((a,b)=>a.count>=b.count?a:b),rgb=(dominant.count>=24*24*.08?dominant.sum.map(v=>v/dominant.count):sum.map(v=>v/(24*24))).map(Math.round);
  if(colors.size>=48)colors.delete(colors.keys().next().value);colors.set(key,rgb);return rgb;
 }

 function paint(ctx,p,x,y,w,h,e){
  const rgb=palette(p),mix=(white,a)=>`rgb(${rgb.map(v=>Math.round(v*a+white*(1-a))).join(',')})`,sx=w/e.width,sy=h/e.height,u=Math.min(w,h),style=e.style;
  const backgrounds={glow:'#273747',linen:'#eee1cd',tide:'#dce9e5',botanical:'#e2e8d5',gallery:'#f2e7d8',film:'#242b30',sunset:'#f0cbb5',arch:'#e6d6c1',postcard:'#eee4cf',petal:'#f3dfdc',constellation:'#172c46',ripple:'#e1e9df',ribbon:'#eadadf',terrace:'#e4d8c6',confetti:'#f5e5b7',orchard:'#f4e7c7',alpine:'#dde8e5',cafe:'#e9ddca',festival:'#30304b'};
  ctx.save();ctx.translate(x,y);ctx.fillStyle=KidsTemplates.backgrounds[style]||backgrounds[style]||mix(250,.15);ctx.fillRect(0,0,w,h);
  const px=e.margin.left*sx,py=e.margin.top*sy,pw=e.crop.width*sx,ph=e.crop.height*sy;
  ctx.save();ctx.beginPath();ctx.rect(0,0,w,h);ctx.rect(px,py,pw,ph);ctx.clip('evenodd');
  // Quiet paper textures support, rather than compete with, each illustration.
  if(['linen','cafe'].includes(style)){
   ctx.strokeStyle='#78604712';ctx.lineWidth=u*.0007;
   for(let i=u*.008;i<w;i+=u*.009){ctx.beginPath();ctx.moveTo(i,0);ctx.lineTo(i,h);ctx.stroke();}
   for(let i=u*.008;i<h;i+=u*.009){ctx.beginPath();ctx.moveTo(0,i);ctx.lineTo(w,i);ctx.stroke();}
  }
  if(['postcard','botanical'].includes(style)){
   ctx.strokeStyle='#60735a16';ctx.lineWidth=u*.0008;for(let i=u*.015;i<h;i+=u*.017){ctx.beginPath();ctx.moveTo(0,i);ctx.lineTo(w,i);ctx.stroke();}
  }
  if(['petal','orchard'].includes(style)){
   const step=u*.032;ctx.fillStyle=style==='petal'?'#c07b8c0d':'#b9a05a12';for(let j=0;j<h/step;j++)for(let i=0;i<w/step;i++)if((i+j)%2===0)ctx.fillRect(i*step,j*step,step,step);
  }
  if(['glow','sunset','tide'].includes(style)){
   const g=ctx.createLinearGradient(0,0,w,h);g.addColorStop(0,style==='glow'?'#171e3600':mix(250,.14));g.addColorStop(1,'#ffffff00');ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
  }
  const box={margin:{left:px,top:py},crop:{width:pw,height:ph}};
  if(KidsTemplates.backgrounds[style])KidsTemplates.paint(ctx,w,h,style,box);
  else ornament(ctx,w,h,style,box,mix(130,.65));
  ctx.restore();
  // Keep the shared photo renderer in paper coordinates for editing and overlays.
  ctx.translate(-x,-y);drawPhoto(ctx,p,x+px,y+py,pw,ph,'cover');ctx.restore();
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
