const assert=require('node:assert/strict'),S=require('../site/meeting-scopes'),A=require('../site/analysis-core');
for(const slug of ['sc/10243','sc/10243/2','sc/10243/3'])assert.equal(S.formalMeetingKey({slug}),'sc/10243');
assert.equal(S.formalMeetingKey({slug:'ga/c1/81/11/2'}),'ga/c1/81/11');
assert.equal(S.formalMeetingKey({slug:'ga/81/12/2'}),'ga/81/12');
for(const title of ['Security Council Arria Formula','Security Council informal meeting','General Assembly special event'])assert.equal(S.formalMeetingKey({slug:'sc/10243',title}),null);
assert.equal(S.formalMeetingKey({slug:'asset/a/b',title:'Security Council'}),null);
assert.equal(S.formalMeetingKey({slug:'sc/10243',pageUrl:'/en/sc/10244'}),null);
assert.ok(S.covers('ga_sc','ga_sc_formal'));assert.ok(!S.covers('ga_sc_formal','ga_sc'));
console.log('PASS formal identity, resumed parts, informal and unknown exclusions, conflicts and scope coverage');
