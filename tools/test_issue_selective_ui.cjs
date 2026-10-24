/* Actual-browser CI fixture only: no original sources or empirical labels. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright'),R=require('../site/issue-report');
const directory=path.resolve(process.argv[2]||'site'),snapshotId='fictional-selective-ui';
const source=(id,body,countries)=>({id,revision:'one',published_date:'2026-10-01',body,family:'un_statement',countries,url:'https://example.invalid/'+id});
const observation=(id,source,country,policy)=>({id,source_id:source,source_revision:'one',country,date:'2026-10-01',policy,context:'sudan',stance:country==='Kenya'?'qualified':'support',qualifications:country==='Kenya'?['Only with consent']:[],attribution:'national',review_state:'assistant_provisional'});
const selectedSource=source('access-SC','SC',['Kenya','United States']),otherSource=source('other-SC','SC',['Ghana']),gaSource=source('access-GA','GA_C3',['Nigeria']);
const empty={schema:'un.issue-history.shard.v1',snapshot_id:snapshotId,sources:[],observations:[],votes:[]};
const definitions=[
 {id:'access-sc',policy:'humanitarian_access',body:'SC',sources:[selectedSource],observations:[observation('kenya','access-SC','Kenya','humanitarian_access'),observation('us','access-SC','United States','humanitarian_access')]},
 {id:'other-sc',policy:'civilian_protection',body:'SC',sources:[otherSource],observations:[observation('ghana-other','other-SC','Ghana','civilian_protection')]},
 {id:'access-ga',policy:'humanitarian_access',body:'GA_C3',sources:[gaSource],observations:[observation('nigeria','access-GA','Nigeria','humanitarian_access')]},
 {id:'roster-sc',policy:'_roster',body:'SC',roster:[{date:'2026-10-01',body:'SC',family:'un_statement',countries:['Kenya','Ghana','United States'],source_count:2}]},
 {id:'roster-ga',policy:'_roster',body:'GA_C3',roster:[{date:'2026-10-01',body:'GA_C3',family:'un_statement',countries:['Nigeria'],source_count:1}]}
];
const bytes=new Map(),manifest={schema:'un.issue-history.manifest.v1',snapshot_id:snapshotId,selection_protocol:'policy-year-body-v1',shards:[]};
for(const item of definitions){const shard={...empty,...item};delete shard.policy;delete shard.body;delete shard.id;const content=Buffer.from(JSON.stringify(shard)),url=item.id+'.json';bytes.set('/'+url,content);manifest.shards.push({id:item.id,url,year:'2026',body:item.body,policy:item.policy,bytes:content.length,sha256:crypto.createHash('sha256').update(content).digest('hex')});}
const requested=[];let manifestRequests=0;
(async()=>{const server=http.createServer((req,res)=>{const url=req.url.split('?')[0];res.setHeader('Cache-Control','no-store');const json=value=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(value));};
 if(url==='/issue-history-config.json')return json({schema:'un.issue-history.config.v1',status:'ready',manifest_url:'manifest-fixture.json'});
 if(url==='/manifest-fixture.json'){manifestRequests++;return json(manifest);}
 if(bytes.has(url)){requested.push(url);res.setHeader('Content-Type','application/json');return res.end(bytes.get(url));}
 const file=path.resolve(directory,'.'+decodeURIComponent(url));if(!file.startsWith(directory+path.sep))return res.writeHead(403).end();try{res.setHeader('Content-Type',({'.js':'text/javascript','.html':'text/html','.css':'text/css'})[path.extname(file)]||'application/json');res.end(fs.readFileSync(file));}catch{return res.writeHead(404).end();}});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));let browser;
 try{browser=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('http://127.0.0.1:'+server.address().port+'/issue-archive.html');await page.waitForFunction(()=>document.getElementById('archiveCoverage').textContent.includes('Historical archive available'));
 await page.locator('#archiveStart').fill('2026-10-01');await page.locator('#archiveEnd').fill('2026-10-23');await page.locator('#archiveTopic').fill('Humanitarian access');await page.locator('#archiveBody').selectOption('SC');await page.locator('details').first().locator('summary').click();await page.locator('#archiveAsOf').fill('2026-10-23');
 await page.locator('#archiveRun').click();await page.waitForFunction(()=>document.getElementById('archiveStatus').textContent.startsWith('Report ready.'));
 assert.deepEqual([...requested].sort(),['/access-sc.json','/roster-sc.json'],'UI requests selected policy/body plus independent country roster only');
 assert.equal(await page.locator('#archiveIssueSummary').isVisible(),true);assert.equal(await page.locator('#archiveIssueSummary').getByRole('heading',{name:'Issue overview',exact:true}).count(),1);
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#archiveSave').click()]);const saved=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
 const full={manifest,sources:[selectedSource,otherSource,gaSource],observations:definitions.flatMap(d=>d.observations||[]),votes:[]},expected=R.build(full,saved.inputs);
 for(const key of ['roster','questions','coverage'])assert.deepEqual(saved.results[key],expected[key],'browser selective '+key+' equals full-fixture report');
 assert.equal(saved.results.questions[0].population,2);assert.equal(saved.results.questions[0].counts.missing,1);
 assert.equal(saved.results.issue_summary.schema,'un.issue-summary.v1');const summary=saved.results.issue_summary,section=summary.sections.find(s=>s.policy_id==='humanitarian_access'&&s.context_id==='sudan');assert.ok(section.gaps.unknown_countries.includes('Ghana'));const qualified=section.groups.find(g=>g.state==='qualified').countries.find(c=>c.country==='Kenya');assert.ok(qualified.qualifications.includes('Only with consent'));assert.ok(qualified.source_references.some(s=>s.source_id==='access-SC'&&s.observation_id==='kenya'&&s.url==='https://example.invalid/access-SC'));assert.match(await page.locator('#archiveOutput').innerText(),/Only with consent/);
 // Exercise prefetch validation beyond the normal HTML length guard.
 const previousHTML=await page.locator('#archiveOutput').innerHTML(),previousRequests=manifestRequests;
 await page.locator('#archiveTopic').evaluate(input=>input.removeAttribute('maxlength'));
 await page.locator('#archiveTopic').fill('Humanitarian access '+('safe '.repeat(500)));
 await page.locator('#archiveRun').click();await page.waitForFunction(()=>document.getElementById('archiveStatus').textContent.startsWith('Could not generate report:'));
 assert.equal(manifestRequests,previousRequests,'overlong topic is rejected before historical manifest retrieval');
 assert.equal(await page.locator('#archiveOutput').innerHTML(),previousHTML,'invalid new topic preserves last valid report');

 const reopened=await context.newPage();await reopened.goto('http://127.0.0.1:'+server.address().port+'/issue-archive.html');await reopened.locator('details').first().locator('summary').click();await reopened.locator('#archiveOpen').setInputFiles({name:'selective-saved.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(saved))});await reopened.waitForFunction(()=>document.getElementById('archiveStatus').textContent.startsWith('Saved report reopened'));
 assert.match(await reopened.locator('#archiveOutput').innerText(),/Ghana/);assert.equal(await reopened.locator('#archiveBody').inputValue(),'SC');
 assert.equal(await reopened.locator('#archiveIssueSummary').isVisible(),true);
 const [again]=await Promise.all([reopened.waitForEvent('download'),reopened.locator('#archiveSave').click()]);const roundtrip=JSON.parse(fs.readFileSync(await again.path(),'utf8'));assert.deepEqual(roundtrip,saved,'reopening preserves frozen selective report and all stored provenance');assert.deepEqual(roundtrip.results.issue_summary,summary,'selective issue summary reopens exactly, including unknown-country gaps and qualified source references');assert.match(await reopened.locator('#archiveOutput').innerText(),/Only with consent/);
 const [htmlDownload]=await Promise.all([reopened.waitForEvent('download'),reopened.locator('#archiveHTML').click()]);const html=fs.readFileSync(await htmlDownload.path(),'utf8');assert.ok(!/<script\b/i.test(html),'standalone briefing remains script free');assert.ok(html.includes('Content-Security-Policy'));assert.ok(html.includes('Only with consent'));assert.ok(html.includes('https://example.invalid/access-SC'));
 assert.deepEqual(errors,[]);console.log('PASS actual-browser fictional selective fetch, independent unknown-country roster, full-report parity and frozen save/reopen');
 }finally{await browser?.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1;});
