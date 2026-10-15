/* Adapters consume accepted validators' existing outputs only. No fitting or authentication of original bytes. */
(function (root, factory) {
  'use strict';
  const api = factory(root);
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.UNResearchValidationAdaptersV2 = api;
})(typeof globalThis === 'object' ? globalThis : this, function (root) {
  'use strict';
  const V = typeof module === 'object' && module.exports ? require('./renderer.js') : root.UNResearchValidationV2;
  const SHA = /^[a-f0-9]{64}$/;
  const fail = message => { throw Error('Read-only adapter refused: ' + message); };
  const need = (yes,message) => { if (!yes) fail(message); };
  const syntheticURL = x => x === null ||
    (typeof x === 'string' && /^https:\/\/example\.invalid(?:\/|$)/.test(x));
  const other = (source,model,kind,reason) => ({
    kind,status:'withheld',reason,rows:[],
    identity:{population:source.cohort.population,weighting:source.cohort.weighting,
      unit:source.cohort.unit,representation_id:model.representation_id,
      representation_version:model.representation_version,
      source_hash_basis:source.upstream.source_hash_basis,
      source_sha256:source.upstream.source_sha256,
      selection_sha256:source.upstream.selection_sha256,
      source_ids:source.observations.map(o=>o.id)},
    coverage:{frame:source.cohort.total_in_frame,eligible:source.cohort.eligible,
      excluded:source.coverage.excluded,missing:source.coverage.unavailable_sources,included:0},
    measure:'Not measured in this accepted upstream output; no inferred results supplied.',
    warnings:['No zeros, models, trajectories, countries or method performance are imputed from absent data.']
  });
  function envelopeToFrame(env) {
    need(env && env.schema==='un.parallel-analysis.v1' && env.producer?.fixture_kind==='synthetic' &&
      env.cohort?.split==='synthetic' && env.publication_eligible===false &&
      env.evaluation_role==='engineering_only' && env.upstream?.source_schema==='synthetic.v1' &&
      env.upstream.source_hash_basis==='synthetic' && SHA.test(env.upstream.source_sha256) &&
      SHA.test(env.upstream.selection_sha256),'Only accepted source-bound synthetic v1 envelopes can be displayed');
    need(Array.isArray(env.observations) && Array.isArray(env.models) && env.models.length>0 &&
      Array.isArray(env.coverage?.models) && env.coverage.unavailable_sources<=env.coverage.excluded &&
      env.observations.length===env.cohort.total_in_frame &&
      env.coverage.eligible===env.cohort.eligible &&
      env.coverage.excluded+env.coverage.eligible===env.observations.length,
      'Source frame / eligibility / missingness contract incomplete');
    const ids=new Set();
    const sources=env.observations.map(o=>{
      need(typeof o.id==='string' && !ids.has(o.id) &&
        !['text','quote','transcript','content','source_text'].some(k=>Object.hasOwn(o,k)) &&
        syntheticURL(o.source_url),'Unknown, duplicate, text-bearing, or non-synthetic original source');
      ids.add(o.id);
      const active=o.source_status==='available' && Array.isArray(o.exclusion_reasons) &&
        o.exclusion_reasons.length===0;
      const status=active?'available':(o.source_status==='available'?'excluded':'missing');
      need(active ? SHA.test(o.text_sha256) :
        (o.text_sha256===null || SHA.test(o.text_sha256)) &&
        typeof o.missing_reason==='string' && o.missing_reason.length>0,
        'Original source hash or missingness reason absent');
      return {id:o.id,sha256:o.text_sha256,status,missing_reason:active?null:o.missing_reason,
        country:o.country??null,period:o.date===null?null:String(o.date).slice(0,4),
        meeting_id:o.meeting_id??null,review_status:o.review_status,
        source_url:o.source_url??null,json_pointer:o.json_pointer??null};
    });
    const missing=sources.filter(s=>s.status==='missing').length;
    need(missing===env.coverage.unavailable_sources &&
      sources.filter(s=>s.status==='available').length===env.cohort.eligible,
      'Unavailable and excluded sources cannot disappear from the inventory');
    return {schema:'un.research-validation-v2.synthetic',fixture_kind:'synthetic',
      publication_eligible:false,evaluation_role:'engineering_only',
      source:{source_schema:env.upstream.source_schema,source_hash_basis:env.upstream.source_hash_basis,
        source_sha256:env.upstream.source_sha256,selection_sha256:env.upstream.selection_sha256},
      sources,panels:[]};
  }

  // The injected validator must be the accepted source-bound UNResearchConsensus.validate.
  async function fromW2(env,sidecar,validators){
    need(validators && typeof validators.validateW2==='function',
      'Accepted W2 source-bound validator is required; do not supply pre-validated booleans');
    const verified=await validators.validateW2(env,sidecar);
    need(verified && verified.env===env && verified.sidecar===sidecar &&
      Array.isArray(verified.ids) && Array.isArray(sidecar.pairs) &&
      Array.isArray(sidecar.family_weight_audit),
      'W2 validator did not return the original source and complete pair read-model');
    const data=envelopeToFrame(env), model=env.models[0];
    need(model && model.representation_id==='w2-hard-assignment-identity-join-v1',
      'W2 consensus representation is not the accepted original');
    const p=other(env,model,'consensus','No eligible weighted consensus pairs');
    p.status=verified.ids.length<=35?'ready':'withheld';
    p.reason=p.status==='ready'?null:'More than 35 source observations: full pair frame retained and plot withheld';
    p.measure='Imported original W2 weighted conditional association, NOT equal method-family rate averaging; assigned-both, planned-fit, noise and failed opportunities are distinct.';
    p.warnings=['Only synthetic engineering results; W1/W2 inferential gates remain withheld.',
      'Method-family planned weights retained; missing per-family attempt counts are not invented.'];
    p.pair_population_ids=verified.ids.slice();
    p.family_weight_audit=sidecar.family_weight_audit.map(f=>({
      family:f.method_family,planned_weight:f.total_weight,
      attempted:null,successful:null,failed:null,skipped:null
    }));
    const ambiguous=new Set((sidecar.ambiguous_members||[]).map(r=>r.observation_id));
    p.rows=p.status==='ready' ? sidecar.pairs.filter(r=>r.observation_a!==r.observation_b).map(r=>({
      a:r.observation_a,b:r.observation_b,record_status:r.association===null?'zero_opportunity':'observed',
      coassigned_count:r.coassigned_count,assigned_both_count:r.assigned_both_count,
      planned_count:r.planned_count,missing_pair_count:r.missing_pair_count,
      noise_pair_count:r.noise_pair_count,different_cluster_count:r.different_cluster_count,
      failed_fit_count:r.failed_fit_count,coassigned_weight:r.coassigned_weight,
      assigned_both_weight:r.assigned_both_weight,planned_weight:r.planned_weight,
      association:r.association,assignment_coverage:r.assignment_coverage,
      contributing_families:r.contributing_families.slice(),
      unstable:ambiguous.has(r.observation_a)||ambiguous.has(r.observation_b),
      missing_reason:r.association===null?'No jointly assigned original W2 fit weight':null,
      source_ids:[r.observation_a,r.observation_b]
    })) : [];
    p.coverage.included=p.status==='ready'?verified.ids.length:0;
    data.panels=[p,
      other(env,model,'country-theme','W2 consensus supplies no NMF component-share evidence'),
      other(env,model,'longitudinal','W2 consensus supplies no comparable period alignment'),
      other(env,model,'method-comparison','W2 aggregate consensus does not identify cross-method stability')];
    return V.validate(data);
  }

  // The injected function MUST be the C5 UNResearchEvidence.loadW4Files,
  // not validateW4 on a pre-parsed JSON map: the loader checks the original
  // five file names/sizes, exact byte SHA256 manifest and saved alignment.
  async function fromW4(files,validators){
    need(validators && typeof validators.loadW4Files==='function',
      'Accepted W4 original five-file byte/hash loader required');
    const result=await validators.loadW4Files(files);
    need(result && result.envelope && result.panel && result.panel.kind==='longitudinal' &&
      result.provenance && result.source && result.analysis,
      'W4 validator did not return an original, source-bound panel');
    const env=result.envelope, p=result.panel, data=envelopeToFrame(env);
    // W4's authoritative source period IDs are p0/p1, not the calendar year
    // parsed from the interchange date. Never manufacture a period join from
    // source date or actor label: use only the independently validated source
    // panel returned by the accepted C5 original-file/alignment validator.
    need(Array.isArray(result.source.observations) && Array.isArray(p.periods),
      'Accepted W4 original source-period frame required');
    const periodByID=new Map();
    for(const row of result.source.observations){
      need(row && typeof row.id==='string' && !periodByID.has(row.id) &&
        typeof row.period==='string' && row.period.length>0,
        'W4 original source contains duplicate ID or missing native period');
      periodByID.set(row.id,row.period);
    }
    for(const item of data.sources){
      const period=periodByID.get(item.id);
      need(p.periods.includes(period),
        'W4 original source ID lacks a validated comparable native period');
      item.period=period;
    }
    const model=env.models.find(m=>m.representation_id===p.identity.representation_id);
    need(model && model.representation_version===p.identity.representation_version &&
      p.identity.source_sha256===env.upstream.source_sha256 &&
      p.identity.selection_sha256===env.upstream.selection_sha256 &&
      p.identity.source_hash_basis===env.upstream.source_hash_basis,
      'Validated W4 original representation or source identity differs');
    const temporal=other(env,model,'longitudinal','Comparable source periods unavailable');
    temporal.status=p.status;
    temporal.reason=p.reason;
    temporal.measure=p.measure;
    temporal.warnings=p.warnings.slice();
    temporal.coverage.included=p.coverage.included;
    temporal.periods=p.periods.slice();
    temporal.actors=p.actors.map(a=>({id:a.id,label:a.label,attribution_status:a.attribution_status,
      roster_status:a.roster_status}));
    temporal.alignments=p.alignments.map(a=>({from:a.from,to:a.to,status:a.status,
      anchors:a.anchors,reference_basis:a.reference_basis,
      selection_comparability:a.selection_comparability,rank_ok:a.rank_ok,
      degeneracy_ok:a.degeneracy_ok,reason:a.status==='passed'?null:(a.reason||'Failed upstream period comparability')}));
    temporal.rows=p.actors.flatMap(a=>a.positions.map(r=>({
      actor:a.id,period:r.period,status:r.status,xy:r.xy,uncertainty_radius:r.radius,
      n:r.n,source_ids:r.observation_ids.slice(),composition:r.composition || 'upstream_not_reported',
      reason:r.reason||null
    })));
    data.panels=[other(env,model,'consensus','W4 contains no W2 weighted pair evidence'),
      other(env,model,'country-theme','W4 contains no independent country-theme memberships'),
      temporal,other(env,model,'method-comparison','W4 original alignment is not a method stability comparison')];
    return V.validate(data);
  }

  // Already-validated W6 source-bound NMF panel, not newly estimated memberships.
  function fromW6Themes(env,panel,validators){
    need(validators && typeof validators.validateEnvelope==='function' &&
      typeof validators.validatePanel==='function', 'Accepted W6 envelope and panel validators required');
    const source=validators.validateEnvelope(env);
    validators.validatePanel(env,panel,source);
    const data=envelopeToFrame(env),model=env.models.find(m=>m.representation_id===panel.identity.representation_id);
    need(model && panel.kind==='country-theme' &&
      model.representation_version===panel.identity.representation_version,
      'Accepted W6 country/theme representation required');
    const p=other(env,model,'country-theme','No comparable country-theme output');
    p.status=panel.status;p.reason=panel.reason;
    p.measure=panel.measure;p.warnings=panel.warnings.slice();p.coverage.included=panel.coverage.included;
    p.countries=panel.countries.slice();p.themes=panel.components.map(x=>({...x}));
    p.unattributed_count=panel.unattributed_count;
    p.rows=panel.cells.map(r=>({country:r.country,theme:r.component,status:r.status,
      weighted_sum:r.weighted_sum,weight_total:r.weight_total,evidence_count:r.evidence_count,
      source_ids:r.observation_ids.slice(),reason:r.missing_reason}));
    data.panels=[other(env,model,'consensus','No accepted W2 weighted pair ledger'),p,
      other(env,model,'longitudinal','No source-comparable W4 alignment supplied'),
      other(env,model,'method-comparison','No comparative method attempt ledger supplied')];
    return V.validate(data);
  }
  return Object.freeze({VERSION:'2.0.0',envelopeToFrame,fromW2,fromW4,fromW6Themes});
});
