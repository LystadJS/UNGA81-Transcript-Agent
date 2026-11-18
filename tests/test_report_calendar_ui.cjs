/* Calendar copies use explicit dates and never count as resumable report saves. */
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
 const page=await workspace();await page.getByText('Calendar entry for a report review',{exact:true}).click();assert(await page.locator('#downloadReviewEntry').isDisabled());assert.equal(await page.locator('#calendarAssessment').isChecked(),false);
 const before=await page.locator('#reportPreview').innerHTML();await page.locator('#reviewDate').fill('2028-02-29');assert(!(await page.locator('#downloadReviewEntry').isDisabled()));assert.equal(await page.locator('#reportPreview').innerHTML(),before);assert(!(await page.locator('#saveReport').isDisabled()));
 const [plain]=await Promise.all([page.waitForEvent('download'),page.locator('#downloadReviewEntry').click()]);const plainText=fs.readFileSync(await plain.path(),'utf8');assert.match(plain.suggestedFilename(),/-review-2028-02-29\.ics$/);assert.match(plainText,/DTSTART;VALUE=DATE:20280229/);assert(!plainText.includes(old.settings.notes));assert.equal(await page.locator('#reportPreview').innerHTML(),before);
 await page.locator('#calendarAssessment').check();const [notes]=await Promise.all([page.waitForEvent('download'),page.locator('#downloadReviewEntry').click()]);assert(fs.readFileSync(await notes.path(),'utf8').replace(/\r\n /g,'').includes(old.settings.notes));
 // Calendar downloads are reading copies, so unsaved-work protection remains.
 await page.locator('#openCollection').setInputFiles(file(b));await page.locator('#replaceReport[open]').waitFor();await page.locator('#keepCurrentReport').click();assert.equal(await page.locator('#analystNotes').inputValue(),old.settings.notes);
 await page.evaluate(()=>{window.normalCalendar=UNMeetingReportCalendar.build;UNMeetingReportCalendar.build=async()=>{throw Error('Synthetic calendar failure');};});await page.locator('#downloadReviewEntry').click();await page.waitForFunction(()=>document.querySelector('#calendarStatus').textContent.includes('Synthetic calendar failure'));assert.equal(await page.locator('#reportPreview').innerHTML(),before);assert(!(await page.locator('#saveReport').isDisabled()));
 // An old calendar export cannot download after its options or source report changes.
 const downloads=[];page.on('download',d=>downloads.push(d));
 for(const change of ['date','note']){
  await page.evaluate(()=>{UNMeetingReportCalendar.build=async(...args)=>{const bytes=await window.normalCalendar(...args);await new Promise(resolve=>window.finishCalendar=resolve);return bytes;};});await page.locator('#downloadReviewEntry').click();await page.waitForFunction(()=>typeof window.finishCalendar==='function');if(change==='date')await page.locator('#reviewDate').fill('2028-03-01');else await page.locator('#analystNotes').fill('Newer assessment');await page.evaluate(()=>{window.finishCalendar();delete window.finishCalendar;});await page.waitForFunction(()=>document.querySelector('#calendarStatus').textContent.startsWith('Your report or calendar options changed'));assert.equal(downloads.length,0);if(change==='note'){assert(await page.locator('#downloadReviewEntry').isDisabled());await page.locator('#prepareReport').click();}
 }
 await page.evaluate(()=>{UNMeetingReportCalendar.build=window.normalCalendar;UNMeetingReport.LIMIT=100;});await page.locator('#downloadReviewEntry').click();await page.waitForFunction(()=>document.querySelector('#calendarStatus').textContent.includes('exceeds 25 MB'));assert.equal(downloads.length,0);assert(!(await page.locator('#saveReport').isDisabled()));await page.evaluate(()=>UNMeetingReport.LIMIT=25000000);
 // Export options remain outside saved report JSON and reset on a replacement.
 const [json]=await Promise.all([page.waitForEvent('download'),page.locator('#saveReport').click()]);const saved=JSON.parse(fs.readFileSync(await json.path()));assert(!Object.hasOwn(saved,'review_date'));assert(!Object.hasOwn(saved.settings,'review_date'));await page.locator('#openCollection').setInputFiles(file(saved));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));assert.equal(await page.locator('#reviewDate').inputValue(),'');assert.equal(await page.locator('#calendarAssessment').isChecked(),false);await page.locator('#prepareReport').click();assert(await page.locator('#downloadReviewEntry').isDisabled());
 // A missing optional exporter does not prevent the report itself being prepared.
 await page.evaluate(()=>{window.savedCalendar=UNMeetingReportCalendar;delete window.UNMeetingReportCalendar;});await page.locator('#prepareReport').click();assert(!(await page.locator('#saveReport').isDisabled()));assert(await page.locator('#downloadReviewEntry').isDisabled());assert.match(await page.locator('#calendarStatus').innerText(),/unavailable/);await page.evaluate(()=>window.UNMeetingReportCalendar=window.savedCalendar);
 for(const width of [390,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));}await page.close();
 assert.equal(requests.length,0);assert.deepEqual(errors,[]);console.log('PASS: explicit personal all-day date and optional assessment, valid ICS download, unchanged report and dirty protection, size/failure preservation, stale date/report refusal, JSON exclusion/reset, optional-module failure isolation and mobile without source requests');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));});
