'use strict';
/* Generate W1->W2->W5/W6 metadata only from invented W1 source fixtures. */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {run}=require('../../validation_framework/runner.cjs');
const {toInterchangeV1}=require('../../validation_framework/interchange.cjs');
const {makeFixture,SETTINGS}=require('../../validation_framework/examples/synthetic_fixture.cjs');
const {fromW1}=require('./bridge.cjs');
const {panelForW6}=require('./w6_panel.cjs');
const W5=require('../../../site/parallel/w05-browser/experimental/method-lab/contracts.js');
const W6=require('../../../site/experimental/evidence-viz/evidence-viz.js');
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const root=path.resolve(__dirname,'../../..');
async function generate(dir){
  if(typeof dir!=='string'||!dir.trim())throw Error('Provide a new output directory.');
  const target=path.resolve(dir);
  if(target===root||target.startsWith(root+path.sep))
    throw Error('Synthetic exports must be outside the source repository.');
  const fixture=makeFixture();
  const native=await run(fixture.frame,SETTINGS,{
    saved:fixture.saved,group_units:['meeting'],replicates:3,group_seed:31});
  const original=toInterchangeV1(native);
  const joined=fromW1(native,original);
  const chart=panelForW6(joined);
  W5.validateParallel(original);
  W5.validateParallel(joined.interchange);
  const picture=W6.renderPanel(joined.interchange,chart.panel);
  if(chart.status!=='ready')throw Error('Expected known synthetic source cohort to satisfy exact renderer equivalence: '+chart.panel.reason);
  fs.mkdirSync(target,{recursive:false,mode:0o700});
  const files={
    'w1-v1-interchange.json':original,
    'w2-family-projection.json':joined.projected_envelope,
    'w2-consensus.json':joined.consensus,
    'w2-v1-interchange.json':joined.interchange,
    'w2-bridge-audit.json':joined.audit,
    'w6-consensus-panel.json':chart.panel,
    'w6-numerical-comparability.json':chart.comparability
  };
  const sums={};
  for(const [name,value] of Object.entries(files)){
    const payload=JSON.stringify(value,null,2)+'\n';
    if(/"text":|"text"\s*:/.test(payload))throw Error('Unexpected original source text in public JSON.');
    const bytes=Buffer.from(payload,'utf8');
    fs.writeFileSync(path.join(target,name),bytes,{flag:'wx',mode:0o600});
    sums[name]=sha(bytes);
  }
  const html=W6.htmlDocument(picture);
  fs.writeFileSync(path.join(target,'synthetic-consensus.html'),html,{encoding:'utf8',flag:'wx',mode:0o600});
  sums['synthetic-consensus.html']=sha(Buffer.from(html,'utf8'));
  const receipt={
    schema:'un.w1-w2-consensus-synthetic-receipt.v1',
    evaluation_role:'engineering_only',publication_eligible:false,
    heldout_transcripts_opened:0,network_access:false,
    eligible:joined.audit.eligible,
    excluded:joined.audit.excluded,unavailable_sources:joined.audit.unavailable_sources,
    source_sha256:joined.audit.source_sha256,selection_sha256:joined.audit.selection_sha256,
    w1_code_sha256:joined.audit.original_w1_code_sha256,
    w2_bridge_code_sha256:joined.audit.bridge_code_sha256,
    original_models:original.models.length,method_families:joined.consensus.family_weight_audit.length,
    w1_grouped_resample_attempts:native.model_reports.reduce(
      (s,m)=>s+(m.group_stability.meeting?.attempted||0),0),
    w2_baseline_pair_records:joined.consensus.pairs.length,
    w2_grouped_refit_pairs:joined.consensus.uncertainty.pairwise.length,
    uncertainty:joined.consensus.uncertainty.design,
    w6_render_status:chart.status,
    w6_displayed_pairs:chart.comparability.compared_pairs,
    w6_max_fraction_difference:chart.comparability.max_absolute_fraction_difference,
    limitations:joined.audit.limitations
  };
  const text=JSON.stringify(receipt,null,2)+'\n';
  fs.writeFileSync(path.join(target,'receipt.json'),text,{flag:'wx',mode:0o600});
  sums['receipt.json']=sha(Buffer.from(text,'utf8'));
  fs.writeFileSync(path.join(target,'SHA256.json'),JSON.stringify(sums,null,2)+'\n',{flag:'wx',mode:0o600});
  return receipt;
}
if(require.main===module) {
  if(process.argv.length!==3){process.stderr.write('Usage: node research/integration/w1_w2/make-synthetic.cjs <new-output-dir>\n');process.exitCode=2;}
  else generate(process.argv[2]).then(r=>process.stdout.write(JSON.stringify(r)+'\n')).catch(e=>{
    process.stderr.write(String(e.stack||e)+'\n');process.exitCode=1;
  });
}
module.exports={generate};
