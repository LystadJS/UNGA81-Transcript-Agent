const assert=require('node:assert/strict'),P=require('../site/position-comparison'),V=require('../site/position-view');
const {record}=require('./test_position_comparison.cjs');
const source=record('Armenia',1,'We identify renewable energy as a national priority.');
const entry={id:'test-doc',country:'Armenia',policy_area:'Renewable energy',reference:{record_id:source.id,text_sha256:source.text_sha256,date:source.date},document:{title:'Synthetic official document',issuer:'Synthetic federal issuer',url:'https://www.energy.gov/synthetic-test',date:'2098-12-31',date_basis:'Printed date',section:'Section 1',historical_status:'Historical context only'},country_summary:'Expressed priority',document_summary:'Different instrument',comparison:'No exact agreement established',qualification:'Does not establish matching targets',relationship:'Different measures',reviewed_on:'2099-01-02'};
const review={schema:'un.documentary-policy-review.v1',entries:[entry]};
const original=JSON.stringify(review);let r=P.documents(review,[source]);assert.equal(r.rows.length,1);assert.equal(r.rows[0].day_difference,-1);assert.equal(r.rows[0].contributes_to_scores,false);assert.equal(r.rows[0].evidence_kind,'official_document_review_not_UN_meeting_statement');assert.equal(JSON.stringify(review),original);
assert.match(V.renderDocuments(r),/separate from UN meeting statements/);assert.match(V.renderDocuments(r),/agreement scores/);assert.match(V.renderDocuments(r),/-1 days/);
for(const url of ['javascript:alert(1)','https://whitehouse.gov.evil.example/x','https://example.org/','https://user:pass@state.gov/a','http://state.gov/a','https://state.gov:444/a'])assert.equal(P.documents({...review,entries:[{...entry,document:{...entry.document,url}}]},[source]).withheld,1,url);
for(const ref of [{...entry.reference,text_sha256:'wrong'},{...entry.reference,date:'2099-01-02'}])assert.equal(P.documents({...review,entries:[{...entry,reference:ref}]},[source]).rows.length,0);
for(const date of ['2099-02-30','bad','2100-01-01'])assert.equal(P.documents({...review,entries:[{...entry,document:{...entry.document,date}}]},[source]).rows.length,0);
assert.equal(P.documents(review,[]).rows.length,0);assert.equal(P.documents(review,[{...source,speaker_metadata:{group:'AOSIS'}}]).rows.length,0);
assert.equal(P.documents({...review,entries:[entry,entry]},[source]).rows.length,1);
const escaped=P.documents({...review,entries:[{...entry,comparison:'<img src=x onerror=alert(1)>'}]},[source]);assert.ok(!V.renderDocuments(escaped).includes('<img'));
assert.equal(P.documents(null,[source]),null);assert.equal(P.documents({entries:[]},[source]).rows.length,0);
console.log('PASS documentary review: bounded fields, official links, historical signed dates, source/hash/filter/attribution binding, deduplication, escaping, no scoring or source mutation (synthetic only)');

assert.equal(P.documents({...review,entries:[{...entry,reference:{...entry.reference,text_sha256:undefined}}]},[{...source,text_sha256:undefined}]).rows.length,0);
