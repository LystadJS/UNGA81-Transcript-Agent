'use strict';
// Versioned adapter; existing upstream schemas and frozen research sources are untouched.
const fs=require('node:fs');
const path=require('node:path');
const F=require('./frame.cjs');
const {combinations2}=require('./metrics.cjs');

function assert(ok,why){if(!ok)throw Error(why);}
const CODE_SHA=F.digest(fs.readFileSync(path.join(__dirname,'runner.cjs'),'utf8'));
function observation(o,unit){
  return {id:o.id,text_sha256:o.text_sha256??null,parent_id:o.parent_id??null,
    parent_text_sha256:o.parent_text_sha256??null,meeting_id:o.meeting_id??null,
    speech_id:o.speech_id??null,source_family_id:o.source_family_id??null,date:o.date??null,
    country:o.country??o.affiliation??null,source_url:o.source_url??null,
    json_pointer:o.json_pointer??null,start:o.start??null,end:o.end??null,
    unit:o.unit??unit,review_status:o.review_status??'not_applicable',
    exclusion_reasons:o.exclusion_reasons??[],source_status:o.source_status,missing_reason:o.missing_reason??null};
}
function model(f,frame){
  return {model_id:f.model_id,method_family:'unsupervised_partition',method:f.method,
    representation_id:f.representation_id,representation_version:f.representation_version,
    fit_version:'source-validation-1.0.0',fit_split:frame.split,
    parameters_sha256:F.digest(f.parameters),training_selection_sha256:frame.selection_sha256,
    diagnostic_basis:'Original retained fit scores, group-preserving omissions; never 2-D displays'};
}
function resultRow(f,o,index,eligible){
  const status=!eligible?'excluded':f.status!=='fitted'?'not_fitted':f.assignments[index]>0?'assigned':'unassigned';
  const cluster=status==='assigned'?f.assignments[index]:status==='unassigned'?0:null;
  const kind=status!=='assigned'&&status!=='unassigned'?'none':
    f.method==='gmm'?'gmm_responsibility':f.method==='hdbscan'?'hdbscan_strength':'none';
  return {model_id:f.model_id,observation_id:o.id,status,cluster,membership_kind:kind,
    memberships:kind==='gmm_responsibility'?f.memberships[index]:null,
    membership_strength:kind==='hdbscan_strength'?f.strengths[index]:null,
    representation_basis_id:f.representation_id,
    reason:status==='excluded'?(o.exclusion_reasons||[]).join('; ')||o.missing_reason||'Excluded from declared population':
      status==='not_fitted'?f.reason:status==='unassigned'?'Density noise/unassigned':null};
}
function diagnostic(model_id,name,value,denominator,unit,status='descriptive',reason=null){
  return {model_id,name,value:Number.isFinite(value)||typeof value==='string'?value:null,
    denominator,unit,status,reason};
}
function toInterchangeV1(out){
  assert(out&&out.schema==='un.source-aware-validation.v1','Unexpected runner result.');
  const rows=out._internal_frame;
  assert(Array.isArray(rows)&&rows.length===out.frame.observations_total,'Original frame is required in private process memory.');
  const eligible=rows.filter(o=>o.source_status==='available'&&!(o.exclusion_reasons||[]).length);
  const excluded=rows.filter(o=>o.source_status!=='available'||(o.exclusion_reasons||[]).length);
  assert(eligible.length===out.frame.eligible,'Changed eligible cohort.');
  const results=[],coverage=[],diagnostics=[];
  for(const f of out.fit_records){
    eligible.forEach((o,i)=>results.push(resultRow(f,o,i,true)));
    excluded.forEach(o=>results.push(resultRow(f,o,-1,false)));
    const rep=out.model_reports.find(m=>m.model_id===f.model_id);
    const groupRuns=Object.values(rep.group_stability).flatMap(s=>s.runs);
    coverage.push({model_id:f.model_id,eligible:eligible.length,
      assigned:f.status==='fitted'?f.assignments.filter(x=>x>0).length:0,
      unassigned:f.status==='fitted'?f.assignments.filter(x=>x===0).length:0,
      not_fitted:f.status==='fitted'?0:eligible.length,excluded:excluded.length,
      attempted_fits:f.attempted_fit+groupRuns.reduce((s,r)=>s+r.attempted_fit,0),
      successful_fits:f.successful_fit+groupRuns.reduce((s,r)=>s+r.successful_fit,0),
      failed_fits:f.failed_fit+groupRuns.reduce((s,r)=>s+r.failed_fit,0),
      skipped_fits:(f.status==='skipped'?1:0)+groupRuns.filter(r=>r.status==='skipped').length});
    diagnostics.push(diagnostic(f.model_id,'assigned_coverage',
      f.status==='fitted'?f.assignments.filter(x=>x>0).length/eligible.length:null,eligible.length,'eligible_observation'));
    for(const [unit,s] of Object.entries(rep.group_stability)){
      diagnostics.push(diagnostic(f.model_id,unit+'_stability_ari_mean',s.ari.mean,s.ari.n,'successful_ari_refit',
        s.ari.n?'descriptive':'inconclusive',s.ari.n?null:s.reason||'No assessable comparisons'));
      diagnostics.push(diagnostic(f.model_id,unit+'_attempted_fits',s.attempted,s.planned,'scheduled_group_refit'));
      diagnostics.push(diagnostic(f.model_id,unit+'_failed_fits',s.failed,s.attempted,'attempted_group_refit'));
    }
  }
  for(const p of out.comparisons){
    if(!p.metrics)continue;
    for(const metric of ['ari','adjusted_mutual_information','pairwise_assignment_consistency','assignment_status_agreement']){
      const denom=metric==='pairwise_assignment_consistency'?p.metrics.pair_opportunities_assigned_both:
        metric==='assignment_status_agreement'?p.metrics.observations:p.metrics.assigned_both;
      diagnostics.push(diagnostic(null,p.left+'__'+p.right+'__'+metric,p.metrics[metric],denom,
        metric.startsWith('pairwise')?'pair':'observation',
        p.metrics[metric]===null?'inconclusive':'descriptive',
        p.metrics[metric]===null?p.metrics.reason:null));
    }
  }
  diagnostics.push(diagnostic(null,'source_concentration_largest_meeting_share',
    out.source_audit.largest_meeting_share,eligible.length,'eligible_observation'));
  diagnostics.push(diagnostic(null,'duplicate_text_groups',out.source_audit.duplicate_text_groups,
    eligible.length,'eligible_observation'));
  const evidence=[];
  const unique=new Set();
  for(const c of out.source_linked_cases)for(const p of c.source_pointers){
    const key=c.left+'|'+c.right+'|'+p.observation_id;
    if(unique.has(key))continue;unique.add(key);
    evidence.push({observation_id:p.observation_id,source_url:p.source_url,json_pointer:p.json_pointer,
      start:p.start,end:p.end,role:'ambiguous',proposition_id:null,verification:c.verification});
  }
  const envelope={schema:'un.parallel-analysis.v1',contract_version:'1.0.0',
    producer:{workstream_id:'W1',adapter_version:'source-validation-1.0.0',code_sha256:CODE_SHA,
      runtime:process.version,generated_at:new Date().toISOString(),
      fixture_kind:out.frame.split==='synthetic'?'synthetic':'private_development'},
    upstream:{source_schema:out.frame.source_schema,source_engine:out.frame.source_engine,
      source_hash_basis:out.frame.source_hash_basis,source_sha256:out.frame.source_sha256,
      frame_sha256:null,corpus_sha256:null,selection_sha256:out.frame.selection_sha256,review_sha256:null,missing_reason:null},
    cohort:{split:out.frame.split,population:'same_eligible_source_bound_observations',
      unit:out.frame.unit,selection_policy:'explicit source IDs + original text hash identities',
      weighting:'equal_observation_with_source_group_resampling',
      source_group_unit:'meeting_or_recorded_affiliation_transitive_source_segment',
      duplicate_policy:'retain_and_audit',
      total_in_frame:rows.length,eligible:eligible.length},
    observations:rows.map(r=>observation(r,out.frame.unit)),
    models:out.fit_records.map(f=>model(f,out.frame)),results,
    coverage:{inventory_meetings:out.frame.inventory_meetings,observations_total:rows.length,
      eligible:eligible.length,excluded:excluded.length,unavailable_sources:rows.filter(r=>r.source_status!=='available').length,
      models:coverage,failure_ledger:out.failure_ledger},
    evidence,diagnostics,limitations:out.limitations.map((description,i)=>({code:'validation_limit_'+(i+1),scope:'all',description})),
    publication_eligible:false,evaluation_role:'engineering_only'};
  validateRelational(envelope);
  return envelope;
}
function validateRelational(x){
  assert(x.schema==='un.parallel-analysis.v1'&&x.publication_eligible===false,'Not an engineering-only v1 envelope.');
  const ids=new Set(x.observations.map(x=>x.id)),models=new Set(x.models.map(x=>x.model_id));
  assert(ids.size===x.observations.length&&models.size===x.models.length,'Duplicate source or model identity.');
  assert(x.coverage.eligible+x.coverage.excluded===x.coverage.observations_total,'Population ledger mismatch.');
  assert(x.coverage.observations_total===x.observations.length,'Source rows missing.');
  assert(x.coverage.models.length===x.models.length,'Fit ledger mismatch.');
  for(const m of x.models){
    const cm=x.coverage.models.find(z=>z.model_id===m.model_id);
    const rows=x.results.filter(z=>z.model_id===m.model_id);
    assert(cm&&rows.length===x.observations.length,'Missing result row per model/observation.');
    assert(cm.assigned+cm.unassigned+cm.not_fitted===cm.eligible,'Assigned/unassigned/not-fitted denominator mismatch.');
    assert(cm.attempted_fits===cm.successful_fits+cm.failed_fits,'Attempt ledger mismatch.');
    assert(rows.filter(z=>z.status==='excluded').length===cm.excluded,'Excluded row count mismatch.');
    assert(new Set(rows.map(x=>x.observation_id)).size===rows.length,'Duplicate result row.');
    for(const z of rows){
      assert(ids.has(z.observation_id)&&z.representation_basis_id===m.representation_id,'Source join or representation drift.');
      assert(z.status==='assigned'?z.cluster>0:z.status==='unassigned'?z.cluster===0:z.cluster===null&&z.reason,'Invalid hard label/missingness.');
      if(z.membership_kind==='gmm_responsibility')assert(z.memberships&&Math.abs(z.memberships.reduce((s,v)=>s+v,0)-1)<1e-6,'GMM responsibilities invalid.');
      if(z.membership_kind==='hdbscan_strength')assert(z.membership_strength>=0&&z.membership_strength<=1,'Invalid density strength.');
    }
  }
  assert(x.evidence.every(v=>ids.has(v.observation_id)),'Evidence references unknown source.');
  return true;
}
module.exports={toInterchangeV1,validateRelational};
