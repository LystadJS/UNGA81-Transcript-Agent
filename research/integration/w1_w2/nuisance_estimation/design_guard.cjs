'use strict';
/* Lock the candidate's original pre-estimation design bytes, NOT a real study. */
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const SOURCE=path.join(__dirname,'design.candidate.v0.json');
const ORIGINAL_GIT_BLOB='eac3c87b2de555db55202d91cf440eaef228e4d0';
const ORIGINAL_SHA256='517ec5122fd23cc86fda46c9886b9971c389a9c5630fb030f9ecdfa3db4e875b';
const check=(x,m)=>{if(!x)throw Error('nuisance-candidate-design: '+m);};
function locked(){
 const bytes=fs.readFileSync(SOURCE);
 const hash=(alg,b)=>crypto.createHash(alg).update(b).digest('hex');
 const blob=hash('sha1',Buffer.concat([
   Buffer.from('blob '+bytes.length+'\0'),bytes]));
 check(blob===ORIGINAL_GIT_BLOB,'original synthetic candidate design blob mutated; create v1 instead');
 check(hash('sha256',bytes)===ORIGINAL_SHA256,'candidate design SHA-256 drift');
 const x=JSON.parse(bytes);
 check(x.schema==='un.w1w2.nuisance-estimator.design-candidate.v0'&&
   x.scope.kind==='fictional_numeric_nuisance_proxy_only'&&
   x.scope.empirical_sources_permitted===false&&
   x.scope.heldout_transcripts_permitted===false&&
   x.status==='candidate_for_independent_statistical_review_not_frozen_empirical_protocol'&&
   x.scientific_gates_passed===0&&x.scientific_gates_not_run===13&&
   x.plan_for_accuracy_calibration.preview_panels_per_feasible_scenario===2,
   'candidate source/nonrelease scientific declaration changed');
 const gate=JSON.parse(fs.readFileSync(path.resolve(__dirname,
   '../../../../docs/parallel-work/w1-w2-inference-readiness.v1.json'),'utf8'));
 check(gate.gates.length===13&&gate.gates.every(g=>g.status==='NOT_RUN') &&
   gate.empirical_evaluation_authorized===false&&
   gate.inferential_eligible===false&&gate.public_release_eligible===false&&
   gate.reserved_october_2026_holdout_sealed===true,
   'G01–G13 empirical/holdout gates were relaxed');
 return {plan:x,git_blob_sha1:blob,sha256:ORIGINAL_SHA256,
   inferential_eligible:false,scientific_gates_passed:0};
}
if(require.main===module){
 const p=locked();
 process.stdout.write(JSON.stringify({
   schema:'un.w1w2.nuisance-estimator.design-lock.v0',
   git_blob_sha1:p.git_blob_sha1,sha256:p.sha256,
   scope:'fictional_scalar_only',
   status:'CANDIDATE_DESIGN_NOT_EMPIRICAL_PREREGISTRATION',
   scientific_gates_passed:0
 })+'\n');
}
module.exports={locked,ORIGINAL_GIT_BLOB,ORIGINAL_SHA256};
