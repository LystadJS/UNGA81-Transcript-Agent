'use strict';
// Node research-side source-bound replay. No DOM, network, file lookup or refit.
// Deliberately independent of the Python producer arithmetic.
const crypto = require('node:crypto');
const SCHEMA = 'un.us-relative-trajectories.v1';
const HASH_BASIS = 'sha256/usref-wire-v1';
const TOL = 1e-10;
const PERMISSIONS = {evaluation_role:'engineering_only', publication_eligible:false,
  real_data_eligible:false, holdout_access:false, approval_receipts:[]};
function need(test, message) { if (!test) throw new Error(message); }
function obj(x) { return x !== null && typeof x === 'object' && !Array.isArray(x); }
function keys(x, wanted) { need(obj(x) && Object.keys(x).sort().join('|') === [...wanted].sort().join('|'), 'Unexpected fields'); }
function wire(v) {
  if (v === null) return Buffer.from('n');
  if (typeof v === 'boolean') return Buffer.from(v ? 't' : 'f');
  if (typeof v === 'number') {
    need(Number.isFinite(v), 'Nonfinite number');
    const b = Buffer.alloc(8); b.writeDoubleBE(v === 0 ? 0 : v);
    return Buffer.from('d' + b.toString('hex'));
  }
  if (typeof v === 'string') {
    const b = Buffer.from(v, 'utf8'); return Buffer.concat([Buffer.from('s' + b.length + ':'), b]);
  }
  if (Array.isArray(v)) return Buffer.concat([Buffer.from('['), ...v.map(wire), Buffer.from(']')]);
  need(obj(v) && Object.keys(v).every(k => /^[\x00-\x7f]*$/.test(k)), 'Invalid hash object');
  return Buffer.concat([Buffer.from('{'), ...Object.keys(v).sort().flatMap(k => [wire(k),wire(v[k])]), Buffer.from('}')]);
}
const digest = v => crypto.createHash('sha256').update(wire(v)).digest('hex');
const withoutSha = v => Object.fromEntries(Object.entries(v).filter(([k]) => k !== 'sha256'));
function equal(actual, expected, where='model') {
  if (typeof expected === 'number') {
    need(typeof actual === 'number' && Number.isFinite(actual) &&
      Math.abs(actual - expected) <= TOL * Math.max(1,Math.abs(expected)), where + ': numerical mismatch');
  } else if (Array.isArray(expected)) {
    need(Array.isArray(actual) && actual.length === expected.length, where + ': array mismatch');
    expected.forEach((v,i) => equal(actual[i],v,where));
  } else if (obj(expected)) {
    keys(actual,Object.keys(expected)); Object.keys(expected).forEach(k => equal(actual[k],expected[k],where+'.'+k));
  } else need(actual === expected, where + ': value mismatch');
}
function vector(a, n) { need(Array.isArray(a) && a.length === n && a.every(x => typeof x === 'number' && Number.isFinite(x) && Math.abs(x)<=1e100), 'Invalid vector'); }
const sub = (a,b) => a.map((v,i) => v-b[i]);
function sum(values) { // Neumaier compensated sum, independent of math.fsum.
  let s=0,c=0; for (const x of values) {const t=s+x;c+=Math.abs(s)>=Math.abs(x)?(s-t)+x:(x-t)+s;s=t;}return s+c;
}
const dot = (a,b) => sum(a.map((v,i)=>v*b[i]));
function pointMetrics(c,u) {
  need(Array.isArray(c) && c.length>=2 && c.length<=1024,'Invalid dimension');
  vector(c,c.length); vector(u,c.length); const r=sub(c,u);
  return {relative_vector:r,distance:Math.hypot(...r)};
}
function transitionMetrics(c0,c1,u0,u1) {
  const a=pointMetrics(c0,u0), b=pointMetrics(c1,u1); need(c0.length===c1.length,'Dimension changed');
  const dc=sub(c1,c0),du=sub(u1,u0),dr=sub(dc,du),total=a.relative_vector.map((v,i)=>v+b.relative_vector[i]);
  const qc=dot(total,dc),qu=-dot(total,du),den=a.distance+b.distance;
  const direction=den>0?total.map(x=>x/den):null;
  const gc=den>0?dot(direction,dc):null,gu=den>0?-dot(direction,du):null;
  return {gap_change:b.distance-a.distance,country_change:dc,us_change:du,relative_change:dr,
    country_displacement:Math.hypot(...dc),us_displacement:Math.hypot(...du),relative_displacement:Math.hypot(...dr),
    squared_gap_country_contribution:qc,squared_gap_us_contribution:qu,gap_country_contribution:gc,gap_us_contribution:gu,
    decomposition_status:den>0?'ready':'undefined_zero_gaps',reconciliation_residual:den>0?gc+gu-(b.distance-a.distance):null,
    interpretation:'algebraic_not_causal'};
}
function displayState(d,m) {
  if (d===null) return {state:'withheld',reason:'display_transform_missing'};
  try {
    keys(d,['method','basis','center','metric_fingerprint','fit_id']);
    need(d.method==='fixed_orthonormal_linear'&&d.metric_fingerprint===m.fingerprint,'Unusable display');
    need(typeof d.fit_id==='string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}$/.test(d.fit_id),'Invalid fit');
    vector(d.center,m.dimension); need(Array.isArray(d.basis)&&d.basis.length===m.dimension,'Wrong basis');
    d.basis.forEach(row=>vector(row,2));const cols=[0,1].map(j=>d.basis.map(row=>row[j]));
    for(let i=0;i<2;i++) for(let j=0;j<2;j++) need(Math.abs(dot(cols[i],cols[j])-(i===j?1:0))<=TOL,'Nonorthogonal basis');
    return {state:'ready',reason:null,...structuredClone(d),sha256:digest(d)};
  } catch {return {state:'withheld',reason:'display_transform_invalid'};}
}
function projected(c,u,d,gap) {
  if(d.state!=='ready')return {state:'withheld',reason:d.reason,country_xy:null,us_xy:null,relative_xy:null,visible_squared_gap_fraction:null,fraction_reason:d.reason};
  const cols=[0,1].map(j=>d.basis.map(r=>r[j])),xy=cols.map(col=>dot(sub(c,u),col));
  return {state:'ready',reason:null,country_xy:cols.map(col=>dot(sub(c,d.center),col)),us_xy:cols.map(col=>dot(sub(u,d.center),col)),relative_xy:xy,
    visible_squared_gap_fraction:gap>0?(Math.hypot(...xy)/gap)**2:null,fraction_reason:gap>0?null:'undefined_zero_gap'};
}
function eligibility(r,s) {
  if(r.source_status!=='available')return r.source_status;
  if(r.capacity!=='national')return 'non_national_capacity';
  if(r.attribution_status!=='synthetic_verified'||r.country_iso3===null)return 'attribution_unverified';
  if(!s.genres.includes(r.genre)||['language','source_type','topic_id'].some(k=>r[k]!==s[k]))return 'scope_excluded';
  return null;
}
function profile(c,p,rows,source) {
  const s=source.scope,m=source.metric_space,candidates=rows.filter(r=>r.country_iso3===c&&r.period===p);
  const selected=candidates.filter(r=>eligibility(r,s)===null),excluded=candidates.filter(r=>eligibility(r,s)!==null).map(r=>({observation_id:r.id,reason:eligibility(r,s)}));
  let state='ready',reason=null;
  if(!candidates.length){state='empty';reason='country_missing';}
  else if(!selected.length){const rs=new Set(excluded.map(r=>r.reason));state=rs.has('failed')||rs.has('inventory_failed')?'failed':'withheld';
    reason=rs.has('attribution_unverified')?'attribution_unverified':rs.has('unverified')?'source_unverified':state==='failed'?'source_failed':'no_eligible_country_sources';}
  else if(new Set(selected.map(r=>r.genre)).size!==s.genres.length){state='withheld';reason='scope_incompatible';}
  const contributions=[];let v=null;
  if(state==='ready') {
    for(const g of [...s.genres].sort()) {
      const meetings=[...new Set(selected.filter(r=>r.genre===g).map(r=>r.meeting_id))].sort();
      for(const meeting of meetings){const group=selected.filter(r=>r.genre===g&&r.meeting_id===meeting);
        const w=1/s.genres.length/meetings.length/group.length;
        for(const r of group)contributions.push({observation_id:r.id,weight:w});}
    }
    const lookup=new Map(selected.map(r=>[r.id,r]));
    v=Array.from({length:m.dimension},(_,j)=>sum(contributions.map(x=>x.weight*lookup.get(x.observation_id).vector[j])));
  }
  return {id:c+'/'+p,country_iso3:c,period:p,scope_sha256:digest(s),metric_fingerprint:m.fingerprint,excluded,
    coverage:{unit:'source_observation',inventory:candidates.length,included:selected.length,excluded:excluded.length},
    state,reason,vector:v,contributions};
}
function counts(values) {const out={};for(const v of values)out[v]=(out[v]||0)+1;return out;}
function validateSyntheticSource(source,receipt) {
  const contract=require('./schema_contract.cjs');contract.validate(source,{source:true});
  keys(source,['schema','split','identity','metric_space','display_space','scope','periods','observations']);
  need(source.schema==='un.us-relative-source-panel.v1'&&source.split==='synthetic','Only synthetic sources');
  equal(receipt,{kind:'synthetic_consistency_only',hash_basis:HASH_BASIS,panel_sha256:digest(source)});
  const s=source.scope,m=source.metric_space,periods=source.periods;
  need(s.support_mode==='common'&&s.baseline_mode==='contemporaneous'&&s.baseline_iso3==='USA','Wrong comparison estimand');
  need(s.weight_policy==='w4_equal_meeting_within_genre_equal_genre_v1'&&s.source_unit_policy==='one_vector_per_original_parent','Wrong weights or source partition');
  need(m.fingerprint===digest(Object.fromEntries(Object.entries(m).filter(([k])=>k!=='fingerprint'))),'Representation mismatch');
  need(Number.isInteger(m.dimension)&&m.dimension>=2&&m.dimension<=1024&&m.feature_order.length===m.dimension,'Invalid dimension or feature order');
  need(Array.isArray(s.countries)&&s.countries.includes('USA')&&new Set(s.countries).size===s.countries.length,'Invalid frame');
  need(Array.isArray(periods)&&periods.length>=2&&periods.length*s.countries.length<=20000,'Invalid periods');
  const validDate=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(x).toISOString().slice(0,10)===x;
  let last=null;const pmap=new Map();
  for(const p of periods){keys(p,['id','start','end']);need(!pmap.has(p.id)&&validDate(p.start)&&validDate(p.end)&&p.start<=p.end&&(last===null||last<p.start),'Period order');pmap.set(p.id,p);last=p.end;}
  const rows=[...source.observations].sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
  need(rows.length<=20000,'Row resource bound');const ids=new Set(),spans=new Map(),parents=new Map(),meetings=new Map(),usedParents=new Set();
  for(const r of rows){
    need(typeof r.id==='string'&&(r.id.startsWith('syn-')||r.id.startsWith('fictional-'))&&!ids.has(r.id)&&r.source_hash_basis==='synthetic','Unsafe or repeated source');ids.add(r.id);
    need(pmap.has(r.period),'Unknown period');
    need(r.country_iso3===null||s.countries.includes(r.country_iso3),'Country outside frame');
    need((r.start===null&&r.end===null)||(Number.isSafeInteger(r.start)&&Number.isSafeInteger(r.end)&&r.start>=0&&r.end>r.start),'Invalid original offsets');
    if(r.parent_id!==null)need(r.parent_text_sha256!==null,'Missing parent hash');
    if(r.date!==null){need(validDate(r.date)&&r.date>=pmap.get(r.period).start&&r.date<=pmap.get(r.period).end&&!['2026-10-05','2026-10-06'].includes(r.date),'Invalid source date');}
    if(r.source_status==='available'){
      vector(r.vector,m.dimension);need(r.representation_fingerprint===m.fingerprint&&r.date!==null&&r.missing_reason===null,'Source representation/date');
      need(['meeting_id','source_family_id','source_sha256','text_sha256','parent_id','parent_text_sha256','source_pointer','start','end'].every(k=>r[k]!==null),'Observed lineage incomplete');
      if(r.attribution_status==='synthetic_verified')need(r.actor_id!==null&&r.review_receipt!==null,'Unreviewed actor attribution');
      const key=r.source_sha256+'/'+r.parent_id;need(!usedParents.has(key),'Repeated parent');usedParents.add(key);need(Number.isSafeInteger(r.start)&&Number.isSafeInteger(r.end)&&r.start>=0&&r.end>r.start,'Invalid offsets');
      for(const ab of spans.get(key)||[])need(r.end<=ab[0]||r.start>=ab[1],'Duplicate or overlapping source');
      spans.set(key,[...(spans.get(key)||[]),[r.start,r.end]]);
    } else need(r.vector===null&&r.missing_reason!==null,'Missing source has values');
    if(r.parent_id!==null){const key=r.source_sha256+'/'+r.parent_id;need(!parents.has(key)||parents.get(key)===r.parent_text_sha256,'Parent conflict');parents.set(key,r.parent_text_sha256);}
    if(r.meeting_id!==null&&r.source_sha256!==null){const signature=digest([r.period,r.date,r.source_family_id,r.source_sha256]);need(!meetings.has(r.meeting_id)||meetings.get(r.meeting_id)===signature,'Meeting conflict');meetings.set(r.meeting_id,signature);}
  }
  return true;
}
function validateFigureModel(model,source,receipt) {
  validateSyntheticSource(source,receipt);require('./schema_contract.cjs').validate(model);
  need(obj(model)&&model.sha256===digest(withoutSha(model)),'Result digest mismatch');
  const s=source.scope,m=source.metric_space,periods=source.periods;
  const rows=[...source.observations].sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
  const display=displayState(source.display_space,m),expectedProfiles=[];let k=0;
  for(const c of s.countries)for(const p of periods){const e=profile(c,p.id,rows,source),a=model.profiles[k++];
    need(a&&a.sha256===digest(withoutSha(a)),'Profile digest mismatch');equal(withoutSha(a),e,'profile');expectedProfiles.push({...e,sha256:a.sha256});}
  need(model.profiles.length===expectedProfiles.length,'Extra profiles');
  const lookup=new Map(expectedProfiles.map(p=>[p.id,p])),comparisons=[];
  for(const c of s.countries)for(const p of periods){const cp=lookup.get(c+'/'+p.id),up=lookup.get('USA/'+p.id),ready=cp.state===up.state&&cp.state==='ready';
    const e={id:c+'/'+p.id,country_iso3:c,period:p.id,country_profile_sha256:cp.sha256,us_profile_sha256:up.sha256,state:ready?'ready':'withheld',
      reason:ready?null:up.state!=='ready'?'baseline_missing':cp.reason,distance:null,relative_vector:null,display:null};
    if(ready){Object.assign(e,pointMetrics(cp.vector,up.vector));e.display=projected(cp.vector,up.vector,display,e.distance);}comparisons.push(e);}
  const cm=new Map(comparisons.map(c=>[c.id,c])),transitions=[];
  for(const c of s.countries)for(let i=1;i<periods.length;i++){const a=periods[i-1].id,b=periods[i].id,ready=cm.get(c+'/'+a).state==='ready'&&cm.get(c+'/'+b).state==='ready';
    transitions.push({country_iso3:c,before:a,after:b,before_comparison_id:c+'/'+a,after_comparison_id:c+'/'+b,state:ready?'ready':'withheld',reason:ready?null:'endpoint_unavailable',
      metrics:ready?transitionMetrics(lookup.get(c+'/'+a).vector,lookup.get(c+'/'+b).vector,lookup.get('USA/'+a).vector,lookup.get('USA/'+b).vector):null});}
  const exclusions=rows.map(r=>eligibility(r,s)),sourceHash=digest(source),metricHash=digest(Object.fromEntries(Object.entries(source).filter(([k])=>k!=='display_space')));
  const expected={schema:SCHEMA,version:'0.1.0',split:'synthetic',hash_basis:HASH_BASIS,
    identity:{...source.identity,source_panel_sha256:sourceHash,metric_input_sha256:metricHash,comparison_set_id:digest({source:metricHash,scope:s}),consistency_receipt:receipt},
    metric_space:m,display_space:display,baseline:{iso3:'USA',mode:'contemporaneous',attribution_rule:'verified_national_capacity',profile_hashes:Object.fromEntries(periods.map(p=>[p.id,lookup.get('USA/'+p.id).sha256]))},
    scope:s,periods,profiles:expectedProfiles,comparisons,transitions,evidence:rows.map(r=>Object.fromEntries(Object.entries(r).filter(([key])=>key!=='vector'))),
    coverage:{unit:'source_observation',inventory:rows.length,included:exclusions.filter(x=>x===null).length,excluded:exclusions.filter(x=>x!==null).length,
      source_status_counts:counts(rows.map(r=>r.source_status)),exclusion_reasons:counts(exclusions.filter(x=>x!==null))},
    uncertainty:{state:'withheld',reason:'uncertainty_unavailable',interval:null},sensitivity:{state:'withheld',reason:'not_executed',attempts:[]},permissions:PERMISSIONS,sha256:model.sha256};
  // Source metadata, integer offsets and original transform bytes are exact.
  // Floating tolerance applies only to independently recomputed arithmetic.
  for(const field of ['identity','metric_space','display_space','scope','periods','evidence','baseline','coverage','permissions','uncertainty','sensitivity'])
    need(digest(model[field])===digest(expected[field]),'Changed source-bound metadata');
  equal(model,expected); return true;
}
function importReadModel(model,source,receipt) {
  try {validateFigureModel(model,source,receipt);return {state:'ready',model:structuredClone(model)};}
  catch {return {state:'failed',reason:'invalid_source_bound_model',model:null};}
}
module.exports={digest,pointMetrics,transitionMetrics,validateSyntheticSource,validateFigureModel,importReadModel};
if(require.main===module){
  let input='';process.stdin.setEncoding('utf8');process.stdin.on('data',x=>{input+=x;if(input.length>32*1024*1024){process.stderr.write('Input resource bound\n');process.exit(2);}});
  process.stdin.on('end',()=>{try {const x=JSON.parse(input);let out;
    if(process.argv.includes('--arithmetic'))out=x.cases.map(c=>({case:c.case,point0:pointMetrics(c.c0,c.u0),point1:pointMetrics(c.c1,c.u1),transition:transitionMetrics(c.c0,c.c1,c.u0,c.u1)}));
    else {validateFigureModel(x.model,x.source,x.receipt);out={validated:true};}
    process.stdout.write(JSON.stringify(out)+'\n');
  }catch{process.stderr.write('Rejected synthetic input or read model\n');process.exitCode=1;}});
}
