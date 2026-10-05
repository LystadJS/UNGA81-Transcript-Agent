/* Optional local or published UI acceptance. Uses an imported corpus locally. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
  const [url,corpus,directory]=process.argv.slice(2);
  if(!url||!corpus||!directory)throw Error('Supply URL, corpus JSON and output directory.');
  fs.mkdirSync(directory,{recursive:true});
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1050},acceptDownloads:true});
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto(url);await page.waitForFunction(()=>document.querySelector('#region').options.length>1);
    await page.locator('#analysisForm > details summary').click();
    await page.locator('#corpusSource').selectOption('import');await page.locator('#corpusFile').setInputFiles(corpus);
    await page.locator('#clusterMethod').check();await page.locator('#representation').selectOption('compare');
    await page.locator('#stabilityEnabled').check();
    const started=Date.now();await page.locator('#runAnalysis').click();
    await page.locator('#analysisOutput').waitFor({state:'visible',timeout:240000});
    const seconds=(Date.now()-started)/1000;
    const download=async(id,name)=>{const [file]=await Promise.all([page.waitForEvent('download'),page.locator(id).click()]);await file.saveAs(path.join(directory,name));};
    await download('#exportResult','analysis.json');await download('#exportClusters','clusters.csv');
    await download('#exportConsensus','consensus.csv');await download('#exportHTML','report.html');
    const result=JSON.parse(fs.readFileSync(path.join(directory,'analysis.json'))),pca=result.methods.clusters,lsa=pca.comparison.alternative,c=pca.comparison;
    assert.equal(result.parameters.clustering.representation,'compare');
    assert.equal(lsa.representation,'lsa');assert.ok(!lsa.pca);assert.equal(c.paired_stability.count,30);
    assert.deepEqual(pca.stability.runs.map(r=>r.groups),lsa.stability.runs.map(r=>r.groups));
    assert.equal(await page.locator('.representation-maps a').count(),2*pca.points.length);
    // Corresponding overview points use the same reference color, regardless of LSA labels.
    const fill=await page.locator('.representation-maps .cluster-map').evaluateAll(maps=>maps.map(map=>[...map.querySelectorAll('circle')].map(c=>c.getAttribute('fill'))));
    assert.deepEqual(fill[0],fill[1]);
    const clusterCsv=fs.readFileSync(path.join(directory,'clusters.csv'),'utf8').trim().split('\r\n');
    assert.equal(clusterCsv.length,1+2*pca.points.length);assert.ok(clusterCsv[0].includes('"representation"'));
    assert.equal(clusterCsv.filter(line=>line.startsWith('"lsa"')).length,lsa.points.length);
    const pairCsv=fs.readFileSync(path.join(directory,'consensus.csv'),'utf8').trim().split('\r\n');
    assert.equal(pairCsv.length,1+pca.points.length*(pca.points.length-1));
    assert.equal(pairCsv.filter(line=>line.startsWith('"lsa"')).length,lsa.points.length*(lsa.points.length-1)/2);
    const exported=fs.readFileSync(path.join(directory,'report.html'),'utf8');
    assert.ok(exported.includes('LSA component vocabulary'));assert.ok(exported.includes('Neighborhood preservation'));
    assert.ok(!exported.includes('<script'));
    await page.locator('.representation-comparison').evaluate(e=>e.scrollIntoView({block:'start'}));
    await page.screenshot({path:path.join(directory,'desktop.png')});
    await page.setViewportSize({width:390,height:900});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.locator('.representation-maps').evaluate(e=>e.scrollIntoView({block:'start'}));
    await page.screenshot({path:path.join(directory,'mobile.png')});
    await page.locator('.representation-result > summary').nth(1).click();
    assert.equal(await page.locator('[aria-label="LSA k-means UMAP results"]').isVisible(),true);
    // Run the standalone LSA route as well as the comparison wrapper.
    await page.locator('#representation').selectOption('lsa');
    assert.equal(await page.locator('#exportClusters').isDisabled(),true);
    await page.locator('#stabilityEnabled').uncheck();await page.locator('#runAnalysis').click();
    await page.locator('#analysisOutput').waitFor({state:'visible',timeout:240000});
    await download('#exportResult','lsa-only.json');await download('#exportClusters','lsa-only.csv');
    const single=JSON.parse(fs.readFileSync(path.join(directory,'lsa-only.json'))).methods.clusters;
    assert.deepEqual(single.points,lsa.points);assert.deepEqual(single.lsa,lsa.lsa);
    assert.ok(fs.readFileSync(path.join(directory,'lsa-only.csv'),'utf8').includes('"LS1"'));
    assert.equal(await page.locator('#exportConsensus').isVisible(),false);
    // Cancel specifically after the comparison has reached the second representation.
    await page.locator('#representation').selectOption('compare');
    await page.evaluate(()=>{
      const status=document.querySelector('#analysisStatus');const observer=new MutationObserver(()=>{
        if(status.textContent.startsWith('LSA comparison')){document.querySelector('#cancelAnalysis').click();observer.disconnect();}
      });observer.observe(status,{childList:true,subtree:true});
    });
    await page.locator('#runAnalysis').click();
    await page.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('cancelled'),{},{timeout:240000});
    assert.equal(await page.locator('#analysisOutput').isVisible(),false);assert.deepEqual(errors,[]);
    const validation={url,engine:result.engine,passages:pca.points.length,components:{pca:pca.pca.components,lsa:lsa.lsa.components},
      centered_variance:{pca:pca.pca.retained_variance,lsa:lsa.lsa.retained_variance},lsa_energy:lsa.lsa.retained_energy,
      between_cluster_ari:c.between_cluster_ari,neighbor_overlap_between_representations:c.mean_neighbor_overlap,
      fidelity:{pca:{...pca.fidelity.representation,points:undefined},lsa:{...lsa.fidelity.representation,points:undefined}},
      stability:{pca:pca.stability.ari,lsa:lsa.stability.ari,paired:c.paired_stability.count},seconds,
      shared_reference_colors:true,source_links:true,standalone_equals_comparison:true,
      exports:['HTML','JSON','cluster CSV','consensus CSV'],stale_exports_disabled:true,cancel_during_alternative:true,mobile_overflow:false,browser_errors:errors};
    fs.writeFileSync(path.join(directory,'validation.json'),JSON.stringify(validation,null,2)+'\n');console.log(JSON.stringify(validation));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
