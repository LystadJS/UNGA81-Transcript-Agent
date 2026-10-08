'use strict';
/* Synthetic-only compatibility, provenance and denominator regressions. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {fromPanel,validateInventory}=require('./source-inventory-v1.cjs');
const contract=fs.readFileSync(path.join(__dirname,'INTERCHANGE_V1.md'),'utf8');
const fence=String.fromCharCode(96).repeat(3);
const pos=contract.indexOf(fence+'json',contract.indexOf('## 4. Mapping example'));
const end=contract.indexOf(fence,pos+7);
assert(pos>=0 && end>pos);
const base=JSON.parse(contract.slice(pos+7,end).trim());
const mk=()=>{
  const legacy=structuredClone(base);
  legacy.observations[0].meeting_id='fictional-UN-meeting';
  legacy.observations[0].source_family_id='fictional-parent-series';
  const upstream={source_schema:legacy.upstream.source_schema,
    source_engine:legacy.upstream.source_engine,
    source_hash_basis:legacy.upstream.source_hash_basis,
    source_sha256:legacy.upstream.source_sha256,
    selection_sha256:legacy.upstream.selection_sha256};
  const panel={schema:'un.longitudinal-panel.v1',split:'synthetic',
    periods:[{id:'before',start:'2026-09-01',end:'2026-09-30'},
      {id:'after',start:'2026-10-01',end:'2026-10-04'}],
    observations:[
      {id:'fictional-unverified',period:'before',year:2026,
        actor_kind:'synthetic',actor_id:'fictional-actor',genre:'synthetic',
        source_status:'unverified',missing_reason:'not_collected',
        date:null,meeting_id:null,source_family_id:null,source_sha256:null,
        text_sha256:null,review_status:'not_applicable',vector:null,map:null},
      {id:'synthetic-1',period:'after',year:2026,actor_kind:'synthetic',
        actor_id:'fictional-actor',genre:'synthetic',
        source_status:'available',missing_reason:null,date:'2026-10-01',
        meeting_id:'fictional-UN-meeting',source_family_id:'fictional-parent-series',
        source_sha256:'a'.repeat(64),text_sha256:'d'.repeat(64),
        review_status:'not_applicable',vector:[2,3,4],map:[0,1],text:'forbidden speech text'}
    ]};
  return {legacy,upstream,panel};
};
const passes=[];
function test(name,fn){fn();passes.push(name);console.log('PASS',name);}
function reject(fn,fragment){assert.throws(fn,e=>String(e.message).includes(fragment),fragment);}
test('old v1 remains unmodified and unverified population is explicit',()=>{
  const {legacy,upstream,panel}=mk();const old=JSON.stringify(legacy);
  const i=fromPanel(panel,upstream);
  assert.equal(JSON.stringify(legacy),old);
  assert.equal(i.population.total_in_frame,2);
  assert.equal(i.population.unverified,1);
  assert.equal(i.legacy_v1_binding.mode,'withheld');
  assert(!JSON.stringify(i).includes('forbidden speech text'));
  assert(!JSON.stringify(i).includes('"vector"'));
  assert(!JSON.stringify(i).includes('"map"'));
});
test('synthetic compatible subset binds unchanged v1 by exact ID/date/hash',()=>{
  const {legacy,upstream,panel}=mk();
  const i=fromPanel(panel,upstream,{legacy});
  assert.equal(validateInventory(i,legacy).legacy_binding,'verified_subset_projection');
  assert.equal(legacy.observations.length,1);
});
test('modified source sha does not silently bind to legacy',()=>{
  const {legacy,upstream,panel}=mk();
  legacy.upstream.source_sha256='e'.repeat(64);
  reject(()=>fromPanel(panel,upstream,{legacy}),'different original sources');
});
test('replaced observed ID cannot be projected as valid source',()=>{
  const {legacy,upstream,panel}=mk();
  legacy.observations[0].id='fake-id';
  reject(()=>fromPanel(panel,upstream,{legacy}),'Legacy source identity');
});
test('unknown time and original source IDs remain null, not invented',()=>{
  const {upstream,panel}=mk();
  const i=fromPanel(panel,upstream);
  const u=i.observations.find(o=>o.source_status==='unverified');
  assert.equal(u.event_date,null);
  assert.equal(u.source_sha256,null);
  assert.equal(u.meeting_id,null);
});
test('available observation without date or digest fails',()=>{
  const {upstream,panel}=mk();panel.observations[1].date=null;
  reject(()=>fromPanel(panel,upstream),'Verified rows require');
});
test('fake zero vector in missing row not serialized as evidence',()=>{
  const {upstream,panel}=mk();
  panel.observations[0].vector=[0,0,0];
  const i=fromPanel(panel,upstream);
  assert.equal(i.population.unverified,1);
  assert(!JSON.stringify(i).includes('"vector"'));
});
test('unverified cannot be marked available without original hash',()=>{
  const {upstream,panel}=mk();panel.observations[0].source_status='available';
  panel.observations[0].missing_reason=null;
  reject(()=>fromPanel(panel,upstream),'Verified rows require');
});
test('duplicate country-year keys rejected',()=>{
  const {upstream,panel}=mk();
  panel.split='development';panel.observations.forEach(r=>{
    r.actor_kind='recorded_affiliation';r.actor_id='ZZZ';});
  panel.observations.push({...panel.observations[0],id:'duplicated-actor-year'});
  const src={...upstream,source_hash_basis:'raw_response_bytes',
    source_schema:'un.p2.original-pv-reconciled.v1'};
  reject(()=>fromPanel(panel,src),'Duplicate country-year');
});
test('historical P2 original schema is supported only in sidecar, not old v1',()=>{
  const {upstream,panel,legacy}=mk();
  panel.split='development';panel.periods=[
    {id:'before',start:'2019-01-01',end:'2019-12-31'},
    {id:'after',start:'2022-01-01',end:'2022-12-31'}];
  panel.observations[0].year=2019;panel.observations[1].year=2022;
  panel.observations[1].date='2022-09-22';
  panel.observations.forEach(r=>{r.actor_kind='recorded_affiliation';r.actor_id='ZZZ';});
  const src={...upstream,source_schema:'un.p2.original-pv-reconciled.v1',
    source_hash_basis:'raw_response_bytes'};
  const i=fromPanel(panel,src);assert.equal(validateInventory(i).legacy_binding,'withheld');
  reject(()=>fromPanel(panel,src,{legacy}),'different original sources');
});
test('reserved October 2026 dates refused',()=>{
  const {upstream,panel}=mk();panel.periods[1].end='2026-10-06';
  panel.observations[1].date='2026-10-05';
  reject(()=>fromPanel(panel,upstream),'Reserved October 5–6');
});
test('denominator corruption, tampered digest, and raw text properties refused',()=>{
  const {upstream,panel}=mk();const i=fromPanel(panel,upstream);
  const a=structuredClone(i);a.coverage[0].unverified=2;
  reject(()=>validateInventory(a),'Period coverage mismatch');
  const b=structuredClone(i);b.observations[0].actor_id='tampered';
  reject(()=>validateInventory(b),'Inventory rows changed');
  const c=structuredClone(i);c.observations[0].text='raw';
  reject(()=>validateInventory(c),'forbidden property');
});
test('claimed legacy link without independently supplied legacy source refused',()=>{
  const {upstream,panel}=mk();const i=fromPanel(panel,upstream);
  i.legacy_v1_binding={mode:'verified_subset_projection',reason:null,
    legacy_eligible:1,legacy_selection_sha256:'c'.repeat(64)};
  reject(()=>validateInventory(i),'not validated by schema alone');
});
console.log(JSON.stringify({suite:'source-inventory-v1-synthetic',tests:passes.length,failed:0,
 legacy_v1_unchanged:true,reserved_meetings_accessed:0,private_text_exported:false}));
