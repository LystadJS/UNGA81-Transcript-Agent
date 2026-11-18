/* Personal facilitator tool. The public application has no dependency on this. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),http=require('node:http'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const F=require('../tests/meeting_report_fixture.cjs'),Collector=require('../site/collector.js'),Core=require('../site/meeting-report-core.js'),root=path.resolve(__dirname,'..');
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
 const report=Core.build(corpora,meetings.map(m=>m.slug),{mission:'Fictional training mission',title:'Fictional two-meeting report'}),addition=Core.build([corpora[1]],[meetings[1].slug],{mission:'Other fictional mission',title:'Fictional additional report',notes:'Fictional incoming assessment; leave this out of the current report.'});
 return {'synthetic-collection.json':corpora[0],'synthetic-multi-meeting-report.json':Core.savedReport(report,corpora),'synthetic-additional-report.json':Core.savedReport(addition,[corpora[1]])};
}
const writePrivate=(folder,name,value)=>fs.writeFileSync(path.join(folder,name),JSON.stringify(value,null,2)+'\n',{mode:0o600});
async function createMaterials(){
 const files=await materials(JSON.parse(fs.readFileSync(path.join(root,'site/countries.json')))),folder=fs.mkdtempSync(path.join(os.tmpdir(),'un-reporting-session-'));fs.chmodSync(folder,0o700);
 try{for(const [name,value] of Object.entries(files))writePrivate(folder,name,value);}catch(error){fs.rmSync(folder,{recursive:true,force:true});throw error;}
 return {folder,files:Object.keys(files),fixture_date:F.date,mode:'fixture_generation',participant_acceptance:'not_recorded'};
}
async function run({smoke=false}={}){
 const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
 const material=await createMaterials(),folder=material.folder;
 const publicRoot=path.join(folder,'public'),downloads=path.join(folder,'downloads');fs.mkdirSync(downloads,{mode:0o700});
 let server,browser,context,origin;const pending=new Set(),errors=[],counts={fixture_requests:0,blocked_requests:0,downloads:0};
 const receipt={schema:'un.reporting-usability-session.v1',mode:smoke?'engineering_smoke':'facilitated',participant_acceptance:'not_recorded',started_at:new Date().toISOString(),fixture_date:F.date,source_commit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),source_dirty:!!execFileSync('git',['status','--porcelain'],{cwd:root,encoding:'utf8'}).trim(),application_release:JSON.parse(fs.readFileSync(path.join(root,'site/release.json'))).browser_engine,status:'incomplete'};
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
  await context.addInitScript(()=>document.addEventListener('DOMContentLoaded',()=>{const banner=document.createElement('p');banner.className='notice';banner.setAttribute('role','note');banner.textContent='FICTIONAL USABILITY SESSION — Synthetic sources only. Source-shaped links do not identify real statements. No human acceptance is recorded automatically.';document.body.prepend(banner);document.title='[FICTIONAL SESSION] '+document.title;}));
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
  console.log(JSON.stringify({folder,url:page.url(),fixture_date:F.date,files:material.files,mode:receipt.mode,participant_acceptance:'not_recorded'}));
  if(smoke){
   await page.locator('#openCollection').setInputFiles(path.join(folder,'synthetic-collection.json'));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));
   await page.locator('#analystNotes').fill('Fictional smoke assessment');await page.locator('#prepareReport').click();
   await page.locator('#meetingDate').fill(F.date);await page.locator('#findMeetings').click();await page.waitForFunction(()=>document.querySelectorAll('#inventory input').length===2);await page.locator('#inventory input').last().check();await page.locator('#addSelectedMeetings').click();await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Transcripts added:'));assert.equal(await page.locator('#analystNotes').inputValue(),'Fictional smoke assessment');assert.equal(await page.locator('#loadedMeetings input:checked').count(),2);
   await page.locator('#prepareReport').click();const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#saveReport').click()]);await download.path();await Promise.all([...pending]);
   const saved=JSON.parse(fs.readFileSync(path.join(downloads,path.basename(download.suggestedFilename()))));assert.equal(saved.settings.notes,'Fictional smoke assessment');assert.equal(saved.corpora.length,2);await Core.openSaved(saved,JSON.parse(fs.readFileSync(path.join(root,'site/reporting-exclusions.json'))),JSON.parse(fs.readFileSync(path.join(root,'site/countries.json'))));
   const [again]=await Promise.all([page.waitForEvent('download'),page.locator('#saveReport').click()]);await again.path();await Promise.all([...pending]);const copies=fs.readdirSync(downloads);assert.equal(copies.length,2);assert.deepEqual(fs.readFileSync(path.join(downloads,copies[0])),fs.readFileSync(path.join(downloads,copies[1])));
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
 if(args.length===1&&args[0]==='--help')console.log('node tools/reporting_usability.cjs [--fixtures-only | --smoke]\n--fixtures-only creates the three JSON files using Node alone. Default launches a visible local facilitator browser using Node, Python and the existing Playwright harness; close the reporting tab to finish. --smoke runs automated headless engineering QA. No mode records human acceptance. Files stay in a private temporary folder outside the repository.');
 else if(args.length>1||args.some(a=>!['--smoke','--fixtures-only'].includes(a))){console.error('Unknown or conflicting option. Use --help.');process.exitCode=2;}
 else (args[0]==='--fixtures-only'?createMaterials().then(result=>console.log(JSON.stringify(result))):run({smoke:args[0]==='--smoke'})).catch(error=>{console.error(error.message);process.exitCode=1;});
}
module.exports={fixtureResponse,run};
