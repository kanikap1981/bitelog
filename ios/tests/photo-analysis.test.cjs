const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(require('node:path').join(__dirname,'../BiteLog/Resources/index.html'),'utf8');
const declaredIds=new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(match=>match[1]));
const referencedIds=new Set([...html.matchAll(/\$\('#([^']+)'\)/g)].map(match=>match[1]));
assert.deepEqual([...referencedIds].filter(id=>!declaredIds.has(id)).sort(),[], 'JavaScript references missing DOM elements');
// Execute the actual bundled handlers with a minimal DOM and controlled network.
const nodes={},order=[];
function $(id){return nodes[id] ||= {
 value:'',textContent:'',disabled:false,_hidden:id.endsWith('Dialog'),
 get hidden(){return this._hidden},set hidden(value){this._hidden=value;if(value)order.push('close')},
 style:{setProperty(name,value,priority){this[name]=value;this[name+'Priority']=priority},removeProperty(name){delete this[name];delete this[name+'Priority']}},
 classList:{values:new Set(),add(name){this.values.add(name)},remove(name){this.values.delete(name)},contains(name){return this.values.has(name)}},handlers:{},attributes:{},
 addEventListener(name,fn){this.handlers[name]=fn},click(){return this.handlers.click?.()},scrollIntoView(){order.push('scrollIntoView')},setAttribute(name,value){this.attributes[name]=value}
}}
class FileReader{readAsDataURL(){this.result='data:audio/mp4;base64,dGVzdA==';this.onload()}}
const context={$,URL,AbortController,TypeError,Blob,FileReader,console,setTimeout,clearTimeout,alert(){},document:{querySelector(selector){if(selector==='meta[name=\"bitelog-api-base\"]')return{content:'http://192.168.1.2:8000'};return $(selector)}},window:{scrollTo(){order.push('scroll')}},photoData:'data:image/jpeg;base64,test',photoVersion:0,analysisController:null,state:{apiBaseURL:'http://192.168.1.2:8000'},fetch:null};
vm.createContext(context);
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script); // Syntax-check the complete app too.
vm.runInContext(script.slice(script.indexOf('// Use app-controlled overlays'),script.indexOf('function openMeal')),context);
vm.runInContext(script.slice(script.indexOf('// Both old full endpoints'),script.indexOf("$('#saveMeal').addEventListener")),context);
vm.runInContext(script.slice(script.indexOf('function saveMeal'),script.indexOf("\n$('#saveMeal')")),context);
vm.runInContext(script.slice(script.indexOf('function validEmail'),script.indexOf("\n$('#saveSettings')")),context);
vm.runInContext(script.slice(script.indexOf('function deleteMeal'),script.indexOf('// Use app-controlled overlays')),context);
vm.runInContext(script.slice(script.indexOf('function blobToDataURL'),script.indexOf('async function transcribeJournalNote')),context);
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
 context.fetch=async()=>{throw new TypeError('Failed to fetch')};await click();assert.match($('#aiHint').textContent,/Check Wi-Fi/);
 context.fetch=async()=>{const e=new Error();e.name='AbortError';throw e};await click();assert.match($('#aiHint').textContent,/timed out/);
 let resolve;context.fetch=()=>new Promise(r=>resolve=r);const pending=click();assert.equal($('#saveMeal').disabled,true);context.resetAnalysis();$('#name').value='New meal';resolve(response(estimate));await pending;assert.equal($('#name').value,'New meal');
 const meals=[];context.day=()=>meals;context.persist=()=>order.push('persist');context.switchTab=tab=>order.push('tab:'+tab);context.render=()=>order.push('render');
 $('#name').value='Eggs';$('#calories').value='400';$('#protein').value='23.5';$('#type').value='Breakfast';$('#time').value='08:15';$('#mealDialog').hidden=false;$('#mealDialog').classList.add('open');order.length=0;
 context.saveMeal();
 assert.equal(JSON.stringify(meals),JSON.stringify([{name:'Eggs',calories:400,protein:23.5,type:'Breakfast',time:'08:15',photo:context.photoData}]));
 assert.equal($('#mealDialog').hidden,true);assert.equal($('#mealDialog').classList.contains('open'),false);assert.equal($('#mealDialog').style.display,'none');assert.equal($('#mealDialog').style.displayPriority,'important');assert.deepEqual(order,['persist','close','tab:today','render','scroll']);
 context.openDialog($('#mealDialog'));assert.equal($('#mealDialog').hidden,false);assert.equal($('#mealDialog').classList.contains('open'),true);assert.equal($('#mealDialog').style.display,undefined);
 context.state={targetCalories:2000,targetProtein:120,profile:{},apiBaseURL:'http://192.168.1.2:8000'};$('#athleteName').value='Alex';$('#dietitianName').value='Jordan';$('#dietitianEmail').value='jordan@example.com';$('#targetCalories').value='2500';$('#targetProtein').value='150';$('#settingsDialog').hidden=false;$('#settingsDialog').classList.add('open');order.length=0;
 context.saveSettings();
 assert.equal(JSON.stringify(context.state),JSON.stringify({targetCalories:2500,targetProtein:150,profile:{athleteName:'Alex',dietitianName:'Jordan',dietitianEmail:'jordan@example.com'},apiBaseURL:'http://192.168.1.2:8000'}));
 assert.equal($('#settingsDialog').hidden,true);assert.equal($('#settingsDialog').classList.contains('open'),false);assert.equal($('#settingsDialog').style.display,'none');assert.equal($('#settingsDialog').style.displayPriority,'important');assert.deepEqual(order,['persist','close','render']);
 context.state.apiBaseURL='http://192.168.1.2:8000';order.length=0;
 context.fetch=async(url,options)=>{assert.equal(url,'http://192.168.1.2:8000/v1/meals/analyze-voice');assert.match(JSON.parse(options.body).audio_data_url,/^data:audio\/mp4;base64,/);return response({...estimate,transcript:'I had two eggs and toast'})};
 await context.logVoiceMeal(new Blob(['test'],{type:'audio/mp4'}));
 assert.equal(meals.length,2);assert.equal(meals[1].source,'voice');assert.equal(meals[1].transcript,'I had two eggs and toast');assert.equal(meals[1].calories,400);assert.deepEqual(order,['persist','close','tab:today','render','scroll']);
 context.fetch=async()=>response({detail:'The voice note did not contain a clear meal. Nothing was saved.'},422);
 await assert.rejects(()=>context.logVoiceMeal(new Blob(['test'],{type:'audio/mp4'})),/Nothing was saved/);assert.equal(meals.length,2);
 context.state.days={'2026-09-20':[...meals]};context.persist=()=>order.push('persist');context.render=()=>order.push('render');order.length=0;
 context.deleteMeal('2026-09-20',0);assert.equal(context.state.days['2026-09-20'].length,1);assert.deepEqual(order,['persist','render']);
 context.deleteMeal('2026-09-20',0);assert.equal(context.state.days['2026-09-20'],undefined);
 context.fmt=date=>date.toISOString().slice(0,10);context.state={days:{},voiceNotes:[],targetCalories:2000,targetProtein:120,program:{},profile:{athleteName:'Alex',dietitianName:'Jordan'}};
 context.localStorage={getItem:key=>key==='bitelogHealth'?JSON.stringify({weeklyActiveCalories:3456,weeklySteps:54321,weeklyWorkoutMinutes:210}):null};
 vm.runInContext(script.slice(script.indexOf('function weeklyData()'),script.indexOf('function renderDietitian()')),context);
 const weekly=context.makeWeekly();assert.match(weekly,/Last 7 days from Apple Health/);assert.match(weekly,/Active calories: 3,456/);assert.match(weekly,/Steps: 54,321/);assert.match(weekly,/Workout minutes: 210/);
 assert.match(html,/function showWeeklyUpdate\(\)/);assert.doesNotMatch(html,/id=\"goWeekly\"/);assert.match(html,/Build my weekly update for the dietitian/);
 assert.match(html,/Last 7 days from Apple Health/);assert.match(html,/weeklySteps/);assert.match(html,/Sync movement in Today before building this update/);
 console.log('PASS: photo/voice analysis, direct meal deletion, meal/settings persistence, single weekly update wiring, app-controlled modal dismissal, and discard-on-failure; complete app syntax');
})().catch(err=>{console.error(err);process.exitCode=1});
