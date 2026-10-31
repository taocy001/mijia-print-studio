import assert from 'node:assert/strict';
const targets=await(await fetch('http://127.0.0.1:9223/json')).json(),target=targets.find(t=>t.url==='https://studio.local/');
const ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.addEventListener('open',r,{once:true}));let id=0;const pending=new Map();ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){pending.get(m.id)(m);pending.delete(m.id);}});
async function send(method,params){const n=++id,p=new Promise(r=>pending.set(n,r));ws.send(JSON.stringify({id:n,method,params}));const m=await p;if(m.error||m.result?.exceptionDetails)throw Error(JSON.stringify(m));return m.result;}
async function evaluate(expression){return (await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true})).result.value;}
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function touch(type,points){await send('Input.dispatchTouchEvent',{type,touchPoints:points.map(([x,y],i)=>({x,y,id:i,radiusX:2,radiusY:2,force:1}))});}
async function swipe(x,y,dx,dy){await touch('touchStart',[[x,y]]);for(let i=1;i<=12;i++){await pause(20);await touch('touchMove',[[x+dx*i/12,y+dy*i/12]]);}await touch('touchEnd',[]);await pause(500);}
const snapshot=await evaluate('JSON.stringify(state)'),checks=[];const check=(v,label)=>{assert(v,label);checks.push(label);};
async function handlePoint(){return evaluate(`(()=>{const r=$('sheetHandle').getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};})()`);}
try{
 await evaluate(`(async()=>{closeSheet();await LayerEditor.ready;state={...defaults,photos:[{src:'/sample.svg',width:1200,height:800,zoom:1,x:0,y:0}],active:0,orientation:'portrait'};await loadPhoto(active());render();scrollTo(0,0);})()`);
 check(await evaluate(`(()=>{const a=document.querySelector('.photo-tools').getBoundingClientRect(),b=$('board').getBoundingClientRect();return a.top>=b.top&&a.bottom<=b.bottom&&a.left>b.left&&a.right<b.right;})()`),'Floating tools sit inside photo area');
 for(const button of ['layoutBtn','filterBtn','templateBtn','addTextQuick','addEmojiQuick']){
  await evaluate(`$('${button}').click()`);await pause(250);
  check(await evaluate(`$('closeSheet').textContent.trim()==='收起'&&!$('sheetBody').querySelector('[data-close]')`),button+': one consistent dismissal action');
  const aligned=await evaluate(`(()=>{const b=$('closeSheet').getBoundingClientRect(),r=document.createRange();r.selectNodeContents($('closeSheet'));const t=r.getBoundingClientRect();return Math.abs((t.left+t.right-b.left-b.right)/2)<2&&Math.abs((t.top+t.bottom-b.top-b.bottom)/2)<3;})()`);check(aligned,button+': dismissal text is centered');
  const initial=await evaluate(`$('sheet').getBoundingClientRect().height`);let p=await handlePoint();await swipe(p.x,p.y,0,-190);const full=await evaluate(`$('sheet').getBoundingClientRect().height`);check(full>initial+100,button+': drag up expands drawer');
  p=await handlePoint();await swipe(p.x,p.y,0,190);check(await evaluate(`!$('sheet').hidden&&$('sheet').getBoundingClientRect().height<${full-100}`),button+': drag down returns to half height');
  p=await handlePoint();await swipe(p.x,p.y,0,300);check(await evaluate(`$('sheet').hidden`),button+': further pull dismisses drawer');
 }
 await evaluate(`LayerEditor.openHome('emoji')`);await pause(250);let body=await evaluate(`$('sheetBody').getBoundingClientRect().toJSON()`),height=await evaluate(`$('sheet').getBoundingClientRect().height`),count=await evaluate('LayerEditor.list().length');
 await swipe(body.x+body.width/2,body.bottom-25,0,-160);check(await evaluate(`$('sheetBody').scrollTop>60&&Math.abs($('sheet').getBoundingClientRect().height-${height})<3`),'Emoji content scrolls without resizing drawer');check(await evaluate(`LayerEditor.list().length===${count}`),'Emoji swipe does not accidentally insert an item');
 await pause(1500);await evaluate(`$('sheetBody').scrollTop=0`);await pause(250);body=await evaluate(`$('sheetBody').getBoundingClientRect().toJSON()`);await swipe(body.x+4,body.top+65,0,220);check(await evaluate(`$('sheet').hidden`),'Pulling down at top of content dismisses drawer');
 await evaluate(`LayerEditor.openEditor();$('layerText').value='保留输入';$('layerText').dispatchEvent(new Event('input'));`);let p=await handlePoint();await swipe(p.x,p.y,0,-180);check(await evaluate(`$('layerText').value==='保留输入'&&LayerEditor.selected().text==='保留输入'`),'Drawer resizing preserves text input and photo layer');
 console.log(JSON.stringify({passed:checks.length,checks},null,2));
}finally{await evaluate(`(async()=>{closeSheet();state=JSON.parse(${JSON.stringify(snapshot)});LayerEditor.select(null);await TemplateStudio.ensureCurrent();render();save();scrollTo(0,0);})()`);ws.close();}
