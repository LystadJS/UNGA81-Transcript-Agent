/* Native Word structure and browser behavior, using fictional source bundles only. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),http=require('node:http'),path=require('node:path'),{spawnSync}=require('node:child_process');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const F=require('./meeting_report_fixture.cjs'),Core=require('../site/meeting-report-core.js'),root=path.resolve(__dirname,'../site');
let browser,server;
(async()=>{
 server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+path.sep)){res.writeHead(403);return res.end();}try{res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':file.endsWith('.json')?'application/json':'text/html');res.end(fs.readFileSync(file));}catch{res.writeHead(404);res.end();}});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_PATH||'/usr/bin/chromium'});
 const page=await browser.newPage({acceptDownloads:true,viewport:{width:1440,height:1000}}),errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));await page.route('**/countries.json',r=>r.fulfill({json:F.countries}));
 await page.route('https://transcripts.un.org/**',r=>{requests.push(r.request().url());return r.abort();});
 const base=process.argv[2]||`http://127.0.0.1:${server.address().port}/`;
 await page.goto(new URL('meeting-reports.html',base).href);await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Ready.'));assert(await page.locator('#downloadWord').isDisabled());
 const corpora=[await F.corpus(),await F.corpus(1)],ids=F.meetings.map(m=>m.slug),notes='Fictional assessment <script>literal</script> 😀\nFollow-up\tline';
 const report=Core.build(corpora,ids,{template:'brief',title:'Word briefing É 😀',mission:'Synthetic mission',notes,questions:[{heading:'Access question',query:'humanitarian access'},{heading:'Unanswered question',query:'fictional-unmatched'}]}, {mode:'selected',record_ids:[corpora[0].records[0].id]},[{record_id:corpora[0].records[2].id,text:'Separate passage note 😀\nSecond line'}]);
 const saved=Core.savedReport(report,corpora),file={name:'fictional.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(saved))};
 await page.locator('#openCollection').setInputFiles(file);await page.waitForFunction(()=>document.querySelector('#status').textContent.startsWith('Saved sources verified'));await page.locator('#prepareReport').click();assert(!(await page.locator('#downloadWord').isDisabled()));
 const before=await page.locator('#reportPreview').innerHTML();await page.locator('#evidenceSearch').fill('nonexistent-filter');await page.locator('#evidenceCountry').selectOption(JSON.stringify('United States'));
 const content=await page.evaluate(()=>{
  const old=UNMeetingReportWord.build;window.wordSnapshot=null;
  UNMeetingReportWord.build=report=>{const doc=new DOMParser().parseFromString(UNMeetingReport.reportHTML(report),'text/html'),walker=doc.createTreeWalker(doc.body,NodeFilter.SHOW_TEXT),text=[];let node;while(node=walker.nextNode())if(node.nodeValue.trim())text.push(node.nodeValue);window.wordSnapshot={text,links:[...doc.querySelectorAll('a[href]')].map(a=>a.getAttribute('href')),time:report.generated_at};return old(report);};return true;
 });assert(content);
 await page.locator('#downloadWord').focus();const [download]=await Promise.all([page.waitForEvent('download'),page.keyboard.press('Enter')]);assert(download.suggestedFilename().endsWith('.docx'));
 const snapshot=await page.evaluate(()=>window.wordSnapshot);assert(download.suggestedFilename().includes(snapshot.time.replace(/[-:.]/g,'')));
 const check=spawnSync('python3',['-c',`
import json,re,sys,zipfile,xml.etree.ElementTree as ET
expected=json.load(sys.stdin);w={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with zipfile.ZipFile(sys.argv[1]) as z:
 assert set(z.namelist())=={'[Content_Types].xml','_rels/.rels','word/document.xml','word/styles.xml','word/numbering.xml','word/_rels/document.xml.rels'}
 assert z.testzip() is None
 parts={name:ET.fromstring(z.read(name)) for name in z.namelist()}
 doc=parts['word/document.xml'];text=''.join('\\n' if n.tag=='{'+w['w']+'}br' else '\\t' if n.tag=='{'+w['w']+'}tab' else n.text or '' for n in doc.iter() if n.tag in {'{'+w['w']+'}t','{'+w['w']+'}br','{'+w['w']+'}tab'});normalize=lambda s:re.sub(r'\\s+',' ',s).strip()
 position=0;flat=normalize(text)
 for chunk in expected['text']:
  wanted=normalize(chunk);index=flat.find(wanted,position);assert index>=0,repr(chunk);position=index+len(wanted)
 assert '8 English source segments' in text and 'Fictional assessment <script>literal</script> 😀' in text
 assert 'Separate passage note 😀' in text and 'question remains unanswered' in text
 assert 'Source SHA-256:' in text and '/transcript/data/0' in text
 assert len(doc.findall('.//w:tbl',w))==2
 assert len(doc.findall('.//w:tblHeader',w))==2
 assert doc.findall('.//w:br',w) and doc.findall('.//w:tab',w) and doc.findall('.//w:numPr',w)
 relations=list(parts['word/_rels/document.xml.rels'])
 external={r.attrib['Target'] for r in relations if r.attrib.get('TargetMode')=='External'}
 assert external=={x for x in expected['links'] if x.startswith('https://')}
 assert all(r.attrib['Type'].endswith('/hyperlink') for r in relations if r.attrib.get('TargetMode')=='External')
 bookmarks={x.attrib['{'+w['w']+'}name'] for x in doc.findall('.//w:bookmarkStart',w)}
 assert all(h.attrib['{'+w['w']+'}anchor'] in bookmarks for h in doc.findall('.//w:hyperlink',w) if '{'+w['w']+'}anchor' in h.attrib)
 assert len(doc.findall('.//w:bookmarkStart',w))==3
 assert not doc.findall('.//w:object',w) and not doc.findall('.//w:altChunk',w)
 print('PASS: independent native OOXML/CRC/XML parsing, complete rendered text, exact source hyperlinks, bookmarks, editable country tables, lists, Unicode and notes; no macros or remote media')
`,await download.path()],{input:JSON.stringify(snapshot),encoding:'utf8'});assert.equal(check.status,0,check.stderr);process.stdout.write(check.stdout);
 assert.equal(await page.locator('#reportPreview').innerHTML(),before);assert.equal(requests.length,0);
 await page.locator('#openCollection').setInputFiles(file);await page.locator('#replaceReport[open]').waitFor();await page.locator('#keepCurrentReport').click(); // Word alone does not mark resumable work saved.
 const [json]=await Promise.all([page.waitForEvent('download'),page.locator('#saveReport').click()]);assert.equal(download.suggestedFilename().replace('.docx','.json'),json.suggestedFilename());assert.deepEqual(JSON.parse(fs.readFileSync(await json.path())).corpora,corpora);
 const originalBytes=fs.readFileSync(await download.path());
 await page.evaluate(size=>{window.wordLimit=UNMeetingReport.LIMIT;UNMeetingReport.LIMIT=size;},originalBytes.length);
 const [exact]=await Promise.all([page.waitForEvent('download'),page.locator('#downloadWord').click()]);assert.deepEqual(fs.readFileSync(await exact.path()),originalBytes);await page.evaluate(()=>{UNMeetingReport.LIMIT=window.wordLimit;});
 let unexpected=0;page.on('download',()=>unexpected++);
 for(const limit of [100,originalBytes.length-1]){
  await page.evaluate(limit=>{window.wordLimit=UNMeetingReport.LIMIT;UNMeetingReport.LIMIT=limit;},limit);await page.locator('#downloadWord').click();assert.match(await page.locator('#wordStatus').innerText(),/exceeds 25 MB/);assert.equal(unexpected,0);assert.equal(await page.locator('#reportPreview').innerHTML(),before);assert(!(await page.locator('#saveReport').isDisabled()));await page.evaluate(()=>{UNMeetingReport.LIMIT=window.wordLimit;});
 }
 await page.evaluate(()=>{window.reportRenderer=UNMeetingReport.reportHTML;UNMeetingReport.reportHTML=(...args)=>window.reportRenderer(...args)+String.fromCharCode(1);});await page.locator('#downloadWord').click();assert.match(await page.locator('#wordStatus').innerText(),/unsupported control character/);assert.equal(unexpected,0);await page.evaluate(()=>{UNMeetingReport.reportHTML=window.reportRenderer;});
 // ZIP overhead is counted independently of the report HTML preflight bound.
 const boundary=await page.evaluate(()=>{const bytes=UNMeetingReportPackage.zip([{name:'word/test.xml',bytes:new Uint8Array([1,2,3])}]);const old=UNMeetingReport.LIMIT;try{UNMeetingReport.LIMIT=bytes.length;UNMeetingReportPackage.zip([{name:'word/test.xml',bytes:new Uint8Array([1,2,3])}]);UNMeetingReport.LIMIT=bytes.length-1;try{UNMeetingReportPackage.zip([{name:'word/test.xml',bytes:new Uint8Array([1,2,3])}]);return false;}catch{return true;}}finally{UNMeetingReport.LIMIT=old;}});assert(boundary);
 await page.locator('#analystNotes').fill('Changed assessment');assert(await page.locator('#downloadWord').isDisabled());await page.locator('#prepareReport').click();assert(!(await page.locator('#downloadWord').isDisabled()));
 for(const width of [390,1440]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));}
 assert.deepEqual(errors,[]);console.log('PASS: browser-only Word download, matching timestamp, unchanged full coverage and JSON, dirty-work protection, size/control refusal without truncation or lost work, stale-export prevention, mobile and no transcript requests');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));});
