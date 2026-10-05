/* Fixed, reviewed inclusion policies. No automatic rank or theme selection. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const A=require('../site/analysis-core.js'),N=require('../site/nmf-core.js'),P=require('./compare_passage_types.cjs');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function run(input,maskPath,out){
  for(const name of ['comparison.json',...['full','substantive','inclusive'].flatMap(p=>[4,6,8].map(k=>`${p}-${k}.json`))]){
    if([input,maskPath].some(p=>path.resolve(p).toLowerCase()===path.resolve(out,name).toLowerCase()))throw Error('Output would overwrite an input.');
  }
  const bytes=fs.readFileSync(input),corpus=A.validateCorpus(JSON.parse(bytes)),maskBytes=fs.readFileSync(maskPath),mask=JSON.parse(maskBytes);
  const validated=P.validateMask(corpus,bytes,mask),types=validated.types,dates=corpus.records.map(r=>r.date).sort();
  const base=await A.analyze(corpus,{topic:'',start:dates[0],end:dates.at(-1),region:'All regions',scope:'general_debate',methods:['tfidf']});
  const policies={full:base.matched,substantive:base.matched.filter(r=>types.get(r.id)==='substantive_speech'),inclusive:base.matched.filter(r=>['substantive_speech','mixed_speech_procedure','speech_fragment'].includes(types.get(r.id)))};
  const result={schema:'un.nmf-comparison.v1',engine:A.VERSION,corpus_sha256:sha(bytes),mask_sha256:sha(maskBytes),human_confirmed:validated.confirmed,
    original_text_unchanged:true,protocol:'Ranks 4, 6, 8 are sensitivity checks, not automatic selection. Rank 6 receives 30 whole-meeting refits retaining 80% (rounded up, at least one omitted), seed 31415. Each fit uses 3 positive random starts, seed 42 for full-data fits, 300 iterations, tolerance 0.0001. TF-IDF is independently refitted. Components aligned by maximum one-to-one cosine over the union vocabulary; mixture L1 uses shared IDs. No thematic names assigned.',
    sources:base.matched.map(r=>({id:r.id,country:r.country,date:r.date,source_url:r.source_url,text_sha256:r.text_sha256,type:types.get(r.id)})),policies:{},comparisons:[]};
  fs.mkdirSync(out,{recursive:true});const saved={};
  for(const [policy,records]of Object.entries(policies)){
    result.policies[policy]={selected:records.length,selected_ids:records.map(r=>r.id),excluded_ids:base.matched.filter(r=>!records.some(s=>s.id===r.id)).map(r=>r.id),fits:[]};
    const vectors=A.tfidf(records).vectors;
    for(const components of [4,6,8]){
      const filename=path.join(out,`${policy}-${components}.json`);
      const fit=await N.run(records,vectors,{components,stability:{enabled:components===6}});
      if(fit.skipped)throw Error(policy+': '+fit.skipped);
      fs.writeFileSync(filename,JSON.stringify(fit));
      const {factors,vocabulary,...publicFit}=fit;result.policies[policy].fits.push(publicFit);
      if(components===6){saved[policy]=fit;if(policy!=='full')result.comparisons.push({policy,...N.align(saved.full,fit)});}
      console.log(JSON.stringify({policy,components,n:fit.usable_count,error:fit.diagnostics.relative_residual,converged:fit.diagnostics.converged,cosine:fit.stability.cosine?.mean,samples:fit.stability.successful}));
    }
  }
  if(sha(fs.readFileSync(input))!==result.corpus_sha256)throw Error('Original collection changed.');
  fs.writeFileSync(path.join(out,'comparison.json'),JSON.stringify(result,null,2)+'\n');
}
if(require.main===module){const [input,mask,out]=process.argv.slice(2);if(!out)throw Error('Supply original collection, reviewed mask and output directory.');run(input,mask,out).catch(e=>{console.error(e);process.exitCode=1;});}
module.exports={run};
