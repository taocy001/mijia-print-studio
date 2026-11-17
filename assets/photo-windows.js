/* One window geometry for rendering, hit testing, crop gestures and coating. */
window.PhotoWindows=(()=>{
 const paths=new Map();let probe;
 function path(shape='rect'){
  if(paths.has(shape))return paths.get(shape);const p=new Path2D();
  if(shape==='heart'){
   p.moveTo(.5,.96);p.bezierCurveTo(.40,.84,.04,.61,.04,.30);p.bezierCurveTo(.04,.03,.36,-.04,.5,.19);p.bezierCurveTo(.64,-.04,.96,.03,.96,.30);p.bezierCurveTo(.96,.61,.60,.84,.5,.96);p.closePath();
  }else if(shape==='alien'){
   p.moveTo(.5,.99);p.bezierCurveTo(.36,.91,.03,.57,.03,.31);p.bezierCurveTo(.03,-.08,.97,-.08,.97,.31);p.bezierCurveTo(.97,.57,.64,.91,.5,.99);p.closePath();
  }else if(shape==='ham'){
   p.moveTo(.21,.08);p.bezierCurveTo(.48,-.06,.89,.03,.97,.29);p.bezierCurveTo(1.04,.56,.82,.67,.69,.75);p.bezierCurveTo(.57,.82,.56,.98,.36,.97);p.bezierCurveTo(.13,.96,-.03,.68,.04,.43);p.bezierCurveTo(.08,.27,.03,.18,.21,.08);p.closePath();
  }else if(shape==='volcano'){
   p.moveTo(.31,.06);p.quadraticCurveTo(.5,.17,.69,.06);p.lineTo(.98,.95);p.quadraticCurveTo(.5,1.02,.02,.95);p.closePath();
  }else if(shape==='toast'){
   p.moveTo(.13,.43);p.bezierCurveTo(-.10,.22,.10,.02,.29,.05);p.bezierCurveTo(.42,-.015,.58,-.015,.71,.05);p.bezierCurveTo(.90,.02,1.10,.22,.87,.43);p.lineTo(.87,.94);p.quadraticCurveTo(.5,1,.13,.94);p.closePath();
  }else if(shape==='bowl'){
   p.moveTo(.02,.12);p.quadraticCurveTo(.5,-.06,.98,.12);p.bezierCurveTo(.98,.61,.83,.98,.5,.98);p.bezierCurveTo(.17,.98,.02,.61,.02,.12);p.closePath();
  }else if(shape==='pudding'){
   p.moveTo(.2,.08);p.quadraticCurveTo(.5,-.03,.8,.08);p.lineTo(.98,.87);p.quadraticCurveTo(.5,1.09,.02,.87);p.closePath();
  }else if(shape==='rice'){
   p.moveTo(.4,.08);p.quadraticCurveTo(.5,-.05,.6,.08);p.lineTo(.95,.76);p.quadraticCurveTo(1.06,.98,.83,.98);p.lineTo(.17,.98);p.quadraticCurveTo(-.06,.98,.05,.76);p.closePath();
  }else if(shape==='melon'){
   p.moveTo(.02,.06);p.lineTo(.98,.06);p.bezierCurveTo(.97,1.27,.03,1.27,.02,.06);p.closePath();
  }else if(shape==='rocket'){
   p.moveTo(.5,.01);p.bezierCurveTo(.92,.2,.97,.59,.86,.97);p.lineTo(.14,.97);p.bezierCurveTo(.03,.59,.08,.2,.5,.01);p.closePath();
  }else if(shape==='ghost'){
   p.moveTo(.03,.96);p.lineTo(.03,.44);p.bezierCurveTo(.03,-.13,.97,-.13,.97,.44);p.lineTo(.97,.96);p.lineTo(.8,.85);p.lineTo(.65,.98);p.lineTo(.5,.85);p.lineTo(.35,.98);p.lineTo(.2,.85);p.closePath();
  }else if(shape==='potion'){
   p.moveTo(.33,.02);p.lineTo(.67,.02);p.lineTo(.67,.22);p.bezierCurveTo(1.13,.42,1.05,.97,.5,.98);p.bezierCurveTo(-.05,.97,-.13,.42,.33,.22);p.closePath();
  }else if(shape==='ellipse'){p.ellipse(.5,.5,.49,.49,0,0,Math.PI*2);}
  else if(shape==='arch'){p.moveTo(.02,.98);p.lineTo(.02,.40);p.bezierCurveTo(.02,-.10,.98,-.10,.98,.40);p.lineTo(.98,.98);p.closePath();}
  else if(shape==='comicLeft'||shape==='comicRight'){const a=shape==='comicLeft'?.07:0,b=.07-a;p.moveTo(a,.02);p.lineTo(1-b,.02);p.lineTo(1-a,.98);p.lineTo(b,.98);p.closePath();}
  else if(shape==='wave'){
   for(let side=0;side<4;side++)for(let i=0;i<=48;i++){const t=i/48,d=.022+.012*Math.cos(t*Math.PI*12);const [x,y]=side===0?[t,d]:side===1?[1-d,t]:side===2?[1-t,1-d]:[d,1-t];if(!side&&!i)p.moveTo(x,y);else p.lineTo(x,y);}p.closePath();
  }else if(shape==='round'){p.roundRect(0,0,1,1,.035);}else p.rect(0,0,1,1);
  paths.set(shape,p);return p;
 }
 function transform(ctx,f){if(f.angle){ctx.translate(f.x+f.w/2,f.y+f.h/2);ctx.rotate(f.angle);ctx.translate(-f.x-f.w/2,-f.y-f.h/2);}}
 function trace(ctx,f){const matrix=new DOMMatrix().translate(f.x,f.y).scale(f.w,f.h),p=new Path2D();p.addPath(path(f.shape),matrix);return p;}
 function clip(ctx,f){transform(ctx,f);ctx.clip(trace(ctx,f));}
 function vector(f,x,y){const a=f.angle||0,c=Math.cos(a),s=Math.sin(a);return{x:x*c+y*s,y:-x*s+y*c};}
 function local(f,p){const q=vector(f,p.x-f.x-f.w/2,p.y-f.y-f.h/2);return{x:q.x+f.x+f.w/2,y:q.y+f.y+f.h/2};}
 function point(f,p){const q=vector({angle:-(f.angle||0)},p.x-f.x-f.w/2,p.y-f.y-f.h/2);return{x:q.x+f.x+f.w/2,y:q.y+f.y+f.h/2};}
 function contains(f,p){const q=local(f,p),x=(q.x-f.x)/f.w,y=(q.y-f.y)/f.h;if(x<0||x>1||y<0||y>1)return false;if(!f.shape||f.shape==='rect')return true;probe ||=document.createElement('canvas').getContext('2d');return probe.isPointInPath(path(f.shape),x,y);}
 function find(frames,p){return [...frames].reverse().find(f=>contains(f,p));}
 function bounds(f){const a=[{x:f.x,y:f.y},{x:f.x+f.w,y:f.y},{x:f.x,y:f.y+f.h},{x:f.x+f.w,y:f.y+f.h}].map(p=>point(f,p));return {left:Math.min(...a.map(p=>p.x)),right:Math.max(...a.map(p=>p.x)),top:Math.min(...a.map(p=>p.y)),bottom:Math.max(...a.map(p=>p.y))};}
 function sidebar(e,w,h){return typeof state!=='undefined'&&[5009,5014].includes(state.media)&&w>h&&e.slots===1&&(e.version===4?e.ratio<=1.1:e.version===3&&!['round','ellipse'].includes(e.shape));}
 function mapFrame(f,m){const c=m.transformPoint({x:f.x+f.w/2,y:f.y+f.h/2});return {...f,x:c.x-f.w/2,y:c.y-f.h/2,angle:(f.angle||0)+Math.atan2(m.b,m.a)};}
 return {sidebar,mapFrame,path,trace,transform,clip,vector,local,point,contains,find,bounds};
})();
