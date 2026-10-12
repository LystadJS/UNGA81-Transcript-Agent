'use strict';

/*
 * Read-only W2 -> accepted W5/W6 panel projection.
 * W6 currently computes a simple mean of per-family integer count ratios.
 * That is NOT generally equal to W2's planned-weight conditional association.
 * Render values only when every pair is mathematically equivalent; otherwise
 * return an explicit withheld panel (never a plausible but incorrect heatmap).
 */
const assert=require('node:assert/strict');
const W2=require('../../consensus/consensus.cjs');
const {fromW1}=require('./bridge.cjs');

const check=(ok,message)=>assert.ok(ok,'w1-w2-viz: '+message);
const intersect=(a,b)=>a.filter(x=>b.includes(x));
function panelForW6(bundle){
  check(bundle&&bundle.audit?.schema==='un.w1-w2-consensus-bridge.v1' &&
    bundle.audit.publication_eligible===false && bundle.audit.source_split==='synthetic',
    'W1/W2 bridge audit required');
  const {projected_envelope:original,consensus:out,interchange:e}=bundle;
  W2.validateEnvelope(original);
  W2.validateEnvelope(e);
  W2.validateConsensus(out);
  check(e.producer.workstream_id==='W2'&&
    e.producer.fixture_kind==='synthetic'&&
    original.upstream.source_sha256===e.upstream.source_sha256 &&
    original.upstream.selection_sha256===e.upstream.selection_sha256 &&
    original.upstream.source_hash_basis===e.upstream.source_hash_basis,
    'source/selection provenance differs between W1 and W2');
  check(e.observations.every(o=>o.source_url===null &&
    !Object.hasOwn(o,'text')), 'public research visualization accepts synthetic, text-free source rows only');
  const originalRows=new Map(original.results.map(x=>[
    x.model_id+'\u001f'+x.observation_id,x
  ]));
  const families=out.family_weight_audit;
  const allModels=families.flatMap(f=>f.records);
  const full=new Set(allModels.map(x=>x.model_id));
  check(allModels.length===original.models.length &&
    full.size===allModels.length && allModels.every(r=>r.resample_type==='baseline' &&
      r.resample_id==='baseline'), 'do not convert W1 refit summaries into pairwise votes');
  const eligible=e.observations.filter(o=>
    o.source_status==='available'&&o.exclusion_reasons.length===0);
  check(eligible.length===e.cohort.eligible &&
    eligible.length===out.observation_ids.length &&
    eligible.every(o=>out.observation_ids.includes(o.id)),
    'W2 output and W6 eligible source population differ');
  const reference=e.models[0];
  const identity={
    source_schema:e.upstream.source_schema,source_hash_basis:e.upstream.source_hash_basis,
    source_sha256:e.upstream.source_sha256,selection_sha256:e.upstream.selection_sha256,
    unit:e.cohort.unit,weighting:e.cohort.weighting,
    representation_id:reference.representation_id,
    representation_version:reference.representation_version,
    observation_refs:eligible.map(o=>({id:o.id,text_sha256:o.text_sha256}))
  };
  const frame=e.cohort.total_in_frame;
  const coverage={frame,eligible:e.cohort.eligible,included:eligible.length,
    excluded:e.coverage.excluded,missing:e.coverage.unavailable_sources};
  const warnings=[
    'Synthetic engineering evidence only: co-assignment is not agreement, stance, a coalition or statistical significance.',
    'W1 grouped-refit stability is separate; W2 pairwise LOO/bootstrap uncertainty is not estimated.',
    'W6 displays equal-family integer count ratios; values are drawn only when they equal W2 weighted conditional association for every pair.',
    'The identity-join protocol compares original hard labels across PCA, LSA and invented semantic geometry, not independent source replication.'
  ];
  const panel={
    kind:'consensus',status:'ready',reason:null,
    identity,measure:'Equal-family mean of pair co-assignment rates, confirmed equal to W2 planned-weight conditional association for each displayed pair; not a diplomatic probability.',
    coverage,warnings,observation_ids:out.observation_ids.slice(),pairs:[]
  };
  const withholding=reason=>{
    panel.status='withheld';
    panel.reason=reason;
    panel.coverage.included=0;
    panel.observation_ids=[];
    panel.pairs=[];
    return {status:'withheld',panel,envelope:e,comparability:{
      compared_pairs:0,withheld_reason:reason,denominator_kind:'none_visualized'}};
  };
  if(eligible.length>35)
    return withholding('W6 permits at most 35 visible pair-matrix observations. Full frame retained; silent truncation prohibited.');
  let compared=0,maxError=0;
  const unstable=new Set(out.ambiguous_members.map(x=>x.observation_id));
  for(const pair of out.pairs.filter(p=>p.observation_a!==p.observation_b)){
    const items=[];
    let together=0,eligibleCount=0,failedCount=0;
    for(const family of families){
      const contributions=family.records.map(f=>{
        const a=originalRows.get(f.model_id+'\u001f'+pair.observation_a);
        const b=originalRows.get(f.model_id+'\u001f'+pair.observation_b);
        check(a&&b,'model result missing original pair');
        const both=a.status==='assigned'&&b.status==='assigned';
        return {both,together:both&&a.cluster===b.cluster,failed:!f.fitting_success};
      });
      const available=contributions.filter(x=>x.both);
      const matches=available.filter(x=>x.together).length;
      const failed=contributions.filter(x=>x.failed).length;
      items.push({family:family.method_family,together:matches,
        eligible:available.length,failed});
      together+=matches;eligibleCount+=available.length;failedCount+=failed;
    }
    check(eligibleCount===pair.assigned_both_count &&
      together===pair.coassigned_count &&
      failedCount===pair.failed_fit_count &&
      allModels.length===pair.planned_count,
      'original fit IDs and pairwise W2 ledger disagree');
    const active=items.filter(x=>x.eligible>0);
    const displayed=active.length?
      active.reduce((sum,x)=>sum+x.together/x.eligible,0)/active.length:null;
    const actual=pair.association;
    if(displayed===null&&actual!==null ||
      displayed!==null&&actual===null ||
      displayed!==null&&Math.abs(displayed-actual)>1e-9)
      return withholding('W6 simple family-mean is not equivalent to the W2 weighted pair association. Do not misstate the numerators or denominators; a W2-native visualization contract is required.');
    if(actual!==null) {
      compared++;
      maxError=Math.max(maxError,Math.abs(displayed-actual));
    }
    panel.pairs.push({
      a:pair.observation_a,b:pair.observation_b,
      families:items,
      missing_reason:actual===null?'No joint hard assignments across included baseline fits':null,
      unstable:unstable.has(pair.observation_a)||unstable.has(pair.observation_b)
    });
  }
  return {status:'ready',panel,envelope:e,
    comparability:{compared_pairs:compared,max_absolute_fraction_difference:maxError,
      withheld_reason:null,denominator_kind:'W2 weighted conditional association = W6 equal-family ratio on every synthetic pair'}};
}
module.exports={panelForW6};
