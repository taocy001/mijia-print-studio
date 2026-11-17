const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync(require('path').join(__dirname,'../assets/crop.js'),'utf8');
const start=source.indexOf(' function move(now,old,multi)'),end=source.indexOf(" canvas.addEventListener('touchstart'",start);
const p={x:.1,y:.2,zoom:1},context={window:{},browsing:()=>false,displayLock:null,target:{p,w:300,h:400,fit:'cover'},peek:false,snapRaw:null,snapGuide:null,state:{mode:'photo',media:5012},photoGeometry:()=>({ex:100,ey:100}),canvas:{width:600,clientWidth:600},schedule(){}};
vm.runInNewContext(source.slice(start,end),context);
context.move({x:5,y:0,n:1},{x:0,y:0,n:1},true);assert.equal(p.x,0);assert(context.snapGuide.x);
// Raw displacement survives snapping: continuing the same drag must leave the centre.
context.move({x:20,y:0,n:1},{x:5,y:0,n:1},true);assert(Math.abs(p.x+.1)<1e-8);assert.equal(context.snapGuide,null);
// Pinches stay continuous and never snap.
context.move({x:12,y:0,n:2,d:40},{x:20,y:0,n:2,d:20},true);assert(Math.abs(p.x+.02)<1e-8);assert.equal(p.zoom,2);assert.equal(context.snapGuide,null);assert.equal(context.snapRaw,null);
// Exercise the actual pointer termination handlers, including consecutive drags
// with a zoom/undo changing the photo between them.
const handlers={};context.canvas.addEventListener=(event,fn)=>handlers[event]=fn;
Object.assign(context,{start:null,previous:null,axis:null,frameDrag:null,mouse:null,gestureScale:null});
const reset=source.match(/ function resetGesture\(\)\{[^\n]+/)[0];
const ends=source.split('\n').find(line=>line.includes("for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas"));
vm.runInNewContext(reset+'\n'+ends,context);
for(const event of ['pointerup','pointercancel','lostpointercapture']){
 p.x=.1;p.y=.2;p.zoom=1;context.target={p,w:300,h:400,fit:'cover'};
 context.move({x:5,y:0,n:1},{x:0,y:0,n:1},true);assert(context.snapGuide.x);
 handlers[event]({pointerType:'mouse'});
 assert.equal(context.snapRaw,null);assert.equal(context.snapGuide,null);assert.equal(context.target,null);
 // Simulate restoring another crop with Undo, then changing its zoom.
 p.x=.4;p.zoom=2;context.target={p,w:300,h:400,fit:'cover'};
 context.move({x:10,y:0,n:1},{x:0,y:0,n:1},true);
 assert(Math.abs(p.x-.3)<1e-8,'new drag must begin at restored crop');
 handlers[event]({pointerType:'mouse'});
}
context.target={p,w:300,h:400,fit:'cover'};p.x=.1;
context.move({x:5,y:0,n:1},{x:0,y:0,n:1},true);
const raw=context.snapRaw,guide=context.snapGuide;
handlers.pointerup({pointerType:'touch'});
assert.equal(context.snapRaw,raw);assert.equal(context.snapGuide,guide);
console.log('PASS: centre snap, unsnapping, pinch, all mouse endings, drag after zoom/undo, touch termination isolation');
