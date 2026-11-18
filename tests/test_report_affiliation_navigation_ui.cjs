/* Affiliation jumps preserve complete reports and work without JavaScript. */
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
 const report=Core.savedReport(Core.build([a,b],[F.meetings[0].slug,F.meetings[1].slug],old.settings,old.appendix,old.passage_notes),[a,b]);
 for(const value of [old,report]){
  const page=await workspace(value);await page.locator('#evidenceSearch').fill('schools');await page.locator('#evidenceCountry').selectOption(JSON.stringify('United States'));
  const before={preview:await page.locator('#reportPreview').innerHTML(),notes:await page.locator('#analystNotes').inputValue(),appendix:await page.locator('#appendixCount').innerText()};
  const jumps=page.locator('#reportPreview .country-jumps a');assert.deepEqual(await jumps.allTextContents(),['Kenya','United States']);assert.equal(await page.locator('#reportPreview .report-country-target').count(),2);
  assert(await page.locator('#reportPreview').evaluate(root=>{const ids=[...root.querySelectorAll('[id]')].map(e=>e.id);return new Set(ids).size===ids.length&&[...root.querySelectorAll('a[href^="#"]')].every(a=>root.querySelector('[id="'+a.getAttribute('href').slice(1)+'"]'));}));
  for(const width of [390,1440]){await page.setViewportSize({width,height:900});await jumps.first().focus();await page.keyboard.press('Enter');const target=page.locator('#reportPreview #report-country-1');assert(await target.evaluate(e=>e===document.activeElement));assert.match(await target.innerText(),/^Kenya/);await target.locator('a[href="#report-country-index"]').click();assert(await page.locator('#reportPreview #report-country-index').evaluate(e=>e===document.activeElement));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));}
  assert.equal(await page.locator('#reportPreview').innerHTML(),before.preview);assert.equal(await page.locator('#analystNotes').inputValue(),before.notes);assert.equal(await page.locator('#appendixCount').innerText(),before.appendix);assert.equal(await page.locator('#evidenceSearch').inputValue(),'schools');assert.equal(await page.locator('#evidenceCountry').inputValue(),JSON.stringify('United States'));assert(!(await page.locator('#saveReport').isDisabled()));
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#downloadReport').click()]);const html=fs.readFileSync(await download.path(),'utf8');assert(!html.includes('<script'));
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:900}});await context.route('**/affiliation-reading-copy.html',r=>r.fulfill({contentType:'text/html',body:html}));const reading=await context.newPage();await reading.goto(new URL('affiliation-reading-copy.html',base).href);await reading.locator('.country-jumps a').last().focus();await reading.keyboard.press('Enter');assert(await reading.locator('#report-country-2').evaluate(e=>e===document.activeElement));await reading.locator('#report-country-2 a[href="#report-country-index"]').click();assert(await reading.locator('#report-country-index').evaluate(e=>e===document.activeElement));await context.close();await page.close();
 }
 assert.equal(requests.length,0);assert.deepEqual(errors,[]);console.log('PASS: single/multi-meeting alphabetical affiliation navigation, unique valid destinations, keyboard row/return focus, unchanged report/filter/notes/appendix/export state, native script-free HTML navigation and mobile without source requests');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));});
