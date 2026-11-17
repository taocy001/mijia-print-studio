const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../assets/app.js'),'utf8'),nodes=new Map();
const c={window:{},sheetKind:'',state:{media:5012},paperSheetSignature:'',deviceSignature:()=>'',paperOptions:()=>'',detectedPaper:()=>0,printerDetectionButton:()=>'',openHistory:()=>{c.sheetKind='history'},openDevice:()=>{c.sheetKind='device'},openSheet:kind=>{c.sheetKind=kind},$:id=>{if(!nodes.has(id))nodes.set(id,{click:()=>{c.sheetKind='menu'}});return nodes.get(id)}};
vm.createContext(c);vm.runInContext(source.slice(source.indexOf("function openPaper(){"),source.indexOf("let deviceSheetSignature=")),c);vm.runInContext(source.slice(source.indexOf("$('settingsBack').onclick="),source.indexOf('window.goBack=')),c);
for(const entry of ['menu','device']){c.sheetKind=entry;c.openPaper();assert.equal(c.sheetKind,'paper');c.openPaper();c.openPaper();nodes.get('settingsBack').onclick();assert.equal(c.sheetKind,'menu','paper always belongs to More');}
c.sheetKind='menu';c.openPaper();c.sheetKind='device';c.openPaper();nodes.get('settingsBack').onclick();assert.equal(c.sheetKind,'menu','paper must return to its sole parent');
console.log('PASS paper returns to More after refresh; sole settings parent');
