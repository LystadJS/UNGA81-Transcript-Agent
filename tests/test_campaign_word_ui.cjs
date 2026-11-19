/* Complete campaign Word copies; fictional records, no Office/account automation. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),{spawnSync}=require('node:child_process'),{startServer,launchBrowser}=require('./reporting_browser_fixture.cjs'),C=require('../site/campaign-notebook-core.js'),F=require('./meeting_report_fixture.cjs');
let browser,server;
(async()=>{
 server=await startServer();browser=await launchBrowser();const base=process.argv[2]||`http://127.0.0.1:${server.address().port}/`,errors=[],external=[];
 const page=await browser.newPage({acceptDownloads:true});page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(new URL(r.url()).origin!==new URL(base).origin)external.push(r.url());});await page.route('**/countries.json',r=>r.fulfill({json:F.countries}));await page.goto(new URL('campaign-notebook.html',base).href);
 const status=prefix=>page.waitForFunction(p=>document.querySelector('#notebookStatus').textContent.startsWith(p),prefix);await status('Ready.');assert.equal(await page.evaluate(()=>typeof UNMeetingReport),'undefined');
 const n=C.empty();n.campaign.title='Fictional briefing É 😀';n.campaign.notes='Private campaign assessment <script>literal</script>\nSecond line';const record=(country,extra={})=>({country,contact:'Fictional lead',role:'Role',email:'lead@example.invalid',status:'unrecorded',status_date:'',follow_up_date:'',reference:'Literal reference',notes:'Country notes 😀',contacts:[],interactions:[],...extra});
 n.entries=[record('Kenya',{contacts:[{id:'fictional-profile',name:'Profile É',role:'Profile role',email:'profile@example.invalid',notes:'Private contact notes'}],interactions:[{id:'fictional-event',date:'2026-11-19',kind:'meeting',contact:'Earlier contact',email:'earlier@example.invalid',summary:'Earlier conversation\nSnapshot',reference:'Earlier reference'}]}),record('United States',{follow_up_date:'2026-11-22',notes:'Hidden country notes'})];
 const file=value=>({name:'fictional.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});await page.locator('#openNotebook').setInputFiles(file(n));await status('Campaign notebook opened');await page.locator('#notebookSearch').fill('Kenya');assert.equal(await page.locator('#notebookRecords article').count(),1);
 const warned=()=>page.evaluate(()=>{const e=new Event('beforeunload',{cancelable:true});window.dispatchEvent(e);return e.defaultPrevented;});
 await page.locator('#campaign_notes').fill(n.campaign.notes+'\tUnsaved note');n.campaign.notes+='\tUnsaved note';assert(await warned());
 const expected=await page.evaluate(value=>{const doc=new DOMParser().parseFromString(UNCampaignNotebook.html(value,[{country:'Kenya'},{country:'United States'}]),'text/html'),walk=doc.createTreeWalker(doc.body,NodeFilter.SHOW_TEXT),text=[];let node;while(node=walk.nextNode())if(node.nodeValue.trim())text.push(node.nodeValue);return text;},n);
 await page.locator('#downloadNotebookWord').focus();const [download]=await Promise.all([page.waitForEvent('download'),page.keyboard.press('Enter')]);assert(download.suggestedFilename().endsWith('.docx'));assert(await warned());
 const bytes=fs.readFileSync(await download.path());assert(bytes.length<C.LIMIT);
 const check=spawnSync('python3',['-c',String.raw`
import json,re,sys,zipfile,xml.etree.ElementTree as ET
expected=json.load(sys.stdin);ns='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
with zipfile.ZipFile(sys.argv[1]) as z:
 assert len(z.namelist())==6 and z.testzip() is None
 parts={name:ET.fromstring(z.read(name)) for name in z.namelist()}
 doc=parts['word/document.xml'];text=''.join('\n' if x.tag==ns+'br' else '\t' if x.tag==ns+'tab' else x.text or '' for x in doc.iter() if x.tag in {ns+'t',ns+'br',ns+'tab'})
 normalize=lambda s:re.sub(r'\s+',' ',s).strip()
 flat=normalize(text);at=0
 for chunk in expected:
  found=flat.find(normalize(chunk),at);assert found>=0,chunk;at=found+len(normalize(chunk))
 assert 'Word edits cannot be imported' in text
 assert 'Private contact notes' in text and 'Earlier conversation' in text and 'Hidden country notes' in text
 assert all('macro' not in name.lower() and not name.startswith('customXml/') for name in z.namelist())
print('PASS: independent native DOCX ZIP/CRC/XML, every complete HTML text chunk in order, private campaign/contact/log scope and resumable-JSON notice')
`,await download.path()],{input:JSON.stringify(expected),encoding:'utf8'});assert.equal(check.status,0,check.stderr);process.stdout.write(check.stdout);
 const [saved]=await Promise.all([page.waitForEvent('download'),page.locator('#saveNotebook').click()]);assert.deepEqual(JSON.parse(fs.readFileSync(await saved.path())),C.validate(n,F.countries));assert.equal(download.suggestedFilename(),saved.suggestedFilename().replace('.json','.docx'));assert.equal(await warned(),false);
 await page.locator('#entry_contact').fill('Unapplied');assert(await page.locator('#downloadNotebookWord').isDisabled());await page.locator('#discardEntry').click();await page.locator('#notebookProceed').click();await status('Country form cleared');
 // Binary bound is enforced before download; exact bound succeeds, one byte less refuses.
 const boundary=await page.evaluate(value=>{const old=UNCampaignNotebook.LIMIT;try{const length=UNMeetingReportWord.buildCampaign(value,[{country:'Kenya'},{country:'United States'}]).length;UNCampaignNotebook.LIMIT=length;const exact=UNMeetingReportWord.buildCampaign(value,[{country:'Kenya'},{country:'United States'}]).length;UNCampaignNotebook.LIMIT=length-1;try{UNMeetingReportWord.buildCampaign(value,[{country:'Kenya'},{country:'United States'}]);return false;}catch(e){return exact===length&&/1 MiB/.test(e.message);}}finally{UNCampaignNotebook.LIMIT=old;}},n);assert(boundary);
 let downloads=0;page.on('download',()=>downloads++);
 await page.evaluate(limit=>{window.campaignWordLimit=UNCampaignNotebook.LIMIT;UNCampaignNotebook.LIMIT=limit;},bytes.length-1);await page.locator('#downloadNotebookWord').click();await status('Word notebook exceeds 1 MiB');assert.equal(downloads,0);assert.equal(await warned(),false);await page.evaluate(()=>UNCampaignNotebook.LIMIT=window.campaignWordLimit);

 const hold=()=>page.evaluate(()=>{window.normalCampaignWord=UNMeetingReportWord.buildCampaign;UNMeetingReportWord.buildCampaign=async(...args)=>{const bytes=window.normalCampaignWord(...args);await new Promise((resolve,reject)=>window.wordGate={resolve,reject});return bytes;};});
 const release=fail=>page.evaluate(async fail=>{UNMeetingReportWord.buildCampaign=window.normalCampaignWord;const gate=window.wordGate;delete window.wordGate;fail?gate.reject(Error('Synthetic stale Word failure')):gate.resolve();await new Promise(r=>setTimeout(r,0));},fail);
 await hold();await page.locator('#downloadNotebookWord').click();await page.waitForFunction(()=>!!window.wordGate);await page.locator('#campaign_notes').fill('Newer edit');await release(false);await status('Notebook changed while preparing Word');assert.equal(downloads,0);assert(await warned());
 await hold();await page.locator('#downloadNotebookWord').click();await page.waitForFunction(()=>!!window.wordGate);await page.locator('#openNotebook').setInputFiles(file({}));await status('Could not open notebook:');const latest=await page.locator('#notebookStatus').innerText();await release(true);assert.equal(await page.locator('#notebookStatus').innerText(),latest);assert.equal(downloads,0);
 await page.evaluate(()=>{window.normalWordURL=URL.createObjectURL;URL.createObjectURL=()=>{throw Error('Synthetic Word download failure');};});await page.locator('#downloadNotebookWord').click();await status('Could not start download:');assert(await warned());assert.equal(downloads,0);await page.evaluate(()=>URL.createObjectURL=window.normalWordURL);
 for(const width of [390,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));}await page.close();
 // Missing/older optional modules disable only Word, preserving ordinary notebook saves.
 for(const mode of ['word','package','older']){const p=await browser.newPage({acceptDownloads:true});p.on('pageerror',e=>errors.push(e.message));await p.route('**/countries.json',r=>r.fulfill({json:F.countries}));await p.route(mode==='word'?'**/meeting-report-word.js*':'**/meeting-report-package.js*',r=>mode==='older'?r.fulfill({contentType:'text/javascript',body:'globalThis.UNMeetingReportPackage={zip(){}};'}):r.abort());await p.goto(new URL('campaign-notebook.html',base).href);await p.waitForFunction(()=>document.querySelector('#notebookStatus').textContent.startsWith('Ready.'));assert(await p.locator('#downloadNotebookWord').isDisabled());await p.locator('#campaign_title').fill('Ordinary save still works');const [d]=await Promise.all([p.waitForEvent('download'),p.locator('#saveNotebook').click()]);assert.equal(JSON.parse(fs.readFileSync(await d.path())).campaign.title,'Ordinary save still works');await p.close();}
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);console.log('PASS: complete campaign Word despite list filters, unchanged resumable JSON/dirty protection, pending form guards, exact binary bound, stale edits/source/errors, failed downloads, mobile and optional-module isolation without report-core/source requests');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{await browser?.close();if(server)await new Promise(r=>server.close(r));});
