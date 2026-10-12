'use strict';
// Invented observations only: verify W1 source selection against the coordinator's
// real source-inventory-v1 validator without reading any historical original bytes.
const assert=require('node:assert/strict');
const {makeFixture,SETTINGS}=require('../examples/synthetic_fixture.cjs');
const {run}=require('../runner.cjs');
const F=require('../frame.cjs');
const {linkW1Inventory}=require('../historical_link.cjs');
const I=require('../../../docs/parallel-work/source-inventory-v1.cjs');

const schema=require('../schemas/historical-link.candidate.v0.schema.json');
function strictShape(rule,value,at='root'){
  if(Object.hasOwn(rule,'const'))assert.deepEqual(value,rule.const,at+' const');
  if(rule.enum)assert(rule.enum.includes(value),at+' enum');
  if(rule.type){
    const ts=Array.isArray(rule.type)?rule.type:[rule.type];
    assert(ts.some(t=>t==='null'?value===null:t==='object'?value!==null&&typeof value==='object'&&!Array.isArray(value):
      t==='array'?Array.isArray(value):t==='integer'?Number.isSafeInteger(value):typeof value===t),at+' type');
  }
  if(typeof value==='string'){
    if(rule.minLength!==undefined)assert(value.length>=rule.minLength,at+' minimum length');
    if(rule.pattern)assert(new RegExp(rule.pattern).test(value),at+' pattern');
  }
  if(Array.isArray(value)){
    if(rule.minItems!==undefined)assert(value.length>=rule.minItems,at+' minimum items');
    if(rule.items)value.forEach((v,i)=>strictShape(rule.items,v,at+'['+i+']'));
  }
  if(value!==null&&typeof value==='object'&&!Array.isArray(value)){
    for(const k of rule.required||[])assert(Object.hasOwn(value,k),at+' missing '+k);
    for(const [k,v] of Object.entries(value)){
      if(rule.properties&&Object.hasOwn(rule.properties,k))strictShape(rule.properties[k],v,at+'.'+k);
      else if(rule.additionalProperties===false)assert.fail(at+' unexpected '+k);
    }
  }
  return true;
}

function makePair(){
  const {frame,saved}=makeFixture();
  for(const row of frame.observations)
    if(row.source_status==='available')
      row.original_source_sha256=F.digest('invented original:'+row.meeting_id);
  const panel={schema:'un.longitudinal-panel.v1',split:'synthetic',
    periods:[{id:'first',start:'2026-01-01',end:'2026-01-03'},
      {id:'second',start:'2026-01-04',end:'2026-01-09'}],
    observations:[]};
  for(const o of frame.observations){
    panel.observations.push({
      id:o.id,period:o.date<='2026-01-03'?'first':'second',year:2026,
      actor_kind:'synthetic',actor_id:o.country||'fictional-unknown',
      genre:'synthetic',source_status:o.source_status,
      missing_reason:o.missing_reason??null,date:o.date,
      meeting_id:o.meeting_id??null,source_family_id:o.source_family_id??null,
      source_sha256:o.original_source_sha256??null,text_sha256:o.text_sha256,
      review_status:o.review_status});
  }
  panel.observations.push({
    id:'synthetic-available-not-selected',period:'second',year:2026,actor_kind:'synthetic',
    actor_id:'fictional-extra',genre:'synthetic',source_status:'available',missing_reason:null,
    date:'2026-01-08',meeting_id:'fictional-extra-meeting',source_family_id:'fictional-extra-family',
    source_sha256:F.digest('fictional extra PV'),text_sha256:F.digest('fictional extra address'),
    review_status:'not_applicable'
  });
  for(const period of ['first','second'])panel.observations.push({
    id:'synthetic-unverified-'+period,period,year:2026,actor_kind:'synthetic',
    actor_id:'fictional-unverified-'+period,genre:'synthetic',
    source_status:'unverified',missing_reason:'Invented source not yet independently verified',
    date:null,meeting_id:null,source_family_id:null,source_sha256:null,text_sha256:null,
    review_status:'not_applicable'
  });
  const upstream={source_schema:frame.source_schema,source_engine:frame.source_engine,
    source_hash_basis:frame.source_hash_basis,source_sha256:frame.source_sha256,
    selection_sha256:F.digest(panel.observations.map(v=>[v.id,v.text_sha256]))};
  const inventory=I.fromPanel(panel,upstream);
  return {frame,saved,inventory};
}
function cloneRun(run){
  const value=structuredClone({...run});
  Object.defineProperty(value,'_internal_frame',{enumerable:false,configurable:true,
    value:structuredClone(run._internal_frame)});
  return value;
}
function mutateInventory(inventory,mutate){
  const x=structuredClone(inventory);mutate(x);
  x.inventory_sha256=I.hash(x.observations);return x;
}
function refuse(callback,message){
  assert.throws(callback,e=>String(e.message).includes(message),message);
}
async function main(){
  const {frame,saved,inventory}=makePair();
  const modelSettings=SETTINGS.slice(0,2);
  const out=await run(frame,modelSettings,{saved,replicates:3,group_seed:83});
  const original=JSON.stringify(out);
  const inventoryOriginal=JSON.stringify(inventory);
  const candidate=linkW1Inventory(out,inventory);
  assert.equal(candidate.schema,'un.w1-historical-inventory-link.candidate.v0');
  assert(strictShape(schema,candidate));
  const fake=structuredClone(candidate);fake.publication_eligible=true;
  assert.throws(()=>strictShape(schema,fake));
  const leak=structuredClone(candidate);leak.original_rows=[];
  assert.throws(()=>strictShape(schema,leak));
  assert.equal(candidate.fixture_kind,'synthetic');
  assert.equal(candidate.coverage.inventory_total,28);
  assert.equal(candidate.coverage.verified_available,25);
  assert.equal(candidate.coverage.unverified,2);
  assert.equal(candidate.coverage.other_missing,1);
  assert.equal(candidate.coverage.w1_selected_fit_eligible,24);
  assert.equal(candidate.coverage.w1_excluded_in_frame,1);
  assert.equal(candidate.coverage.verified_not_selected,1);
  assert.equal(candidate.models.length,2);
  assert(candidate.models.every(m=>m.status==='fitted'&&m.assigned===24));
  assert.equal(candidate.group_refits.length,4);
  assert.equal(candidate.legacy_interchange_v1,'withheld');
  assert(!JSON.stringify(candidate).includes('synthetic-01'),'Row ID leaked into aggregate');
  assert(!JSON.stringify(candidate).includes('Harbor ferry'),'Original source text leaked');
  assert.equal(JSON.stringify(out),original,'Source-bound fit changed during linking');
  assert.equal(JSON.stringify(inventory),inventoryOriginal,'Sidecar changed during linking');

  const cases=[
    ['upstream hash basis',x=>{x.upstream.source_hash_basis='utf8_response_text';},'hash basis mismatch'],
    ['source schema relabel',x=>{x.upstream.source_schema='un.passage-corpus.v1';},'source schema mismatch'],
    ['tampered original source SHA',x=>{x.upstream.source_sha256=F.digest('not the archive');},'SHA-256 mismatch'],
    ['changed meeting',x=>{x.observations.find(o=>o.id===frame.observations[0].id).meeting_id='wrong-meeting';},'meeting/source group mismatch'],
    ['changed source family',x=>{x.observations.find(o=>o.id===frame.observations[0].id).source_family_id='new-family';},'source-family identity mismatch'],
    ['text SHA change',x=>{x.observations.find(o=>o.id===frame.observations[0].id).text_sha256=F.digest('changed synthetic text');},'observed-text digest mismatch'],
    ['verified original hash change',x=>{
      for(const o of x.observations.filter(o=>o.meeting_id===frame.observations[0].meeting_id))
        o.source_sha256=F.digest('different source byte hash');
    },'original-source identifier mismatch'],
    ['wrong missing reason',x=>{x.observations.find(o=>o.source_status==='unavailable').missing_reason='pretend zero';},'unavailable observed record reason mismatch']
  ];
  for(const [label,mutation,message] of cases){
    const x=mutateInventory(inventory,mutation);
    refuse(()=>linkW1Inventory(out,x),message);
  }
  const r0=cloneRun(out);r0.fit_records[0].assignments.pop();
  refuse(()=>linkW1Inventory(r0,inventory),'incomplete or invalid hard assignment');
  const r1=cloneRun(out);r1.fit_records[0].observation_ids[0]='different';
  refuse(()=>linkW1Inventory(r1,inventory),'population/order changed');
  const r2=cloneRun(out);r2.frame.selection_sha256=F.digest('alternative cohort');
  refuse(()=>linkW1Inventory(r2,inventory),'cannot be reproduced');
  const r3=cloneRun(out);r3.model_reports[0].group_stability.meeting.runs[0].selected++;
  refuse(()=>linkW1Inventory(r3,inventory),'refit changed denominator');
  const r4=cloneRun(out);r4._internal_frame[0].original_source_sha256=null;
  refuse(()=>linkW1Inventory(r4,inventory),'synthetic original-source identifier mismatch');
  const invOld=structuredClone(inventory);
  invOld.legacy_v1_binding={mode:'verified_subset_projection',reason:null,
    legacy_selection_sha256:F.digest('fake-v1'),legacy_eligible:25};
  refuse(()=>linkW1Inventory(out,invOld),'legacy');
  const invLeak=structuredClone(inventory);invLeak.observations[0].text='not source linked';
  refuse(()=>linkW1Inventory(out,invLeak),'forbidden property');
  const invStatus=mutateInventory(inventory,x=>{
    const row=x.observations.find(o=>o.source_status==='unverified');
    row.source_status='available';
  });
  refuse(()=>linkW1Inventory(out,invStatus),'Verified rows require');
  const invInvalid=structuredClone(inventory);
  invInvalid.observations[0].text_sha256='not-a-digest';
  refuse(()=>linkW1Inventory(out,invInvalid),'pattern');

  process.stdout.write(JSON.stringify({suite:'w1-historical-inventory-link-synthetic',
    positive:1,negative:19,failed:0,
    observations:28,source_verified:25,selected:24,unverified:2,
    reserved_2026_text_accessed:0,public_development_rows_exported:0,
    legacy_v1_modified:false,source_rows_serialized:false})+'\n');
}
main().catch(e=>{process.stderr.write('FAIL '+(e.stack||e)+'\n');process.exitCode=1;});
