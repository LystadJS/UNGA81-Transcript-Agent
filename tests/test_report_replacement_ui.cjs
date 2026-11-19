/* Synthetic replacement transactions; no real sources or owner notes. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {startServer,launchBrowser}=require('./reporting_browser_fixture.cjs');
const F=require('./meeting_report_fixture.cjs'),R=require('../site/meeting-report-core.js');
let browser,server;
(async()=>{
 server=await startServer();
 browser=await launchBrowser();
 const page=await browser.newPage({acceptDownloads:true,viewport:{width:1440,height:900}}),requests=[],errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/countries.json',r=>r.fulfill({json:F.countries}));
 await page.route('https://transcripts.un.org/**',route=>{requests.push(route.request().url());const u=new URL(route.request().url()),data=u.pathname.endsWith('meetings.json')?{meetings:F.meetings,page:1,total:2,hasMore:false}:F.transcript(F.meetings.find(m=>u.pathname==='/en/'+m.slug+'.json'));return route.fulfill({json:data,headers:{'access-control-allow-origin':'*'}});});
 await page.goto(new URL('meeting-reports.html',process.argv[2]||`http://127.0.0.1:${server.address().port}/`).href);await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready.'));
 const a=await F.corpus(),b=await F.corpus(1),file=value=>({name:'synthetic.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});
 const status=prefix=>page.waitForFunction(p=>document.querySelector('#status').textContent.startsWith(p),prefix);
 const snapshot=()=>page.evaluate(()=>JSON.stringify({loaded:document.querySelector('#loadedMeetings').innerHTML,preview:document.querySelector('#reportPreview').innerHTML,notes:document.querySelector('#analystNotes').value,passages:[...document.querySelectorAll('#evidenceResults textarea')].map(e=>e.value),appendix:[...document.querySelectorAll('#evidenceResults input')].map(e=>e.checked),exports:['downloadReport','saveReport','downloadEvidence'].map(id=>document.getElementById(id).disabled)}));
 const open=value=>page.locator('#openCollection').setInputFiles(file(value));
 // Clearing a source-file selection supersedes an already checked pending file.
 const hold=async method=>{await page.evaluate(method=>{const original=UNMeetingReport[method];window.sourceFileOriginal=original;UNMeetingReport[method]=async(...args)=>{const result=await original(...args);await new Promise((resolve,reject)=>window.sourceFileGate={resolve,reject});return result;};},method);};
 const release=async(method,failure=false)=>{await page.evaluate(async({method,failure})=>{UNMeetingReport[method]=window.sourceFileOriginal;const gate=window.sourceFileGate;delete window.sourceFileGate;if(failure)gate.reject(Error('Synthetic obsolete validation failure'));else gate.resolve();await new Promise(resolve=>setTimeout(resolve,0));},{method,failure});};
 const empty=await snapshot();await hold('openSaved');await open(a);await page.waitForFunction(()=>!!window.sourceFileGate);await page.locator('#openCollection').setInputFiles([]);await release('openSaved');assert.equal(await snapshot(),empty,'Cleared selection must prevent the older source file from opening');await status('No source file selected');
 await open(a);await status('Saved sources verified');
 await page.locator('#analystNotes').fill('Unsaved synthetic assessment');await page.locator('#evidenceResults .passage-note-editor summary').first().click();await page.locator('#evidenceResults textarea').first().fill('Unsaved passage note');await page.locator('#evidenceResults input').first().check();await page.locator('#prepareReport').click();
 const original=await snapshot();await hold('appendSaved');await page.locator('#addCollection').setInputFiles(file(b));await page.waitForFunction(()=>!!window.sourceFileGate);await page.locator('#addCollection').setInputFiles([]);await release('appendSaved');assert.equal(await snapshot(),original,'Cleared addition must preserve sources, notes and prepared exports');await status('No source file selected');
 const bad=structuredClone(b);bad.records[0].text='Tampered';
 await open(bad);await status('Could not open file:');assert.equal(await page.locator('#replaceReport').evaluate(e=>e.open),false);assert.equal(await snapshot(),original);
 await page.locator('#openCollection').focus();await open(b);await page.locator('#replaceReport[open]').waitFor();assert.equal(await page.locator('#keepCurrentReport').evaluate(e=>e===document.activeElement),true);
 for(const width of [390,1440]){await page.setViewportSize({width,height:900});assert(await page.locator('#replaceReport').evaluate(e=>e.scrollWidth<=e.clientWidth+2&&e.getBoundingClientRect().width<=innerWidth));}
 await page.keyboard.press('Escape');await status('Current report kept');assert.equal(await page.locator('#openCollection').evaluate(e=>e===document.activeElement),true);assert.equal(await snapshot(),original);
 await open(b);await page.locator('#replaceReport[open]').waitFor();await page.locator('#keepCurrentReport').click();await status('Current report kept');assert.equal(await snapshot(),original);assert.equal(requests.length,0);
 const [keptCSV]=await Promise.all([page.waitForEvent('download'),page.locator('#downloadEvidence').click()]);assert.equal(fs.readFileSync(await keptCSV.path(),'utf8'),R.evidenceCSV(a.records));
 await open(b);await page.locator('#replaceCurrentReport').click();await status('Saved sources verified');assert.equal(await page.locator('#analystNotes').inputValue(),'');assert.equal(await page.locator('#evidenceResults textarea').first().inputValue(),'');assert.equal(await page.locator('#evidenceResults input:checked').count(),0);assert.equal(await page.locator('#downloadReport').isDisabled(),true);assert.equal(await page.locator('#loadedMeetings input').first().inputValue(),F.meetings[1].slug);
 await page.locator('#analystNotes').fill('Keep during loading');await page.locator('#prepareReport').click();
 await page.locator('#meetingDate').fill(F.date);await page.locator('#findMeetings').click();await page.waitForFunction(()=>document.querySelectorAll('#inventory input').length===2);for(const checkbox of await page.locator('#inventory input').all())await checkbox.check();
 const beforeLoad=await snapshot(),beforeRequests=requests.length;await page.locator('#loadMeetings').click();await page.locator('#keepCurrentReport').click();await status('Current report kept');assert.equal(requests.length,beforeRequests);assert.equal(await snapshot(),beforeLoad);
 // Gate the second valid bundle, allowing an explicit cancellation after the first completed.
 await page.evaluate(()=>{const original=UNCollector.collect;window.testOriginalCollect=original;UNCollector.collect=async(...args)=>{const result=await original(...args);if(args[0].meeting_slug.startsWith('sc/'))await new Promise(resolve=>window.testReleaseCollect=resolve);return result;};});
 await page.locator('#loadMeetings').click();await page.locator('#replaceCurrentReport').click();await page.waitForFunction(()=>typeof window.testReleaseCollect==='function');await page.locator('#cancelLoad').click();await page.evaluate(()=>{window.testReleaseCollect();delete window.testReleaseCollect;});await status('Loading cancelled');assert.equal(await snapshot(),beforeLoad);
 // Editing the current report while retrieval is pending invalidates its replacement ticket.
 await page.locator('#loadMeetings').click();await page.locator('#replaceCurrentReport').click();await page.waitForFunction(()=>typeof window.testReleaseCollect==='function');await page.locator('#analystNotes').fill('Newer edit during retrieval');await page.locator('#prepareReport').click();const edited=await snapshot();await page.evaluate(()=>{window.testReleaseCollect();delete window.testReleaseCollect;});await status('Your report changed');assert.equal(await snapshot(),edited);
 // A partial replacement requires a separate decision even after initial approval.
 await page.evaluate(()=>{UNCollector.collect=async(...args)=>{if(args[0].meeting_slug.startsWith('sc/'))throw Error('Synthetic collection failure');return window.testOriginalCollect(...args);};});
 await page.locator('#loadMeetings').click();await page.locator('#replaceCurrentReport').click();await page.waitForFunction(()=>document.querySelector('#replaceReport').open&&document.querySelector('#replaceReportMessage').textContent.includes('retrieval is incomplete'));await page.locator('#keepCurrentReport').click();await status('Current report kept');assert.equal(await snapshot(),edited);
 // Incomplete coverage also prompts when the collector returns successfully.
 await page.evaluate(()=>{UNCollector.collect=async(...args)=>{const c=await window.testOriginalCollect(...args);c.collection.partial=true;return c;};});await page.locator('#loadMeetings').click();await page.locator('#replaceCurrentReport').click();await page.waitForFunction(()=>document.querySelector('#replaceReport').open&&document.querySelector('#replaceReportMessage').textContent.includes('retrieval is incomplete'));await page.locator('#keepCurrentReport').click();await status('Current report kept');assert.equal(await snapshot(),edited);
 await page.evaluate(()=>{UNCollector.collect=async(...args)=>{if(args[0].meeting_slug.startsWith('sc/'))throw Error('Synthetic collection failure');return window.testOriginalCollect(...args);};});await page.locator('#loadMeetings').click();await page.locator('#replaceCurrentReport').click();await page.waitForFunction(()=>document.querySelector('#replaceReport').open&&document.querySelector('#replaceReportMessage').textContent.includes('retrieval is incomplete'));await page.locator('#replaceCurrentReport').click();await status('Synthetic collection failure');assert.equal(await page.locator('#loadedMeetings input').count(),1);assert.equal(await page.locator('#loadedMeetings input').first().inputValue(),F.meetings[0].slug);assert.equal(await page.locator('#analystNotes').inputValue(),'');assert.equal(await page.locator('#downloadReport').isDisabled(),true);
 // A fully failed collection must retain the prepared workspace without another decision.
 await page.locator('#analystNotes').fill('Keep on complete failure');await page.locator('#prepareReport').click();const failureBefore=await snapshot();await page.evaluate(()=>{UNCollector.collect=async()=>{throw Error('Synthetic total failure');};});await page.locator('#loadMeetings').click();await page.locator('#replaceCurrentReport').click();await status('Synthetic total failure');assert.equal(await snapshot(),failureBefore);
 await page.evaluate(()=>{UNCollector.collect=async(...args)=>{if(args[0].meeting_slug.startsWith('sc/'))throw new DOMException('Synthetic abort','AbortError');return window.testOriginalCollect(...args);};});await page.locator('#loadMeetings').click();await page.locator('#replaceCurrentReport').click();await status('Loading cancelled');assert.equal(await snapshot(),failureBefore);
 // Slow validation cannot overwrite edits made while it was pending.
 await page.evaluate(()=>{const original=UNMeetingReport.openSaved;window.testOriginalOpen=original;UNMeetingReport.openSaved=async(...args)=>{const result=await original(...args);await new Promise(resolve=>window.testReleaseOpen=resolve);return result;};});
 await open(b);await page.waitForFunction(()=>typeof window.testReleaseOpen==='function');await page.locator('#analystNotes').fill('Newer edit during validation');await page.locator('#prepareReport').click();const validationBefore=await snapshot();await page.evaluate(()=>{window.testReleaseOpen();delete window.testReleaseOpen;});await status('Your report changed');assert.equal(await snapshot(),validationBefore);assert.equal(await page.locator('#replaceReport').evaluate(e=>e.open),false);
 // When two imports complete out of order, only the newest request can apply.
 await open(b);await page.waitForFunction(()=>typeof window.testReleaseOpen==='function');await page.evaluate(()=>{UNMeetingReport.openSaved=window.testOriginalOpen;});
 const newer=R.savedReport(R.build([a],[F.meetings[0].slug],{title:'Newest synthetic report',notes:'Imported source-bound assessment'}),[a]);await open(newer);await page.locator('#replaceCurrentReport').click();await status('Saved sources verified');await page.locator('#prepareReport').click();const newest=await snapshot();await page.evaluate(async()=>{window.testReleaseOpen();delete window.testReleaseOpen;await new Promise(r=>setTimeout(r,0));});assert.equal(await snapshot(),newest);assert.equal(await page.locator('#reportTitle').inputValue(),'Newest synthetic report');assert.equal(await page.locator('#analystNotes').inputValue(),'Imported source-bound assessment');assert.equal(await page.locator('#replaceReport').evaluate(e=>e.open),false);
 const [saved]=await Promise.all([page.waitForEvent('download'),page.locator('#saveReport').click()]);assert.equal(JSON.parse(fs.readFileSync(await saved.path())).settings.notes,'Imported source-bound assessment');await open(b);await status('Saved sources verified');assert.equal(await page.locator('#replaceReport').evaluate(e=>e.open),false);
 // Obsolete errors must not replace newer prepared work, cleared selections or later file errors.
 await page.locator('#prepareReport').click();
 for(const [method,input,prefix] of [['openSaved','openCollection','Could not open file:'],['appendSaved','addCollection','Could not add sources:']]){
  await hold(method);await page.locator('#'+input).setInputFiles(file(a));await page.waitForFunction(()=>!!window.sourceFileGate);await page.locator('#mission').fill('Newer mission during '+method);await page.locator('#prepareReport').click();const editedFile=await snapshot();await release(method,true);await status('Your report changed');assert.equal(await snapshot(),editedFile);assert(!(await page.locator('#status').innerText()).includes('Synthetic obsolete'));assert.equal(await page.locator('#'+input).inputValue(),'');
  await hold(method);await page.locator('#'+input).setInputFiles(file(a));await page.waitForFunction(()=>!!window.sourceFileGate);await page.locator('#'+input).setInputFiles([]);await release(method,true);await status('No source file selected');assert.equal(await snapshot(),editedFile);
  await hold(method);await page.locator('#'+input).setInputFiles(file(a));await page.waitForFunction(()=>!!window.sourceFileGate);await page.locator('#'+input).setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from('{')});await status(prefix);const latestError=await page.locator('#status').innerText();await release(method,true);assert.equal(await page.locator('#status').innerText(),latestError);assert.equal(await snapshot(),editedFile);
  await hold(method);await page.locator('#'+input).setInputFiles(file(a));await page.waitForFunction(()=>!!window.sourceFileGate);await release(method,true);await status(prefix);assert((await page.locator('#status').innerText()).includes('Synthetic obsolete validation failure'));assert.equal(await snapshot(),editedFile);
 }
 // A newer action in the other source-file control wins and clears the obsolete filename.
 await hold('openSaved');await open(a);await page.waitForFunction(()=>!!window.sourceFileGate);await page.locator('#addCollection').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from('{')});await status('Could not add sources:');assert.equal(await page.locator('#openCollection').inputValue(),'');const otherError=await page.locator('#status').innerText();await release('openSaved');assert.equal(await page.locator('#status').innerText(),otherError);assert.equal(await page.locator('#replaceReport').evaluate(e=>e.open),false);
 // A non-file source action supersedes a pending import, whose own filename still cleans up.
 await hold('openSaved');await open(a);await page.waitForFunction(()=>!!window.sourceFileGate);await page.locator('#manageSources').evaluate(e=>e.open=true);await page.locator('#sourceCollections button').first().click();await page.locator('#keepSources').click();await status('Sources kept.');const keptSources=await snapshot();await release('openSaved');assert.equal(await snapshot(),keptSources);assert.equal(await page.locator('#openCollection').inputValue(),'');await status('Sources kept.');
 // A stale file read is discarded before expensive source validation begins.
 await page.evaluate(()=>{const text=File.prototype.text,open=UNMeetingReport.openSaved;window.normalFileText=text;window.normalEarlyOpen=open;window.earlyValidationCalls=0;UNMeetingReport.openSaved=(...args)=>{window.earlyValidationCalls++;return open(...args);};File.prototype.text=async function(){const value=await text.call(this);await new Promise(resolve=>window.releaseSourceRead=()=>resolve(value));return value;};});
 await open(a);await page.waitForFunction(()=>typeof window.releaseSourceRead==='function');await page.locator('#mission').fill('Newest mission during file read');await page.locator('#prepareReport').click();const earlyBefore=await snapshot();await page.evaluate(async()=>{File.prototype.text=window.normalFileText;window.releaseSourceRead();await new Promise(resolve=>setTimeout(resolve,0));UNMeetingReport.openSaved=window.normalEarlyOpen;});await status('Your report changed');assert.equal(await page.evaluate(()=>window.earlyValidationCalls),0);assert.equal(await snapshot(),earlyBefore);
 // Exercise actual directory/file handles with a fictional shared folder. Only the OS picker is substituted.
 const folderContext=await browser.newContext(),reader=await folderContext.newPage();
 await reader.route('**/countries.json',r=>r.fulfill({json:F.countries}));
 await reader.addInitScript(()=>{window.showDirectoryPicker=async options=>{
   if(options.mode!=='read')throw Error('Expected read-only folder access');
   return (await navigator.storage.getDirectory()).getDirectoryHandle('Fictional Mission');
 };});
 await reader.goto(page.url());
 await reader.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready.'));
 const writerPage=await reader.context().newPage();
 await writerPage.goto(page.url());
 await writerPage.evaluate(async corpus=>{
   const root=await navigator.storage.getDirectory();
   const dir=await root.getDirectoryHandle('Fictional Mission',{create:true});
   await dir.getDirectoryHandle('Nested',{create:true});
   for(const [name,content] of [['Briefing.json',JSON.stringify(corpus)],['Other.json','{}'],['Notes.txt','ignore']]){
     const handle=await dir.getFileHandle(name,{create:true}),writer=await handle.createWritable();
     await writer.write(content);await writer.close();
   }
 },a);
 await reader.locator('#missionFolder summary').click();
 await reader.locator('#chooseMissionFolder').click();
 await reader.waitForFunction(()=>document.querySelector('#missionFolderFiles').length===2);
 await reader.locator('#missionFolderSearch').fill('BRIEF');
 assert.equal(await reader.locator('#missionFolderFiles option').count(),1);
 await reader.locator('#openMissionFile').click();
 await reader.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));
 await reader.locator('#analystNotes').fill('Preserve work');
 await writerPage.evaluate(async corpus=>{
   const dir=await (await navigator.storage.getDirectory()).getDirectoryHandle('Fictional Mission');
   const handle=await dir.getFileHandle('Briefing.json'),writer=await handle.createWritable();
   await writer.write(JSON.stringify(corpus));await writer.close();
 },b);
 await reader.locator('#openMissionFile').click();
 await reader.locator('#keepCurrentReport').click();
 assert.equal(await reader.locator('#analystNotes').inputValue(),'Preserve work');
 await reader.locator('#openMissionFile').click();
 await reader.locator('#replaceCurrentReport').click();
 await reader.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));
 assert.equal(await reader.locator('#loadedMeetings input').first().inputValue(),b.records[0].meeting_slug);
 await reader.locator('#analystNotes').fill('Preserve work');
 await writerPage.evaluate(async()=>{
   const dir=await (await navigator.storage.getDirectory()).getDirectoryHandle('Fictional Mission');
   await dir.removeEntry('Briefing.json');
 });
 await writerPage.close();
 await reader.locator('#openMissionFile').click();
 await reader.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Could not open file'));
 assert.equal(await reader.locator('#analystNotes').inputValue(),'Preserve work');
 await reader.locator('#refreshMissionFolder').click();
 await reader.waitForFunction(()=>document.querySelector('#missionFolderFiles').length===0);
 await reader.locator('#missionFolderSearch').fill('');
 assert.equal(await reader.locator('#missionFolderFiles').inputValue(),'Other.json');
 await reader.locator('#forgetMissionFolder').click();
 assert(await reader.locator('#openMissionFile').isDisabled());
 await folderContext.close();
 assert.deepEqual(errors,[]);console.log('PASS: invalid-import preservation; explicit keep/replace and Escape/focus; unchanged sources, notes, appendix, preview and exports on cancellation; no requests before collection approval; partial/failed/cancelled collection; edits during retrieval/validation; stale import isolation; cleared open/add selections, stale/current errors, newer invalid/cross-control selection, file cleanup and early-read refusal; mobile; synthetic sources only');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));});
