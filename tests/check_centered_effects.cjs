/* Exercise the actual carousel handlers with measured card rectangles and controlled timers. */
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../assets/effect-browser.js'),'utf8');
let vertical=false,clock=0,serial=0,selected='a',calls=[],timers=new Map(),handlers={},documentHandlers={};
const track={scrollLeft:0,scrollTop:0,clientWidth:300,clientHeight:300,contains:b=>buttons.includes(b),getBoundingClientRect:()=>({left:10,top:20,width:300,height:300}),addEventListener:(type,fn)=>handlers[type]=fn,setPointerCapture(){},querySelectorAll:()=>buttons.filter(b=>!b.disabled)};
const buttons=['a','b','c','d'].map((id,i)=>({dataset:{effect:id},disabled:id==='c',getBoundingClientRect:()=>({left:10+122+i*62-track.scrollLeft,top:20+122+i*62-track.scrollTop,width:56,height:56})}));
const context={mode:'templates',sheetKind:'',document:{body:{classList:{contains:n=>n==='landscape'&&vertical}},addEventListener:(type,fn)=>documentHandlers[type]=fn},$:()=>track,choiceNodes:new Map(buttons.map(b=>['templates:'+b.dataset.effect,b])),performance:{now:()=>clock},setTimeout:fn=>{timers.set(++serial,fn);return serial;},clearTimeout:id=>timers.delete(id),choose:id=>{calls.push(id);selected=id},step:()=>{},Math};
vm.createContext(context);vm.runInContext(source.slice(source.indexOf(' const verticalStrip='),source.indexOf(' function choose(id)')),context);
function flush(){const callbacks=[...timers.values()];timers.clear();callbacks.forEach(f=>f());}
function event(id=1,type='mouse'){return {button:0,pointerId:id,pointerType:type,clientX:100,clientY:100,preventDefault(){}};}
context.centerChoice('a');assert.equal(track.scrollLeft,0);context.centerChoice('d');assert.equal(track.scrollLeft,186);
handlers.scroll();flush();assert.equal(calls.length,0,'programmatic centering must not select intermediates');
handlers.wheel();track.scrollLeft=62;handlers.scroll();flush();assert.equal(selected,'b');assert.equal(track.scrollLeft,62);
handlers.wheel();track.scrollLeft=124;handlers.scrollend();assert.equal(selected,'b','disabled centre must choose nearest enabled card');assert.equal(track.scrollLeft,62);
// A pointer held still cannot commit, even after the debounce period.
handlers.pointerdown(event());track.scrollLeft=186;handlers.scroll();flush();assert.equal(selected,'b');documentHandlers.pointerup(event());flush();assert.equal(selected,'d');
// Native touch scroll cancels PointerEvents; TouchEvents keep it held until actual release.
handlers.pointerdown(event(2,'touch'));handlers.touchstart({touches:[{}]});track.scrollLeft=0;documentHandlers.pointercancel(event(2,'touch'));handlers.scroll();flush();assert.equal(selected,'d');documentHandlers.touchend({touches:[]});flush();assert.equal(selected,'a');
// The last finger can finish outside the rail: global touch termination must unlock settling.
handlers.pointerdown(event(3,'touch'));handlers.touchstart({touches:[{}]});documentHandlers.touchstart({touches:[{},{}]});documentHandlers.pointercancel(event(3,'touch'));track.scrollLeft=186;documentHandlers.touchend({touches:[{}]});flush();assert.equal(selected,'a');documentHandlers.touchend({touches:[]});flush();assert.equal(selected,'d');
selected='a';
// Exit/cancel invalidates queued work; subsequent scroll events cannot apply anything.
handlers.wheel();track.scrollLeft=186;handlers.scroll();context.stopStrip();context.mode='';flush();assert.equal(selected,'a');
context.mode='templates';vertical=true;context.centerChoice('d');assert.equal(track.scrollTop,186);handlers.wheel();track.scrollTop=62;handlers.scrollend();assert.equal(selected,'b');
// Direct desktop dragging is supported and a resulting synthetic click is suppressed.
vertical=false;track.scrollLeft=0;handlers.pointerdown(event());handlers.pointermove({...event(),clientX:38});documentHandlers.pointerup(event());flush();assert.equal(selected,'b');assert(vm.runInContext('stripClickBlockedUntil>performance.now()',context));
console.log('PASS centre selection: first/last, disabled, mouse/touch inertia, held pointer, programmatic scroll, exit, vertical rail');
