/* Test the offline review artifact with synthetic choices; never import into the real mask. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),assert=require('node:assert/strict');
(async()=>{
 const [packet,report,out]=process.argv.slice(2);fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_PATH?{executablePath:process.env.BROWSER_PATH}:{})});
 try{const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.resolve(packet)).href);await page.waitForSelector('#heading');assert.match(await page.locator('#status').textContent(),/0 of 460/);
 await page.locator('#record').click();assert.match(await page.locator('#status').textContent(),/Enter your reviewer/);
 await page.locator('#reviewer').fill('Synthetic UI test reviewer');await page.locator('#filter').selectOption('all');await page.locator('#search').fill('Egypt');
 assert.match(await page.locator('#status').textContent(),/2 match/);await page.locator('#next').click();assert.match(await page.locator('#text').textContent(),/^upon which/);assert.equal(await page.locator('#choice').inputValue(),'speech_fragment');
 await page.locator('#record').click();assert.match(await page.locator('#status').textContent(),/1 of 460/);
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#save').click()]);const saved=path.join(out,'synthetic-review.json');await download.saveAs(saved);
 const review=JSON.parse(fs.readFileSync(saved));assert.equal(review.choices.length,1);assert.equal(review.choices[0].type,'speech_fragment');assert.equal(review.choices[0].confirmed,true);
 await page.reload();assert.match(await page.locator('#status').textContent(),/0 of 460/);await page.locator('#resume').setInputFiles(saved);assert.match(await page.locator('#status').textContent(),/1 of 460/);
 await page.locator('#filter').selectOption('subset-unassigned');assert.ok(Number((await page.locator('#status').textContent()).match(/(\d+) match/)[1])>=145);
 await page.locator('#search').fill('Brazil');assert.match(await page.locator('#meta').textContent(),/Substantive PCA unassigned \/ LSA unassigned/);
 await page.screenshot({path:path.join(out,'review-desktop.png')});await page.setViewportSize({width:390,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(out,'review-mobile.png')});
 const bad={...review,corpus_sha256:'0'.repeat(64)};fs.writeFileSync(path.join(out,'wrong-review.json'),JSON.stringify(bad));await page.locator('#resume').setInputFiles(path.join(out,'wrong-review.json'));assert.match(await page.locator('#status').textContent(),/different collection/);
 await page.setViewportSize({width:1440,height:1000});await page.goto(report.startsWith('http')?report:pathToFileURL(path.resolve(report)).href);
 assert.equal(await page.locator('svg').count(),2);assert.equal(await page.locator('table').first().locator('tbody tr').count(),30);assert.match(await page.locator('body').textContent(),/460 of 460 records/);
 await page.screenshot({path:path.join(out,'report-desktop.png')});await page.locator('section').nth(1).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'coverage-desktop.png')});
 await page.setViewportSize({width:390,height:900});await page.evaluate(()=>window.scrollTo(0,0));assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(out,'report-mobile.png')});
 assert.deepEqual(errors,[]);const validation={status:'PASS',packet_passages:460,synthetic_choices:1,source_review_saved_and_resumed:true,wrong_corpus_rejected:true,substantive_unassigned_filter:true,report_fit_rows:30,charts:2,mobile_document_overflow:false,browser_errors:errors};
 fs.writeFileSync(path.join(out,'validation.json'),JSON.stringify(validation,null,2)+'\n');console.log(JSON.stringify(validation));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
