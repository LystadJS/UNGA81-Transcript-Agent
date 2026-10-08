'use strict';
const assert=require('node:assert/strict');const crypto=require('node:crypto');
const Q=require('../../site/meeting-quick-reader.js'),B=require('./quick_reader_benchmark.cjs');
let count=0;const test=(name,fn)=>{fn();count++;console.log('PASS',name)};
const rec=(id,text,opts={})=>({id:'ga/c3/81/1#'+id,meeting_slug:'ga/c3/81/1',date:'2026-10-01',language:'en',
 text,country:'Country A',region:'Africa',source_url:'https://transcripts.un.org/en/ga/c3/81/1',
 attribution:{country_status:'registry_mapped'},speaker_metadata:{affiliation_full:'Country A',function:'Permanent Representative',group:opts.group||null}});
test('Collective first person delivered on behalf of list withheld',()=>{
 const x=rec(1,'I have the honor of delivering the statement on behalf of a group of several Member States. We strongly condemn racial discrimination across all regions.');
 assert.equal(Q.collectiveAttribution(x),true);assert.equal(Q.build([x],{meeting_slug:x.meeting_slug}).positions.length,0);
});
test('National alignment followed by national capacity is not group delivery',()=>{const x=rec(2,'We align ourselves with the regional group, but we make our own remarks in national capacity. We firmly support humanitarian access.');assert.equal(Q.collectiveAttribution(x),false);assert.equal(Q.build([x],{meeting_slug:x.meeting_slug}).positions.length,1)});
test('Explicit group metadata withholds individual positions',()=>{const x=rec(3,'We support humanitarian access in affected areas.',{group:'Coalition of Fifteen'});assert.equal(Q.build([x],{meeting_slug:x.meeting_slug}).positions.length,0)});
test('International humanitarian law does not imply support/opposition to humanitarian assistance',()=>{const x=rec(4,'We condemn grave violations of international humanitarian law that occurred during the conflict.');assert.equal(Q.build([x],{meeting_slug:x.meeting_slug}).positions.some(p=>p.issue_id==='humanitarian'),false)});
test('Welcoming a report about human rights is not broad support',()=>{const x=rec(5,'We welcome the report of the Office of the High Commissioner for Human Rights and thank the experts.');assert.equal(Q.build([x],{meeting_slug:x.meeting_slug}).positions.length,0)});
test('Concern about individual subject to sanctions not a sanctions stance',()=>{const x=rec(6,'We are concerned that an individual subject to EU restrictive sanctions was given the floor and we reject his presentation.');assert.equal(Q.build([x],{meeting_slug:x.meeting_slug}).positions.length,0)});
test('Direct targeted expressions remain detectable',()=>{const x=rec(7,'We strongly support humanitarian assistance for civilians in the region and request safe access for all affected families.');assert.equal(Q.build([x],{meeting_slug:x.meeting_slug}).positions[0].classification,'support_or_advocacy_expressed')});
function sample(){
 const c=[{id:'position:a',kind:'position',source_id:'a',source_sha256:'x',current_classification:null},
 {id:'position:b',kind:'position',source_id:'b',source_sha256:'y',current_classification:'support_or_advocacy_expressed'},
 {id:'context:c',kind:'context',source_id:'c',source_sha256:'z'},
 {id:'abstention:d',kind:'abstention',source_id:'d',source_sha256:'w'}];
 const packet={schema:'un.quick-reader-adjudication-benchmark.v1',corpus_sha256:B.DIGEST,coverage:{additional_meetings:13},cases:c};packet.case_binding_sha256=B.bindingFor(packet);
 const review={schema:'un.quick-reader-adjudication-choices.v1',case_binding_sha256:packet.case_binding_sha256,reviewer_type:'assistant_provisional',choices:[
 {id:'position:a',source_id:'a',source_sha256:'x',labels:{attribution:'collective_or_non_country',stance:'supported_expression'},note:'Group spokesman rather than national statement'},
 {id:'position:b',source_id:'b',source_sha256:'y',labels:{attribution:'individual_country',stance:'supported_expression'},note:'Direct national expression in the source'},
 {id:'context:c',source_id:'c',source_sha256:'z',labels:{context:'missed'},note:'The source topic is not shown in synopsis'},
 {id:'abstention:d',source_id:'d',source_sha256:'w',labels:{abstention:'appropriate_withhold'},note:'Only a procedural speech occurred'}]};return {packet,review};
}
const mustFail=(f)=>assert.throws(f);
test('Four metrics have independent denominators',()=>{let {packet,review}=sample(),s=B.evaluate(packet,review);assert.equal(s.attribution_precision.value,.5);assert.equal(s.stance_precision.value,1);assert.equal(s.joint_correct.share,.5);assert.equal(s.context_coverage.value,0);assert.equal(s.abstention_correct_withhold_fraction.value,1)});
test('Revised case precision uses only retained cases',()=>{let {packet,review}=sample(),s=B.evaluate(packet,review);assert.equal(s.revised_joint_correct.assessable,1);assert.equal(s.revised_joint_correct.share,1)});
test('Partial review returns missing and null denominators',()=>{let {packet,review}=sample();review.choices=[];let s=B.evaluate(packet,review);assert.equal(s.context_coverage.value,null);assert.equal(s.coverage.unreviewed,4)});
test('Uncertain adjudications not counted as correct',()=>{let {packet,review}=sample();review.choices[0].labels.stance='uncertain';let s=B.evaluate(packet,review);assert.equal(s.stance_precision.uncertain,1);assert.equal(s.stance_precision.assessable,1)});
test('Duplicate review choice rejected',()=>{let {packet,review}=sample();review.choices.push(review.choices[0]);mustFail(()=>B.evaluate(packet,review))});
test('Tampered predicted-state flag cannot inflate revised precision',()=>{let {packet,review}=sample();packet.cases[0].current_classification='support_or_advocacy_expressed';mustFail(()=>B.evaluate(packet,review))});
test('Review source hash modification rejected',()=>{let {packet,review}=sample();review.choices[0].source_sha256='tampered';mustFail(()=>B.evaluate(packet,review))});
test('Unknown source ID rejected',()=>{let {packet,review}=sample();review.choices[0].id='position:unseen';mustFail(()=>B.evaluate(packet,review))});
test('Wrong review lock rejected',()=>{let {packet,review}=sample();review.case_binding_sha256='wrong';mustFail(()=>B.evaluate(packet,review))});
test('Unknown category rejected',()=>{let {packet,review}=sample();review.choices[0].labels.stance='policy_ally';mustFail(()=>B.evaluate(packet,review))});
test('Unconfirmed human reviewer metadata rejected',()=>{let {packet,review}=sample();review.reviewer_type='owner_human';mustFail(()=>B.evaluate(packet,review,{allowHuman:true}))});
test('Assistant cannot represent human confirmation',()=>{let {packet,review}=sample();review.reviewer_type='owner_human';mustFail(()=>B.evaluate(packet,review))});
test('Human review requires explicit authorized path',()=>{let {packet,review}=sample();review.reviewer_type='owner_human';review.owner_confirmation=true;review.reviewer_name='Future reviewer';review.reviewed_at='2026-10-08T12:00:00Z';let s=B.evaluate(packet,review,{allowHuman:true});assert.equal(s.reviewer_type,'owner_human')});
test('Missing reasoning rejected',()=>{let {packet,review}=sample();review.choices[0].note='';mustFail(()=>B.evaluate(packet,review))});
test('Missing task label rejected',()=>{let {packet,review}=sample();delete review.choices[0].labels.stance;mustFail(()=>B.evaluate(packet,review))});
test('Wrong corpus rejected',()=>{let {packet,review}=sample();packet.corpus_sha256='incorrect';mustFail(()=>B.evaluate(packet,review))});
test('Reserved metadata cannot substitute for development corpus',()=>{mustFail(()=>B.checked({schema:'un.passage-corpus.v1',sha256:B.DIGEST,frame:{holdout_state:'downloaded',meetings:[]}}))});
console.log(JSON.stringify({schema:'un.quick-reader-adjudication-tests.v1',passed:count,failed:0,source:'synthetic',holdout_transcripts_accessed:0}));
