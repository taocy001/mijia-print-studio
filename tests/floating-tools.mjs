import assert from 'node:assert/strict';
const targets=await(await fetch('http://127.0.0.1:9223/json')).json(),target=targets.find(t=>t.url==='https://studio.local/');
const ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));let id=0;const pending=new Map();ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id);}});
async function send(method,params){const n=++id,p=new Promise(r=>pending.set(n,r));ws.send(JSON.stringify({id:n,method,params}));const m=await p;if(m.error||m.result?.exceptionDetails)throw Error(JSON.stringify(m));return m.result;}
async function evaluate(expression){return (await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true})).result.value;}
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function touch(type,points){await send('Input.dispatchTouchEvent',{type,touchPoints:points.map(([x,y],i)=>({x,y,id:i,radiusX:2,radiusY:2,force:1}))});}
async function swipe(x,y,dx,dy){await touch('touchStart',[[x,y]]);for(let i=1;i<=12;i++){await pause(20);await touch('touchMove',[[x+dx*i/12,y+dy*i/12]]);}await touch('touchEnd',[]);await pause(500);}
const snapshot=await evaluate('JSON.stringify(state)'),savedPosition=await evaluate('localStorage.getItem("liuying-toolbar-position")');let passed=0;
const check=(v,label)=>{assert(v,label);passed++;console.log(label);};
const rect=selector=>evaluate(`document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect().toJSON()`);
try{
 await evaluate(`(async()=>{closeSheet();state={...defaults,photos:[{src:'/sample.svg',width:1200,height:800,zoom:1,x:0,y:0}],active:0,orientation:'portrait'};await loadPhoto(active());render();scrollTo(0,0);})()`);await pause(100);
 let r=await rect('.photo-tools'),b=await rect('#board');
 const before=await evaluate('JSON.stringify(active())');
 await swipe(r.left+85,r.top+22,20,-130);let moved=await rect('.photo-tools');
 check(moved.top<r.top-100,'Toolbar follows actual finger drag');
 check(await evaluate(`JSON.stringify(active())===${JSON.stringify(before)}`),'Drag across zoom button does not edit photo');
 check(await evaluate('!!localStorage.getItem("liuying-toolbar-position")'),'Toolbar position saved');
 r=await rect('#zoomIn');await touch('touchStart',[[r.x+r.width/2,r.y+r.height/2]]);await touch('touchEnd',[]);await pause(100);
 check(await evaluate('active().zoom>1'),'Tap still zooms after dragging');
 r=await rect('#compare');await touch('touchStart',[[r.x+r.width/2,r.y+r.height/2]]);check(await evaluate('peek'),'Hold original comparison still works');await touch('touchEnd',[]);check(await evaluate('!peek'),'Releasing comparison restores edited preview');
 r=await rect('.photo-tools');await swipe(r.left+100,r.top+22,0,-400);r=await rect('.photo-tools');b=await rect('#board');check(r.top>=b.top&&r.bottom<=b.bottom,'Toolbar clamped inside photo');
 await evaluate(`state.orientation='landscape';render()`);await pause(100);r=await rect('.photo-tools');b=await rect('#board');check(r.top>=b.top&&r.bottom<=b.bottom,'Toolbar stays reachable after aspect ratio changes');
 const p=await rect('#photos'),d=await rect('.dock');check(Math.abs(p.bottom-d.top)<2,'No empty strip below photo picker');
 console.log({passed});
}finally{
 await evaluate(`(async()=>{closeSheet();state=JSON.parse(${JSON.stringify(snapshot)});${savedPosition===null?'localStorage.removeItem("liuying-toolbar-position")':`localStorage.setItem("liuying-toolbar-position",${JSON.stringify(savedPosition)})`};await TemplateStudio.ensureCurrent();render();save();location.reload();})()`);ws.close();
}
