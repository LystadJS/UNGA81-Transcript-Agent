/* Confirmed source removal keeps other sources and annotations intact. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {startServer,launchBrowser}=require('./reporting_browser_fixture.cjs');
const F=require('./meeting_report_fixture.cjs'),Core=require('../site/meeting-report-core.js');
let browser,server;
(async()=>{
 server=await startServer();
 browser=await launchBrowser();
 const a=await F.corpus(),b=await F.corpus(1);
 const file=value=>({name:'synthetic.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});
 const old=Core.savedReport(Core.build([a],[F.meetings[0].slug],{mission:'Current mission',title:'Current report',notes:'Keep global assessment 😀',questions:[{heading:'Current question',query:'humanitarian access'}]}, {mode:'selected',record_ids:[a.records[0].id]},[{record_id:a.records[0].id,text:'Keep source interpretation'}]),[a]);
 const errors=[],requests=[],base=process.argv[2]||`http://127.0.0.1:${server.address().port}/`;
 async function workspace(value=old){
  const page=await browser.newPage({acceptDownloads:true,viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/countries.json',r=>r.fulfill({json:F.countries}));await page.route('https://transcripts.un.org/**',r=>{requests.push(r.request().url());return r.abort();});
  await page.goto(new URL('meeting-reports.html',base).href);await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready.'));assert(await page.locator('#addCollection').isDisabled());
  await page.locator('#openCollection').setInputFiles(file(value));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));await page.locator('#prepareReport').click();assert(!(await page.locator('#addCollection').isDisabled()));return page;
 }
 const both=Core.savedReport(Core.build([a,b],[F.meetings[0].slug,F.meetings[1].slug],old.settings,{mode:'selected',record_ids:[a.records[0].id,b.records[0].id]},[{record_id:a.records[0].id,text:'A note'},{record_id:b.records[0].id,text:'B note'}]),[a,b]);
 const page=await workspace(both);await page.locator('#saveDeviceReport').click();await page.waitForFunction(()=>document.querySelector('#deviceReportStatus').textContent.startsWith('Report saved'));const stored=await page.evaluate(()=>UNReportStorage.read());await page.locator('#manageSources summary').click();
 assert.equal(await page.locator('#sourceCollections button').count(),2);assert.match(await page.locator('#sourceCollections').innerText(),/source JSON bytes/);
 const preview=await page.locator('#reportPreview').innerHTML();
 await page.locator('#sourceCollections button').first().click();assert(await page.locator('#keepSources').evaluate(e=>e===document.activeElement));assert.match(await page.locator('#removeSourcesMessage').innerText(),/1 passage note and 1 appendix selection/);await page.keyboard.press('Escape');
 await page.waitForFunction(()=>!document.querySelector('#removeSources').open);assert.equal(await page.locator('#reportPreview').innerHTML(),preview);assert.equal(await page.locator('#loadedMeetings input').count(),2);
 assert(await page.locator('#sourceCollections button').first().evaluate(e=>e===document.activeElement));
 await page.locator('#sourceCollections button').first().click();await page.locator('#confirmRemoveSources').click();await page.waitForFunction(()=>document.querySelector('#loadedMeetings').children.length===1);
 assert.equal(await page.locator('#analystNotes').inputValue(),old.settings.notes);assert.equal(await page.locator('#mission').inputValue(),old.settings.mission);assert.match(await page.locator('#passageNotesCount').innerText(),/^1 passage note/);assert.match(await page.locator('#appendixCount').innerText(),/^1 passage selected/);assert(await page.locator('#saveReport').isDisabled());assert(await page.locator('#downloadWord').isDisabled());assert(await page.locator('#printReportButton').isDisabled());
 await page.locator('#prepareReport').click();const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#saveReport').click()]);const saved=JSON.parse(fs.readFileSync(await download.path()));assert.deepEqual(saved.corpora,[b]);assert.deepEqual(saved.passage_notes,[both.passage_notes[1]]);assert.deepEqual(saved.appendix.record_ids,[b.records[0].id]);assert.deepEqual(saved.settings,old.settings);assert(file(saved).buffer.length<file(both).buffer.length);
 // A newer edit invalidates a previously displayed removal plan.
 await page.locator('#sourceCollections button').click();await page.evaluate(()=>{const e=document.querySelector('#analystNotes');e.value='Newer assessment';e.dispatchEvent(new Event('input',{bubbles:true}));});await page.locator('#confirmRemoveSources').click();await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Your report changed'));assert.equal(await page.locator('#loadedMeetings input').count(),1);assert.equal(await page.locator('#analystNotes').inputValue(),'Newer assessment');
 await page.locator('#sourceCollections button').click();assert.match(await page.locator('#removeSourcesMessage').innerText(),/last collection.*assessment will also be cleared/);
 for(const width of [390,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));}
 await page.locator('#keepSources').click();assert.equal(await page.locator('#analystNotes').inputValue(),'Newer assessment');
 await page.locator('#sourceCollections button').click();await page.locator('#confirmRemoveSources').click();await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Current sources and assessment cleared'));
 assert.equal(await page.locator('#loadedMeetings input').count(),0);assert.equal(await page.locator('#analystNotes').inputValue(),'');assert.equal(await page.locator('#mission').inputValue(),old.settings.mission);assert.equal(await page.locator('#briefingQuestions [data-heading]').inputValue(),'Current question');assert(await page.locator('#manageSources').isHidden());assert(await page.locator('#addCollection').isDisabled());assert(await page.locator('#analystNotes').isDisabled());assert(await page.locator('#openCollection').evaluate(e=>e===document.activeElement));
 assert.equal(await page.evaluate(()=>UNReportStorage.read()),stored);await page.locator('#openCollection').setInputFiles(file(old));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));assert.equal(await page.locator('#loadedMeetings input').count(),1);assert.equal(await page.locator('#replaceReport').evaluate(e=>e.open),false);await page.close();
 assert.equal(requests.length,0);assert.deepEqual(errors,[]);console.log('PASS: default keep/Escape and focus, exact kept sources and annotations, export invalidation and smaller saved JSON, stale confirmation refusal, explicit last-assessment clearing, reusable settings, reopening, mobile and no transcript requests');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));});
