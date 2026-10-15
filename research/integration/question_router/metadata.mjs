/** U2 metadata boundary. The original inventory validator and hash basis stay authoritative. */
import inventoryContract from '../../../docs/parallel-work/source-inventory-v1.cjs';
import {canonical, parseStrict, digest, validateCapability, validateQuery} from '../product_contracts/contracts.mjs';
export const C0_HEAD = '884097997f89b0040e4418480378f077e3b65434';
export const U1_HEAD = 'afb92e82881dc11003170899aef9958682d61abe';
export const MAX_HOPS = 16;
export const LIVE_MAX_DAYS = 31;
export const INTENTS = Object.freeze(['country','topic','meeting','comparison','trends']);
const RESERVED = ['2026-10-05','2026-10-06'];
export class RouterError extends Error { constructor(code) { super(code); this.name = 'RouterError'; this.code = code; } }
export const ensure = (ok, code) => { if (!ok) throw new RouterError(code); };
export const equal = (a,b) => canonical(a) === canonical(b);
/** Validate data descriptors before cloning; preserve insertion order for the upstream row hash. */
export function snapshot(value) {
  if (typeof value === 'string') return parseStrict(value);
  canonical(value); // Rejects getters, hooks, non-JSON objects and sparse arrays synchronously.
  const result = JSON.stringify(value);
  return parseStrict(result);
}
function closed(value, fields, code) { ensure(value && !Array.isArray(value) && typeof value === 'object' && Object.keys(value).sort().join(',') === [...fields].sort().join(','), code); }
function token(value) { ensure(typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9._:/-]{0,159}$/.test(value), 'metadata_identifier'); }
function label(value) { ensure(typeof value === 'string' && value.trim().length > 0 && value.length <= 160 && !/[\u0000-\u001f<>]/u.test(value), 'metadata_label'); }
function list(value, max = 256) { ensure(Array.isArray(value) && value.length <= max, 'metadata_array'); }
function ids(items, key = 'id') { ensure(new Set(items.map(x=>x[key])).size === items.length, 'metadata_duplicate'); }
export function validDate(value) { return typeof value === 'string' && /^\d{4}-\d\d-\d\d$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0,10) === value; }
export function checkPeriod(p) { closed(p,['start','end'],'period_fields'); ensure(validDate(p.start) && validDate(p.end) && p.start <= p.end, 'date_range'); }
export function inclusiveDays(p) { checkPeriod(p); return (Date.parse(p.end)-Date.parse(p.start))/86400000+1; }
/** UTC instants are converted to New York calendar dates, never the runner's local zone. */
export function newYorkDate(instant) {
  ensure(typeof instant === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(instant), 'instant');
  const date = new Date(instant);
  ensure(Number.isFinite(date.valueOf()) && date.toISOString() === instant.replace(/(?<!\.\d{3})Z$/,'.000Z'), 'instant');
  const p = new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date);
  const v = key=>p.find(x=>x.type===key).value;
  return `${v('year')}-${v('month')}-${v('day')}`;
}
const normalize = s => s.normalize('NFKC').trim().replace(/\s+/gu,' ').toLowerCase();
function aliasMap(items) {
  const aliases = new Map();
  for (const item of items) for (const value of [item.id,item.name,...item.aliases]) {
    const key = normalize(value);
    ensure(!aliases.has(key) || aliases.get(key) === item.id, 'ambiguous_alias_registry');
    aliases.set(key,item.id);
  }
  return aliases;
}
function lookup(items, value) { label(value); const id=aliasMap(items).get(normalize(value)); ensure(id !== undefined,'unknown_alias'); return id; }
export function countryId(catalog,value) { return lookup(catalog.countries,value); }
export function topicId(catalog,value) { return lookup(catalog.topics,value); }
export function findMeetings(catalog, input) {
  const search=snapshot(input); closed(search,['name','date','forum'],'meeting_search_fields');
  label(search.name); if(search.date!==null) ensure(validDate(search.date),'date_range'); if(search.forum!==null) token(search.forum);
  return snapshot(catalog.meetings.filter(m=>normalize(m.name).includes(normalize(search.name)) && (search.date===null || m.date===search.date) && (search.forum===null || m.forum===search.forum))
    .sort((a,b)=>(a.date??'').localeCompare(b.date??'') || a.forum.localeCompare(b.forum) || a.id.localeCompare(b.id)));
}
export function meetingId(catalog,input) { const matches=findMeetings(catalog,input); ensure(matches.length===1,matches.length?'ambiguous_meeting':'unknown_meeting'); return matches[0].id; }
export async function validateMetadata(value, expectedSha256) {
  const m=snapshot(value); // Snapshot before the first await; the caller cannot replace metadata mid-hash.
  closed(m,['schema','fixture_kind','catalog','inventory','bindings','policies'],'metadata_fields');
  ensure(m.schema==='un.question-router-metadata.v1' && m.fixture_kind==='synthetic','synthetic_only');
  ensure(typeof expectedSha256==='string' && /^[a-f0-9]{64}$/.test(expectedSha256) && await digest(m)===expectedSha256,'metadata_commitment');
  const c=m.catalog;
  closed(c,['schema','timezone','collection_kind','countries','topics','meetings','period'],'catalog_fields');
  ensure(c.schema==='u2.synthetic-catalog.v1' && c.timezone==='America/New_York','catalog_version');
  ensure(['synthetic_live','synthetic_saved','synthetic_historical'].includes(c.collection_kind),'collection_kind');
  checkPeriod(c.period);
  for(const [name,items] of [['country',c.countries],['topic',c.topics]]) {
    list(items); ids(items); ensure(items.length>0,'empty_registry');
    for(const item of items) {
      closed(item,['id','name','aliases'],'entity_fields'); token(item.id);label(item.name);list(item.aliases,32);item.aliases.forEach(label);
      if(name==='country') ensure(/^[A-Z]{3}$/.test(item.id),'country_id');
    }
    aliasMap(items);
  }
  ensure(c.countries.some(x=>x.id==='USA'),'baseline_registry');
  list(c.meetings,1000);ids(c.meetings);
  for(const item of c.meetings) {
    closed(item,['id','name','date','forum','period_id','protected'],'meeting_fields');
    token(item.id);label(item.name);token(item.forum);token(item.period_id);
    ensure(item.date===null || validDate(item.date),'meeting_date');ensure(typeof item.protected==='boolean','protected_flag');
  }
  const inv=m.inventory;
  ensure(inv?.population?.split==='synthetic' && inv?.producer?.fixture_kind==='synthetic' && inv?.upstream?.source_hash_basis==='synthetic','synthetic_inventory_only');
  // Do not canonicalize row key order before this original validator's JSON.stringify hash.
  inventoryContract.validateInventory(inv);
  ensure(inv.population.frame_unit==='synthetic' && inv.legacy_v1_binding.mode==='withheld','unsupported_inventory_binding');
  list(inv.observations,1000);list(inv.periods,256);list(m.bindings,1000);ids(m.bindings,'observation_id');
  const periods=new Map(inv.periods.map(p=>[p.id,p])), meetings=new Map(c.meetings.map(p=>[p.id,p]));
  const countries=new Set(c.countries.map(p=>p.id)), topics=new Set(c.topics.map(p=>p.id));
  for(const meeting of c.meetings) {
    const p=periods.get(meeting.period_id);ensure(p,'meeting_period');
    ensure(meeting.date===null || meeting.date>=p.start && meeting.date<=p.end,'meeting_period');
  }
  ensure(m.bindings.length===inv.observations.length,'binding_denominator');
  const bindings=new Map(m.bindings.map(b=>[b.observation_id,b])), parents=new Set();
  for(const r of inv.observations) {
    token(r.id);token(r.period_id); if(r.meeting_id!==null)token(r.meeting_id);
    const b=bindings.get(r.id);ensure(b,'missing_binding');
    closed(b,['observation_id','country','capacity','topics','topics_complete','language','parent_id','start','end','parent_length'],'binding_fields');
    ensure(b.country===null || countries.has(b.country),'binding_country');
    ensure(['national','recorded','collective','unverified','not_applicable'].includes(b.capacity),'binding_capacity');
    ensure(typeof b.topics_complete==='boolean','topic_completeness');token(b.language);list(b.topics,64);
    ensure(new Set(b.topics).size===b.topics.length && b.topics.every(t=>topics.has(t)),'binding_topic');
    if(b.country!==null) ensure(r.actor_id===b.country && ['synthetic','recorded_affiliation'].includes(r.actor_kind),'affiliation_join');
    if(b.capacity==='national') ensure(b.country!==null && r.actor_kind==='synthetic','national_capacity');
    if(r.meeting_id!==null) {
      const meeting=meetings.get(r.meeting_id);ensure(meeting && meeting.period_id===r.period_id && (r.event_date===null || r.event_date===meeting.date),'meeting_join');
    }
    if(r.source_status==='available') {
      token(b.parent_id); ensure([b.start,b.end,b.parent_length].every(x=>Number.isSafeInteger(x) && x>=0 && x<=1000000) && b.start<b.end && b.end<=b.parent_length,'source_span');
      const key=canonical([r.meeting_id,b.parent_id]);ensure(!parents.has(key),'duplicate_parent');parents.add(key);
    } else ensure([b.parent_id,b.start,b.end,b.parent_length].every(x=>x===null),'unavailable_parent');
  }
  closed(m.policies,['entrypoints','capabilities'],'policy_fields');closed(m.policies.entrypoints,INTENTS,'entrypoints');
  list(m.policies.capabilities,32);ids(m.policies.capabilities);
  for(const cap of m.policies.capabilities) validateCapability(cap);
  const caps=new Map(m.policies.capabilities.map(cap=>[cap.id,cap]));
  for(const id of [...Object.values(m.policies.entrypoints),...caps.keys()]) {
    const visited=new Set();let next=id;
    while(next!==null) {
      ensure(caps.has(next),'unknown_fallback');ensure(!visited.has(next),'fallback_cycle');ensure(visited.size<MAX_HOPS,'fallback_limit');
      visited.add(next);next=caps.get(next).fallback;
    }
  }
  return m;
}
export async function queryFromSelection(metadata,input) {
  metadata=snapshot(metadata);
  const s=snapshot(input);closed(s,['country','topic','meeting','page','period'],'selection_fields');
  ensure(['explore','meetings'].includes(s.page),'selection_page');
  ensure(s.country===null || metadata.catalog.countries.some(x=>x.id===s.country),'unknown_country');
  ensure(s.topic===null || metadata.catalog.topics.some(x=>x.id===s.topic),'unknown_topic');
  const meeting=metadata.catalog.meetings.find(m=>m.id===s.meeting);
  ensure(s.page==='meetings' ? Boolean(meeting) : s.meeting===null,'unknown_meeting');
  if(meeting) ensure(meeting.date!==null,'meeting_date_unknown');
  const requested={countries:s.country===null?[]:[s.country],topic:s.topic,period:s.period,meeting:s.meeting,baseline:null};
  const period=s.period??(meeting?{start:meeting.date,end:meeting.date}:snapshot(metadata.catalog.period));
  const q={schema:'un.research-query.v1',contract_version:'1.0.0',intent:s.page==='meetings'?'meeting':s.country!==null?'country':s.topic!==null?'topic':'trends',timezone:'America/New_York',entity_role:'speaking_country',requested,
    resolved:{...snapshot(requested),period,baseline:'USA',forum:meeting?.forum??'synthetic_catalog',source_mode:'synthetic'},defaulted_fields:s.period===null?['period','baseline']:['baseline'],entity_registry_sha256:await digest(metadata.catalog)};
  validateQuery(q);return q;
}
function covers(periods,queryPeriod) {
  const lo=Date.parse(queryPeriod.start),hi=Date.parse(queryPeriod.end);
  const count=periods.reduce((n,p)=>n+Math.max(0,(Math.min(hi,Date.parse(p.end))-Math.max(lo,Date.parse(p.start)))/86400000+1),0);
  return count===inclusiveDays(queryPeriod);
}
/** Plans carry counts and identities, not approvals or a new fit. Country filters affect only display. */
export async function planQuery(metadata,input) {
  metadata=snapshot(metadata);
  const q=snapshot(input);validateQuery(q);ensure(q.resolved.source_mode==='synthetic','synthetic_only');
  ensure(q.entity_registry_sha256===await digest(metadata.catalog),'registry_mismatch');
  const c=metadata.catalog,inv=metadata.inventory,r=q.resolved,p=r.period;
  ensure(r.countries.every(id=>c.countries.some(x=>x.id===id)) && (r.baseline===null || c.countries.some(x=>x.id===r.baseline)),'unknown_country');
  ensure(r.topic===null || c.topics.some(x=>x.id===r.topic),'unknown_topic');
  const meeting=r.meeting===null?null:c.meetings.find(x=>x.id===r.meeting);
  ensure(r.meeting===null || Boolean(meeting),'unknown_meeting');
  ensure(r.forum===(meeting?.forum??'synthetic_catalog'),'forum_mismatch');
  let reason=null;
  if(RESERVED.some(d=>d>=p.start && d<=p.end) || meeting?.protected) reason='protected_scope';
  else if(meeting && meeting.date===null) reason='meeting_date_unknown';
  else if(meeting && (meeting.date<p.start || meeting.date>p.end)) reason='meeting_outside_requested_period';
  else if(!covers(inv.periods,p)) reason='unsupported_history';
  else if(c.collection_kind==='synthetic_live' && inclusiveDays(p)>LIVE_MAX_DAYS) reason='live_range_limit';
  const periods=new Map(inv.periods.map(x=>[x.id,x]));
  const rows=inv.observations.filter(row=> {
    const period=periods.get(row.period_id);
    return (row.event_date===null ? period.start<=p.end && period.end>=p.start : row.event_date>=p.start && row.event_date<=p.end) && (r.meeting===null || row.meeting_id===null || row.meeting_id===r.meeting);
  });
  if(!reason && rows.some(row=>row.event_date===null || row.meeting_id===null))reason='unresolved_source_scope';
  if(!reason && rows.some(row=>c.meetings.find(m=>m.id===row.meeting_id)?.protected))reason='protected_scope';
  const bindings=new Map(metadata.bindings.map(b=>[b.observation_id,b]));
  const counts={frame:rows.length,eligible:0,excluded:0,missing:0,unverified:0};
  const classified=rows.map(row=> {
    const b=bindings.get(row.id);let state,why=null;
    if(row.source_status==='unverified'){state='unverified';why='source_unverified';}
    else if(row.source_status==='excluded_language'){state='excluded';why='excluded_language';}
    else if(row.source_status!=='available'){state='missing';why=row.source_status;}
    else if(r.topic!==null && !b.topics_complete){state='unverified';why='topic_unverified';}
    else if(r.topic!==null && !b.topics.includes(r.topic)){state='excluded';why='topic_not_selected';}
    else {state='eligible';}
    counts[state]++;return {id:row.id,state,reason:why};
  });
  const fitIds=classified.filter(x=>x.state==='eligible').map(x=>x.id).sort();
  const displayIds=fitIds.filter(id=>r.countries.length===0 || (bindings.get(id).capacity==='national' && r.countries.includes(bindings.get(id).country)));
  const uncertainAffiliation=fitIds.filter(id=>r.countries.length>0 && bindings.get(id).capacity==='unverified').length;
  if(!reason && uncertainAffiliation)reason='unresolved_country_attribution';
  if(!reason && (new Set(fitIds.map(id=>bindings.get(id).language)).size>1 || new Set(rows.filter(row=>fitIds.includes(row.id)).map(row=>row.genre)).size>1))reason='heterogeneous_source_regime';
  if(reason) return {schema:'un.query-route-plan.v1',authority:'none',publication_eligible:false,synthetic_only:true,state:'unavailable',reason,query:q,query_sha256:await digest(q),
    source_sha256:null,parent_selection_sha256:null,source_hash_basis:null,inventory_sha256:null,fit_population:null,display_population:null,selection_sha256:null,
    fit_ids:[],display_ids:[],classification:[],days:inclusiveDays(p),source_states:null,excluded_from_country:null};
  const fitSha=await digest({schema:'u2.fit-population.v1',source:inv.upstream.source_sha256,parent_selection:inv.upstream.selection_sha256,inventory:inv.inventory_sha256,period:p,meeting:r.meeting,topic:r.topic,classification:classified});
  const displaySha=await digest({schema:'u2.display-population.v1',parent:fitSha,countries:r.countries,ids:displayIds});
  return {schema:'un.query-route-plan.v1',authority:'none',publication_eligible:false,synthetic_only:true,state:reason?'unavailable':'planned',reason,query:q,query_sha256:await digest(q),
    source_sha256:inv.upstream.source_sha256,parent_selection_sha256:inv.upstream.selection_sha256,source_hash_basis:inv.upstream.source_hash_basis,inventory_sha256:inv.inventory_sha256,
    fit_population:{id:'u2_frozen_scope',sha256:fitSha,unit:'synthetic',weighting:'equal_record',dependence_unit:'meeting',...counts},display_population:{parent_sha256:fitSha,sha256:displaySha,count:displayIds.length,selection_only:true},
    selection_sha256:displaySha,fit_ids:fitIds,display_ids:displayIds,classification:classified,days:inclusiveDays(p),
    source_states:inventoryContract.statusLedger(rows),excluded_from_country:fitIds.length-displayIds.length};
}
