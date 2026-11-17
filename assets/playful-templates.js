/* Original vector illustrations: photo silhouettes are also the interaction masks. */
window.PlayfulTemplates=(()=>{
 const series=[['food','美食派对'],['imagination','脑洞乐园']];
 const designs=[
  ['pork','猪肘子本肘','food','ham',1,'#fff0cf','#68391f','#d87532','今日份快乐：加大份'],
  ['feast','干杯！大猪肘','food','ham',2,'#fbe4bd','#71361d','#c76936','一起大口吃快乐'],
  ['burger','人气堡堡','food','round',1,'#ffce43','#633623','#cf4933','快乐套餐 · 主角是你'],
  ['toast','吐司双胞胎','food','toast',2,'#fff5df','#70442a','#c58447','烤得刚刚好的一天'],
  ['ramen','一碗有料的你','food','bowl',1,'#f8e6dc','#ae4039','#efb558','生活热气腾腾'],
  ['pudding','焦糖布丁本人','food','pudding',1,'#e8f0d9','#76503e','#d39a49','甜度：百分之百'],
  ['rice','饭团碰个头','food','rice',2,'#e5eddf','#34534a','#d88067','今天也要好好吃饭'],
  ['melon','西瓜味的夏天','food','melon',1,'#dff1dc','#386d50','#e56e78','快乐不限量供应'],
  ['volcano','快乐大喷发','imagination','volcano',1,'#292942','#ffdfad','#f27445','今天的能量：爆表'],
  ['ufo','被快乐抓走了','imagination','ellipse',1,'#242740','#e5e4ff','#8c8dd6','地球太可爱 · 带走'],
  ['rocket','好心情发射','imagination','rocket',1,'#e2eef4','#284561','#dd6856','下一站：快乐星球'],
  ['monster','怪兽一口吞','imagination','ellipse',1,'#dfed9e','#394a35','#7d9c53','啊呜！可爱超标'],
  ['ghost','两只捣蛋鬼','imagination','ghost',2,'#e9ddf3','#534768','#af8bbd','出没注意 · 专偷快乐'],
  ['tv','今日离谱新闻','imagination','round',1,'#edbd8a','#4b393d','#ba685b','本台正在播报你的可爱'],
  ['potion','开心魔法药水','imagination','potion',1,'#e8e2f5','#594578','#aa80cd','摇一摇 · 好运就来了'],
  ['game','头号快乐玩家','imagination','round',1,'#d6e9e3','#38574c','#82aca0','今日任务：开心通关']
 ];
 const catalog=designs.map(([key,name,group,shape,slots,bg,ink,accent,caption])=>({id:'booth-fun-'+key,style:'booth-fun-'+key,version:3,key,names:{zh:name},category:series.find(s=>s[0]===group)[1],group,shape,slots,bg,ink,accent,caption}));
 function frames(w,h,e){
  const compact=typeof state!=='undefined'&&[5009,5014].includes(state.media),side=PhotoWindows.sidebar(e,w,h),u=Math.min(w,h),m=u*(compact?.025:.065),g=u*(compact?.025:.06),top=h*(side?.02:compact?.055:.14),W=w-2*m-(side?w*.18:0),H=h*(side?.96:compact?.90:.73);
  const cells=e.slots===1?[[m,top,W,H]]:w>=h?[[m,top,(W-g)/2,H],[m+(W+g)/2,top,(W-g)/2,H]]:[[m,top,W,(H-g)/2],[m,top+(H+g)/2,W,(H-g)/2]];
  return cells.map(([x,y,cw,ch],i)=>{const ratio=e.shape==='round'?1.2:e.shape==='ellipse'?1.25:e.shape==='rocket'?.8:1.05;
   const a=(e.key==='feast'?[-7,7][i]:e.key==='toast'?[-4,4][i]:e.key==='ghost'?[-5,5][i]:e.key==='pork'?-8:0)*Math.PI/180;
   // Fit the entire illustrated object, not just its photo window, between title and caption.
   const envelopes={pork:[0,-.03,1.1,1.2],feast:[0,-.03,1.1,1.2],burger:[-.10,-.22,1.1,1.14],toast:[-.02,-.10,1.02,1.03],ramen:[-.02,-.33,1.02,1.02],pudding:[-.10,-.30,1.10,1.11],rice:[-.02,-.02,1.02,1.05],melon:[-.07,-.02,1.07,1.09],volcano:[-.07,-.31,1.07,1.06],ufo:[-.18,-.23,1.18,1.03],rocket:[-.10,-.02,1.10,1.24],monster:[-.14,-.24,1.14,1.15],ghost:[-.14,-.27,1.14,1.03],tv:[-.09,-.31,1.09,1.12],potion:[-.03,-.08,1.03,1.02],game:[-.11,-.14,1.11,1.31]};
   const [l,t,r,b]=envelopes[e.key],ew=r-l,eh=b-t,c=Math.cos(a),s=Math.sin(a);let fw=Math.min(cw,ch*ratio),fh=fw/ratio;
   const k=Math.min(1,cw/(fw*ew*Math.abs(c)+fh*eh*Math.abs(s)),ch/(fh*eh*Math.abs(c)+fw*ew*Math.abs(s)))*.97;fw*=k;fh*=k;
   const dx=((l+r)/2-.5)*fw,dy=((t+b)/2-.5)*fh;
   return {x:x+cw/2-fw/2-(dx*c-dy*s),y:y+ch/2-fh/2-(dx*s+dy*c),w:fw,h:fh,shape:e.shape,angle:a};});
 }
 function available(e,w,h){return frames(w,h,e).every(f=>Math.min(f.w,f.h)*(['rice','volcano','potion','rocket','melon'].includes(e.shape)?.70:.80)>=310);}
 const ellipse=(c,x,y,rx,ry,color)=>{c.fillStyle=color;c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fill();};
 function line(c,x,y,x2,y2,color,width){c.strokeStyle=color;c.lineWidth=width;c.beginPath();c.moveTo(x,y);c.lineTo(x2,y2);c.stroke();}
 function poly(c,pts,color){c.fillStyle=color;c.beginPath();pts.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.closePath();c.fill();}
 function round(c,x,y,w,h,r,color){c.fillStyle=color;c.beginPath();c.roundRect(x,y,w,h,r);c.fill();}
 function star(c,x,y,r,color){poly(c,Array.from({length:10},(_,i)=>{const a=i*Math.PI/5-Math.PI/2,s=i%2?.43:1;return[x+Math.cos(a)*r*s,y+Math.sin(a)*r*s]}),color);}
 // Small food drawings are vectors, avoiding platform-dependent emoji artwork.
 function snack(c,x,y,s,kind,a){c.save();c.translate(x,y);c.rotate(a);c.scale(s,s);
  if(kind===0){poly(c,[[-.7,-.7],[.8,-.4],[-.1,.9]],'#f3bc54');line(c,-.7,-.7,.8,-.4,'#c8803a',.23);ellipse(c,0,0,.16,.14,'#cd6052');ellipse(c,.25,-.23,.12,.11,'#cd6052');}
  else if(kind===1){ellipse(c,0,0,.8,.57,'#fff9eb');ellipse(c,.1,0,.3,.3,'#f8c044');}
  else if(kind===2){round(c,-.6,-.5,1.2,1,.2,'#fff9e7');round(c,-.7,-.6,1.4,.45,.15,'#eb927b');round(c,-.15,-.6,.3,1.1,.03,'#426856');}
  else if(kind===3){ellipse(c,0,0,.63,.57,'#cf6054');line(c,-.25,-.55,.05,-.8,'#648658',.15);line(c,.05,-.8,.27,-.53,'#648658',.15);}
  else {round(c,-.35,-.6,.7,1.15,.3,'#d29968');for(let i=0;i<3;i++)line(c,-.25,-.4+i*.3,.1,-.24+i*.3,'#fff1c8',.1);}
  c.restore();
 }
 function surround(c,f,e){
  c.save();PhotoWindows.transform(c,f);c.translate(f.x,f.y);c.scale(f.w,f.h);c.lineJoin='round';c.lineCap='round';
  if(['pork','feast'].includes(e.key)){
   line(c,.33,.82,.19,1.08,'#fef5d8',.15);ellipse(c,.12,1.08,.10,.08,'#fff7df');ellipse(c,.26,1.12,.10,.08,'#fff7df');
   for(const [xx,yy] of [[.88,.08],[.98,.55]]){poly(c,[[xx-.05,yy],[xx+.08,yy-.08],[xx+.10,yy+.01],[xx,yy+.08]],'#6f8a47');}
  }else if(e.key==='burger'){
   ellipse(c,.5,-.03,.52,.18,'#d99b42');round(c,-.03,.94,1.06,.19,.07,'#d99b42');
   for(let i=0;i<9;i++)ellipse(c,.12+(i%5)*.17,-.12+Math.floor(i/5)*.10,.018,.009,'#fff3b0');
   for(let i=0;i<7;i++){ellipse(c,-.025,.12+i*.13,.065,.08,i%2?'#8fab49':'#d56544');ellipse(c,1.025,.12+i*.13,.065,.08,i%2?'#8fab49':'#d56544');}
   poly(c,[[-.05,.23],[.13,.35],[-.07,.44]],'#f7ce55');poly(c,[[1.04,.66],[.9,.76],[1.09,.85]],'#f7ce55');
  }else if(e.key==='toast'){
   poly(c,[[.73,0],[.87,-.08],[.99,.02],[.86,.10]],'#f5d16f');
  }else if(e.key==='ramen'){
   line(c,.15,-.12,.96,-.26,'#6f4930',.023);line(c,.15,-.06,.98,-.20,'#6f4930',.023);
   for(let i=0;i<4;i++){c.strokeStyle='#edba59';c.lineWidth=.018;c.beginPath();c.moveTo(.2+i*.16,.08);c.bezierCurveTo(.08+i*.16,-.23,.4+i*.16,-.17,.26+i*.16,-.30);c.stroke();}
   round(c,.28,.91,.44,.10,.04,e.ink);
  }else if(e.key==='pudding'){
   ellipse(c,.5,1,.59,.10,'#b7c7b1');ellipse(c,.5,-.005,.3,.065,'#a6673b');ellipse(c,.5,-.14,.07,.08,'#c95554');line(c,.52,-.19,.57,-.28,'#667a42',.015);
  }else if(e.key==='rice'){
   round(c,.35,.91,.30,.13,.02,'#426356');for(let i=0;i<4;i++)line(c,.38+i*.07,.96,.4+i*.07,1.03,'#90a383',.012);
  }else if(e.key==='melon'){
   c.strokeStyle='#639967';c.lineWidth=.10;c.beginPath();c.moveTo(-.015,.065);c.bezierCurveTo(-.01,1.37,1.01,1.37,1.015,.065);c.stroke();
  }else if(e.key==='volcano'){
   for(let i=0;i<5;i++){const xx=.30+i*.10;line(c,.5,.10,xx,-.15-Math.sin(i)*.07,'#f29956',.018);ellipse(c,xx,-.19-Math.sin(i)*.07,.027,.048,'#f59c62');}
   ellipse(c,.5,.04,.22,.07,'#fa9861');ellipse(c,.5,.02,.16,.037,'#ffdb89');
   poly(c,[[.08,.94],[-.06,.99],[.22,1.05],[.80,1.04],[1.06,.99],[.92,.92]],'#b05745');
  }else if(e.key==='ufo'){
   ellipse(c,.5,.67,.67,.31,'#8584bd');ellipse(c,.5,.69,.61,.22,'#d1ccef');
   for(let i=0;i<5;i++)ellipse(c,.02+i*.24,.83+Math.sin(i*Math.PI/4)*.06,.04,.035,'#fbdda1');
   line(c,.5,.04,.5,-.14,'#bab6ea',.018);ellipse(c,.5,-.17,.045,.045,'#f4ba96');
  }else if(e.key==='rocket'){
   poly(c,[[.15,.65],[-.09,.99],[.15,.90]],'#d56d5b');poly(c,[[.85,.65],[1.09,.99],[.85,.90]],'#d56d5b');
   poly(c,[[.24,.94],[.33,1.16],[.43,1.07],[.5,1.23],[.60,1.06],[.68,1.16],[.76,.94]],'#e6ab4a');poly(c,[[.36,.96],[.5,1.14],[.66,.96]],'#fff1a7');
  }else if(e.key==='monster'){
   ellipse(c,.5,.5,.59,.64,'#87a057');for(const xx of [.23,.76]){ellipse(c,xx,-.03,.18,.20,'#fff9d8');ellipse(c,xx,.00,.062,.087,'#3e4b38');}
   poly(c,[[.03,.13],[-.13,-.04],[.17,.00]],'#cbb875');poly(c,[[.83,0],[1.13,-.04],[.97,.13]],'#cbb875');
   for(const xx of [.2,.5,.8]){poly(c,[[xx-.06,.03],[xx+.06,.03],[xx,.18]],'#fffae5');poly(c,[[xx-.06,.97],[xx+.06,.97],[xx,.84]],'#fffae5');}
  }else if(e.key==='ghost'){
   ellipse(c,-.01,.61,.12,.1,'#fff9f0');ellipse(c,1.01,.61,.12,.1,'#fff9f0');poly(c,[[.12,.09],[.48,-.26],[.67,.07]],'#655080');round(c,.11,.03,.62,.07,.02,'#655080');
  }else if(e.key==='tv'){
   round(c,-.08,-.08,1.16,1.19,.12,'#b06b58');line(c,.44,-.08,.19,-.29,'#67545b',.025);line(c,.51,-.08,.79,-.28,'#67545b',.025);
   ellipse(c,.88,1.04,.027,.027,'#ead2b1');ellipse(c,.77,1.04,.027,.027,'#ead2b1');
  }else if(e.key==='potion'){
   round(c,.31,-.06,.38,.11,.025,'#b38a68');line(c,.29,.16,.73,.16,'#89679b',.02);star(c,.87,.76,.10,'#ffdd8d');
  }else if(e.key==='game'){
   round(c,-.10,-.13,1.2,1.43,.12,'#7fa699');round(c,.07,1.07,.22,.05,.01,'#38574c');round(c,.15,1.0,.055,.2,.01,'#38574c');ellipse(c,.8,1.10,.047,.047,'#d7877b');ellipse(c,.92,1.03,.047,.047,'#dfb275');
  }
  c.restore();
 }
 function paint(c,photos,x,y,w,h,e){
  const compact=typeof state!=='undefined'&&[5009,5014].includes(state.media),u=Math.min(w,h),fs=frames(w,h,e);c.save();c.translate(x,y);c.lineCap='round';c.lineJoin='round';c.fillStyle=e.bg;c.fillRect(0,0,w,h);
  // Peripheral illustrations remain large enough to read on paper, behind all photo windows.
  for(let i=0;i<12;i++){const xx=w*(i%2?.95:.05),yy=h*(.12+Math.floor(i/2)*.145);
   if(e.group==='food')snack(c,xx,yy,u*.04,i%5,(i%3-1)*.32);
   else {star(c,xx,yy,u*(i%3===0?.022:.012),e.accent);ellipse(c,xx+(i%2?-.04:.04)*w,yy+h*.035,u*.006,u*.006,e.ink);}}
  if(e.key==='volcano'){for(let i=0;i<6;i++)ellipse(c,w*(.2+i*.12),h*.22,u*.055,u*.03,'#575068');}
  if(e.key==='ufo'){poly(c,[[w*.43,h*.56],[w*.15,h*.86],[w*.85,h*.86],[w*.57,h*.56]],'#ffffff15');ellipse(c,w*.82,h*.20,u*.065,u*.065,'#b58c99');}
  if(e.key==='melon'){for(let i=0;i<6;i++)ellipse(c,w*(.18+i*.13),h*.87,u*.007,u*.014,'#61846a');}
  if(PhotoWindows.sidebar(e,w,h))drawTemplateSidebar(c,w,h,e);else{
  c.fillStyle=e.ink;c.textAlign='center';c.textBaseline='middle';c.font=`${u*(compact?.030:.055)}px StudioHappy,sans-serif`;c.fillText(e.names.zh,w*.5,h*(compact?.027:.072),w*.82);
  c.font=`600 ${u*(compact?.018:.022)}px sans-serif`;c.fillText(e.caption,w*.5,h*(compact?.979:.935),w*.82);
  }
  for(let i=0;i<fs.length;i++){
   const f=fs[i];surround(c,f,e);c.save();PhotoWindows.transform(c,f);c.shadowColor='#27182226';c.shadowBlur=u*.009;c.shadowOffsetY=u*.004;c.fillStyle=e.accent;c.strokeStyle=['ham','toast','pudding'].includes(e.shape)?e.accent:e.key==='monster'?'#425b36':'#fff8e8';c.lineWidth=u*.022;c.lineJoin='round';const p=PhotoWindows.trace(c,f);c.fill(p);c.stroke(p);c.restore();
   // drawPhoto owns the very same silhouette for hit testing, crop and coating.
   c.save();c.translate(-x,-y);drawPhoto(c,photos[i],x+f.x,y+f.y,f.w,f.h,'cover',{shape:f.shape,angle:f.angle});c.restore();
  }
  c.restore();
 }
 return{catalog,series,frames,available,paint};
})();
