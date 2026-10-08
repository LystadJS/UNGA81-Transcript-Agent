'use strict';
const crypto=require('node:crypto');
const C=require('../../site/cluster-core.js');
const {combinations2}=require('./metrics.cjs');
const HEX=/^[a-f0-9]{64}$/;
const SOURCE_SCHEMAS=new Set(['un.browser.corpus.v1','un.passage-corpus.v1','un.passage-frame.v1','un.review.v1','un.source-validation.synthetic.v1']);
const RESERVED=new Set(['2026-10-05','2026-10-06']);
function assert(ok,msg){if(!ok)throw Error(msg);}
function digest(value){return crypto.createHash('sha256').update(typeof value==='string'?value:JSON.stringify(value)).digest('hex');}
function hasHash(value){return typeof value==='string'&&HEX.test(value);}
function validateFrame(frame){
  assert(frame&&frame.schema==='un.source-validation.frame.v1','Unknown validation input schema.');
  assert(['synthetic','development'].includes(frame.split),'Only synthetic or authorized development inputs are supported.');
  assert(SOURCE_SCHEMAS.has(frame.source_schema),'Unsupported source schema; provide a source-bound adapter.');
  assert(hasHash(frame.source_sha256),'Original upstream source SHA-256 required.');
  assert(['utf8_corpus_export','raw_response_bytes','utf8_response_text','canonical_source_text','source_text_file_bytes','synthetic'].includes(frame.source_hash_basis),'Exact supported upstream source hash basis required.');
  assert(frame.split!=='development'||frame.source_hash_basis!=='synthetic','Development cannot masquerade as synthetic source hashes.');
  assert(typeof frame.source_engine==='string'&&frame.source_engine.length>0,'Source engine identity required.');
  assert(Array.isArray(frame.observations)&&frame.observations.length>0&&frame.observations.length<=600,'Frame requires 1–600 rows; no implicit sampling.');
  const seen=new Set(), eligible=[], excluded=[], rows=[];
  for(const o of frame.observations){
    assert(o&&typeof o.id==='string'&&o.id.length>0&&!seen.has(o.id),'Missing or duplicate observation ID.');
    seen.add(o.id);
    assert(o.split===frame.split,'Mixed selection splits are prohibited.');
    assert(!RESERVED.has(o.date),'Reserved October 5–6 transcript metadata cannot enter development fitting.');
    if(frame.split==='development')assert(/^\d{4}-\d{2}-\d{2}$/.test(o.date)&&o.date<='2026-10-04','Only verified pre-holdout development dates through October 4 are allowed.');
    assert(o.source_status==='available'||o.source_status==='unavailable','Unknown source availability.');
    const absent=o.source_status!=='available'||(Array.isArray(o.exclusion_reasons)&&o.exclusion_reasons.length>0);
    assert(o.text_sha256===null||hasHash(o.text_sha256),'Invalid text digest.');
    assert(absent||hasHash(o.text_sha256),'Available observations require existing text hashes.');
    assert(o.parent_id==null||hasHash(o.parent_text_sha256),'Parent ID requires a verified parent hash.');
    assert(o.start==null&&o.end==null||Number.isSafeInteger(o.start)&&Number.isSafeInteger(o.end)&&o.start>=0&&o.start<o.end,'Invalid zero-based, end-exclusive source span.');
    assert((o.start==null)===(o.end==null),'Offsets must be both present or both null.');
    assert(o.source_url==null||/^https:\/\//.test(o.source_url),'Only HTTPS original source pointers are accepted.');
    assert(o.source_status==='available'||typeof o.missing_reason==='string'&&o.missing_reason.length>0,'Missing source must have a reason.');
    assert(o.speech_id==null||o.review_status==='confirmed','Unverified speech identities cannot be promoted.');
    if(o.text!==undefined)assert(typeof o.text==='string'&&digest(o.text)===o.text_sha256,'Provided text does not match its canonical UTF-8 text hash.');
    if(!absent)assert(typeof o.meeting_id==='string'&&o.meeting_id.length>0 || frame.split==='synthetic','Development observations need verified meeting IDs.');
    rows.push(o);
    (absent?excluded:eligible).push(o);
  }
  assert(eligible.length>=1,'No eligible observations; record a skipped comparison outside the fitting path.');
  const identities=eligible.map(r=>[r.id,r.text_sha256]);
  const selection_sha256=digest(identities);
  if(frame.selection_sha256!==undefined&&frame.selection_sha256!==null)assert(selection_sha256===frame.selection_sha256,'Population ID/text hashes changed from pinned selection.');
  const population_hash=digest([frame.source_schema,frame.source_hash_basis,frame.source_sha256,selection_sha256]);
  return {rows,eligible,excluded,selection_sha256,population_hash,inventory_meetings:frame.inventory_meetings??new Set(rows.map(x=>x.meeting_id).filter(Boolean)).size};
}
function alignScores(cohort,saved){
  assert(saved&&typeof saved.id==='string'&&typeof saved.version==='string'&&saved.id&&saved.version,'Representation identity/version required.');
  assert(saved.kind==='pinned-minilm'||saved.kind==='synthetic-saved','Saved vectors must be a pinned MiniLM cache or explicitly synthetic.');
  assert(hasHash(saved.identity_sha256),'Saved transformation or model-lock digest required.');
  assert(Array.isArray(saved.rows)&&saved.rows.length===cohort.eligible.length,'Saved representation must contain exactly the eligible population.');
  const positions=new Map();
  for(const r of saved.rows){
    assert(r&&typeof r.id==='string'&&hasHash(r.text_sha256)&&!positions.has(r.id),'Duplicate or invalid saved vector identity.');
    assert(Array.isArray(r.vector)&&r.vector.length>0&&r.vector.every(x=>typeof x==='number'&&Number.isFinite(x)),'Invalid saved vector.');
    positions.set(r.id,r);
  }
  const dims=saved.rows[0].vector.length;
  const scores=cohort.eligible.map(o=>{
    const r=positions.get(o.id);
    assert(r&&r.text_sha256===o.text_sha256&&r.vector.length===dims,'Saved representation population/hash/shape mismatch.');
    return r.vector.slice();
  });
  assert(scores.length>1,'Representation needs at least two eligible observations.');
  return {id:saved.id,version:saved.version,identity_sha256:saved.identity_sha256,kind:saved.kind,values:scores};
}
function unionGroups(rows,unit){
  assert(['meeting','affiliation'].includes(unit),'Grouping must use whole meeting or recorded affiliation.');
  const n=rows.length,parent=Array.from({length:n},(_,i)=>i);
  const find=i=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
  const link=(i,j)=>{const a=find(i),b=find(j);if(a!==b)parent[b]=a;};
  const keys=new Map();
  let unknownAffiliations=0;
  for(let i=0;i<n;i++){
    const r=rows[i];let affiliation=String(r.affiliation??r.country??'').trim().normalize('NFKC').toLowerCase();
    if(!affiliation||['unknown','unidentified','unmapped'].includes(affiliation)){affiliation='unidentified affiliation';unknownAffiliations++;}
    if(unit==='meeting')assert(typeof r.meeting_id==='string'&&r.meeting_id,'Whole-meeting resampling requires verified meeting IDs.');
    const segments=[...(r.parent_id?['parent:'+r.parent_id]:[]),...(r.source_family_id?['family:'+r.source_family_id]:[])];
    if(!segments.length&&r.meeting_id)segments.push('meeting:'+r.meeting_id);
    assert(segments.length,'No verified source-segment group; grouped resampling withheld.');
    const labels=unit==='meeting'?['meeting:'+r.meeting_id]:['affiliation:'+affiliation,...segments];
    // Bipartite transitive closure ensures the same source segment is never divided across samples.
    for(const key of labels){if(keys.has(key))link(i,keys.get(key));else keys.set(key,i);}
  }
  const groups=new Map();
  rows.forEach((r,i)=>{const k=find(i);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(i);});
  const arr=[...groups.values()].sort((a,b)=>rows[a[0]].id.localeCompare(rows[b[0]].id));
  const count=new Set(arr.flatMap(g=>g)).size;
  assert(count===rows.length,'Resampling would duplicate or lose a passage.');
  return {groups:arr,unit,unknown_affiliation_observations:unknownAffiliations};
}
function schedule(rows,unit,replicates=20,fraction=0.8,seed=31415){
  assert(Number.isInteger(replicates)&&replicates>=2&&replicates<=100,'Replicates must be 2–100.');
  assert(fraction>=0.5&&fraction<=0.9,'Retain 50–90% of independent groups.');
  assert(Number.isInteger(seed)&&seed>=0&&seed<=4294967295,'Invalid schedule seed.');
  let grouped;
  try{grouped=unionGroups(rows,unit);}catch(error){return {status:'skipped',reason:error.message,unit,attempted:0,groups:0,samples:[]};}
  const G=grouped.groups.length;
  if(G<3)return {status:'skipped',reason:'Insufficient independent source groups (at least three required).',unit,attempted:0,groups:G,samples:[],unknown_affiliation_observations:grouped.unknown_affiliation_observations};
  const take=Math.min(G-1,Math.max(1,Math.ceil(fraction*G))),random=C.rng(seed);
  const samples=[];
  for(let attempt=1;attempt<=replicates;attempt++){
    const selected=C.rng ? require('../../site/cluster-stability.js').sampleGroups(G,take,random) : [];
    const indices=selected.flatMap(j=>grouped.groups[j]).sort((a,b)=>a-b);
    samples.push({attempt,group_indices:selected,indices,selected_count:indices.length,excluded_count:rows.length-indices.length});
  }
  return {status:'scheduled',unit,groups:G,selected_groups:take,attempted:replicates,seed,fraction,unknown_affiliation_observations:grouped.unknown_affiliation_observations,unique_group_samples:new Set(samples.map(x=>x.group_indices.join(','))).size,schedule_sha256:digest(samples.map(x=>x.group_indices)),samples};
}
function auditSources(rows,labels=null) {
  const by=(key)=>{const m=new Map();rows.forEach(r=>{const s=key(r);m.set(s,(m.get(s)||0)+1);});return [...m].map(([key,count])=>({key,count})).sort((a,b)=>b.count-a.count||String(a.key).localeCompare(String(b.key)));};
  const meetings=by(r=>r.meeting_id||'(unverified)'),duplicateHashes=by(r=>r.text_sha256).filter(x=>x.count>1);
  const role=by(r=>r.role||'(not recorded)'),genre=by(r=>r.genre||'(not recorded)');
  const affiliation=by(r=>r.affiliation||r.country||'(missing)');
  const strata=labels?rows.map((r,i)=>({genre:r.genre||'(not recorded)',role:r.role||'(not recorded)',cluster:labels[i],meeting_id:r.meeting_id})):null;
  const dependence=strata?['genre','role'].map(variable=>{
    const map=new Map();strata.forEach(r=>{const key=JSON.stringify([r[variable],r.cluster]);map.set(key,(map.get(key)||0)+1);});
    return {variable,counts:[...map].map(([key,count])=>({stratum:JSON.parse(key)[0],cluster:JSON.parse(key)[1],count}))};
  }):[];
  const n=rows.length;
  return {observations:n,meetings:meetings.length,largest_meeting_count:meetings[0]?.count??0,largest_meeting_share:n?meetings[0].count/n:null,
    observed_meeting_pair_share:n>1?meetings.reduce((s,m)=>s+combinations2(m.count),0)/combinations2(n):null,
    duplicate_text_groups:duplicateHashes.length,duplicate_observations:duplicateHashes.reduce((s,v)=>s+v.count,0),
    recorded_affiliations:affiliation.length,missing_affiliation_count:rows.filter(r=>!r.affiliation&&!r.country).length,
    role_marginals:role,genre_marginals:genre,cluster_cross_tabs:dependence,
    warnings:[...(duplicateHashes.length?['Repeated text hashes: duplicates can dominate cluster sizes.']:[]),
      ...(n&&meetings[0].count/n>0.5?['One meeting supplies more than half of eligible passages.']:[]),
      ...(rows.some(r=>!r.affiliation&&!r.country)?['Missing speaker affiliation: do not infer a country.']:[])]};
}
module.exports={digest,validateFrame,alignScores,unionGroups,schedule,auditSources};
