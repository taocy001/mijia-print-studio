/* Deterministic gesture state tests. Browser event/layout checks remain separate. */
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
let next=0,clock=0,timers=new Map(),draws=[],resets=0,layerHit=false;
class Element{
 constructor(){this.style={};this.hidden=false;this.handlers={};this.width=600;this.height=400;this.classList={add(){},remove(){}};}
 setAttribute(){}append(...children){this.children=children;}contains(e){return e===this;}
 getBoundingClientRect(){return {left:0,top:0,width:600,height:400};}
 getContext(){return {fillRect(){},drawImage(...args){draws.push(args);}};}
 addEventListener(k,fn){(this.handlers[k]??=[]).push(fn);}
 emit(k,data={}){const e={cancelable:true,preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;},...data};for(const f of this.handlers[k]||[]){f(e);if(e.stopped)break;}return e;}
}
const canvas=new Element(),stage=new Element(),a={src:'a'},b={src:'b'},sourceA={width:1200,height:400},sourceB={width:300,height:900};
const document=new Element();document.createElement=()=>new Element();document.body=new Element();
const window=new Element();window.EffectBrowser={active:()=>false};
const state={photos:[a,b]};
const context={window,document,state,$:id=>id==='preview'?canvas:stage,images:new Map([['a',sourceA],['b',sourceB]]),photoFrames:[{p:a,x:0,y:0,w:300,h:400},{p:b,x:300,y:0,w:300,h:400}],sheetKind:'',previewReady:()=>true,CropEditor:{toPaper:e=>({x:e.clientX,y:e.clientY}),resetGesture:()=>resets++},LayerEditor:{hit:()=>layerHit},navigator:{vibrate(){}},performance:{now:()=>clock},setTimeout:fn=>{timers.set(++next,fn);return next;},clearTimeout:id=>timers.delete(id)};
vm.runInNewContext(fs.readFileSync(require('path').join(__dirname,'../assets/original-preview.js'),'utf8'),context);
const api=window.OriginalPreview,t=(x=100,y=100,id=1)=>({clientX:x,clientY:y,identifier:id}),fire=()=>{clock+=450;const ts=[...timers.values()];timers.clear();ts.forEach(fn=>fn());};
const before=JSON.stringify(state);
canvas.emit('touchstart',{touches:[t(450)]});assert(api.pending());fire();assert(api.active());assert.equal(draws.at(-1)[0],sourceB);draws.at(-1).slice(1).forEach((n,i)=>assert(Math.abs(n-[600/2-400/3/2,0,400/3,400][i])<1e-8));
assert(canvas.emit('touchmove',{touches:[t(50)]}).stopped);assert(api.active());assert(canvas.emit('touchstart',{touches:[t(),t(200,100,2)]}).stopped);assert(api.active());
assert(canvas.emit('touchend',{touches:[t()]}).stopped);assert(api.active());assert(canvas.emit('touchend',{touches:[]}).stopped);assert(!api.active());assert.equal(JSON.stringify(state),before);
canvas.emit('touchstart',{touches:[t()]});canvas.emit('touchmove',{touches:[t(120)]});fire();assert(!api.active());assert(!api.pending());
canvas.emit('touchstart',{touches:[t()]});canvas.emit('touchstart',{touches:[t(),t(200,100,2)]});fire();assert(!api.active());
layerHit=true;canvas.emit('touchstart',{touches:[t()]});fire();assert(!api.active());layerHit=false;
canvas.emit('pointerdown',{pointerType:'mouse',button:0,pointerId:2,clientX:100,clientY:100});fire();assert(api.active());assert.equal(draws.at(-1)[0],sourceA);assert.deepEqual(draws.at(-1).slice(1),[0,100,600,200]);assert(canvas.emit('pointermove',{pointerType:'mouse',pointerId:2,clientX:400,clientY:200}).stopped);assert(api.active());assert(canvas.emit('pointerup',{pointerType:'mouse'}).stopped);assert(!api.active());
canvas.emit('touchstart',{touches:[t()]});fire();window.emit('blur');assert(!api.active());assert(stage.children[0].hidden);assert(resets>=6);assert.equal(JSON.stringify(state),before);
canvas.emit('pointerdown',{pointerType:'pen',button:0,pointerId:7,clientX:100,clientY:100});fire();assert(api.active());assert(document.emit('pointerup',{pointerType:'pen',target:stage}).stopped);assert(!api.active());
canvas.emit('pointerdown',{pointerType:'pen',button:0,pointerId:8,clientX:100,clientY:100});document.emit('pointerup',{pointerType:'pen',target:stage});fire();assert(!api.active());
console.log('PASS: full-image geometry, touched slot, held movement/multitouch, release, drag/pinch cancellation, layer exclusion, immutable state');
