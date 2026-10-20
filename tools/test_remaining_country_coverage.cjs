'use strict';
const assert=require('node:assert/strict'),P=require('../site/position-comparison');
const {record,settings}=require('./test_position_comparison.cjs');
const cases=[
 ['human_rights_defenders','human rights defenders','global'],
 ['international_crime_accountability','combating impunity for international crimes','global'],
 ['nuclear_deterrence','nuclear deterrence','global'],
 ['freedom_navigation','freedom of navigation','global'],
 ['unsc_2803','Security Council Resolution 2803 in Gaza','gaza'],
 ['human_rights_treaty_bodies','the UN human rights treaty body system','global'],
 ['human_centric_ai','human-centric AI governance','global'],
 ['resident_coordinator','the Resident Coordinator system','global'],
 ['national_development_ownership','national ownership of development cooperation','global'],
 ['universal_jurisdiction','the exercise of universal jurisdiction','global'],
 ['resilient_food_systems','resilient food systems','global'],
 ['civil_society_participation','effective participation of civil society','global'],
 ['nuclear_weapon_free_zones','nuclear-weapon-free zones','global'],
 ['peaceful_nuclear_energy','the use of nuclear energy for peaceful purposes','global'],
 ['food_supply_chains','fertilizer and food supply chains','global'],
 ['libya_un_mediation','UNSMIL in Libya','libya'],
 ['libya_territorial_integrity','the unity, sovereignty, independence and territorial integrity of Libya','libya'],
 ['lebanon_1701','Resolution 1701 in Lebanon','lebanon'],
 ['lebanon_sovereignty',"Lebanon's independence, unity, and territorial integrity",'lebanon'],
 ['iran_iaea_cooperation','Iran to cooperate fully with the IAEA','iran']
];
assert.equal(P.POLICIES.length,107);assert.equal(new Set(P.POLICIES.map(p=>p.id)).size,107);
for(const [id,obj,ctx] of cases){const policy=P.POLICIES.find(p=>p.id===id),r=record('Armenia',1,'We support '+obj+'.'),us=record('United States',1,'We oppose '+obj+'.');
 assert.equal(P.direction(r.text,policy,r),'support',id);assert.equal(P.direction(us.text,policy,us),'oppose',id);
 assert.equal(P.direction('We support a report on '+obj+'.',policy,r),null,id+' wrong object');
 assert.equal(P.direction('Armenia supported '+obj+' in 1990.',policy,r),null,id+' past');
 const p={...settings,positionPolicy:id,positionContext:ctx};const result=P.build([r,us],[r,us],p);
 assert.equal(result.countries.find(c=>c.country==='Armenia').days[0].comparison,'opposite_direction',id);
 assert.deepEqual(P.overview([r,us,r],[r,us],settings).countries,P.overview([r,us],[r,us],settings).countries,id+' repetition');
 assert.equal(P.evidence([record('Armenia',1,r.text,{speaker_metadata:{group:'NAM'}})],p).found.length,0,id+' collective');
}
const policy=id=>P.POLICIES.find(p=>p.id===id),d=(id,text,country='Armenia')=>P.direction(text,policy(id),record(country,1,text));
assert.equal(d('nuclear_deterrence','Belgium fully supports nuclear deterrence as long as adversaries possess nuclear weapons.','Belgium'),'qualified');
assert.equal(d('peaceful_nuclear_energy','We support the use of nuclear energy for peaceful purposes as long as safeguards apply.'),'qualified');
assert.equal(d('universal_jurisdiction','Universal jurisdiction must, however, be applied with circumspection.'),'qualified');
assert.equal(d('universal_jurisdiction','Universal jurisdiction must be applied with caution.'),'qualified');
assert.equal(d('libya_un_mediation','We call upon the head of UNSMIL to follow this logic.'),null);
assert.equal(d('libya_un_mediation','We welcome the agreement reached through UNSMIL.'),null);
assert.equal(d('libya_un_mediation',"We advocate for UNSMIL's efforts to facilitate equal participation of women."),null);
assert.equal(d('peaceful_nuclear_energy','We call for resetting the imbalance between the peaceful uses of nuclear energy and disarmament.'),null);
assert.equal(d('nuclear_weapon_free_zones','We support nuclear-weapon-free zones in the Middle East.'),null);
assert.equal(d('libya_un_mediation','Colombia reiterates its support to the work of UNSMIL.','Colombia'),'support');
assert.equal(d('civil_society_cooperation','We appreciate your advocacy and remain committed to cooperation with civil society.'),'support');
assert.equal(d('global_alliance_human_rights','Given the challenges, Uruguay welcomes and supports the Global Alliance for Human Rights.','Uruguay'),'support');
assert.equal(d('nuclear_disarmament','The Netherlands remains committed to a world without nuclear weapons.','Netherlands'),'support');
assert.equal(d('social_protection','Despite these challenges, Lebanon remains committed to strengthening social protection.','Lebanon'),'support');
assert.equal(d('npt','We call upon all countries, especially nuclear weapons states, to fully adhere to the principles and articles of the NPT.'),'support');
assert.equal(d('npt','We encourage all States Parties to the NPT to strengthen safeguards.'),null);
const r=record('Syria',1,"Syria renews its support for Lebanon's independence, unity, and territorial integrity.");assert.equal(P.context(r.text,r,policy('lebanon_sovereignty')).id,'lebanon');
assert.equal(P.context('We support a two-state solution in Cyprus.',r,policy('two_state')).id,'cyprus');
console.log('PASS 20 source-supported questions, explicit-object boundaries, qualifications, same-question U.S. comparisons, no repetition weight or collective inference');

assert.equal(P.context('On Gaza, Austria supports Resolution 2803.',record('Austria',1,''),policy('unsc_2803')).id,'gaza');
assert.equal(d('international_crime_accountability','We support combating impunity for traffic violations.'),null);
