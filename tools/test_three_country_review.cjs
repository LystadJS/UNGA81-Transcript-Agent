'use strict';
const assert=require('node:assert/strict'),P=require('../site/position-comparison'),V=require('../site/position-view');
const {record,settings}=require('./test_position_comparison.cjs');
const role='I would like to underscore the crucial role of the Office of the High Commissioner on Human Rights, particularly through its technical assistance, capacity building, and comprehensive reporting.';
const framing='We need to move beyond the narrative on human rights that is too often negative, one that risks coding human rights as a partisan or luxury agenda.';
const rolePolicy=P.POLICIES.find(p=>p.id==='ohchr_technical_functions'),framingPolicy=P.POLICIES.find(p=>p.id==='human_rights_framing');
assert.equal(P.POLICIES.length,125);assert.equal(new Set(P.POLICIES.map(p=>p.id)).size,125);
const a=record('Armenia',1,'In this difficult period, '+role),b=record('United States',1,role),c=record('France',1,framing),palau=record('Palau',1,'I deliver this statement on behalf of the Alliance of Small Island States. '+framing,{speaker_metadata:{group:'AOSIS'}});
assert.equal(P.direction(role,rolePolicy,a),'qualified');assert.equal(P.direction(framing,framingPolicy,c),'support');
for(const policy of [rolePolicy,framingPolicy]){
 assert.equal(P.direction('The report said: '+(policy===rolePolicy?role:framing),policy,a),null);
 assert.equal(P.direction('How should we discuss '+(policy===rolePolicy?'OHCHR technical assistance, capacity building, and reporting':'negative framing of human rights as a partisan agenda')+'?',policy,a),null);
 assert.equal(P.evidence([palau],{positionPolicy:policy.id,positionContext:'global'}).found.length,0);
}
assert.equal(P.direction('We thank the Office of the High Commissioner for the report.',rolePolicy,a),null);
assert.equal(P.direction('We heard a call about negative framing of human rights as a partisan agenda.',framingPolicy,a),null);
const overview=P.overview([a,b,c,palau],[a,b,c,palau],settings),own=overview.countries.find(c=>c.country==='Armenia'),group=overview.countries.find(c=>c.country==='Palau');
assert.equal(own.positions[0].days[0].country_state,'qualified');assert.equal(own.comparable_question_dates,0);assert.equal(own.positions[0].days[0].value,null);assert.match(own.positions[0].days[0].country_evidence[0].qualification,/no explicit funding or implementation commitment/);assert.equal(own.positions[0].days[0].country_evidence[0].excerpt,a.text);
assert.deepEqual(group.positions,[]);assert.equal(group.coverage_reason,'national_attribution_withheld');assert.equal(group.withheld_sources[0].explicit_group,'Alliance of Small Island States (AOSIS)');assert.equal(group.withheld_sources[0].record_id,palau.id);
const html=V.renderOverview(overview);assert.match(html,/no explicit funding or implementation commitment/);assert.match(html,/Expressly delivered for Alliance of Small Island States/);assert.match(html,/No separate national position/);
assert.deepEqual(P.overview([a,b,c,palau,a],[a,b,c,palau],settings).countries,overview.countries);
console.log('PASS qualified institutional-role assessment never scores; explicit framing request, no inference from questions/courtesy, and source-linked AOSIS attribution without national assignment');

assert.equal(P.direction('We oppose moving beyond negative framing of human rights as a partisan agenda.',framingPolicy,a),'oppose');
assert.equal(P.direction('We oppose negative framing of human rights as a partisan agenda.',framingPolicy,a),null);
assert.equal(P.direction('We support a negative narrative on human rights as a partisan agenda.',framingPolicy,a),null);
