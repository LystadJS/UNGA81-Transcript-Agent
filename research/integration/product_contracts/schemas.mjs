/** C0 draft v1 metadata wrappers. No upstream schema is amended. */
export const VERSION = '1.0.0';
const str = (maxLength = 160, pattern = '^[A-Za-z0-9][A-Za-z0-9._:/-]*$') => ({type:'string',minLength:1,maxLength,pattern});
const id = str(), hash = str(64, '^[a-f0-9]{64}$'), commit = str(40, '^[a-f0-9]{40}$');
const date = str(10, '^\\d{4}-\\d{2}-\\d{2}$');
const stamp = str(20, '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$');
const count = {type:'integer',minimum:0,maximum:1000000};
const en = (...values) => ({enum:values});
const nullable = schema => ({anyOf:[schema,{type:'null'}]});
const list = (items, maxItems = 256) => ({type:'array',items,maxItems});
const unique = (items, maxItems = 256) => ({...list(items,maxItems),uniqueItems:true});
const obj = properties => ({type:'object',properties,required:Object.keys(properties),additionalProperties:false});
const country = str(3, '^[A-Z]{3}$');
export const GATES = Object.freeze(['engineering','source','comparability','review','inference','display','export']);
export const DESTINATIONS = Object.freeze(['local_view','local_export','public_site','email']);
export const UPSTREAM = Object.freeze(['un.browser.corpus.v1','un.latent-comparison.v1','un.passage-corpus.v1','un.review.v1','un.parallel-analysis.v1','un.parallel-source-inventory.v1','un.diplomatic-readout.v1','un.us-relative-trajectories.v1']);
const period = obj({start:date,end:date});
const intent = en('country','topic','meeting','comparison','trends');
const claim = en('descriptive','exploratory','inferential','stance');
const sourceMode = en('synthetic','live','saved','historical');
const unit = en('source_segment','passage','reviewed_speech','parent','country_period','synthetic');
const selections = {countries:unique(country),topic:nullable(id),period:nullable(period),meeting:nullable(id),baseline:nullable(country)};
const query = obj({schema:{const:'un.research-query.v1'},contract_version:{const:VERSION},intent,
  timezone:{const:'America/New_York'},entity_role:{const:'speaking_country'},
  requested:obj(selections),resolved:obj({...selections,period,forum:id,source_mode:sourceMode}),
  defaulted_fields:unique(en('period','baseline'),2),entity_registry_sha256:hash});
const capability = obj({schema:{const:'un.product-capability.v1'},contract_version:{const:VERSION},id,
  intents:unique(intent,5),recipe:obj({id,version:id,configuration_sha256:hash,representation_id:nullable(id),checkpoint_sha256:nullable(hash)}),
  regime:obj({source_schemas:unique(en(...UPSTREAM),8),source_modes:unique(sourceMode,4),units:unique(unit,6),languages:unique(id,16),genres:unique(id,32),max_days:{type:'integer',minimum:1,maximum:36600},max_frame:count,max_display:count}),
  claims:unique(claim,4),destinations:unique(en(...DESTINATIONS),4),extra_gates:unique(en(...GATES),7),
  fallback:nullable(id),benchmark_sha256:nullable(hash)});
const ref = obj({schema:en(...UPSTREAM),artifact_sha256:hash,pointer:str(320,'^(?:/(?:[A-Za-z0-9_.:/-]|~[01])*)*$')});
const population = obj({id,sha256:hash,unit,weighting:id,dependence_unit:id,frame:count,eligible:count,excluded:count,missing:count,unverified:count});
const assignment = obj({eligible:count,assigned:count,unassigned:count,not_fitted:count});
const attempt = obj({id,model_id:id,family_id:id,seed:count,status:en('succeeded','failed','skipped'),reason:nullable(id)});
const evidence = obj({id,ref,source_id:id,text_sha256:hash,raw_sha256:nullable(hash),hash_basis:id,parent_id:nullable(id),meeting_id:nullable(id),source_family_id:nullable(id),
  start:nullable(count),end:nullable(count),parent_length:nullable(count),country:nullable(country),capacity:en('national','collective','unverified','not_applicable')});
const finding = obj({id,claim,template:en('observed_coverage','observed_topic','observed_expression','language_comparison','period_comparison','synthetic_only'),
  result:ref,support:unique(id),contrary:unique(id),contrary_search:en('not_run','searched','unavailable'),country:nullable(country)});
const section = obj({id,kind:en('overview','evidence','comparison','trend','map'),claim,
  data_state:en('available','partial','empty','failed','withheld'),reason:nullable(id),finding_ids:unique(id),
  result:nullable(ref),display:nullable(ref),uncertainty:en('unavailable','sensitivity','calibrated')});
const product = obj({schema:{const:'un.evidence-product.v1'},contract_version:{const:VERSION},id,run_id:id,
  fixture_kind:en('synthetic','development'),publication_eligible:{const:false},evaluation_role:{const:'engineering_only'},
  query_sha256:hash,capability_sha256:hash,
  upstream:obj({schema:en(...UPSTREAM),source_sha256:nullable(hash),source_missing_reason:nullable(id),source_hash_basis:id,selection_sha256:hash,inventory_sha256:hash,review_sha256:nullable(hash),entity_registry_sha256:hash,language:id,genre:id}),
  fit_population:population,display_population:obj({parent_sha256:hash,sha256:hash,count:count,selection_only:{const:true}}),
  fit:obj({representation_id:nullable(id),configuration_sha256:hash,checkpoint_sha256:nullable(hash),result_sha256:hash,planned:count,attempted:count,succeeded:count,failed:count,skipped:count,ledger:list(attempt,512),assignments:assignment}),
  provenance:obj({base_sha:commit,worker_sha:commit,effective_tree_sha:commit,adapter_version:{const:VERSION},runtime:id}),
  evidence:list(evidence,2048),findings:list(finding,512),sections:list(section,32)});
const binding = obj({product_sha256:hash,query_sha256:hash,capability_sha256:hash,source_sha256:nullable(hash),selection_sha256:hash,fit_population_sha256:hash,display_population_sha256:hash,worker_sha:commit,effective_tree_sha:commit});
const decision = obj({schema:{const:'un.product-decision.v1'},contract_version:{const:VERSION},id,key_id:id,gate:en(...GATES),
  verdict:en('pass','fail','not_run','not_applicable'),section_id:id,destination:en(...DESTINATIONS),binding,
  issued_at:stamp,expires_at:stamp,evidence_kind:en('coordinator_acceptance','source_validation','comparability_review','owner_review','statistical_acceptance','display_validation','output_authorization'),
  evidence_sha256:hash});
const receipt = obj({payload:decision,signature:str(88,'^[A-Za-z0-9+/]{86}==$')});
const authority = obj({key_id:id,spki_base64:str(512,'^[A-Za-z0-9+/]+={0,2}$'),gates:unique(en(...GATES),7),destinations:unique(en(...DESTINATIONS),4)});
const state = en('ready','partial','empty','failed','withheld');
const readinessSection = obj({id,state,reason:nullable(id),gates:obj(Object.fromEntries(GATES.map(g=>[g,en('pass','fail','not_run','not_applicable','conflict')]))),blocked_gates:unique(en(...GATES),7),findings:list(finding,512),evidence:list(evidence,2048),result:nullable(ref),display:nullable(ref),uncertainty:en('unavailable','sensitivity','calibrated'),coverage:nullable(obj({population,assignments:assignment,planned:count,attempted:count,succeeded:count,failed:count,skipped:count}))});
const readiness = obj({schema:{const:'un.product-readiness.v1'},contract_version:{const:VERSION},valid:{type:'boolean'},state,reason:nullable(id),product_sha256:nullable(hash),sections:list(readinessSection,32),destination:en(...DESTINATIONS,'none'),can_export:{type:'boolean'},publication_eligible:{const:false},evaluation_role:{const:'engineering_only'},synthetic_only:{const:true}});
const entries = {query,capability,product,decision,receipt,authority,readiness};
function freeze(value) { if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } return value; }
export const SCHEMAS = freeze(Object.fromEntries(Object.entries(entries).map(([key,value]) => [key,{$schema:'https://json-schema.org/draft/2020-12/schema',$id:`urn:unga81:c0:${key}:${VERSION}`,...value}])));
