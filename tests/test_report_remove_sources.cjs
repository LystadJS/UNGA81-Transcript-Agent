/* Removal plans keep complete source bundles and only prune linked annotations. */
'use strict';
const assert=require('node:assert/strict'),R=require('../site/meeting-report-core.js'),F=require('./meeting_report_fixture.cjs');
(async()=>{
 const a=await F.corpus(),b=await F.corpus(1),corpora=[a,b],original=JSON.stringify(corpora);
 const state={selected:corpora.flatMap(c=>c.coverage.map(m=>m.slug)),appendix:{mode:'selected',record_ids:[a.records[0].id,b.records[0].id]},passage_notes:[{record_id:a.records[0].id,text:'A note'},{record_id:b.records[0].id,text:'B note'}]},snapshot=JSON.stringify(state);
 const plan=R.planSourceRemoval(corpora,0,state);
 assert.deepEqual(plan.corpora,[b]);assert.equal(plan.corpora[0],b);assert.deepEqual(plan.selected,[F.meetings[1].slug]);assert.deepEqual(plan.passage_notes,[state.passage_notes[1]]);assert.deepEqual(plan.appendix.record_ids,[b.records[0].id]);assert.equal(plan.removed_notes,1);assert.equal(plan.removed_appendix,1);assert.equal(plan.clear_assessment,false);
 const last=R.planSourceRemoval(plan.corpora,0,plan);assert.deepEqual(last.corpora,[]);assert.deepEqual(last.selected,[]);assert.deepEqual(last.passage_notes,[]);assert.deepEqual(last.appendix,{mode:'template',record_ids:[]});assert(last.clear_assessment);
 const unchecked=R.planSourceRemoval(corpora,0,{selected:[F.meetings[1].slug],appendix:{mode:'selected',record_ids:[b.records[0].id]},passage_notes:[state.passage_notes[1]]});assert.equal(unchecked.removed_notes,0);assert.equal(unchecked.removed_appendix,0);assert.deepEqual(unchecked.passage_notes,[state.passage_notes[1]]);
 // A collection with multiple meetings is removed as one original bundle.
 const multi={coverage:[...a.coverage,...b.coverage],records:[...a.records,...b.records]};const whole=R.planSourceRemoval([multi],0,state);assert.equal(whole.removed_meetings.length,2);assert.equal(whole.removed_notes,2);assert(whole.clear_assessment);
 for(const index of [-1,2,0.5])assert.throws(()=>R.planSourceRemoval(corpora,index,state),/Source list changed/);
 assert.throws(()=>R.planSourceRemoval(corpora,0,{...state,selected:['unknown']}),/Invalid current/);
 assert.throws(()=>R.planSourceRemoval(corpora,0,{...state,passage_notes:[{record_id:'unknown',text:'unsafe'}]}));
 assert.equal(JSON.stringify(corpora),original);assert.equal(JSON.stringify(state),snapshot);
 console.log('PASS: whole-bundle removal, exact kept source identity, selective note/appendix pruning, unchecked sources, last-assessment clear plan, invalid state refusal and input immutability');
})().catch(e=>{console.error(e);process.exitCode=1;});
