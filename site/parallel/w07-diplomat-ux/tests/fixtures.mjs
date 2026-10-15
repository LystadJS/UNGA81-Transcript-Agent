/** TEST HARNESS ONLY. Generates ephemeral keys for fictional inputs, never operational approvals. */
import {generateKeyPairSync,sign} from 'node:crypto';
import {canonical,digest,receiptSetDigest,bindingFor,validateQuery,validateProduct,assess} from '../../../../research/integration/product_contracts/contracts.mjs';
import {textDigest,C0_COMMIT} from '../controller.mjs';
const copy=x=>JSON.parse(canonical(x)), ZERO='0'.repeat(40);
export const CATALOG={schema:'u1.synthetic-catalog.v1',fixture_kind:'synthetic',countries:[{id:'BRA',name:'Brazil'},{id:'CAN',name:'Canada'},{id:'USA',name:'United States'}],topics:[{id:'climate',name:'Climate and energy'},{id:'peace',name:'Peace and dialogue'},{id:'development',name:'Sustainable development'}],meetings:[{id:'01',name:'Sustainable futures',date:'2024-09-23',forum:'Plenary · invented'},{id:'1',name:'Sustainable futures',date:'2024-09-24',forum:'Special session · invented'},{id:'03',name:'Dialogue for peace',date:'2024-09-25',forum:'Plenary · invented'}],period:{start:'2024-09-23',end:'2024-09-25'}};
const RECORDS=[
 {id:'e01',meeting:'01',country:'BRA',capacity:'national',topic:'climate',text:'Invented example: We propose a joint programme to improve access to clean energy.'},
 {id:'e02',meeting:'01',country:'USA',capacity:'national',topic:'climate',text:'Invented example: We call for practical cooperation on energy infrastructure.'},
 {id:'e03',meeting:'01',country:'CAN',capacity:'national',topic:'development',text:'Invented example: We support a shared fund for resilient local services.'},
 {id:'e04',meeting:'01',country:'BRA',capacity:'collective',topic:'development',text:'Invented example: On behalf of a group, we request a review of access to development finance.'},
 {id:'e05',meeting:'1',country:'BRA',capacity:'national',topic:'peace',text:'Invented example: We propose a dialogue on reducing tensions.'},
 {id:'e06',meeting:'1',country:'USA',capacity:'national',topic:'development',text:'Invented example: We request practical steps to improve access to essential services.'}
];
const KINDS={engineering:'coordinator_acceptance',source:'source_validation',comparability:'comparability_review',review:'owner_review',display:'display_validation',export:'output_authorization'};
export async function makeHarness() {
  const {publicKey,privateKey}=generateKeyPairSync('ed25519');
  const key={key_id:'ephemeral_synthetic',spki_base64:publicKey.export({type:'spki',format:'der'}).toString('base64'),gates:Object.keys(KINDS),destinations:['local_view','local_export']};
  const ledger=new Map(), cache=new Map(); let revision=1, revoked=false, offset=0, resolveCount=0;
  const now=()=>new Date(Date.now()+offset).toISOString().replace(/\.\d{3}Z$/,'Z');
  const sourceHash=await digest({records:RECORDS,synthetic:true}),registryHash=await digest(CATALOG);
  async function issue(product) {
    const binding=await bindingFor(product),issued=now(),expires=new Date(Date.parse(issued)+3600000).toISOString().replace(/\.\d{3}Z$/,'Z');
    const receipts=[];
    for(const destination of ['local_view','local_export'])for(const gate of Object.keys(KINDS)) {
      const payload={schema:'un.product-decision.v1',contract_version:'1.0.0',id:`test-${destination}-${gate}`,key_id:key.key_id,gate,verdict:'pass',section_id:'all',destination,binding,issued_at:issued,expires_at:expires,evidence_kind:KINDS[gate],evidence_sha256:await digest({test_only:gate})};
      receipts.push({payload,signature:sign(null,Buffer.from(canonical(payload)),privateKey).toString('base64')});
    }
    ledger.set(binding.product_sha256,{receipts:copy(receipts),commitment:await receiptSetDigest(receipts),product:copy(product)});
    return receipts;
  }
  async function resolve(input) {
    const s=copy(input);if(Object.keys(s).sort().join(',')!=='country,meeting,page,period,topic')throw new Error('selection_fields');
    if(!['explore','meetings'].includes(s.page)||s.country!==null&&!CATALOG.countries.some(x=>x.id===s.country)||s.topic!==null&&!CATALOG.topics.some(x=>x.id===s.topic))throw new Error('selection');
    const meeting=CATALOG.meetings.find(m=>m.id===s.meeting);
    if(s.meeting!==null&&!meeting||s.page==='meetings'&&!meeting||s.page==='explore'&&s.meeting!==null)throw new Error('meeting');
    const requested={countries:s.country?[s.country]:[],topic:s.topic,period:s.period,meeting:s.meeting,baseline:null};
    const period=s.period || (meeting?{start:meeting.date,end:meeting.date}:CATALOG.period);
    const query={schema:'un.research-query.v1',contract_version:'1.0.0',intent:s.page==='meetings'?'meeting':s.country?'country':s.topic?'topic':'trends',timezone:'America/New_York',entity_role:'speaking_country',requested,resolved:{...copy(requested),period:copy(period),baseline:'USA',forum:'synthetic_preview',source_mode:'synthetic'},defaulted_fields:s.period===null?['period','baseline']:['baseline'],entity_registry_sha256:registryHash};
    validateQuery(query);
    const cacheKey=canonical(query);if(cache.has(cacheKey))return copy(cache.get(cacheKey));resolveCount++;
    if(cache.size>=128)throw new Error('test_cache_limit');
    const configuration=await digest({recipe:'invented_record_description',version:'1',model_runs:0});
    const capability={schema:'un.product-capability.v1',contract_version:'1.0.0',id:'u1_synthetic_description',intents:['country','topic','meeting','trends'],recipe:{id:'invented_record_description',version:'1',configuration_sha256:configuration,representation_id:null,checkpoint_sha256:null},regime:{source_schemas:['un.parallel-analysis.v1'],source_modes:['synthetic'],units:['synthetic'],languages:['en'],genres:['invented'],max_days:31,max_frame:600,max_display:600},claims:['descriptive'],destinations:['local_view','local_export'],extra_gates:[],fallback:null,benchmark_sha256:null};
    const inside=m=>m.date>=period.start&&m.date<=period.end&&(!s.meeting||s.meeting===m.id);
    const scopeMeetings=CATALOG.meetings.filter(inside),scope=RECORDS.filter(r=>scopeMeetings.some(m=>m.id===r.meeting));
    const selected=scope.filter(r=>(!s.country||(r.country===s.country&&r.capacity==='national'))&&(!s.topic||s.topic===r.topic));
    const unavailable=period.start<CATALOG.period.start||period.end>CATALOG.period.end;
    const readerFailed=s.meeting==='03';
    const missing=scopeMeetings.some(m=>m.id==='1')?1:0;
    const rows=unavailable||readerFailed?[]:selected;
    const popHash=await digest({query,ids:selected.map(x=>x.id),missing});
    const resultHash=await digest({description:rows.map(x=>x.id),model_runs:0});
    const ref={schema:'un.parallel-analysis.v1',artifact_sha256:resultHash,pointer:'/synthetic_description'};
    const evidence=[];
    for(const r of rows)evidence.push({id:r.id,ref:copy(ref),source_id:'invented-'+r.id,text_sha256:await textDigest(r.text),raw_sha256:await textDigest(r.text),hash_basis:'synthetic_utf8',parent_id:'parent-'+r.id,meeting_id:r.meeting,source_family_id:'family-'+r.meeting,start:0,end:[...r.text].length,parent_length:[...r.text].length,country:r.country,capacity:r.capacity});
    const findings=rows.map(r=>({id:'finding-'+r.id,claim:'descriptive',template:'synthetic_only',result:copy(ref),support:[r.id],contrary:[],contrary_search:'not_run',country:r.capacity==='national'?r.country:null}));
    const dataState=unavailable?'withheld':readerFailed?'failed':rows.length?'available':'empty';
    const reason=unavailable?'source_unavailable':readerFailed?'synthetic_reader_failure':rows.length?null:'no_matches';
    const planned=unavailable?0:readerFailed?1:rows.length?1:0,succeeded=rows.length?1:0,failed=readerFailed?1:0;
    const eligible=unavailable?0:readerFailed?2:selected.length;
    const population={id:'synthetic_selection',sha256:popHash,unit:'synthetic',weighting:'equal_record',dependence_unit:'meeting',frame:unavailable?0:readerFailed?2:scope.length+missing,eligible,excluded:unavailable||readerFailed?0:scope.length-selected.length,missing:unavailable||readerFailed?0:missing,unverified:0};
    const sections=[{id:'overview',kind:'overview',claim:'descriptive',data_state:dataState,reason,finding_ids:findings.map(f=>f.id),result:findings.length?copy(ref):null,display:null,uncertainty:'unavailable'}];
    // No PR82/92 numerical outputs, coordinates or fabricated comparison receipts are consumed.
    if(rows.length)for(const [id,kind] of [['comparison','comparison'],['changes','trend']])sections.push({id,kind,claim:'descriptive',data_state:'withheld',reason:'trajectory_not_integrated',finding_ids:[],result:null,display:null,uncertainty:'unavailable'});
    const product={schema:'un.evidence-product.v1',contract_version:'1.0.0',id:'u1-invented-'+(await digest(query)).slice(0,12),run_id:'description-'+(await digest(query)).slice(0,12),fixture_kind:'synthetic',publication_eligible:false,evaluation_role:'engineering_only',query_sha256:await digest(query),capability_sha256:await digest(capability),upstream:{schema:'un.parallel-analysis.v1',source_sha256:unavailable?null:sourceHash,source_missing_reason:unavailable?'source_unavailable':null,source_hash_basis:'synthetic_utf8',selection_sha256:popHash,inventory_sha256:sourceHash,review_sha256:null,entity_registry_sha256:registryHash,language:'en',genre:'invented'},fit_population:population,display_population:{parent_sha256:popHash,sha256:popHash,count:rows.length,selection_only:true},fit:{representation_id:null,configuration_sha256:configuration,checkpoint_sha256:null,result_sha256:resultHash,planned,attempted:planned,succeeded,failed,skipped:0,ledger:planned?[{id:'describe',model_id:'no_model_description',family_id:'description',seed:0,status:failed?'failed':'succeeded',reason:failed?'synthetic_reader_failure':null}]:[],assignments:{eligible,assigned:rows.length,unassigned:0,not_fitted:eligible-rows.length}},provenance:{base_sha:C0_COMMIT,worker_sha:ZERO,effective_tree_sha:ZERO,adapter_version:'1.0.0',runtime:'fictional_fixture_not_a_commit_receipt'},evidence,findings,sections};
    await validateProduct(product,query,capability);
    const bundle={query,capability,product,receipts:await issue(product)};ledger.get(await digest(product)).bundle=copy(bundle);cache.set(cacheKey,copy(bundle));return copy(bundle);
  }
  async function getTrust(id) {const entry=ledger.get(id);return {keys:entry&&!revoked?[copy(key)]:[],commitment:entry?.commitment??null,revision:String(revision),now:now()};}
  async function getEvidence(id,eid){const entry=ledger.get(id);if(revoked||!entry||!entry.product.evidence.some(e=>e.id===eid))throw new Error('denied');const trust=await getTrust(id);const view=await assess({...entry.bundle,receipts:entry.receipts,trustedKeys:trust.keys,trustedReceiptSetSha256:trust.commitment,now:trust.now,destination:'local_view'});if(!view.sections.some(s=>s.evidence.some(e=>e.id===eid)))throw new Error('denied');const r=RECORDS.find(x=>x.id===eid);return {fixture_kind:'synthetic',id:eid,source_id:'invented-'+eid,meeting_id:r.meeting,text:r.text};}
  async function veto(id){const entry=ledger.get(id);if(!entry)throw new Error('id');const payload={...copy(entry.receipts.find(r=>r.payload.gate==='source'&&r.payload.destination==='local_view').payload),id:'synthetic-veto-'+revision,verdict:'fail'};entry.receipts.push({payload,signature:sign(null,Buffer.from(canonical(payload)),privateKey).toString('base64')});entry.commitment=await receiptSetDigest(entry.receipts);revision++;}
  return Object.freeze({resolve,getTrust,getEvidence,catalog:async()=>copy(CATALOG),get resolveCount(){return resolveCount;},
    revoke(){revoked=true;revision++;}, expire(){offset=7200000;revision++;},reset(){revoked=false;offset=0;revision++;ledger.clear();cache.clear();},veto,
    async fullBundle(bundle){const b=copy(bundle);b.receipts=copy(ledger.get(await digest(b.product)).receipts);return b;}
  });
}
