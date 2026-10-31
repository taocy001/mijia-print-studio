/* Initial crop only; later edits always belong to the user. */
window.FaceCrop={plan(width,height,tw,th,faces){
 const bounds=(faces||[]).filter(f=>Array.isArray(f)&&f.length===4&&f.every(Number.isFinite)).map(f=>f.map(v=>Math.max(0,Math.min(1,v)))).filter(f=>f[2]>f[0]&&f[3]>f[1]).map(([l,t,r,b])=>[Math.max(0,l-(r-l)*.2),Math.max(0,t-(b-t)*.5),Math.min(1,r+(r-l)*.2),Math.min(1,b+(b-t)*.2)]);
 if(!bounds.length)return {fit:'cover',x:0,y:0};
 const l=Math.min(...bounds.map(f=>f[0])),t=Math.min(...bounds.map(f=>f[1])),r=Math.max(...bounds.map(f=>f[2])),b=Math.max(...bounds.map(f=>f[3]));
 const cw=Math.min(1,height/width*tw/th),ch=Math.min(1,width/height*th/tw);
 if(r-l>cw+1e-6||b-t>ch+1e-6)return {fit:'contain',x:0,y:0};
 const left=Math.max(Math.max(0,r-cw),Math.min((1-cw)/2,Math.min(l,1-cw))),top=Math.max(Math.max(0,b-ch),Math.min((1-ch)/2,Math.min(t,1-ch)));
 return {fit:'cover',x:1-cw>1e-9?1-2*left/(1-cw):0,y:1-ch>1e-9?1-2*top/(1-ch):0};
}};
