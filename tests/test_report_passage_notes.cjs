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
  const old={...missing,schema,settings:{...missing.settings}};delete old.settings.questions;if(schema===R.LEGACY_VERSION)delete old.appendix;
  assert.deepEqual((await R.openSaved(old,policy,F.countries)).passage_notes,[]);
  await assert.rejects(R.openSaved({...old,passage_notes:notes},policy,F.countries));
 }
 const records=Array.from({length:101},(_,i)=>({id:'synthetic#'+i})),many=records.map(r=>({record_id:r.id,text:'x'}));
 assert.equal(R.passageNotes(many.slice(0,100),records).length,100);assert.throws(()=>R.passageNotes(many,records));
 assert.equal(R.passageNotes([{record_id:record.id,text:'x'.repeat(2000)}],baseline.records)[0].text.length,2000);
 assert(!JSON.stringify(R.exportPreferences({...report.settings,passage_notes:notes})).includes('user note'));
 // Parse with an independent CSV reader, including formulas, quotes and line breaks.
 const parseCSV=value=>{const r=require('node:child_process').spawnSync('python',['-c','import csv,json,sys; print(json.dumps(list(csv.DictReader(sys.stdin))))'],{input:value,encoding:'utf8'});assert.equal(r.status,0,r.stderr);return JSON.parse(r.stdout);};
 const csvNote=' \t=HYPERLINK("https://example.invalid","check")\r\nSecond line, 😀';
 const noteReport=R.build(corpora,selected,{notes:'Excluded report-level assessment'},undefined,[{record_id:record.id,text:csvNote}]);
 const frozen=JSON.stringify(noteReport),rows=parseCSV(R.passageNotesCSV(noteReport));assert.equal(rows.length,1);
 const row=rows[0];assert.equal(row.analyst_note,"'"+csvNote);assert.equal(row.note_type,'User-authored interpretation');assert.equal(row.report_generated_at,noteReport.generated_at);
 for(const key of ['id','meeting_slug','date','country','source_url','source_id','source_version','raw_sha256','text_sha256','json_pointer'])assert.equal(row[key],String(record[key]??''));
 assert(!Object.hasOwn(row,'text'));assert(!R.passageNotesCSV(noteReport).includes('Excluded report-level assessment'));assert(!R.passageNotesCSV(noteReport).includes(corpora[1].records[0].id));
 assert.deepEqual(parseCSV(R.passageNotesCSV(baseline)),[]);assert.equal(JSON.stringify(noteReport),frozen);
 for(const prefix of ['=','+','-','@',' \t=']){const r={...noteReport,passage_notes:[{record_id:record.id,text:prefix+'check'}]};assert.equal(parseCSV(R.passageNotesCSV(r))[0].analyst_note,"'"+prefix+'check');}
 for(const passage_notes of [[...notes,...notes],[{record_id:corpora[1].records[0].id,text:'outside selected meetings'}]])assert.throws(()=>R.passageNotesCSV({...noteReport,passage_notes}));
 assert.equal(R.evidenceCSV(report.records),R.evidenceCSV(baseline.records));
 assert.equal(JSON.stringify(corpora),original);assert.equal(report.model_status,'withheld_not_accepted');
 console.log('PASS: source-bound passage notes, separate escaped interpretation, unchanged source/summary/CSV, v1/v2/v3 replay, duplicate/out-of-scope/type/length/count rejection and source immutability and independently parsed, formula-safe source-bound notes CSV');
})().catch(e=>{console.error(e);process.exitCode=1;});
