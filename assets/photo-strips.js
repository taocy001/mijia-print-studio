/* Ordered photo strips; each splice half is an independent printable panel. */
window.PhotoStrips=(()=>{
 function layout(w,h,count,border=0,gap=16,split=false){
  count=Math.max(0,Math.min(6,Math.floor(count)));if(!count)return [];
  if(split){const first=Math.ceil(count/2);return [...layout(w,h/2,first,border,gap),...layout(w,h/2,count-first,border,gap).map(f=>({...f,y:f.y+h/2,index:f.index+first}))];}
  const u=Math.min(w,h),margin=Math.min(u*.2,Math.max(0,+border||0)),space=Math.min(80,Math.max(0,+gap||0)),rim=u*.025,footer=u*.07;
  const cols=count>3?2:1,rows=Math.ceil(count/cols),ph=Math.min(((w-margin*2-space*(cols-1))/cols-rim*2)*.75,(h-margin*2-rim*2-footer-space*(rows-1))/rows),pw=ph*4/3;
  const sw=pw+rim*2,sh=rows*ph+space*(rows-1)+rim*2+footer,left=(w-cols*sw-space*(cols-1))/2,top=(h-sh)/2;
  return Array.from({length:count},(_,index)=>({index,x:left+Math.floor(index/rows)*(sw+space)+rim,y:top+(index%rows)*(ph+space)+rim,w:pw,h:ph}));
 }
 function paint(ctx,w,h,photos){
  for(const frame of layout(w,h,photos.length,state.stripBorder??photos[0]?.border??state.border,state.gap,state.media===5014))drawPhoto(ctx,photos[frame.index],frame.x,frame.y,frame.w,frame.h);
 }
 return {layout,paint};
})();
