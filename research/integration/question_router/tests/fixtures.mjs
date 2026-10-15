/** Test-only fictional metadata and ephemeral approvals. No transcript or model input. */
import {generateKeyPairSync,sign} from 'node:crypto';
import inventory from '../../../../docs/parallel-work/source-inventory-v1.cjs';
import {canonical,digest,bindingFor,receiptSetDigest,validateProduct,GATES} from '../../product_contracts/contracts.mjs';
import {snapshot,queryFromSelection,planQuery,C0_HEAD} from '../metadata.mjs';
import {createRouter} from '../router.mjs';
export const select=(extra={})=>({page:'explore',country:null,topic:null,meeting:null,period:{start:'2024-09-23',end:'2024-09-23'},...extra});
export async function fixtureMetadata() {
  const periods=[{id:'001',start:'2024-09-23',end:'2024-09-23'},{id:'002',start:'2024-09-24',end:'2024-09-24'}];
  const catalog={schema:'u2.synthetic-catalog.v1',timezone:'America/New_York',collection_kind:'synthetic_live',
    countries:[{id:'BRA',name:'Brazil',aliases:['Brasil']},{id:'CAN',name:'Canada',aliases:[]},{id:'USA',name:'United States',aliases:['US','United States of America']}],
    topics:[{id:'climate',name:'Climate and energy',aliases:['clean energy']},{id:'peace',name:'Peace and dialogue',aliases:['dialogue']},{id:'development',name:'Sustainable development',aliases:['services']}],
    meetings:[{id:'01',name:'Invented sustainable futures',date:'2024-09-23',forum:'synthetic_plenary',period_id:'001',protected:false},{id:'1',name:'Invented sustainable futures',date:'2024-09-24',forum:'synthetic_special',period_id:'002',protected:false}],period:{start:'2024-09-23',end:'2024-09-24'}};
  const specs=[['r01','01','BRA','national','climate','available'],['r02','01','USA','national','climate','available'],['r03','01','CAN','national','development','available'],['r04','01','BRA','collective','peace','available'],['r05','01','CAN','recorded','peace','available'],['r06','1','BRA','national','peace','available'],['r07','1',null,'unverified',null,'unavailable'],['r08','1',null,'unverified',null,'unverified']];
  const observations=[],bindings=[];
  for(const [id,meeting,country,capacity,topic,status] of specs) {
    const m=catalog.meetings.find(x=>x.id===meeting),available=status==='available';
    observations.push({id,period_id:m.period_id,year:2024,actor_kind:'synthetic',actor_id:country,genre:'invented',source_status:status,missing_reason:available?null:'synthetic_missing_record',event_date:m.date,meeting_id:meeting,source_family_id:'family/'+meeting,source_sha256:available?await digest({fictional_meeting:meeting}):null,text_sha256:available?await digest({fictional_record:id}):null,source_verification:available?'synthetic':'unverified',review_status:'not_applicable'});
    bindings.push({observation_id:id,country,capacity,topics:topic?[topic]:[],topics_complete:available,language:'en',parent_id:available?'parent/'+id:null,start:available?0:null,end:available?40:null,parent_length:available?40:null});
  }
  const counts=inventory.statusLedger(observations);
  const inv={schema:'un.parallel-source-inventory.v1',contract_version:'1.0.0',producer:{workstream_id:'C0',adapter_version:'1.0.0',fixture_kind:'synthetic'},
    upstream:{source_schema:'synthetic.v1',source_engine:'u2_fictional_metadata',source_hash_basis:'synthetic',source_sha256:await digest({schema:'u2.fictional-source.v1',ids:specs.map(r=>r[0])}),selection_sha256:await digest({schema:'u2.fictional-source-selection.v1',ids:specs.map(r=>r[0])})},
    population:{split:'synthetic',population_id:'fictional_u2_frame',frame_unit:'synthetic',selection_policy:'Fictional metadata; no original speech population',total_in_frame:counts.total,available:counts.available,unverified:counts.unverified,other_missing:counts.other_missing},
    periods,observations,coverage:periods.map(p=>({period_id:p.id,...inventory.statusLedger(observations.filter(r=>r.period_id===p.id))})),inventory_sha256:inventory.hash(observations),
    legacy_v1_binding:{mode:'withheld',reason:'No legacy analytical projection issued',legacy_selection_sha256:null,legacy_eligible:null},limitations:['Fictional metadata, not verified UN records.'],publication_eligible:false,evaluation_role:'engineering_only'};
  const capabilities=[];
  for(const id of ['semantic','description'])capabilities.push({schema:'un.product-capability.v1',contract_version:'1.0.0',id,
    intents:['country','topic','meeting','comparison','trends'],recipe:{id:'fictional_'+id,version:'1',configuration_sha256:await digest({fictional_recipe:id}),representation_id:id==='semantic'?'fictional_representation':null,checkpoint_sha256:null},
    regime:{source_schemas:['un.parallel-source-inventory.v1'],source_modes:['synthetic'],units:['synthetic'],languages:['en'],genres:['invented'],max_days:31,max_frame:1000,max_display:1000},claims:id==='semantic'?['exploratory']:['descriptive'],destinations:['local_view','local_export'],extra_gates:[],fallback:id==='semantic'?'description':null,benchmark_sha256:null});
  return {schema:'un.question-router-metadata.v1',fixture_kind:'synthetic',catalog,inventory:inv,bindings,policies:{entrypoints:Object.fromEntries(['country','topic','meeting','comparison','trends'].map(x=>[x,'semantic'])),capabilities}};
}
export function rehashInventory(metadata) {
  const inv=metadata.inventory,c=inventory.statusLedger(inv.observations);
  Object.assign(inv.population,{total_in_frame:c.total,available:c.available,unverified:c.unverified,other_missing:c.other_missing});
  inv.inventory_sha256=inventory.hash(inv.observations);
  inv.coverage=inv.periods.map(p=>({period_id:p.id,...inventory.statusLedger(inv.observations.filter(r=>r.period_id===p.id))}));return metadata;
}
export async function fixtureBundle(m,selection,capId='description',state='auto') {
  const query=selection.schema==='un.research-query.v1'?snapshot(selection):await queryFromSelection(m,selection),plan=await planQuery(m,query);
  const cap=snapshot(m.policies.capabilities.find(x=>x.id===capId)),claim=cap.claims[0];
  const failed=state==='failed',skipped=state==='skipped',n=plan.fit_ids.length;
  const ids=failed||skipped?[]:plan.display_ids;
  const resultSha=await digest({schema:'u2.fictional-result.v1',fit:plan.fit_population.sha256,capability:cap.id,state});
  const ref={schema:'un.parallel-analysis.v1',artifact_sha256:resultSha,pointer:'/fictional_metadata'};
  const evidence=ids.map(id=>{const row=m.inventory.observations.find(r=>r.id===id),b=m.bindings.find(x=>x.observation_id===id);return {id,ref:snapshot(ref),source_id:id,text_sha256:row.text_sha256,raw_sha256:row.source_sha256,hash_basis:'synthetic',parent_id:b.parent_id,meeting_id:row.meeting_id,source_family_id:row.source_family_id,start:b.start,end:b.end,parent_length:b.parent_length,country:b.country,capacity:b.capacity==='recorded'?'unverified':b.capacity};});
  const findings=evidence.map((e,i)=>({id:'finding/'+i,claim,template:'synthetic_only',result:snapshot(ref),support:[e.id],contrary:[],contrary_search:'not_run',country:e.capacity==='national'?e.country:null}));
  const dataState=failed?'failed':skipped?'withheld':ids.length?'available':'empty';
  const reason=failed?'fixture_reader_failure':skipped?'fixture_skipped':ids.length?null:'no_matches';
  const planned=n?1:0,succeeded=n&&!failed&&!skipped?1:0;
  const product={schema:'un.evidence-product.v1',contract_version:'1.0.0',id:'fixture/'+(await digest(query)).slice(0,24)+'/'+cap.id,run_id:'fixture_run/'+resultSha.slice(0,24),fixture_kind:'synthetic',publication_eligible:false,evaluation_role:'engineering_only',query_sha256:await digest(query),capability_sha256:await digest(cap),
    upstream:{schema:'un.parallel-source-inventory.v1',source_sha256:plan.source_sha256,source_missing_reason:null,source_hash_basis:'synthetic',selection_sha256:plan.selection_sha256,inventory_sha256:plan.inventory_sha256,review_sha256:null,entity_registry_sha256:query.entity_registry_sha256,language:'en',genre:'invented'},
    fit_population:snapshot(plan.fit_population),display_population:snapshot(plan.display_population),fit:{representation_id:cap.recipe.representation_id,configuration_sha256:cap.recipe.configuration_sha256,checkpoint_sha256:null,result_sha256:resultSha,planned,attempted:skipped?0:planned,succeeded,failed:failed?planned:0,skipped:skipped?planned:0,ledger:planned?[{id:'fictional_attempt',model_id:'fictional_metadata_only',family_id:'no_fitted_model',seed:0,status:failed?'failed':skipped?'skipped':'succeeded',reason:failed||skipped?reason:null}]:[],assignments:{eligible:n,assigned:succeeded?n:0,unassigned:0,not_fitted:succeeded?0:n}},
    provenance:{base_sha:C0_HEAD,worker_sha:'0'.repeat(40),effective_tree_sha:'0'.repeat(40),adapter_version:'1.0.0',runtime:'fictional_metadata_not_a_fit_or_commit'},evidence,findings,
    sections:[{id:'overview',kind:'overview',claim,data_state:dataState,reason,finding_ids:findings.map(f=>f.id),result:ids.length?ref:null,display:null,uncertainty:'unavailable'}]};
  await validateProduct(product,query,cap);return {query,capability:cap,product,receipts:[]};
}
export async function environment(metadata=null) {
  const m=metadata??await fixtureMetadata(),{privateKey,publicKey}=generateKeyPairSync('ed25519');
  const kinds=['coordinator_acceptance','source_validation','comparability_review','owner_review','statistical_acceptance','display_validation','output_authorization'];
  const key={key_id:'ephemeral_u2_test',spki_base64:publicKey.export({type:'spki',format:'der'}).toString('base64'),gates:[...GATES],destinations:['local_view','local_export']};
  const bundles=new Map(),ledger=new Map(),state={now:'2026-10-15T21:00:00Z',revision:1,revoked:false,lookups:0,trustReads:0};
  const lookupKey=b=>canonical({query_sha256:b.product.query_sha256,capability_sha256:b.product.capability_sha256});
  async function authorize(b,verdicts={}) {
    const binding=await bindingFor(b.product),receipts=[];
    for(const destination of ['local_view','local_export'])for(const [i,gate] of GATES.entries()) {
      const payload={schema:'un.product-decision.v1',contract_version:'1.0.0',id:`fixture/${destination}/${gate}`,key_id:key.key_id,gate,verdict:verdicts[destination+':'+gate]??verdicts[gate]??'pass',section_id:'all',destination,binding,issued_at:'2026-10-15T20:00:00Z',expires_at:'2026-10-15T23:00:00Z',evidence_kind:kinds[i],evidence_sha256:await digest({fictional_only:gate})};
      receipts.push({payload,signature:sign(null,Buffer.from(canonical(payload)),privateKey).toString('base64')});
    }
    b.receipts=receipts;ledger.set(binding.product_sha256,{receipts:snapshot(receipts),commitment:await receiptSetDigest(receipts)});bundles.set(lookupKey(b),snapshot(b));return b;
  }
  const getTrust=async id=>{state.trustReads++;const entry=ledger.get(id);return {keys:entry&&!state.revoked?[snapshot(key)]:[],commitment:entry?.commitment??null,revision:String(state.revision),now:state.now};};
  const getBundle=async q=>{state.lookups++;return snapshot(bundles.get(canonical(q))??null);};
  const config={metadata:m,expectedMetadataSha256:await digest(m),getTrust,getBundle};
  return {metadata:m,bundles,ledger,state,key,getTrust,getBundle,authorize,lookupKey,config,
    async register(selection,capId='description',status='auto',verdicts={}) {return authorize(await fixtureBundle(m,selection,capId,status),verdicts);},
    async router(extra={}) {return createRouter({...config,...extra});},
    async veto(b) {
      const id=await digest(b.product),entry=ledger.get(id),payload={...snapshot(entry.receipts.find(r=>r.payload.gate==='source').payload),id:'fixture/source/veto',verdict:'fail'};
      entry.receipts.push({payload,signature:sign(null,Buffer.from(canonical(payload)),privateKey).toString('base64')});entry.commitment=await receiptSetDigest(entry.receipts);state.revision++;
    }
  };
}
