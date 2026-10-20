 'use strict';
const assert=require('node:assert/strict'),P=require('../site/position-comparison');
const {record,settings}=require('./test_position_comparison.cjs');
const npt=P.POLICIES.find(p=>p.id==='npt');
for(const text of ['Armenia supports the NPT.','Armenia reaffirms its strong support for the NPT.','Mr. Chair, Armenia reaffirms its commitment to the NPT.','In this regard, my country reaffirms its commitment to the NPT.']){let r=record('Armenia',1,text);assert.equal(P.direction(text,npt,r),'support',text);assert.equal(P.evidence([r],{positionPolicy:'npt',positionContext:'global'}).found[0].excerpt,text);}
for(const text of ['China supports the NPT.','Armenia supported the NPT in 1970.','Armenia said China supports the NPT.','How can Armenia support the NPT?','Armenia supports a report which mentions the NPT.'])assert.equal(P.direction(text,npt,record('Armenia',1,text)),null,text);
let r=record('India',1,"India's commitment to nuclear disarmament remains undiminished.");assert.equal(P.direction(r.text,P.POLICIES.find(p=>p.id==='nuclear_disarmament'),r),'support');
r=record('India',1,"India's commitment to nuclear disarmament was questioned.");assert.equal(P.direction(r.text,P.POLICIES.find(p=>p.id==='nuclear_disarmament'),r),null);
assert.equal(P.direction('Armenia opposes the NPT.',npt,record('Armenia',1,'')),'oppose');
assert.equal(P.direction('Armenia reaffirms its opposition to the NPT.',npt,record('Armenia',1,'')),'oppose');
assert.equal(P.direction('Armenia supports the NPT only if all parties agree.',npt,record('Armenia',1,'')),'qualified');
assert.equal(P.direction('The NPT must be respected.',npt),'support');assert.equal(P.direction('The NPT must not be respected.',npt),null);assert.equal(P.direction('The NPT was ratified decades ago.',npt),null);
assert.equal(P.direction('The UN Programme of Action on Small Arms remains contested.',P.POLICIES.find(p=>p.id==='small_arms_programme')),null);
assert.equal(P.evidence([record('Armenia',1,'Armenia supports the NPT.',{speaker_metadata:{group:'NAM'}})],{positionPolicy:'npt',positionContext:'global'}).found.length,0);
assert.equal(P.direction('Turkey supports the NPT.',npt,record('Türkiye',1,'')),'support');assert.equal(P.direction('Tanzania supports the NPT.',npt,record('Tanzania, United Republic of',1,'')),'support');
const two=P.POLICIES.find(p=>p.id==='two_state');r=record('Canada',1,'Canada remains committed to a two-state solution, with Israel and a Palestinian state living side by side.');assert.equal(P.direction(r.text,two,r),'support');assert.equal(P.context(r.text,r,two).id,'israel_palestine');
assert.equal(P.context('We support a two-state solution in Cyprus.',r,two).id,'cyprus');
assert.equal(P.context('We support a two-state solution in Gaza and the West Bank.',r,two).id,'israel_palestine');
assert.equal(P.context('We support humanitarian access in Gaza and the West Bank.',r,P.POLICIES[0]),null);
const added=[['ihl_compliance','international humanitarian law','global'],['poverty_eradication','poverty eradication','global'],['food_security','food security','global'],['cyprus_good_offices',"the Secretary-General's Good Offices Mission in Cyprus",'cyprus'],['global_alliance_human_rights','the Global Alliance for Human Rights','global'],['civil_society_cooperation','cooperation with civil society','global'],['end_golan_occupation','ending the Israeli occupation of the occupied Syrian Golan','golan']];
for(const [id,obj,ctx] of added){const policy=P.POLICIES.find(p=>p.id===id);const a=record('Armenia',1,'Armenia supports '+obj+'.'),b=record('United States',1,'We oppose '+obj+'.');assert.equal(P.direction(a.text,policy,a),'support',id);let q=P.build([a,b],[a,b],{...settings,positionPolicy:id,positionContext:ctx});assert.equal(q.countries.find(c=>c.country==='Armenia').days[0].comparison,'opposite_direction',id);assert.deepEqual(P.overview([a,b,a],[a,b],settings).countries,P.overview([a,b],[a,b],settings).countries,id+' duplicate invariance');assert.equal(P.direction('Armenia supports a report on '+obj+'.',policy,a),null,id+' wrong object');}
console.log('PASS recorded-country declarations, no third-party/historical inference, normative obligations, conditional gaps, shared two-state context and seven source-supported questions');

assert.equal(P.direction('Jamaica therefore reaffirms its firm support for the NPT.',npt,record('Jamaica',1,'')),'support');
assert.equal(P.direction('Our delegation reaffirms its unwavering support for the NPT.',npt,record('Jamaica',1,'')),'support');
assert.equal(P.direction('We promoted language that parties should implement IHL.',P.POLICIES.find(p=>p.id==='ihl_compliance'),record('Armenia',1,'')),null);

assert.equal(P.direction('Let us recall that under international law, the parties must ensure safe and unhindered humanitarian access throughout Sudan.',P.POLICIES[0],record('France',1,'')),'support');

assert.equal(P.direction('We encourage all State Parties to the NPT to adopt stronger safeguards.',npt,record('United States',1,'')),null);
assert.equal(P.direction('We urge states to ratify the NPT.',npt,record('United States',1,'')),'support');

assert.equal(P.direction('Costa Rica calls upon states that have not yet done so to accede to the TPNW.',P.POLICIES.find(p=>p.id==='tpnw'),record('Costa Rica',1,'')),'support');
assert.equal(P.direction('Our country remains fully committed to the NPT.',npt,record('Niger',1,'')),'support');
assert.equal(P.direction('Iceland is a long-standing supporter of UNRWA.',P.POLICIES.find(p=>p.id==='unrwa'),record('Iceland',1,'')),'support');
assert.equal(P.direction('Suriname, therefore, continues to call for respect for international humanitarian law.',P.POLICIES.find(p=>p.id==='ihl_compliance'),record('Suriname',1,'')),'support');
assert.equal(P.direction('We must strengthen local delivery of the SDGs.',P.POLICIES.find(p=>p.id==='sdgs'),record('Armenia',1,'')),'support');
assert.equal(P.direction('Negotiations on FMCT should begin without further delay.',P.POLICIES.find(p=>p.id==='fissile_material_treaty'),record('Norway',1,'')),'support');
assert.equal(P.direction('We remain steadfast in supporting a two-state solution in Palestine.',two,record('Viet Nam',1,'')),'support');

const nuclear=P.POLICIES.find(p=>p.id==='nuclear_disarmament');
assert.equal(P.direction('Brazil supports advancing nuclear disarmament verification.',nuclear,record('Brazil',1,'')),null);
assert.equal(P.direction('Jamaica reaffirms its support for the TPNW as a significant contribution to nuclear disarmament.',nuclear,record('Jamaica',1,'')),null);
assert.equal(P.direction('We encourage greater transparency and accountability in nuclear disarmament.',nuclear),null);
assert.equal(P.direction('Turkey supports a consensus-based outcome on negotiations for a treaty on the protection of persons in the event of disasters.',P.POLICIES.find(p=>p.id==='disaster_protection_treaty'),record('Türkiye',1,'')),'qualified');
