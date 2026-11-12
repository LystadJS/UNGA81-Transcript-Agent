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
 for(const bad of ['source','text','country','speaker','date','duplicate','reserved']){
  const c=clone(a);
  if(bad==='source')c.provenance.sources.find(s=>s.kind==='transcript').raw+=' ';
  if(bad==='text')c.records[0].text='invented';
  if(bad==='country')c.records[0].country='Other';
  if(bad==='speaker')c.records[0].speaker_metadata.group=null;
  if(bad==='speaker')c.records[2].speaker_metadata.group=null;
  if(bad==='date')c.records[0].date='2026-11-09';
  if(bad==='duplicate')c.records.push(c.records[0]);
  if(bad==='reserved')c.collection.start='2026-10-05';
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
 assert(R.evidenceCSV([{text:'=cmd()',country:'\t+formula'}]).includes("'=cmd()"));
 assert.equal(JSON.stringify([a,b]),original);
 assert.throws(()=>R.build([a],[],{}));assert.throws(()=>R.settings({template:'foreign'}));
 console.log('PASS: reporting provenance, actor tampering, 37 exclusions, source selection, collective boundaries, Unicode search, safe exports and input immutability');
})().catch(e=>{console.error(e);process.exitCode=1;});
