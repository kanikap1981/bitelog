const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(require('node:path').join(__dirname,'../BiteLog/Resources/index.html'),'utf8');
// Execute the actual bundled handlers with a minimal DOM and controlled network.
const nodes={},order=[];
function $(id){return nodes[id] ||= {
 value:'',textContent:'',disabled:false,open:id.endsWith('Dialog'),
 style:{removeProperty(name){delete this[name]}},classList:{add(){},remove(){}},handlers:{},
 addEventListener(name,fn){this.handlers[name]=fn},showModal(){this.open=true},
 close(){order.push('native-close')},setAttribute(name){if(name==='open')this.open=true},
 removeAttribute(name){if(name==='open'){this.open=false;order.push('close')}}
}}
const context={$,URL,AbortController,TypeError,console,setTimeout,clearTimeout,requestAnimationFrame:fn=>fn(),alert(){},photoData:'data:image/jpeg;base64,test',photoVersion:0,analysisController:null,state:{apiBaseURL:'http://192.168.1.2:8000'},fetch:null};
vm.createContext(context);
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script); // Syntax-check the complete app too.
vm.runInContext(script.slice(script.indexOf('// Some WKWebView'),script.indexOf('function openMeal')),context);
vm.runInContext(script.slice(script.indexOf('// Both old full endpoints'),script.indexOf("$('#saveMeal').addEventListener")),context);
vm.runInContext(script.slice(script.indexOf('function saveMeal'),script.indexOf("\n$('#saveMeal')")),context);
vm.runInContext(script.slice(script.indexOf('function saveSettings'),script.indexOf("\n$('#saveSettings')")),context);
const estimate={name:'Eggs',calories:400,protein:23.5,confidence:.8,assumptions:['Two eggs']};
const response=(payload,status=200)=>({ok:status===200,status,headers:{get:()=>null},json:async()=>payload});
const click=()=>$('#estimateMeal').handlers.click();
(async()=>{
 assert.equal(context.normalizeAPIURL(' http://192.168.1.2:8000/v1/meals/analyze-inline/ '),'http://192.168.1.2:8000');
 assert.throws(()=>context.checkedAPIURL('http://localhost:8000'),/Wi-Fi/);
 assert.throws(()=>context.checkedAPIURL('https://user:secret@example.com'),/credentials/);
 context.fetch=async(url,options)=>{assert.equal(url,'http://192.168.1.2:8000/v1/meals/analyze-inline');assert.equal(JSON.parse(options.body).image_data_url,context.photoData);return response(estimate)};
 await click();assert.equal($('#name').value,'Eggs');assert.equal($('#protein').value,23.5);assert.match($('#aiHint').textContent,/Two eggs/);assert.match($('#estimateValues').textContent,/80%/);
 context.fetch=async()=>response({});await click();assert.match($('#aiHint').textContent,/invalid meal estimate/);assert.equal($('#name').value,'Eggs');
 context.fetch=async()=>response({detail:'Photo analysis timed out.'},504);await click();assert.match($('#aiHint').textContent,/timed out/);assert.equal($('#saveMeal').disabled,false);
 context.fetch=async()=>{throw new TypeError('Failed to fetch')};await click();assert.match($('#aiHint').textContent,/same Wi-Fi/);
 context.fetch=async()=>{const e=new Error();e.name='AbortError';throw e};await click();assert.match($('#aiHint').textContent,/timed out/);
 let resolve;context.fetch=()=>new Promise(r=>resolve=r);const pending=click();assert.equal($('#saveMeal').disabled,true);context.resetAnalysis();$('#name').value='New meal';resolve(response(estimate));await pending;assert.equal($('#name').value,'New meal');
 const meals=[];context.day=()=>meals;context.persist=()=>order.push('persist');context.render=()=>order.push('render');
 $('#name').value='Eggs';$('#calories').value='400';$('#protein').value='23.5';$('#type').value='Breakfast';$('#time').value='08:15';$('#mealDialog').open=true;order.length=0;
 context.saveMeal();
 assert.equal(JSON.stringify(meals),JSON.stringify([{name:'Eggs',calories:400,protein:23.5,type:'Breakfast',time:'08:15',photo:context.photoData}]));
 assert.equal($('#mealDialog').open,false);assert.deepEqual(order,['persist','render','native-close','close']);
 context.state={targetCalories:2000,targetProtein:120,apiBaseURL:''};$('#targetCalories').value='2500';$('#targetProtein').value='150';$('#apiBaseURL').value='http://192.168.1.2:8000/';$('#settingsDialog').open=true;order.length=0;
 context.saveSettings();
 assert.deepEqual(context.state,{targetCalories:2500,targetProtein:150,apiBaseURL:'http://192.168.1.2:8000'});
 assert.equal($('#settingsDialog').open,false);assert.deepEqual(order,['persist','render','native-close','close']);
 console.log('PASS: photo analysis errors, cancellation, meal/settings persistence, and WKWebView dialog dismissal; complete app syntax');
})().catch(err=>{console.error(err);process.exitCode=1});
