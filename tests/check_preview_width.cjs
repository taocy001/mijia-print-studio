/* Execute the production preview sizing block: phone portrait must never height-fit. */
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync(require('path').join(__dirname,'../assets/crop.js'),'utf8');
const code=source.slice(source.indexOf('  const [w,h]=logicalSize()'),source.indexOf('  view={tx,ty,scale:1'));
for(const screenWidth of [320,390,430])for(const height of [480,700,844])for(const [w,h] of [[1216,1824],[1824,1216],[1040,1040]]){
 const style={width:'200px',removeProperty(k){delete this[k]}};
 const stage={clientWidth:screenWidth,style};
 const context={logicalSize:()=>[w,h],$:id=>id==='paperStage'?stage:{getBoundingClientRect:()=>({bottom:95})},displayLock:null,document:{body:{classList:{contains:()=>false}},querySelector:()=>({offsetHeight:150})},window:{},innerWidth:screenWidth,innerHeight:height,matchMedia:()=>({matches:false}),Math,canvas:{},result:null};
 vm.runInNewContext(code+'\nresult={width,pad,cw,ch,tx,ty};',context);
 assert.equal(context.result.width,screenWidth);assert.equal(context.result.pad,0);assert.equal(context.result.cw,w);assert.equal(context.result.ch,h);assert.equal(style.width,undefined);
}
console.log('PASS: 27 portrait viewport/paper cases retain full width and zero horizontal surround');
