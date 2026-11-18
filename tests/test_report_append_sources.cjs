/* Source-only append preserves original identities and editor ownership. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const R=require('../site/meeting-report-core.js'),C=require('../site/collector.js'),F=require('./meeting_report_fixture.cjs');
const policy=JSON.parse(fs.readFileSync(require.resolve('../site/reporting-exclusions.json')));
(async()=>{
 const a=await F.corpus(),b=await F.corpus(1),original=JSON.stringify([a,b]);
 const report=R.build([a],[F.meetings[0].slug],{title:'Current report',notes:'Current assessment 😀'}, {mode:'selected',record_ids:[a.records[0].id]},[{record_id:a.records[0].id,text:'Keep current passage note'}]);
 const added=await R.appendSaved([a],b,policy,F.countries);assert.deepEqual(added.corpora,[a,b]);assert.deepEqual(added.selected_added,[F.meetings[1].slug]);assert.equal(added.incoming_report,false);
 const foreign=R.savedReport(R.build([b],[F.meetings[1].slug],{title:'Foreign title',notes:'Do not copy'},undefined,[{record_id:b.records[0].id,text:'Foreign passage note'}]),[b]);
 const fromReport=await R.appendSaved([a],foreign,policy,F.countries);assert.deepEqual(fromReport.corpora,[a,b]);assert(fromReport.incoming_report);assert(!Object.hasOwn(fromReport,'settings'));assert(!Object.hasOwn(fromReport,'passage_notes'));
 const combined=R.build(added.corpora,[...report.selected_meetings,...added.selected_added],report.settings,report.appendix,report.passage_notes),state={settings:report.settings,selected:combined.selected_meetings,appendix:report.appendix,passage_notes:report.passage_notes};
 assert.equal(R.savedStateBytes(added.corpora,state),new TextEncoder().encode(JSON.stringify(R.savedReport(combined,added.corpora))).length);
 assert.equal(combined.settings.notes,report.settings.notes);assert.deepEqual(combined.passage_notes,report.passage_notes);assert.deepEqual(combined.appendix,report.appendix);assert.equal(combined.records.length,8);assert.deepEqual(R.countryTimeline(combined).map(c=>c.observations.length),[2,2]);
 const emptyTitle={...state,settings:{...state.settings,title:''}},normalized=R.build(added.corpora,state.selected,emptyTitle.settings,state.appendix,state.passage_notes);assert.equal(R.savedStateBytes(added.corpora,emptyTitle),new TextEncoder().encode(JSON.stringify(R.savedReport(normalized,added.corpora))).length);
 assert.doesNotThrow(()=>R.savedStateBytes(added.corpora,{...state,settings:{...state.settings,questions:[{heading:'Unfinished',query:''}]}}));
 await assert.rejects(R.appendSaved([],b,policy,F.countries),/Open a collection/);
 await assert.rejects(R.appendSaved([a],a,policy,F.countries),/Already loaded/);
 await assert.rejects(R.appendSaved([a],R.savedReport(R.build([a,b],[F.meetings[1].slug]),[a,b]),policy,F.countries),/Already loaded/); // Unselected bundles still count.
 const corrupt=structuredClone(b);corrupt.records[0].text='tampered source';await assert.rejects(R.appendSaved([a],corrupt,policy,F.countries));
 const revised=structuredClone(a);revised.collection.checked_at='2026-11-18T21:00:00Z';await assert.rejects(R.appendSaved([a],revised,policy,F.countries),/Already loaded/);
 const revision=await C.collect({start:F.date,end:F.date,scope:'all',meeting_slug:F.meetings[0].slug,meeting_date:F.date},F.countries,{request:async url=>{const data=new URL(url).pathname.endsWith('meetings.json')?{meetings:[F.meetings[0]],total:1,page:1,hasMore:false}:F.transcript(F.meetings[0]);if(data.transcript)data.transcript.data[0].paragraphs[0].sentences[0].text+=' A changed source revision.';const raw=JSON.stringify(data);return {data,raw,hash:await C.sha(raw),retrieved_at:'2026-11-18T21:00:00Z'};}});
 assert.notEqual(revision.records[0].raw_sha256,a.records[0].raw_sha256);await assert.rejects(R.appendSaved([a],revision,policy,F.countries),/Already loaded/);
 const reserved=structuredClone(b);reserved.collection.start=reserved.collection.end=policy.dates[0];await assert.rejects(R.appendSaved([a],reserved,policy,F.countries),/Reserved/);
 const badReport={...foreign,passage_notes:[{record_id:'missing#0',text:'x'}]};await assert.rejects(R.appendSaved([a],badReport,policy,F.countries));
 const existing=[a,b];
 for(let i=2;i<11;i++){
  const m={...F.meetings[0],slug:'ga/81/'+(900+i),pageUrl:'/en/ga/81/'+(900+i),jsonUrl:'/en/ga/81/'+(900+i)+'.json'};
  const corpus=await C.collect({start:F.date,end:F.date,scope:'all',meeting_slug:m.slug,meeting_date:F.date},F.countries,{request:async url=>{const data=new URL(url).pathname.endsWith('meetings.json')?{meetings:[m],total:1,page:1,hasMore:false}:F.transcript(m),raw=JSON.stringify(data);return {data,raw,hash:await C.sha(raw),retrieved_at:'2026-11-18T20:00:00Z'};}});
  if(i<10)existing.push(corpus);else await assert.rejects(R.appendSaved(existing,corpus,policy,F.countries),/ten source bundles/);
 }
 assert.equal(existing.length,10);assert.equal(JSON.stringify([a,b]),original);
 console.log('PASS: verified source/report append, unchanged originals and current notes/settings/appendix, foreign annotation exclusion, all-bundle overlap/revision/corruption refusal, ten-bundle cap, exact saved-JSON UTF-8 budget and unfinished-editor measurement');
})().catch(e=>{console.error(e);process.exitCode=1;});
