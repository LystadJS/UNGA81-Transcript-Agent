/* Optional end-to-end acceptance. Provide a saved public corpus; nothing uploads.
 * node tools/test_browser_stability_ui.cjs URL CORPUS OUTPUT_DIRECTORY
 * PLAYWRIGHT_MODULE and BROWSER_PATH can point to an existing local QA runtime. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
  const [url,corpus,directory]=process.argv.slice(2);
  if(!url||!corpus||!directory)throw Error('Supply URL, corpus JSON and output directory.');
  fs.mkdirSync(directory,{recursive:true});
  const browser=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1050},acceptDownloads:true});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto(url);await page.waitForFunction(()=>document.querySelector('#region').options.length>1);
    await page.locator('#analysisForm > details summary').click();
    await page.locator('#corpusSource').selectOption('import');
    await page.locator('#corpusFile').setInputFiles(corpus);
    await page.locator('#topic').fill('');await page.locator('#clusterMethod').check();
    await page.locator('#stabilityEnabled').check();
    const started=Date.now();await page.locator('#runAnalysis').click();
    await page.locator('#analysisOutput').waitFor({state:'visible',timeout:240000});
    const seconds=(Date.now()-started)/1000;
    const download=async(id,name)=>{
      const [file]=await Promise.all([page.waitForEvent('download'),page.locator(id).click()]);
      await file.saveAs(path.join(directory,name));
    };
    await download('#exportResult','analysis.json');await download('#exportClusters','clusters.csv');
    await download('#exportConsensus','consensus.csv');await download('#exportHTML','report.html');
    const result=JSON.parse(fs.readFileSync(path.join(directory,'analysis.json')));
    const s=result.methods.clusters.stability;
    assert.equal(s.successful,30);assert.ok(s.consensus.co_observed.length>0);
    assert.equal(await page.locator('.consensus-map svg').count(),1);
    assert.ok(await page.locator('.stability-review a').count()>0);
    assert.equal((await page.locator('.stability-section').innerText()).includes('not confidence intervals'),true);
    assert.equal(fs.readFileSync(path.join(directory,'consensus.csv'),'utf8').trim().split('\r\n').length,1+s.reference_ids.length*(s.reference_ids.length-1)/2);
    await page.locator('.stability-section').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(directory,'desktop.png')});
    await page.setViewportSize({width:390,height:900});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.locator('.consensus-map').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(directory,'mobile.png')});
    await page.locator('#stabilitySeed').fill('17');
    assert.equal(await page.locator('#exportConsensus').isDisabled(),true);
    // Termination must stop refitting as well as the earlier PCA / UMAP stages.
    await page.evaluate(()=>{
      const status=document.querySelector('#analysisStatus');
      const observer=new MutationObserver(()=>{
        if(status.textContent.startsWith('Stability')){document.querySelector('#cancelAnalysis').click();observer.disconnect();}
      });observer.observe(status,{childList:true,subtree:true});
    });
    await page.locator('#runAnalysis').click();
    await page.waitForFunction(()=>document.querySelector('#analysisStatus').textContent.includes('cancelled'),{},{timeout:240000});
    assert.equal(await page.locator('#analysisOutput').isVisible(),false);
    assert.equal(await page.locator('#stabilitySeed').isDisabled(),false);
    assert.equal(await page.locator('#runAnalysis').isDisabled(),false);
    assert.deepEqual(errors,[]);
    const validation={url,engine:result.engine,passages:s.reference_ids.length,groups:s.group_count,
      successful:s.successful,attempted:s.attempted,unique_group_samples:s.unique_group_samples,
      ari:s.ari,cluster_jaccard:s.clusters,pair_coverage:s.consensus.pair_coverage,seconds,
      source_links:true,exports:['HTML','JSON','cluster CSV','consensus CSV'],
      stale_export_disabled:true,cancel_during_stability:true,mobile_overflow:false,browser_errors:errors};
    fs.writeFileSync(path.join(directory,'validation.json'),JSON.stringify(validation,null,2)+'\n');
    console.log(JSON.stringify(validation));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
