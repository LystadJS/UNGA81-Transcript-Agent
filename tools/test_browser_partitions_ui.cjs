/* Full worker, form, source-link and export acceptance against a local import. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
  const [url,corpus,directory]=process.argv.slice(2);
  if(!url||!corpus||!directory)throw Error('Supply URL, saved corpus and output directory.');
  const raw=JSON.parse(fs.readFileSync(corpus,'utf8')),dates=raw.records.map(r=>r.date).sort();
  fs.mkdirSync(directory,{recursive:true});
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1050},acceptDownloads:true});
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto(url);await page.waitForFunction(()=>document.querySelector('#region').options.length>1);
    await page.locator('#analysisForm > details summary').click();
    await page.locator('#corpusSource').selectOption('import');await page.locator('#corpusFile').setInputFiles(corpus);
    await page.locator('#topic').fill('');await page.locator('#startDate').fill(dates[0]);await page.locator('#endDate').fill(dates.at(-1));
    await page.locator('#clusterMethod').check();await page.locator('#representation').selectOption('compare');await page.locator('#stabilityEnabled').check();
    const validation={url,cases:[],browser_errors:errors};let reference=null;
    for(const mode of ['pam','ward','average']){
      const out=path.join(directory,mode);fs.mkdirSync(out,{recursive:true});
      await page.locator('#clusterAlgorithm').selectOption(mode==='pam'?'pam':'hierarchical');
      if(mode!=='pam')await page.locator('#clusterLinkage').selectOption(mode);
      assert.equal(await page.locator('#clusterSeed').isDisabled(),true);
      assert.equal(await page.locator('#clusterLinkage').isVisible(),mode!=='pam');
      const start=Date.now();await page.locator('#runAnalysis').click();
      await page.locator('#analysisOutput').waitFor({state:'visible',timeout:240000});
      const seconds=(Date.now()-start)/1000;
      const download=async(id,file)=>{const [d]=await Promise.all([page.waitForEvent('download'),page.locator(id).click()]);await d.saveAs(path.join(out,file));};
      await download('#exportResult','analysis.json');await download('#exportHTML','report.html');
      await download('#exportClusters','clusters.csv');await download('#exportConsensus','consensus.csv');
      const result=JSON.parse(fs.readFileSync(path.join(out,'analysis.json'))),fit=result.methods.clusters,other=fit.comparison.alternative;
      const pairs=fit.points.length*(fit.points.length-1)/2;
      assert.equal(fit.algorithm,mode==='pam'?'pam':'hierarchical');assert.ok(!fit.kmeans);assert.ok(!other.kmeans);
      assert.equal(fit.comparison.paired_stability.count,30);
      assert.equal(fit.stability.successful,30);assert.equal(other.stability.successful,30);
      assert.equal(await page.locator('#exportHierarchy').isVisible(),mode!=='pam');
      const clusters=fs.readFileSync(path.join(out,'clusters.csv'),'utf8').trim().split('\r\n');
      assert.equal(clusters.length,1+fit.points.length*2);assert.match(clusters[0],/"algorithm","linkage","representative_role","is_representative"/);
      const consensus=fs.readFileSync(path.join(out,'consensus.csv'),'utf8').trim().split('\r\n');
      assert.equal(consensus.length,1+pairs*2);assert.match(consensus[0],/"representation","algorithm","linkage"/);
      const html=fs.readFileSync(path.join(out,'report.html'),'utf8');assert.ok(!html.includes('<script'));assert.doesNotMatch(html,/k-means assignments|K-means inertia/);
      await page.locator('.representation-result > summary').first().click();
      if(mode==='pam'){
        assert.equal(await page.locator('.cluster-cards').first().locator('a').count(),fit.clustering.k);
        assert.match(html,/PAM medoid/);assert.deepEqual(fit.pam.medoid_ids,fit.clusters.map(c=>c.representative_id));
      }else{
        await download('#exportHierarchy','hierarchy.csv');
        const rows=fs.readFileSync(path.join(out,'hierarchy.csv'),'utf8').trim().split('\r\n');assert.equal(rows.length,1+2*(2*fit.points.length-1));
        assert.equal(await page.locator('.hierarchy-full a').count(),fit.points.length*2);
        assert.equal(await page.locator('.hierarchy-wide a').count(),fit.clustering.k*2);
        assert.equal(await page.locator('.hierarchy-small a').count(),fit.clustering.k*2);
        if(mode==='average')assert.match(html,/90% or more/);
        assert.match(html,/Full passage dendrogram/);
      }
      const target=mode==='pam'?'.cluster-cards':'.hierarchy-section';
      await page.locator(target).first().evaluate(e=>e.scrollIntoView({block:'start'}));await page.screenshot({path:path.join(out,'desktop.png')});
      await page.setViewportSize({width:390,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await page.locator(target).first().evaluate(e=>e.scrollIntoView({block:'start'}));await page.screenshot({path:path.join(out,'mobile.png')});
      await page.setViewportSize({width:1440,height:1050});
      if(reference)for(const [a,b] of [[fit,reference],[other,reference.comparison.alternative]]){
        assert.deepEqual(a.points.map(p=>p[a.representation]),b.points.map(p=>p[b.representation]));
        assert.deepEqual(a.points.map(p=>p.umap),b.points.map(p=>p.umap));
        assert.deepEqual(a.stability.runs.map(r=>r.groups),b.stability.runs.map(r=>r.groups));
      }
      else reference=fit;
      const check={mode,engine:result.engine,passages:fit.points.length,seconds,paired_samples:30,
        silhouette:{pca:fit.clustering.silhouette,lsa:other.clustering.silhouette},
        mean_stability_ari:{pca:fit.stability.ari.mean,lsa:other.stability.ari.mean},
        between_representation_ari:fit.comparison.between_cluster_ari,
        cluster_sizes:{pca:fit.clusters.map(c=>c.size),lsa:other.clusters.map(c=>c.size)},
        exports:mode==='pam'?['JSON','HTML','cluster CSV','consensus CSV']:['JSON','HTML','cluster CSV','consensus CSV','hierarchy CSV'],
        source_links:true,mobile_overflow:false};validation.cases.push(check);
      console.log(JSON.stringify(check));
      // Method and linkage changes invalidate downloads before another run.
      await page.locator('#clusterLinkage').evaluate(e=>e.dispatchEvent(new Event('input',{bubbles:true})));
      assert.equal(await page.locator('#exportResult').isDisabled(),true);
      assert.equal(await page.locator('#exportClusters').isDisabled(),true);
    }
    // Confirm default k-means restores its control and cancels a worker cleanly.
    await page.locator('#clusterAlgorithm').selectOption('kmeans');assert.equal(await page.locator('#clusterSeed').isDisabled(),false);
    await page.locator('#clusterAlgorithm').selectOption('hierarchical');
    await page.evaluate(()=>{
      const status=document.querySelector('#analysisStatus'),observer=new MutationObserver(()=>{
        if(status.textContent.includes('Stability · sample 2')){document.querySelector('#cancelAnalysis').click();observer.disconnect();}
      });observer.observe(status,{childList:true,subtree:true});
    });
    await page.locator('#runAnalysis').click();
    await page.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('cancelled'),{},{timeout:240000});
    assert.equal(await page.locator('#analysisOutput').isVisible(),false);assert.deepEqual(errors,[]);
    Object.assign(validation,{shared_coordinates_and_samples:true,stale_exports_disabled:true,cancel_during_resampling:true,status:'PASS'});
    fs.writeFileSync(path.join(directory,'validation.json'),JSON.stringify(validation,null,2)+'\n');console.log('PASS partition browser acceptance');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
