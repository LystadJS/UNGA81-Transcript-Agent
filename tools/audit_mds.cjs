const fs=require('node:fs'),D=require('../site/mds-core.js'),M=require('../site/representation-metrics.js'),{distanceError}=require('./audit_umap.cjs');
(async()=>{
  const [input,output,iterations="1000"]=process.argv.slice(2),u=JSON.parse(fs.readFileSync(input)),result={schema:'un.mds-comparison.v1',protocol:`Metric equal-weight SMACOF on the same frozen scores as the UMAP audit; three starts, seed 42, maximum ${iterations} iterations, tolerance 0.000001. All pair distances included. No cluster refit.`,fits:[]};
  for(const f of u.fits){const d=await D.fit(f.scores,{maxIterations:Number(iterations)}),high=M.denseDistances(f.scores),low=M.denseDistances(d.coordinates),{points,...fidelity}=M.agreement(M.order(high),M.order(low),10,f.ids);
    result.fits.push({policy:f.policy,representation:f.representation,ids:f.ids,frozen_state_sha256:f.frozen_state_sha256,...d,fidelity,scale_adjusted:distanceError(high,low)});
    console.log(JSON.stringify({policy:f.policy,representation:f.representation,converged:d.converged,iterations:d.iterations,error:d.relative_distance_error,overlap:fidelity.neighbor_overlap,starts:d.runs.map(r=>({seed:r.seed,converged:r.converged,stress:r.stress}))}));
  }
  fs.writeFileSync(output,JSON.stringify(result)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
