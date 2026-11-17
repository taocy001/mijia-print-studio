/* Original themed illustrations; the declared envelope includes every object decoration. */
window.EverydayTemplates=(()=>{
 const series=[['outing','出发与时光'],['tea','茶歇果园'],['school','快乐上学'],['office','上班也有趣']];
 const specs=[
  ['plate','可爱专属号牌','outing',1,'round',1.35,'#e8eee7','#234c52','#42878a',[-.08,-.09,1.08,1.24],'一路可爱 · 平安抵达'],
  ['roadtrip','我们的周末专车','outing',2,'round',1.25,'#f7e9ce','#695041','#c88756',[-.08,-.10,1.08,1.28],'快乐出发 · 两位主角'],
  ['tea','把你泡进春天','tea',1,'bowl',1.1,'#e9eddf','#50634d','#8ba581',[-.12,-.24,1.28,1.15],'温度刚好 · 心情正好'],
  ['teatime','双人下午茶','tea',2,'bowl',1.1,'#f8e7e0','#885854','#d7a398',[-.12,-.24,1.28,1.15],'今天的甜点是一起发呆'],
  ['dragonfruit','火龙果里的你','tea',1,'ellipse',.94,'#f4e3ed','#804366','#d2609b',[-.20,-.17,1.20,1.18],'一颗热带星球 · 甜度满格'],
  ['fruitduo','红心白心好朋友','tea',2,'ellipse',.94,'#e6eed8','#5d7549','#ca5e93',[-.20,-.17,1.20,1.18],'不一样的我们 · 一样甜'],
  ['ufopilot','飞碟驾驶员','imagination',1,'alien',1.1,'#282f45','#e2f1e4','#87b9ad',[-.15,-.19,1.15,1.22],'宇宙驾照 · 可爱已认证'],
  ['ufoduo','星际双人顺风车','imagination',2,'ellipse',1.05,'#e3e3f2','#53557c','#aaa4cc',[-.14,-.12,1.14,1.20],'这次一起去月亮散步'],
  ['schoolbag','今天也要背可爱','school',1,'round',.95,'#fff0cf','#72563c','#e2a75b',[-.15,-.23,1.15,1.22],'小小书包 · 大大世界'],
  ['schoolbus','快乐幼儿园专线','school',2,'round',1.18,'#dceef0','#3a6570','#e7b94d',[-.13,-.18,1.13,1.27],'下一站 · 好朋友幼儿园'],
  ['clipboard','今日工作：开心','office',1,'round',.95,'#efe6d9','#69634f','#bda77a',[-.12,-.20,1.12,1.27],'待办清单 · 认真快乐'],
  ['briefcase','快乐合伙人','office',2,'round',1.18,'#e5e8e5','#4f5d55','#8b9a85',[-.10,-.25,1.10,1.16],'一起上班 · 准时下班'],
  ['computer','可爱正在加载','office',1,'round',1.30,'#e5e8f0','#555d7c','#a5acc5',[-.09,-.16,1.09,1.28],'桌面唯一置顶 · 就是你'],
  ['windows','双窗口摸鱼现场','office',2,'round',1.25,'#e4eee7','#48735f','#8db89d',[-.07,-.19,1.07,1.09],'消息提示 · 快乐已上线'],
  ['watch','此刻值得收藏','outing',1,'ellipse',1,'#f1e7dc','#6b5344','#c79a75',[-.15,-.27,1.15,1.27],'把好时光戴在身上'],
  ['watchduo','我们的同步时刻','outing',2,'round',1,'#e4e9e8','#4e6362','#8ba7a1',[-.12,-.27,1.12,1.27],'同一时刻 · 两份快乐']
 ];
 const catalog=specs.map(([key,name,group,slots,shape,ratio,bg,ink,accent,envelope,caption])=>({id:'booth-life-'+key,style:'booth-life-'+key,version:4,key,names:{zh:name},category:series.find(s=>s[0]===group)?.[1]||'脑洞乐园',group,slots,shape,ratio,bg,ink,accent,envelope,caption}));
 function frames(w,h,e){
  const compact=typeof state!=='undefined'&&[5009,5014].includes(state.media),side=PhotoWindows.sidebar(e,w,h),u=Math.min(w,h),m=u*(compact?.025:.06),g=u*(compact?.025:.055),top=h*(side?.02:compact?.055:.14),W=w-2*m-(side?w*.18:0),H=h*(side?.96:compact?.90:.73);
  const cells=e.slots===1?[[m,top,W,H]]:w>=h?[[m,top,(W-g)/2,H],[m+(W+g)/2,top,(W-g)/2,H]]:[[m,top,W,(H-g)/2],[m,top+(H+g)/2,W,(H-g)/2]];
  return cells.map(([x,y,cw,ch],i)=>{const a=(['roadtrip','teatime','fruitduo','windows','briefcase'].includes(e.key)?[-3,3][i]:0)*Math.PI/180;
   const [l,t,r,b]=e.envelope,c=Math.cos(a),s=Math.sin(a),ew=r-l,eh=b-t;let fw=Math.min(cw,ch*e.ratio),fh=fw/e.ratio;
   const k=Math.min(1,cw/(fw*ew*Math.abs(c)+fh*eh*Math.abs(s)),ch/(fh*eh*Math.abs(c)+fw*ew*Math.abs(s)))*.97;fw*=k;fh*=k;
   const dx=((l+r)/2-.5)*fw,dy=((t+b)/2-.5)*fh;
   return {x:x+cw/2-fw/2-(dx*c-dy*s),y:y+ch/2-fh/2-(dx*s+dy*c),w:fw,h:fh,shape:e.shape,angle:a};});
 }
 function available(e,w,h){return frames(w,h,e).every(f=>Math.min(f.w,f.h)*(e.shape==='alien'?.72:.8)>=310);}
 function oval(c,x,y,rx,ry,color){c.fillStyle=color;c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fill();}
 function box(c,x,y,w,h,r,color){c.fillStyle=color;c.beginPath();c.roundRect(x,y,w,h,r);c.fill();}
 function line(c,x,y,x2,y2,color,width){c.strokeStyle=color;c.lineWidth=width;c.beginPath();c.moveTo(x,y);c.lineTo(x2,y2);c.stroke();}
 function poly(c,pts,color){c.fillStyle=color;c.beginPath();pts.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.closePath();c.fill();}
 function label(c,s,x,y,size,color){c.fillStyle=color;c.font=`600 ${size}px sans-serif`;c.textAlign='center';c.textBaseline='middle';c.fillText(s,x,y);}
 function object(c,f,e,index){c.save();PhotoWindows.transform(c,f);c.translate(f.x,f.y);c.scale(f.w,f.h);const a=e.accent,ink=e.ink;c.lineCap='round';c.lineJoin='round';
  if(e.key==='plate'||e.key==='roadtrip'){
   box(c,-.06,-.065,1.12,e.key==='plate'?1.29:1.22,.055,a);box(c,-.025,-.028,1.05,1.07,.035,'#eaf0df');
   for(const xx of [.04,.96]){oval(c,xx,-.037,.015,.017,ink);oval(c,xx,1.18,.015,.017,ink);}
   label(c,e.key==='plate'?'HAPPY · 001':index?'WEEKEND · 02':'WEEKEND · 01',.5,1.12,.072,'#fff8df');
   if(e.key==='roadtrip'){oval(c,.18,1.19,.09,.07,ink);oval(c,.82,1.19,.09,.07,ink);box(c,.15,-.08,.70,.035,.015,'#eadab7');}
  }else if(e.key==='tea'||e.key==='teatime'){
   oval(c,1.02,.39,.21,.27,a);oval(c,1.025,.37,.14,.19,e.bg);oval(c,.5,1,.60,.10,a);oval(c,.5,.98,.49,.065,'#fffaf0');
   for(let j=0;j<3;j++){c.strokeStyle=a;c.lineWidth=.018;c.beginPath();c.moveTo(.25+j*.2,-.05);c.bezierCurveTo(.1+j*.2,-.12,.4+j*.2,-.13,.3+j*.2,-.23);c.stroke();}
   line(c,.87,.05,.91,.54,'#b6a174',.009);box(c,.84,.44,.15,.17,.01,'#ede1aa');label(c,'TEA',.915,.52,.045,ink);
  }else if(e.key==='dragonfruit'||e.key==='fruitduo'){
   oval(c,.5,.5,.56,.57,a);oval(c,.5,.5,.525,.535,index?'#f5d4e7':'#fff2e9');
   for(let j=0;j<10;j++){const t=j*Math.PI/5,xx=.5+Math.cos(t)*.53,yy=.5+Math.sin(t)*.53;poly(c,[[xx-.04,yy-.02],[.5+Math.cos(t)*.68,.5+Math.sin(t)*.65],[xx+.04,yy+.02]],'#88a764');}
   for(let j=0;j<22;j++){const t=j*Math.PI/11;oval(c,.5+Math.cos(t)*.507,.5+Math.sin(t)*.507,.007,.011,'#80506e');}
  }else if(e.key==='ufopilot'||e.key==='ufoduo'){
   oval(c,.5,.83,.62,.34,a);oval(c,.5,.86,.55,.23,'#d8e9e5');
   for(let j=0;j<5;j++)oval(c,.10+j*.2,1.06,.028,.035,j%2?'#f4d17b':ink);
   if(e.key==='ufopilot'){line(c,.5,.05,.5,-.12,a,.023);oval(c,.5,-.14,.04,.04,'#f1c782');}
   else {oval(c,.5,.5,.54,.56,'#c5bbdb');box(c,.14,1.02,.72,.08,.03,a);}
  }else if(e.key==='schoolbag'){
   c.strokeStyle=a;c.lineWidth=.05;c.beginPath();c.ellipse(.5,-.06,.17,.14,0,Math.PI,2*Math.PI);c.stroke();
   box(c,-.08,-.075,1.16,1.28,.14,a);box(c,-.13,.41,.17,.43,.045,'#d28c54');box(c,.96,.41,.17,.43,.045,'#d28c54');
   box(c,.13,1.03,.74,.13,.04,'#fae4b7');line(c,.25,1.07,.76,1.07,ink,.012);oval(c,.73,1.12,.018,.025,ink);
  }else if(e.key==='schoolbus'){
   box(c,-.105,-.12,1.21,1.28,.12,a);box(c,.08,-.105,.84,.10,.03,'#f9ecc3');label(c,'HAPPY SCHOOL',.5,-.052,.055,ink);
   for(const xx of [.16,.84]){oval(c,xx,1.15,.09,.10,ink);oval(c,xx,1.15,.038,.04,'#d4dfd7');}
   oval(c,.03,1.02,.033,.04,'#fff3ba');oval(c,.97,1.02,.033,.04,'#fff3ba');label(c,index?'02':'01',.5,1.09,.055,ink);
  }else if(e.key==='clipboard'){
   box(c,-.07,-.08,1.14,1.30,.05,a);box(c,-.025,-.025,1.05,1.09,.018,'#fff9e9');
   box(c,.26,-.14,.48,.13,.03,'#858779');box(c,.40,-.185,.20,.09,.03,'#b4b8a5');
   box(c,.09,1.09,.065,.065,.007,'#fff8df');line(c,.1,1.12,.12,1.14,ink,.012);line(c,.12,1.14,.15,1.1,ink,.012);label(c,'HAVE A NICE DAY',.58,1.125,.048,ink);
  }else if(e.key==='briefcase'){
   box(c,.32,-.23,.36,.18,.035,ink);box(c,.37,-.18,.26,.15,.015,e.bg);box(c,-.075,-.07,1.15,1.19,.06,a);
   for(const xx of [.14,.82]){box(c,xx,1.01,.065,.085,.01,'#e7d4a6');}
  }else if(e.key==='computer'||e.key==='windows'){
   box(c,-.055,-.135,1.11,1.20,.055,a);box(c,-.014,-.10,1.028,.12,.015,'#e6e9ee');
   ['#cf8f86','#e5bf73','#98b9a1'].forEach((col,j)=>oval(c,.045+j*.052,-.048,.015,.020,col));label(c,e.key==='computer'?'HAPPY OS':'ONLINE',.55,-.05,.044,ink);
   if(e.key==='computer'){box(c,.39,1.0,.22,.18,.025,a);box(c,.20,1.16,.60,.065,.025,a);}
   else {line(c,.91,-.08,.95,-.03,ink,.012);line(c,.91,-.03,.95,-.08,ink,.012);}
  }else if(e.key==='watch'||e.key==='watchduo'){
   box(c,.25,-.25,.50,1.50,.075,a);box(c,1.01,.43,.09,.15,.025,ink);
   if(e.key==='watch'){oval(c,.5,.5,.565,.565,ink);oval(c,.5,.5,.535,.535,'#eedaba');
    for(let j=0;j<12;j++){const t=j*Math.PI/6;line(c,.5+Math.sin(t)*.51,.5-Math.cos(t)*.51,.5+Math.sin(t)*.54,.5-Math.cos(t)*.54,ink,.009);}
   }else {box(c,-.06,-.065,1.12,1.13,.16,ink);box(c,-.018,-.020,1.036,1.04,.10,'#e2e9db');label(c,index?'WE · 02':'WE · 01',.5,1.14,.056,ink);}
  }
  c.restore();
 }
 function motif(c,x,y,s,e,n){c.save();c.translate(x,y);c.scale(s,s);c.rotate((n%3-1)*.22);const a=e.accent;
  if(e.group==='tea'){if(n%2){oval(c,0,0,.6,.4,a);line(c,-.4,.3,.5,-.3,e.ink,.06);}else{oval(c,0,0,.55,.65,a);poly(c,[[-.3,-.45],[0,-.9],[.2,-.45]],'#94a268');}}
  else if(e.group==='school'){if(n%2){box(c,-.25,-.7,.5,1.25,.04,a);poly(c,[[-.25,.55],[0,.85],[.25,.55]],e.ink);}else{box(c,-.6,-.45,1.2,.9,.1,a);line(c,0,-.4,0,.4,e.bg,.06);}}
  else if(e.group==='office'){box(c,-.5,-.6,1,1.2,.06,a);for(let j=0;j<3;j++)line(c,-.3,-.25+j*.25,.3,-.25+j*.25,e.bg,.07);}
  else if(e.group==='outing'){if(n%2){line(c,-.5,-.5,.5,.5,a,.18);line(c,-.5,.5,.5,-.5,a,.18);}else{oval(c,0,0,.6,.6,a);oval(c,0,0,.4,.4,e.bg);line(c,0,0,0,-.3,e.ink,.06);line(c,0,0,.25,.12,e.ink,.06);}}
  else {oval(c,0,0,.7,.3,a);oval(c,0,-.22,.37,.34,a);}
  c.restore();
 }
 function paint(c,photos,x,y,w,h,e){const compact=typeof state!=='undefined'&&[5009,5014].includes(state.media),u=Math.min(w,h),fs=frames(w,h,e);c.save();c.translate(x,y);c.lineCap='round';c.lineJoin='round';c.fillStyle=e.bg;c.fillRect(0,0,w,h);
  if(e.group==='outing'){c.strokeStyle=e.accent+'28';c.lineWidth=u*.018;c.setLineDash([u*.028,u*.022]);c.beginPath();c.moveTo(w*.08,0);c.bezierCurveTo(w*.22,h*.3,-w*.05,h*.7,w*.08,h);c.stroke();c.setLineDash([]);}
  if(e.group==='school'){for(let j=0;j<4;j++){c.strokeStyle=['#e9b75f','#d59483','#8cbca3','#88abbf'][j];c.lineWidth=u*.012;c.beginPath();c.arc(w*.92,h*.07,u*(.10+j*.018),Math.PI,Math.PI*1.5);c.stroke();}}
  if(e.group==='office'){c.strokeStyle=e.accent+'20';c.lineWidth=u*.001;for(let yy=0;yy<h;yy+=u*.035){c.beginPath();c.moveTo(0,yy);c.lineTo(w,yy);c.stroke();}}
  for(let j=0;j<8;j++)motif(c,w*(j%2?.955:.045),h*(.20+Math.floor(j/2)*.20),u*.030,e,j);
  for(let i=0;i<fs.length;i++){const f=fs[i];object(c,f,e,i);c.save();PhotoWindows.transform(c,f);c.fillStyle='#fff6e7';c.strokeStyle='#fff7e9';c.lineWidth=u*.009;c.shadowColor='#30252222';c.shadowBlur=u*.006;const p=PhotoWindows.trace(c,f);c.fill(p);c.stroke(p);c.restore();
   c.save();c.translate(-x,-y);drawPhoto(c,photos[i],x+f.x,y+f.y,f.w,f.h,'cover',{shape:f.shape,angle:f.angle});c.restore();}
  // Text is painted last, outside the complete object envelope.
  if(PhotoWindows.sidebar(e,w,h))drawTemplateSidebar(c,w,h,e);else{
  c.fillStyle=e.ink;c.textAlign='center';c.textBaseline='middle';c.font=`${u*(compact?.030:.050)}px StudioHappy,sans-serif`;c.fillText(e.names.zh,w*.5,h*(compact?.027:.069),w*.82);
  c.font=`600 ${u*(compact?.018:.022)}px sans-serif`;c.fillText(e.caption,w*.5,h*(compact?.979:.935),w*.82);}c.restore();
 }
 return{catalog,series,frames,available,paint};
})();
