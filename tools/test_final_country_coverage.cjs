'use strict';
const assert=require('node:assert/strict'),P=require('../site/position-comparison'),V=require('../site/position-view');
const {record,settings}=require('./test_position_comparison.cjs');
const policy=id=>P.POLICIES.find(p=>p.id===id);
const examples=[
 ['ohchr_work','We support the work of the High Commissioner for Human Rights.','support'],
 ['disaster_risk_reduction','We support disaster risk reduction.','support'],
 ['disaster_assistance_consent','Assistance must be provided with the consent of the affected states.','support'],
 ['predictable_development_finance','We support predictable development financing.','support'],
 ['state_sovereignty','We call for respect for state sovereignty.','support'],
 ['peaceful_dispute_settlement','We support the peaceful settlement of international disputes.','support'],
 ['iran_no_nuclear_weapon','Iran must never acquire a nuclear weapon.','support'],
 ['palestinian_statehood','We support Palestinian statehood.','support'],
 ['poverty_reduction','We advocate poverty reduction.','support'],
 ['development_cooperation_framework','We support the UN Sustainable Development Cooperation Framework.','support'],
 ['opcw_mandate','We support the OPCW.','support'],
 ['russian_nuclear_threats',"We oppose Russia's threats of nuclear weapons use.",'oppose'],
 ['outer_space_militarization','We oppose militarization of outer space.','oppose'],
 ['abandon_unilateral_measures','We call for states to abandon illegitimate unilateral measures.','support'],
 ['treaty_implementation_assistance','States parties to these mechanisms need training and technical assistance, financing to effectively implement these instruments.','support'],
 ['halt_settlement_expansion','We urge an immediate end to settlement expansion.','support']
];
assert.equal(P.POLICIES.length,125);assert.equal(new Set(P.POLICIES.map(p=>p.id)).size,125);
for(const [id,text,expected] of examples){const r=record('Armenia',1,text+' Human rights treaty bodies are the context.');assert.equal(P.direction(text,policy(id),r),expected,id);assert.equal(P.evidence([record('Armenia',1,r.text,{speaker_metadata:{group:'NAM'}})],{positionPolicy:id,positionContext:'*'}).found.length,0,id+' collective');assert.equal(P.direction('The report said: '+text,policy(id),r),null,id+' reported');assert.equal(P.direction('Is it true that '+text+'?',policy(id),r),null,id+' question');}
for(const text of ['We support humanitarian access.','We oppose humanitarian access.']){
 const r=record('Armenia',1,text,{meeting:'International policy exchange'}),us=record('United States',1,'We support humanitarian access.',{meeting:'International policy exchange'});
 const q=P.build([r,us],[r,us],{...settings,positionPolicy:'humanitarian_access',positionContext:'unspecified'});
 assert.equal(q.countries.find(c=>c.country==='Armenia').days[0].comparison,'context_unestablished');assert.equal(q.countries[0].days[0].value,null);
 const o=P.overview([r,us],[r,us],settings),c=o.countries.find(c=>c.country==='Armenia');assert.ok(c.positions.some(p=>p.context.id==='unspecified'));assert.equal(c.comparable_question_dates,0);assert.equal(c.agreement_percent,null);assert.deepEqual(P.overview([r,r,us],[r,us],settings).countries,o.countries);assert.match(V.renderOverview(o),/Gap: context not established/);assert.ok(P.evidence([r],{positionPolicy:'humanitarian_access',positionContext:'unspecified'}).found[0].excerpt===text);
}
const r=record('Armenia',1,'We support humanitarian access in Sudan and Gaza.');assert.equal(P.context(r.text,r,policy('humanitarian_access')),null);assert.equal(P.build([r],[r],{...settings,positionPolicy:'humanitarian_access',positionContext:'unspecified'}).countries[0].comparable_days,0);
const own=(id,text,country='Armenia')=>P.direction(text,policy(id),record(country,1,text));
assert.equal(own('ohchr_work','Armenia thanks High Commissioner Turk for his update and reiterates its support for his mandate and the independence of his office.'),'support');
assert.equal(own('ohchr_work','Armenia welcomes the High Commissioner and congratulates him on renewal of his mandate and reiterates our commitment to continue supporting your work. Human rights treaty bodies are discussed.'),'support');
assert.equal(own('ohchr_work','We welcome High Commissioner Turk.'),null);
assert.equal(own('ohchr_work','We support the work of the High Commissioner for Refugees.'),null);
assert.equal(own('ohchr_work','China thanks High Commissioner Turk for his update and reiterates its support for his mandate and the independence of his office.'),null);
assert.equal(own('disaster_risk_reduction',"We support draft article 9, which enshrines States' obligations to reduce disaster risks."),'support');
assert.equal(own('disaster_assistance_consent','Assistance must not be provided with the consent of the affected states.'),null);
assert.equal(own('predictable_development_finance','Armenia reiterates the call for financing that is predictable, affordable, and easier to access.'),'support');
assert.equal(own('npt','Armenia supported the NPT in 1970.'),null);
assert.equal(own('food_security','We are committed to promoting practical policies and working towards food security.'),'support');
assert.equal(own('food_security','We are committed to a report that discusses working towards food security.'),null);
assert.equal(own('pelindaba','While reiterating its commitment to the Pelindaba Treaty, my country supports dialogue.'),'support');
assert.equal(own('outer_space_militarization','We will consistently oppose all forms of destabilizing weapons, as well as militarization of outer space.'),'oppose');
assert.equal(own('disaster_protection_treaty',"It's precisely in this context that Armenia believes that it is of the utmost importance to move towards the conclusion of an international convention on the protection of persons in the event of disasters."),'support');
console.log('PASS 16 added questions, bounded own declarations, same-sentence institutional references, no courtesy/third-party inference, and visible unspecified positions with permanently withheld comparison');

assert.equal(own('nuclear_disarmament',"Armenia's commitment to nuclear disarmament remains firm, he said."),null);
assert.equal(own('disaster_protection_treaty',"China believes that it is of the utmost importance to move towards the conclusion of an international convention on the protection of persons in the event of disasters."),null);

assert.deepEqual(P.contextsFor(policy('treaty_implementation_assistance')),['unspecified']);
const instrumentText='States parties to these mechanisms need training and technical assistance, financing to effectively implement these instruments.';
const instrument=record('Armenia',1,instrumentText+' Human rights treaty bodies in Sudan are discussed.');
assert.equal(P.context(instrumentText,instrument,policy('treaty_implementation_assistance')),null);
assert.equal(P.build([instrument],[record('United States',1,instrument.text)],{...settings,positionPolicy:'treaty_implementation_assistance',positionContext:'unspecified'}).countries[0].comparable_days,0);
