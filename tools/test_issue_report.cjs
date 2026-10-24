const assert=require('node:assert/strict'),R=require('../site/issue-report'),V=require('../site/issue-archive-view'),M=require('../site/issue-models');
const source=(id,date,extra={})=>({id,revision:'r1',family:'un_statement',body:'SC',published_date:date,countries:['Kenya','Ghana','United States'],url:'https://example.org/'+id,...extra});
const obs=(id,country,date,stance,extra={})=>({id,country,date,stance,source_id:'s'+date,source_revision:'r1',policy:'humanitarian_access',context:'sudan',attribution:'national',review_state:'assistant_provisional',...extra});
const inputs={topic:'humanitarian access',start:'2026-10-01',end:'2026-10-23',as_of:'2026-10-23',bodies:['SC'],exclusions:[]};
const snapshot={manifest:{snapshot_id:'synthetic_report_test'},sources:[source('s2018-01-01','2018-01-01'),source('s2026-10-01','2026-10-01'),source('s2026-10-02','2026-10-02'),source('doc','2026-10-01',{family:'executive_policy',countries:['Malta']}),source('s2015-01-01','2015-01-01')],observations:[obs('old','Kenya','2018-01-01','support'),obs('oldUS','United States','2018-01-01','oppose'),obs('new','Kenya','2026-10-01','qualified',{qualifications:['only with consent']}),obs('newUS','United States','2026-10-01','support'),obs('gap','Kenya','2026-10-02','oppose',{context:'gaza'}),obs('docObs','Malta','2026-10-01','support',{source_id:'doc'}),obs('tooOld','Kenya','2015-01-01','support')],votes:[]};
const frozen=JSON.stringify({snapshot,inputs}),r=R.build(snapshot,inputs),q=r.questions.find(q=>q.context==='sudan'),kenya=q.countries.find(c=>c.country==='Kenya');
assert.equal(r.window.start,'2016-10-24');assert.equal(r.window.end,'2026-10-23');assert.equal(kenya.current_state,'qualified');assert.equal(kenya.comparisons.find(o=>o.date==='2018-01-01').relationship,'opposite_direction');assert.equal(kenya.comparisons.find(o=>o.date==='2026-10-01').relationship,'qualified_or_mixed');
assert.ok(r.roster.includes('Ghana'),'recorded countries without explicit positions remain visible');assert.ok(!r.roster.includes('Malta'),'official documents cannot establish UN country population');assert.equal(q.population,2);assert.equal(q.counts.missing,1);assert.equal(r.questions.find(q=>q.context==='gaza').countries.find(c=>c.country==='Kenya').comparisons[0].relationship,'missing_us');assert.ok(r.withheld_ids.includes('docObs'));
assert.equal(JSON.stringify({snapshot,inputs}),frozen,'report does not mutate source snapshot or frozen inputs');
const p=M.observed(M.panel(snapshot.observations.filter(o=>o.source_id!=='doc'),{start:r.window.start,end:r.window.end,countries:r.roster}));assert.equal(p.countries.find(c=>c.country_id==='Kenya').comparisons.find(c=>c.date==='2018-01-01').relationship,kenya.comparisons.find(o=>o.date==='2018-01-01').relationship);
const conflict=structuredClone(snapshot);conflict.sources.push({...snapshot.sources[0],published_date:'2019-01-01'});assert.ok(!R.build(conflict,inputs).questions.flatMap(q=>q.countries.flatMap(c=>c.observations)).some(o=>o.date==='2018-01-01'),'conflicting source identities withheld');
const obConflict=structuredClone(snapshot);obConflict.observations.push({...snapshot.observations[0],country:'Ghana'});assert.ok(R.build(obConflict,inputs).withheld_ids.includes('old'),'conflicting observation identity withheld');
const mismatched=structuredClone(snapshot);mismatched.observations.push(obs('mismatch','Ghana','2026-10-02','support',{source_id:'s2026-10-01'}));assert.ok(R.build(mismatched,inputs).withheld_ids.includes('mismatch'),'source and expression dates agree');
const malicious=structuredClone(r),hostile='<img src=x onerror=alert(1)>';malicious.sources.forEach(s=>s.url='javascript:alert(1)');malicious.roster=malicious.roster.map(c=>c==='Kenya'?hostile:c);malicious.questions.forEach(q=>q.countries.forEach(c=>{if(c.country==='Kenya')c.country=hostile;}));const html=V.render(malicious);assert.ok(!html.includes('href="javascript:'));assert.ok(!html.includes('<img'));assert.ok(html.includes('&lt;img'));assert.ok(html.includes('Unknown'));assert.ok(!html.includes('<script'));
assert.throws(()=>R.build(snapshot,{...inputs,topic:'international football'}));assert.throws(()=>R.build(snapshot,{...inputs,end:'2027-01-01'}));
console.log('PASS country report unknown denominators, source-family separation, dated stance changes, independent historical window, conflicts, exact US comparison, immutable inputs and escaped source-linked view (synthetic only)');


// Independent source-free selective-history contract. All sources and countries below are fictional test inputs.
(function selectiveHistoryAcceptance(){
 const O=require('../site/issue-ontology'),sources=[],observations=[];
 const add=(id,date,body,countries,family='un_statement')=>{sources.push(source(id,date,{body,countries,family}));};
 const addObservation=(id,sourceId,country,date,policy='humanitarian_access',extra={})=>observations.push(obs(id,country,date,'support',{source_id:sourceId,policy,...extra}));
 add('before','2016-10-23','SC',['OutsideOld']);add('start','2016-10-24','SC',['Kenya','United States']);
 add('current','2026-10-01','SC',['Kenya','United States']);add('other-policy','2026-10-01','SC',['Ghana']);
 add('roster-only','2026-10-02','SC',['France']);add('last-day','2026-10-23','SC',['India','United States']);
 add('after','2026-10-24','SC',['OutsideFuture']);add('committee','2026-10-01','GA_C3',['Nigeria']);
 add('plenary','2026-10-01','GA',['Palau']);add('official-doc','2026-10-01','SC',['Malta'],'executive_policy');
 add('recorded-vote','2026-10-01','SC',['Liberia'],'un_recorded_vote');
 for(const [id,date] of [['start','2016-10-24'],['current','2026-10-01'],['last-day','2026-10-23']]){
  addObservation(id+'-national',id,id==='last-day'?'India':'Kenya',date);addObservation(id+'-US',id,'United States',date);
 }
 addObservation('other-policy-expression','other-policy','Ghana','2026-10-01','civilian_protection');
 addObservation('committee-expression','committee','Nigeria','2026-10-01');addObservation('plenary-expression','plenary','Palau','2026-10-01');
 addObservation('doc-expression','official-doc','Malta','2026-10-01');
 const full={manifest:{snapshot_id:'selective-contract-fictional'},sources,observations,votes:[{country:'Liberia',source_id:'recorded-vote',source_revision:'r1',date:'2026-10-01',policy:'humanitarian_access',context:'sudan',vote:'yes'}]};
 const compactRoster=()=>{const cells=new Map();for(const s of sources){const key=[s.published_date,s.body,s.family].join('|');if(!cells.has(key))cells.set(key,{date:s.published_date,body:s.body,family:s.family,countries:new Set(),ids:new Set()});const c=cells.get(key);for(const country of s.countries)c.countries.add(country);c.ids.add(s.id);}return [...cells.values()].map(c=>({date:c.date,body:c.body,family:c.family,countries:[...c.countries].sort(),source_count:c.ids.size}));};
 const selectedObservations=observations.filter(o=>o.policy==='humanitarian_access'&&sources.find(s=>s.id===o.source_id).body==='SC');
 const selectedSourceIds=new Set(selectedObservations.map(o=>o.source_id));
 const selected={manifest:full.manifest,observations:selectedObservations,sources:sources.filter(s=>selectedSourceIds.has(s.id)),votes:[],roster:compactRoster().filter(r=>r.body==='SC')};
 const baseline=R.build(full,inputs),selective=R.build(selected,inputs);
 const comparison=r=>({roster:r.roster,questions:r.questions,coverage:r.coverage});
 assert.deepEqual(comparison(selective),comparison(baseline),'selected policy shards and full source snapshot must produce the same country denominators, positions and historical coverage');
 assert.ok(selective.roster.includes('Ghana'),'country with only another-policy evidence remains Unknown for selected policy');
 assert.ok(selective.roster.includes('France'),'country with recorded source affiliation and no extracted position remains Unknown');
 assert.ok(!selective.roster.includes('OutsideOld')&&!selective.roster.includes('OutsideFuture'),'compact roster respects exact partial-year endpoint dates');
 assert.ok(!selective.roster.includes('Malta')&&!selective.roster.includes('Liberia'),'official documents and votes never create statement-opinion population');
 assert.equal(selective.coverage.find(y=>y.year==='2016').sources,1);assert.equal(selective.coverage.find(y=>y.year==='2026').sources,4);
 const duplicated=structuredClone(full);duplicated.sources.push({...sources.find(s=>s.id==='current')});duplicated.observations.push({...observations.find(o=>o.id==='current-national'),id:'repeated-expression-id'});
 assert.deepEqual(comparison(R.build(duplicated,inputs)),comparison(baseline),'duplicate source identity and repeated expressions do not change opinion counts or source coverage');
 const duplicatedRoster=structuredClone(selected);duplicatedRoster.roster.push(structuredClone(selected.roster.find(r=>r.date==='2026-10-01'&&r.family==='un_statement')));
 assert.deepEqual(comparison(R.build(duplicatedRoster,inputs)),comparison(selective),'compact roster repeated in policy shards is counted exactly once');
 const ga=R.build(full,{...inputs,bodies:['GA']});assert.ok(ga.roster.includes('Nigeria')&&ga.roster.includes('Palau'),'GA selection includes committees and plenary');assert.ok(!ga.roster.includes('Kenya'),'GA hierarchy does not include Security Council');
 const committee=R.build(full,{...inputs,bodies:['GA_C3']});assert.deepEqual(committee.roster,['Nigeria'],'specific committee excludes plenary and other bodies');
 const methodSnapshot=()=>structuredClone(full),relationship=r=>r.questions.find(q=>q.context==='sudan').countries.find(c=>c.country==='Kenya').comparisons.find(c=>c.date==='2026-10-01').relationship;
 const ownKnown=methodSnapshot();Object.assign(ownKnown.observations.find(o=>o.id==='current-national'),{ontology_version:O.version,extractor_version:'rules-v1'});
 assert.equal(relationship(R.build(ownKnown,inputs)),'method_version_gap','known and legacy extraction provenance cannot silently form an exact comparison');
 const sameKnown=structuredClone(ownKnown);Object.assign(sameKnown.observations.find(o=>o.id==='current-US'),{ontology_version:O.version,extractor_version:'rules-v1'});
 assert.equal(relationship(R.build(sameKnown,inputs)),'same_direction','matching ontology and extractor versions preserve exact observed comparison');
 const differingExtractor=structuredClone(sameKnown);differingExtractor.observations.find(o=>o.id==='current-US').extractor_version='rules-v2';
 assert.equal(relationship(R.build(differingExtractor,inputs)),'method_version_gap','incompatible extractors produce an explicit comparison gap');
 assert.match(V.render(R.build(differingExtractor,inputs)),/1 method-version gaps/,'method incompatibility is visible in the country trajectory rather than hidden missingness');
 assert.match(V.render(baseline),/observations lack complete method versions/,'legacy provenance warning remains visible');
 const alternateMethod=structuredClone(sameKnown);alternateMethod.observations.push({...alternateMethod.observations.find(o=>o.id==='current-national'),id:'alternate-extractor-current',extractor_version:'rules-v2'});
 assert.equal(relationship(R.build(alternateMethod,inputs)),'method_version_gap','different extraction versions on one source identity cannot be deduplicated into a false compatible comparison');
 const incompatible=structuredClone(sameKnown);incompatible.observations.find(o=>o.id==='current-national').ontology_version='different-policy-object-v9';
 const withheld=R.build(incompatible,inputs);assert.ok(withheld.withheld_ids.includes('current-national'),'unsupported ontology is withheld from current position counts');
 assert.equal(withheld.questions.find(q=>q.context==='sudan').countries.find(c=>c.country==='Kenya').current_state,'missing');
 console.log('PASS selective/full source-free parity: policy-independent country denominator, roster coverage, duplicate invariance, partial-year boundaries, GA hierarchy, source-kind separation and method-version gaps');
})();

const wrongAffiliation=structuredClone(snapshot);wrongAffiliation.sources.find(s=>s.id==='s2026-10-01').countries=['United States'];assert.ok(R.build(wrongAffiliation,inputs).withheld_ids.includes('new'),'national attribution must agree with recorded nonempty source affiliations');
const conflictingRoster=structuredClone(snapshot);conflictingRoster.roster=[{date:'2026-10-01',body:'SC',family:'un_statement',countries:['Kenya'],source_count:1},{date:'2026-10-01',body:'SC',family:'un_statement',countries:['Ghana'],source_count:2}];assert.throws(()=>R.build(conflictingRoster,inputs),/Conflicting historical affiliation coverage/);
assert.ok(R.build(conflict,inputs).withheld_ids.includes('old'),'source conflict withholding remains visible');
