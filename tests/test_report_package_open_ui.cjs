/* Direct package reopening never executes imported HTML or replaces newer work. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {startServer,launchBrowser}=require('./reporting_browser_fixture.cjs');
const F=require('./meeting_report_fixture.cjs'),Core=require('../site/meeting-report-core.js'),Package=require('../site/meeting-report-package.js');
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
 const zip=(bytes,name='report.zip')=>({name,mimeType:'application/zip',buffer:Buffer.from(bytes)});
 const oldReport=Core.build([a],old.selected_meetings,old.settings,old.appendix,old.passage_notes),originalHTML=Core.standalone;
 Core.standalone=()=>'<script>globalThis.importedHTMLExecuted=true</script><p>UNTRUSTED_DERIVED_HTML</p>';
 const oldZip=await Package.build(oldReport,[a]);Core.standalone=originalHTML;
 const foreignReport=Core.build([b],[F.meetings[1].slug],{mission:'Foreign mission',notes:'FOREIGN_ASSESSMENT'},undefined,[{record_id:b.records[0].id,text:'FOREIGN_PASSAGE_NOTE'}]),foreignZip=await Package.build(foreignReport,[b]);
 const page=await workspace(),preview=await page.locator('#reportPreview').innerHTML();
 const corrupt=oldZip.slice();corrupt[30+'report.html'.length]^=1;
 const broken=structuredClone(a);broken.records[0].text='Tampered original record';
 const sourceCorrupt=await Package.build(oldReport,[broken]);
 for(const bytes of [corrupt,sourceCorrupt,new Uint8Array([80,75,0,0])]){
  await page.locator('#openCollection').setInputFiles(zip(bytes));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Could not open file:'));assert.equal(await page.locator('#reportPreview').innerHTML(),preview);assert.equal(await page.locator('#analystNotes').inputValue(),old.settings.notes);assert.equal(await page.locator('#replaceReport').evaluate(e=>e.open),false);assert(!(await page.locator('#saveReport').isDisabled()));
 }
 await page.locator('#openCollection').setInputFiles(zip(oldZip));await page.locator('#replaceReport[open]').waitFor();await page.keyboard.press('Escape');assert.equal(await page.locator('#reportPreview').innerHTML(),preview);
 await page.locator('#openCollection').setInputFiles(zip(oldZip,'RENAMED.JSON'));await page.locator('#replaceReport[open]').waitFor();await page.locator('#replaceCurrentReport').click();await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));assert.equal(await page.locator('#analystNotes').inputValue(),old.settings.notes);assert.equal(await page.locator('#reportPreview').innerHTML(),'');assert(await page.locator('#saveReport').isDisabled());assert.equal(await page.evaluate(()=>globalThis.importedHTMLExecuted),undefined);assert(!((await page.locator('body').innerText()).includes('UNTRUSTED_DERIVED_HTML')));
 await page.locator('#prepareReport').click();assert.match(await page.locator('#reportPreview').innerText(),/4 English source segments/);
 await page.locator('#addCollection').setInputFiles(zip(foreignZip));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Sources added:'));assert.equal(await page.locator('#loadedMeetings input').count(),2);assert.equal(await page.locator('#analystNotes').inputValue(),old.settings.notes);assert.match(await page.locator('#passageNotesCount').innerText(),/^1 passage note/);assert.match(await page.locator('#status').innerText(),/were not copied/);await page.locator('#prepareReport').click();
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#saveReport').click()]);const saved=JSON.parse(fs.readFileSync(await download.path()));assert.deepEqual(saved.corpora,[a,b]);assert.deepEqual(saved.passage_notes,old.passage_notes);assert.deepEqual(saved.settings,old.settings);assert(!JSON.stringify(saved).includes('FOREIGN_ASSESSMENT'));
 const fullPreview=await page.locator('#reportPreview').innerHTML();await page.locator('#addCollection').setInputFiles(zip(foreignZip));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Could not add sources:'));assert.match(await page.locator('#status').innerText(),/Already loaded/);assert.equal(await page.locator('#reportPreview').innerHTML(),fullPreview);
 await page.evaluate(limit=>{window.normalLimit=UNMeetingReport.LIMIT;UNMeetingReport.LIMIT=limit;},oldZip.length-1);await page.locator('#openCollection').setInputFiles(zip(oldZip));await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('under 25 MB'));assert.equal(await page.locator('#reportPreview').innerHTML(),fullPreview);await page.evaluate(()=>UNMeetingReport.LIMIT=window.normalLimit);
 // Slow ZIP verification cannot replace a newer edit.
 await page.evaluate(()=>{const read=UNMeetingReportPackage.read;UNMeetingReportPackage.read=async bytes=>{const result=await read(bytes);await new Promise(resolve=>window.finishRead=resolve);return result;};});
 await page.locator('#openCollection').setInputFiles(zip(oldZip));await page.waitForFunction(()=>typeof window.finishRead==='function');await page.locator('#analystNotes').fill('Newer ZIP-time edit');await page.evaluate(()=>window.finishRead());await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Your report changed'));assert.equal(await page.locator('#loadedMeetings input').count(),2);assert.equal(await page.locator('#analystNotes').inputValue(),'Newer ZIP-time edit');assert.equal(await page.locator('#replaceReport').evaluate(e=>e.open),false);assert.equal(await page.locator('#openCollection').inputValue(),'');
 for(const width of [390,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));}await page.close();
 assert.equal(requests.length,0);assert.deepEqual(errors,[]);console.log('PASS: direct ZIP opening and source addition, corrupt ZIP/source and size refusal preserve work, Keep/Escape and replacement, JSON-name signature sniffing, no imported HTML execution, exact source/note/settings replay, incoming annotation exclusion, overlap/stale-edit refusal and mobile without transcript requests');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));});
