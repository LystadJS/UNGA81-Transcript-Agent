'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const R=require('../site/meeting-report-core.js'),F=require('./meeting_report_fixture.cjs');
const policy=JSON.parse(fs.readFileSync(require.resolve('../site/reporting-exclusions.json')));
(async()=>{
 const corpora=[await F.corpus(),await F.corpus(1)],original=JSON.stringify(corpora),ids=[F.meetings[0].slug];
 const baseline=R.build(corpora,ids,{template:'evidence'}),one=corpora[0].records[2].id;
 for(const template of Object.keys(R.TEMPLATES)){
  const report=R.build(corpora,ids,{template,notes:'Analyst interpretation'},{mode:'selected',record_ids:[one]});
  assert.deepEqual(report.meetings,baseline.meetings);assert.deepEqual(report.records,baseline.records);
  assert.deepEqual(report.priority_evidence,baseline.priority_evidence);assert.equal(report.records.length,4);
  assert.deepEqual(report.appendix_records,[corpora[0].records[2]]);assert.equal(report.model_status,'withheld_not_accepted');
  const saved=R.savedReport(report,corpora),opened=await R.openSaved(saved,policy,F.countries);
  const replay=R.build(opened.corpora,opened.selected,opened.settings,opened.appendix);
  assert.deepEqual(replay.appendix_records,report.appendix_records);assert.deepEqual(replay.meetings,report.meetings);
  assert.match(R.standalone(report),/Analyst-selected passages: 1 of 4/);
  assert.equal(R.evidenceCSV(report.records),R.evidenceCSV(baseline.records));
 }
 const empty=R.build(corpora,ids,{template:'evidence'},{mode:'selected',record_ids:[]});
 assert.equal(empty.appendix_records.length,0);assert.match(R.reportHTML(empty),/No appendix passages selected/);assert.deepEqual(empty.meetings,baseline.meetings);
 const ordered=R.build(corpora,ids,{}, {mode:'selected',record_ids:[corpora[0].records[3].id,one]});
 assert.deepEqual(ordered.appendix.record_ids,[one,corpora[0].records[3].id]);
 const saved=R.savedReport(baseline,corpora);
 for(const bad of [null,{}, {mode:'selected',record_ids:[one,one]}, {mode:'selected',record_ids:['missing#0']}, {mode:'selected',record_ids:[corpora[1].records[0].id]}, {mode:'selected',record_ids:[{}]}, {mode:'all',record_ids:[]}, {mode:'template',record_ids:[one]}, {mode:'selected',record_ids:[],notes:'extra'}]){
  assert.throws(()=>R.build(corpora,ids,{},bad));
  await assert.rejects(R.openSaved({...saved,appendix:bad},policy,F.countries));
 }
 const missing={...saved};delete missing.appendix;await assert.rejects(R.openSaved(missing,policy,F.countries));
 for(const selected_meetings of [undefined,null,[],[ids[0],ids[0]],['missing/1']])await assert.rejects(R.openSaved({...saved,selected_meetings},policy,F.countries));
 const legacy={...missing,schema:R.LEGACY_VERSION,derived_summary:'Untrusted invented claim'};delete legacy.passage_notes;
 const reopened=await R.openSaved(legacy,policy,F.countries),legacyReport=R.build(reopened.corpora,reopened.selected,reopened.settings,reopened.appendix);
 assert.equal(legacyReport.appendix_records.length,4);assert(!R.reportHTML(legacyReport).includes('Untrusted invented claim'));
 await assert.rejects(R.openSaved({...legacy,appendix:saved.appendix},policy,F.countries));
 const collection=await R.openSaved(corpora[0],policy,F.countries);assert.deepEqual(collection.appendix,{mode:'template',record_ids:[]});
 assert.equal(JSON.stringify(corpora),original);
 console.log('PASS: appendix selection independent of whole-meeting summaries/denominators/CSV, exact provenance, stable order, empty/invalid/out-of-scope/duplicate rejection, v1/v2 replay and immutable sources');
})().catch(e=>{console.error(e);process.exitCode=1;});
