'use strict';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require('playwright'),{fixture}=require('./latent_fixture.cjs');
(async()=>{
  const [site,out]=process.argv.slice(2);if(!site||!out)throw Error('Usage: node tools/test_latent_ui.cjs BUILT_SITE_OR_URL NEW_OUTPUT');
  fs.mkdirSync(out,{recursive:true});let server,url=site;
  if(!/^https?:/.test(site)){
    const root=path.resolve(site);server=http.createServer((req,res)=>{
      const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]).replace(/\/$/,'/index.html'));
      if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
      try{res.setHeader('Content-Type',({'.js':'text/javascript','.json':'application/json','.css':'text/css','.html':'text/html'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch(e){res.writeHead(404).end();}
    });await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));url='http://127.0.0.1:'+server.address().port+'/';
  }
  if(!url.endsWith('/'))url+='/';
  const browser=await chromium.launch({headless:true});const checks=[];
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true}),errors=[],uploads=[],external=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()!=='GET')uploads.push(r.url());if(new URL(r.url()).origin!==new URL(url).origin)external.push(r.url());});
    await page.goto(url+'latent.html');await page.waitForFunction(()=>document.querySelector('#scope').options.length===8);
    const f=await fixture();f.plan.settings.push({label:'NMF engineering comparison',method:'nmf',options:{components:2,starts:1,maxIterations:100}});
    const file=(name,text)=>({name,mimeType:'application/json',buffer:Buffer.from(text)});
    const finished=async()=>{await page.waitForFunction(()=>!document.querySelector('#results').hidden||document.querySelector('#status').textContent.startsWith('Could not complete:'),{},{timeout:120000});assert.equal(await page.locator('#results').isVisible(),true,await page.locator('#status').textContent());};
    const download=async(id,name)=>{const [d]=await Promise.all([page.waitForEvent('download'),page.locator('#'+id).click()]);await d.saveAs(path.join(out,name));return fs.readFileSync(path.join(out,name));};
    await page.locator('#sourceFile').setInputFiles(file('synthetic-reviewed.json',f.payload.text));await page.waitForFunction(()=>document.querySelector('#sourceStatus').textContent.startsWith('Selected'));
    await page.locator('#planFile').setInputFiles(file('synthetic-plan.json',JSON.stringify(f.plan)));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Plan opened'));
    assert.equal(await page.locator('#planRows tr').count(),3);await page.locator('#run').click();await finished();
    assert.match(await page.locator('#output').textContent(),/Parent coverage and weighting/);assert.match(await page.locator('#output').textContent(),/NMF reconstruction/);
    const result=JSON.parse(await download('saveJSON','comparison.json'));assert.equal(result.entries.length,6);assert.equal(result.entries[0].result.counts.matched,18);assert.equal(result.entries[3].result.counts.matched,6);assert.equal(result.coverage.length,6);assert.ok(result.runtime.module_sha256['latent-core.js']);checks.push('real worker: PCA/LSA/NMF, full parents, coverage and runtime hashes');
    const archive=await download('saveRun','saved-run.json'),csv=await download('saveCSV','diagnostics.csv'),html=await download('saveHTML','report.html');
    assert.match(csv.toString(),/assignment_fraction/);assert.ok(!/<script\b/i.test(html.toString()));assert.ok(html.toString().includes('<svg'));assert.ok(html.toString().includes('https://transcripts.un.org/'));checks.push('replay archive, numerical JSON, diagnostics CSV and script-free source-linked visual HTML');
    await page.locator('#savePlan').scrollIntoViewIfNeeded();const savedPlan=JSON.parse(await download('savePlan','settings.json'));assert.equal(savedPlan.settings.length,3);assert.equal(savedPlan.schema,'un.latent-plan.v1');checks.push('validated reusable settings export');
    await page.locator('#results').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});await page.setViewportSize({width:1440,height:1000});checks.push('1440px desktop and 390px mobile: no page overflow');
    await page.locator('#topic').fill('changed');assert.equal(await page.locator('#results').isVisible(),false);checks.push('stale settings hide completed results and exports');
    await page.locator('#savedA').setInputFiles(file('saved-run.json',archive.toString()));await finished();const replay=JSON.parse(await download('saveJSON','replayed.json'));assert.deepEqual(replay,result);const sameBytes=await download('saveRun','saved-again.json');assert.deepEqual(sameBytes,archive);checks.push('saved run restores exact coordinates, numerical results and archive bytes');
    await page.locator('#savedB').setInputFiles(file('same-run-b.json',archive.toString()));await page.waitForFunction(()=>document.querySelector('#resultMode').textContent.startsWith('Two archived runs'));
    const comparison=JSON.parse(await download('saveJSON','cross-run.json'));assert.equal(comparison.schema,'un.latent-saved-comparison.v1');assert.equal(comparison.pairs.find(p=>p.left==='A/excerpt-1'&&p.right==='B/excerpt-1').ari,1);assert.equal(await page.locator('#saveRun').isDisabled(),true);checks.push('two saved-run comparison uses shared identities, not matching numeric labels');
    const bad=JSON.parse(archive);bad.result_json+=' ';
    await page.locator('#savedA').setInputFiles(file('tampered.json',JSON.stringify(bad)));await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('integrity check failed'));assert.equal(await page.locator('#results').isVisible(),false);checks.push('tampered saved run rejected without retaining a prior export');
    await page.locator('#savedA').setInputFiles(file('saved-run.json',archive.toString()));await finished();
    await page.locator('details').filter({has:page.locator('#stability')}).locator('summary').click();await page.locator('#stability').check();await page.locator('#replicates').fill('100');await page.locator('#run').click();await page.locator('#cancel').click();assert.equal(await page.locator('#results').isVisible(),false);assert.match(await page.locator('#status').textContent(),/Cancelled|cancelled/);checks.push('worker cancellation releases no partial result');
    const small=await fixture(3);await page.locator('#sourceFile').setInputFiles(file('synthetic-small.json',small.payload.text));await page.waitForFunction(()=>document.querySelector('#sourceStatus').textContent.includes('synthetic-small'));
    await page.locator('#planFile').setInputFiles(file('small-plan.json',JSON.stringify(small.plan)));await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Plan opened'));await page.locator('#run').click();await finished();
    const tiny=JSON.parse(await download('saveJSON','small-parent.json'));assert.equal(tiny.entries[2].summary.status,'withheld');assert.ok((await page.locator('#output').textContent()).includes('four passages'));checks.push('three-parent baseline withheld visibly, while excerpt fit remains available');
    assert.deepEqual(errors,[]);assert.deepEqual(uploads,[]);assert.deepEqual(external,[]);checks.push('no JavaScript errors, uploads or external requests');
    const validation={status:'PASS',source:url+'latent.html',synthetic_only:true,private_owner_bundle_used:false,checks,check_count:checks.length,browser:browser.version(),node:process.version,errors,uploads,external_requests:external};
    fs.writeFileSync(path.join(out,'validation.json'),JSON.stringify(validation,null,2));console.log(JSON.stringify(validation));
  }finally{await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1;});
