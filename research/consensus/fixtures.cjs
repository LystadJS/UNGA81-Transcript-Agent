'use strict';
/* Synthetic fit-record generator. No transcripts, downloaded material, or real country claims. */
const {createHash} = require('node:crypto');
const sha = x => createHash('sha256').update(String(x)).digest('hex');
const groups = Array.from({length:6}, (_, i) => 'synthetic-meeting-' + (i + 1));
const observations = groups.flatMap((meeting, i) => ['a', 'b'].map((kind, j) => {
  const id = 'fictional-unit-' + (i + 1) + '-' + kind;
  return {id,text_sha256:sha('synthetic-content-id:' + id),
    parent_id:null,parent_text_sha256:null,meeting_id:meeting,speech_id:null,
    source_family_id:meeting,date:'2026-10-01',country:null,
    source_url:'https://example.invalid/synthetic/' + id,json_pointer:'/rows/' + (2 * i + j),
    start:null,end:null,unit:'synthetic',review_status:'not_applicable',
    exclusion_reasons:[],source_status:'available',missing_reason:null};
}));
function envelope(spec) {
  const selection = sha('fixed-synthetic-selection-v1'), source = sha('fixed-synthetic-source-v1');
  const settings = {
    schema:'un.parallel-analysis.v1',contract_version:'1.0.0',
    producer:{workstream_id:'W1',adapter_version:'synthetic-1',
      code_sha256:sha('synthetic fixture generator'),runtime:'node-22',
      generated_at:'2026-10-08T00:00:00Z',fixture_kind:'synthetic'},
    upstream:{source_schema:'synthetic.v1',source_engine:'consensus-test-fixture',
      source_hash_basis:'synthetic',source_sha256:source,
      frame_sha256:null,corpus_sha256:null,selection_sha256:selection,
      review_sha256:null,missing_reason:null},
    cohort:{split:'synthetic',population:'fictional paired topics by synthetic meeting',
      unit:'synthetic',selection_policy:'every synthetic observation',
      weighting:'equal_passage',source_group_unit:'meeting',duplicate_policy:'retain_and_audit',
      total_in_frame:6,eligible:observations.length},
    observations:structuredClone(observations),
    models:[{model_id:spec.id,method_family:spec.family,method:spec.method,
      representation_id:spec.representation || 'synthetic-lsa-locked-v1',
      representation_version:'1',fit_version:'1',fit_split:'synthetic',
      parameters_sha256:sha('parameter set:' + (spec.config || spec.method)),
      training_selection_sha256:selection,diagnostic_basis:'synthetic frozen fixture'}],
    results:[],coverage:{inventory_meetings:6,observations_total:observations.length,
      eligible:observations.length,excluded:0,unavailable_sources:0,models:[],failure_ledger:[]},
    evidence:[],diagnostics:[],limitations:[{code:'synthetic_only',scope:'all',
      description:'Synthetic analytical fixture with no diplomatic meaning.'}],
    publication_eligible:false,evaluation_role:'engineering_only'
  };
  const present = new Set(spec.sampled_groups || groups);
  settings.results = observations.map(o => {
    const withheld = !present.has(o.meeting_id) || !!spec.fail;
    const noise = !withheld && spec.noise && o.id === 'fictional-unit-6-a';
    const n = Number(o.id.match(/unit-(\d+)-/)[1]);
    const label = spec.nuisance ? n : o.id.endsWith('-a') ? 1 : 2;
    const kind = spec.method === 'gmm' && !withheld && !noise ? 'gmm_responsibility' : 'none';
    return {model_id:spec.id,observation_id:o.id,status:withheld ? 'not_fitted' : noise ? 'unassigned' : 'assigned',
      cluster:withheld ? null : noise ? 0 : label,membership_kind:kind,
      memberships:kind === 'gmm_responsibility' ? label === 1 ? [0.9,0.1] : [0.1,0.9] : null,
      membership_strength:null,representation_basis_id:spec.representation || 'synthetic-lsa-locked-v1',
      reason:withheld ? spec.fail ? 'Synthetic optimization failure' : 'Omitted whole source group' : noise ? 'Synthetic density noise' : null};
  });
  const count = status => settings.results.filter(r => r.status === status).length;
  settings.coverage.models = [{model_id:spec.id,eligible:observations.length,assigned:count('assigned'),
    unassigned:count('unassigned'),not_fitted:count('not_fitted'),excluded:0,
    attempted_fits:1,successful_fits:spec.fail ? 0 : 1,failed_fits:spec.fail ? 1 : 0}];
  if (spec.fail) settings.coverage.failure_ledger = [{model_id:spec.id,
    attempt:0,status:'failed',reason:'Deliberate synthetic optimization failure',seed:777,source_group:null}];
  return settings;
}
function fixtureKnown(includeResamples = true) {
  const specs = [
    ...[1,2,3,4].map(seed => ({id:'kmeans-' + seed,family:'partition',method:'kmeans',config:'kmeans_k2',seed})),
    {id:'pam-1',family:'partition',method:'pam',config:'pam_k2',seed:1},
    {id:'ward-1',family:'hierarchical',method:'ward',config:'ward_k2',seed:1},
    {id:'density-1',family:'density',method:'hdbscan',config:'hdbscan',noise:true,seed:1},
    {id:'gmm-1',family:'mixture',method:'gmm',config:'gmm2',seed:1},
    {id:'failed-1',family:'partition',method:'kmeans',config:'kmeans_k2',seed:777,fail:true}
  ];
  const fit_plan = {};
  for (const s of specs) fit_plan[s.id] = {configuration_id:s.config,seed:s.seed};
  if (includeResamples) {
    const designs = [];
    groups.forEach((omitted, i) => designs.push({
      type:'leave_group_out',id:'loo-' + (i + 1),sampled:groups.filter(g => g !== omitted)}));
    const selections = [[0,0,1,2,3,4],[0,1,1,2,4,5],[0,2,2,3,4,5],
      [0,1,3,3,4,5],[0,1,2,4,5,5],[0,1,2,3,4,5],[1,1,2,3,4,5]];
    selections.forEach((indices, i) => designs.push({
      type:'group_bootstrap',id:'boot-' + (i + 1),sampled:indices.map(j => groups[j])}));
    for (const d of designs) for (const [method,family,noise] of [
      ['kmeans','partition',false],['ward','hierarchical',false],['hdbscan','density',true],['gmm','mixture',false]]) {
      const id = method + '-' + d.id;
      const config = method + '-frozen';
      const s = {id,method,family,noise,config,sampled_groups:d.sampled};
      specs.push(s);
      fit_plan[id] = {configuration_id:config,resample_type:d.type,
        resample_id:d.id,sampled_groups:d.sampled.slice(),seed:1};
    }
  }
  return {envelopes:specs.map(envelope), fit_plan,
    truth:Object.fromEntries(observations.map(o => [o.id,o.id.endsWith('-a') ? 1 : 2])),
    source_groups:groups.slice()};
}
function fixtureNuisance() {
  const specs = [
    {id:'n-kmeans',family:'partition',method:'kmeans',config:'kmeans',nuisance:true},
    {id:'n-pam',family:'partition',method:'pam',config:'pam',nuisance:true},
    {id:'n-ward',family:'hierarchical',method:'ward',config:'ward',nuisance:true},
    {id:'n-gmm',family:'mixture',method:'gmm',config:'gmm',nuisance:true}
  ];
  return {envelopes:specs.map(envelope),
    fit_plan:Object.fromEntries(specs.map(s => [s.id,{configuration_id:s.config}])),
    nuisance_meeting_groups:groups.slice()};
}
module.exports = {sha, groups, observations, envelope, fixtureKnown, fixtureNuisance};
