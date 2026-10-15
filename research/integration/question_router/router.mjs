/** Offline selection of stored synthetic products. No source reader, signer, fitter or exporter. */
import {assess,canonical,digest,validateProduct,validateShape} from '../product_contracts/contracts.mjs';
import {ensure,equal,snapshot,RouterError,validateMetadata,queryFromSelection,planQuery,MAX_HOPS,findMeetings,countryId,topicId,meetingId} from './metadata.mjs';
export {RouterError} from './metadata.mjs';
const HASH=/^[a-f0-9]{64}$/;
function bundleData(value) {
  const b=snapshot(value);
  ensure(Object.keys(b).sort().join(',')==='capability,product,query,receipts','bundle_fields');
  ensure(b.product?.fixture_kind==='synthetic' && b.query?.resolved?.source_mode==='synthetic','synthetic_only');
  ensure(Array.isArray(b.receipts) && b.receipts.length<=512,'receipt_limit');b.receipts.forEach(r=>validateShape('receipt',r));
  return b;
}
function trustContext(value) {
  const t=snapshot(value);
  ensure(Object.keys(t).sort().join(',')==='commitment,keys,now,revision','host_context');
  ensure(typeof t.revision==='string' && t.revision.length>0 && t.revision.length<=100,'host_revision');
  ensure(typeof t.now==='string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(t.now) && Number.isFinite(Date.parse(t.now)) && new Date(t.now).toISOString()===t.now.replace('Z','.000Z'),'host_clock');
  ensure(t.commitment===null || typeof t.commitment==='string' && HASH.test(t.commitment),'host_commitment');
  ensure(Array.isArray(t.keys) && t.keys.length<=32,'host_keys');t.keys.forEach(k=>validateShape('authority',k));return t;
}
const trustIdentity=t=>canonical([t.keys,t.commitment,t.revision]);
const fresh=(b,now)=>b.receipts.every(r=>r.payload.issued_at<=now && now<r.payload.expires_at);
function eligible(cap,plan,metadata) {
  const r=cap.regime;
  if(!cap.intents.includes(plan.query.intent) || !r.source_schemas.includes('un.parallel-source-inventory.v1') || !r.source_modes.includes('synthetic') || !r.units.includes('synthetic'))return 'unsupported_regime';
  if(plan.days>r.max_days || plan.fit_population.frame>r.max_frame || plan.display_population.count>r.max_display)return 'resource_limit';
  const bindings=new Map(metadata.bindings.map(b=>[b.observation_id,b]));
  if(plan.fit_ids.some(id=>!r.languages.includes(bindings.get(id).language)))return 'unsupported_language';
  const rows=new Map(metadata.inventory.observations.map(o=>[o.id,o]));
  if(plan.fit_ids.some(id=>!r.genres.includes(rows.get(id).genre)))return 'unsupported_genre';
  return null;
}
async function validateBoundBundle(b,plan,cap,metadata) {
  ensure(equal(b.query,plan.query) && equal(b.capability,cap),'bundle_query_policy');
  await validateProduct(b.product,b.query,b.capability);
  const p=b.product,u=p.upstream;
  ensure(u.schema==='un.parallel-source-inventory.v1' && u.source_sha256===plan.source_sha256 && u.source_hash_basis===plan.source_hash_basis && u.inventory_sha256===plan.inventory_sha256 && u.selection_sha256===plan.selection_sha256,'source_inventory_binding');
  ensure(equal(p.fit_population,plan.fit_population) && equal(p.display_population,plan.display_population),'population_binding');
  // One C0 language/genre summary cannot stand for a heterogeneous source regime.
  const rows=new Map(metadata.inventory.observations.map(o=>[o.id,o])),bindings=new Map(metadata.bindings.map(o=>[o.observation_id,o]));
  ensure(plan.fit_ids.every(id=>bindings.get(id).language===u.language && rows.get(id).genre===u.genre),'heterogeneous_summary');
  ensure(!p.sections.some(s=>s.data_state==='empty') || plan.display_ids.length===0,'false_empty');
  for(const e of p.evidence) {
    ensure(plan.display_ids.includes(e.id),'evidence_outside_display');
    const row=rows.get(e.id),b=bindings.get(e.id);
    const expectedCapacity=b.capacity==='recorded'?'unverified':b.capacity;
    ensure(e.source_id===row.id && e.meeting_id===row.meeting_id && e.source_family_id===row.source_family_id && e.raw_sha256===row.source_sha256 && e.text_sha256===row.text_sha256 && e.hash_basis===plan.source_hash_basis,'evidence_lineage');
    ensure(e.country===b.country && e.capacity===expectedCapacity && e.parent_id===b.parent_id && e.start===b.start && e.end===b.end && e.parent_length===b.parent_length,'evidence_attribution_span');
  }
}
/** All three arguments are provisioned by trusted host code, never extracted from a bundle.
 * getBundle must only retrieve stored products. A missing product is null, not permission to fit.
 * getTrust supplies the CURRENT out-of-band ledger commitment/keyring/clock on every call.
 */
export async function createRouter({metadata,expectedMetadataSha256,getBundle,getTrust}) {
  ensure(typeof getBundle==='function' && typeof getTrust==='function','host_services');
  const m=await validateMetadata(metadata,expectedMetadataSha256);
  const caps=new Map(m.policies.capabilities.map(c=>[c.id,c]));
  const admitted=new Map();let generation=0;
  const current=ticket=>ensure(ticket===generation,'stale_route');
  const envelope=(state,reason,plan,trace,bundle=null,readiness=null)=>({schema:'un.query-route-result.v1',authority:'none',synthetic_only:true,publication_eligible:false,state,reason,plan,trace,bundle,readiness});
  async function evaluate(bundle,ticket) {
    const id=await digest(bundle.product);current(ticket);
    const before=trustContext(await getTrust(id));current(ticket);
    const readiness=await assess({...bundle,trustedKeys:before.keys,trustedReceiptSetSha256:before.commitment,destination:'local_view',now:before.now});current(ticket);
    const after=trustContext(await getTrust(id));current(ticket);
    ensure(trustIdentity(before)===trustIdentity(after) && fresh(bundle,after.now),'trust_changed');
    return {id,readiness};
  }
  async function run(getPlan) {
    const ticket=++generation, trace=[];let plan=null,last=null;
    try {
      plan=await getPlan();current(ticket);
      if(plan.state==='unavailable')return envelope('unavailable',plan.reason,plan,trace);
      let next=m.policies.entrypoints[plan.query.intent];const seen=new Set();
      while(next!==null) {
        current(ticket);ensure(seen.size<MAX_HOPS && !seen.has(next),'fallback_cycle');seen.add(next);
        const cap=caps.get(next);ensure(cap,'unknown_fallback');
        const why=eligible(cap,plan,m);
        if(why) {trace.push({capability_id:cap.id,outcome:'ineligible',reason:why,fit:null});next=cap.fallback;continue;}
        const key={query_sha256:plan.query_sha256,capability_sha256:await digest(cap)};current(ticket);
        // The lookup has only fixed identities. It cannot accept a tuning parameter or source URL.
        const value=await getBundle(snapshot(key));current(ticket);
        if(value===null) {trace.push({capability_id:cap.id,outcome:'missing',reason:'stored_product_missing',fit:null});next=cap.fallback;continue;}
        const b=bundleData(value);await validateBoundBundle(b,plan,cap,m);current(ticket);
        const {id,readiness}=await evaluate(b,ticket);current(ticket);
        ensure(readiness.valid,'invalid_decision');
        ensure(admitted.has(id) || admitted.size<128,'session_product_limit');
        admitted.set(id,true);
        trace.push({capability_id:cap.id,outcome:readiness.state,reason:readiness.reason,fit:snapshot(b.product.fit)});
        last=envelope(readiness.state,readiness.reason,plan,snapshot(trace),b,readiness);
        if(['ready','partial','empty'].includes(readiness.state))return snapshot(last);
        // Never search for another approval to bypass source, reviewer, engineering or output denial.
        const floor=['engineering','source','review','export'];
        if(readiness.sections.some(s=>floor.some(g=>s.gates[g]!=='pass')))return snapshot(last);
        next=cap.fallback;
      }
      return last?snapshot({...last,trace}):envelope('unavailable','no_qualifying_product',plan,trace);
    } catch(error) {
      if(ticket!==generation)return envelope('withheld','stale_route',null,[]);
      // No rejected product, raw exception message, prior result, or forged permission is returned.
      return envelope('withheld',error instanceof RouterError?error.code:'invalid_metadata_or_product',plan,trace);
    }
  }
  const api={
    metadataSha256:expectedMetadataSha256,
    async plan(selection) {const s=snapshot(selection);return planQuery(m,await queryFromSelection(m,s));},
    async planQuery(query) {return planQuery(m,snapshot(query));},
    async route(selection) {return run(async()=>{const s=snapshot(selection);return planQuery(m,await queryFromSelection(m,s));});},
    async routeQuery(query) {return run(()=>planQuery(m,snapshot(query)));},
    catalog() {return snapshot(m.catalog);},
    country(value) {return countryId(m.catalog,value);},
    topic(value) {return topicId(m.catalog,value);},
    meetings(search) {return findMeetings(m.catalog,search);},
    meeting(search) {return meetingId(m.catalog,search);},
    invalidate() {generation++;admitted.clear();},
    async getTrust(id) {
      ensure(typeof id==='string' && HASH.test(id),'product_id');
      if(!admitted.has(id))return {keys:[],commitment:null,revision:'unadmitted_product',now:new Date().toISOString().replace(/\.\d{3}Z$/,'Z')};
      const ticket=generation,t=trustContext(await getTrust(id));
      ensure(ticket===generation && admitted.has(id),'stale_route');return t;
    }
  };
  return Object.freeze(api);
}
/** Adapter for the accepted U1 controller's provider contract. No UI files are changed.
 * Source text delivery belongs to the separately authorized evidence service, not U2.
 */
export function createU1Provider(router) {
  return Object.freeze({
    async catalog() {
      const c=router.catalog();
      return {schema:'u1.synthetic-catalog.v1',fixture_kind:'synthetic',countries:c.countries.map(({id,name})=>({id,name})),topics:c.topics.map(({id,name})=>({id,name})),
        meetings:c.meetings.filter(m=>!m.protected && m.date!==null).map(({id,name,date,forum})=>({id,name,date,forum})),period:c.period};
    },
    async resolve(selection) {
      const result=await router.route(selection);
      if(!result.bundle)throw new RouterError(result.reason??'no_qualifying_product');
      return snapshot(result.bundle);
    },
    getTrust:id=>router.getTrust(id),
    async getEvidence() {throw new RouterError('evidence_service_not_connected');}
  });
}
