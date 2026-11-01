/* Original little characters and scenes; no external artwork. */
window.KidsTemplates=(()=>{
 const designs=[['kids-dino','恐龙探险队'],['kids-space','太空好朋友'],['kids-ocean','海底游乐园'],['kids-bakery','熊兔甜品屋'],['kids-unicorn','彩虹独角兽'],['kids-picnic','森林野餐日'],['kids-train','小动物列车'],['kids-ducks','鸭鸭下雨天'],['kids-art','怪兽画画班'],['kids-moon','月亮晚安曲']];
 const backgrounds={'kids-dino':'#f3edcf','kids-space':'#28374e','kids-ocean':'#d9f1ef','kids-bakery':'#f9e5d9','kids-unicorn':'#eee8f6','kids-picnic':'#eaf0d9','kids-train':'#f2e8cb','kids-ducks':'#e1edf3','kids-art':'#f7ecd6','kids-moon':'#333c60'};
 function paint(ctx,w,h,style,box){
  const u=Math.min(w,h),foot=box.margin.top+box.crop.height,bg=backgrounds[style],ink='#3e5159',outline=u*.0018;
  ctx.save();ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.shadowBlur=0;ctx.shadowOffsetX=ctx.shadowOffsetY=0;ctx.textBaseline='alphabetic';ctx.textAlign='center';ctx.lineCap='round';ctx.lineJoin='round';ctx.setLineDash([]);
  const ellipse=(x,y,rx,ry,color,angle=0)=>{ctx.fillStyle=color;ctx.beginPath();ctx.ellipse(x,y,rx,ry,angle,0,Math.PI*2);ctx.fill();};
  const dot=(x,y,r,color)=>ellipse(x,y,r,r,color);
  const rect=(x,y,ww,hh,color,r=0)=>{ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,ww,hh,r);ctx.fill();};
  const poly=(pts,color)=>{ctx.fillStyle=color;ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();ctx.fill();};
  const line=(pts,color=ink,width=outline)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.stroke();};
  const curve=(x,y,a,b,c,d,xx,yy,color=ink,width=outline)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x,y);ctx.bezierCurveTo(a,b,c,d,xx,yy);ctx.stroke();};
  const star=(x,y,r,color,n=5)=>{const pts=[];for(let i=0;i<n*2;i++){const a=-Math.PI/2+i*Math.PI/n,k=i%2?.43:1;pts.push([x+Math.cos(a)*r*k,y+Math.sin(a)*r*k]);}poly(pts,color);};
  const cloud=(x,y,r,color='#fff9e8')=>{ellipse(x,y,r*1.3,r*.48,color);dot(x-r*.54,y-r*.2,r*.48,color);dot(x+r*.04,y-r*.45,r*.6,color);dot(x+r*.65,y-r*.12,r*.4,color);};
  const leaf=(x,y,r,angle,color)=>ellipse(x,y,r*.42,r,color,angle);
  const sprig=(x,y,r,color)=>{curve(x,y,x-r*.2,y-r*.5,x+r*.2,y-r,x,y-r*1.3,color,u*.002);for(let i=0;i<3;i++){leaf(x-r*.19,y-r*(.2+i*.35),r*.24,-.8,color);leaf(x+r*.19,y-r*(.35+i*.35),r*.24,.8,color);}};
  const flower=(x,y,r,color)=>{for(let i=0;i<5;i++){const a=i*Math.PI*2/5;dot(x+Math.cos(a)*r*.65,y+Math.sin(a)*r*.65,r*.44,color);}dot(x,y,r*.3,'#e9b94c');};
  const smile=(x,y,s,wink=false)=>{ctx.fillStyle=ink;if(wink)curve(x-s*.38,y,x-s*.3,y-s*.12,x-s*.18,y-s*.12,x-s*.1,y,ink,s*.07);else ellipse(x-s*.27,y,s*.067,s*.1,ink);ellipse(x+s*.27,y,s*.067,s*.1,ink);curve(x-s*.13,y+s*.19,x-s*.06,y+s*.32,x+s*.06,y+s*.32,x+s*.13,y+s*.19,ink,s*.055);ellipse(x-s*.46,y+s*.16,s*.14,s*.08,'#e99d8f');ellipse(x+s*.46,y+s*.16,s*.14,s*.08,'#e99d8f');};
  const bear=(x,y,r,color='#c59672',kind='bear',wink=false)=>{if(kind==='rabbit'){ellipse(x-r*.48,y-r*.86,r*.24,r*.8,color,-.15);ellipse(x+r*.45,y-r*.86,r*.24,r*.8,color,.15);ellipse(x-r*.48,y-r*.96,r*.09,r*.5,'#e8ac9f',-.15);ellipse(x+r*.45,y-r*.96,r*.09,r*.5,'#e8ac9f',.15);}else{dot(x-r*.72,y-r*.64,r*.38,color);dot(x+r*.72,y-r*.64,r*.38,color);dot(x-r*.72,y-r*.64,r*.19,'#e7b8a1');dot(x+r*.72,y-r*.64,r*.19,'#e7b8a1');}ellipse(x,y,r,r*.84,color);ellipse(x,y+r*.27,r*.43,r*.3,'#f5dfbc');smile(x,y-r*.02,r*.92,wink);};
  const actor=(x,y,k)=>{ctx.save();ctx.translate(x,y);ctx.scale(k,k);ctx.translate(-x,-y);};
  const ground=(color)=>{rect(0,foot+u*.155,w,h-foot,color);};
  const butterfly=(x,y,r)=>{ellipse(x-r*.6,y-r*.3,r*.63,r*.8,'#e8b075',-.25);ellipse(x+r*.6,y-r*.3,r*.63,r*.8,'#e8b075',.25);ellipse(x-r*.5,y+r*.45,r*.45,r*.5,'#ca8c9c');ellipse(x+r*.5,y+r*.45,r*.45,r*.5,'#ca8c9c');line([[x,y-r*.6],[x,y+r*.7]],ink,u*.0015);};
  // The photograph stays above a miniature story, with small details along the sides.
  if(style==='kids-dino'){
   ground('#b6ce91');curve(0,foot+u*.17,w*.3,foot+u*.07,w*.7,h+u*.02,w,foot+u*.155,'#95b47c',u*.045);
   const dino=(x,y,s,color,flip=false)=>{ctx.save();ctx.translate(x,y);if(flip)ctx.scale(-1,1);poly([[-s*.5,s*.18],[-s*1.3,-s*.05],[-s*.74,s*.55]],color);ellipse(0,s*.2,s*.72,s*.47,color);rect(s*.1,-s*.53,s*.4,s*.85,color,s*.15);ellipse(s*.4,-s*.55,s*.44,s*.33,color);for(let i=0;i<3;i++)poly([[-s*.48+i*s*.3,-s*.13],[-s*.35+i*s*.3,-s*.4],[-s*.18+i*s*.3,-s*.14]],'#6d9876');for(const xx of [-s*.3,s*.35])rect(xx-s*.12,s*.4,s*.24,s*.33,color,s*.08);ellipse(s*.09,s*.22,s*.4,s*.29,'#dce4ad');smile(s*.48,-s*.59,s*.4);dot(-s*.29,s*.1,s*.08,'#78a07d');dot(-s*.03,s*.03,s*.065,'#78a07d');rect(s*.25,-s*.95,s*.5,s*.12,'#bd9564',s*.04);ellipse(s*.5,-s*.82,s*.42,s*.07,'#bd9564');ctx.restore();};
   dino(w*.5-u*.18,foot+u*.108,u*.09,'#8dbd98');dino(w*.5+u*.17,foot+u*.12,u*.071,'#dfb270',true);
   ellipse(w*.5,foot+u*.145,u*.035,u*.045,'#fff0cc');poly([[w*.5-u*.03,foot+u*.12],[w*.5-u*.015,foot+u*.135],[w*.5,foot+u*.117],[w*.5+u*.015,foot+u*.135],[w*.5+u*.03,foot+u*.12]],'#a6b77b');star(w*.53,foot+u*.08,u*.012,'#dca45e',4);
   for(const x of [u*.025,w-u*.025]){sprig(x,h*.45,u*.1,'#a2bc7c');leaf(x,h*.75,u*.045,.5,'#87a975');}for(let i=0;i<7;i++)ellipse(w*(.09+i*.14),h-u*.017,u*.009,u*.004,'#6b9979',i*.5);butterfly(w*.87,foot+u*.048,u*.014);
  }
  if(style==='kids-space'){
   ground('#64738d');ellipse(w*.45,h,u*.43,u*.075,'#8991a7');for(let i=0;i<7;i++)ellipse(w*(.04+i*.15),h-u*(.012+(i%2)*.015),u*(.017+(i%3)*.005),u*.006,'#455d79');
   ctx.strokeStyle='#9dadbf66';ctx.lineWidth=u*.0015;ctx.setLineDash([u*.005,u*.008]);ctx.beginPath();ctx.ellipse(w*.5,foot+u*.11,w*.42,u*.072,-.025,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);star(w*.14,foot+u*.075,u*.012,'#eccd90',4);star(w*.85,foot+u*.14,u*.012,'#eccd90',4);
   const x=w*.5-u*.18,y=foot+u*.08;actor(x,foot+u*.11,1.25);rect(x-u*.038,y+u*.02,u*.076,u*.07,'#e9eadb',u*.025);for(const xx of [-.024,.024])rect(x+u*xx-u*.01,y+u*.065,u*.02,u*.035,'#f3b36f',u*.006);line([[x-u*.03,y+u*.04],[x-u*.066,y+u*.02]],'#ececdf',u*.015);line([[x+u*.03,y+u*.04],[x+u*.07,y-u*.005]],'#ececdf',u*.015);dot(x,y,u*.049,'#edf0e1');dot(x,y,u*.039,'#779bb0');bear(x,y+u*.006,u*.027,'#c69b7b');curve(x-u*.025,y-u*.02,x-u*.01,y-u*.035,x+u*.01,y-u*.035,x+u*.022,y-u*.025,'#d5e9e9',u*.004);rect(x-u*.012,y+u*.035,u*.024,u*.018,'#eca765',u*.004);ctx.restore();
   const rx=w*.5+u*.2,ry=foot+u*.095;actor(rx,foot+u*.11,1.2);ellipse(rx,ry,u*.036,u*.068,'#f1e9d2');poly([[rx-u*.033,ry+u*.008],[rx-u*.06,ry+u*.05],[rx-u*.027,ry+u*.045]],'#e29b7b');poly([[rx+u*.033,ry+u*.008],[rx+u*.06,ry+u*.05],[rx+u*.027,ry+u*.045]],'#e29b7b');dot(rx,ry-u*.012,u*.021,'#658ca5');dot(rx,ry-u*.012,u*.013,'#aecdd0');poly([[rx-u*.015,ry+u*.06],[rx,ry+u*.095],[rx+u*.015,ry+u*.06]],'#edbd69');ctx.restore();
   dot(w*.5,foot+u*.107,u*.027,'#9db6a2');smile(w*.5,foot+u*.102,u*.024,true);line([[w*.5,foot+u*.08],[w*.5,foot+u*.063]],'#9db6a2');dot(w*.5,foot+u*.057,u*.007,'#e8c77c');
   for(let i=0;i<16;i++){const x=i%2?u*.03:w-u*.03,y=h*(.09+Math.floor(i/2)*.115);star(x,y,u*(i%3?.007:.014),i%3?'#c2d8d4':'#eed19b',4);}ctx.strokeStyle='#b796ba';ctx.lineWidth=u*.004;ctx.beginPath();ctx.ellipse(w-u*.025,h*.25,u*.055,u*.016,-.6,0,Math.PI*2);ctx.stroke();dot(w-u*.025,h*.25,u*.025,'#bda4bf');
  }
  if(style==='kids-ocean'){
   ground('#e7d3a4');for(let j=0;j<3;j++)curve(0,foot+u*(.035+j*.035),w*.28,foot-u*.02+j*u*.035,w*.7,foot+u*.1+j*u*.02,w,foot+u*(.035+j*.035),['#b3dbd4','#94cbc8','#79b9be'][j],u*.025);
   for(const x of [w*.09,w*.91]){const y=foot+u*.18;line([[x,y],[x,y-u*.08]],'#cf9a9c',u*.009);curve(x,y-u*.04,x-u*.025,y-u*.04,x-u*.035,y-u*.055,x-u*.028,y-u*.075,'#cf9a9c',u*.007);curve(x,y-u*.02,x+u*.025,y-u*.035,x+u*.035,y-u*.05,x+u*.025,y-u*.063,'#cf9a9c',u*.007);sprig(x+u*.04,y,u*.06,'#82b39c');}
   for(const [x,y,a] of [[w*.15,foot+u*.045,0],[w*.83,foot+u*.048,Math.PI]]){ctx.save();ctx.translate(x,y);ctx.rotate(a);ellipse(0,0,u*.022,u*.011,'#d7b16d');poly([[-u*.018,0],[-u*.032,-u*.012],[-u*.032,u*.012]],'#d7b16d');dot(u*.012,-u*.002,u*.002,ink);ctx.restore();}
   const x=w*.5-u*.16,y=foot+u*.1;actor(x,foot+u*.11,1.3);ellipse(x,y,u*.09,u*.045,'#719eaf');poly([[x+u*.073,y],[x+u*.12,y-u*.04],[x+u*.12,y+u*.025]],'#719eaf');ellipse(x-u*.01,y+u*.02,u*.062,u*.023,'#c7e0d7');smile(x-u*.045,y-u*.007,u*.028);ellipse(x,y+u*.027,u*.028,u*.012,'#547f95',.5);curve(x-u*.028,y-u*.048,x-u*.06,y-u*.08,x-u*.04,y-u*.09,x-u*.028,y-u*.07,'#82bec5',u*.004);curve(x-u*.025,y-u*.048,x,y-u*.085,x-u*.006,y-u*.092,x-u*.022,y-u*.066,'#82bec5',u*.004);ctx.restore();
   const ox=w*.5+u*.19,oy=foot+u*.11;actor(ox,foot+u*.12,1.3);for(let i=0;i<5;i++)curve(ox+u*(i*.013-.026),oy+u*.02,ox+u*(i*.02-.04),oy+u*.065,ox+u*(i*.026-.045),oy+u*.04,ox+u*(i*.027-.054),oy+u*.055,'#dc9f97',u*.011);ellipse(ox,oy,u*.038,u*.04,'#e4aaa0');smile(ox,oy,u*.031,true);star(ox+u*.026,oy-u*.034,u*.014,'#f0d58a');ctx.restore();
   for(const x of [u*.035,w-u*.035])for(let i=0;i<3;i++){curve(x,h*.85,x+u*(i*.02-.02),h*.7,x-u*.018,h*.6,x+u*(i*.018-.018),h*.5,'#7fb09a',u*.012);}
   for(let i=0;i<8;i++){const x=w*(.04+i*.13),y=foot+u*(.185+(i%2)*.012);if(i%3)ellipse(x,y,u*.014,u*.009,'#c7ae83');else star(x,y,u*.02,'#d99477');}for(let i=0;i<10;i++){ctx.strokeStyle='#7abac0';ctx.lineWidth=u*.0015;ctx.beginPath();ctx.arc(i%2?u*.033:w-u*.028,h*(.12+Math.floor(i/2)*.17),u*(.007+(i%3)*.004),0,Math.PI*2);ctx.stroke();}
  }
  if(style==='kids-bakery'){
   ground('#cfa585');rect(0,foot+u*.155,w,u*.012,'#a57d69');
   const x=w*.5-u*.17,y=foot+u*.098;actor(x,foot+u*.11,1.28);rect(x-u*.033,y+u*.028,u*.066,u*.063,'#c8d7bd',u*.012);bear(x,y,u*.036,'#c69a76');cloud(x,y-u*.04,u*.029,'#fff9e7');rect(x-u*.028,y-u*.043,u*.056,u*.016,'#fff9e7');line([[x-u*.025,y+u*.042],[x+u*.025,y+u*.042]],'#f9f1d7',u*.003);ctx.restore();
   const bx=w*.5+u*.17,by=foot+u*.1;actor(bx,foot+u*.11,1.3);rect(bx-u*.029,by+u*.028,u*.058,u*.055,'#dda4a3',u*.01);bear(bx,by,u*.03,'#fff0d8','rabbit',true);poly([[bx-u*.008,by-u*.047],[bx-u*.026,by-u*.06],[bx-u*.022,by-u*.032]],'#b98493');poly([[bx-u*.008,by-u*.047],[bx+u*.01,by-u*.06],[bx+u*.014,by-u*.033]],'#b98493');ctx.restore();
   for(let i=0;i<3;i++){const xx=w*.5+u*(i*.05-.05),yy=foot+u*.16;poly([[xx-u*.019,yy-u*.015],[xx+u*.019,yy-u*.015],[xx+u*.014,yy+u*.014],[xx-u*.014,yy+u*.014]],'#d7b477');cloud(xx,yy-u*.02,u*.019,['#fff4dc','#e7b1b6','#b7cba6'][i]);dot(xx,yy-u*.037,u*.006,'#c87978');}
   for(let i=0;i<7;i++){const x=w*(.06+i*.15);ctx.strokeStyle='#d4a797';ctx.lineWidth=u*.002;ctx.beginPath();ctx.arc(x,u*.012,u*.023,0,Math.PI);ctx.stroke();}for(const x of [u*.027,w-u*.027])for(let i=0;i<4;i++){dot(x,h*(.2+i*.2),u*.018,'#e6c694');for(let j=0;j<3;j++)dot(x+u*(j*.009-.009),h*(.2+i*.2)+u*(j%2?.006:-.004),u*.002,'#9e735f');}
  }
  if(style==='kids-unicorn'){
   for(let i=0;i<5;i++){ctx.strokeStyle=['#e7a9ac','#edc58e','#e9dd9b','#afcbb7','#aebed7'][i];ctx.lineWidth=u*.012;ctx.beginPath();ctx.arc(w*.5,foot+u*.165,u*(.14-i*.013),Math.PI,0);ctx.stroke();}
   for(let i=0;i<7;i++)cloud(w*(i/6),h-u*.01,u*.07,i%2?'#e5ddef':'#fbf3e7');
   const x=w*.5-u*.2,y=foot+u*.12;actor(x,foot+u*.13,1.25);ellipse(x,y+u*.023,u*.049,u*.029,'#fff5e7');rect(x-u*.035,y+u*.026,u*.013,u*.052,'#fff5e7',u*.006);rect(x+u*.022,y+u*.026,u*.013,u*.052,'#fff5e7',u*.006);ellipse(x+u*.035,y-u*.025,u*.029,u*.042,'#fff5e7',-.15);poly([[x+u*.025,y-u*.055],[x+u*.039,y-u*.09],[x+u*.047,y-u*.052]],'#e2bc73');poly([[x+u*.008,y-u*.048],[x+u*.005,y-u*.076],[x+u*.026,y-u*.06]],'#fff5e7');for(let i=0;i<3;i++)curve(x+u*.01,y-u*.057,x-u*.025,y-u*.038,x+u*.027,y-u*.01,x-u*.007,y+u*.01,['#c7a9cb','#e0a9b4','#a6c4cb'][i],u*(.012-i*.002));smile(x+u*.04,y-u*.027,u*.024,true);curve(x-u*.04,y+u*.01,x-u*.09,y-u*.025,x-u*.055,y+u*.04,x-u*.085,y+u*.03,'#c5a7ca',u*.014);ctx.restore();
   cloud(w*.5+u*.22,foot+u*.12,u*.07);smile(w*.5+u*.22,foot+u*.118,u*.048);for(let i=0;i<14;i++){const x=i%2?u*.03:w-u*.03,y=h*(.12+Math.floor(i/2)*.13);star(x,y,u*(i%3?.009:.016),['#d4b478','#bf9fbf','#98b6bf'][i%3],4);}star(w*.7,foot+u*.035,u*.021,'#e3c281');
  }
  if(style==='kids-picnic'){
   ground('#aec48e');for(let i=0;i<10;i++)flower(w*(.03+i*.105),h-u*(.015+(i%2)*.02),u*.009,i%2?'#e7b0a0':'#f3e5b3');
   const mx=w*.5;rect(mx-u*.11,foot+u*.115,u*.22,u*.07,'#f5ddbd',u*.005);for(let i=0;i<8;i++)rect(mx-u*.105+i*u*.03,foot+u*.115,u*.012,u*.07,'#d69b8166');for(let i=0;i<3;i++)rect(mx-u*.11,foot+u*(.123+i*.024),u*.22,u*.009,'#d69b8166');
   const x=w*.5-u*.14,y=foot+u*.09;actor(x,foot+u*.11,1.3);ellipse(x,y+u*.045,u*.039,u*.047,'#bf9471');bear(x,y,u*.04,'#bf9471');ellipse(x-u*.032,y+u*.046,u*.016,u*.022,'#bf9471',-.6);rect(x-u*.01,y+u*.023,u*.025,u*.03,'#d89671',u*.004);rect(x-u*.009,y+u*.026,u*.023,u*.005,'#f3ddb5');ctx.restore();
   const bx=w*.5+u*.14,by=foot+u*.095;actor(bx,foot+u*.12,1.28);ellipse(bx,by+u*.036,u*.032,u*.044,'#e5d8b7');bear(bx,by,u*.03,'#e5d8b7','rabbit');flower(bx+u*.024,by-u*.04,u*.012,'#e4b0a4');ctx.restore();
   rect(mx-u*.04,foot+u*.105,u*.08,u*.055,'#b88c5c',u*.008);ctx.strokeStyle='#8f6f4d';ctx.lineWidth=u*.004;ctx.beginPath();ctx.arc(mx,foot+u*.11,u*.029,Math.PI,0);ctx.stroke();for(let i=0;i<4;i++)line([[mx-u*.034+i*u*.021,foot+u*.11],[mx-u*.034+i*u*.021,foot+u*.155]],'#d8b781',u*.002);dot(mx+u*.07,foot+u*.14,u*.013,'#d77c6c');leaf(mx+u*.074,foot+u*.125,u*.009,.6,'#719262');
   for(const x of [u*.026,w-u*.026]){sprig(x,h*.75,u*.12,'#94ae78');butterfly(x,h*.22,u*.019);}
  }
  if(style==='kids-train'){
   rect(0,foot+u*.174,w,u*.015,'#b0bf8d');line([[0,foot+u*.185],[w,foot+u*.185]],'#8e8269',u*.003);line([[0,foot+u*.202],[w,foot+u*.202]],'#8e8269',u*.003);for(let x=0;x<w;x+=u*.025)line([[x,foot+u*.18],[x+u*.006,foot+u*.208]],'#a99474',u*.004);
   const gap=w*.23,start=w*.14;for(let i=0;i<4;i++){const x=start+i*gap,y=foot+u*.12,color=['#759fa9','#d6aa70','#bd8b9a','#9db58c'][i];rect(x-u*.09,y-u*.026,u*.18,u*.065,color,u*.009);for(const dx of [-.06,.06]){dot(x+u*dx,y+u*.048,u*.023,'#57686c');dot(x+u*dx,y+u*.048,u*.008,'#e5d5b2');}if(i<3)line([[x+u*.09,y+u*.025],[x+gap-u*.09,y+u*.025]],'#687779',u*.004);if(i===0){rect(x-u*.07,y-u*.075,u*.063,u*.065,color,u*.005);rect(x-u*.063,y-u*.065,u*.045,u*.041,'#f5e9c9',u*.003);rect(x+u*.022,y-u*.054,u*.024,u*.037,'#658f9b',u*.003);cloud(x+u*.033,y-u*.09,u*.027,'#f8f2df');smile(x+u*.038,y+u*.003,u*.027);}else if(i===2){bear(x,y-u*.04,u*.037,'#f0e2c2','rabbit',true);}else bear(x,y-u*.045,u*.043,i===1?'#c59975':'#a4bab0');}
   for(let i=0;i<5;i++)cloud(w*(.1+i*.2),u*.025,u*.025,'#faf6e6');for(const x of [u*.027,w-u*.027])for(let i=0;i<3;i++){const y=h*(.24+i*.23);rect(x-u*.004,y,u*.008,u*.05,'#a08a68');ellipse(x,y-u*.009,u*.025,u*.032,'#9db78b');}
  }
  if(style==='kids-ducks'){
   for(let i=0;i<5;i++)ellipse(w*(.06+i*.23),foot+u*.175,u*.12,u*.026,i%2?'#aacbd1':'#bed8d8');
   const duck=(x,y,s,umbrella=false)=>{ellipse(x,y+s*.5,s*.78,s*.46,'#eed087');dot(x+s*.25,y,s*.47,'#eed087');poly([[x+s*.57,y],[x+s*.96,y+s*.08],[x+s*.57,y+s*.2]],'#cf945d');smile(x+s*.28,y-s*.04,s*.39);ellipse(x-s*.16,y+s*.42,s*.36,s*.21,'#e2b76e',-.3);for(const dx of [-.25,.3])rect(x+s*dx-s*.15,y+s*.77,s*.32,s*.23,'#a77883',s*.05);if(umbrella){const ux=x-s*.65,uy=y-s*.75;line([[ux,uy],[ux,y+s*.5]],'#8a7b6e',u*.002);ctx.fillStyle='#b18eaa';ctx.beginPath();ctx.arc(ux,uy,s*1.05,Math.PI,0);ctx.closePath();ctx.fill();poly([[ux,uy-s*1.05],[ux-s*.35,uy],[ux+s*.35,uy]],'#d5b7c7');curve(ux,y+s*.5,ux,y+s*.8,ux-s*.25,y+s*.8,ux-s*.25,y+s*.57,'#8a7b6e',u*.002);}};
   duck(w*.5-u*.14,foot+u*.12,u*.063,true);duck(w*.5+u*.08,foot+u*.14,u*.043);duck(w*.5+u*.22,foot+u*.15,u*.035);
   cloud(w*.75,foot+u*.022,u*.05,'#f6f3e7');for(let i=0;i<12;i++){const x=i%2?u*.025:w-u*.025,y=h*(.1+Math.floor(i/2)*.15);line([[x+u*.004,y],[x-u*.004,y+u*.017]],'#8fb6c5',u*.003);}for(let i=0;i<4;i++){const x=w*(.48+i*.07);line([[x,foot+u*.05],[x-u*.004,foot+u*.063]],'#8fb6c5',u*.002);}
  }
  if(style==='kids-art'){
   ground('#e0c4a2');for(let i=0;i<6;i++)ellipse(w*(.05+i*.18),foot+u*(.18+(i%2)*.015),u*.045,u*.012,['#d99a93','#a7bda0','#aaa6c4','#e5bf77'][i%4]);
   const monster=(x,y,s,color,one=false)=>{ellipse(x,y,s*.7,s,color);poly([[x-s*.5,y-s*.65],[x-s*.6,y-s*1.25],[x-s*.1,y-s*.85]],'#e5bf7b');poly([[x+s*.5,y-s*.65],[x+s*.6,y-s*1.25],[x+s*.1,y-s*.85]],'#e5bf7b');for(const dx of [-.32,.32])rect(x+s*dx-s*.12,y+s*.7,s*.24,s*.4,color,s*.09);if(one){dot(x,y-s*.23,s*.29,'#fff6e3');dot(x+s*.025,y-s*.22,s*.11,ink);curve(x-s*.15,y+s*.24,x-s*.06,y+s*.39,x+s*.08,y+s*.39,x+s*.18,y+s*.2,ink,u*.002);}else smile(x,y-s*.15,s*.8,true);line([[x+s*.6,y],[x+s*1.12,y-s*.2]],color,u*.012);line([[x+s*1.08,y-s*.15],[x+s*1.28,y-s*.85]],'#9d7e63',u*.003);ellipse(x+s*1.3,y-s*.91,u*.006,u*.014,'#cd857e',.25);};
   monster(w*.5-u*.18,foot+u*.112,u*.058,'#9fb7a2',true);monster(w*.5+u*.18,foot+u*.12,u*.05,'#b5a4c3');
   const x=w*.51;line([[x-u*.035,foot+u*.18],[x,foot+u*.015],[x+u*.04,foot+u*.18]],'#b18a65',u*.007);rect(x-u*.045,foot+u*.036,u*.09,u*.105,'#f9f0d6',u*.004);circleSun(x,foot+u*.074);line([[x-u*.037,foot+u*.145],[x+u*.037,foot+u*.145]],'#a17c5d',u*.006);
   for(const xx of [u*.025,w-u*.025])for(let i=0;i<4;i++){const yy=h*(.17+i*.21);flower(xx,yy,u*.022,['#dda89a','#aac4b0','#b7abd0'][i%3]);}for(let i=0;i<4;i++)rect(w*.4+u*i*.03,foot+u*.17,u*.018,u*.024,['#d78e80','#88aaa1','#b8a0bd','#d8b473'][i],u*.003);
  }
  function circleSun(x,y){dot(x,y,u*.017,'#e8bc67');for(let i=0;i<8;i++){const a=i*Math.PI/4;line([[x+Math.cos(a)*u*.022,y+Math.sin(a)*u*.022],[x+Math.cos(a)*u*.028,y+Math.sin(a)*u*.028]],'#d3a65c',u*.0015);}curve(x-u*.035,y+u*.055,x-u*.015,y+u*.02,x+u*.02,y+u*.03,x+u*.035,y+u*.055,'#9ab593',u*.015);}
  if(style==='kids-moon'){
   for(let i=0;i<7;i++)cloud(w*(i/6),h-u*.009,u*.075,i%2?'#8b91af':'#b2b4c8');
   const x=w*.3,y=foot+u*.08;dot(x,y,u*.065,'#edd59b');dot(x+u*.032,y-u*.02,u*.058,bg);curve(x-u*.031,y-u*.003,x-u*.024,y+u*.006,x-u*.014,y+u*.006,x-u*.008,y-u*.003,ink,u*.002);ellipse(x-u*.032,y+u*.014,u*.009,u*.005,'#dca69b');star(x-u*.001,y+u*.038,u*.013,'#f7e9b5');
   const bx=w*.5+u*.16,by=foot+u*.105;actor(bx,foot+u*.11,1.3);rect(bx-u*.08,by+u*.015,u*.16,u*.065,'#a7a9c5',u*.025);rect(bx-u*.067,by-u*.005,u*.073,u*.045,'#e4dcca',u*.018);bear(bx-u*.03,by-u*.008,u*.028,'#c69f84');rect(bx-u*.055,by+u*.02,u*.125,u*.05,'#8998b4',u*.015);for(let i=0;i<4;i++)star(bx-u*.04+u*i*.03,by+u*.043,u*.007,'#d9d9c4',4);poly([[bx-u*.053,by-u*.025],[bx-u*.035,by-u*.068],[bx+u*.004,by-u*.022]],'#a99ab9');dot(bx-u*.035,by-u*.068,u*.008,'#e4dcca');ctx.restore();
   for(let i=0;i<12;i++){const xx=i%2?u*.03:w-u*.03,yy=h*(.1+Math.floor(i/2)*.16);star(xx,yy,u*(i%3?.009:.016),'#dbc798',4);}for(let i=0;i<3;i++){const xx=w*(.48+i*.055);line([[xx,foot-u*.005],[xx,foot+u*(.025+(i%2)*.02)]],'#a5afc3',u*.001);star(xx,foot+u*(.035+(i%2)*.02),u*.01,'#decaa0');}
  }
  ctx.fillStyle=['kids-space','kids-moon'].includes(style)?'#f0dfb3':'#526268';ctx.font=`600 ${u*.025}px sans-serif`;ctx.fillText(designs.find(d=>d[0]===style)?.[1]||'',w/2,u*.038,w-u*.2);
  ctx.restore();
 }
 return {designs,backgrounds,paint};
})();
