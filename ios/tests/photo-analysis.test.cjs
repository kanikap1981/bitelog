const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(require('node:path').join(__dirname,'../BiteLog/Resources/index.html'),'utf8');
// Execute the actual bundled handlers with a minimal DOM and controlled network.
const nodes={};
function $(id){return nodes[id] ||= {value:'',textContent:'',disabled:false,style:{},classList:{add(){},remove(){}},handlers:{},addEventListener(name,fn){this.handlers[name]=fn}}}
const context={$,URL,AbortController,TypeError,console,setTimeout,clearTimeout,photoData:'data:image/jpeg;base64,test',photoVersion:0,analysisController:null,state:{apiBaseURL:'http://192.168.1.2:8000'},fetch:null};
vm.createContext(context);
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script); // Syntax-check the complete app too.
vm.runInContext(script.slice(script.indexOf('// Both old full endpoints'),script.indexOf("$('#saveMeal').addEventListener")),context);
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
 console.log('PASS: URL migration, payload, successful estimate, malformed response, server error, network error, timeout, stale response cancellation; complete app syntax');
})().catch(err=>{console.error(err);process.exitCode=1});
