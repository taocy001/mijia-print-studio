/* Execute the real refresh/thumbnail scheduler; changing selection must retain decoded images. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const code=fs.readFileSync(path.join(__dirname,'../assets/effect-browser.js'),'utf8');
let selected='a',renders=0,replacements=0,frameQueue=[],list=[{id:'a',name:'A',slots:1},{id:'b',name:'B',slots:2},{id:'c',name:'C',slots:1}],connected=[];
function button(){const img={dataset:{},src:''},badge={};return {dataset:{},isConnected:false,setAttribute(k,v){this[k]=v},querySelector:q=>q==='img'?img:badge};}
const track={replaceChildren(...items){replacements++;connected.forEach(b=>b.isConnected=false);connected=items;items.forEach(b=>b.isConnected=true);}};
const ui={effectChoices:track,photos:{},effectName:{},templateBtn:{setAttribute(){}},filterBtn:{setAttribute(){}}};
const p={src:'photo-A',zoom:1},state={media:5012,photos:[p],photoSelection:[],mode:'photo'};
const c={mode:'templates',draft:state,state,photo:p,window:{active:()=>state.photos[0]},document:{createElement:()=>button()},$:id=>ui[id],PhotoFlow:{multiple:()=>false},logicalSize:()=>[1200,1800],thumbnailSources:new WeakMap(),sourceSequence:0,thumbnailCache:new Map(),choiceNodes:new Map(),thumbRunKey:'',generation:0,railKey:'',lastChoice:'',stripUser:false,items:()=>list,current:()=>selected,TemplateStudio:{selectedName:()=>selected,groups:()=>[['all','全部']],currentGroup:()=> 'all',thumbnail:async id=>{renders++;return 'image:'+id+':'+state.photos[0].src+':'+state.photos[0].zoom}},mountHeading(){},heading:{},rail:{},fitRail(){},showGroups(){},stopStrip(){},centerChoice(){},requestAnimationFrame:fn=>frameQueue.push(fn),Map,WeakMap,JSON,Math,Promise,performance:{now:()=>0}};
vm.createContext(c);vm.runInContext(code.slice(code.indexOf(' function thumbnailSignature()'),code.indexOf(' const verticalStrip=')),c);
async function flush(){for(let i=0;i<50;i++){const jobs=frameQueue.splice(0);jobs.forEach(f=>f());await Promise.resolve();await Promise.resolve();}}
(async()=>{
 c.refresh(true);await flush();assert.equal(renders,3);assert.equal(replacements,1);const nodes=[...connected],images=nodes.map(b=>b.querySelector('img').src);
 selected='b';c.refresh(true);await flush();assert.equal(renders,3,'same input must not regenerate the strip');assert.equal(replacements,1,'refresh(true) cannot clear same-group DOM');assert(nodes.every((b,i)=>b===connected[i]));assert.deepEqual(connected.map(b=>b.querySelector('img').src),images);
 state.photos[0].zoom=2;c.refresh();assert.deepEqual(connected.map(b=>b.querySelector('img').src),images,'retain old image while replacement renders');await flush();assert.equal(renders,6);assert.equal(replacements,1);assert(connected.every(b=>b.querySelector('img').src.endsWith(':2')));
 list=list.slice(0,2);c.refresh(true);await flush();assert.equal(replacements,2);assert.equal(renders,6);assert.equal(connected[0],nodes[0]);
 state.photos[0].src='photo-B';c.refresh();await flush();assert.equal(renders,8);assert(connected.every(b=>b.querySelector('img').src.includes('photo-B')));
 for(let i=0;i<150;i++)c.retainThumbnail('key'+i,'value');assert.equal(c.thumbnailCache.size,108,'small thumbnail cache is bounded');
 state.photos[0].zoom=3;c.refresh();c.generation++;c.mode='';const before=renders;await flush();assert.equal(renders,before,'exit invalidates thumbnail work');
 console.log('PASS thumbnail reuse: selection/forced refresh preserve DOM and src, source/crop invalidation, group reuse, bounded cache, exit cancellation');
})().catch(e=>{console.error(e);process.exit(1)});
