/* Public archive browser acceptance: entirely synthetic; no live transcript calls. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),http=require('node:http'),path=require('node:path'),crypto=require('node:crypto');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'../site');
const date=new Date().toISOString().slice(0,10);
const meetings=[
  {meeting_id:'ga/81/42',date,title:'General Assembly synthetic meeting',body:'General Assembly',source_url:'https://transcripts.un.org/en/ga/81/42',status:'deferred',segments:3,issues:[{id:'ceasefire',label:'Ceasefire'}],positions:[{country:'Kenya',capacity:'national',issue_id:'ceasefire',proposition:'An immediate ceasefire',label:'support',status:'emitted'}]},
  {meeting_id:'sc/81/10021',date,title:'=SUM(1,2)',body:'Security Council',source_url:'javascript:alert(1)',status:'pending',segments:0,issues:[],positions:[{country:'France',capacity:'national',issue_id:'ceasefire',proposition:'An immediate ceasefire',label:'support',status:'conditional',condition:'Subject to a verified monitoring mechanism'}]},
  {meeting_id:'hrc/81/5',date:null,title:'<img src=x onerror=alert(1)>',body:'Human Rights Council',source_url:'https://transcripts.un.org/en/hrc/81/5',status:'excluded_reserved',segments:0,issues:[],positions:[]}
];
const partition=Buffer.from(JSON.stringify({meetings}));
const csv=Buffer.from('meeting_id,date\r\nga/81/42,'+date+'\r\n');
const descriptor=(name,data)=>({path:name,sha256:crypto.createHash('sha256').update(data).digest('hex'),bytes:data.length});
const manifest={schema:'un.archive.v1',snapshot_id:'synthetic-archive-001',generated_at:'2026-01-01T12:00:00Z',status:'partial',model_status:'accepted',coverage:{selected:3},partitions:[descriptor('part.json',partition)],downloads:[{...descriptor('meetings.csv',csv),name:'meetings.csv',rows:1}]};
let mode='empty',server,browser,checks=0;
async function test(name,fn){await fn();checks++;console.log('PASS '+name);}
(async()=>{
  server=http.createServer((req,res)=>{
    const pathname=new URL(req.url,'http://localhost').pathname;
    res.setHeader('Content-Type',pathname.endsWith('.js')?'text/javascript':pathname.endsWith('.css')?'text/css':pathname.endsWith('.html')?'text/html':'application/json');
    if(pathname==='/archive-config.json')return res.end(JSON.stringify({schema:'un.archive-config.v1',manifest_url:mode==='empty'?null:'fixture/manifest.json'}));
    if(pathname==='/fixture/manifest.json'){
      const copy=structuredClone(manifest);
      if(mode==='withheld')copy.model_status='not_evaluated_missing_labels';
      if(mode==='path')copy.partitions[0].path='../private.json';
      if(mode==='bytes')copy.partitions[0].bytes++;
      if(mode==='missing')copy.partitions[0].path='missing.json';
      return res.end(JSON.stringify(copy));
    }
    if(pathname==='/fixture/part.json')return res.end(mode==='tamper'?Buffer.from(partition.toString().replace('Kenya','Benya')):partition);
    if(pathname==='/fixture/meetings.csv')return res.end(mode==='download-tamper'?Buffer.from('bad!'):csv);
    if(pathname.startsWith('/fixture/')){res.writeHead(404);return res.end('{}');}
    const file=path.resolve(root,'.'+pathname);
    if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
    try{res.end(fs.readFileSync(file));}catch{res.writeHead(404);res.end();}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_PATH||'/usr/bin/chromium'});
  const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('https://transcripts.un.org/**',route=>route.abort());
  const open=async next=>{mode=next;await page.goto(`http://127.0.0.1:${server.address().port}/archive.html`);await page.waitForFunction(()=>!document.querySelector('#archiveStatus').textContent.includes('Checking'));};
  await test('Unprovisioned archive displays honest status and disables filters',async()=>{await open('empty');assert.match(await page.locator('#archiveStatus').innerText(),/has not been published/);assert.equal(await page.locator('#filters').evaluate(el=>el.disabled),true);assert.equal(await page.locator('#meetingRows tr').count(),0);});
  await test('Verified partition renders meetings, estimates, gaps and stale update',async()=>{await open('ready');assert.equal(await page.locator('#meetingRows tr').count(),3);assert.equal(await page.locator('#positionRows tr').count(),2);assert.match(await page.locator('#positionRows').innerText(),/Kenya/);assert.match(await page.locator('#positionRows').innerText(),/Conditional position/);assert.match(await page.locator('#freshness').innerText(),/more than two days old/);assert.match(await page.locator('#verificationStatus').textContent(),/match/);});
  await test('Deferred refresh retains archived text and separates the latest attempt',async()=>{const row=page.locator('#meetingRows tr').filter({hasText:'General Assembly synthetic meeting'});assert.equal(await row.locator('td').nth(3).innerText(),'Text archived');assert.equal(await row.locator('td').nth(4).innerText(),'deferred');assert.match(await page.locator('#coverageSummary').innerText(),/1 meetings with archived text/);assert.match(await page.locator('#coverageSummary').innerText(),/Latest collection checks/);const absent=page.locator('#meetingRows tr').filter({hasText:'=SUM(1,2)'});assert.equal(await absent.locator('td').nth(3).innerText(),'No text archived');});
  await test('Source markup and unsafe URLs never become executable content',async()=>{assert.equal(await page.locator('#meetingRows img').count(),0);assert.equal(await page.locator('a[href^="javascript:"]').count(),0);assert.match(await page.locator('#meetingRows').innerText(),/<img src=x/);});
  await test('Unknown dates and descriptive issue coverage remain visible',async()=>{assert.match(await page.locator('#meetingRows').innerText(),/Date unknown/);assert.match(await page.locator('#issueList').innerText(),/Ceasefire — 1 meeting/);});
  await test('Venue and issue filters narrow results and can be reset',async()=>{await page.locator('#archiveBody').selectOption('General Assembly');assert.equal(await page.locator('#meetingRows tr').count(),1);await page.locator('#clearFilters').click();await page.locator('#archiveSearch').fill('ceasefire');assert.equal(await page.locator('#meetingRows tr').count(),1);await page.locator('#clearFilters').click();});
  await test('Invalid date range is explicit and exports no misleading selection',async()=>{await page.locator('#archiveStart').fill('2027-01-01');await page.locator('#archiveEnd').fill('2026-01-01');assert.match(await page.locator('#filterStatus').innerText(),/start date/);assert.equal(await page.locator('#exportSelection').isDisabled(),true);await page.locator('#clearFilters').click();});
  await test('Selected CSV preserves metadata and neutralizes spreadsheet formula cells',async()=>{const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#exportSelection').click()]);const content=fs.readFileSync(await download.path(),'utf8');assert.match(content,/'=SUM\(1,2\)/);assert.match(content,/excluded_reserved/);});
  await test('Published downloads are hash verified before saving',async()=>{const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'meetings.csv',exact:true}).click()]);assert.deepEqual(fs.readFileSync(await download.path()),csv);assert.match(await page.locator('#downloadStatus').innerText(),/Verified/);});
  await test('Mobile layout has no page overflow and keyboard skip link works',async()=>{await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),true);await page.goto(page.url());await page.keyboard.press('Tab');assert.equal(await page.locator('.skip').evaluate(el=>el===document.activeElement),true);await page.keyboard.press('Enter');assert.equal(new URL(page.url()).hash,'#main');});
  await test('Unaccepted model suppresses substantive predictions even if supplied',async()=>{await open('withheld');assert.equal(await page.locator('#positionRows tr').count(),0);assert.match(await page.locator('#modelStatus').innerText(),/withheld/);assert.equal(await page.locator('#meetingRows tr').count(),3);assert.match(await page.locator('#issueList').innerText(),/Ceasefire/);});
  for(const failure of ['tamper','bytes','missing','path'])await test('Fail closed on '+failure+' partition',async()=>{await open(failure);assert.match(await page.locator('#archiveStatus').innerText(),/could not be loaded safely/);assert.equal(await page.locator('#meetingRows tr').count(),0);assert.equal(await page.locator('#filters').evaluate(el=>el.disabled),true);});
  await test('Corrupt download is rejected without changing loaded snapshot',async()=>{await open('download-tamper');await page.getByRole('button',{name:'meetings.csv',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#downloadStatus').textContent.includes('does not match'));assert.equal(await page.locator('#meetingRows tr').count(),3);});
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({status:'PASS',checks,synthetic_only:true,live_transcripts_opened:0,browser:browser.version()}));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server)await new Promise(resolve=>server.close(resolve));});
