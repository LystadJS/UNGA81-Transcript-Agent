import test from 'node:test';
import assert from 'node:assert/strict';
import {generateKeyPairSync,sign} from 'node:crypto';
import {fixture,NOW,H,J,K,C} from './fixtures.mjs';
import {VERSION,GATES,canonical,digest,parseStrict,validateShape,validateQuery,validateCapability,validateProduct,bindingFor,receiptSetDigest,assess,createSession} from './contracts.mjs';
const keypair=generateKeyPairSync('ed25519');
const key={key_id:'ephemeral_test_only',spki_base64:keypair.publicKey.export({type:'spki',format:'der'}).toString('base64'),gates:[...GATES],destinations:['local_view','local_export','public_site','email']};
const kinds={engineering:'coordinator_acceptance',source:'source_validation',comparability:'comparability_review',review:'owner_review',inference:'statistical_acceptance',display:'display_validation',export:'output_authorization'};
async function receipt(f,gate,verdict='pass',section_id='all',destination='local_view',extra={}) {
  const payload={schema:'un.product-decision.v1',contract_version:VERSION,id:`decision_${gate}_${section_id}_${destination}`,key_id:key.key_id,gate,verdict,section_id,destination,binding:await bindingFor(f.product),issued_at:'2000-02-01T11:00:00Z',expires_at:'2000-02-02T12:00:00Z',evidence_kind:kinds[gate],evidence_sha256:H,...extra};
  return {payload,signature:sign(null,Buffer.from(canonical(payload)),keypair.privateKey).toString('base64')};
}
async function signed(f,gates=['engineering','source','review','export'],destination='local_view') {
  const receipts=await Promise.all(gates.map(g=>receipt(f,g,'pass','all',destination)));
  return {...f,receipts,trustedReceiptSetSha256:await receiptSetDigest(receipts),trustedKeys:[key],destination,now:NOW};
}
async function result(f,options={}) {return assess({...await signed(f),...options});}
function empty(f,state='empty',reason='no_matches') {f.product.evidence=[];f.product.findings=[];Object.assign(f.product.sections[0],{data_state:state,reason,finding_ids:[],result:null,display:null});}
async function refresh(f) {f.product.query_sha256=await digest(f.query);f.product.capability_sha256=await digest(f.capability);}

test('three wrappers and correct signed synthetic receipt validate',async()=>{const f=await fixture();assert.equal(await validateProduct(f.product,f.query,f.capability),true);validateShape('receipt',await receipt(f,'source'));assert.equal((await result(f)).state,'ready');});
test('default context cannot authorize a product',async()=>{const f=await fixture();const r=await assess({...f,now:NOW});assert.equal(r.state,'withheld');assert.equal(r.sections[0].gates.inference,'not_run');assert.equal(r.sections[0].findings.length,0);});
for(const [name,mutate] of [
  ['statistical knob',f=>f.query.k=4],['nested tuning',f=>f.query.resolved.seed=42],['raw transcript',f=>f.product.raw_text='C0_PRIVATE_SENTINEL'],
  ['nested vector',f=>f.product.findings[0].embedding=[1,2]],['reviewer prose',f=>f.product.sections[0].reviewer_note='C0_PRIVATE_SENTINEL'],
  ['self permission',f=>f.product.publication_eligible=true],['self gate',f=>f.product.gates={source:'pass'}],['embedded trusted key',f=>f.product.trustedKeys=[key]],
  ['holdout',f=>f.product.fixture_kind='holdout'],['wrong version',f=>f.query.contract_version='1.1.0'],['unknown schema',f=>f.product.upstream.schema='un.fake.v1'],
  ['mentions not affiliation',f=>f.query.entity_role='country_mentions'],['numeric meeting ID',f=>f.product.evidence[0].meeting_id=1],['boolean count',f=>f.product.fit_population.eligible=true],
  ['nonintegral count',f=>f.product.fit_population.eligible=1.5],['NaN count',f=>f.product.fit.failed=NaN],['unsafe integer',f=>f.product.fit.planned=Number.MAX_SAFE_INTEGER+1],
  ['empty country',f=>f.product.evidence[0].country=''],['unknown metadata field',f=>f.product.upstream.extra='x'],
]) test(`closed schema rejects ${name}`,async()=>{const f=await fixture();mutate(f);const r=await assess({...f,now:NOW});assert.equal(r.valid,false);assert.deepEqual(r.sections,[]);assert.ok(!JSON.stringify(r).includes('C0_PRIVATE_SENTINEL'));});
for(const [name,mutate] of [
  ['requested date changed',f=>f.query.resolved.period.start='2000-01-02'],['requested country changed',f=>f.query.resolved.countries=['XBB']],
  ['unrecorded default',f=>f.query.defaulted_fields=[]],['other baseline default',f=>f.query.resolved.baseline='XBB'],
  ['invalid calendar date',f=>{f.query.requested.period.start='2000-02-30';f.query.resolved.period.start='2000-02-30';}],
  ['date reversed',f=>{f.query.requested.period.start='2000-03-01';f.query.resolved.period.start='2000-03-01';}],
  ['meeting missing',f=>f.query.intent='meeting'],['topic missing',f=>f.query.intent='topic'],['country missing',f=>{f.query.requested.countries=[];f.query.resolved.countries=[];}],
]) test(`query rejects ${name}`,async()=>{const f=await fixture();mutate(f);assert.throws(()=>validateQuery(f.query));});
test('explicit non-US comparison is not silently changed',async()=>{const f=await fixture();f.query.intent='comparison';f.query.requested.baseline='XBB';f.query.resolved.baseline='XBB';f.query.defaulted_fields=[];assert.equal(validateQuery(f.query),true);});
test('recorded date default validates',async()=>{const f=await fixture();f.query.requested.period=null;f.query.defaulted_fields.push('period');assert.equal(validateQuery(f.query),true);});
test('opaque leading-zero identifiers remain distinct',async()=>{const f=await fixture();assert.notEqual(await digest('01'),await digest('1'));assert.notEqual(canonical('001'),canonical(1));assert.equal(f.product.evidence[0].meeting_id,'01');});
for(const [name,mutate] of [
  ['frame denominator',f=>f.product.fit_population.frame++],['view parent drift',f=>f.product.display_population.parent_sha256=H],
  ['display exceeds fit',f=>f.product.display_population.count=3],['planned fits lost',f=>f.product.fit.planned++],
  ['failed count hidden',f=>f.product.fit.failed=1],['duplicate attempt',f=>f.product.fit.ledger.push(structuredClone(f.product.fit.ledger[0]))],
  ['assignment denominator',f=>f.product.fit.assignments.assigned=1],['duplicate evidence',f=>f.product.evidence.push(structuredClone(f.product.evidence[0]))],
  ['bad support join',f=>f.product.findings[0].support=['absent']],['missing support',f=>f.product.findings[0].support=[]],
  ['same support and contrary',f=>{f.product.findings[0].contrary=['e01'];f.product.findings[0].contrary_search='searched';}],
  ['span past parent',f=>f.product.evidence[0].end=10],['partial span',f=>f.product.evidence[0].start=null],
  ['wrong hash basis',f=>f.product.evidence[0].hash_basis='decoded_not_original'],['withheld prose refs',f=>{f.product.sections[0].data_state='withheld';f.product.sections[0].reason='hold';}],
  ['uncalibrated ribbon',f=>f.product.sections[0].uncertainty='calibrated'],['orphan finding',f=>f.product.sections[0].finding_ids=[]],
  ['result digest',f=>f.product.sections[0].result.artifact_sha256=J],['config drift',f=>f.product.fit.configuration_sha256=J],
  ['registry mismatch',f=>f.product.upstream.entity_registry_sha256=J],['missing source unexplained',f=>f.product.upstream.source_sha256=null],
  ['collective attribution',f=>{f.product.evidence[0].capacity='collective';f.product.findings[0].country='XAA';}],
  ['cross-country attribution',f=>f.product.findings[0].country='XBB'],
]) test(`relational validation rejects ${name}`,async()=>{const f=await fixture();mutate(f);await assert.rejects(validateProduct(f.product,f.query,f.capability));});
test('all failed and skipped attempts retained without invented assignments',async()=>{const f=await fixture();empty(f,'failed','fit_failed');Object.assign(f.product.fit,{planned:2,attempted:1,succeeded:0,failed:1,skipped:1,ledger:[{id:'a',model_id:'m',family_id:'f',seed:1,status:'failed',reason:'timeout'},{id:'b',model_id:'m',family_id:'f',seed:2,status:'skipped',reason:'unsupported'}],assignments:{eligible:2,assigned:0,unassigned:0,not_fitted:2}});const r=await result(f);assert.equal(r.state,'failed');assert.equal(r.sections[0].coverage.failed,1);assert.equal(r.sections[0].coverage.skipped,1);});
for(const verdict of ['fail','not_run','not_applicable']) test(`required gate ${verdict} never becomes pass`,async()=>{const f=await fixture(),input=await signed(f);input.receipts=input.receipts.filter(x=>x.payload.gate!=='source');input.receipts.push(await receipt(f,'source',verdict));input.trustedReceiptSetSha256=await receiptSetDigest(input.receipts);const r=await assess(input);assert.equal(r.state,'withheld');assert.equal(r.sections[0].findings.length,0);});
test('competing current pass and fail holds, not newest-wins',async()=>{const f=await fixture(),input=await signed(f);input.receipts.push(await receipt(f,'source','fail','all','local_view',{id:'other_source'}));input.trustedReceiptSetSha256=await receiptSetDigest(input.receipts);const r=await assess(input);assert.equal(r.sections[0].gates.source,'conflict');assert.equal(r.state,'withheld');});
test('PR prose or CI success cannot impersonate source authority',async()=>{const f=await fixture(),input=await signed(f);input.receipts[1]=await receipt(f,'source','pass','all','local_view',{evidence_kind:'coordinator_acceptance'});input.trustedReceiptSetSha256=await receiptSetDigest(input.receipts);assert.equal((await assess(input)).valid,false);});
for(const [name,change] of [
  ['signature mutation',x=>x.receipts[0].signature='A'.repeat(86)+'=='],['unknown key',x=>x.trustedKeys=[]],
  ['key has no source authority',x=>x.trustedKeys=[{...key,gates:['engineering','review','export']}]],
  ['expired receipt',x=>x.now='2000-02-03T00:00:00Z'],['future receipt',x=>x.now='2000-02-01T10:00:00Z'],
  ['digest drift',x=>x.product.run_id='other_run'],['display filter drift',x=>x.product.display_population.count=0],
  ['worker head drift',x=>x.product.provenance.worker_sha='e'.repeat(40)],['merge tree drift',x=>x.product.provenance.effective_tree_sha='f'.repeat(40)],
  ['duplicate receipt',x=>x.receipts.push(x.receipts[0])],['duplicate key IDs',x=>x.trustedKeys=[key,key]],
]) test(`permission rejects ${name}`,async()=>{const x=await signed(await fixture());change(x);x.trustedReceiptSetSha256=await receiptSetDigest(x.receipts);const r=await assess(x);assert.equal(r.valid,false);assert.equal(r.can_export,false);assert.deepEqual(r.sections,[]);});
test('policy cannot remove mandatory source review and export requirements',async()=>{const f=await fixture(),input=await signed(f,['engineering']);assert.equal((await assess(input)).state,'withheld');});
test('descriptive product needs no inferential or comparability acceptance',async()=>{const r=await result(await fixture());assert.equal(r.state,'ready');assert.equal(r.sections[0].gates.inference,'not_run');assert.equal(r.sections[0].gates.comparability,'not_run');});
test('unverified source never means a complete zero finding',async()=>{const f=await fixture();empty(f);f.product.fit_population.unverified=1;f.product.fit_population.frame=3;const r=await result(f);assert.equal(r.state,'partial');assert.equal(r.sections[0].reason,'incomplete_coverage');});
test('complete source no-match remains empty',async()=>{const f=await fixture();empty(f);assert.equal((await result(f)).state,'empty');});
test('missing source does not expose findings or evidence',async()=>{const f=await fixture();f.product.upstream.source_sha256=null;f.product.upstream.source_missing_reason='source_unavailable';const r=await result(f);assert.equal(r.reason,'source_unavailable');assert.deepEqual(r.sections[0].evidence,[]);assert.equal(r.sections[0].coverage,null);});
for(const target of ['public_site','email']) test(`${target} prohibited even with signed authorizations`,async()=>{const f=await fixture();f.capability.destinations.push(target);await refresh(f);const r=await assess(await signed(f,undefined,target));assert.equal(r.state,'withheld');assert.equal(r.reason,'destination_prohibited');assert.equal(r.publication_eligible,false);});
test('local export requires its own destination receipt',async()=>{const f=await fixture();assert.equal((await assess({...await signed(f),destination:'local_export'})).can_export,false);assert.equal((await assess(await signed(f,undefined,'local_export'))).can_export,true);});
test('development cannot be enabled by a flag or even synthetic signer',async()=>{const f=await fixture();f.product.fixture_kind='development';const r=await result(f);assert.equal(r.reason,'development_not_authorized');assert.equal(r.state,'withheld');});
test('resource cap withholds rather than selecting a smaller population',async()=>{const f=await fixture();f.capability.regime.max_frame=1;await refresh(f);const r=await result(f);assert.equal(r.reason,'resource_limit');assert.equal(f.product.fit_population.frame,2);});
test('unsupported source regime withholds',async()=>{const f=await fixture();f.capability.regime.languages=['fr'];await refresh(f);assert.equal((await result(f)).reason,'unsupported_regime');});
test('display gate failure does not erase valid descriptive metric',async()=>{const f=await fixture();f.product.sections.push({id:'map',kind:'map',claim:'descriptive',data_state:'available',reason:null,finding_ids:[],result:structuredClone(f.product.sections[0].result),display:structuredClone(f.product.sections[0].result),uncertainty:'unavailable'});const r=await result(f);assert.equal(r.state,'partial');assert.equal(r.sections[0].state,'ready');assert.equal(r.sections[1].state,'withheld');assert.equal(r.sections[1].display,null);});
test('inferential display requires distinct inference acceptance',async()=>{const f=await fixture();f.product.findings[0].claim='inferential';f.product.sections[0].claim='inferential';f.product.sections[0].uncertainty='calibrated';const r=await result(f);assert.equal(r.state,'withheld');assert.ok(r.sections[0].blocked_gates.includes('inference'));});
test('session erases previous result after corrupt import',async()=>{const f=await fixture(),s=createSession();await s.load(await signed(f));assert.equal(s.snapshot().state,'ready');f.product.bad='C0_PRIVATE_SENTINEL';await s.load({...f,now:NOW});assert.deepEqual(s.snapshot().sections,[]);});
test('invalidation races do not revive prior permissions',async()=>{const s=createSession(),input=await signed(await fixture());const pending=s.load(input);s.invalidate();assert.equal(await pending,null);assert.equal(s.snapshot(),null);});
test('snapshots cannot mutate stored results',async()=>{const s=createSession();await s.load(await signed(await fixture()));s.snapshot().sections[0].state='hacked';assert.equal(s.snapshot().sections[0].state,'ready');});
test('same input replay is deterministic but receipts are reverified',async()=>{const x=await signed(await fixture());assert.deepEqual(await assess(x),await assess(x));const a=await assess({...x,now:'2000-02-03T00:00:00Z'});assert.equal(a.valid,false);});
for(const [name,text] of [
  ['duplicate','{"a":1,"a":2}'],['escaped duplicate','{"a":1,"\\u0061":2}'],['prototype','{"__proto__":{}}'],
  ['trailing','{}true'],['trailing comma','[1,]'],['lone surrogate','"\\ud800"'],['infinity','1e999'],['unsafe number','9007199254740992'],
  ['deep', '['.repeat(26)+'0'+']'.repeat(26)],['size',' '.repeat(2097153)],
]) test(`wire rejects ${name}`,()=>assert.throws(()=>parseStrict(text)));
test('wire roundtrip preserves IDs, null and zero separately',()=>assert.deepEqual(parseStrict('{"ids":["01","1"],"missing":null,"zero":0}'),{ids:['01','1'],missing:null,zero:0}));
test('stable digest independent of key insertion order',async()=>assert.equal(await digest({z:1,a:'01'}),await digest({a:'01',z:1})));
test('capability fallback cannot point to itself',async()=>{const f=await fixture();f.capability.fallback=f.capability.id;assert.throws(()=>validateCapability(f.capability));});
test('max length opaque meeting remains intact',async()=>{const f=await fixture();f.product.evidence[0].meeting_id='0'.repeat(160);assert.equal(await validateProduct(f.product,f.query,f.capability),true);f.product.evidence[0].meeting_id+='1';await assert.rejects(validateProduct(f.product,f.query,f.capability));});
test('async assessment uses immutable input snapshots',async()=>{const input=await signed(await fixture());const pending=assess(input);input.product.findings[0].support=['attacker'];input.product.sections[0].reason='C0_PRIVATE_SENTINEL';input.trustedKeys[0]={...key,gates:[]};const r=await pending;assert.equal(r.state,'ready');assert.deepEqual(r.sections[0].findings[0].support,['e01']);assert.ok(!JSON.stringify(r).includes('C0_PRIVATE_SENTINEL'));});
test('non-enumerable smuggled fields rejected',async()=>{const f=await fixture();Object.defineProperty(f.product,'private_text',{value:'C0_PRIVATE_SENTINEL'});assert.equal((await assess({...f,now:NOW})).valid,false);});
test('untrusted receipt field rejected before getters execute',async()=>{const f=await fixture();let calls=0;Object.defineProperty(f.product.upstream,'source_sha256',{get(){calls++;return H;},enumerable:true});const r=await assess({...f,now:NOW});assert.equal(r.valid,false);assert.equal(calls,0);});
test('safe export rechecks destination and omits withheld sections',async()=>{const {exportReadModel}=await import('./contracts.mjs');const f=await fixture();f.product.sections.push({id:'map',kind:'map',claim:'descriptive',data_state:'available',reason:null,finding_ids:[],result:{schema:'un.parallel-analysis.v1',artifact_sha256:H,pointer:'/secret_result'},display:{schema:'un.parallel-analysis.v1',artifact_sha256:H,pointer:'/secret_display'},uncertainty:'unavailable'});const input=await signed(f,undefined,'local_export');const out=await exportReadModel(input);assert.equal(out.ok,true);assert.ok(!out.utf8.includes('secret_result'));assert.ok(!out.utf8.includes('secret_display'));assert.equal(JSON.parse(out.utf8).sections[1].state,'withheld');});
test('safe export refuses view-only receipt and stale authorization',async()=>{const {exportReadModel}=await import('./contracts.mjs');const f=await fixture();assert.equal((await exportReadModel(await signed(f))).utf8,null);assert.equal((await exportReadModel({...await signed(f,undefined,'local_export'),now:'2000-02-03T00:00:00Z'})).utf8,null);});
test('derived readiness has its own closed output shape, never input authority',async()=>{const f=await fixture(),r=await result(f);assert.equal(validateShape('readiness',r),true);const invalid=await assess({...f,product:r,now:NOW});assert.equal(invalid.valid,false);assert.equal(validateShape('readiness',invalid),true);});
test('unevaluated eligible items cannot become a complete empty result',async()=>{const f=await fixture();empty(f);f.product.fit.assignments.assigned=1;f.product.fit.assignments.not_fitted=1;const r=await result(f);assert.equal(r.state,'partial');assert.equal(r.sections[0].reason,'incomplete_coverage');});
