/* Private owner-pilot acceptance. No source or review file is uploaded or committed. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
  const [site,input,out]=process.argv.slice(2);if(!out)throw Error('Usage: node check_latent_pilot.cjs BUILT_SITE_OR_URL REVIEWED_BUNDLE NEW_OUTPUT');
  fs.mkdirSync(out,{recursive:false});let server,url=site;
  if(!/^https?:/.test(site)){
    const root=path.resolve(site);server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]).replace(/\/$/,'/index.html'));
      if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      try{res.setHeader('Content-Type',({'.js':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch(e){res.writeHead(404).end();}});
    await new Promise(r=>server.listen(0,'127.0.0.1',r));url='http://127.0.0.1:'+server.address().port+'/';
  }
  const browser=await chromium.launch({headless:true,...(process.env.PW_CHANNEL?{channel:process.env.PW_CHANNEL}:{})});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true}),errors=[],uploads=[],external=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()!=='GET')uploads.push(r.url());if(new URL(r.url()).origin!==new URL(url).origin)external.push(r.url());});
    await page.goto(url+'latent.html');await page.waitForFunction(()=>document.querySelector('#scope').options.length===8);
    const plan={schema:'un.latent-plan.v1',base:{topic:'',start:'2026-09-22',end:'2026-09-28',region:'All regions',scope:'general_debate'},compare_parents:true,
      stability:{enabled:true,unit:'meeting',replicates:10,fraction:.8,seed:31415},settings:[...['pca','lsa'].map(representation=>({label:representation.toUpperCase()+' · 4 dimensions · 3 clusters',method:'clusters',options:{representation,algorithm:'kmeans',components:4,k:3,neighbors:3,seed:42,umapSeed:42}})),{label:'NMF · 3 overlapping components',method:'nmf',options:{components:3,seed:42}}]};
    const file=(name,text)=>({name,mimeType:'application/json',buffer:Buffer.from(text)});
    const finished=async()=>{await page.waitForFunction(()=>!document.querySelector('#results').hidden||document.querySelector('#status').textContent.startsWith('Could not complete'),{},{timeout:120000});assert.equal(await page.locator('#results').isVisible(),true,await page.locator('#status').textContent());};
    const download=async(id,name)=>{const [d]=await Promise.all([page.waitForEvent('download'),page.locator('#'+id).click()]);await d.saveAs(path.join(out,name));return fs.readFileSync(path.join(out,name));};
    const run=async p=>{await page.locator('#planFile').setInputFiles(file('plan.json',JSON.stringify(p)));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Plan opened'));await page.locator('#run').click();await finished();};
    await page.locator('#sourceFile').setInputFiles(input);await page.waitForFunction(()=>document.querySelector('#sourceStatus').textContent.startsWith('Selected'));
    await run(plan);const a=JSON.parse(await download('saveJSON','run-a.json')),archiveA=await download('saveRun','saved-run-a.json');
    assert.equal(a.coverage.length,3);assert.ok(a.coverage.every(c=>c.passages===4&&c.coverage_fraction<.4));assert.equal(a.counts.matched,12);
    assert.ok(a.entries.filter(e=>e.unit==='parent').every(e=>e.summary.status==='withheld'&&e.result.counts.matched===3));
    assert.ok(a.entries.filter(e=>e.unit==='excerpt').every(e=>e.summary.status==='fitted'&&e.result.counts.matched===12));
    assert.ok(a.entries[2].mixture.totals.every(r=>Math.abs(r.passage_weighted-r.parent_balanced)<1e-10));
    await download('saveHTML','pilot-report.html');await download('saveCoverage','coverage.csv');await download('saveWeights','weights.csv');
    await page.locator('.coverage-chart').first().screenshot({path:path.join(out,'coverage-desktop.png')});
    const nmfDetail=page.locator('#output > details').filter({has:page.locator('summary').filter({hasText:'excerpt-3 · NMF'})}).first();
    await nmfDetail.locator('summary').first().click();await nmfDetail.locator('.weighting-chart').screenshot({path:path.join(out,'weights-desktop.png')});
    const bPlan=JSON.parse(JSON.stringify(plan));bPlan.settings.filter(r=>r.method==='clusters').forEach(r=>{r.options.umapSeed=99;r.label+=' · display seed 99';});
    await run(bPlan);const archiveB=await download('saveRun','saved-run-b.json');
    await page.locator('#savedA').setInputFiles(file('a.json',archiveA.toString()));await finished();assert.deepEqual(await download('saveRun','restored-a.json'),archiveA);
    await page.locator('#savedB').setInputFiles(file('b.json',archiveB.toString()));await page.waitForFunction(()=>document.querySelector('#resultMode').textContent.startsWith('Two archived'));
    const compared=JSON.parse(await download('saveJSON','comparison.json'));await download('saveHTML','saved-comparison.html');await download('saveCoverage','comparison-coverage.csv');await download('saveWeights','comparison-weights.csv');
    assert.equal(compared.snapshots.length,2);assert.ok(compared.coverage_change.every(r=>r.comparable&&r.coverage_change===0));
    for(const id of [1,2]){const pair=compared.pairs.find(p=>p.left==='A/excerpt-'+id&&p.right==='B/excerpt-'+id);assert.equal(pair.geometry_identical,true);assert.equal(pair.labels_identical,true);assert.equal(pair.ari,1);}
    await page.locator('.snapshot-grid').screenshot({path:path.join(out,'saved-coverage-desktop.png')});
    await page.setViewportSize({width:390,height:900});await page.locator('.saved-snapshot').first().scrollIntoViewIfNeeded();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(out,'mobile.png')});
    assert.deepEqual(errors,[]);assert.deepEqual(uploads,[]);assert.deepEqual(external,[]);
    fs.writeFileSync(path.join(out,'plan.json'),JSON.stringify(plan,null,2)+'\n');
    const validation={status:'PASS',source:url+'latent.html',actual_owner_bundle:true,reviewed_excerpts:12,parent_speeches:3,meetings:3,settings_per_run:3,
      parent_models_withheld:true,exact_archive_replay:true,A_B_coverage_preserved:true,display_only_scores_and_assignments_unchanged:true,
      NMF_weighting_views_coincide_because_each_parent_has_four_defined_excerpts:true,script_free_visual_exports:true,coverage_and_weighting_CSV:true,mobile_overflow:false,errors,uploads,external_requests:external,
      interpretation:'Workflow pilot, not representative inference or a test of nonrandom diplomatic structure.'};
    fs.writeFileSync(path.join(out,'validation.json'),JSON.stringify(validation,null,2)+'\n');console.log(JSON.stringify(validation));
  }finally{await browser.close();if(server)await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
