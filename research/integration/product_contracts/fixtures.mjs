/** Fictional metadata only. No persistent signing keys or authority records. */
import {digest, VERSION} from './contracts.mjs';
export const NOW='2000-02-01T12:00:00Z';
export const H='a'.repeat(64), J='b'.repeat(64), K='c'.repeat(64), C='d'.repeat(40);
export async function fixture() {
  const selection={countries:['XAA'],topic:null,period:{start:'2000-01-01',end:'2000-01-31'},meeting:null,baseline:null};
  const query={schema:'un.research-query.v1',contract_version:VERSION,intent:'country',timezone:'America/New_York',entity_role:'speaking_country',requested:structuredClone(selection),resolved:{...structuredClone(selection),baseline:'USA',forum:'synthetic_forum',source_mode:'synthetic'},defaulted_fields:['baseline'],entity_registry_sha256:H};
  const capability={schema:'un.product-capability.v1',contract_version:VERSION,id:'synthetic_descriptive',intents:['country','topic','meeting','comparison','trends'],recipe:{id:'synthetic_recipe',version:'1',configuration_sha256:H,representation_id:null,checkpoint_sha256:null},regime:{source_schemas:['un.parallel-analysis.v1'],source_modes:['synthetic'],units:['synthetic'],languages:['en'],genres:['synthetic_genre'],max_days:31,max_frame:600,max_display:600},claims:['descriptive','exploratory','inferential'],destinations:['local_view','local_export'],extra_gates:[],fallback:null,benchmark_sha256:null};
  const ref={schema:'un.parallel-analysis.v1',artifact_sha256:H,pointer:'/results/0'};
  const product={schema:'un.evidence-product.v1',contract_version:VERSION,id:'synthetic_product',run_id:'synthetic_run',fixture_kind:'synthetic',publication_eligible:false,evaluation_role:'engineering_only',query_sha256:await digest(query),capability_sha256:await digest(capability),
    upstream:{schema:'un.parallel-analysis.v1',source_sha256:H,source_missing_reason:null,source_hash_basis:'synthetic_bytes',selection_sha256:J,inventory_sha256:H,review_sha256:H,entity_registry_sha256:H,language:'en',genre:'synthetic_genre'},
    fit_population:{id:'synthetic_population',sha256:J,unit:'synthetic',weighting:'equal_source',dependence_unit:'meeting',frame:2,eligible:2,excluded:0,missing:0,unverified:0},
    display_population:{parent_sha256:J,sha256:K,count:1,selection_only:true},
    fit:{representation_id:null,configuration_sha256:H,checkpoint_sha256:null,result_sha256:H,planned:1,attempted:1,succeeded:1,failed:0,skipped:0,ledger:[{id:'attempt_01',model_id:'synthetic_model',family_id:'description',seed:0,status:'succeeded',reason:null}],assignments:{eligible:2,assigned:2,unassigned:0,not_fitted:0}},
    provenance:{base_sha:C,worker_sha:C,effective_tree_sha:C,adapter_version:VERSION,runtime:'node22_synthetic'},
    evidence:[{id:'e01',ref:structuredClone(ref),source_id:'synthetic_source_01',text_sha256:H,raw_sha256:H,hash_basis:'synthetic_bytes',parent_id:'synthetic_parent_01',meeting_id:'01',source_family_id:'synthetic_family',start:0,end:3,parent_length:5,country:'XAA',capacity:'national'}],
    findings:[{id:'f01',claim:'descriptive',template:'synthetic_only',result:structuredClone(ref),support:['e01'],contrary:[],contrary_search:'not_run',country:null}],
    sections:[{id:'overview',kind:'overview',claim:'descriptive',data_state:'available',reason:null,finding_ids:['f01'],result:structuredClone(ref),display:null,uncertainty:'unavailable'}]};
  return {query,capability,product};
}
export async function examples() {
  const base=await fixture();
  const empty=structuredClone(base);empty.product.evidence=[];empty.product.findings=[];
  Object.assign(empty.product.sections[0],{data_state:'empty',reason:'no_matches',finding_ids:[],result:null});
  const missing=structuredClone(empty);missing.product.upstream.source_sha256=null;missing.product.upstream.source_missing_reason='source_unavailable';
  const partial=structuredClone(base);partial.product.fit_population.frame=3;partial.product.fit_population.missing=1;
  return {ready_candidate:base,empty_candidate:empty,missing_source:missing,partial_candidate:partial};
}