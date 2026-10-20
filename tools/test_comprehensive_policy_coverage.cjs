 'use strict';
const assert=require('node:assert/strict'),P=require('../site/position-comparison'),V=require('../site/position-view');
const {record,settings}=require('./test_position_comparison.cjs');
const cases=require('./comprehensive_policy_cases.json');
assert.equal(cases.length,50);assert.equal(P.POLICIES.length,80);assert.equal(new Set(P.POLICIES.map(p=>p.domain)).size,8);assert.equal(new Set(P.POLICIES.map(p=>p.id)).size,80);
for(const c of cases){
 const p=P.POLICIES.find(p=>p.id===c.id),context=c.context==='global'?'':` in ${P.CONTEXTS.find(x=>x.id===c.context).label}`;
 const yes=`We support ${c.object}${context}.`,no=`We oppose ${c.object}${context}.`;
 assert.equal(P.direction(yes,p),'support',c.id+' support');assert.equal(P.direction(`We reaffirm our commitment to ${c.object}${context}.`,p),'support',c.id+' explicit commitment');assert.equal(P.direction(`We reaffirm our opposition to ${c.object}${context}.`,p),'oppose',c.id+' explicit opposition');assert.equal(P.direction(no,p),'oppose',c.id+' oppose');
 assert.equal(P.direction(`We support ${c.object}${context} only if all parties agree.`,p),'qualified',c.id+' conditional');
 for(const text of [`The delegate said we support ${c.object}${context}.`,`We support a report which mentions ${c.object}${context}.`,`We support criticism of ${c.object}${context}.`,`We support noncompliance with ${c.object}${context}.`,`We support action against ${c.object}${context}.`,`We support restrictions on ${c.object}${context}.`])assert.equal(P.direction(text,p),null,c.id+' '+text);
 const own=record('Kenya',1,yes),us=record('United States',1,no);
 const b=P.build([own,us],[own,us],{...settings,positionPolicy:p.id,positionContext:c.context});assert.equal(b.trajectory[0].comparison,'opposite_direction',c.id+' baseline');assert.equal(b.trajectory[1].value,null,c.id+' gap');
 const o=P.overview([own,us],[own,us],settings);assert.ok(o.questions.some(q=>q.policy.id===p.id),c.id+' automatic');assert.ok(V.renderOverview(o).includes(p.label),c.id+' report');
 assert.deepEqual(o.countries,P.overview([own,us,own],[own,us,us],settings).countries,c.id+' no repetition weight');
 const group={...own,speaker_metadata:{group:'NAM'}};assert.equal(P.build([group,us],[group,us],{...settings,positionPolicy:p.id,positionContext:c.context}).trajectory[0].value,null,c.id+' group abstention');
}
const get=id=>P.POLICIES.find(p=>p.id===id);
assert.equal(P.direction('We support ending the extraterritorial application of the embargo on Cuba.',get('cuba_embargo')),null);
assert.equal(P.direction('We support maintaining unilateral coercive measures in Sudan.',get('end_unilateral_measures')),null);
assert.equal(P.direction('We support imposing sanctions in Sudan.',get('end_unilateral_measures')),null);
assert.equal(P.direction('We support lifting unilateral coercive measures in Sudan.',get('end_unilateral_measures')),'support');
assert.equal(P.direction('We support expanding health coverage.',get('universal_health')),null);
assert.equal(P.direction('We support a moratorium on nuclear testing.',get('no_first_use')),null);
assert.equal(P.direction('We support the International Court of Justice.',get('icc')),null);
assert.equal(P.direction('We support the Global Compact on Refugees.',get('migration_compact')),null);
assert.equal(P.direction('We support sovereign debt restructuring.',get('debt_cancellation')),null);
assert.equal(P.direction('We support permanent seats for Africa on the Security Council.',get('security_council_reform')),null);
assert.throws(()=>P.options({...settings,positionPolicy:'libya_elections',positionContext:'sudan'}),/valid context/);
const cross=record('Kenya',1,'We support national elections in Libya. Sudan was also discussed.');assert.equal(P.overview([cross],[cross],settings).questions.find(q=>q.policy.id==='libya_elections').context.id,'libya');
const text=record('Kenya',1,'We support economic growth. We oppose the 0.7 per cent ODA target.');assert.equal(P.evidence([text],{positionPolicy:'oda_target',positionContext:'global'}).found[0].stance,'oppose');
assert.equal(P.direction('We support removal of Cuba from the U.S. list of state sponsors of terrorism.',get('cuba_terrorism_removal')),'support');
console.log('PASS 50 comprehensive additions across eight areas: direction, qualification, wrong object, automatic report, gaps, context, group abstention and duplicate invariance; no general accuracy claim');

assert.equal(P.direction('We support the working group created under the UN80 Initiative.',get('un80')),null);
