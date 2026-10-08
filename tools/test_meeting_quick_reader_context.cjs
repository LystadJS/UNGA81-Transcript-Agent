'use strict';
/** Synthetic-only adversarial validation of attribution, contradictory clauses, and context. */
const assert=require('node:assert/strict');
const Q=require('../site/meeting-quick-reader.js');
const ID='ga/c4/81/1', URL='https://transcripts.un.org/en/'+ID;
const make=(n,text,options={})=>({
  id:ID+'#'+n,meeting_slug:ID,date:'2099-01-01',language:'en',meeting:'SYNTHETIC committee meeting',
  text,source_url:URL,text_sha256:'a'.repeat(64),json_pointer:'/transcript/data/'+n,
  country:options.country||'Illustrative Country',region:options.region||'Africa',
  attribution:{country_status:options.mapped===false?'unresolved':'registry_mapped'},
  speaker_metadata:{affiliation_full:options.country||'Illustrative Country',function:options.function||'Representative',group:options.group||null}
});
function read(rows){return Q.build(rows.map(r=>({...r,text:r.text+' This additional artificial context adds no diplomatic policy position.'})),{meeting_slug:ID,meeting_date:'2099-01-01',title:'SYNTHETIC committee meeting'});}
let count=0;
function test(name,run){run();console.log('PASS',name);count++;}
const sub='Thank you, Mr. Chair. '+Array(9).fill('This public discussion addresses fundamental human rights and transparent accountability.').join(' ');
test('long courtesies do not discard substantive national remarks',()=>assert(Q.isSubstantive(sub)));
test('short procedural courtesies do not manufacture substance',()=>assert(!Q.isSubstantive('Thank you, Mr. Chair. I now give the floor to the next speaker.')));
test('short courteous opening with substantive issue remains accessible',()=>assert(Q.isSubstantive('Thank you, Chair. We support humanitarian assistance and safe access to food security.')));
test('decolonization is an explicit independent issue family',()=>assert(Q.ISSUES.some(x=>x.id==='decolonization'&&x.pattern.test('decolonization and self-determination'))));
test('crime-prevention topics do not appear as a silent issue-dictionary miss',()=>assert(Q.ISSUES.some(x=>x.id==='justice'&&x.pattern.test('criminal justice'))));
test('institutional label does not automatically tag generic international cooperation',()=>assert(!Q.ISSUES.find(x=>x.id==='institutions').pattern.test('international cooperation')));
test('speaker speaking for a multi-country group is not a single-country position',()=>{
 const r=make(1,'I have the honour to speak on behalf of the Nordic-Baltic States. We support humanitarian assistance in this region.');
 assert(Q.collectiveAttribution(r));assert.equal(read([r]).positions.length,0);
});
test('metadata group coalition withholds national attribution',()=>{
 const r=make(1,'We support humanitarian assistance to displaced persons.',{group:'Group of Friends'});
 assert(Q.collectiveAttribution(r));assert.equal(read([r]).positions.length,0);
});
test('national speaker citing a third-party group is not mistaken for group representative',()=>{
 const r=make(1,'Illustrative Country aligns itself with the statement delivered by the union on behalf of the member states. I now add observations in my national capacity. We support humanitarian assistance to displaced families.');
 assert(!Q.collectiveAttribution(r));assert.equal(read([r]).positions.length,1);
});
test('national delegation group metadata remains permissible',()=>{
 const r=make(1,'We support humanitarian assistance to displaced families.',{group:'National delegation'});
 assert.equal(read([r]).positions.length,1);
});
test('long-distance support for a procedural call is not support for distant topic',()=>{
 const r=make(1,'We support the call contained in the latest report of the agency to examine alleged concerns at the Security Council.');
 assert.equal(read([r]).positions.length,0);
});
test('direct support with a nearby issue object is retained',()=>{
 const q=read([make(1,'We support humanitarian assistance for displaced families and improved relief access.')]);
 assert.equal(q.positions[0].classification,'support_or_advocacy_expressed');
});
test('explicit rejection is not misclassified as support',()=>{
 const q=read([make(1,'We do not support sanctions on essential food and medical supplies.')]);
 assert.equal(q.positions[0].classification,'concern_or_opposition_expressed');
});
test('opposing clauses on the SAME subject yield a mixed descriptor',()=>{
 const q=read([make(1,'We support humanitarian assistance for the displaced, but we oppose humanitarian assistance without transparent monitoring.')]);
 assert.equal(q.positions[0].classification,'mixed_or_qualified');
});
test('opposing actions on DIFFERENT subjects do not imply a contradiction',()=>{
 const q=read([make(1,'We support humanitarian assistance but we oppose sanctions on food security.')]);
 assert.equal(q.positions.find(x=>x.issue_id==='humanitarian').classification,'support_or_advocacy_expressed');
 assert.equal(q.positions.find(x=>x.issue_id==='sanctions').classification,'concern_or_opposition_expressed');
});
test('explicit conditional language prevents an unqualified position',()=>{
 const q=read([make(1,'We support humanitarian assistance, provided that neutral agencies monitor delivery.')]);
 assert.equal(q.positions[0].classification,'mixed_or_qualified');
});
test('reported third-party positions stay unclassified',()=>{
 const r=make(1,'We heard that another country would support sanctions on medicine, but we have not considered the proposal.');
 assert.equal(read([r]).positions.length,0);
});
test('unresolved metadata stays unresolved even if first-person language appears',()=>{
 const q=read([make(1,'We support humanitarian assistance for displaced persons.',{mapped:false,region:'Unmapped'})]);
 assert.equal(q.stats.unresolved_country_segments,1);assert.equal(q.positions.length,0);
});
test('mapped-but-unresolved region is not accidentally counted as verified',()=>{
 const q=read([make(1,'We support humanitarian assistance for displaced persons.',{region:'Unmapped'})]);
 assert.equal(q.stats.mapped_country_segments,0);assert.equal(q.stats.unresolved_country_segments,1);assert.equal(q.positions.length,0);
});
test('two exact meeting agenda introductions remain available, not mistaken for official outcomes',()=>{
 const rows=[make(0,'We will now hold the interactive dialogue on the oral update on rights in Illustrative Place. This simulated procedural opening concerns the first agenda discussion.',{function:'Vice-President'}),
  make(1,'We will now hold the interactive dialogue with the Special Rapporteur on rights in Another Place. This introduction concerns a second simulated discussion.',{function:'Vice-President'})];
 const q=read(rows);assert.equal(q.agenda_cues.length,2);assert(q.agenda_cues.every(c=>c.source_url===URL));
});
test('generic speaker-list transitions do not replace substantive agenda cue',()=>{
 const q=read([make(0,'We will now hold the interactive dialogue on rights in Example Territory and will present the oral report.',{function:'Vice-President'}),
  make(1,'We shall now turn to the list of speakers for the remaining participants and their organizations.',{function:'Vice-President'})]);
 assert.equal(q.agenda_cues.length,1);
});
test('an opening agenda cue is independent of topic-filtered detailed analysis',()=>{
 const q=read([make(0,'We will now hold the interactive dialogue on developments in Territory A.',{function:'Vice-President'}),make(1,'We support humanitarian assistance to displaced communities.')]);
 assert.equal(q.sources,'all_english_source_segments_in_exact_selected_meeting_before_topic_filter');assert.equal(q.agenda_cues.length,1);
});
test('positions retain source hash and original JSON pointer when present',()=>{
 const q=read([make(4,'We support humanitarian assistance to displaced communities.')]);
 assert.equal(q.positions[0].evidence[0].text_sha256,'a'.repeat(64));assert.equal(q.positions[0].evidence[0].json_pointer,'/transcript/data/4');
});
test('no information is obtained from other meetings',()=>{
 const other=make(0,'We support humanitarian assistance.');other.meeting_slug='ga/81/20';other.id='ga/81/20#0';
 assert.equal(read([other]).stats.source_segments,0);
});
test('counts and country position records remain source bounded and offline',()=>{
 const q=read([make(1,'We support humanitarian assistance and protect the affected families.')]);
 assert.equal(q.external_ai_calls,0);assert.equal(q.stats.source_segments,1);assert.equal(q.stats.recorded_countries,1);
});
console.log(JSON.stringify({schema:'un.quick-reader-context-tests.v1',tests:count,failed:0,synthetic:true,heldout_opened:0}));
