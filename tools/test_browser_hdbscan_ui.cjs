/* Live/local HDBSCAN acceptance: real worker, explicit noise, and all-noise success. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
  const [url,corpus,directory]=process.argv.slice(2);if(!directory)throw Error('Supply URL, saved corpus and output directory.');
  fs.mkdirSync(directory,{recursive:true});
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1050},acceptDownloads:true}),errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto(url);await page.waitForFunction(()=>document.querySelector('#region').options.length>1);
    await page.locator('#analysisForm > details summary').click();
    await page.locator('#corpusSource').selectOption('import');await page.locator('#corpusFile').setInputFiles(corpus);
    await page.locator('#startDate').fill('2026-09-22');await page.locator('#endDate').fill('2026-09-28');await page.locator('#topic').fill('');
    await page.locator('#clusterMethod').check();await page.locator('#clusterAlgorithm').selectOption('hdbscan');
    assert.equal(await page.locator('#clusterCount').isDisabled(),true);assert.equal(await page.locator('#clusterSeed').isDisabled(),true);
    await page.locator('#representation').selectOption('compare');await page.locator('#stabilityEnabled').check();
    const validation={url,cases:[],browser_errors:errors};let reference=null;
    for(const mode of ['eom','leaf','all-unassigned']){
      const out=path.join(directory,mode);fs.mkdirSync(out,{recursive:true});
      await page.locator('#hdbSelection').selectOption(mode==='leaf'?'leaf':'eom');
      await page.locator('#hdbMinClusterSize').fill(mode==='all-unassigned'?'600':'15');
      await page.locator('#stabilityReplicates').fill(mode==='all-unassigned'?'10':'30');
      const start=Date.now();await page.locator('#runAnalysis').click();await page.locator('#analysisOutput').waitFor({state:'visible',timeout:240000});
      const seconds=(Date.now()-start)/1000;
      const download=async(id,name)=>{const [d]=await Promise.all([page.waitForEvent('download'),page.locator(id).click()]);await d.saveAs(path.join(out,name));};
      for(const [id,name] of [['#exportResult','analysis.json'],['#exportClusters','clusters.csv'],['#exportConsensus','consensus.csv'],['#exportHTML','report.html']])await download(id,name);
      const result=JSON.parse(fs.readFileSync(path.join(out,'analysis.json'))),left=result.methods.clusters,right=left.comparison.alternative;
      const fits=[left,right];assert.equal(left.algorithm,'hdbscan');assert.equal(await page.locator('#exportHierarchy').isVisible(),false);
      for(const fit of fits){
        assert.ok(!fit.skipped);assert.equal(fit.hdbscan.assigned_count+fit.hdbscan.unassigned_count,fit.points.length);
        assert.equal(fit.points.filter(p=>p.cluster===0).length,fit.hdbscan.unassigned_count);
        assert.ok(fit.points.every(p=>p.cluster===0?(p.assignment_status==='unassigned'&&p.membership_strength===0):p.assignment_status==='assigned'));
        assert.equal(fit.stability.successful,mode==='all-unassigned'?10:30);
        assert.equal(fit.hdbscan.unassigned_ids.length,fit.hdbscan.unassigned_count);
        if(mode==='all-unassigned'){
          assert.equal(fit.clustering.k,0);assert.equal(fit.clustering.silhouette,null);assert.equal(fit.stability.ari.count,0);
          assert.ok(fit.stability.consensus.co_clustered.every(v=>v===0));assert.ok(fit.stability.consensus.co_assigned.every(v=>v===0));
        }
      }
      assert.equal(left.comparison.membership_counts.flat().reduce((a,b)=>a+b,0),left.points.length);
      const clusters=fs.readFileSync(path.join(out,'clusters.csv'),'utf8').trim().split('\r\n'),pairs=fs.readFileSync(path.join(out,'consensus.csv'),'utf8').trim().split('\r\n');
      assert.equal(clusters.length,1+left.points.length*2);assert.match(clusters[0],/"assignment_status","membership_strength"/);
      assert.equal(clusters.filter(r=>r.includes('"unassigned"')).length,left.hdbscan.unassigned_count+right.hdbscan.unassigned_count);
      assert.equal(pairs.length,1+left.points.length*(left.points.length-1));assert.match(pairs[0],/"co_assigned","co_assignment_given_assigned"/);
      const html=fs.readFileSync(path.join(out,'report.html'),'utf8');assert.ok(!html.includes('<script'));assert.match(html,/Unassigned passages/);
      // Inspect computed UI separately: source quotations can legitimately contain words such as "undefined".
      const computed=await page.locator('#analysisOutput').evaluate(element=>{const copy=element.cloneNode(true);copy.querySelectorAll('.unassigned-passages').forEach(e=>e.remove());return copy.innerHTML;});
      const invalid=computed.match(/>\s*(?:undefined|NaN|Infinity%)\s*<|(?:cx|cy|x|y|width|height)="(?:undefined|NaN|Infinity)"/);
      assert.equal(invalid,null,invalid?`Invalid computed report value: ${invalid[0]}`:undefined);
      assert.equal(await page.locator('.unassigned-passages a').count(),left.hdbscan.unassigned_count+right.hdbscan.unassigned_count);
      await page.locator('.representation-result > summary').first().click();
      await page.locator('.assignment-coverage').first().evaluate(e=>e.scrollIntoView({block:'start'}));await page.screenshot({path:path.join(out,'desktop.png')});
      await page.setViewportSize({width:390,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await page.locator('.assignment-coverage').first().evaluate(e=>e.scrollIntoView({block:'start'}));await page.screenshot({path:path.join(out,'mobile.png')});await page.setViewportSize({width:1440,height:1050});
      if(reference)for(const [i,fit] of fits.entries()){
        assert.deepEqual(fit.points.map(p=>p[fit.representation]),reference[i].points.map(p=>p[fit.representation]));
        assert.deepEqual(fit.points.map(p=>p.umap),reference[i].points.map(p=>p.umap));
      }else reference=fits;
      const row={mode,engine:result.engine,passages:left.points.length,seconds,
        groups:fits.map(f=>f.clusters.map(g=>g.size)),unassigned:fits.map(f=>f.hdbscan.unassigned_count),
        resamples:fits.map(f=>f.stability.successful),assessable_ari_samples:fits.map(f=>f.stability.ari.count),
        mean_stability_ari:fits.map(f=>f.stability.ari.mean),between_representation_ari:left.comparison.between_cluster_ari,
        all_points_and_sources_retained:true,exports:['HTML','JSON','cluster CSV','consensus CSV'],mobile_overflow:false};
      validation.cases.push(row);console.log(JSON.stringify(row));
      await page.locator('#hdbMinSamples').fill('6');assert.equal(await page.locator('#exportResult').isDisabled(),true);await page.locator('#hdbMinSamples').fill('5');
    }
    await page.locator('#clusterAlgorithm').selectOption('kmeans');assert.equal(await page.locator('#clusterCount').isDisabled(),false);
    await page.locator('#clusterAlgorithm').selectOption('hdbscan');await page.locator('#hdbMinClusterSize').fill('15');
    await page.evaluate(()=>{const status=document.querySelector('#analysisStatus'),observer=new MutationObserver(()=>{if(status.textContent.includes('Stability · sample 2')){document.querySelector('#cancelAnalysis').click();observer.disconnect();}});observer.observe(status,{childList:true,subtree:true});});
    await page.locator('#runAnalysis').click();await page.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('cancelled'),{},{timeout:240000});
    assert.equal(await page.locator('#analysisOutput').isVisible(),false);assert.deepEqual(errors,[]);
    Object.assign(validation,{status:'PASS',stale_exports_disabled:true,cancellation:true,settings_do_not_change_coordinates:true});
    fs.writeFileSync(path.join(directory,'validation.json'),JSON.stringify(validation,null,2)+'\n');console.log('PASS HDBSCAN browser acceptance');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
