'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const R=require('../site/meeting-report-core.js'),F=require('./meeting_report_fixture.cjs');
const policy=JSON.parse(fs.readFileSync(require.resolve('../site/reporting-exclusions.json')));
const clone=x=>JSON.parse(JSON.stringify(x));
(async()=>{
 const a=await F.corpus(),b=await F.corpus(1),original=JSON.stringify([a,b]);
 await R.validateCorpora([a,b],policy,F.countries);
 assert.equal(R.allowed('2026-10-05',null,policy),false);
 for(const slug of policy.meetings)assert.equal(R.allowed(F.date,slug,policy),false);
 for(const bad of ['source','text','country','speaker','date','duplicate','reserved','legacy','identity','locator','meeting']){
  const c=clone(a);
  if(bad==='source')c.provenance.sources.find(s=>s.kind==='transcript').raw+=' ';
  if(bad==='text')c.records[0].text='invented';
  if(bad==='country')c.records[0].country='Other';
  if(bad==='speaker')c.records[0].speaker_metadata.group=null;
  if(bad==='speaker')c.records[2].speaker_metadata.group=null;
  if(bad==='date')c.records[0].date='2026-11-09';
  if(bad==='duplicate')c.records.push(c.records[0]);
  if(bad==='reserved')c.collection.start='2026-10-05';
  if(bad==='legacy')c.records[0].legacy_provenance_unavailable=true;
  if(bad==='identity')c.records.push({...c.records[0],id:'invented-copy'});
  if(bad==='locator')c.records[0].source_url='https://transcripts.un.org/en/sc/10900';
  if(bad==='meeting')c.coverage[0].title='Invented meeting';
  await assert.rejects(R.validateCorpora([c],policy,F.countries),undefined,bad);
 }
 await assert.rejects(R.validateCorpora([a,a],policy,F.countries));
 const report=R.build([a,b],[F.meetings[0].slug],{mission:'Example mission',priorities:'humanitarian access',notes:'Owner interpretation only'});
 assert.equal(report.meetings.length,1);assert.equal(report.records.length,4);assert.equal(report.priority_evidence.length,2);
 assert.equal(report.model_status,'withheld_not_accepted');assert.equal(report.meetings[0].summary.stats.withheld_collective_segments,1);
 assert(!report.meetings[0].summary.positions.some(p=>p.issue_id==='humanitarian'));
 assert.equal(R.search(report.records,'😀').length,1);
 const h=R.standalone({...report,settings:{...report.settings,template:'evidence',notes:'<script>alert(1)</script>'}});
 assert(!h.includes('<script>'));assert(h.includes('&lt;script&gt;'));assert(h.includes('&lt;img'));assert(h.includes('No matching U.S.')||h.includes('Matching policy wording'));
 assert(!h.includes('<nav class="report-meeting-index"'));
 const multi=R.build([a,b],F.meetings.map(m=>m.slug)),before=JSON.stringify(multi),csvBefore=R.evidenceCSV(multi.records);
 for(const template of Object.keys(R.TEMPLATES)){
  const rendered=R.reportHTML({...multi,settings:{...multi.settings,template}});
  assert.equal((rendered.match(/href="#report-meeting-[12]"/g)||[]).length,2);
  assert.equal((rendered.match(/href="#report-meeting-index"/g)||[]).length,2);
  assert.equal((rendered.match(/4 loaded source segments/g)||[]).length,2);
  assert(rendered.includes('Counts describe loaded evidence, not completeness or policy importance.'));
 }
 const many={...multi,meetings:Array.from({length:100},(_,i)=>({...multi.meetings[i%2],title:'Repeated <img> title',status:i?'downloaded':'unavailable'}))};
 const longHTML=R.standalone(many),anchors=[...longHTML.matchAll(/id="(report-meeting-\d+)"/g)].map(m=>m[1]);
 assert.equal(anchors.length,100);assert.equal(new Set(anchors).size,100);for(const id of anchors)assert(longHTML.includes('href="#'+id+'"'));
 assert(longHTML.includes('Repeated &lt;img&gt; title'));assert(longHTML.includes('Collection outcome: unavailable'));assert(!longHTML.includes('<script'));
 assert.equal(JSON.stringify(multi),before);assert.equal(R.evidenceCSV(multi.records),csvBefore);
 assert(R.evidenceCSV([{text:'=cmd()',country:'\t+formula'}]).includes("'=cmd()"));
 assert.equal(JSON.stringify([a,b]),original);
 assert.throws(()=>R.build([a],[],{}));assert.throws(()=>R.settings({template:'foreign'}));
 console.log('PASS: reporting provenance, actor tampering, 37 exclusions, source selection, collective boundaries, Unicode search, safe exports and input immutability');
})().catch(e=>{console.error(e);process.exitCode=1;});
