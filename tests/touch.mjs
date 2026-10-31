import assert from 'node:assert/strict';
const targets=await(await fetch('http://127.0.0.1:9223/json')).json(),target=targets.find(t=>t.url==='https://studio.local/');
const ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));let id=0;const pending=new Map();ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id);}});
async function send(method,params){const n=++id,p=new Promise(r=>pending.set(n,r));ws.send(JSON.stringify({id:n,method,params}));const m=await p;if(m.error||m.result?.exceptionDetails)throw Error(JSON.stringify(m));return m.result;}
async function evaluate(expression){return (await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true})).result.value;}
const snapshot=await evaluate('JSON.stringify(state)');
try{
 await evaluate(`(async()=>{await LayerEditor.ready;state={...defaults,photos:[{src:'/sample.svg',width:1200,height:800,zoom:1,x:0,y:0}],active:0,orientation:'portrait'};await loadPhoto(active());render();LayerEditor.create({text:'触摸测试',sizePct:12,fy:.45});})()`);
 const p=await evaluate(`(()=>{closeSheet();document.activeElement.blur();scrollTo(0,240);LayerEditor.select(LayerEditor.list()[0].id);render();const o=LayerEditor.selected(),r=$('layerSelection').getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,size:o.sizePct,angle:o.angle,photo:[active().x,active().y,active().zoom]};})()`);
 const touch=async(type,points)=>send('Input.dispatchTouchEvent',{type,touchPoints:points.map(([x,y],i)=>({x,y,id:i,radiusX:2,radiusY:2,force:1}))});
 await touch('touchStart',[[p.x-25,p.y],[p.x+25,p.y]]);
 await touch('touchMove',[[p.x-38,p.y-20],[p.x+38,p.y+20]]);
 await touch('touchEnd',[]);
 const after=await evaluate('({size:LayerEditor.selected().sizePct,angle:LayerEditor.selected().angle,photo:[active().x,active().y,active().zoom]})');
 assert(after.size>p.size*1.3,'Two fingers enlarge selected text');assert(Math.abs(after.angle-p.angle)>10,'Two fingers rotate selected text');assert.deepEqual(after.photo,p.photo,'Photo crop unchanged');
 console.log(JSON.stringify({passed:true,before:p,after},null,2));
}finally{await evaluate(`closeSheet();state=JSON.parse(${JSON.stringify(snapshot)});LayerEditor.select(null);render();save();`);ws.close();}
