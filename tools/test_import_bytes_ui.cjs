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
  const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
  const records=Array.from({length:4},(_,i)=>{const text='Synthetic passage '+['energy climate','health research','chair procedure','thank delegates'][i];return {id:'fixture-'+i,text,text_sha256:sha(text),date:'2026-09-22',country:'Fixture',region:'Unmapped',language:'en',scope:'general_debate',meeting:'Fixture meeting',source_url:'https://example.org/'+i};});
  const raw=Buffer.from('\uFEFF'+JSON.stringify({schema:'un.browser.corpus.v1',records,coverage:[]},null,2).replace(/\n/g,'\r\n'));
  const review=Buffer.from(JSON.stringify({schema:'un.passage-type-review.v1',corpus_sha256:sha(raw),choices:records.map((r,i)=>({id:r.id,text_sha256:r.text_sha256,type:i<2?'substantive_speech':'procedure',confirmed:true,reviewer:'Synthetic test',reviewed_at:'2020-01-01T00:00:00Z'}))}));
  const b=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});
  try{const p=await b.newPage({acceptDownloads:true});const errors=[];p.on('pageerror',e=>errors.push(e.message));await p.goto(url+'#analyze');await p.waitForFunction(()=>document.querySelector('#region').options.length>2);
    await p.locator('details').filter({has:p.locator('#corpusSource')}).locator('summary').first().click();await p.locator('#corpusSource').selectOption('import');
    await p.locator('#corpusFile').setInputFiles({name:'fixture.json',mimeType:'application/json',buffer:raw});await p.locator('#passagePolicy').selectOption('substantive');await p.locator('#passageReviewFile').setInputFiles({name:'fixture-review.json',mimeType:'application/json',buffer:review});
    await p.locator('#topic').fill('');await p.locator('#startDate').fill('2026-09-22');await p.locator('#endDate').fill('2026-09-28');await p.locator('#runAnalysis').click();await p.locator('#analysisOutput').waitFor({state:'visible'});assert.match(await p.locator('#analysisReport').textContent(),/2 of 4 passages/);
    const [download]=await Promise.all([p.waitForEvent('download'),p.locator('#exportCorpus').click()]);const saved=path.join(out,'synthetic-original.json');await download.saveAs(saved);assert.deepEqual(fs.readFileSync(saved),raw);
    await p.locator('#corpusFile').setInputFiles(saved);await p.locator('#runAnalysis').click();await p.locator('#analysisOutput').waitFor({state:'visible'});assert.match(await p.locator('#analysisReport').textContent(),/2 of 4 passages/);assert.deepEqual(errors,[]);
    const result={status:'PASS',source:url,synthetic_fixture:true,bom_crlf_indentation_preserved:true,all_original_records_retained:true,export_reimport_same_review_valid:true,browser_errors:errors};fs.writeFileSync(path.join(out,'validation.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
  }finally{await b.close();if(server)await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
