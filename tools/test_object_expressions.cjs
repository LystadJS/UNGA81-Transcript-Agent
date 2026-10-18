'use strict';
const assert=require('node:assert/strict');
const Q=require('../site/meeting-quick-reader.js');
const issue=Q.ISSUES.find(i=>i.id==='humanitarian');
for(const text of [
  'We condemn attacks targeting humanitarian aid convoys and humanitarian workers.',
  'We also condemn the growing targeting of humanitarian personnel whose lives are at risk.'
]) {
  const [e]=Q.expressions(text,issue);
  assert.equal(e.expression_label,'Condemns');
  assert.match(e.expression_object,/attacks|targeting/);
  assert.ok(!e.expression_label.includes('opposition'));
}
const [support]=Q.expressions('We support unhindered humanitarian access.',issue);
assert.equal(support.expression_label,'Supports');assert.equal(support.expression_object,'unhindered humanitarian access');
const [oppose]=Q.expressions('We oppose restrictions on humanitarian access.',issue);
assert.equal(oppose.expression_label,'Opposes');assert.equal(oppose.expression_object,'restrictions on humanitarian access');
assert.equal(Q.expressions('Another country said we support humanitarian assistance.',issue).length,0);
assert.equal(Q.expressions('We support no humanitarian assistance.',issue).length,0);
const slug='sc/synthetic';
const row=(id,text)=>({id:slug+'#'+id,meeting_slug:slug,language:'en',country:'Illustrative',region:'Africa',text,source_url:'https://transcripts.un.org/en/'+slug,attribution:{country_status:'registry_mapped'},speaker_metadata:{function:'Representative'}});
const q=Q.build([row(0,'We support humanitarian assistance for displaced families and vulnerable children across the region.'),row(1,'We oppose restrictions on humanitarian assistance for displaced families and vulnerable children.')],{meeting_slug:slug});
assert.equal(q.positions.length,2);assert.deepEqual(new Set(q.positions.map(x=>x.expression_label)),new Set(['Supports','Opposes']));
assert.ok(q.positions.every(x=>x.expression_object&&x.evidence.length));
console.log('PASS object-specific actions preserve support for aid and condemnation of attacks, without merging different objects');
