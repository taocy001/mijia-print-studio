/* Group filtering and device capacity rules, without a browser or printer. */
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const basics=[{id:'single',name:'单张',slots:1},{id:'grid6',name:'六格',slots:6}];
const catalog=[{id:'a',names:{zh:'旧童趣'},style:'kids-test',slots:1},{id:'b',names:{zh:'旧自然'},style:'botanical',slots:1},{id:'c',names:{zh:'兔兔四格'},style:'booth',group:'purikura',slots:4}];
let limit=6;const context={console,PhotoFlow:{basics},TEMPLATE_CATALOG:catalog,BoothTemplates:{series:[['purikura','草莓兔兔']]},state:{mode:'photo',media:5012},active:()=>null,photoBatchLimit:()=>limit,$:()=>({}),window:null};context.window=context;
vm.createContext(context);vm.runInContext(fs.readFileSync(require('path').join(__dirname,'../assets/templates.js'),'utf8'),context);
const studio=context.TemplateStudio,ids=()=>Array.from(studio.browseItems(),t=>t.id);
assert.equal(studio.currentGroup(),'all');assert.equal(studio.groups().at(-1)[0],'basic');assert.deepEqual(ids().slice(-2),['single','grid6']);studio.setGroup('basic');assert.deepEqual(ids(),['single','grid6']);
for(const [group,expected] of [['kids',['a']],['nature',['b']],['purikura',['c']],['celebration',['polaroid']]]){studio.setGroup(group);assert.deepEqual(ids(),expected);assert(studio.browseItems().every(t=>t.group===group));}
studio.setGroup('missing');assert.equal(studio.currentGroup(),'celebration');
studio.setGroup('all');assert.equal(ids().length,basics.length+catalog.length+1);
context.state.media=5014;studio.setGroup('purikura');assert.equal(studio.browseItems()[0].disabled,true);limit=12;assert.equal(studio.browseItems()[0].disabled,false);
context.state.templateId='c';assert.equal(studio.selectedName(),'兔兔四格');studio.setGroup('basic');assert.equal(studio.selectedName(),'兔兔四格','group selection must not mutate chosen template');
console.log('PASS: template groups, selected-name isolation, invalid groups, phone/tablet capacities');
