/* Same processing order and coefficients as mijia.py apply_filter. */
window.Tone=(()=>{
 const full=new Map(),thumbs=new Map(),names=[['none','原片'],['auto','一键增强'],['bw','黑白'],['sepia','暖棕'],['cool','蓝调'],['dusk','黄昏'],['film','胶片'],['fresh','清新']];
 const clip=x=>Math.max(0,Math.min(255,Math.floor(x)));
 const gray=(r,g,b)=>(r*19595+g*38470+b*7471+32768)>>16;
 function pixels(data,key){
  if(key==='warm')key='sepia';if(key==='none')return data;
  const n=data.length/4;
  function auto(){const maps=[];for(let c=0;c<3;c++){const hist=new Uint32Array(256);for(let i=c;i<data.length;i+=4)hist[data[i]]++;let lo=0,hi=255,count=Math.floor(n*.01);while(lo<255&&count>=hist[lo])count-=hist[lo++];count=Math.floor(n*.01);while(hi>0&&count>=hist[hi])count-=hist[hi--];maps.push(Array.from({length:256},(_,v)=>hi>lo?clip((v-lo)*255/(hi-lo)):v));}for(let i=0;i<data.length;i+=4)for(let c=0;c<3;c++)data[i+c]=maps[c][data[i+c]];}
  function saturation(f){for(let i=0;i<data.length;i+=4){const g=gray(data[i],data[i+1],data[i+2]);for(let c=0;c<3;c++)data[i+c]=clip(g+f*(data[i+c]-g));}}
  function contrast(f){let sum=0;for(let i=0;i<data.length;i+=4)sum+=gray(data[i],data[i+1],data[i+2]);const mean=Math.floor(sum/n+.5);for(let i=0;i<data.length;i+=4)for(let c=0;c<3;c++)data[i+c]=clip(mean+f*(data[i+c]-mean));}
  if(key==='bw'){for(let i=0;i<data.length;i+=4)data[i]=data[i+1]=data[i+2]=gray(data[i],data[i+1],data[i+2]);auto();return data;}
  if(key==='auto'){auto();saturation(1.12);contrast(1.05);return data;}
  for(let i=0;i<data.length;i+=4){const r=data[i],g=data[i+1],b=data[i+2];
   if(key==='sepia'){data[i]=clip(.393*r+.769*g+.189*b);data[i+1]=clip(.349*r+.686*g+.168*b);data[i+2]=clip(.272*r+.534*g+.131*b);}
   if(key==='cool'){data[i]=clip(r*.92);data[i+2]=clip(b*1.08);}
   if(key==='dusk'){data[i]=clip(r*1.10);data[i+2]=clip(b*.85);}
   if(key==='film')for(let c=0;c<3;c++)data[i+c]=clip(data[i+c]*.92+18);
   if(key==='fresh')for(let c=0;c<3;c++)data[i+c]=clip(data[i+c]*1.08);
  }
  if(key==='cool')saturation(.95);if(key==='dusk')contrast(1.03);if(key==='film')saturation(.88);if(key==='fresh')saturation(.92);
  return data;
 }
 function image(source,key='none',small=false){if(key==='none'&&!small)return source;const cache=small?thumbs:full,id=source.src+'|'+key;if(cache.has(id))return cache.get(id);const c=document.createElement('canvas'),scale=small?Math.min(1,320/Math.max(source.naturalWidth,source.naturalHeight)):1;c.width=Math.round(source.naturalWidth*scale);c.height=Math.round(source.naturalHeight*scale);const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(source,0,0,c.width,c.height);const d=ctx.getImageData(0,0,c.width,c.height);pixels(d.data,key);ctx.putImageData(d,0,0);if(cache.size>=(small?16:2))cache.delete(cache.keys().next().value);cache.set(id,c);return c;}
 return {pixels,image,names};
})();
