/* Browser package transaction with fictional sources only. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),http=require('node:http'),path=require('node:path'),{spawnSync}=require('node:child_process');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright'),F=require('./meeting_report_fixture.cjs'),root=path.resolve(__dirname,'../site');
let browser,server;
(async()=>{
 server=http.createServer((req,res)=>{const p=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!p.startsWith(root+path.sep)){res.writeHead(403);return res.end();}try{res.setHeader('Content-Type',p.endsWith('.js')?'text/javascript':p.endsWith('.css')?'text/css':p.endsWith('.json')?'application/json':'text/html');res.end(fs.readFileSync(p));}catch{res.writeHead(404);res.end();}});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_PATH||'/usr/bin/chromium'});
 const page=await browser.newPage({acceptDownloads:true,viewport:{width:1440,height:900}}),errors=[],requests=[],downloads=[];
 page.setDefaultTimeout(30000);page.on('pageerror',e=>errors.push(e.message));page.on('download',d=>downloads.push(d));
 await page.route('**/countries.json',r=>r.fulfill({json:F.countries}));await page.route('https://transcripts.un.org/**',r=>{requests.push(r.request().url());return r.abort();});
 await page.goto(new URL('meeting-reports.html',process.argv[2]||`http://127.0.0.1:${server.address().port}/`).href);await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready.'));
 const a=await F.corpus(),b=await F.corpus(1),file=c=>({name:'synthetic.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(c))});
 await page.locator('#openCollection').setInputFiles(file(a));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));
 assert.equal(await page.locator('#downloadPackage').isDisabled(),true);await page.locator('#analystNotes').fill('Fictional local assessment 😀');await page.locator('#prepareReport').click();
 await page.locator('#downloadPackage').focus();const [download]=await Promise.all([page.waitForEvent('download'),page.keyboard.press('Enter')]);assert.match(download.suggestedFilename(),/^un-meeting-report-\d{8}T\d{9}Z\.zip$/);
 const check=spawnSync('python3',['-c',"import zipfile,sys,json,hashlib; z=zipfile.ZipFile(sys.argv[1]); assert z.testzip() is None; m=json.loads(z.read('manifest.json')); assert all(hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'] for f in m['files']); print(z.read('report.json').decode())",await download.path()],{encoding:'utf8'});assert.equal(check.status,0,check.stderr);const saved=JSON.parse(check.stdout);assert.equal(saved.settings.notes,'Fictional local assessment 😀');assert.deepEqual(saved.corpora,[a]);
 const [csv]=await Promise.all([page.waitForEvent('download'),page.locator('#downloadEvidence').click()]);assert.equal(csv.suggestedFilename(),download.suggestedFilename().replace('.zip','-evidence.csv'));
 // Saving the complete package preserves replayable work, so replacement needs no unsaved warning.
 await page.locator('#openCollection').setInputFiles(file(saved));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));assert.equal(await page.locator('#replaceReport').evaluate(e=>e.open),false);assert.equal(await page.locator('#analystNotes').inputValue(),saved.settings.notes);
 await page.locator('#prepareReport').click();
 // Hold package completion across a new edit; stale output must never download or clear dirty state.
 await page.evaluate(()=>{const original=UNMeetingReportPackage.build;window.originalPackage=original;UNMeetingReportPackage.build=async(...args)=>{const bytes=await original(...args);await new Promise(r=>window.releasePackage=r);return bytes;};});
 const count=downloads.length;await page.locator('#downloadPackage').click();await page.waitForFunction(()=>typeof window.releasePackage==='function');assert.equal(await page.locator('#downloadPackage').isDisabled(),true);
 await page.locator('#analystNotes').fill('Newer assessment');await page.locator('#prepareReport').click();assert.equal(await page.locator('#downloadPackage').isDisabled(),true);await page.evaluate(()=>window.releasePackage());await page.waitForFunction(()=>document.querySelector('#packageStatus').textContent.startsWith('Your report changed'));assert.equal(downloads.length,count);assert.equal(await page.locator('#analystNotes').inputValue(),'Newer assessment');assert.equal(await page.locator('#downloadPackage').isDisabled(),false);
 await page.locator('#openCollection').setInputFiles(file(b));await page.locator('#replaceReport[open]').waitFor();await page.locator('#keepCurrentReport').click();
 // A real byte-bound refusal also leaves the current preview and unsaved warning intact.
 await page.evaluate(()=>{UNMeetingReportPackage.build=window.originalPackage;UNMeetingReport.LIMIT=100;});const preview=await page.locator('#reportPreview').innerHTML();await page.locator('#downloadPackage').click();await page.waitForFunction(()=>document.querySelector('#packageStatus').textContent.includes('exceeds 25 MB'));assert.equal(downloads.length,count);assert.equal(await page.locator('#reportPreview').innerHTML(),preview);await page.evaluate(()=>UNMeetingReport.LIMIT=25000000);
 await page.locator('#openCollection').setInputFiles(file(b));await page.locator('#replaceReport[open]').waitFor();await page.locator('#keepCurrentReport').click();await page.evaluate(()=>UNMeetingReport.LIMIT=25000000);
 for(const width of [390,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));}
 assert.deepEqual(requests,[]);assert.deepEqual(errors,[]);console.log('PASS: local ZIP download, independent checksum/CRC verification, saved-work replay, timestamp, stale-package refusal, size-failure preservation, keyboard-accessible controls and mobile layout; no source requests');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));});
