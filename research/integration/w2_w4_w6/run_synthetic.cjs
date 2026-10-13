'use strict';
/* Generate only invented consensus and W6 accepted read models in a local dir. */
const fs=require('node:fs');
const path=require('node:path');
const {fixtureKnown}=require('../../consensus/fixtures.cjs');
const {runConsensus,toInterchangeV1}=require('../../consensus/consensus.cjs');
const B=require('./w2_bridge.cjs');
const V=require('./evidence_renderer.cjs');

function generate(folder) {
  if(!folder)throw Error('Provide an empty destination directory.');
  fs.mkdirSync(folder,{recursive:true});
  if(fs.readdirSync(folder).length)throw Error('Refuse to overwrite synthetic output.');
  const f=fixtureKnown(true),report=runConsensus(f.envelopes,{
    fit_plan:f.fit_plan,min_coverage:0.2
  }),envelope=toInterchangeV1(f.envelopes[0],report,{
    generated_at:'2026-10-12T00:00:00Z'
  });
  const panel=B.toW6Consensus(report,envelope);
  const view=V.renderPanel(envelope,panel);
  for(const [name,data] of [
    ['w2-report.json',report],['w2-envelope.json',envelope],['w2-panel.json',panel]
  ])fs.writeFileSync(path.join(folder,name),JSON.stringify(data,null,2)+'\n');
  fs.writeFileSync(path.join(folder,'w2-consensus.svg'),view.svg);
  const receipt={workstream:'W2',result:'synthetic_only',source_records:envelope.observations.length,
    inventory_meetings:envelope.coverage.inventory_meetings,
    eligible:envelope.cohort.eligible,excluded:envelope.coverage.excluded,
    pair_records:report.pairs.length,rendered_pairs:panel.pairs.length,
    family_count:report.family_weight_audit.length,publication_eligible:false,
    inference:'withheld',holdout_transcripts_opened:0};
  fs.writeFileSync(path.join(folder,'w2-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  return receipt;
}
if(require.main===module){
  try {console.log(JSON.stringify(generate(process.argv[2])));}
  catch(e){console.error(e.stack||e);process.exitCode=1;}
}
module.exports={generate};
