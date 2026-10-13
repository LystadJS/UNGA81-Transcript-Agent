'use strict';
/* Synthetic-only source-bound grouped numerical receipt; no transcript text. */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const W1=require('../../validation_framework/runner.cjs');
const Interchange=require('../../validation_framework/interchange.cjs');
const Group=require('../../validation_framework/group_refit_interchange.cjs');
const {makeFixture,SETTINGS}=require('../../validation_framework/examples/synthetic_fixture.cjs');
const {withGroupedRefits}=require('./grouped_refits.cjs');
const {validateConsensus}=require('../../consensus/consensus.cjs');
const repo=path.resolve(__dirname,'../../..');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');

async function generate(directory){
  if(typeof directory!=='string'||!directory.trim())throw Error('A new private/local output directory is required.');
  const dest=path.resolve(directory);
  if(dest===repo||dest.startsWith(repo+path.sep))throw Error('Synthetic export directory must stay outside the repository.');
  if(fs.existsSync(dest))throw Error('Refuse to replace an existing output directory.');
  const fixture=makeFixture();
  const native=await W1.run(fixture.frame,SETTINGS,{
    saved:fixture.saved,group_units:['meeting'],
    replicates:18,group_seed:31,retain_group_assignments:true
  });
  const v1=Interchange.toInterchangeV1(native);
  const sidecar=Group.fromNative(native,v1);
  const merged=withGroupedRefits(native,v1,{sidecar});
  validateConsensus(merged.consensus);
  if(merged.audit.distinct_group_samples.leave_group_out<3 ||
    merged.audit.pairwise_descriptive===0)throw Error('Insufficient independently distinct source-selection sensitivity fixture.');
  const files={
    'source-group-refits-v1.json':sidecar,
    'w2-grouped-uncertainty.json':merged.consensus.uncertainty,
    'w2-grouped-pair-ledger.json':merged.consensus.pairs,
    'w2-grouped-family-audit.json':merged.consensus.family_weight_audit,
    'w1-w2-grouped-audit.json':merged.audit,
    'w2-grouped-interchange-v1.json':merged.interchange
  };
  const counters={
    schema:'un.w1-w2-grouped-refits-receipt.v1',
    evaluation_role:'engineering_only',publication_eligible:false,
    heldout_transcripts_opened:0,external_network_access:false,
    source_sha256:v1.upstream.source_sha256,
    selection_sha256:v1.upstream.selection_sha256,
    runner_sha256:v1.producer.code_sha256,
    original_models:v1.models.length,
    distinct_source_groups:sidecar.cohort.source_group_count,
    grouped_fit_records:sidecar.refits.length,
    full_frame_observations:v1.observations.length,
    eligible:sidecar.cohort.eligible,
    attempted_fits:merged.audit.attempts.attempted,
    successful_fits:merged.audit.attempts.successful,
    failed_fits:merged.audit.attempts.failed,
    skipped_fits:merged.audit.attempts.skipped,
    unique_group_samples:merged.audit.distinct_group_samples,
    pairwise_records:merged.audit.pairwise_records,
    pairwise_descriptive:merged.audit.pairwise_descriptive,
    uncertainty_basis:'without_replacement_leave_one_meeting_out',
    inferential_evidence:'withheld',
    limitations:merged.audit.limitations
  };
  files['receipt.json']=counters;
  fs.mkdirSync(dest,{recursive:false,mode:0o700});
  const sha={};
  for(const [name,data] of Object.entries(files)){
    const content=JSON.stringify(data,null,2)+'\n';
    if(/"text"\s*:|"vector"\s*:/.test(content) ||
      /Harbor ferry cargo docks|Clinic nurse treatment vaccine|Forest canopy oak nature/.test(content))
      throw Error('W1 original text/vectors are forbidden in saved sidecar');
    const bytes=Buffer.from(content,'utf8');
    fs.writeFileSync(path.join(dest,name),bytes,{flag:'wx',mode:0o600});
    sha[name]=hash(bytes);
  }
  fs.writeFileSync(path.join(dest,'SHA256.json'),JSON.stringify(sha,null,2)+'\n',
    {flag:'wx',mode:0o600});
  return counters;
}
if(require.main===module){
  if(process.argv.length!==3){process.stderr.write('Usage: node research/integration/w1_w2/make_grouped_synthetic.cjs <new-local-output-directory>\n');process.exitCode=2;}
  else generate(process.argv[2]).then(x=>process.stdout.write(JSON.stringify(x)+'\n'))
    .catch(e=>{process.stderr.write(String(e.stack||e)+'\n');process.exitCode=1;});
}
module.exports={generate};
