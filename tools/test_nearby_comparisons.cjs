'use strict';
const assert=require('node:assert/strict'),P=require('../site/position-comparison'),V=require('../site/position-view');
const {record,settings}=require('./test_position_comparison.cjs');
const policy=(c,d,text,extra={})=>record(c,d,text,extra);
const run=(rows,window=7)=>P.nearby(rows,rows,{...settings,nearbyDays:window},P.overview(rows,rows,settings));
let rows=[policy('Armenia',3,'We support the NPT.'),policy('United States',1,'We support the NPT.'),policy('United States',5,'We oppose the NPT.')];
let r=run(rows);assert.equal(r.rows.length,2);assert.deepEqual(r.rows.map(x=>x.day_difference),[-2,2]);assert.deepEqual(r.rows.map(x=>x.relationship),['same_policy_same_direction','same_policy_opposite_direction']);assert.ok(r.rows.every(x=>x.contributes_to_same_day_score===false));assert.equal(P.overview(rows,rows,settings).countries.find(c=>c.country==='Armenia').comparable_question_dates,0);
assert.equal(run(rows,1).rows.length,0);assert.equal(run(rows,0).rows.length,0);
const plan=policy('Armenia',1,'Guided by the CRC, Armenia is formulating a comprehensive national child protection strategy.');const priority=policy('United States',3,'We identify child protection as a national priority.');r=run([plan,priority]);assert.equal(r.rows.length,1);assert.equal(r.rows[0].relationship,'shared_priority_only');assert.equal(r.rows[0].day_difference,2);assert.match(V.renderNearby(r),/Shared priority only/);assert.match(V.renderNearby(r),/\+2/);assert.match(V.renderNearby(r),/do not contribute to the same-day score/);
for(const extra of [{speaker_metadata:{function:'Governor'}},{speaker_metadata:{function:'Mayor'}},{speaker_metadata:{group:'AOSIS'}}])assert.equal(run([plan,{...priority,...extra}]).rows.length,0);
for(const text of ['The report says we identify child protection as a national priority.','We oppose child protection.','Do we identify child protection as a national priority?','We identify climate finance as a national priority.'])assert.equal(run([plan,policy('United States',3,text)]).rows.length,0);
assert.equal(run([plan,priority,priority]).rows.length,1);
assert.equal(run([plan,policy('United States',3,'We identify child protection as a national priority.',{date:'2099-01-20'})]).rows.length,0);
rows=[policy('Armenia',3,'We support the NPT.'),policy('United States',1,'We support the NPT.'),policy('United States',2,'We support the NPT only if all parties agree.')];assert.equal(run(rows).rows.length,0,'closer qualified evidence must not be skipped for a more distant simple position');
rows=[policy('Armenia',1,'We support humanitarian access in Sudan.'),policy('United States',2,'We support humanitarian access in Gaza.')];assert.equal(run(rows).rows.length,0);
for(const value of [-1,15,1.5,'7',null])assert.throws(()=>P.options({...settings,nearbyDays:value}));assert.equal(P.options(settings).nearbyDays,7);
console.log('PASS nearby signed offsets, nearest ties, shared-vs-exact distinction, qualification blocking, context/date/attribution guards, repetition invariance, saved window and unchanged same-day scores (synthetic only)');

// Synthetic declarations exercise each additional object without publishing source transcripts.
for(const [id,object] of [['climate_finance','climate finance'],['torture_convention','accession to the Convention against Torture'],['human_rights_institutions','strengthening national human rights institutions'],['renewable_energy','renewable energy']]){
 const a=policy('Armenia',1,`We identify ${object} as a national priority.`),u=policy('United States',3,`We identify ${object} as a national priority.`);
 const result=run([a,u]);const row=result.rows.find(x=>x.policy.id===id+'_priority');assert.ok(row,id);assert.equal(row.relationship,'shared_priority_only');assert.equal(row.day_difference,2);assert.equal(row.contributes_to_same_day_score,false);assert.match(row.qualification,/No exact-policy agreement/);assert.equal(run([a,u,u]).rows.length,result.rows.length);
 for(const text of [`The report says we identify ${object} as a national priority.`,`We identify ${object} as a national priority if funding is available.`,`We have completed work on ${object}.`,`We oppose ${object}.`])assert.equal(run([a,policy('United States',3,text)]).rows.filter(x=>x.policy.id===id+'_priority').length,0,text);
 for(const extra of [{speaker_metadata:{group:'AOSIS'}},{speaker_metadata:{function:'Governor'}}])assert.equal(run([a,{...u,...extra}]).rows.length,0);
 assert.equal(run([a,u],1).rows.length,0);
}
assert.equal(run([policy('Armenia',1,'We identify accession to the Convention against Torture as a national priority.'),policy('United States',3,'We identify accession to the NPT as a national priority.')]).rows.length,0);
assert.equal(run([policy('Armenia',1,'We identify climate finance as a national priority.'),policy('United States',3,'We identify health financing as a national priority.')]).rows.length,0);
console.log('PASS expanded shared priorities: four objects, signed dates, non-scoring, unrelated objects, conditions, reported/completed acts and national attribution (synthetic only)');

for(const [id,text,object] of [
 ['climate_finance','We call upon our international partners, UN agencies, the OHCHR Pacific Regional Office, and the Pacific community to support Armenia through technical assistance, capacity building, and climate finance.','climate finance'],
 ['torture_convention','Armenia has prioritized the accession and ratification of the UN Convention Against Torture, UNCAT, as our immediate international treaty priority, while continuing internal legal reviews across other instruments.','accession to the Convention against Torture'],
 ['human_rights_institutions','While financial and human resource constraints currently impede the immediate creation of an independent national human rights institution fully compliant with the Paris Principles, Armenia is prioritizing the reestablishment of the Office of the Ombudsman.','strengthening national human rights institutions'],
 ['renewable_energy','Armenia has integrated human rights into its updated climate change policy. and third, nationally determined contribution. Setting a target of 100% renewable energy transition by 2050.','renewable energy']]){
 const r=run([policy('Armenia',1,text),policy('United States',3,`We identify ${object} as a national priority.`)]);
 assert.ok(r.rows.some(x=>x.policy.id===id+'_priority'),id+' source-reviewed grammar');
}
console.log('PASS qualified source-reviewed treaty, institution, adjacent renewable target and finance appeal patterns match broad priorities without exact agreement');

assert.equal(run([policy('Armenia',1,'We identify renewable energy as a national priority.'),policy('United States',3,'We support expanding renewable energy. We oppose expanding renewable energy.')]).rows.filter(x=>x.policy.id==='renewable_energy_priority').length,0,'conflicting dated evidence must not become a shared priority');
