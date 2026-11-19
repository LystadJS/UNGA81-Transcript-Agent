/* Personal facilitator tool. The public application has no dependency on this. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),http=require('node:http'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const F=require('../tests/meeting_report_fixture.cjs'),Collector=require('../site/collector.js'),Core=require('../site/meeting-report-core.js'),Draft=require('../site/meeting-report-draft.js'),Campaign=require('../site/campaign-notebook-core.js'),root=path.resolve(__dirname,'..');
const meetings=F.meetings.map(m=>({...m,title:'FICTIONAL TRAINING — '+m.title}));
function fixtureResponse(url){
 const u=new URL(url);
 if(u.origin!=='https://transcripts.un.org')return null;
 if(u.pathname==='/en/meetings.json'){
  const selected=u.searchParams.get('date')===F.date?meetings:[];
  return {meetings:selected,page:1,total:selected.length,hasMore:false};
 }
 const meeting=meetings.find(m=>u.pathname==='/en/'+m.slug+'.json');
 return meeting?F.transcript(meeting):null;
}
async function materials(countries){
 const policy=JSON.parse(fs.readFileSync(path.join(root,'site/reporting-exclusions.json'))),corpora=[];
 const request=async url=>{const data=fixtureResponse(url);if(!data)throw Error('Unexpected fictional fixture request.');const raw=JSON.stringify(data);return {data,raw,hash:await Collector.sha(raw),retrieved_at:new Date().toISOString()};};
 for(const m of meetings)corpora.push(await Collector.collect({start:F.date,end:F.date,scope:'all',meeting_slug:m.slug,meeting_date:F.date},countries,{request}));
 await Core.validateCorpora(corpora,policy,countries);
 const report=Core.build(corpora,meetings.map(m=>m.slug),{mission:'Fictional training mission',title:'Fictional two-meeting report',questions:[{heading:'Fictional humanitarian question',query:'humanitarian access'},{heading:'Fictional unanswered question',query:'absentfixtureterm'}]}),addition=Core.build([corpora[1]],[meetings[1].slug],{mission:'Other fictional mission',title:'Fictional additional report',notes:'Fictional incoming assessment; leave this out of the current report.'});
 const packet=await Draft.createInput(report,policy),record=packet.context.records.find(r=>r.speaking_capacity==='collective_indicated');assert(record,'Fictional draft needs its collective source passage.');
 const draft={schema:Draft.OUTPUT,context_sha256:packet.context_sha256,generated_at:new Date().toISOString(),model:'FICTIONAL UI FIXTURE — SIMULATED REQUEST COUNT; NO MODEL INFERENCE',request_count:1,review_status:'unreviewed',sections:packet.context.questions.map(q=>({heading:q.heading,query:q.query,status:q.record_ids.length?'generated':'no_matching_source',bullets:q.record_ids.length?[{text:'FICTIONAL HAND-AUTHORED DRAFT — The fictional collective passage supports humanitarian access; national attribution is withheld.',evidence:[{record_id:record.id,quote:record.text}]}]:[]}))};
 Draft.checkOutput(draft,packet);
 const profile=(id,name)=>({id,name,role:'FICTIONAL training representative',email:'fictional@example.invalid',notes:'FICTIONAL profile notes — not a real contact.'}),entry=(country,extra={})=>({country,contact:'',role:'',email:'',status:'unrecorded',status_date:'',follow_up_date:'',reference:'',notes:'',contacts:[],interactions:[],...extra});
 const campaign=Campaign.empty();campaign.campaign={title:'FICTIONAL TRAINING — Outreach notebook',candidate:'FICTIONAL candidate / exercise only',body:'FICTIONAL exercise, not an actual election',election_date:'2026-11-30',notes:'FICTIONAL current campaign assessment — keep this separate from contacts.'};campaign.entries=[entry('Kenya',{contact:'FICTIONAL current lead',status:'contacted',status_date:'2026-11-18',follow_up_date:'2026-11-21',reference:'FICTIONAL conversation reference',notes:'FICTIONAL country-only note',contacts:[profile('training-kenya-1','FICTIONAL KENYA PROFILE 1')],interactions:[{id:'training-log-1',date:'2026-11-18',kind:'meeting',contact:'FICTIONAL earlier contact snapshot',email:'',summary:'FICTIONAL earlier conversation — no verified pledge or vote.',reference:'FICTIONAL source reference'}]})];
 const incoming=Campaign.empty();incoming.campaign.notes='FICTIONAL incoming campaign assessment — must not be transferred.';incoming.entries=[entry('Kenya',{contacts:[...campaign.entries[0].contacts,profile('training-kenya-2','FICTIONAL KENYA PROFILE 2')]}),entry('United States',{contacts:[profile('training-us-1','FICTIONAL US PROFILE 1')]})];const contactTransfer=Campaign.contactTransfer(incoming,countries);Campaign.validate(campaign,countries);const plan=Campaign.planContactTransfer(campaign,contactTransfer,countries);assert.equal(plan.added,2);assert.equal(plan.unchanged,1);
 return {'synthetic-collection.json':corpora[0],'synthetic-multi-meeting-report.json':Core.savedReport(report,corpora),'synthetic-additional-report.json':Core.savedReport(addition,[corpora[1]]),'synthetic-model-draft.json':draft,'synthetic-campaign-notebook.json':Campaign.validate(campaign,countries),'synthetic-contact-transfer.json':contactTransfer};
}
const writePrivate=(folder,name,value)=>fs.writeFileSync(path.join(folder,name),JSON.stringify(value,null,2)+'\n',{mode:0o600});
async function createMaterials(){
 const files=await materials(JSON.parse(fs.readFileSync(path.join(root,'site/countries.json')))),folder=fs.mkdtempSync(path.join(os.tmpdir(),'un-reporting-session-'));fs.chmodSync(folder,0o700);
 try{for(const [name,value] of Object.entries(files))writePrivate(folder,name,value);}catch(error){fs.rmSync(folder,{recursive:true,force:true});throw error;}
 return {folder,files:Object.keys(files),fixture_date:F.date,mode:'fixture_generation',tool_model_inference:'not_run',bundled_draft:'hand_authored_fictional',campaign_materials:'hand_authored_fictional',tool_calendar_client_import:'not_run',participant_acceptance:'not_recorded'};
}
async function run({smoke=false}={}){
 const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
 const material=await createMaterials(),folder=material.folder;
 const publicRoot=path.join(folder,'public'),downloads=path.join(folder,'downloads');fs.mkdirSync(downloads,{mode:0o700});
 let server,browser,context,origin;const pending=new Set(),errors=[],counts={fixture_requests:0,blocked_requests:0,downloads:0};
 const receipt={schema:'un.reporting-usability-session.v1',mode:smoke?'engineering_smoke':'facilitated',participant_acceptance:'not_recorded',tool_model_inference:'not_run',bundled_draft:'hand_authored_fictional',campaign_materials:'hand_authored_fictional',tool_calendar_client_import:'not_run',started_at:new Date().toISOString(),fixture_date:F.date,source_commit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),source_dirty:!!execFileSync('git',['status','--porcelain'],{cwd:root,encoding:'utf8'}).trim(),application_release:JSON.parse(fs.readFileSync(path.join(root,'site/release.json'))).browser_engine,status:'incomplete'};
 const write=(name,value)=>writePrivate(folder,name,value);
 try{
  execFileSync(process.env.PYTHON||'python',[path.join(root,'tools/build_pages.py'),publicRoot],{cwd:root,stdio:'pipe'});
  server=http.createServer((req,res)=>{
   if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);return res.end();}
   try{
    const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(publicRoot,'.'+(pathname==='/'?'/meeting-reports.html':pathname));
    if(!file.startsWith(publicRoot+path.sep)||!fs.realpathSync(file).startsWith(publicRoot+path.sep))throw Error('Outside public build');
    const type={'.js':'text/javascript','.css':'text/css','.json':'application/json','.html':'text/html','.svg':'image/svg+xml','.woff2':'font/woff2'}[path.extname(file)]||'application/octet-stream';res.setHeader('Content-Type',type);res.end(req.method==='HEAD'?undefined:fs.readFileSync(file));
   }catch{res.writeHead(404);res.end('Not in this public fixture workspace.');}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));origin='http://127.0.0.1:'+server.address().port;
  browser=await chromium.launch({headless:smoke,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});receipt.browser=browser.version();
  context=await browser.newContext({acceptDownloads:true,serviceWorkers:'block',viewport:{width:1440,height:1000}});
  await context.route('**/*',route=>{
   const u=new URL(route.request().url());if(u.origin===origin)return route.continue();
   const data=route.request().method()==='GET'?fixtureResponse(u.href):null;
   if(data){counts.fixture_requests++;return route.fulfill({json:data,headers:{'access-control-allow-origin':'*'}});}
   counts.blocked_requests++;return route.fulfill({status:403,contentType:'text/plain',body:'Fictional usability session: external requests and source-shaped locators are blocked. No real statement was retrieved.'});
  });
  await context.addInitScript(()=>document.addEventListener('DOMContentLoaded',()=>{const banner=document.createElement('p');banner.className='notice';banner.setAttribute('role','note');banner.textContent='FICTIONAL USABILITY SESSION — Synthetic sources only. Source-shaped links do not identify real statements. Bundled draft text and request counts are hand-authored simulations. This tool performs no model inference. No human acceptance is recorded automatically.';document.body.prepend(banner);document.title='[FICTIONAL SESSION] '+document.title;}));
  context.on('page',page=>{
   page.on('pageerror',error=>errors.push(error.name));
   page.on('download',download=>{
    const failed=()=>{errors.push('DownloadFailure');console.error('Could not retain a session download. Keep the browser open and resolve the output-folder error before closing.');};
    try{
     const filename=path.basename(download.suggestedFilename()).replace(/[\\/]/g,'_');let target=path.join(downloads,filename),suffix=1;while(fs.existsSync(target))target=path.join(downloads,String(suffix++)+'-'+filename);fs.writeFileSync(target,'',{flag:'wx',mode:0o600});
     const saved=download.saveAs(target).then(()=>{fs.chmodSync(target,0o600);counts.downloads++;});pending.add(saved);saved.catch(failed).finally(()=>pending.delete(saved));
    }catch{failed();}
   });
  });
  const page=await context.newPage();await page.goto(origin+'/meeting-reports.html');await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready.'));
  await page.locator('#reportTitle').fill('Fictional training report');
  console.log(JSON.stringify({folder,url:page.url(),fixture_date:F.date,files:material.files,mode:receipt.mode,tool_model_inference:'not_run',bundled_draft:'hand_authored_fictional',campaign_materials:'hand_authored_fictional',tool_calendar_client_import:'not_run',participant_acceptance:'not_recorded'}));
  if(smoke){
   await page.locator('#openCollection').setInputFiles(path.join(folder,'synthetic-collection.json'));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));
   await page.locator('#analystNotes').fill('Fictional smoke assessment');await page.locator('#prepareReport').click();
   await page.locator('#meetingDate').fill(F.date);await page.locator('#findMeetings').click();await page.waitForFunction(()=>document.querySelectorAll('#inventory input').length===2);await page.locator('#inventory input').last().check();await page.locator('#addSelectedMeetings').click();await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Transcripts added:'));assert.equal(await page.locator('#analystNotes').inputValue(),'Fictional smoke assessment');assert.equal(await page.locator('#loadedMeetings input:checked').count(),2);
   await page.locator('#prepareReport').click();const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#saveReport').click()]);await download.path();await Promise.all([...pending]);
   const saved=JSON.parse(fs.readFileSync(path.join(downloads,path.basename(download.suggestedFilename()))));assert.equal(saved.settings.notes,'Fictional smoke assessment');assert.equal(saved.corpora.length,2);await Core.openSaved(saved,JSON.parse(fs.readFileSync(path.join(root,'site/reporting-exclusions.json'))),JSON.parse(fs.readFileSync(path.join(root,'site/countries.json'))));
   const [again]=await Promise.all([page.waitForEvent('download'),page.locator('#saveReport').click()]);await again.path();await Promise.all([...pending]);const copies=fs.readdirSync(downloads);assert.equal(copies.length,2);assert.deepEqual(fs.readFileSync(path.join(downloads,copies[0])),fs.readFileSync(path.join(downloads,copies[1])));
   // A hand-authored draft exercises review/export without installing or calling a model.
   await page.locator('#openCollection').setInputFiles(path.join(folder,'synthetic-multi-meeting-report.json'));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));await page.locator('#prepareReport').click();await page.getByText('Personal model drafts (Python)',{exact:true}).click();
   const reading=async id=>{const [file]=await Promise.all([page.waitForEvent('download'),page.locator('#'+id).click()]);const bytes=fs.readFileSync(await file.path());await Promise.all([...pending]);return {name:file.suggestedFilename(),bytes};};
   const packet=JSON.parse((await reading('downloadDraftInput')).bytes),draft=JSON.parse(fs.readFileSync(path.join(folder,'synthetic-model-draft.json')));assert.equal(packet.context_sha256,draft.context_sha256);Draft.checkOutput(draft,packet);
   await page.locator('#openModelDraft').setInputFiles(path.join(folder,'synthetic-model-draft.json'));await page.waitForFunction(()=>document.querySelector('#modelDraftStatus').textContent.startsWith('Draft opened'));const review=await page.locator('#modelDraftPreview').innerText();assert(review.includes('NO MODEL INFERENCE'));assert(review.includes('Collective statement indicated; national attribution withheld.'));assert(review.includes('No matching source passage.'));
   const word=await reading('downloadModelDraftWord');assert(word.name.endsWith('-draft-review.docx'));assert(word.bytes.length>0);assert.equal(word.bytes.readUInt32LE(0),0x04034b50);
   const html=(await reading('downloadModelDraft')).bytes.toString('utf8');assert(html.includes('FICTIONAL HAND-AUTHORED DRAFT'));assert(html.includes('NO MODEL INFERENCE'));assert(!html.includes('<script'));
   // Rehearse the manual campaign workflow without claiming a user or calendar-client session.
   await page.getByRole('link',{name:'Campaign notebook',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#notebookStatus').textContent.startsWith('Ready.'));await page.locator('#openNotebook').setInputFiles(path.join(folder,'synthetic-campaign-notebook.json'));await page.waitForFunction(()=>document.querySelector('#notebookStatus').textContent.startsWith('Campaign notebook opened'));
   await page.locator('#campaign_notes').fill('Fictional campaign smoke assessment');await page.locator('#contactTransferPanel summary').click();await page.locator('#importContactTransfer').setInputFiles(path.join(folder,'synthetic-contact-transfer.json'));await page.locator('#notebookConfirm[open]').waitFor();assert.equal(await page.locator('#notebookConfirmPreview details').count(),2);await page.locator('#notebookProceed').click();await page.waitForFunction(()=>document.querySelector('#notebookStatus').textContent.startsWith('Added 2 contact profiles'));assert.equal(await page.locator('#campaign_notes').inputValue(),'Fictional campaign smoke assessment');
   await page.getByRole('button',{name:'Edit United States',exact:true}).click();await page.locator('#entry_follow_up_date').fill('2026-11-22');await page.locator('#applyEntry').click();await page.waitForFunction(()=>document.querySelector('#notebookStatus').textContent.startsWith('Country record applied'));const notebook=JSON.parse((await reading('saveNotebook')).bytes),country=notebook.entries.find(e=>e.country==='Kenya');Campaign.validate(notebook,JSON.parse(fs.readFileSync(path.join(root,'site/countries.json'))));assert.equal(notebook.campaign.notes,'Fictional campaign smoke assessment');assert.equal(country.status,'contacted');assert.equal(country.interactions.length,1);assert.equal(notebook.entries.find(e=>e.country==='United States').status,'unrecorded');
   const transfer=JSON.parse((await reading('downloadContactTransfer')).bytes);assert.equal(transfer.entries.flatMap(e=>e.contacts).length,3);assert(!JSON.stringify(transfer).includes('Fictional campaign smoke assessment'));assert(!JSON.stringify(transfer).includes('FICTIONAL earlier conversation'));
   await page.locator('#notebookSearch').fill('FICTIONAL KENYA');assert.equal(await page.locator('#notebookRecords article').count(),1);const contactsCSV=(await reading('downloadNotebookContactCSV')).bytes.toString('utf8');assert(contactsCSV.includes('FICTIONAL US PROFILE 1'));
   await page.locator('#campaignCalendarPanel summary').click();const calendar=(await reading('downloadCampaignCalendar')).bytes.toString('utf8').replace(/\r\n /g,'');assert.equal(calendar.split('BEGIN:VEVENT').length-1,2);assert(calendar.includes('DTSTART;VALUE=DATE:20261121'));assert(calendar.includes('DTSTART;VALUE=DATE:20261122'));assert(!calendar.includes('Fictional campaign smoke assessment'));assert(!calendar.includes('FICTIONAL country-only note'));assert(!calendar.includes('FICTIONAL US PROFILE 1'));assert(!calendar.includes('\r\nATTENDEE:'));assert(!calendar.includes('BEGIN:VALARM'));
   const campaignHTML=(await reading('downloadNotebookHTML')).bytes.toString('utf8');assert(campaignHTML.includes('FICTIONAL US PROFILE 1'));assert(campaignHTML.includes('Fictional campaign smoke assessment'));assert(!campaignHTML.includes('<script'));
   for(const name of ['synthetic-campaign-notebook.json','synthetic-contact-transfer.json'])assert.equal((await page.request.get(origin+'/'+name)).status(),404);
   assert.equal((await page.request.get(origin+'/synthetic-model-draft.json')).status(),404);
   assert.equal((await page.request.get(origin+'/synthetic-collection.json')).status(),404);assert.equal((await page.request.get(origin+'/session-receipt.json')).status(),404);assert.equal((await page.request.post(origin+'/write-notes')).status(),405);
   const blocked=await context.newPage();const response=await blocked.goto('https://example.invalid/usability-network-check');assert.equal(response.status(),403);await blocked.close();assert(counts.blocked_requests>=1);assert(counts.fixture_requests>=3);assert.deepEqual(errors,[]);receipt.status='smoke_passed';
  }else{
   const interrupt=()=>browser.close();process.once('SIGINT',interrupt);
   try{await new Promise(resolve=>{page.once('close',resolve);browser.once('disconnected',resolve);});receipt.status='session_closed';}finally{process.removeListener('SIGINT',interrupt);}
  }
 }catch(error){receipt.status='failed';receipt.error_type=error.name;throw error;}
 finally{
  await Promise.allSettled([...pending]);if(context)await context.close().catch(()=>{});if(browser)await browser.close().catch(()=>{});if(server)await new Promise(resolve=>server.close(resolve));fs.rmSync(publicRoot,{recursive:true,force:true});receipt.finished_at=new Date().toISOString();receipt.counts=counts;receipt.session_error_count=errors.length;write('session-receipt.json',receipt);console.log(JSON.stringify({folder,receipt:'session-receipt.json',status:receipt.status,participant_acceptance:'not_recorded'}));
 }
 return {folder,receipt};
}
if(require.main===module){
 const args=process.argv.slice(2);
 if(args.length===1&&args[0]==='--help')console.log('node tools/reporting_usability.cjs [--fixtures-only | --smoke]\n--fixtures-only creates six fictional JSON files using Node alone: three reporting sources, a paired hand-authored draft, a campaign notebook and a contact-only transfer. Draft request counts are simulated; no model inference is run. Default launches a visible local facilitator browser using Node, Python and the existing Playwright harness; close the session tab to finish. --smoke runs automated headless engineering QA. No mode records human acceptance. Files stay in a private temporary folder outside the repository.');
 else if(args.length>1||args.some(a=>!['--smoke','--fixtures-only'].includes(a))){console.error('Unknown or conflicting option. Use --help.');process.exitCode=2;}
 else (args[0]==='--fixtures-only'?createMaterials().then(result=>console.log(JSON.stringify(result))):run({smoke:args[0]==='--smoke'})).catch(error=>{console.error(error.message);process.exitCode=1;});
}
module.exports={fixtureResponse,run};
