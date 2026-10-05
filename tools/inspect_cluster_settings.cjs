/* Reproducible descriptive sensitivity audit on an existing saved collection.
 * No transcript edits, relabeling, filtering of procedural text or UMAP fitting.
 * Representation refits are cached per identical cohort, never across cohorts. */
const fs=require('node:fs'),crypto=require('node:crypto');
const A=require('../site/analysis-core.js'),C=require('../site/cluster-core.js'),S=require('../site/cluster-stability.js');
const mean=x=>x.length?x.reduce((a,b)=>a+b,0)/x.length:null;
(async()=>{
  const [input,output]=process.argv.slice(2);if(!input||!output)throw Error('Supply saved corpus and output JSON.');
  const density=process.argv.includes('--density');
  const bytes=fs.readFileSync(input),corpus=A.validateCorpus(JSON.parse(bytes)),dates=corpus.records.map(r=>r.date).sort();
  const report=await A.analyze(corpus,{topic:'',start:dates[0],end:dates.at(-1),region:'All regions',scope:'general_debate',methods:['tfidf']});
  const records=report.matched,groups=S.groupRecords(records,'meeting').groups;
  const cohorts=[{name:'full',records},...groups.map((g,i)=>({name:g.key,records:records.filter((_,j)=>!g.indices.includes(j))}))];
  const cache=[];
  for(const cohort of cohorts){
    const tf=A.tfidf(cohort.records),keep=tf.vectors.flatMap((v,i)=>v.size?[i]:[]),rows=keep.map(i=>cohort.records[i]),v=keep.map(i=>tf.vectors[i]);
    cache.push({name:cohort.name,records:rows,representations:{pca:C.represent(v,40,'pca',false),lsa:C.represent(v,40,'lsa',false)}});
  }
  const cases=[];
  const plan=[];
  for(const representation of ['pca','lsa'])for(const components of [10,20,40]){
    if(density){for(const minClusterSize of [5,15,30])for(const minSamples of [5,10])plan.push({representation,components,algorithm:'hdbscan',hdbscan:{minClusterSize,minSamples,selection:'eom'}});}
    else for(const k of [3,4,6,8])for(const mode of ['kmeans','pam','ward','average'])plan.push({representation,components,k,algorithm:['ward','average'].includes(mode)?'hierarchical':mode,linkage:mode==='average'?'average':'ward'});
  }
  for(const settings of plan){
    const {representation,components}=settings,mode=settings.algorithm==='hierarchical'?settings.linkage:settings.algorithm;
    const fits=[];
    for(const [index,cohort] of cache.entries()){
      const x=cohort.representations[representation].scores.map(row=>row.slice(0,components));
      const fitted=await C.fitPartition(x,{...settings,seed:index?((31415+Math.imul(index,0x85ebca6b))>>>0):42});
      fits.push({...fitted,x,records:cohort.records});
    }
    const full=fits[0];if(full.skipped){cases.push({...settings,mode,skipped:full.skipped});continue;}
    const k=new Set(full.labels.filter(c=>c>=0)).size,assigned=full.labels.flatMap((c,i)=>c>=0?[i]:[]);
    const reference=new Map(full.records.map((r,i)=>[r.id,full.labels[i]]));
    const sizes=Array.from({length:k},(_,c)=>full.labels.filter(l=>l===c).length);
    const ari=fits.slice(1).map(f=>f.skipped?null:density?S.assignmentAgreement(f.records.map(r=>reference.get(r.id)+1),f.labels).ari:C.ari(f.records.map(r=>reference.get(r.id)),f.labels));
    const exemplars=Array.from({length:k},(_,c)=>{
      const indices=full.labels.flatMap((label,i)=>label===c?[i]:[]);
      const center=full.x[0].map((_,d)=>mean(indices.map(i=>full.x[i][d])));
      const dist=i=>full.x[i].reduce((sum,v,d)=>sum+(v-center[d])**2,0);
      const index=full.medoids?.[c]??indices.reduce((a,i)=>dist(i)<dist(a)?i:a,indices[0]),r=full.records[index];
      return {cluster:c+1,size:indices.length,representative_id:r.id,source_url:r.source_url,country:r.country,date:r.date,
        representative_words:r.text.trim().split(/\s+/).length,
        recorded_GA_count:indices.filter(i=>full.records[i].country==='GA').length,
        under_20_words:indices.filter(i=>full.records[i].text.trim().split(/\s+/).length<20).length};
    });
    const result={...settings,mode,n:full.labels.length,cluster_sizes:sizes,largest_share:Math.max(0,...sizes)/full.labels.length,
      ...(density?{selected_groups:k,assigned:assigned.length,unassigned:full.labels.length-assigned.length,
        omission_assignment_counts:fits.slice(1).map(f=>f.skipped?null:f.labels.filter(c=>c>=0).length),
        omission_assignment_coverage:fits.slice(1).map(f=>f.skipped?{skipped:f.skipped}:S.assignmentAgreement(f.records.map(r=>reference.get(r.id)+1),f.labels))}:{}),
      singleton_clusters:sizes.filter(n=>n===1).length,silhouette:k>=2&&assigned.length>k?C.silhouette(assigned.map(i=>full.x[i]),assigned.map(i=>full.labels[i])):null,
      leave_one_meeting_out_ari:ari,mean_leave_one_meeting_out_ari:mean(ari.filter(v=>v!==null)),exemplars};
    cases.push(result);
    console.log([representation,components,k,mode,result.largest_share.toFixed(3),result.mean_leave_one_meeting_out_ari?.toFixed(3)??'unassessed'].join(' '));
  }
  const result={schema:'un.cluster-settings-audit.v1',input_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),
    selection:report.parameters,counts:report.counts,usable_passages:cache[0].records.length,meeting_groups:groups.length,
    protocol:(density?'Fixed grid: PCA/LSA, 10/20/40 components, HDBSCAN EOM minimum size=5/15/30, density neighbors=5/10 (includes self). ARI uses only jointly assigned passages with two represented groups in each fit. ':'Fixed grid: PCA/LSA, 10/20/40 components, k=3/4/6/8, k-means/PAM/Ward/average. ')+ 'Full TF-IDF and representation refits for every leave-one-meeting-out cohort; six distinct omissions, not 30 independent repetitions. No auto-selected winner; no UMAP needed for partition sensitivity.',
    omission_keys:groups.map(g=>g.key),cases};
  fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
})().catch(error=>{console.error(error);process.exitCode=1;});
