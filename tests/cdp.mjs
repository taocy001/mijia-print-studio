// Talks only to this app via an explicit adb-forwarded local debug socket.
import fs from 'node:fs';
const targets=await(await fetch('http://127.0.0.1:9223/json')).json();
const target=targets.find(t=>t.url==='https://studio.local/');
if(!target)throw new Error('Studio debug page not found');
const ws=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
const source=process.argv[2]==='--eval'?process.argv[3]:fs.readFileSync(process.argv[2],'utf8');
const result=await new Promise((resolve,reject)=>{
 const timeout=setTimeout(()=>reject(Error('CDP timeout')),45000);
 ws.addEventListener('message',event=>{const value=JSON.parse(event.data);if(value.id===1){clearTimeout(timeout);resolve(value);}});
 ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:source,awaitPromise:true,returnByValue:true}}));
});
ws.close();
if(result.error||result.result.exceptionDetails){console.error(JSON.stringify(result));process.exit(1);}
console.log(JSON.stringify(result.result.result.value,null,2));
