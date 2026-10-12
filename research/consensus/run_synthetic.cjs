'use strict';
/* Explicit opt-in synthetic-only reproducibility export; no real corpus or network access. */
const fs = require('node:fs');
const path = require('node:path');
const {fixtureKnown,fixtureNuisance,sha} = require('./fixtures.cjs');
const {runConsensus,toInterchangeV1,validateConsensus,validateEnvelope} = require('./consensus.cjs');
function csv(rows,cols) {
  const cell=x => '"' + (x === null || x === undefined ? '' : typeof x === 'object' ? JSON.stringify(x) : String(x)).replace(/"/g,'""') + '"';
  return [cols.map(cell).join(','),...rows.map(r=>cols.map(k=>cell(r[k])).join(','))].join('\n') + '\n';
}
function generate(outDir) {
  if (!outDir || !outDir.trim()) throw Error('Provide a local output directory, never a source directory.');
  const fixture=fixtureKnown(true), opts={fit_plan:fixture.fit_plan,min_coverage:0.2};
  const result=runConsensus(fixture.envelopes,opts);
  const v1=toInterchangeV1(fixture.envelopes[0],result,{generated_at:'2026-10-08T00:00:00Z'});
  const nuisance=fixtureNuisance();
  const control=runConsensus(nuisance.envelopes,{fit_plan:nuisance.fit_plan});
  validateConsensus(result);validateEnvelope(v1);validateConsensus(control);
  fs.mkdirSync(outDir,{recursive:true});
  const write=(name,data)=>fs.writeFileSync(path.join(outDir,name),data,'utf8');
  const pretty=x=>JSON.stringify(x,null,2)+'\n';
  const ids=result.observation_ids;
  write('association-matrix.csv',csv(ids.map((id,i)=>({observation_id:id,
    ...Object.fromEntries(ids.map((other,j)=>[other,result.matrix.association[i][j]]))})),
    ['observation_id',...ids]));
  write('pairwise-denominators.csv',csv(result.pairs,
    ['observation_a','observation_b','coassigned_count','assigned_both_count','planned_count',
      'missing_pair_count','noise_pair_count','different_cluster_count','failed_fit_count',
      'coassigned_weight','assigned_both_weight','planned_weight','association','assignment_coverage','contributing_families']));
  write('method-family-weight-audit.json',pretty(result.family_weight_audit));
  write('sensitivity-report.json',pretty(result.sensitivity_report));
  write('unsupported-pair-ledger.csv',csv(result.unsupported_pair_ledger,
    ['observation_a','observation_b','reason','association','assigned_both_count','planned_count']));
  write('grouped-uncertainty.json',pretty(result.uncertainty));
  write('consensus-v1.json',pretty(result));
  write('standardized-interchange-v1.json',pretty(v1));
  write('nuisance-only-control.json',pretty({
    tested:'source-specific partitions without across-group latent structure',
    reproducible_groups:control.reproducible_groups.length,
    source_concentrated_rejected_groups:control.source_restricted_groups.length,
    interpretation:'Descriptive group consistency alone is not substantive or null-calibrated evidence.'}));
  const receipt={schema:'un.consensus.synthetic-receipt.v1',fixture:'synthetic only',
    fixture_sha256:sha('fixed-synthetic-source-v1'),contract:'un.parallel-analysis.v1',
    base_models:fixtureKnown(false).envelopes.length,all_fit_records:fixture.envelopes.length,
    attempted_fits:fixture.envelopes.reduce((s,e)=>s+e.coverage.models[0].attempted_fits,0),
    failed_fits:fixture.envelopes.reduce((s,e)=>s+e.coverage.models[0].failed_fits,0),
    observations:ids.length,source_groups:result.uncertainty.source_groups,
    pair_records:result.pairs.length,descriptive_groups:result.reproducible_groups.length,
    nuisance_rejected:control.source_restricted_groups.length,network_access:false,
    holdout_access:false,evaluation_role:'engineering_only',publication_eligible:false};
  write('validation-receipt.json',pretty(receipt));
  return receipt;
}
if (require.main === module) {
  const target = process.argv[2];
  if (!target || process.argv.length !== 3) {
    process.stderr.write('Usage: node research/consensus/run_synthetic.cjs <local-output-directory>\n');
    process.exitCode=2;
  } else {
    try {process.stdout.write(JSON.stringify(generate(path.resolve(target)))+'\n');}
    catch(e){process.stderr.write(String(e.stack||e)+'\n');process.exitCode=1;}
  }
}
module.exports={generate,csv};
