import assert from 'node:assert/strict';
const targets=await(await fetch('http://127.0.0.1:9223/json')).json(),target=targets.find(t=>t.url==='https://studio.local/');
const ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));let id=0;const pending=new Map();ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id);}});
async function send(method,params){const n=++id,p=new Promise(r=>pending.set(n,r));ws.send(JSON.stringify({id:n,method,params}));const m=await p;if(m.error||m.result?.exceptionDetails)throw Error(JSON.stringify(m));return m.result;}
async function evaluate(expression){return (await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true})).result.value;}
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function touch(type,points){await send('Input.dispatchTouchEvent',{type,touchPoints:points.map(([x,y],i)=>({x,y,id:i,radiusX:2,radiusY:2,force:1}))});}
async function swipe(x,y,dx,dy){await touch('touchStart',[[x,y]]);for(let i=1;i<=12;i++){await pause(20);await touch('touchMove',[[x+dx*i/12,y+dy*i/12]]);}await touch('touchEnd',[]);await pause(500);}
const snapshot=await evaluate('JSON.stringify(state)');let passed=0;const check=(v,m)=>{assert(v,m);passed++;console.log(m);};
try{
 await evaluate(`(async()=>{closeSheet();state={...defaults,photos:[{src:'/sample.svg',width:1200,height:800,zoom:1,x:0,y:0,overlays:[]}],active:0,orientation:'portrait'};await loadPhoto(active());render();LayerEditor.create({kind:'emoji',text:'❤️',sizePct:2,fx:.5,fy:.4});render();scrollTo(0,0);})()`);
 let before=await evaluate('({...LayerEditor.selected()})'),r=await evaluate(`$('layerSelection').getBoundingClientRect().toJSON()`);
 await swipe(r.x+r.width/2+10,r.y+r.height/2,25,70);
 check(await evaluate(`LayerEditor.selected().fy>${before.fy}+.05&&LayerEditor.selected().sizePct===2`),'Dragging small emoji moves it without resizing');
 r=await evaluate(`$('layerResize').getBoundingClientRect().toJSON()`);await swipe(r.x+r.width/2,r.y+r.height/2,40,40);
 check(await evaluate('LayerEditor.selected().sizePct>2'),'Separate resize handle still changes emoji size');
 for(const [x,y]of [[.03,.03],[.97,.97],[.03,.97],[.97,.03]]){await evaluate(`Object.assign(LayerEditor.selected(),{fx:${x},fy:${y},sizePct:2,angle:35});render()`);check(await evaluate(`(()=>{const a=$('layerSelection').getBoundingClientRect(),b=$('layerResize').getBoundingClientRect();return a.right<=b.left||a.left>=b.right||a.bottom<=b.top||a.top>=b.bottom})()`),'No handle overlap near corner '+x+','+y);}
 const old=await evaluate('Studio.state()');check(await evaluate(`JSON.parse(Studio.printBatch('[]')).error!==undefined`),'Native bridge rejects empty batch');check(await evaluate(`JSON.parse(Studio.state()).job.token===JSON.parse(${JSON.stringify(old)}).job.token`),'Rejected batch preserves existing job');
 console.log({passed});
}finally{await evaluate(`(async()=>{closeSheet();state=JSON.parse(${JSON.stringify(snapshot)});LayerEditor.select(null);await TemplateStudio.ensureCurrent();render();save();scrollTo(0,0);})()`);ws.close();}
