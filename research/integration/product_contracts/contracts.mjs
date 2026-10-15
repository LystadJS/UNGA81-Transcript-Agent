/** Pure, source-free C0 validation and readiness. No fetch, fit, render or release. */
import {SCHEMAS, GATES, DESTINATIONS, VERSION} from './schemas.mjs';
export {SCHEMAS, GATES, DESTINATIONS, VERSION};
const fail = code => { throw new Error(code); };
const check = (condition, code) => { if (!condition) fail(code); };
const same = (a,b) => canonical(a) === canonical(b);
const copy = value => JSON.parse(JSON.stringify(value));
const own = (o,k) => Object.prototype.hasOwnProperty.call(o,k);
const plain = o => o !== null && typeof o === 'object' && Object.getPrototypeOf(o) === Object.prototype;
const isDate = s => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(Date.parse(s)) && new Date(s).toISOString().slice(0,10) === s;
const isStamp = s => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(s) && !Number.isNaN(Date.parse(s)) && new Date(s).toISOString() === s.replace('Z','.000Z');

export function canonical(value) {
  if (value === null || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'string') { check(value.isWellFormed(),'unicode'); return JSON.stringify(value); }
  if (typeof value === 'number') { check(Number.isSafeInteger(value),'integer_wire'); return JSON.stringify(value); }
  if (Array.isArray(value)) return '['+value.map(canonical).join(',')+']';
  check(plain(value),'plain_object');
  return '{'+Object.keys(value).sort().map(k => JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
}
export async function digest(value) {
  const bytes = new TextEncoder().encode(canonical(value));
  const hash = await globalThis.crypto.subtle.digest('SHA-256',bytes);
  return Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
}

/** Duplicate-key rejecting JSON boundary; never use JSON.parse on untrusted bundles. */
export function parseStrict(text) {
  check(typeof text === 'string' && new TextEncoder().encode(text).length <= 2097152,'wire_size');
  let i = 0;
  const space = () => { while (/[\t\n\r ]/.test(text[i] || '\0')) i++; };
  const string = () => {
    const match = /^"(?:[^"\\\u0000-\u001f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"/.exec(text.slice(i));
    check(match,'json_string'); i += match[0].length;
    const value = JSON.parse(match[0]); check(value.isWellFormed(),'unicode'); return value;
  };
  const value = depth => {
    check(depth <= 24,'wire_depth'); space();
    if (text[i] === '"') return string();
    if (text[i] === '{') {
      i++; space(); const result = {}; const seen = new Set();
      if (text[i] === '}') { i++; return result; }
      for (;;) {
        check(text[i] === '"','json_key'); const key = string();
        check(!seen.has(key) && !['__proto__','constructor','prototype'].includes(key),'duplicate_or_unsafe_key'); seen.add(key);
        space(); check(text[i++] === ':','json_colon'); result[key] = value(depth+1); space();
        const close = text[i++]; if (close === '}') return result; check(close === ',','json_object'); space();
      }
    }
    if (text[i] === '[') {
      i++; space(); const result = []; if (text[i] === ']') { i++; return result; }
      for (;;) { check(result.length < 10000,'wire_items'); result.push(value(depth+1)); space(); const close=text[i++]; if(close === ']') return result; check(close === ',','json_array'); }
    }
    const token = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(text.slice(i));
    check(token,'json_value'); i += token[0].length; const result = JSON.parse(token[0]);
    if (typeof result === 'number') check(Number.isSafeInteger(result),'integer_wire'); return result;
  };
  const result = value(0); space(); check(i === text.length,'json_trailing'); return result;
}

/** Deliberately closed schema subset, independently cross-checked with Draft 2020-12. */
export function validateShape(kind, data) {
  check(own(SCHEMAS,kind),'schema_kind');
  const walk = (s,v,depth=0) => {
    check(depth <= 24,'schema_depth');
    if (s.anyOf) { check(s.anyOf.some(child => { try {walk(child,v,depth+1);return true;} catch{return false;} }),'nullable_shape'); return; }
    if (own(s,'const')) {check(same(v,s.const),'const');return;}
    if (s.enum) {check(s.enum.some(x=>same(v,x)),'enum');return;}
    if (s.type === 'boolean') {check(typeof v==='boolean','boolean');return;}
    if (s.type === 'null') {check(v===null,'null');return;}
    if (s.type === 'string') {check(typeof v==='string' && v.isWellFormed() && [...v].length>=s.minLength && [...v].length<=s.maxLength && new RegExp(s.pattern).test(v),'string');return;}
    if (s.type === 'integer') {check(Number.isSafeInteger(v) && v>=s.minimum && v<=s.maximum,'integer');return;}
    if (s.type === 'array') {check(Array.isArray(v) && v.length<=s.maxItems,'array');v.forEach(x=>walk(s.items,x,depth+1));if(s.uniqueItems)check(new Set(v.map(canonical)).size===v.length,'duplicate');return;}
    check(s.type==='object' && plain(v),'object');
    const descriptors=Object.getOwnPropertyDescriptors(v);
    check(Reflect.ownKeys(v).length===s.required.length && s.required.every(k=>own(v,k)) && Object.keys(v).every(k=>own(s.properties,k) && own(descriptors[k],'value')),'closed_fields');
    Object.entries(s.properties).forEach(([k,child])=>walk(child,v[k],depth+1));
  };
  walk(SCHEMAS[kind],data); return true;
}

export function validateQuery(query) {
  validateShape('query',query);
  const a=query.requested,b=query.resolved;
  for(const key of ['countries','topic','meeting']) check(same(a[key],b[key]),'query_scope_changed');
  for(const key of ['period','baseline']) {
    if(a[key]!==null) check(same(a[key],b[key]) && !query.defaulted_fields.includes(key),'query_scope_changed');
    else check((b[key]!==null)===query.defaulted_fields.includes(key),'unrecorded_default');
  }
  for(const p of [a.period,b.period].filter(Boolean)) check(isDate(p.start) && isDate(p.end) && p.start<=p.end,'date_range');
  if(a.baseline===null && b.baseline!==null) check(b.baseline==='USA','baseline_default');
  if(query.intent==='country') check(b.countries.length===1,'country_query');
  if(query.intent==='topic') check(b.topic!==null,'topic_query');
  if(query.intent==='meeting') check(b.meeting!==null,'meeting_query');
  if(query.intent==='comparison') check(b.countries.length>0 && b.baseline!==null,'comparison_query');
  return true;
}
export function validateCapability(cap) {
  validateShape('capability',cap);
  for(const key of ['intents','claims','destinations']) check(cap[key].length>0,'empty_capability');
  for(const key of ['source_schemas','source_modes','units','languages','genres']) check(cap.regime[key].length>0,'empty_regime');
  check(cap.fallback!==cap.id,'fallback_cycle'); return true;
}
const uniqueIds = items => check(new Set(items.map(x=>x.id)).size===items.length,'duplicate_identity');
export async function validateProduct(product,query,cap) {
  validateQuery(query); validateCapability(cap); validateShape('product',product);
  check(product.query_sha256===await digest(query) && product.capability_sha256===await digest(cap),'query_policy_digest');
  const u=product.upstream,p=product.fit_population,v=product.display_population,f=product.fit;
  check((u.source_sha256===null)===(u.source_missing_reason!==null),'source_missing_reason');
  check(u.entity_registry_sha256===query.entity_registry_sha256,'entity_registry');
  check(p.frame===p.eligible+p.excluded+p.missing+p.unverified,'frame_denominator');
  check(v.parent_sha256===p.sha256 && v.count<=p.eligible,'display_population');
  check(f.configuration_sha256===cap.recipe.configuration_sha256 && f.representation_id===cap.recipe.representation_id && f.checkpoint_sha256===cap.recipe.checkpoint_sha256,'fit_recipe');
  check(f.planned===f.ledger.length && f.planned===f.attempted+f.skipped && f.attempted===f.succeeded+f.failed,'fit_denominator');
  uniqueIds(f.ledger);
  for(const state of ['succeeded','failed','skipped']) check(f.ledger.filter(x=>x.status===state).length===f[state],'fit_ledger');
  for(const a of f.ledger) check((a.status==='succeeded')===(a.reason===null),'attempt_reason');
  check(f.assignments.eligible===p.eligible && p.eligible===f.assignments.assigned+f.assignments.unassigned+f.assignments.not_fitted,'assignment_denominator');
  if(f.succeeded===0) check(f.assignments.assigned===0 && f.assignments.unassigned===0,'no_success_assignments');
  for(const entries of [product.evidence,product.findings,product.sections]) uniqueIds(entries);
  check(product.sections.length>0,'empty_sections');
  const evidence=new Map(product.evidence.map(e=>[e.id,e])),findings=new Map(product.findings.map(e=>[e.id,e]));
  for(const e of evidence.values()) {
    check(e.hash_basis===u.source_hash_basis,'evidence_hash_basis');
    const spans=[e.start,e.end,e.parent_length];
    check(spans.every(x=>x===null) || (spans.every(x=>x!==null) && e.parent_id!==null && e.start<e.end && e.end<=e.parent_length),'evidence_span');
    if(e.capacity==='national') check(e.country!==null && e.meeting_id!==null,'national_identity');
  }
  const used=new Set();
  for(const finding of findings.values()) {
    check(finding.support.length>0,'missing_support');
    check([...finding.support,...finding.contrary].every(x=>evidence.has(x)),'evidence_join');
    check(!finding.support.some(x=>finding.contrary.includes(x)),'support_contrary_overlap');
    if(finding.contrary.length) check(finding.contrary_search==='searched','contrary_search');
    if(finding.country!==null) check(finding.support.every(x=>evidence.get(x).country===finding.country && evidence.get(x).capacity==='national'),'country_attribution');
    if(finding.template==='observed_expression') check(finding.country!==null,'expression_attribution');
  }
  for(const section of product.sections) {
    check(section.finding_ids.every(x=>findings.has(x) && findings.get(x).claim===section.claim),'finding_join');
    section.finding_ids.forEach(x=>used.add(x));
    if(section.data_state==='available') check(section.reason===null,'available_reason');
    else check(section.reason!==null,'unavailable_reason');
    if(['empty','failed','withheld'].includes(section.data_state)) check(section.finding_ids.length===0 && section.result===null && section.display===null,'withheld_payload');
    if(section.kind==='map' && ['available','partial'].includes(section.data_state)) check(section.display!==null,'missing_display');
    if(section.uncertainty==='calibrated') check(section.claim==='inferential','uncertainty_promotion');
    if(section.result) check(section.result.artifact_sha256===f.result_sha256,'result_binding');
    for(const x of section.finding_ids) check(findings.get(x).result.artifact_sha256===f.result_sha256,'finding_result_binding');
  }
  check(used.size===findings.size,'orphan_findings');
  const evidenceUsed=new Set(product.findings.flatMap(x=>[...x.support,...x.contrary]));
  check(evidenceUsed.size===evidence.size,'orphan_evidence'); return true;
}
export async function bindingFor(product) {
  return {product_sha256:await digest(product),query_sha256:product.query_sha256,capability_sha256:product.capability_sha256,
    source_sha256:product.upstream.source_sha256,selection_sha256:product.upstream.selection_sha256,
    fit_population_sha256:product.fit_population.sha256,display_population_sha256:product.display_population.sha256,
    worker_sha:product.provenance.worker_sha,effective_tree_sha:product.provenance.effective_tree_sha};
}
const KINDS={engineering:'coordinator_acceptance',source:'source_validation',comparability:'comparability_review',review:'owner_review',inference:'statistical_acceptance',display:'display_validation',export:'output_authorization'};
const fromBase64 = s => Uint8Array.from(atob(s),x=>x.charCodeAt(0));
async function verifyReceipt(receipt,keys,binding,now,sections) {
  validateShape('receipt',receipt); const p=receipt.payload;
  check(p.evidence_kind===KINDS[p.gate],'evidence_authority_kind');
  check(p.section_id==='all' || sections.has(p.section_id),'decision_section');
  check(isStamp(p.issued_at) && isStamp(p.expires_at) && p.issued_at<=now && p.issued_at<p.expires_at && now<p.expires_at,'stale_decision');
  check(same(p.binding,binding),'decision_binding');
  const authority=keys.find(k=>k.key_id===p.key_id);
  check(authority && authority.gates.includes(p.gate) && authority.destinations.includes(p.destination),'unknown_authority');
  const key=await crypto.subtle.importKey('spki',fromBase64(authority.spki_base64),{name:'Ed25519'},false,['verify']);
  check(await crypto.subtle.verify('Ed25519',key,fromBase64(receipt.signature),new TextEncoder().encode(canonical(p))),'signature');
  return p;
}
function gateVector(decisions,section,destination) {
  return Object.fromEntries(GATES.map(gate=>{
    const ds=decisions.filter(d=>d.gate===gate && (d.section_id==='all' || d.section_id===section.id) && d.destination===destination);
    const values=new Set(ds.map(d=>d.verdict));
    return [gate,values.size>1?'conflict':values.size===0?'not_run':[...values][0]];
  }));
}
function needed(section,cap) {
  const gates=new Set(['engineering','source','review','export',...cap.extra_gates]);
  if(['comparison','trend','map'].includes(section.kind) || section.claim!=='descriptive') gates.add('comparability');
  if(['inferential','stance'].includes(section.claim) || section.uncertainty==='calibrated') gates.add('inference');
  if(section.kind==='map') gates.add('display'); return [...gates];
}
function regimeFailure(product,query,cap) {
  if(product.fixture_kind!=='synthetic' || query.resolved.source_mode!=='synthetic') return 'development_not_authorized';
  const r=cap.regime,u=product.upstream,p=product.fit_population;
  if(!cap.intents.includes(query.intent) || !r.source_schemas.includes(u.schema) || !r.source_modes.includes(query.resolved.source_mode) || !r.units.includes(p.unit) || !r.languages.includes(u.language) || !r.genres.includes(u.genre)) return 'unsupported_regime';
  const days=(Date.parse(query.resolved.period.end)-Date.parse(query.resolved.period.start))/86400000+1;
  if(days>r.max_days || p.frame>r.max_frame || product.display_population.count>r.max_display) return 'resource_limit';
  if(u.source_sha256===null) return 'source_unavailable'; return null;
}
/** Keys are host configuration, NEVER imported from the product or an uploaded receipt. */
export async function assess({query,capability:cap,product,receipts=[],trustedKeys=[],destination='local_view',now=new Date().toISOString().replace(/\.\d{3}Z$/,'Z')}) {
  try {
    check(DESTINATIONS.includes(destination) && isStamp(now),'assessment_context');
    // Snapshot every untrusted object synchronously before crypto yields control.
    validateShape('query',query); validateShape('capability',cap); validateShape('product',product);
    check(Array.isArray(receipts) && Array.isArray(trustedKeys),'context_arrays');
    receipts.forEach(r=>validateShape('receipt',r)); trustedKeys.forEach(k=>validateShape('authority',k));
    query=copy(query); cap=copy(cap); product=copy(product); receipts=copy(receipts); trustedKeys=copy(trustedKeys);
    await validateProduct(product,query,cap);
    check(Array.isArray(receipts) && receipts.length<=512 && Array.isArray(trustedKeys) && trustedKeys.length<=32,'receipt_limit');
    check(new Set(trustedKeys.map(k=>k.key_id)).size===trustedKeys.length,'duplicate_authority');
    const binding=await bindingFor(product), ids=new Set(product.sections.map(s=>s.id));
    const ds=await Promise.all(receipts.map(r=>verifyReceipt(r,trustedKeys,binding,now,ids)));
    uniqueIds(ds);
    const globalReason=regimeFailure(product,query,cap) || (!['local_view','local_export'].includes(destination)?'destination_prohibited':!cap.destinations.includes(destination)?'destination_not_eligible':null);
    const results=product.sections.map(section=>{
      const gates=gateVector(ds,section,destination),required=needed(section,cap);
      const blocked=required.filter(g=>gates[g]!=='pass');
      let state,reason;
      if(globalReason) {state='withheld';reason=globalReason;}
      else if(!cap.claims.includes(section.claim)) {state='withheld';reason='claim_not_eligible';}
      else if(blocked.length) {state='withheld';reason='required_gate';}
      else if(section.data_state==='available') {state=product.fit_population.missing+product.fit_population.unverified+product.fit.failed+product.fit.skipped+product.fit.assignments.not_fitted>0?'partial':'ready';reason=state==='partial'?'incomplete_coverage':null;}
      else if(section.data_state==='empty' && product.fit_population.missing+product.fit_population.unverified+product.fit.failed+product.fit.skipped+product.fit.assignments.not_fitted>0) {state='partial';reason='incomplete_coverage';}
      else {state=section.data_state;reason=section.reason;}
      const visible=['ready','partial'].includes(state);
      const selected=visible?product.findings.filter(x=>section.finding_ids.includes(x.id)):[];
      const selectedEvidence=new Set(selected.flatMap(x=>[...x.support,...x.contrary]));
      return {id:section.id,state,reason,gates,blocked_gates:blocked,findings:copy(selected),evidence:visible?copy(product.evidence.filter(x=>selectedEvidence.has(x.id))):[],result:visible?copy(section.result):null,display:visible?copy(section.display):null,uncertainty:visible?section.uncertainty:'unavailable',coverage:(!globalReason && blocked.length===0)?{population:copy(product.fit_population),assignments:copy(product.fit.assignments),planned:product.fit.planned,attempted:product.fit.attempted,succeeded:product.fit.succeeded,failed:product.fit.failed,skipped:product.fit.skipped}:null};
    });
    const states=results.map(x=>x.state), visible=states.some(s=>['ready','partial'].includes(s));
    const state=states.every(s=>s==='ready')?'ready':visible?'partial':states.every(s=>s==='empty')?'empty':states.every(s=>s==='failed')?'failed':'withheld';
    return {schema:'un.product-readiness.v1',contract_version:VERSION,valid:true,state,reason:globalReason,product_sha256:binding.product_sha256,sections:results,destination,
      can_export:destination==='local_export' && visible,publication_eligible:false,evaluation_role:'engineering_only',synthetic_only:true};
  } catch {
    // Do not echo attacker-controlled strings, rejected prose or a previous result.
    return {schema:'un.product-readiness.v1',contract_version:VERSION,valid:false,state:'withheld',reason:'invalid_contract_or_decision',product_sha256:null,sections:[],destination:'none',can_export:false,publication_eligible:false,evaluation_role:'engineering_only',synthetic_only:true};
  }
}
/** Generation tokens prevent stale async imports from restoring old results. */
export function createSession() {
  let generation=0,current=null;
  return Object.freeze({
    invalidate() {generation++;current=null;},
    snapshot() {return copy(current);},
    async load(input) {const ticket=++generation;current=null;const result=await assess(input);if(ticket===generation)current=copy(result);return ticket===generation?copy(result):null;}
  });
}
/** Memory-only safe export. Never serialize the unfiltered input product. */
export async function exportReadModel(input) {
  const model=await assess({...input,destination:'local_export'});
  return model.can_export?{ok:true,media_type:'application/json',utf8:canonical(model)+'\n'}:{ok:false,media_type:null,utf8:null};
}
