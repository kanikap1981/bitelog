const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(require('node:path').join(__dirname,'../BiteLog/Resources/index.html'),'utf8');
const declaredIds=new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(match=>match[1]));
const referencedIds=new Set([...html.matchAll(/\$\('#([^']+)'\)/g)].map(match=>match[1]));
assert.deepEqual([...referencedIds].filter(id=>!declaredIds.has(id)).sort(),[], 'JavaScript references missing DOM elements');
assert.match(html,/Math\.min\(1,1280\/Math\.max\(img\.width,img\.height\)\)/,'meal photos retain enough resolution for food analysis');
assert.match(html,/toDataURL\('image\/jpeg',\.84\)/,'meal photos use the expected JPEG quality');
assert.match(html,/id="inviteDialog"/,'invite access is required before onboarding');
assert.match(html,/\/v1\/invites\/redeem/,'invite codes are redeemed by the backend');
assert.match(html,/headers:apiHeaders\(\)/,'protected API requests use shared authorization headers');
assert.doesNotMatch(html,/BITE-[A-F0-9]{4}-[A-F0-9]{4}/,'reserved invite codes are never bundled in the app');
// Execute the actual bundled handlers with a minimal DOM and controlled network.
const nodes={},order=[];
function $(id){return nodes[id] ||= {
 value:'',textContent:'',disabled:false,_hidden:id.endsWith('Dialog'),
 get hidden(){return this._hidden},set hidden(value){this._hidden=value;if(value&&id.endsWith('Dialog'))order.push('close')},
 style:{setProperty(name,value,priority){this[name]=value;this[name+'Priority']=priority},removeProperty(name){delete this[name];delete this[name+'Priority']}},
 classList:{values:new Set(),add(name){this.values.add(name)},remove(name){this.values.delete(name)},contains(name){return this.values.has(name)}},handlers:{},attributes:{},
 addEventListener(name,fn){this.handlers[name]=fn},click(){return this.handlers.click?.()},scrollIntoView(){order.push('scrollIntoView')},setAttribute(name,value){this.attributes[name]=value}
}}
class FileReader{readAsDataURL(){this.result='data:audio/mp4;base64,dGVzdA==';this.onload()}}
const testAccessToken='signed-invite-token-for-bitelog-tests';
const context={$,URL,AbortController,TypeError,Blob,FileReader,console,setTimeout,clearTimeout,alert(){},today:()=> '2026-09-20',document:{querySelector(selector){if(selector==='meta[name=\"bitelog-api-base\"]')return{content:'http://192.168.1.2:8000'};return $(selector)}},window:{scrollTo(){order.push('scroll')}},photoData:'data:image/jpeg;base64,test',photoThumbnailData:'data:image/jpeg;base64,thumb',photoEstimate:null,photoVersion:0,analysisController:null,state:{apiBaseURL:'http://192.168.1.2:8000',inviteAccess:{token:testAccessToken,expiresAt:Date.now()+60000}},fetch:null};
vm.createContext(context);
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script); // Syntax-check the complete app too.
vm.runInContext(script.slice(script.indexOf('// Use app-controlled overlays'),script.indexOf('function openMeal')),context);
vm.runInContext(script.slice(script.indexOf('// Both old full endpoints'),script.indexOf("$('#saveMeal').addEventListener")),context);
vm.runInContext(script.slice(script.indexOf('function saveMeal'),script.indexOf("\n$('#saveMeal')")),context);
vm.runInContext(script.slice(script.indexOf('function validEmail'),script.indexOf("\n$('#saveSettings')")),context);
vm.runInContext(script.slice(script.indexOf('function deleteMeal'),script.indexOf('// Use app-controlled overlays')),context);
vm.runInContext(script.slice(script.indexOf('function blobToDataURL'),script.indexOf('async function transcribeJournalNote')),context);
const estimate={name:'Eggs',calories:400,carbs:34,protein:23.5,estimated_weight_grams:500,confidence:.8,assumptions:['Two eggs']};
const response=(payload,status=200)=>({ok:status===200,status,headers:{get:()=>null},json:async()=>payload});
const click=()=>$('#estimateMeal').handlers.click();
(async()=>{
 context.state.days={old:[{id:'old-meal',photo:'x'.repeat(180001)}]};assert.equal(context.compactLegacyMealPhotos('new-meal'),true);assert.equal(context.state.days.old[0].photo,'');context.state.days={};
 assert.equal(context.normalizeAPIURL(' http://192.168.1.2:8000/v1/meals/analyze-inline/ '),'http://192.168.1.2:8000');
 assert.throws(()=>context.checkedAPIURL('http://localhost:8000'),/Wi-Fi/);
 assert.throws(()=>context.checkedAPIURL('https://user:secret@example.com'),/credentials/);
 context.fetch=async(url,options)=>{assert.equal(url,'http://192.168.1.2:8000/v1/meals/analyze-inline');assert.equal(options.headers.Authorization,'Bearer '+testAccessToken);assert.equal(JSON.parse(options.body).image_data_url,context.photoData);return response(estimate)};
 await click();assert.equal($('#name').value,'Eggs');assert.equal($('#carbs').value,34);assert.equal($('#protein').value,23.5);assert.equal($('#portionField').hidden,false);assert.match($('#portionHint').textContent,/500g/);assert.match($('#aiHint').textContent,/Two eggs/);assert.match($('#estimateValues').textContent,/34g carbs/);assert.match($('#estimateValues').textContent,/80%/);
 $('#portionGrams').value='250';$('#portionGrams').handlers.input();assert.equal($('#calories').value,200);assert.equal($('#carbs').value,17);assert.equal($('#protein').value,11.8);
 context.fetch=async()=>response({});await click();assert.match($('#aiHint').textContent,/invalid meal estimate/);assert.equal($('#name').value,'Eggs');
 context.fetch=async()=>response({detail:'Photo analysis timed out.'},504);await click();assert.match($('#aiHint').textContent,/timed out/);assert.equal($('#saveMeal').disabled,false);
 context.fetch=async()=>{throw new TypeError('Failed to fetch')};await click();assert.match($('#aiHint').textContent,/Check Wi-Fi/);
 context.fetch=async()=>{const e=new Error();e.name='AbortError';throw e};await click();assert.match($('#aiHint').textContent,/timed out/);
 let resolve;context.fetch=()=>new Promise(r=>resolve=r);const pending=click();assert.equal($('#saveMeal').disabled,true);context.resetAnalysis();$('#name').value='New meal';resolve(response(estimate));await pending;assert.equal($('#name').value,'New meal');
 const meals=[];context.day=()=>meals;context.persist=()=>order.push('persist');context.storedMealExists=()=>true;context.switchTab=tab=>order.push('tab:'+tab);context.render=()=>order.push('render');context.photoEstimate=estimate;
 $('#name').value='Eggs';$('#calories').value='200';$('#carbs').value='17';$('#protein').value='11.8';$('#portionGrams').value='250';$('#type').value='Breakfast';$('#time').value='08:15';$('#mealDialog').hidden=false;$('#mealDialog').classList.add('open');order.length=0;
 context.saveMeal();
 assert.equal(meals.length,1);assert.equal(meals[0].name,'Eggs');assert.equal(meals[0].calories,200);assert.equal(meals[0].carbs,17);assert.equal(meals[0].protein,11.8);assert.equal(meals[0].portionGrams,250);assert.equal(meals[0].estimatedWeightGrams,500);assert.equal(meals[0].photo,context.photoThumbnailData);assert.match(meals[0].id,/^\d+-/);
 assert.equal($('#mealDialog').hidden,true);assert.equal($('#mealDialog').classList.contains('open'),false);assert.equal($('#mealDialog').style.display,'none');assert.equal($('#mealDialog').style.displayPriority,'important');assert.deepEqual(order,['persist','close','tab:today','render','scroll']);
 context.persist=()=>{const error=new Error('full');error.name='QuotaExceededError';throw error};$('#mealDialog').hidden=false;$('#mealDialog').classList.add('open');$('#name').value='Another meal';$('#calories').value='300';$('#portionGrams').value='';order.length=0;context.saveMeal();assert.equal(meals.length,1);assert.equal($('#mealDialog').hidden,false);assert.match($('#mealSaveStatus').textContent,/storage is full/);assert.equal($('#saveMeal').disabled,false);
 context.openDialog($('#mealDialog'));assert.equal($('#mealDialog').hidden,false);assert.equal($('#mealDialog').classList.contains('open'),true);assert.equal($('#mealDialog').style.display,undefined);
 context.persist=()=>order.push('persist');
 context.state={targetCalories:2000,targetProtein:120,profile:{},apiBaseURL:'http://192.168.1.2:8000'};$('#athleteName').value='Alex';$('#dietitianName').value='Jordan';$('#dietitianEmail').value='jordan@example.com';$('#targetCalories').value='2500';$('#targetProtein').value='150';$('#settingsDialog').hidden=false;$('#settingsDialog').classList.add('open');order.length=0;
 context.saveSettings();
 assert.equal(JSON.stringify(context.state),JSON.stringify({targetCalories:2500,targetProtein:150,profile:{athleteName:'Alex',dietitianName:'Jordan',dietitianEmail:'jordan@example.com'},apiBaseURL:'http://192.168.1.2:8000'}));
 assert.equal($('#settingsDialog').hidden,true);assert.equal($('#settingsDialog').classList.contains('open'),false);assert.equal($('#settingsDialog').style.display,'none');assert.equal($('#settingsDialog').style.displayPriority,'important');assert.deepEqual(order,['persist','close','render']);
 context.fetch=async(url,options)=>{assert.equal(url,'http://192.168.1.2:8000/v1/invites/redeem');assert.equal(JSON.parse(options.body).code,'BITE-TEST-0001');return response({access_token:testAccessToken,expires_in_seconds:432000,invite_id:'tester-01'})};$('#inviteCode').value='bite-test-0001';await context.redeemInvite();assert.equal(context.state.inviteAccess.token,testAccessToken);assert.equal(context.state.inviteAccess.inviteId,'tester-01');assert.ok(context.state.inviteAccess.expiresAt>Date.now());assert.equal($('#inviteDialog').hidden,true);
 context.state.apiBaseURL='http://192.168.1.2:8000';order.length=0;
 context.fetch=async(url,options)=>{assert.equal(url,'http://192.168.1.2:8000/v1/meals/analyze-voice');assert.match(JSON.parse(options.body).audio_data_url,/^data:audio\/mp4;base64,/);return response({...estimate,transcript:'I had two eggs and toast'})};
 await context.logVoiceMeal(new Blob(['test'],{type:'audio/mp4'}));
 assert.equal(meals.length,2);assert.equal(meals[1].source,'voice');assert.equal(meals[1].transcript,'I had two eggs and toast');assert.equal(meals[1].calories,400);assert.equal(meals[1].carbs,34);assert.deepEqual(order,['persist','close','tab:today','render','scroll']);
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
