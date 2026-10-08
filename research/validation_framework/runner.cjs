'use strict';
// Read-only adapter around existing browser numerical kernels. Never fit on UMAP/MDS displays.
const C=require('../../site/cluster-core.js');
const A=require('../../site/analysis-core.js');
const M=require('./metrics.cjs');
const F=require('./frame.cjs');

function assert(ok,msg){if(!ok)throw Error(msg);}
function options(spec){
  assert(spec&&typeof spec.id==='string'&&spec.id.length>0,'Unique model ID required.');
  assert(['pca','lsa','minilm_pca'].includes(spec.representation),'Use lexical PCA, lexical LSA, or pinned MiniLM + PCA.');
  const validated=C.options({representation:spec.representation==='minilm_pca'?'pca':spec.representation,
    algorithm:spec.algorithm, k:spec.k??3,components:spec.components??4,seed:spec.seed??42,
    linkage:spec.linkage??'ward',gmm:spec.gmm||{},hdbscan:spec.hdbscan||{},
    stability:{enabled:false},mds:{enabled:false}});
  return {...validated,id:spec.id,representation_requested:spec.representation};
}
function geometry(rows,spec,representation){
  if(spec.representation_requested==='minilm_pca'){
    assert(representation,'Pinned MiniLM representation is not available.');
    const lookup=new Map(representation.rows.map(o=>[o.id,o.vector]));
    const vectorLength=representation.rows[0].vector.length;
    const dense=rows.map(row=>{
      const x=lookup.get(row.id);assert(x&&x.length===vectorLength,'Pinned cache does not cover this exact population.');
      return new Map(x.map((v,i)=>[String(i),v]));
    });
    return C.represent(dense,spec.components,'pca',false);
  }
  assert(rows.every(r=>typeof r.text==='string'&&r.text.length>0),'Lexical refitting requires locally authorized source text.');
  const vectors=A.tfidf(rows).vectors;
  assert(vectors.length===rows.length,'Unexpected TF-IDF output size.');
  if(vectors.some(v=>v.size===0))return {rank:0,scores:[],reason:'At least one row has no surviving terms; refuse population change.'};
  return C.represent(vectors,spec.components,spec.representation_requested,false);
}
async function fitOne(rows,spec,representation){
  const baseline={status:'skipped',assignments:null,memberships:null,strengths:null,warnings:[],
    convergence:null,diagnostics:{},reason:null,attempted_fit:0,successful_fit:0,failed_fit:0};
  if(rows.length<4){baseline.reason='Fewer than four eligible passages.';return baseline;}
  if(spec.algorithm!=='hdbscan'&&spec.k>=rows.length){baseline.reason='k is not smaller than the population size.';return baseline;}
  let attempted=false;
  try{
    const z=geometry(rows,spec,representation);
    if(!z.rank){baseline.reason=z.reason||'Representation has no measurable rank or distinct variation.';return baseline;}
    attempted=true;
    const fitted=await C.fitPartition(z.scores,spec);
    if(fitted.skipped)return {...baseline,status:'failed',attempted_fit:1,failed_fit:1,reason:fitted.skipped,
      diagnostics:fitted.diagnostics||{},convergence:false};
    const assignments=fitted.labels.map(label=>label+1);
    assert(assignments.length===rows.length&&assignments.every(x=>Number.isInteger(x)&&x>=0),'Invalid upstream hard assignments.');
    const memberships=fitted.responsibilities||null,strengths=fitted.strengths||null;
    if(memberships)assert(memberships.length===rows.length&&memberships.every(v=>v.every(x=>Number.isFinite(x)&&x>=0)&&Math.abs(v.reduce((a,b)=>a+b,0)-1)<1e-6),'Invalid upstream conditional responsibilities.');
    if(strengths)assert(strengths.length===rows.length&&strengths.every(x=>Number.isFinite(x)&&x>=0&&x<=1),'Invalid density membership strengths.');
    const diagnostics=fitted.diagnostics||{};
    return {status:'fitted',assignments,memberships,strengths,warnings:diagnostics.warnings||[],
      convergence:fitted.converged===true,attempted_fit:1,successful_fit:1,failed_fit:0,reason:null,
      rank:z.rank,retained_dimensions:z.scores[0].length,
      diagnostics:{
        algorithm:spec.algorithm,converged_starts:diagnostics.converged_starts??null,
        iterations:diagnostics.iterations??null,inertia:diagnostics.inertia??null,
        total_distance:diagnostics.total_distance??null,cut_height:diagnostics.cut_height??null,
        tied_cut:diagnostics.tied_cut??null,assigned_count:assignments.filter(x=>x>0).length,
        unassigned_count:assignments.filter(x=>x===0).length,
        log_likelihood:diagnostics.log_likelihood??null,
        parameter_count:diagnostics.parameter_count??null,
        near_floor_dimensions:diagnostics.near_floor_dimensions??null,
        mean_entropy:diagnostics.mean_entropy??null,
        hdbscan_selection_stability:diagnostics.selection_stability??null,
        selected_nodes:diagnostics.selected_nodes?.length??null,
        min_cluster_size:diagnostics.min_cluster_size??null
      }};
  }catch(e){
    return {...baseline,status:'failed',reason:String(e.message||e).slice(0,300),
      convergence:false,attempted_fit:attempted?1:0,failed_fit:attempted?1:0,
      warnings:['Failed fit or preprocessing is recorded; no fallback assignment used.']};
  }
}
function representationRecord(cohort,spec,saved){
  if(spec.representation_requested==='minilm_pca'){
    assert(saved&&saved.kind==='pinned-minilm'||saved&&saved.kind==='synthetic-saved'&&cohort.split==='synthetic',
      'MiniLM representation requires a verified pinned development cache or synthetic fixture.');
    return {id:saved.id,version:saved.version,model_identity:saved.identity_sha256,
      basis:'Pinned MiniLM vectors; PCA refit for each group; no display-coordinate fitting'};
  }
  return {id:'lexical-'+spec.representation_requested+'-'+cohort.selection_sha256.slice(0,16)+'-c'+spec.components,
    version:'site/analysis-core.js:tfidf+site/cluster-core.js:representation',
    model_identity:F.digest([cohort.selection_sha256,spec.representation_requested,spec.components]),
    basis:'Refit TF-IDF vocabulary and '+spec.representation_requested.toUpperCase()+' on eligible selected text'};
}
async function run(frame,settings,{saved=null,group_units=['meeting','affiliation'],replicates=20,fraction=0.8,group_seed=31415}={}){
  const cohort=F.validateFrame(frame);
  cohort.split=frame.split;
  assert(Array.isArray(settings)&&settings.length>0&&settings.length<=20,'Specify 1–20 model settings.');
  const specs=settings.map(options);
  assert(new Set(specs.map(x=>x.id)).size===specs.length,'Duplicate model identity.');
  if(saved){F.alignScores(cohort,saved);
    if(frame.split==='development')assert(saved.kind==='pinned-minilm'&&saved.verified_pinned_cache===true,'Development vectors must come from the pinned-cache bridge.');
  }
  for(const s of specs)if(s.representation_requested==='minilm_pca')assert(saved,'MiniLM model requested without loaded pinned vectors.');
  assert(Array.isArray(group_units)&&group_units.every(u=>['meeting','affiliation'].includes(u)),'Unknown resampling grouping.');
  const schedules=Object.fromEntries([...new Set(group_units)].map(u=>[u,F.schedule(cohort.eligible,u,replicates,fraction,group_seed)]));
  const fitRecords=[],failureLedger=[],modelReports=[];
  for(const spec of specs){
    const rep=representationRecord(cohort,spec,saved),main=await fitOne(cohort.eligible,spec,saved);
    const record={model_id:spec.id,method:spec.algorithm,parameters:spec,seed:spec.seed,
      representation_id:rep.id,representation_version:rep.version,representation_identity_sha256:rep.model_identity,
      representation_basis:rep.basis,population_hash:cohort.population_hash,selection_sha256:cohort.selection_sha256,
      source_sha256:frame.source_sha256,observation_ids:cohort.eligible.map(r=>r.id),
      observation_hashes:cohort.eligible.map(r=>r.text_sha256),
      ...main};
    fitRecords.push(record);
    if(main.status!=='fitted')failureLedger.push({model_id:spec.id,attempt:0,status:main.status==='failed'?'failed':'skipped',reason:main.reason,seed:spec.seed,source_group:null});
    const refs={};
    for(const unit of Object.keys(schedules)){
      const plan=schedules[unit],runs=[];
      if(plan.status==='skipped'){
        failureLedger.push({model_id:spec.id,attempt:0,status:'skipped',reason:unit+': '+plan.reason,seed:group_seed,source_group:unit});
      }else if(main.status==='fitted')for(const sample of plan.samples){
        const rows=sample.indices.map(i=>cohort.eligible[i]);
        const child=await fitOne(rows,{...spec,seed:(spec.seed+Math.imul(sample.attempt,0x85ebca6b))>>>0},saved);
        const observationIds=rows.map(r=>r.id);
        const meta={attempt:sample.attempt,seed:(spec.seed+Math.imul(sample.attempt,0x85ebca6b))>>>0,
          groups:sample.group_indices,selected:sample.selected_count,out_of_sample:sample.excluded_count,
          observation_ids:observationIds,status:child.status,attempted_fit:child.attempted_fit,
          successful_fit:child.successful_fit,failed_fit:child.failed_fit,
          assigned:child.assignments?.filter(v=>v>0).length??0,
          unassigned:child.assignments?.filter(v=>v===0).length??0,
          reason:child.reason,convergence:child.convergence,warnings:child.warnings,
          comparison:child.status==='fitted'?M.evaluateAssignments(sample.indices.map(i=>main.assignments[i]),child.assignments):null};
        if(child.status!=='fitted')failureLedger.push({model_id:spec.id,attempt:sample.attempt,
          status:child.status==='failed'?'failed':'skipped',reason:unit+': '+child.reason,seed:meta.seed,source_group:unit});
        runs.push(meta);
      }else{
        failureLedger.push({model_id:spec.id,attempt:0,status:'skipped',reason:unit+': full fit unavailable',seed:group_seed,source_group:unit});
      }
      const used=runs.filter(r=>r.status==='fitted');
      refs[unit]={schedule_sha256:plan.schedule_sha256??null,groups:plan.groups,
        planned:plan.attempted,attempted:runs.length,successful:used.length,
        failed:runs.filter(r=>r.status==='failed').length,skipped:runs.filter(r=>r.status==='skipped').length,
        unique_group_samples:plan.unique_group_samples??0,
        ari:M.summarize(used.map(r=>r.comparison.ari)),
        ami:M.summarize(used.map(r=>r.comparison.adjusted_mutual_information)),
        pairwise_consistency:M.summarize(used.map(r=>r.comparison.pairwise_assignment_consistency)),
        assignment_status_agreement:M.summarize(used.map(r=>r.comparison.assignment_status_agreement)),
        assessable_ari:used.filter(r=>r.comparison.ari!==null).length,
        not_assessable_ari:used.filter(r=>r.comparison.ari===null).length,
        runs,reason:plan.reason??null};
    }
    modelReports.push({model_id:spec.id,fit_status:main.status,source_audit:F.auditSources(cohort.eligible,main.assignments),group_stability:refs});
  }
  const comparisons=[];
  for(let i=0;i<fitRecords.length;i++)for(let j=i+1;j<fitRecords.length;j++) comparisons.push(M.compareFits(fitRecords[i],fitRecords[j]));
  const cases=[];
  for(const pair of comparisons){
    if(pair.status!=='descriptive'||cases.length>=12)continue;
    const left=fitRecords.find(r=>r.model_id===pair.left),right=fitRecords.find(r=>r.model_id===pair.right);
    for(let i=0;i<cohort.eligible.length&&cases.length<12;i++)for(let j=0;j<i&&cases.length<12;j++){
      const [a,b]=[left.assignments[i],left.assignments[j]], [c,d]=[right.assignments[i],right.assignments[j]];
      if(a>0&&b>0&&c>0&&d>0&&(a===b)!==(c===d)){
        const pointers=[j,i].map(k=>{const row=cohort.eligible[k];return {observation_id:row.id,text_sha256:row.text_sha256,
          source_url:row.source_url??null,json_pointer:row.json_pointer??null,start:row.start??null,end:row.end??null,
          meeting_id:row.meeting_id??null,parent_id:row.parent_id??null};});
        cases.push({left:pair.left,right:pair.right,case:'discordant_pair_coassignment',
          left_coassigned:a===b,right_coassigned:c===d,source_pointers:pointers,
          verification:frame.split==='synthetic'?'synthetic':'provisional',
          interpretation:'Source-linked cluster disagreement, not conflicting national positions.'});
      }
    }
  }
  return {schema:'un.source-aware-validation.v1',evaluation_role:'engineering_only',publication_eligible:false,
    frame:{source_schema:frame.source_schema,source_engine:frame.source_engine,source_hash_basis:frame.source_hash_basis,
      source_sha256:frame.source_sha256,selection_sha256:cohort.selection_sha256,population_hash:cohort.population_hash,
      split:frame.split,unit:frame.unit??'passage',inventory_meetings:cohort.inventory_meetings,observations_total:cohort.rows.length,
      eligible:cohort.eligible.length,excluded:cohort.excluded.length,eligible_observation_ids:cohort.eligible.map(x=>x.id)},
    fit_records:fitRecords,model_reports:modelReports,comparisons,source_linked_cases:cases,
    source_audit:F.auditSources(cohort.eligible),schedules,failure_ledger:failureLedger,
    limitations:['Stability under grouped omissions is descriptive, not a null-calibrated significance test.',
      'No latent cluster, embedding similarity or coassignment establishes diplomatic stance or governmental alignment.',
      'Country/affiliation metadata is not an authenticated speaker or vote.',
      'Lexical group refits rebuild vocabulary/IDF; pinned MiniLM vectors remain fixed, with PCA recomputed.',
      'No UMAP or MDS display coordinates are used for fitting or validation.'],
    _internal_frame:cohort.rows};
}
function publicAggregate(out){
  assert(out.frame.split==='synthetic','Public export refused: private development observations and evidence must not be published.');
  const trim=out.fit_records.map(f=>({model_id:f.model_id,method:f.method,status:f.status,assigned:f.assignments?.filter(x=>x>0).length??0,
    unassigned:f.assignments?.filter(x=>x===0).length??0,attempted_fits:f.attempted_fit,successful_fits:f.successful_fit,
    failed_fits:f.failed_fit,reason:f.reason,representation_id:f.representation_id}));
  return {schema:'un.source-validation.public-aggregate.v1',fixture_kind:'synthetic',publication_eligible:false,
    observations_total:out.frame.observations_total,eligible:out.frame.eligible,excluded:out.frame.excluded,
    models:trim,comparisons:out.comparisons,group_stability:out.model_reports.map(m=>({model_id:m.model_id,
      groups:Object.fromEntries(Object.entries(m.group_stability).map(([u,s])=>[u,
        {groups:s.groups,planned:s.planned,attempted:s.attempted,successful:s.successful,failed:s.failed,skipped:s.skipped,
          assessable_ari:s.assessable_ari,ari:s.ari,ami:s.ami}]))})),
    cases_count:out.source_linked_cases.length,failure_count:out.failure_ledger.length,
    failure_ledger:out.failure_ledger,limitations:out.limitations};
}
module.exports={run,fitOne,options,geometry,publicAggregate};
