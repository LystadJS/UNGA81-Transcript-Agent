'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),R=require('../site/meeting-report-core.js'),F=require('./meeting_report_fixture.cjs');
const policy=JSON.parse(fs.readFileSync(require.resolve('../site/reporting-exclusions.json')));
(async()=>{
 const corpora=[await F.corpus(),await F.corpus(1)],selected=[F.meetings[0].slug],original=JSON.stringify(corpora);
 const questions=[{heading:'Access <script>?</script>',query:'humanitarian access'},{heading:'Unknown',query:'unmatched-example'}];
 const baseline=R.build(corpora,selected),report=R.build(corpora,selected,{questions});
 assert.equal(report.question_evidence[0].records.length,2);assert(report.question_evidence[0].records.every(r=>r.meeting_slug===selected[0]));assert.equal(report.question_evidence[1].records.length,0);
 assert.deepEqual(report.meetings,baseline.meetings);assert.deepEqual(report.records,baseline.records);assert.equal(R.evidenceCSV(report.records),R.evidenceCSV(baseline.records));
 const html=R.standalone(report);assert(html.includes('Access &lt;script&gt;'));assert(!html.includes('<script>'));assert(html.includes('question remains unanswered'));assert(html.includes('not generated answers'));assert(html.includes(report.records[2].raw_sha256));
 const saved=R.savedReport(report,corpora),opened=await R.openSaved({...saved,question_evidence:[{heading:'invented answer'}]},policy,F.countries);
 assert.deepEqual(opened.settings.questions,questions);assert.deepEqual(R.build(opened.corpora,opened.selected,opened.settings,opened.appendix,opened.passage_notes).question_evidence,report.question_evidence);
 assert.deepEqual(R.importPreferences(R.exportPreferences({questions})).questions,questions);
 const reversed=[...questions].reverse(),reordered=R.build(corpora,selected,{questions:reversed});
 assert.deepEqual(reordered.question_evidence.map(q=>q.heading),reversed.map(q=>q.heading));assert.deepEqual(reordered.meetings,report.meetings);assert.equal(R.evidenceCSV(reordered.records),R.evidenceCSV(report.records));assert.deepEqual(R.importPreferences(R.exportPreferences({questions:reversed})).questions,reversed);
 const reorderedHTML=R.standalone(reordered);assert(reorderedHTML.indexOf('<h3>Unknown</h3>')<reorderedHTML.indexOf('<h3>Access &lt;script&gt;?&lt;/script&gt;</h3>'));
 const reorderedSaved=R.savedReport(reordered,corpora),reorderedOpened=await R.openSaved(reorderedSaved,policy,F.countries);assert.deepEqual(reorderedOpened.settings.questions,reversed);
 const largeQuestions=Array.from({length:8},()=>({heading:'界'.repeat(160),query:'界'.repeat(300)}));assert.throws(()=>R.exportPreferences({questions:largeQuestions}),/8 KiB/);
 const largeReport=R.build(corpora,selected,{questions:largeQuestions}),largeSaved=R.savedReport(largeReport,corpora);assert.deepEqual((await R.openSaved(largeSaved,policy,F.countries)).settings.questions,largeQuestions);
 const legacyPrefs={schema:'un.mission-preferences.v1',settings:{template:'brief',mission:'',title:'Old report',priorities:''}};assert.deepEqual(R.importPreferences(legacyPrefs).questions,[]);
 const old={...saved,schema:R.NOTES_VERSION,settings:{...saved.settings}};delete old.settings.questions;assert.deepEqual((await R.openSaved(old,policy,F.countries)).settings.questions,[]);
 await assert.rejects(R.openSaved({...old,settings:saved.settings},policy,F.countries));
 const missing={...saved,settings:{...saved.settings}};delete missing.settings.questions;await assert.rejects(R.openSaved(missing,policy,F.countries));
 for(const bad of [null,{},Array(9).fill(questions[0]),[{heading:'',query:'x'}],[{heading:'h',query:' '}],[{heading:'h'.repeat(161),query:'x'}],[{heading:'h',query:'x'.repeat(301)}],[{heading:1,query:'x'}],[{...questions[0],answer:'invented'}]]){
  assert.throws(()=>R.build(corpora,selected,{questions:bad}));await assert.rejects(R.openSaved({...saved,settings:{...saved.settings,questions:bad}},policy,F.countries));assert.throws(()=>R.importPreferences({...R.exportPreferences({}),settings:{...R.exportPreferences({}).settings,questions:bad}}));
 }
 assert.equal(R.questions(Array(8).fill({heading:'h'.repeat(160),query:'q'.repeat(300)})).length,8);
 assert.equal(JSON.stringify(corpora),original);assert.equal(report.model_status,'withheld_not_accepted');console.log('PASS: ordered briefing questions and reusable/source-verified replay, bounds, selected-source citations, unanswered gaps, unchanged country coverage/CSV, safe HTML, v4 replay, v1-v3 report/v1 preferences compatibility and malformed import rejection');
})().catch(e=>{console.error(e);process.exitCode=1;});
