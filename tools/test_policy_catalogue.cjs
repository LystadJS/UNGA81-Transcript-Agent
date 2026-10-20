 'use strict';
const assert=require('node:assert/strict');
const P=require('../site/position-comparison'),V=require('../site/position-view');
const {record,settings}=require('./test_position_comparison.cjs');
const examples={npt:'the Nuclear Non-Proliferation Treaty',iaea_additional_protocol:'the IAEA Additional Protocol',bwc:'the Biological Weapons Convention',cwc:'the Chemical Weapons Convention',arms_trade_treaty:'the Arms Trade Treaty',small_arms_programme:'the Programme of Action on Small Arms and Light Weapons',nuclear_disarmament:'nuclear disarmament',pelindaba:'the Treaty of Pelindaba',fissile_material_treaty:'a fissile material cut-off treaty',paris_agreement:'the Paris Agreement',climate_finance:'climate finance',loss_damage_fund:'the Fund for Responding to Loss and Damage',sdgs:'the 2030 Agenda for Sustainable Development',disaster_protection_treaty:'a legally binding instrument on the protection of persons in the event of disasters',icc:'the International Criminal Court',death_penalty_abolition:'the abolition of the death penalty',death_penalty_moratorium:'a global moratorium on the death penalty',security_council_reform:'reform of the Security Council',security_council_expansion:'expansion of the Security Council',palestine_recognition:'recognition of the State of Palestine',unrwa:'UNRWA',korean_denuclearization:'the denuclearization of the Korean Peninsula',cuba_terrorism_removal:'the removal of Cuba from the United States list of state sponsors of terrorism'};
assert.equal(P.POLICIES.length,80);assert.equal(Object.keys(examples).length,23);
for(const [id,object] of Object.entries(examples)){
 const policy=P.POLICIES.find(p=>p.id===id);assert.ok(policy,id);
 const positive=`We support ${object}.`,negative=`We oppose ${object}.`;
 assert.equal(P.direction(positive,policy),'support',id+' support');assert.equal(P.direction(negative,policy),'oppose',id+' oppose');
 assert.equal(P.direction(`We support ${object} only if all parties agree.`,policy),'qualified',id+' conditional');
 for(const line of [`The delegate said we support ${object}.`,`We support a report which mentions ${object}.`,`We support cuts to ${object}.`,`We support criticism of ${object}.`,`We support restrictions on ${object}.`])assert.equal(P.direction(line,policy),null,id+' '+line);
 const own=record('Kenya',1,positive),us=record('United States',1,negative);
 const r=P.build([own,us],[own,us],{...settings,positionPolicy:id,positionContext:policy.global?'global':'cuba'});
 assert.equal(r.trajectory[0].comparison,'opposite_direction',id+' matched question');assert.equal(r.trajectory[1].value,null,id+' no imputation');
 const o=P.overview([own,us],[own,us],settings);assert.ok(o.questions.some(q=>q.policy.id===id),id+' automatic discovery');
 assert.equal(o.countries.find(c=>c.country==='Kenya').opposite_direction,1,id+' one question/date');assert.ok(V.renderOverview(o).includes(policy.label),id+' report');
}
const npt=P.POLICIES.find(p=>p.id==='npt');assert.equal(P.direction('We support the Additional Protocol to the Non-Proliferation Treaty.',npt),null);
assert.equal(P.direction('We call for a successful next NPT Review Conference that upholds the treaty integrity.',npt),null);
const rem=P.POLICIES.find(p=>p.id==='cuba_terrorism_removal');assert.equal(P.direction('We support removal of Cuba from a list of state sponsors of terrorism.',rem),null);
assert.equal(P.direction('We call for removal of Cuba from a list of state sponsors of terrorism and ask you to help us.',rem),null);
assert.equal(P.direction('We support the UN Programme of Action for Least Developed Countries.',P.POLICIES.find(p=>p.id==='small_arms_programme')),null);
assert.equal(P.direction('We support removing Iran from the United States list of state sponsors of terrorism.',rem),null);
assert.equal(P.direction('The United States list of state sponsors of terrorism includes Cuba.',rem),null);
const own=record('Kenya',1,'We support the Arms Trade Treaty.'),other=record('United States',1,'We oppose the Biological Weapons Convention.');
const o=P.overview([own,other],[own,other],settings);assert.equal(o.countries.find(c=>c.country==='Kenya').comparable_question_dates,0);
const group={...own,speaker_metadata:{group:'NAM'}};assert.equal(P.overview([group,other],[group,other],settings).countries.find(c=>c.country==='Kenya').positions.length,0);
const cases=Object.entries(examples).flatMap(([id,object])=>[record('Kenya',1,`We support ${object}.`),record('United States',1,`We oppose ${object}.`)]);
const all=P.overview(cases,cases,settings),repeated=P.overview([...cases,...cases], [...cases,...cases],settings);assert.deepEqual(all.countries,repeated.countries);
console.log('PASS 23 added policies: support, opposition, conditions, quotation/object abstention, automatic discovery, same-question comparison, country attribution and repetition-invariant weighting (synthetic only)');

const wrongEmbargo=record('Kenya',1,'We call for lifting the blockade in Gaza. Cuba was also mentioned.');assert.doesNotThrow(()=>P.overview([wrongEmbargo],[wrongEmbargo],settings));assert.equal(P.overview([wrongEmbargo],[wrongEmbargo],settings).questions.some(q=>q.policy.id==='cuba_embargo'),false);
