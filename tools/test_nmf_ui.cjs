/* Browser acceptance against a local build or a deployed URL; input stays local. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
  const [site,corpus,review,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});let server;
  let url=site;
  if(!site.startsWith('http')){
    const root=path.resolve(site);
    server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]).replace(/\/$/,'/index.html'));
      if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      try{res.setHeader('Content-Type',({'.js':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch(e){res.writeHead(404).end();}});
    await new Promise(r=>server.listen(0,'127.0.0.1',r));url='http://127.0.0.1:'+server.address().port+'/';
  }
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true}),errors=[],uploads=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()!=='GET')uploads.push({url:r.url(),method:r.method()});});
    await page.goto(url+'#analyze');await page.waitForFunction(()=>document.querySelector('#region').options.length>2);
    await page.locator('details').filter({has:page.locator('#corpusSource')}).locator('summary').first().click();
    await page.locator('#corpusSource').selectOption('import');await page.locator('#corpusFile').setInputFiles(corpus);
    await page.locator('#passagePolicy').selectOption('substantive');await page.locator('#passageReviewFile').setInputFiles(review);
    await page.locator('#topic').fill('');await page.locator('#startDate').fill('2026-09-22');await page.locator('#endDate').fill('2026-09-28');
    for(const e of await page.locator('input[name=method]').all())await e.uncheck();
    await page.locator('#nmfMethod').check();await page.locator('#nmfStability').check();await page.locator('#nmfReplicates').fill('10');
    await page.locator('#runAnalysis').click();await page.locator('#analysisOutput').waitFor({state:'visible',timeout:240000});
    assert.match(await page.locator('#analysisReport').textContent(),/194 of 460 passages/);
    assert.equal(await page.locator('.nmf-component').count(),6);assert.equal(await page.locator('#exportNMF').isVisible(),true);
    await page.locator('.nmf-component summary').first().click();assert.ok(await page.locator('.nmf-component a[href^="https://transcripts.un.org/"]').count()>0);
    await page.locator('.nmf-report').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'nmf-desktop.png')});
    const [data]=await Promise.all([page.waitForEvent('download'),page.locator('#exportResult').click()]);await data.saveAs(path.join(out,'analysis.json'));
    const fit=JSON.parse(fs.readFileSync(path.join(out,'analysis.json')));assert.equal(fit.engine,'browser-descriptive-1.8.0');assert.equal(fit.counts.input,460);assert.equal(fit.counts.matched,194);assert.equal(fit.methods.nmf.stability.attempted,10);
    const [csv]=await Promise.all([page.waitForEvent('download'),page.locator('#exportNMF').click()]);await csv.saveAs(path.join(out,'mixtures.csv'));assert.equal(fs.readFileSync(path.join(out,'mixtures.csv'),'utf8').split('\r\n').length,195);
    const [report]=await Promise.all([page.waitForEvent('download'),page.locator('#exportHTML').click()]);await report.saveAs(path.join(out,'report.html'));const html=fs.readFileSync(path.join(out,'report.html'),'utf8');assert.ok(html.includes('NMF · overlapping'));assert.ok(!/<script\b/i.test(html));
    const [original]=await Promise.all([page.waitForEvent('download'),page.locator('#exportCorpus').click()]);await original.saveAs(path.join(out,'collection.json'));assert.deepEqual(JSON.parse(fs.readFileSync(path.join(out,'collection.json'))),JSON.parse(fs.readFileSync(corpus)));
    await page.locator('#nmfComponents').fill('4');assert.equal(await page.locator('#exportResult').isDisabled(),true);
    await page.locator('#runAnalysis').click();await page.locator('#cancelAnalysis').click();await page.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('cancelled'));assert.equal(await page.locator('#analysisOutput').isVisible(),false);
    const bad=JSON.parse(fs.readFileSync(review));bad.corpus_sha256='0'.repeat(64);fs.writeFileSync(path.join(out,'wrong-review.json'),JSON.stringify(bad));await page.locator('#passageReviewFile').setInputFiles(path.join(out,'wrong-review.json'));await page.locator('#runAnalysis').click();await page.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('does not match'));assert.equal(await page.locator('#analysisOutput').isVisible(),false);
    await page.setViewportSize({width:390,height:900});await page.locator('#nmfMethod').scrollIntoViewIfNeeded();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(out,'controls-mobile.png')});
    await page.goto(url+'nmf-audit.html');assert.equal(await page.locator('.nmf-report').count(),9);assert.match(await page.locator('body').textContent(),/460 explicit passage-type decisions/);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(out,'audit-mobile.png')});
    await page.setViewportSize({width:1440,height:1000});await page.locator('section').nth(2).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'audit-desktop.png')});
    await page.goto(url+'passage-audit.html');assert.match(await page.locator('body').textContent(),/460 of 460 records/);assert.equal(await page.locator('table').first().locator('tbody tr').count(),30);
    assert.deepEqual(errors,[]);assert.deepEqual(uploads,[]);
    const result={status:'PASS',source:url,reviewed_subset:194,original_records:460,components:6,grouped_refits:10,source_links:true,report_json_csv_original_exports:true,stale_exports_blocked:true,cancellation:true,wrong_review_rejected:true,mobile_overflow:false,browser_errors:errors,uploads};
    fs.writeFileSync(path.join(out,'validation.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
  }finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
