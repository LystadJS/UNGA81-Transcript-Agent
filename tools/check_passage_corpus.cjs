'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const C=require('../research/corpus/contract.cjs');
const root=path.join(__dirname,'../research/corpus'),read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const frame=read(path.join(root,'frame.json')),plan=read(path.join(root,'plan.json')),inventory=read(path.join(root,'inventory.json'));
assert.equal(C.makeFrame(inventory,plan).sha256,frame.sha256,'Frozen frame does not reproduce');
const dev=frame.meetings.filter(m=>m.split==='development'),holdout=frame.meetings.filter(m=>m.split==='holdout');
assert.equal(dev.length,21);assert.equal(holdout.length,37);
assert(dev.every(m=>!holdout.some(h=>h.meeting_id===m.meeting_id||h.date===m.date)));
const result={schema:'un.passage-frame-check.v1',status:'PASS',frame_sha256:frame.sha256,plan_sha256:frame.plan.sha256,inventory_sha256:frame.inventory_sha256,development_meetings:dev.length,holdout_meetings:holdout.length,development_transcript_flags:dev.filter(m=>m.has_transcript).length,holdout_transcript_flags:holdout.filter(m=>m.has_transcript).length,whole_meeting_and_date_disjoint:true,holdout_content_state:'reserved_not_downloaded',formal_independence_established:false};
if(process.argv[2]){
 const dir=process.argv[2],corpus=C.load(read(path.join(dir,'corpus.json'))),audit=C.audit(corpus);
 assert.equal(corpus.frame.sha256,frame.sha256);
 assert.equal(audit.holdout.transcripts_downloaded,0);
 assert(corpus.parent_coverage.every(p=>p.partitioned_code_points===p.observed_code_points));
 Object.assign(result,{corpus_sha256:corpus.sha256,counts:audit.counts,source_statuses:audit.source_statuses,unknown_country_passages:audit.unknown_country_passages,all_observed_code_points_accounted:true,heldout_opened:false,reviewed_speech_population:'pending_new_source_boundaries; existing owner pilot unchanged'});
}
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
