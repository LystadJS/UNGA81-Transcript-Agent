/* Real reviewed input stays on this machine; the published page receives no upload. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
  const [site,bundleFile,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});let server,url=site;
  if(!site.startsWith('http')){
    const root=path.resolve(site);server=http.createServer((req,res)=>{
      const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]).replace(/\/$/,'/index.html'));
      if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      try{res.setHeader('Content-Type',({'.js':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch(e){res.writeHead(404).end();}
    });await new Promise(r=>server.listen(0,'127.0.0.1',r));url='http://127.0.0.1:'+server.address().port+'/';
  }
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true}),errors=[],uploads=[],external=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()!=='GET')uploads.push(r.url());if(new URL(r.url()).origin!==new URL(url).origin)external.push(r.url());});
    await page.goto(url+'#analyze');await page.waitForFunction(()=>document.querySelector('#region').options.length>2);
    await page.locator('details').filter({has:page.locator('#corpusSource')}).locator('summary').first().click();
    await page.locator('#corpusSource').selectOption('reviewed');assert.equal(await page.locator('#reviewedSelection').isVisible(),false);
    await page.locator('#reviewedUnitsFile').setInputFiles(bundleFile);await page.locator('#topic').fill('');await page.locator('#startDate').fill('2026-09-22');await page.locator('#endDate').fill('2026-09-28');
    await page.locator('#clusterMethod').check();await page.locator('details').filter({has:page.locator('#clusterCount')}).locator('summary').first().click();await page.locator('#clusterCount').fill('3');await page.locator('#umapNeighbors').fill('3');await page.locator('#stabilityEnabled').check();await page.locator('#stabilityReplicates').fill('10');
    await page.locator('#nmfMethod').check();await page.locator('#nmfComponents').fill('3');
    const run=async()=>{await page.locator('#runAnalysis').click();await page.waitForFunction(()=>!document.querySelector('#analysisOutput').hidden||document.querySelector('#analysisStatus').textContent.startsWith('Could not complete'),{},{timeout:90000});assert.equal(await page.locator('#analysisOutput').isVisible(),true,await page.locator('#analysisStatus').textContent());};
    const download=async(id,name)=>{const [d]=await Promise.all([page.waitForEvent('download'),page.locator('#'+id).click()]);await d.saveAs(path.join(out,name));return fs.readFileSync(path.join(out,name));};
    await run();assert.match(await page.locator('.reviewed-unit-summary').textContent(),/12 included excerpts · 3 parent speeches · 3 meetings/);
    await page.locator('#analysisOutput').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'desktop.png')});
    await page.locator('.reviewed-unit-summary summary').click();assert.match(await page.locator('.reviewed-unit-summary').textContent(),/39.7%/);
    const result=JSON.parse(await download('exportResult','analysis.json'));assert.equal(result.engine,'browser-descriptive-1.11.0');assert.equal(result.counts.matched,12);assert.equal(result.counts.duplicates,0);
    assert.deepEqual(result.reviewed_units.included,{passages:12,parent_speeches:3,meetings:3});assert.equal(result.methods.clusters.points.length,12);assert.equal(result.methods.clusters.stability.successful,10);assert.equal(result.methods.clusters.stability.group_count,3);
    assert.ok(result.methods.clusters.stability.groups.every(g=>g.ids.length===4));assert.ok(result.matched.every(r=>r.parent_id&&r.start>=0&&r.end>r.start));assert.equal(result.methods.nmf.points.length,12);
    assert.match((await download('exportCSV','passages.csv')).toString(),/parent_text_sha256/);
    assert.match((await download('exportClusters','clusters.csv')).toString(),/parent_id/);
    assert.match((await download('exportNMF','components.csv')).toString(),/parent_id/);
    const ledger=JSON.parse(await download('exportAudioLedger','audio-review-ledger.json'));assert.equal(ledger.records.filter(r=>r.decision==='mismatch').length,5);assert.ok(ledger.records.every(r=>r.replacement_text===null));
    const html=(await download('exportHTML','report.html')).toString();assert.ok(html.includes('Original offsets'));assert.ok(!/<script\b/i.test(html));
    assert.deepEqual(await download('exportCorpus','reviewed-analysis.json'),fs.readFileSync(bundleFile));
    await page.setViewportSize({width:390,height:900});await page.locator('.reviewed-unit-summary').scrollIntoViewIfNeeded();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(out,'mobile.png')});await page.setViewportSize({width:1440,height:1000});
    await page.locator('#clusterMethod').uncheck();await page.locator('#nmfMethod').uncheck();await page.locator('#startDate').fill('2026-09-24');await page.locator('#endDate').fill('2026-09-24');assert.equal(await page.locator('#exportResult').isDisabled(),true);
    await run();const filtered=JSON.parse(await download('exportResult','filtered.json'));assert.deepEqual(filtered.reviewed_units.included,{passages:4,parent_speeches:1,meetings:1});
    await page.locator('#startDate').fill('2026-09-22');await page.locator('#endDate').fill('2026-09-28');
    const bad=JSON.parse(fs.readFileSync(bundleFile));bad.units.records[0].start++;await page.locator('#reviewedUnitsFile').setInputFiles({name:'changed.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bad))});
    await page.locator('#runAnalysis').click();await page.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('differ from'));assert.equal(await page.locator('#analysisOutput').isVisible(),false);
    await page.locator('#reviewedUnitsFile').setInputFiles(path.join(out,'reviewed-analysis.json'));await run();
    // A bundle cannot bypass the reviewed importer by using the ordinary collection control.
    await page.locator('#corpusSource').selectOption('import');await page.locator('#corpusFile').setInputFiles(bundleFile);await page.locator('#runAnalysis').click();await page.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('un.browser.corpus.v1'));assert.equal(await page.locator('#analysisOutput').isVisible(),false);
    assert.deepEqual(errors,[]);assert.deepEqual(uploads,[]);assert.deepEqual(external,[]);
    const validation={status:'PASS',source:url,reviewed_passages:12,parent_speeches:3,meetings:3,grouped_refits:10,group_children_kept_together:true,nmf:true,source_offsets_in_exports:true,bundle_bytes_preserved:true,corruption_rejected:true,wrong_import_path_rejected:true,filtered_parent_denominators:true,stale_exports_blocked:true,mobile_overflow:false,browser_errors:errors,uploads,external_requests:external};
    fs.writeFileSync(path.join(out,'validation.json'),JSON.stringify(validation,null,2)+'\n');console.log(JSON.stringify(validation));
  }finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
