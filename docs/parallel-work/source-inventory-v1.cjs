'use strict';
/* Coordinator-owned supplemental inventory contract. No source text, fitting or network. */
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const schema = JSON.parse(fs.readFileSync(path.join(__dirname,'source-inventory-v1.schema.json'),'utf8'));
const HEX = /^[a-f0-9]{64}$/;
const RESERVED = new Set(['2026-10-05', '2026-10-06']);
const other = new Set(['unverified','unavailable','failed','inventory_failed','empty_transcript','excluded_language']);
function assert(ok,why){if(!ok)throw Error(why);}
function hash(obj){return crypto.createHash('sha256').update(JSON.stringify(obj)).digest('hex');}
function isObj(x){return x !== null && typeof x === 'object' && !Array.isArray(x);}
function shape(def,x,at='$'){
  if (Object.hasOwn(def,'const'))assert(x===def.const,at+': wrong const');
  if (def.enum)assert(def.enum.includes(x),at+': unknown enum');
  if (def.type){
    const types=Array.isArray(def.type)?def.type:[def.type];
    assert(types.some(t=>t==='null'?x===null:t==='object'?isObj(x):
      t==='array'?Array.isArray(x):t==='integer'?Number.isSafeInteger(x):
      t==='number'?typeof x==='number'&&Number.isFinite(x):typeof x===t),at+': wrong type');
  }
  if(typeof x==='string'){
    if(def.minLength!==undefined)assert(x.length>=def.minLength,at+': too short');
    if(def.pattern)assert(new RegExp(def.pattern).test(x),at+': invalid pattern');
  }
  if(typeof x==='number'&&def.minimum!==undefined)assert(x>=def.minimum,at+': less than minimum');
  if(typeof x==='number'&&def.maximum!==undefined)assert(x<=def.maximum,at+': larger than maximum');
  if(Array.isArray(x)){
    if(def.minItems!==undefined)assert(x.length>=def.minItems,at+': too few entries');
    x.forEach((v,i)=>{if(def.items)shape(def.items,v,at+'['+i+']');});
  }
  if(isObj(x)){
    for(const k of def.required??[])assert(Object.hasOwn(x,k),at+': missing '+k);
    for(const [k,v] of Object.entries(x)){
      if(def.properties?.[k])shape(def.properties[k],v,at+'.'+k);
      else assert(def.additionalProperties!==false,at+': forbidden property '+k);
    }
  }
}
function validDate(v){
  if(typeof v!=='string'||!/^(\d{4})-(\d\d)-(\d\d)$/.test(v))return false;
  const [y,m,d]=v.split('-').map(Number);
  const date=new Date(Date.UTC(y,m-1,d));
  return date.getUTCFullYear()===y && date.getUTCMonth()+1===m && date.getUTCDate()===d;
}
function statusLedger(rows){
  const c={total:rows.length,available:0,unverified:0,other_missing:0};
  for(const r of rows){
    if(r.source_status==='available')c.available++;
    else if(r.source_status==='unverified')c.unverified++;
    else c.other_missing++;
  }
  return c;
}
function validateInventory(x,legacy=null){
  shape(schema,x);
  assert((x.population.split==='synthetic')===(x.producer.fixture_kind==='synthetic'),
    'Producer and population split disagree');
  assert(x.population.split==='synthetic' || x.upstream.source_hash_basis!=='synthetic',
    'Real historical source cannot masquerade as synthetic');
  const p=new Map();
  for(const v of x.periods){
    assert(!p.has(v.id) && validDate(v.start) && validDate(v.end) && v.start<=v.end,
      'Invalid/duplicate period');
    p.set(v.id,v);
  }
  const ordered=[...p.values()].sort((a,b)=>a.start.localeCompare(b.start));
  for(let i=1;i<ordered.length;i++)assert(ordered[i-1].end<ordered[i].start,
    'Overlapping periods');
  const ids=new Set(), countryYears=new Set(), seenMeetings=new Map();
  for(const r of x.observations){
    assert(!ids.has(r.id),'Duplicate inventory row identity');
    ids.add(r.id);
    const period=p.get(r.period_id);
    assert(period,'Inventory row references unknown period');
    assert(Number(r.year)>=Number(period.start.slice(0,4))&&
      Number(r.year)<=Number(period.end.slice(0,4)),'Inventory year outside declared period');
    if(r.event_date!==null)assert(validDate(r.event_date)&&
      r.event_date>=period.start&&r.event_date<=period.end&&
      Number(r.event_date.slice(0,4))===r.year,'Actual event date not in source period');
    assert(!RESERVED.has(r.event_date),'Reserved October 5–6 meeting cannot enter inventory');
    if(x.population.frame_unit==='country_year'){
      assert(r.actor_kind==='recorded_affiliation'||r.actor_kind==='synthetic',
        'Country-year unit is not a person identity');
      assert(r.actor_id,'Country-year frame requires recorded affiliation');
      const key=JSON.stringify([r.actor_id,r.year]);
      assert(!countryYears.has(key),'Duplicate country-year inventory key');
      countryYears.add(key);
    }
    if(r.source_status==='available'){
      assert(r.missing_reason===null,'Available source has a missingness reason');
      assert(r.meeting_id && r.source_family_id && HEX.test(r.source_sha256??'') &&
        HEX.test(r.text_sha256??'') && r.event_date,'Verified rows require event date and source/text provenance');
      assert(r.source_verification===(x.population.split==='synthetic'?
        'synthetic':'full_original_verified'),'Original provenance lacks independent source verification');
      const prior=seenMeetings.get(r.meeting_id), current=[r.year,r.source_sha256];
      assert(!prior||prior[0]===current[0]&&prior[1]===current[1],
        'One source meeting spans contradictory year or original bytes');
      seenMeetings.set(r.meeting_id,current);
    }else{
      assert(other.has(r.source_status),'Unexpected excluded source status');
      assert(typeof r.missing_reason==='string'&&r.missing_reason.trim(),
        'Unknown or missing source must keep an explicit reason');
      assert(r.source_verification!=='full_original_verified',
        'Unverified row cannot assert verified source evidence');
      assert(r.meeting_id===null||r.meeting_id.trim(),
        'Invented empty meeting identifier');
    }
  }
  assert(hash(x.observations)===x.inventory_sha256,'Inventory rows changed since digest');
  const counts=statusLedger(x.observations), keys=['total','available','unverified','other_missing'];
  for(const k of keys)assert(counts[k]===x.population[k==='total'?'total_in_frame':k],
    'Population denominator mismatch: '+k);
  assert(x.coverage.length===p.size,'One coverage row per declared period required');
  const cover=new Set();
  for(const c of x.coverage){
    assert(p.has(c.period_id)&&!cover.has(c.period_id),'Unknown/duplicate period coverage');
    cover.add(c.period_id);
    const want=statusLedger(x.observations.filter(r=>r.period_id===c.period_id));
    for(const k of keys)assert(c[k]===want[k],'Period coverage mismatch: '+c.period_id+': '+k);
  }
  const b=x.legacy_v1_binding;
  if(b.mode==='withheld'){
    assert(typeof b.reason==='string'&&b.reason.trim()&&b.legacy_selection_sha256===null&&
      b.legacy_eligible===null,'Withheld legacy binding needs explicit reason and no fabricated v1 identity');
    assert(legacy===null,'A supplied legacy envelope cannot bypass a withheld binding');
  }else{
    assert(b.reason===null&&HEX.test(b.legacy_selection_sha256??'')&&
      b.legacy_eligible===counts.available,'Unsupported legacy binding metadata');
    assert(legacy!==null,'A legacy binding is not validated by schema alone');
    assert(legacy.schema==='un.parallel-analysis.v1'&&
      legacy.contract_version==='1.0.0'&&legacy.publication_eligible===false,
      'Wrong or published legacy envelope');
    assert(legacy.upstream.source_schema===x.upstream.source_schema &&
      legacy.upstream.source_hash_basis===x.upstream.source_hash_basis &&
      legacy.upstream.source_sha256===x.upstream.source_sha256,
      'Legacy and sidecar refer to different original sources');
    assert(legacy.upstream.selection_sha256===b.legacy_selection_sha256,
      'Legacy selection hash mismatch');
    assert(legacy.cohort.eligible===b.legacy_eligible,
      'Legacy eligible count mismatch');
    const eligible=new Map(x.observations.filter(r=>r.source_status==='available')
      .map(r=>[r.id,r]));
    const oldEligible=legacy.observations.filter(r=>r.source_status==='available' &&
      (!r.exclusion_reasons||r.exclusion_reasons.length===0));
    assert(oldEligible.length===eligible.size,
      'Legacy v1 must consume identical supported observations, not unknown rows');
    for(const row of oldEligible)assert(eligible.get(row.id)?.text_sha256===row.text_sha256 &&
      eligible.get(row.id)?.meeting_id===row.meeting_id &&
      eligible.get(row.id)?.event_date===row.date,
      'Legacy source identity/hash/date differs from verified sidecar');
    assert(!legacy.observations.some(r=>other.has(r.source_status) &&
      r.source_status==='unverified'),'Legacy v1 cannot contain unverified');
  }
  assert(x.publication_eligible===false && x.evaluation_role==='engineering_only',
    'Inventory has no publication gate');
  return {status:'valid_inventory_contract',total:counts.total,available:counts.available,
    unverified:counts.unverified,other_missing:counts.other_missing,
    legacy_binding:b.mode};
}
function fromPanel(panel, upstream, {legacy=null, legacyWithheldReason=null,
  populationId='historical_country_session_candidate'}={}){
  assert(panel&&panel.schema==='un.longitudinal-panel.v1' &&
    (panel.split==='synthetic'||panel.split==='development'),'Unexpected original panel contract');
  assert(upstream&&typeof upstream.source_schema==='string'&&
    HEX.test(upstream.source_sha256??'')&&HEX.test(upstream.selection_sha256??''),
    'Upstream original source and selection digests required');
  const periods=panel.periods.map(p=>({id:p.id,start:p.start,end:p.end}));
  const observations=panel.observations.map(r=>({
    id:r.id,period_id:r.period,year:Number(r.year??r.date?.slice(0,4)),
    actor_kind:r.actor_kind,actor_id:r.actor_id??null,genre:r.genre,
    source_status:r.source_status,missing_reason:r.missing_reason??null,
    event_date:r.date??null,meeting_id:r.meeting_id??null,
    source_family_id:r.source_family_id??null,source_sha256:r.source_sha256??null,
    text_sha256:r.text_sha256??null,
    source_verification:r.source_status==='available'?
      (panel.split==='synthetic'?'synthetic':'full_original_verified'):'unverified',
    review_status:r.review_status??(panel.split==='synthetic'?'not_applicable':'unreviewed')
  })).sort((a,b)=>a.period_id.localeCompare(b.period_id) ||
    a.year-b.year || String(a.actor_id).localeCompare(String(b.actor_id)) || a.id.localeCompare(b.id));
  const counts=statusLedger(observations);
  const coverage=periods.map(p=>({period_id:p.id,...statusLedger(observations.filter(r=>r.period_id===p.id))}));
  const obj={
    schema:'un.parallel-source-inventory.v1',contract_version:'1.0.0',
    producer:{workstream_id:'W4',adapter_version:'1.0.0',
      fixture_kind:panel.split==='synthetic'?'synthetic':'private_development'},
    upstream:{source_schema:upstream.source_schema,source_engine:upstream.source_engine,
      source_hash_basis:upstream.source_hash_basis,source_sha256:upstream.source_sha256,
      selection_sha256:upstream.selection_sha256},
    population:{split:panel.split,population_id:populationId,
      frame_unit:panel.split==='synthetic'?'synthetic':'country_year',
      selection_policy:'Original source-backed candidate frame; unverified not absent/zero',
      total_in_frame:counts.total,available:counts.available,
      unverified:counts.unverified,other_missing:counts.other_missing},
    periods,observations,coverage,inventory_sha256:hash(observations),
    legacy_v1_binding:{mode:'withheld',
      reason:legacyWithheldReason??'No validated compatible legacy v1 projection supplied',
      legacy_selection_sha256:null,legacy_eligible:null},
    limitations:['Source inventory and source verification are distinct.',
      'Unverified country-years are not absent speech or zero vector.',
      'Meeting/year dependence and source sample selection prevent automatic statistical inference.'],
    publication_eligible:false,evaluation_role:'engineering_only'
  };
  validateInventory(obj);
  if(legacy!==null)bindLegacyV1(obj,legacy);
  return obj;
}
function bindLegacyV1(sidecar,legacy){
  assert(sidecar.legacy_v1_binding.mode==='withheld','Legacy binding already asserted');
  const backup=sidecar.legacy_v1_binding;
  sidecar.legacy_v1_binding={mode:'verified_subset_projection',reason:null,
    legacy_selection_sha256:legacy.upstream?.selection_sha256??null,
    legacy_eligible:sidecar.population.available};
  try{validateInventory(sidecar,legacy);}catch(e){
    sidecar.legacy_v1_binding=backup;throw e;
  }
  return sidecar;
}
module.exports={fromPanel,bindLegacyV1,validateInventory,hash,statusLedger};
