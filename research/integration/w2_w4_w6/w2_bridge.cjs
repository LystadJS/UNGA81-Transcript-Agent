'use strict';
/*
 * Coordinator W2 → W6 bridge: metadata-only, no fit/refit or publication.
 * The complete W2 weighted conditional ratio is preserved, NEVER replaced
 * with the original W6 equal-family conditional mean.
 */
const {validateConsensus} = require('../../consensus/consensus.cjs');
const {validateRelational} = require('../../validation_framework/interchange.cjs');
const V = require('../../../site/experimental/evidence-viz/evidence-viz.js');

const check = (ok,msg)=>{if(!ok)throw Error('W2/W6: '+msg);};
const SHA = /^[a-f0-9]{64}$/;
const key = x => JSON.stringify([x.id,x.text_sha256,x.parent_id,x.meeting_id,
  x.source_url,x.json_pointer,x.start,x.end]);
const clone = x => structuredClone(x);

function validateSource(report, envelope) {
  validateConsensus(report);
  check(validateRelational(envelope) === true,'W1 relational validation rejected source.');
  check(report.schema==='un.consensus.v1'&&report.contract_schema==='un.parallel-analysis.v1',
    'Unsupported W2 source type.');
  check(report.publication_eligible===false&&report.evaluation_role==='engineering_only' &&
    envelope.publication_eligible===false&&envelope.evaluation_role==='engineering_only',
    'Publication flag not permitted.');
  check(envelope.producer.workstream_id==='W2'&&
    envelope.producer.fixture_kind==='synthetic'&&
    envelope.cohort.split==='synthetic'&&
    envelope.upstream.source_schema==='synthetic.v1'&&
    envelope.upstream.source_hash_basis==='synthetic',
    'Only accepted W2 synthetic inputs may enter this browser adapter.');
  const s=report.source, u=envelope.upstream;
  for(const k of ['source_schema','source_engine','source_hash_basis','source_sha256',
    'frame_sha256','corpus_sha256','selection_sha256','review_sha256','missing_reason']) {
    check(s[k]===u[k],'W2 upstream provenance mismatch: '+k);
  }
  check(SHA.test(u.source_sha256)&&SHA.test(u.selection_sha256),
    'Missing source / selection digest.');
  const eligible=envelope.observations.filter(o=>o.source_status==='available' &&
    o.exclusion_reasons.length===0);
  const actual=new Map(eligible.map(o=>[o.id,o]));
  check(eligible.length===report.observation_ids.length &&
    report.source.observation_keys.length===eligible.length &&
    report.observation_ids.every((id,i)=>report.source.observation_keys[i].id===id),
    'W2 sidecar source order / eligible identity mismatch.');
  for(const o of report.source.observation_keys){
    const from=actual.get(o.id);
    check(from&&key(from)===key(o),'W2 sidecar source link or SHA mismatch: '+o.id);
    check(from.source_url===null&&!Object.hasOwn(from,'text'),
      'Synthetic adapter rejects real source URL or embedded source text.');
  }
  check(report.source.cohort.unit===envelope.cohort.unit &&
    report.source.cohort.weighting===envelope.cohort.weighting &&
    report.source.cohort.total_in_frame===envelope.cohort.total_in_frame,
    'W2 source unit, weighting or full frame drift.');
  check(envelope.models.length===1 &&
    envelope.models[0].representation_id==='w2-hard-assignment-identity-join-v1' &&
    envelope.models[0].method_family==='ensemble',
    'W2 derived representation or family mismatch.');
  check(report.pairs.every(p=>p.planned_count>=p.assigned_both_count &&
    p.assigned_both_count>=p.coassigned_count &&
    p.planned_weight>=p.assigned_both_weight &&
    p.assigned_both_weight>=p.coassigned_weight),
    'W2 full-pair source exposure inconsistent.');
  return {eligible};
}

function toW6Consensus(report,envelope){
  const {eligible}=validateSource(report,envelope);
  const m=envelope.models[0];
  const identity={
    source_schema:envelope.upstream.source_schema,
    source_hash_basis:envelope.upstream.source_hash_basis,
    source_sha256:envelope.upstream.source_sha256,
    selection_sha256:envelope.upstream.selection_sha256,
    unit:envelope.cohort.unit,weighting:envelope.cohort.weighting,
    representation_id:m.representation_id,representation_version:m.representation_version,
    observation_refs:eligible.map(o=>({id:o.id,text_sha256:o.text_sha256}))
  };
  const limited=eligible.length>35;
  const ambiguous=new Set(report.ambiguous_members.map(a=>a.observation_id));
  const familyAudit=report.family_weight_audit.map(f=>({
    family:f.method_family, planned_weight:f.total_weight,
    configurations:f.configurations,models:f.models,
    failed_fit_records:f.completely_failed_fit_records,internal_failures:f.internal_failures
  }));
  const reason=limited?'W6 exact pair heatmap supports at most 35 source identities; '+
    eligible.length+' eligible W2 observations are retained, not sampled.':null;
  const panel={
    kind:'consensus',status:limited?'withheld':'ready',reason,
    pair_mode:'w2_weighted_conditional',
    measure:'Source-linked W2 conditional weighted co-assignment = preplanned co-assigned '+
      'fit weight / assigned-both fit weight. Coverage uses assigned-both / planned '+
      'weight and retains noise, missing, failed and source-group refit denominators. '+
      'These are descriptions of fitting agreement, not calibrated probabilities.',
    identity,coverage:{
      frame:envelope.cohort.total_in_frame,
      eligible:envelope.cohort.eligible,
      included:limited?0:eligible.length,
      excluded:envelope.coverage.excluded,missing:envelope.coverage.unavailable_sources
    },
    family_weight_audit:familyAudit,
    warnings:[
      'Synthetic engineering-only; W2 grouped refit ranges are NOT confidence intervals or null significance.',
      'Weight allocation across method families, methods, configurations, grouped refits, and seeds is authored by W2, not recalculated in W6.',
      'Source-group design '+report.uncertainty.design+' with '+
        report.uncertainty.source_groups+' source groups. No independence or cross-country inference.',
      report.reproducible_groups.length+' descriptive complete-link groups; '+
        report.source_restricted_groups.length+' same-source-only candidate groups withheld; '+
        report.ambiguous_members.length+' ambiguous observations.'
    ],
    observation_ids:limited?[]:clone(report.observation_ids),
    pairs:limited?[]:report.pairs.filter(x=>x.observation_a!==x.observation_b).map(p=>({
      a:p.observation_a,b:p.observation_b,
      coassigned_count:p.coassigned_count,assigned_both_count:p.assigned_both_count,
      planned_count:p.planned_count,missing_pair_count:p.missing_pair_count,
      noise_pair_count:p.noise_pair_count,different_cluster_count:p.different_cluster_count,
      failed_fit_count:p.failed_fit_count,coassigned_weight:p.coassigned_weight,
      assigned_both_weight:p.assigned_both_weight,planned_weight:p.planned_weight,
      association:p.association,assignment_coverage:p.assignment_coverage,
      contributing_families:clone(p.contributing_families),
      unstable:ambiguous.has(p.observation_a)||ambiguous.has(p.observation_b),
      missing_reason:p.association===null?
        'No jointly assigned eligible weight for this observation pair.':null
    }))
  };
  V.validatePanel(envelope,panel,V.validateEnvelope(envelope));
  return Object.freeze(panel);
}

function render(report,envelope) {
  return V.renderPanel(envelope,toW6Consensus(report,envelope));
}

module.exports={validateSource,toW6Consensus,render};
