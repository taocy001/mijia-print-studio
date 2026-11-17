/* Date annotations are independent of the device timezone. */
window.CalendarInfo=(()=>{
 const terms=new Set('小寒 大寒 立春 雨水 惊蛰 春分 清明 谷雨 立夏 小满 芒种 夏至 小暑 大暑 立秋 处暑 白露 秋分 寒露 霜降 立冬 小雪 大雪 冬至'.split(' '));
 const days='初一 初二 初三 初四 初五 初六 初七 初八 初九 初十 十一 十二 十三 十四 十五 十六 十七 十八 十九 二十 廿一 廿二 廿三 廿四 廿五 廿六 廿七 廿八 廿九 三十'.split(' ');
 const formatter=new Intl.DateTimeFormat('zh-CN-u-ca-chinese',{month:'long',day:'numeric',timeZone:'Asia/Shanghai'});
 function parts(date){return Object.fromEntries(formatter.formatToParts(date).map(p=>[p.type,p.value]));}
 function get(year,month,day){
  const key=`${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`,known=window.CALENDAR_DAYS?.[key];
  if(known){const [label,badge,off,work]=known,ordinary=/^(闰)?[正一二三四五六七八九十冬腊]+月$/.test(label)||days.includes(label);return {label,badge,off,work,solarTerm:terms.has(label),festival:!ordinary&&(!terms.has(label)||label==='清明')};}
  const date=new Date(`${key}T12:00:00+08:00`),p=parts(date),n=Number(p.day),lunar=n===1?p.month:days[n-1];
  const fixed={'1-1':'元旦','5-1':'劳动节','10-1':'国庆节'},traditional={'正月-1':'春节','正月-15':'元宵节','五月-5':'端午节','七月-7':'七夕','八月-15':'中秋节','九月-9':'重阳节','腊月-8':'腊八节'};
  const next=parts(new Date(date.getTime()+86400000));
  const festival=fixed[`${month}-${day}`]||traditional[`${p.month}-${n}`]||(next.month==='正月'&&Number(next.day)===1?'除夕':'');
  return {label:festival||lunar||'',badge:'',off:false,work:false,solarTerm:false,festival:!!festival};
 }
 return {get,holidayLastYear:2027,lunarLastYear:2035};
})();

/* Quiet seasonal line art, clipped to the title margins and unused date cells. */
window.CalendarArt=(()=>{
 const themes=[['snow','#608397'],['plum','#ab6267'],['kite','#6c9475'],['rain','#638b91'],['bloom','#8b789c'],['lotus','#5c927e'],['waves','#538d9b'],['stars','#94804d'],['osmanthus','#a48948'],['maple','#b1734d'],['ginkgo','#9b8d52'],['fir','#658879']];
 function motif(c,type){
  const line=(points)=>{c.beginPath();points.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.stroke();};
  const circle=(x,y,r,fill=false)=>{c.beginPath();c.arc(x,y,r,0,Math.PI*2);fill?c.fill():c.stroke();};
  const leaf=(x,y,r,angle=0)=>{c.save();c.translate(x,y);c.rotate(angle);c.beginPath();c.moveTo(0,0);c.quadraticCurveTo(-r*.65,-r*.65,0,-r);c.quadraticCurveTo(r*.65,-r*.65,0,0);c.fill();c.restore();};
  const flower=(x,y,r,petals=5)=>{for(let i=0;i<petals;i++){const a=i*Math.PI*2/petals;circle(x+Math.cos(a)*r*.55,y+Math.sin(a)*r*.55,r*.42,true);}circle(x,y,r*.16);};
  const snow=(x,y,r)=>{for(let i=0;i<6;i++){c.save();c.translate(x,y);c.rotate(i*Math.PI/3);line([[0,0],[0,-r]]);line([[-r*.24,-r*.57],[0,-r*.75],[r*.24,-r*.57]]);c.restore();}};
  switch(type){
   case 'snow':snow(0,0,29);snow(30,-25,9);circle(-32,20,3,true);break;
   case 'plum':line([[-33,34],[-8,11],[8,-7],[29,-31]]);flower(-9,6,12);flower(20,-23,10);flower(13,17,8);break;
   case 'kite':line([[-4,-36],[20,-12],[0,8],[-22,-15],[-4,-36],[0,8]]);line([[-22,-15],[20,-12]]);c.beginPath();c.moveTo(0,8);c.bezierCurveTo(29,22,-18,21,2,40);c.stroke();line([[2,24],[-7,19],[-6,29],[2,24],[10,18],[12,28],[2,24]]);break;
   case 'rain':c.beginPath();c.arc(0,0,30,Math.PI,Math.PI*2);c.lineTo(-30,0);c.stroke();line([[0,-30],[0,23]]);c.beginPath();c.arc(-6,23,6,0,Math.PI);c.stroke();for(const [x,y] of [[-33,-31],[30,-36],[-24,19],[25,20]])line([[x,y],[x-4,y+10]]);break;
   case 'bloom':line([[-25,35],[-8,3],[8,-28]]);for(const [x,y,r] of [[8,-25,11],[-6,-4,10],[-21,17,8]])flower(x,y,r);leaf(1,20,17,.7);leaf(-16,8,17,-.8);break;
   case 'lotus':for(const angle of [-.9,-.45,0,.45,.9]){c.save();c.rotate(angle);leaf(0,15,38);c.restore();}line([[0,13],[0,31]]);c.beginPath();c.ellipse(0,32,32,6,0,0,Math.PI*2);c.stroke();break;
   case 'waves':for(const y of [-8,8,24]){c.beginPath();c.moveTo(-38,y);c.bezierCurveTo(-14,y-19,4,y+19,38,y);c.stroke();}circle(21,-29,9);break;
   case 'stars':for(const [x,y,r] of [[-16,-18,13],[20,10,10],[-24,30,5]]){line([[x-r,y],[x,y-r],[x+r,y],[x,y+r],[x-r,y]]);}line([[20,-31],[3,-14]]);line([[32,-26],[17,-11]]);break;
   case 'osmanthus':line([[-22,35],[0,0],[23,-31]]);leaf(-7,15,25,-.85);leaf(8,-9,25,.9);for(const [x,y] of [[-13,-13],[0,-25],[19,5],[28,-9]])flower(x,y,6,4);break;
   case 'maple':c.beginPath();c.moveTo(0,26);for(const [x,y] of [[-28,12],[-21,0],[-34,-12],[-15,-10],[-18,-31],[-5,-20],[0,-40],[8,-20],[22,-30],[18,-8],[35,-12],[24,1],[29,13],[0,26]])c.lineTo(x,y);c.fill();line([[0,36],[0,-21]]);break;
   case 'ginkgo':c.beginPath();c.moveTo(0,26);c.bezierCurveTo(-17,8,-40,-9,-28,-25);c.quadraticCurveTo(-11,-39,0,-25);c.quadraticCurveTo(18,-39,31,-22);c.bezierCurveTo(41,-5,12,15,0,26);c.fill();line([[0,38],[0,-21]]);line([[0,25],[-19,-17]]);line([[0,25],[22,-16]]);break;
   case 'fir':line([[0,37],[0,-35]]);for(const y of [-25,-10,5,20]){const r=(y+45)*.47;line([[-r,y+13],[0,y],[r,y+13]]);}snow(29,-28,8);circle(-28,-8,3,true);break;
  }
 }
 function paint(ctx,month,zones){
  const [type,color]=themes[month-1]||themes[0];
  zones.forEach((z,i)=>{ctx.save();ctx.beginPath();ctx.rect(z.x,z.y,z.w,z.h);ctx.clip();ctx.translate(z.x+z.w/2,z.y+z.h/2);const scale=Math.min(z.w,z.h)/100;ctx.scale(scale,scale);ctx.rotate((i%3-1)*.12);ctx.globalAlpha=.38;ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineWidth=2.6;ctx.lineCap='round';ctx.lineJoin='round';motif(ctx,type);ctx.restore();});
 }
 return {paint,themes};
})();
