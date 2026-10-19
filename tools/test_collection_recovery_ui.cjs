/* Synthetic transport check: preserve BOM, CRLF and indentation with the review hash. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
  const [site,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});let server,url=site;
  if(!site.startsWith('http')){const root=path.resolve(site);server=http.createServer((req,res)=>{
    const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]).replace(/\/$/,'/index.html'));
    if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
    try{res.setHeader('Content-Type',({'.js':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch(e){res.writeHead(404).end();}
  });await new Promise(r=>server.listen(0,'127.0.0.1',r));url='http://127.0.0.1:'+server.address().port+'/';}

  let b;
  try {
    b=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});
    const p=await b.newPage({acceptDownloads:true}),errors=[],calls=[];
    p.on('pageerror',e=>errors.push(e.message));
    const date='2026-09-24',meetings=['one','two'].map(name=>({slug:'asset/synthetic/'+name,title:'Synthetic '+name,date,pageUrl:'/en/asset/synthetic/'+name,jsonUrl:'/en/asset/synthetic/'+name+'.json',hasTranscript:true}));
    let failed=true, delaySecond=false, releaseSecond=null, unRequests=0;
    await p.route('https://transcripts.un.org/**',async route=>{
      unRequests++;const u=new URL(route.request().url());let data;
      if(u.pathname==='/en/meetings.json')data={page:1,total:2,hasMore:false,meetings};
      else {calls.push(u.pathname);const m=meetings.find(m=>m.jsonUrl===u.pathname);if(!m)throw Error('Unselected source requested');
        if(delaySecond&&m===meetings[1]) await new Promise(resolve=>{releaseSecond=resolve;});
        if(failed&&m===meetings[1])return route.fulfill({status:503,headers:{'access-control-allow-origin':'*'},body:'Fixture outage'});
        data={video:{slug:m.slug,date},transcript:{language:'en',data:[{paragraphs:[{sentences:[{text:'Synthetic climate change and sustainable development evidence '+m.title}]}]}]}};
      }
      await route.fulfill({status:200,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(data)});
    });
    await p.goto(url+'#analyze');await p.waitForFunction(()=>document.querySelector('#region').options.length>2);
    await p.locator('#topic').fill('');await p.locator('#startDate').fill(date);await p.locator('#endDate').fill(date);await p.locator('#meetingScope').selectOption('all');
    await p.evaluate(()=>{window.realAnalyze=UNAnalysis.analyze;UNAnalysis.analyze=async()=>{throw Error('Synthetic optional analysis failure');};});
    await p.locator('#runAnalysis').click();await p.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('Synthetic optional analysis failure'));
    assert.equal(await p.locator('#analysisOutput').isVisible(),false);assert.equal(await p.locator('#saveRetainedCorpus').isEnabled(),true);assert.equal(await p.locator('#retryCollection').isEnabled(),true);
    const save=async name=>{const [d]=await Promise.all([p.waitForEvent('download'),p.locator('#saveRetainedCorpus').click()]);const file=path.join(out,name);await d.saveAs(file);return JSON.parse(fs.readFileSync(file,'utf8'));};
    const first=await save('partial-synthetic.json');assert.equal(first.records.length,1);
    // Form edits do not invalidate the saved source or alter the retry's original selection.
    await p.locator('#startDate').fill('2026-09-25');failed=false;calls.length=0;await p.locator('#retryCollection').click();
    await p.waitForFunction(()=>!document.querySelector('#runAnalysis').disabled&&document.querySelector('#collectionRecoveryStatus').textContent.startsWith('2 source segments'));
    assert.deepEqual(calls,[meetings[1].jsonUrl]);const retried=await save('retried-synthetic.json');assert.equal(retried.collection.start,date);assert.equal(retried.records.length,2);assert.deepEqual(retried.records[0],first.records[0]);
    await p.locator('#startDate').fill(date);await p.evaluate(()=>{UNAnalysis.analyze=window.realAnalyze;});calls.length=0;await p.locator('#analyzeRetainedCorpus').click();await p.locator('#analysisOutput').waitFor({state:'visible'});assert.deepEqual(calls,[]);assert.equal(await p.locator('#retryCollection').isDisabled(),true);assert.deepEqual(errors,[]);
    delaySecond=true;await p.locator('#runAnalysis').click();
    await p.waitForFunction(()=>document.querySelector('#collectionRecoveryStatus').textContent.startsWith('1 source segments')&&!document.querySelector('#cancelAnalysis').disabled);
    await p.locator('#cancelAnalysis').click();if(releaseSecond)releaseSecond();
    await p.waitForFunction(()=>!document.querySelector('#runAnalysis').disabled&&document.querySelector('#analysisStatus').textContent.startsWith('Cancelled.'));
    assert.equal(await p.locator('#analysisOutput').isVisible(),false);const cancelled=await save('cancelled-synthetic.json');assert.equal(cancelled.records.length,1);assert.equal(await p.locator('#retryCollection').isEnabled(),true);assert.deepEqual(errors,[]);
    await p.evaluate(()=>{for(let e=document.querySelector('#corpusSource');e;e=e.parentElement)if(e.tagName==='DETAILS')e.open=true;UNAnalysis.analyze=async()=>{throw Error('Synthetic import analysis failure');};});
    const importedBytes=Buffer.from('\uFEFF'+JSON.stringify(cancelled,null,2).replace(/\n/g,'\r\n'));
    await p.locator('#corpusSource').selectOption('import');await p.locator('#corpusFile').setInputFiles({name:'import-fixture.json',mimeType:'application/json',buffer:importedBytes});
    await p.locator('#runAnalysis').click();await p.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('Synthetic import analysis failure'));
    const [importDownload]=await Promise.all([p.waitForEvent('download'),p.locator('#saveOriginalCollection').click()]);const importedPath=path.join(out,'recovered-import.json');await importDownload.saveAs(importedPath);assert.deepEqual(fs.readFileSync(importedPath),importedBytes);
    const invalid=JSON.parse(JSON.stringify(cancelled));invalid.records[0].text+=' corrupted';
    await p.locator('#corpusFile').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(invalid))});await p.locator('#runAnalysis').click();await p.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('Text hash mismatch'));
    const [validDownload]=await Promise.all([p.waitForEvent('download'),p.locator('#saveOriginalCollection').click()]);await validDownload.saveAs(importedPath);assert.deepEqual(fs.readFileSync(importedPath),importedBytes);assert.deepEqual(errors,[]);
    const mismatch=JSON.parse(JSON.stringify(cancelled));Object.assign(mismatch.collection,{selection_mode:'single_meeting',selected_meeting_slug:'asset/synthetic/different',selected_meeting_title:'Unverified meeting label',selected_meeting_date:date});
    await p.evaluate(()=>{UNAnalysis.analyze=window.realAnalyze;});await p.locator('#corpusFile').setInputFiles({name:'mismatch.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(mismatch))});await p.locator('#runAnalysis').click();await p.locator('#analysisOutput').waitFor({state:'visible'});
    const mismatchReport=await p.locator('#analysisReport').textContent();assert.match(mismatchReport,/saved single-meeting label could not be verified/);assert.ok(!mismatchReport.includes('Only this meeting was collected'));assert.ok(!mismatchReport.includes('whole recorded meeting'));assert.ok(!mismatchReport.includes('Unverified meeting label'));assert.match(mismatchReport,/What the collected passages show/);assert.deepEqual(errors,[]);
    const [rangeDownload]=await Promise.all([p.waitForEvent('download'),p.locator('#exportHTML').click()]);const rangePath=path.join(out,'range-report.html');await rangeDownload.saveAs(rangePath);const rangeHTML=fs.readFileSync(rangePath,'utf8');assert.match(rangeHTML,/What the collected passages show/);assert.ok(rangeHTML.includes(cancelled.records[0].source_url));assert.match(rangeHTML,/Subjects and source evidence/);
    const reopened=JSON.parse(JSON.stringify(retried));const slug=meetings[0].slug;Object.assign(reopened.collection,{selection_mode:'single_meeting',selected_meeting_slug:slug,selected_meeting_title:'Synthetic saved meeting',selected_meeting_date:date,selected_meetings:1,selected_meeting_slugs:[slug]});
    reopened.records.forEach((record,index)=>Object.assign(record,{id:slug+'#'+index,meeting_slug:slug,meeting:'Synthetic saved meeting',country:index?'France':'Kenya',region:index?'Europe & Eurasia':'Africa',attribution:{country_status:'registry_mapped',basis:'source_affiliation_country_registry'}}));
    reopened.passage_labels=require('../site/passage-labels').snapshot(reopened.records);
    reopened.coverage=[{...reopened.coverage.find(row=>row.status==='collected'),slug,status:'collected',segments:2}];const beforeReopen=unRequests;
    await p.locator('#corpusFile').setInputFiles({name:'saved-single.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(reopened))});await p.locator('#region').selectOption('Africa');await p.locator('#runAnalysis').click();await p.locator('#analysisOutput').waitFor({state:'visible'});assert.equal(unRequests,beforeReopen,'Saved meeting reopen must not fetch UN sources');
    assert.equal(await p.locator('.meeting-quick-read').count(),1);assert.match(await p.locator('#analysisReport h2').textContent(),/Synthetic saved meeting/);
    const [singleResultDownload]=await Promise.all([p.waitForEvent('download'),p.locator('#exportResult').click()]);const singleResultPath=path.join(out,'reopened-single-analysis.json');await singleResultDownload.saveAs(singleResultPath);const singleResult=JSON.parse(fs.readFileSync(singleResultPath,'utf8'));assert.equal(singleResult.counts.eligible,1);assert.equal(singleResult.quick_reader.stats.source_segments,2);assert.equal(singleResult.quick_reader.meeting_slug,slug);assert.deepEqual(errors,[]);
    console.log(JSON.stringify({status:'PASS',synthetic_only:true,checks:['source export survives analysis failure','retry skips complete source','retry retains original date selection after form edit','successful source bytes preserved','retained analysis succeeds without recollection','cancellation hides partial report and retains downloadable complete responses','validated import bytes retained after analysis failure','invalid import cannot replace trusted retained source','unverified single-meeting metadata produces qualified range report','descriptive briefing renders for imported range collection','standalone range HTML retains briefing and source links','saved single-meeting reopen restores quickreader without UN requests','regional detailed analysis preserves whole-meeting quickreader source count'],browser_errors:errors}));
  } finally {if(b)await b.close();if(server)await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
