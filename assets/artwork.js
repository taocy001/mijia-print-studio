window.StudioArtwork=(()=>{
 const tau=Math.PI*2;
 function oval(c,x,y,rx,ry,color){c.fillStyle=color;c.beginPath();c.ellipse(x,y,rx,ry,0,0,tau);c.fill();}
 function star(c,x,y,r,color){c.fillStyle=color;c.beginPath();for(let i=0;i<10;i++){const a=i*Math.PI/5-Math.PI/2,s=i%2?r*.43:r;c.lineTo(x+Math.cos(a)*s,y+Math.sin(a)*s);}c.closePath();c.fill();}
 function flower(c,x,y,r){for(let i=0;i<6;i++)oval(c,x+Math.cos(i*tau/6)*r*.6,y+Math.sin(i*tau/6)*r*.6,r*.43,r*.43,'#dca0a7');oval(c,x,y,r*.29,r*.29,'#ecd494');}
 function rainbow(c,x,y,r){['#d38b77','#e4bb77','#a3ba9c','#8baeb7'].forEach((v,i)=>{c.strokeStyle=v;c.lineWidth=r*.15;c.beginPath();c.arc(x,y,r*(1-i*.18),Math.PI,tau);c.stroke();});}
 function label(c,w,h,id){
  c.save();c.scale(w,h);const kind=id.slice(5),bg={rainbow:'#fff7e9',space:'#253749',panda:'#eef4eb',flower:'#fff2f1',minimal:'#ffffff',unicorn:'#f3effa'}[kind];
  c.fillStyle=bg;c.fillRect(0,0,1,1);c.strokeStyle=kind==='space'?'#728799':'#c6c6b9';c.lineWidth=.003;c.strokeRect(.025,.025,.95,.95);
  const r=Math.min(w,h)/w;c.save();c.scale(r,1);const x=.5/r;
  if(kind==='rainbow')rainbow(c,x,.29,.19);
  if(kind==='space'){oval(c,x,.18,.082,.082,'#dfcfa4');oval(c,x+.035,.15,.075,.075,bg);star(c,x-.19,.16,.024,'#e6c887');star(c,x+.18,.24,.032,'#e6c887');}
  if(kind==='panda'){oval(c,x-.075,.12,.045,.045,'#324842');oval(c,x+.075,.12,.045,.045,'#324842');oval(c,x,.20,.115,.10,'#fff');oval(c,x-.043,.2,.028,.035,'#324842');oval(c,x+.043,.2,.028,.035,'#324842');oval(c,x,.25,.016,.01,'#324842');}
  if(kind==='flower'){flower(c,x,.18,.105);flower(c,x-.20,.25,.045);flower(c,x+.20,.13,.05);}
  if(kind==='unicorn'){c.fillStyle='#d7b379';c.beginPath();c.moveTo(x-.025,.12);c.lineTo(x+.02,.025);c.lineTo(x+.038,.14);c.fill();oval(c,x,.21,.075,.105,'#fff');c.strokeStyle='#b4a0c9';c.lineWidth=.019;c.beginPath();c.arc(x+.015,.19,.09,-1.4,1.4);c.stroke();oval(c,x-.025,.20,.008,.008,'#584b68');star(c,x-.17,.17,.026,'#d7b379');}
  c.restore();if(kind==='minimal'){c.strokeStyle='#283431';c.lineWidth=.008;c.beginPath();c.moveTo(.39,.19);c.lineTo(.61,.19);c.stroke();}c.restore();
 }
 function card(c,w,h,id){
  const kind=id.slice(5),palette={reading:['#faf5e9','#ad8963'],habit:['#eff5ed','#7b9c7b'],todo:['#f1f5f9','#849cb5'],schedule:['#eff6f5','#81a7a2'],luggage:['#ecf3ee','#709b87'],praise:['#fcf0ee','#ce8d8a'],invite:['#f3f0f8','#ad99c2']},[bg,ink]=palette[kind];
  c.save();c.fillStyle=bg;c.fillRect(0,0,w,h);c.strokeStyle=ink;c.lineWidth=Math.max(1,w*.0015);c.strokeRect(w*.035,h*.035,w*.93,h*.93);
  const box=(x,y,bw,bh)=>{c.beginPath();c.roundRect(x,y,bw,bh,Math.min(bw,bh)*.09);c.stroke();};
  const text=(s,x,y,size)=>{c.fillStyle=ink;c.font=`${size}px sans-serif`;c.textAlign='center';c.textBaseline='middle';c.fillText(s,x,y);};
  if(kind==='reading'||kind==='habit'){
   const cols=kind==='reading'?7:5,rows=kind==='reading'?3:2,dx=w*.84/cols,dy=h*.52/rows;
   for(let i=0;i<cols*rows;i++){const x=w*.08+(i%cols)*dx,y=h*.32+Math.floor(i/cols)*dy;box(x+dx*.07,y+dy*.07,dx*.86,dy*.86);text(String(i+1),x+dx*.5,y+dy*.5,Math.min(dx,dy)*.23);}
   text(kind==='reading'?'每天读一点，慢慢看见更大的世界':'每一次坚持，都值得记录',w*.5,h*.91,Math.min(w,h)*.023);
  }
  if(kind==='todo')for(let i=0;i<6;i++){const y=h*(.34+i*.093),r=Math.min(w,h)*.025;box(w*.1,y-r,r,r);c.beginPath();c.moveTo(w*.18,y);c.lineTo(w*.9,y);c.stroke();}
  if(kind==='schedule'){
   const x=w*.08,y=h*.30,bw=w*.84,bh=h*.59;for(let r=0;r<=7;r++){c.beginPath();c.moveTo(x,y+r*bh/7);c.lineTo(x+bw,y+r*bh/7);c.stroke();}for(let col=0;col<=6;col++){c.beginPath();c.moveTo(x+col*bw/6,y);c.lineTo(x+col*bw/6,y+bh);c.stroke();}
   ['节次','周一','周二','周三','周四','周五'].forEach((s,i)=>text(s,x+(i+.5)*bw/6,y+bh/14,Math.min(w,h)*.025));for(let i=1;i<=6;i++)text(String(i),x+bw/12,y+(i+.5)*bh/7,Math.min(w,h)*.025);
  }
  if(kind==='luggage'){text('一路有风景',w*.5,h*.22,Math.min(w,h)*.035);c.setLineDash([w*.006,w*.007]);c.beginPath();c.moveTo(w*.18,h*.80);c.bezierCurveTo(w*.3,h*.69,w*.6,h*.94,w*.82,h*.78);c.stroke();c.setLineDash([]);oval(c,w*.18,h*.8,w*.006,w*.006,ink);oval(c,w*.82,h*.78,w*.006,w*.006,ink);}
  if(kind==='praise'){const r=Math.min(w,h)*.17;star(c,w*.5,h*.53,r,'#dfb969');c.strokeStyle=ink;c.beginPath();c.moveTo(w*.23,h*.8);c.lineTo(w*.77,h*.8);c.stroke();text('送给认真成长的你',w*.5,h*.9,Math.min(w,h)*.026);}
  if(kind==='invite'){const u=Math.min(w,h);c.fillStyle='#dfbdad';c.fillRect(w*.31,h*.53,w*.38,h*.16);c.fillStyle='#c4afcf';c.fillRect(w*.35,h*.46,w*.3,h*.07);for(let i=0;i<3;i++){const x=w*(.42+.08*i);c.fillStyle=ink;c.fillRect(x-u*.004,h*.38,u*.008,h*.08);oval(c,x,h*.355,u*.008,u*.016,'#dfb969');}text('一起留下一段快乐时光',w*.5,h*.83,u*.026);}
  c.restore();
 }
 return {label,card,star,flower,rainbow};
})();
