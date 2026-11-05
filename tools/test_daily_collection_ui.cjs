/* Browser acceptance uses artificial inventory/transcripts only; never live UN sources. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const [site='site',out='work/daily-collection-browser']=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
 let server,browser;let url=site;
 try{
  if(!site.startsWith('http')){const root=path.resolve(site);server=http.createServer((req,res)=>{
   const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]).replace(/\/$/,'/index.html'));
   if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
   try{res.setHeader('Content-Type',({'.js':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch{res.writeHead(404).end();}
  });await new Promise(r=>server.listen(0,'127.0.0.1',r));url='http://127.0.0.1:'+server.address().port+'/';}
  browser=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});
  const p=await browser.newPage({acceptDownloads:true,timezoneId:'Asia/Tokyo'}),errors=[],calls=[];
  p.on('pageerror',e=>errors.push(e.message));await p.clock.setFixedTime(new Date('2026-09-25T02:30:00Z'));
  const date='2026-09-24';
  const meeting=(name,extra={})=>({slug:'asset/synthetic/'+name,title:'Synthetic '+name,date,pageUrl:'/en/asset/synthetic/'+name,jsonUrl:'/en/asset/synthetic/'+name+'.json',hasTranscript:true,...extra});
  const meetings=[meeting('available'),meeting('pending',{hasTranscript:false,transcriptStatus:'pending'}),meeting('unavailable',{hasTranscript:false}),meeting('failed')];
  let fail=true,refresh=false,unRequests=0;
  await p.route('https://transcripts.un.org/**',async route=>{
   unRequests++;const u=new URL(route.request().url());let data;
   if(u.pathname==='/en/meetings.json'){const rows=refresh?[...meetings,meeting('newly-published')]:meetings;data={page:1,total:rows.length,hasMore:false,meetings:rows};}
   else{calls.push(u.pathname);const m=[...meetings,meeting('newly-published')].find(m=>m.jsonUrl===u.pathname);assert.ok(m,'Only fixture transcript requested');if(fail&&m.slug.endsWith('/failed'))return route.fulfill({status:503,headers:{'access-control-allow-origin':'*'},body:'Synthetic failure'});
    data={video:{slug:m.slug,date},transcript:{language:'en',data:[{speaker:{affiliation:'Kenya'},paragraphs:[{sentences:[{text:'We support humanitarian access and civilian protection. Synthetic evidence '+m.title+'.'}]}]}]}};}
   await route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(data)});
  });
  await p.goto(url+'#analyze');await p.waitForFunction(()=>document.querySelector('#region').options.length>2);
  assert.equal(await p.locator('#startDate').inputValue(),date,'Reporting day must use New York rather than browser timezone');assert.equal(await p.locator('#endDate').inputValue(),date);assert.equal(await p.locator('#meetingScope').inputValue(),'all');
  await p.locator('#yesterdayDate').click();assert.equal(await p.locator('#startDate').inputValue(),'2026-09-23');assert.equal(await p.locator('#endDate').inputValue(),'2026-09-23');
  await p.locator('#todayDate').click();assert.equal(await p.locator('#startDate').inputValue(),date);await p.locator('#startDate').fill('2026-09-22');assert.equal(await p.locator('#startDate').inputValue(),'2026-09-22');await p.locator('#todayDate').click();
  await p.locator('#meetingSelectionMode').selectOption('single');assert.equal(await p.locator('#todayDate').isDisabled(),true);assert.equal(await p.locator('#yesterdayDate').isDisabled(),true);await p.locator('#meetingSelectionMode').selectOption('range');assert.equal(await p.locator('#todayDate').isEnabled(),true);assert.equal(await p.locator('#yesterdayDate').isEnabled(),true);
  await p.locator('#runAnalysis').click();await p.locator('#analysisOutput').waitFor({state:'visible'});
  assert.match(await p.locator('#analysisStatus').textContent(),/Partial collection/);
  const download=async(id,name)=>{const [d]=await Promise.all([p.waitForEvent('download'),p.locator('#'+id).click()]);const file=path.join(out,name);await d.saveAs(file);return {file,value:JSON.parse(fs.readFileSync(file,'utf8'))};};
  const first=await download('exportCorpus','initial-synthetic.json');assert.deepEqual(new Set(first.value.coverage.map(r=>r.transcript_status)),new Set(['available','pending','unavailable','failed']));assert.equal(first.value.records.length,1);
  const visible=await p.locator('#analysisReport').innerText();for(const label of ['Available','Pending','Unavailable','Failed'])assert.match(visible,new RegExp(label,'i'));assert.match(visible,/2026|Sep|September/);assert.ok(first.value.collection.checked_at);assert.match(await p.locator('#collectionCheckedAt').innerText(),new RegExp(first.value.collection.checked_at.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));assert.match(await p.locator('#transcriptStatusCounts').innerText(),/Available: 1.*Pending: 1.*Unavailable: 1.*Failed: 1/);
  for(const r of first.value.records){assert.ok(r.source_id);assert.ok(r.source_version);assert.match(r.raw_sha256,/^[a-f0-9]{64}$/);assert.ok(r.json_pointer);}
  fail=false;calls.length=0;await p.locator('#retryCollection').click();await p.waitForFunction(()=>!document.querySelector('#runAnalysis').disabled&&document.querySelector('#analysisOutput').hidden===false);
  assert.deepEqual(calls,[meetings[3].jsonUrl]);const retried=await download('exportCorpus','retried-synthetic.json');assert.equal(retried.value.records.length,2);assert.deepEqual(retried.value.records[0],first.value.records[0]);
  refresh=true;calls.length=0;await p.locator('#refreshCollection').click();await p.waitForFunction(()=>!document.querySelector('#runAnalysis').disabled&&document.querySelector('#analysisOutput').hidden===false);
  assert.deepEqual(calls,[meeting('newly-published').jsonUrl],'Refresh must retain successful source responses');const fresh=await download('exportCorpus','refreshed-synthetic.json');assert.equal(fresh.value.records.length,3);assert.deepEqual(fresh.value.records[0],first.value.records[0]);assert.equal(fresh.value.collection.selected_meetings,5);
  const report=await download('exportResult','analysis-synthetic.json');assert.deepEqual(report.value.collection,fresh.value.collection);
  await p.setViewportSize({width:390,height:844});await p.screenshot({path:path.join(out,'daily-mobile-synthetic.png'),fullPage:true});assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+2),'Mobile page must fit the viewport');await p.setViewportSize({width:1280,height:900});
  const before=unRequests;await p.evaluate(()=>{for(let e=document.querySelector('#corpusSource');e;e=e.parentElement)if(e.tagName==='DETAILS')e.open=true;});
  await p.locator('#corpusSource').selectOption('import');await p.locator('#corpusFile').setInputFiles(fresh.file);await p.locator('#runAnalysis').click();await p.locator('#analysisOutput').waitFor({state:'visible'});assert.equal(unRequests,before,'Saved source replay must make no UN requests');
  const reopened=await download('exportResult','reopened-analysis-synthetic.json');assert.deepEqual(reopened.value.collection,report.value.collection);assert.deepEqual(reopened.value.matched,report.value.matched);assert.deepEqual(reopened.value.counts,report.value.counts);
  const rejectedImport=async(value,pattern)=>{await p.locator('#corpusFile').setInputFiles({name:'tampered.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});await p.locator('#runAnalysis').click();await p.waitForFunction(()=>!document.querySelector('#runAnalysis').disabled);assert.match(await p.locator('#analysisStatus').innerText(),pattern);assert.equal(await p.locator('#analysisOutput').isVisible(),false);assert.equal(unRequests,before);};
  assert.ok(fresh.value.provenance.sources.every(s=>typeof s.raw==='string'));
  const rawTampered=JSON.parse(JSON.stringify(fresh.value));rawTampered.provenance.sources[0].raw+=' ';await rejectedImport(rawTampered,/raw source hash mismatch/);
  const rebound=JSON.parse(JSON.stringify(fresh.value));rebound.records[0].text+=' altered';rebound.records[0].text_sha256=crypto.createHash('sha256').update(rebound.records[0].text).digest('hex');await rejectedImport(rebound,/does not match its raw source passage/);
  const tampered=JSON.parse(JSON.stringify(fresh.value));tampered.records[0].text+=' altered';await p.locator('#corpusFile').setInputFiles({name:'tampered.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(tampered))});await p.locator('#runAnalysis').click();await p.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('hash mismatch'));assert.equal(await p.locator('#analysisOutput').isVisible(),false);assert.equal(unRequests,before);assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',synthetic_only:true,checks:['New York current-day default independent of browser timezone','Today/Yesterday/date pickers and single-meeting mode safeguards','all inventory daily scope','four source states and partial report','retry skips successful sources','explicit refresh discovers new sources without re-fetching successes','visible collection status/time and mobile fit','saved identifiers/versions/hashes','offline replay preserves source metadata and analysis counts','tampered raw bytes, rebound excerpt and text hash refused'],browser_errors:errors}));
 }finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
