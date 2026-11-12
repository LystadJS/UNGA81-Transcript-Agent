'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const R=require('../site/meeting-report-core.js'),F=require('./meeting_report_fixture.cjs');
const policy=JSON.parse(fs.readFileSync(require.resolve('../site/reporting-exclusions.json')));
(async()=>{
 const corpora=[await F.corpus(),await F.corpus(1)],original=JSON.stringify(corpora),selected=[F.meetings[0].slug];
 const baseline=R.build(corpora,selected,{template:'brief'}),record=baseline.records[0],text='<script>user note</script>\nFollow up 😀';
 const notes=[{record_id:record.id,text}],report=R.build(corpora,selected,{},undefined,notes);
 assert.deepEqual(report.meetings,baseline.meetings);assert.deepEqual(report.records,baseline.records);assert.deepEqual(report.appendix,baseline.appendix);assert.equal(R.evidenceCSV(report.records),R.evidenceCSV(baseline.records));
 assert.deepEqual(report.passage_notes,notes);const html=R.standalone(report);assert(html.includes('&lt;script&gt;user note'));assert(!html.includes('<script>'));assert(html.includes('User-authored interpretation'));assert(html.includes(record.raw_sha256));assert(html.includes(record.json_pointer));
 const saved=R.savedReport(report,corpora),opened=await R.openSaved(saved,policy,F.countries);assert.deepEqual(opened.passage_notes,notes);
 const replay=R.build(opened.corpora,opened.selected,opened.settings,opened.appendix,opened.passage_notes);assert.deepEqual(replay.passage_notes,notes);assert.deepEqual(replay.meetings,baseline.meetings);
 for(const passage_notes of [null,{},[...notes,...notes],[{record_id:'missing#0',text:'x'}],[{record_id:corpora[1].records[0].id,text:'x'}],[{record_id:record.id,text:''}],[{record_id:record.id,text:'  '}],[{record_id:record.id,text:1}],[{record_id:record.id,text:'x'.repeat(2001)}],[{...notes[0],label:'support'}]]){
  assert.throws(()=>R.passageNotes(passage_notes,baseline.records));await assert.rejects(R.openSaved({...saved,passage_notes},policy,F.countries));
 }
 const missing={...saved};delete missing.passage_notes;await assert.rejects(R.openSaved(missing,policy,F.countries));
 for(const schema of [R.LEGACY_VERSION,R.APPENDIX_VERSION]){
  const old={...missing,schema};if(schema===R.LEGACY_VERSION)delete old.appendix;
  assert.deepEqual((await R.openSaved(old,policy,F.countries)).passage_notes,[]);
  await assert.rejects(R.openSaved({...old,passage_notes:notes},policy,F.countries));
 }
 const records=Array.from({length:101},(_,i)=>({id:'synthetic#'+i})),many=records.map(r=>({record_id:r.id,text:'x'}));
 assert.equal(R.passageNotes(many.slice(0,100),records).length,100);assert.throws(()=>R.passageNotes(many,records));
 assert.equal(R.passageNotes([{record_id:record.id,text:'x'.repeat(2000)}],baseline.records)[0].text.length,2000);
 assert(!JSON.stringify(R.exportPreferences({...report.settings,passage_notes:notes})).includes('user note'));
 assert.equal(JSON.stringify(corpora),original);assert.equal(report.model_status,'withheld_not_accepted');
 console.log('PASS: source-bound passage notes, separate escaped interpretation, unchanged source/summary/CSV, v1/v2/v3 replay, duplicate/out-of-scope/type/length/count rejection and source immutability');
})().catch(e=>{console.error(e);process.exitCode=1;});
