/** Independent coordinator U2 probes. Only fictional metadata and ephemeral test keys. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const root=resolve(process.env.U2_CHECKOUT??process.cwd());
const load=p=>import(pathToFileURL(resolve(root,p)).href);
const {fixtureMetadata,environment,select,rehashInventory}=await load('research/integration/question_router/tests/fixtures.mjs');
const {validateMetadata,queryFromSelection,planQuery,snapshot}=await load('research/integration/question_router/metadata.mjs');
const {createU1Provider}=await load('research/integration/question_router/router.mjs');
const {digest,canonical}=await load('research/integration/product_contracts/contracts.mjs');
const u1=resolve(process.env.U1_CHECKOUT??root,'site/parallel/w07-diplomat-ux/controller.mjs');
const bytes=readFileSync(u1);
assert.equal(createHash('sha1').update(Buffer.concat([Buffer.from(`blob ${bytes.length}\0`),bytes])).digest('hex'),'7abba75142aab66e9b197ce7d04154c87a013a30');
const {createController}=await import(pathToFileURL(u1).href);
const plan=async(m,s=select())=>(await (await environment(m)).router()).plan(s);
const orphan=(m,extra={})=>m.catalog.meetings.push({...m.catalog.meetings[0],id:'catalog_only',...extra});

test('positive: independently pinned U1 consumes exact source-bound descriptive metadata',async()=>{
  const e=await environment();await e.register(select({country:'BRA'}));
  const c=createController(createU1Provider(await e.router()));
  assert.equal((await c.create(select({country:'BRA'}))).phase,'ready');
  assert.ok(await c.exportModel());
});
for(const [name,extra,reason] of [
  ['missing inventory',{},'meeting_inventory_missing'],
  ['protected missing inventory',{protected:true},'protected_scope'],
  ['unknown date without inventory',{date:null},'meeting_date_unknown'],
  ['protected unknown date',{date:null,protected:true},'protected_scope']
])test('R1: catalogue '+name+' cannot disappear from date scope',async()=>{
  const m=await fixtureMetadata();orphan(m,extra);const e=await environment(m),r=await e.router();
  const o=await r.route(select());assert.equal(o.state,'unavailable');assert.equal(o.reason,reason);
  assert.equal(o.bundle,null);assert.equal(o.plan.fit_population,null);assert.deepEqual(o.plan.classification,[]);assert.equal(e.state.lookups,0);
});
test('R1: selecting a catalogue-only meeting cannot manufacture complete emptiness',async()=>{
  const m=await fixtureMetadata();orphan(m);
  const p=await plan(m,select({page:'meetings',meeting:'catalog_only'}));
  assert.equal(p.state,'unavailable');assert.equal(p.reason,'meeting_inventory_missing');
});
test('R1 positive: out-of-period missing/protected meeting does not suppress a valid query',async()=>{
  const m=await fixtureMetadata();orphan(m,{date:'2024-09-24',period_id:'002',protected:true});
  assert.equal((await plan(m)).state,'planned');
});
test('R1 positive: specific meeting selection does not widen to another catalogue meeting',async()=>{
  const m=await fixtureMetadata();orphan(m,{protected:true});
  assert.equal((await plan(m,select({page:'meetings',meeting:'01'}))).state,'planned');
});
for(const [field,value] of [['start',1],['end',20],['parent_length',50],['parent_id','different_parent']])test('R2: changed '+field+' invalidates the fitted unit identity',async()=>{
  const m=await fixtureMetadata(),changed=snapshot(m);changed.bindings[0][field]=value;
  const a=await plan(m),b=await plan(changed);
  assert.equal(a.state,'planned');assert.equal(b.state,'planned');
  assert.equal(a.inventory_sha256,b.inventory_sha256);assert.equal(a.source_sha256,b.source_sha256);
  assert.notEqual(a.fit_population.sha256,b.fit_population.sha256);
  assert.notEqual(a.display_population.sha256,b.display_population.sha256);
});
test('R2: changed source language changes fit identity even when all sources still match',async()=>{
  const m=await fixtureMetadata(),changed=snapshot(m);changed.bindings.forEach(b=>b.language='fr');
  assert.notEqual((await plan(m)).fit_population.sha256,(await plan(changed)).fit_population.sha256);
});
test('R2 positive: country display filtering preserves fitted identity',async()=>{
  const m=await fixtureMetadata(),a=await plan(m,select({country:'BRA'})),b=await plan(m,select({country:'USA'}));
  assert.equal(a.fit_population.sha256,b.fit_population.sha256);assert.notEqual(a.display_population.sha256,b.display_population.sha256);
});
test('R2 positive: changing a navigation alias does not refit source units',async()=>{
  const m=await fixtureMetadata(),changed=snapshot(m);changed.catalog.countries[0].aliases.push('Fictional label');
  assert.equal((await plan(m)).fit_population.sha256,(await plan(changed)).fit_population.sha256);
});
function failedLedger(b,skipped=false){
  const f=b.product.fit;f.succeeded=0;f.failed=skipped?0:1;f.skipped=skipped?1:0;f.attempted=skipped?0:1;
  f.ledger[0].status=skipped?'skipped':'failed';f.ledger[0].reason='independent_synthetic_failure';
  f.assignments.assigned=0;f.assignments.not_fitted=f.assignments.eligible;
}
for(const skipped of [false,true])test('R3: all-'+(skipped?'skipped':'failed')+' exploratory result cannot expose findings',async()=>{
  const e=await environment(),b=await e.register(select(),'semantic');failedLedger(b,skipped);await e.authorize(b);
  const o=await (await e.router()).route(select());assert.equal(o.state,'withheld');assert.equal(o.bundle,null);
  assert.equal(o.reason,'unfitted_analytical_result');assert.equal(e.state.lookups,1);
});
test('R3 positive: descriptive evidence can survive an unrelated failed attempt',async()=>{
  const e=await environment(),b=await e.register(select(),'description');failedLedger(b);await e.authorize(b);
  const o=await (await e.router()).route(select());assert.equal(o.state,'partial');assert.ok(o.readiness.sections[0].findings.length);
});
test('R3 positive: genuine failed result falls back with its full failure ledger',async()=>{
  const e=await environment();await e.register(select(),'semantic','failed');await e.register(select());
  const o=await (await e.router()).route(select());assert.equal(o.state,'ready');assert.equal(o.trace[0].fit.failed,1);assert.equal(o.trace.length,2);
});
for(const gate of ['engineering','source','review','export'])test('trust floor: a signed '+gate+' veto never triggers alternate approval search',async()=>{
  const e=await environment();await e.register(select(),'semantic','auto',{[gate]:'fail'});await e.register(select());
  const o=await (await e.router()).route(select());assert.equal(o.state,'withheld');assert.equal(e.state.lookups,1);
});
test('complete signed-decision commitment detects omitted veto before U1 output',async()=>{
  const e=await environment(),b=await e.register(select()),r=await e.router(),c=createController(createU1Provider(r));
  await c.create(select());await e.veto(b);await c.importBundle(JSON.stringify(b));
  assert.equal(c.snapshot().phase,'withheld');assert.equal(c.snapshot().canExport,false);
});
test('host key revocation invalidates U1 saved replay and export',async()=>{
  const e=await environment();await e.register(select());const c=createController(createU1Provider(await e.router()));
  await c.create(select());await c.save();e.state.revoked=true;e.state.revision++;
  await c.openSaved(c.snapshot().saved[0].id);assert.equal(c.snapshot().phase,'withheld');assert.equal(await c.exportModel(),null);
});
test('destination separation: permitted view does not grant a local export',async()=>{
  const e=await environment();await e.register(select(),'description','auto',{'local_export:export':'fail'});
  const c=createController(createU1Provider(await e.router()));await c.create(select());
  assert.equal(c.snapshot().phase,'ready');assert.equal(await c.exportModel(),null);
});
test('async trust replacement cannot admit a stale result',async()=>{
  const e=await environment();await e.register(select());let count=0;
  const r=await e.router({getTrust:async id=>{const t=await e.getTrust(id);if(++count===2)t.revision='replaced';return t;}});
  const o=await r.route(select());assert.equal(o.reason,'trust_changed');assert.equal(o.bundle,null);
});
test('source denominator corruption cannot be repaired by signing it',async()=>{
  const e=await environment(),b=await e.register(select());b.product.fit_population.frame++;await e.authorize(b);
  const o=await (await e.router()).route(select());assert.equal(o.state,'withheld');assert.equal(o.bundle,null);
});
test('source span corruption cannot be repaired by signing it',async()=>{
  const e=await environment(),b=await e.register(select());b.product.evidence[0].end=20;await e.authorize(b);
  const o=await (await e.router()).route(select());assert.equal(o.state,'withheld');assert.equal(o.reason,'evidence_attribution_span');
});
test('metadata self-commitment never replaces the independently supplied pin',async()=>{
  const m=await fixtureMetadata();await assert.rejects(()=>validateMetadata(m,undefined));
});
test('missing sources remain partial rather than false country absence',async()=>{
  const e=await environment(),s=select({country:'CAN',topic:'climate',period:{start:'2024-09-24',end:'2024-09-24'}});
  await e.register(s);const o=await (await e.router()).route(s);assert.equal(o.state,'partial');assert.equal(o.plan.fit_population.missing,1);assert.equal(o.plan.fit_population.unverified,1);
});
test('collective/recorded affiliation cannot become national support',async()=>{
  const m=await fixtureMetadata(),p=await plan(m,select({country:'BRA'}));assert.deepEqual(p.display_ids,['r01']);assert.equal(p.fit_population.eligible,5);
});
test('unsupported history and absent evidence service remain explicit integration limits',async()=>{
  const e=await environment(),r=await e.router();assert.equal((await r.route(select({period:{start:'1999-01-01',end:'1999-01-01'}}))).state,'unavailable');
  await assert.rejects(()=>createU1Provider(r).getEvidence(),/evidence_service_not_connected/);
});
