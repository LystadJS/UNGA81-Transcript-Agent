/* Compare inclusion policies without changing source text or selecting on clusters. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const A=require('../site/analysis-core.js'),C=require('../site/cluster-core.js'),S=require('../site/cluster-stability.js');
const TYPES=['substantive_speech','mixed_speech_procedure','right_of_reply','procedure','speech_fragment','suspected_transcription_issue','uncertain'];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const count=values=>values.reduce((out,key)=>(out[key]=(out[key]||0)+1,out),{});
function validateMask(corpus,bytes,mask,allowProvisional=false){
  if(mask.schema!=='un.passage-type-mask.v1'||mask.corpus_sha256!==sha(bytes))throw Error('Mask does not match original corpus bytes.');
  const originals=new Map(corpus.records.map(r=>[r.id,r]));
  if(!Array.isArray(mask.rows)||mask.rows.length!==originals.size||new Set(mask.rows.map(r=>r.id)).size!==originals.size)throw Error('Mask must cover every original ID exactly once.');
  let confirmed=0;
  const types=new Map(mask.rows.map(r=>{
    const source=originals.get(r.id);if(!source||source.text_sha256!==r.text_sha256||sha(Buffer.from(source.text))!==r.text_sha256)throw Error('Source or mask hash mismatch.');
    if(!TYPES.includes(r.proposed_type))throw Error('Unknown proposed type.');
    if(r.confirmed_type!==null&&r.confirmed_type!==undefined){
      if(!TYPES.includes(r.confirmed_type)||typeof r.reviewer!=='string'||!r.reviewer.trim()||!/(Z|[+-]\d\d:\d\d)$/.test(r.reviewed_at||'')||!Number.isFinite(Date.parse(r.reviewed_at))||Date.parse(r.reviewed_at)>Date.now()+300000)throw Error('Invalid confirmed decision.');
      confirmed++;
    }else if(!allowProvisional)throw Error('Unconfirmed types require --allow-provisional for an exploratory comparison.');
    return [r.id,r.confirmed_type??r.proposed_type];
  }));
  return {types,confirmed,status:confirmed===mask.rows.length?'human_confirmed':'provisional'};
}
function summarize(fit,records,types){
  if(fit.skipped)return {representation:fit.representation,skipped:fit.skipped};
  const byId=new Map(records.map(r=>[r.id,r]));
  const s=fit.stability,points=fit.points;
  return {representation:fit.representation,passages:points.length,components:fit[fit.representation].components,
    retained_variance:fit[fit.representation].retained_variance,groups:fit.clusters.map(c=>({cluster:c.cluster,size:c.size,
      types:count(points.filter(p=>p.cluster===c.cluster).map(p=>types.get(p.id))),representative_id:c.representative_id,
      representative_type:types.get(c.representative_id),source_url:byId.get(c.representative_id).source_url})),
    assigned:points.filter(p=>p.cluster>0).length,unassigned:points.filter(p=>p.cluster===0).length,
    unassigned_types:count(points.filter(p=>p.cluster===0).map(p=>types.get(p.id))),
    unassigned_passages:points.filter(p=>p.cluster===0).map(p=>({id:p.id,type:types.get(p.id),source_url:byId.get(p.id).source_url})),
    largest_share:Math.max(0,...fit.clusters.map(c=>c.size))/points.length,silhouette:fit.clustering.silhouette,
    silhouette_scope:fit.clustering.silhouette_scope||'All usable passages',
    stability:{successful:s.successful,attempted:s.attempted,ari:s.ari,groups:s.group_count,sampled_groups:s.sample_group_count,unique_samples:s.unique_group_samples,
      failed:s.runs.filter(r=>r.skipped).map(r=>({attempt:r.attempt,reason:r.skipped})),
      assignment_coverage:s.runs.filter(r=>r.assignment).map(r=>({attempt:r.attempt,...r.assignment})),
      jaccards:s.clusters,warnings:s.warnings},
    points:points.map(p=>({id:p.id,cluster:p.cluster,type:types.get(p.id)}))};
}
function compare(full,subset){
  if(full.skipped||subset.skipped)return {skipped:'A fit is unavailable.'};
  const reference=new Map(full.points.map(p=>[p.id,p.cluster])),noise=full.algorithm==='hdbscan';
  const refs=subset.points.map(p=>reference.get(p.id)),labels=subset.points.map(p=>p.cluster-1);
  const enough=noise?S.assignmentAgreement(refs,labels):{ari:C.ari(refs,labels)};
  return {shared_passages:subset.points.length,...enough,
    scope:noise?'Only passages assigned in both fits; require two represented groups in each. Coverage changes reported separately.':'All subset passages, comparing full-corpus memberships with the independently refitted subset.',
    full_clusters_represented:new Set(refs.filter(c=>c>0)).size,subset_clusters_represented:new Set(labels.filter(c=>c>=0)).size};
}
async function run(input,maskPath,out,allowProvisional=false){
  for(const name of ['comparison.json',...['full','substantive','inclusive'].flatMap(p=>['kmeans','pam','ward','average','hdbscan'].map(m=>`${p}-${m}.json`))]){
    if([input,maskPath].some(p=>path.resolve(p).toLowerCase()===path.resolve(out,name).toLowerCase()))throw Error('Output would overwrite an input.');
  }
  const bytes=fs.readFileSync(input),corpus=A.validateCorpus(JSON.parse(bytes)),maskBytes=fs.readFileSync(maskPath),mask=JSON.parse(maskBytes);
  const validated=validateMask(corpus,bytes,mask,allowProvisional),types=validated.types,dates=corpus.records.map(r=>r.date).sort();
  const selection={topic:'',start:dates[0],end:dates.at(-1),region:'All regions',scope:'general_debate',methods:['tfidf']};
  const base=await A.analyze(corpus,selection),records=base.matched;
  const policies={full:records,substantive:records.filter(r=>types.get(r.id)==='substantive_speech'),inclusive:records.filter(r=>['substantive_speech','mixed_speech_procedure','speech_fragment'].includes(types.get(r.id)))};
  fs.mkdirSync(out,{recursive:true});
  const result={schema:'un.passage-type-comparison.v1',engine:A.VERSION,corpus_sha256:sha(bytes),mask_sha256:sha(maskBytes),review_status:validated.status,
    human_confirmed:validated.confirmed,selection,counts:base.counts,type_counts:count(records.map(r=>types.get(r.id))),
    protocol:'Fixed 20 components, k=4 for fixed partitions; HDBSCAN EOM minimum size=15, min_samples=5 (includes self); 30 whole-meeting samples, fraction=0.8, seed=31415. TF-IDF, PCA/LSA and partitions refitted separately for each inclusion policy and each sample. UMAP is display only. No setting tuned to improve agreement.',
    original_text_unchanged:true,policies:{},comparisons:[]};
  const saved=new Map();
  for(const [policy,rows]of Object.entries(policies)){
    const vectors=A.tfidf(rows).vectors;
    result.policies[policy]={selected:rows.length,selected_ids:rows.map(r=>r.id),excluded_ids:records.filter(r=>!rows.some(s=>s.id===r.id)).map(r=>r.id),
      types:count(rows.map(r=>types.get(r.id))),dates:count(rows.map(r=>r.date)),fits:[]};
    for(const mode of ['kmeans','pam','ward','average','hdbscan']){
      const options={representation:'compare',algorithm:['ward','average'].includes(mode)?'hierarchical':mode,linkage:mode==='average'?'average':'ward',components:20,k:4,seed:42,hdbscan:{minClusterSize:15,minSamples:5,selection:'eom'},stability:{enabled:true,replicates:30,fraction:.8,unit:'meeting',seed:31415}};
      const fit=await C.run(rows,vectors,options);
      fs.writeFileSync(path.join(out,`${policy}-${mode}.json`),JSON.stringify({methods:{clusters:fit}}));
      for(const f of [fit,fit.comparison.alternative]){
        const key=mode+'/'+f.representation;saved.set(policy+'/'+key,f);
        const summary=summarize(f,rows,types);result.policies[policy].fits.push({mode,...summary});
        if(policy!=='full')result.comparisons.push({policy,mode,representation:f.representation,...compare(saved.get('full/'+key),f)});
        console.log(JSON.stringify({policy,mode,representation:f.representation,n:summary.passages,sizes:summary.groups?.map(g=>g.size),unassigned:summary.unassigned,ari:summary.stability?.ari?.mean}));
      }
    }
  }
  if(sha(fs.readFileSync(input))!==result.corpus_sha256)throw Error('Original corpus changed during comparison.');
  fs.writeFileSync(path.join(out,'comparison.json'),JSON.stringify(result,null,2)+'\n');return result;
}
module.exports={validateMask,summarize,compare,run};
if(require.main===module){const [input,mask,out]=process.argv.slice(2);if(!out)throw Error('Supply original corpus, mask and output directory.');run(input,mask,out,process.argv.includes('--allow-provisional')).catch(e=>{console.error(e);process.exitCode=1;});}
