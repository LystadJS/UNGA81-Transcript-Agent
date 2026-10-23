const assert=require('node:assert/strict'),crypto=require('node:crypto'),E=require('../../../site/issue-extraction'),O=require('../../../site/issue-ontology');
const record=(text,extra={})=>({id:crypto.createHash('sha256').update(text).digest('hex').slice(0,8),date:'2024-01-01',country:'Kenya',language:'en',text,text_sha256:crypto.createHash('sha256').update(text).digest('hex'),source_url:'https://transcripts.un.org/en/fixture',attribution:{country_status:'registry_mapped'},speaker_metadata:{function:'Representative'},...extra});
const yes=record('We call for humanitarian access in Sudan.'),description=record('Humanitarian access in Sudan remains restricted.'),group=record('We support protection of civilians in Gaza.',{speaker_metadata:{group:'Regional group'}}),conditional=record('We support humanitarian access in Sudan only if all parties agree.');
const result=E.extract([yes,yes,description,group,conditional]);assert.equal(result.observations.length,2);assert.equal(result.observations.find(e=>e.stance==='qualified').qualifications.length,1);assert.ok(result.observations.every(e=>!('excerpt' in e)&&e.review_state==='assistant_provisional'));assert.equal(E.extract([yes,{...yes,country:'Ghana'}]).observations.length,0);assert.equal(E.extract([{...yes,language:'fr'}]).observations.length,0);assert.throws(()=>E.toStore(result,{}));assert.equal(E.toStore(E.extract([yes]),{[yes.id]:'canonical-revision'})[0].source_revision,'canonical-revision');assert.deepEqual(O.resolve('humanitarian access and civilian protection').policy_ids,['humanitarian_access','civilian_protection']);assert.equal(O.resolve('aid spending').status,'unsupported');console.log('PASS humanitarian ontology, conservative source-bound extraction, conditions, collective and revision safeguards');

assert.deepEqual(O.resolve('humanitarian access in Sudan').contexts,['sudan']);
assert.deepEqual(O.resolve('protecting civilians in South Sudan').contexts,['south_sudan']);
assert.deepEqual(O.resolve('humanitarian access in Gaza').contexts,['gaza']);
assert.deepEqual(O.resolve('civilian protection in Israel and Palestine').contexts,['israel_palestine']);
assert.deepEqual(O.resolve('humanitarian access and civilian protection').contexts,[]);
assert.equal(O.resolve('humanitarian access in Ethiopia').context_warning,true);
assert.equal(O.resolve('humanitarian access in Ethiopia').unrecognized_qualifier,'Ethiopia');
assert.equal(O.resolve('safe unimpeded humanitarian access in Darfur').context_warning,false);
assert.deepEqual(O.resolve('safe unimpeded humanitarian access in Darfur').contexts,['sudan']);
assert.deepEqual(O.resolve('civilian protection in Gaza and Sudan').contexts,['sudan','gaza']);
console.log('PASS requested source-catalog contexts, South Sudan disambiguation, generic all-context scope and unknown qualifier warning');
