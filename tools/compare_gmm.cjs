/* Fixed exploratory grid and paired meeting refits; no automatic model selection. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const A=require('../site/analysis-core.js'),C=require('../site/cluster-core.js'),G=require('../site/gmm-core.js'),P=require('./compare_passage_types.cjs');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function brief(f){
  if(f.skipped)return {representation:f.representation,skipped:f.skipped,fit_diagnostics:f.fit_diagnostics};
  const s=f.stability;
  return {representation:f.representation,parameters:f.parameters,analyzed_count:f.analyzed_count,excluded:f.excluded,
    representation_summary:{components:f[f.representation].components,retained_variance:f[f.representation].retained_variance},
    clustering:f.clustering,gmm:f.gmm,clusters:f.clusters,points:f.points.map(({pca,lsa,umap,...p})=>p),
    stability:{attempted:s.attempted,successful:s.successful,groups:s.group_count,sampled_groups:s.sample_group_count,unique_samples:s.unique_group_samples,
      ari:s.ari,jaccard:s.clusters,soft_membership:s.soft_membership,warnings:s.warnings,
      runs:s.runs.map(({memberships,labels,...r})=>r)}};
}
async function run(input,maskPath,out){
  for(const name of ['comparison.json',...['full','substantive','inclusive'].flatMap(p=>['diag','spherical'].map(c=>`${p}-${c}.json`))])
    if([input,maskPath].some(p=>path.resolve(p).toLowerCase()===path.resolve(out,name).toLowerCase()))throw Error('Output would overwrite an input.');
  const raw=fs.readFileSync(input),corpus=A.validateCorpus(JSON.parse(raw)),maskRaw=fs.readFileSync(maskPath),mask=JSON.parse(maskRaw),review=P.validateMask(corpus,raw,mask);
  const dates=corpus.records.map(r=>r.date).sort(),base=await A.analyze(corpus,{topic:'',start:dates[0],end:dates.at(-1),region:'All regions',scope:'general_debate',methods:['tfidf']});
  const records=base.matched,types=review.types,policies={full:records,substantive:records.filter(r=>types.get(r.id)==='substantive_speech'),inclusive:records.filter(r=>['substantive_speech','mixed_speech_procedure','speech_fragment'].includes(types.get(r.id)))};
  const result={schema:'un.gmm-comparison.v1',engine:A.VERSION,corpus_sha256:sha(raw),mask_sha256:sha(maskRaw),human_confirmed:review.confirmed,original_text_unchanged:true,
    protocol:'Same reviewed inclusion policies; unwhitened PCA/LSA with 20 requested dimensions. Grid: 1/2/4/6 mixture components, diagonal/spherical covariance, variance regularization 0.0001/0.001, five seeded k-means initializations, 300 EM iterations, tolerance 0.00001. No model selected from the grid. Four components and regularization 0.0001 receive 30 whole-meeting refits per policy, covariance and representation (seed 31415; retain 80%, rounded up with one omitted). UMAP is display-only.',
    sources:records.map(r=>({id:r.id,text_sha256:r.text_sha256,country:r.country,date:r.date,source_url:r.source_url,type:types.get(r.id)})),policies:{},full_subset_comparisons:[]};
  fs.mkdirSync(out,{recursive:true});const saved={};
  for(const [policy,rows]of Object.entries(policies)){
    const vectors=A.tfidf(rows).vectors,usable=rows.flatMap((r,i)=>vectors[i].size?[i]:[]);
    const p={selected:rows.length,usable:usable.length,selected_ids:rows.map(r=>r.id),excluded_ids:records.filter(r=>!rows.some(s=>s.id===r.id)).map(r=>r.id),grid:[],fits:[]};result.policies[policy]=p;
    for(const method of ['pca','lsa']){
      const rep=C.represent(usable.map(i=>vectors[i]),20,method,false);
      for(const covariance of ['diag','spherical'])for(const regularization of [.0001,.001])for(const k of [1,2,4,6]){
        const f=await G.fit(rep.scores,{k,seed:42,covariance,regularization});
        p.grid.push({representation:method,dimensions:rep.components,covariance,regularization,k,passages:rep.scores.length,
          ...(f.skipped?{skipped:f.skipped,diagnostics:f.diagnostics}:{log_likelihood:f.diagnostics.log_likelihood,parameter_count:f.diagnostics.parameter_count,aic:f.diagnostics.aic,bic:f.diagnostics.bic,
            sizes:f.diagnostics.hard_counts,soft_counts:f.diagnostics.soft_counts,converged_starts:f.diagnostics.converged_starts,near_floor_dimensions:f.diagnostics.near_floor_dimensions,
            mean_entropy:f.diagnostics.mean_entropy,ambiguous:f.diagnostics.ambiguous_count,warnings:f.diagnostics.warnings})});
      }
      console.log(JSON.stringify({policy,grid:method,rows:p.grid.filter(g=>g.representation===method).length}));
    }
    for(const covariance of ['diag','spherical']){
      const fit=await C.run(rows,vectors,{representation:'compare',algorithm:'gmm',components:20,k:4,seed:42,gmm:{covariance},stability:{enabled:true,replicates:30,fraction:.8,unit:'meeting',seed:31415}});
      fs.writeFileSync(path.join(out,`${policy}-${covariance}.json`),JSON.stringify({methods:{clusters:fit}}));
      for(const f of [fit,fit.comparison.alternative]){
        p.fits.push(brief(f));saved[policy+'/'+covariance+'/'+f.representation]=f;
        if(policy!=='full'&&!f.skipped){const full=saved['full/'+covariance+'/'+f.representation],by=new Map(full.points.map(p=>[p.id,p]));
          const reference=f.points.map(p=>by.get(p.id));result.full_subset_comparisons.push({policy,covariance,representation:f.representation,shared_passages:reference.length,
            hard_ari:new Set(reference.map(p=>p.cluster)).size>=2&&new Set(f.points.map(p=>p.cluster)).size>=2?C.ari(reference.map(p=>p.cluster),f.points.map(p=>p.cluster)):null,
            soft_agreement:G.align(reference.map(p=>p.memberships),f.points.map(p=>p.memberships))});
        }
        console.log(JSON.stringify({policy,covariance,representation:f.representation,n:f.analyzed_count,sizes:f.gmm?.hard_counts,ari:f.stability?.ari?.mean,tv:f.stability?.soft_membership?.mean_total_variation?.mean,samples:f.stability?.successful,skipped:f.skipped}));
      }
    }
  }
  if(sha(fs.readFileSync(input))!==result.corpus_sha256)throw Error('Original collection changed.');
  fs.writeFileSync(path.join(out,'comparison.json'),JSON.stringify(result,null,2)+'\n');return result;
}
if(require.main===module){const [input,mask,out]=process.argv.slice(2);if(!out)throw Error('Supply collection, reviewed mask and output directory.');run(input,mask,out).catch(e=>{console.error(e);process.exitCode=1;});}
module.exports={run,brief};
