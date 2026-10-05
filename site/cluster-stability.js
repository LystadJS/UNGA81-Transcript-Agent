/* Group subsampling: refit TF-IDF, representation and partition; compare shared observations.
 * Consensus is descriptive co-assignment, not a new partition or a probability
 * of policy agreement. Failed fits never enter pair or agreement denominators. */
(function(root) {
  'use strict';
  const isNode=typeof module!=='undefined'&&module.exports;
  const C=isNode?require('./cluster-core.js'):root.UNClusters;
  const A=isNode?require('./analysis-core.js'):root.UNAnalysis;
  const normalize=value=>String(value||'').normalize('NFKC').trim().replace(/\s+/g,' ');
  const pairIndex=(a,b)=>{const i=Math.max(a,b),j=Math.min(a,b);return i*(i-1)/2+j;};

  function groupRecords(records,unit) {
    const groups=new Map();
    let fallback=0,unknown=0;
    for(let i=0;i<records.length;i++) {
      const r=records[i];let key,label;
      if(unit==='meeting') {
        let asset=null;
        try {
          const u=new URL(r.source_url);
          if(u.hostname==='transcripts.un.org') asset=u.pathname.match(/\/asset\/([^/]+)\/([^/]+)/i)?.slice(1).join('/');
        } catch (_) { /* Imported metadata is validated by the caller. */ }
        if(asset){key='un-asset:'+asset;label=normalize(r.meeting)||asset;}
        else {
          if(!normalize(r.meeting)||!A.dateOK(r.date)) throw Error('Meeting resampling requires a meeting title and date for every passage.');
          key=JSON.stringify([r.date,normalize(r.scope),normalize(r.meeting)]);
          label=r.date+' · '+normalize(r.meeting);fallback++;
        }
      } else {
        label=normalize(r.country);
        if(!label||/^(unidentified|unknown|unmapped)$/i.test(label)){label='Unidentified affiliation';unknown++;}
        key=label;
      }
      if(!groups.has(key))groups.set(key,{key,label,indices:[]});
      groups.get(key).indices.push(i);
    }
    return {groups:[...groups.values()].sort((a,b)=>a.key.localeCompare(b.key)),fallback,unknown};
  }

  function sampleGroups(total,count,random) {
    const indices=Array.from({length:total},(_,i)=>i);
    for(let i=total-1;i>0;i--){const j=Math.floor(random()*(i+1));[indices[i],indices[j]]=[indices[j],indices[i]];}
    return indices.slice(0,count).sort((a,b)=>a-b);
  }

  function summary(values) {
    const x=values.filter(v=>v!==null&&Number.isFinite(v)).sort((a,b)=>a-b);
    if(!x.length)return {count:0,mean:null,median:null,min:null,max:null};
    return {count:x.length,mean:x.reduce((a,b)=>a+b,0)/x.length,
      median:(x[Math.floor((x.length-1)/2)]+x[Math.floor(x.length/2)])/2,min:x[0],max:x[x.length-1]};
  }

  // Each reference cluster gets its best Jaccard overlap on the retained rows.
  // Matches are deliberately many-to-one; splits/merges reduce overlap, and
  // clusters represented by fewer than two rows are explicitly unevaluable.
  function jaccards(reference,labels,clusterIds,noiseAware=false) {
    return clusterIds.map(cluster=>{
      const members=reference.flatMap((c,i)=>c===cluster?[i]:[]);
      if(members.length<2)return {cluster,reference_count:members.length,jaccard:null,matched_cluster:null};
      let best=0,match=null;
      for(const label of new Set(labels)) {
        if(noiseAware&&label<0)continue;
        const size=labels.filter(v=>v===label).length;
        const intersection=members.filter(i=>labels[i]===label).length;
        const j=intersection/(members.length+size-intersection);
        if(j>best||match===null){best=j;match=label+1;}
      }
      return {cluster,reference_count:members.length,jaccard:best,matched_cluster:match};
    });
  }

  function consensus(reference,runs,noiseAware=false) {
    const n=reference.length,length=n*(n-1)/2;
    const observed=Array(length).fill(0),together=Array(length).fill(0),included=Array(n).fill(0);
    const coAssigned=noiseAware?Array(length).fill(0):null,assigned=noiseAware?Array(n).fill(0):null;
    for(const run of runs.filter(r=>!r.skipped)) {
      for(let a=0;a<run.indices.length;a++) {
        const i=run.indices[a];included[i]++;
        if(noiseAware&&run.labels[a]>=0)assigned[i]++;
        for(let b=0;b<a;b++) {
          const pos=pairIndex(i,run.indices[b]);observed[pos]++;
          const bothAssigned=!noiseAware||(run.labels[a]>=0&&run.labels[b]>=0);
          if(noiseAware&&bothAssigned)coAssigned[pos]++;
          if(bothAssigned&&run.labels[a]===run.labels[b])together[pos]++;
        }
      }
    }
    const points=reference.map((cluster,i)=>{
      const bins=new Map();let evaluated=0;
      for(let j=0;j<n;j++)if(i!==j){
        const pos=pairIndex(i,j),o=observed[pos];if(!o)continue;evaluated++;
        if(!noiseAware||reference[j]>0){const bin=bins.get(reference[j])||[0,0];bin[0]+=together[pos];bin[1]+=o;bins.set(reference[j],bin);}
      }
      const within=bins.has(cluster)?bins.get(cluster)[0]/bins.get(cluster)[1]:null;
      const other=[...bins].filter(([c])=>c!==cluster).map(([c,[a,b]])=>({cluster:c,rate:a/b})).sort((a,b)=>b.rate-a.rate||a.cluster-b.cluster)[0];
      return {index:i,included:included[i],observed_peers:evaluated,within_cluster:within,
        ...(noiseAware?{assigned:assigned[i],unassigned:included[i]-assigned[i],assignment_rate:included[i]?assigned[i]/included[i]:null}:{}),
        strongest_other_cluster:other?.cluster??null,strongest_other:other?.rate??null,
        margin:within===null||!other?null:within-other.rate};
    });
    const counts=summary(observed);
    return {packing:'Strict lower triangle: index = i*(i-1)/2+j for i>j; diagonal is point inclusion count',
      co_observed:observed,co_clustered:together,points,
      ...(noiseAware?{co_assigned:coAssigned,noise_rule:'All jointly sampled pairs enter co_observed; co_clustered requires the same non-noise cluster. co_assigned counts both assigned, in any clusters. Reference unassigned passages are never a comparison cluster.'}:{}),
      pair_coverage:{total:length,observed:observed.filter(v=>v>0).length,never_observed:observed.filter(v=>!v).length,
        min:counts.min,max:counts.max,mean:counts.mean}};
  }

  function assignmentAgreement(reference,labels){
    const shared=reference.flatMap((c,i)=>c>0&&labels[i]>=0?[i]:[]);
    const enough=shared.length>=2&&new Set(shared.map(i=>reference[i])).size>=2&&new Set(shared.map(i=>labels[i])).size>=2;
    const transitions={both_assigned:shared.length,reference_assigned_sample_unassigned:0,reference_unassigned_sample_assigned:0,both_unassigned:0};
    reference.forEach((c,i)=>{if(c>0&&labels[i]<0)transitions.reference_assigned_sample_unassigned++;else if(c===0&&labels[i]>=0)transitions.reference_unassigned_sample_assigned++;else if(c===0&&labels[i]<0)transitions.both_unassigned++;});
    return {ari:enough?C.ari(shared.map(i=>reference[i]),shared.map(i=>labels[i])):null,
      assignment:{...transitions,shared_assigned_for_ari:shared.length,assigned_count:labels.filter(c=>c>=0).length,unassigned_count:labels.filter(c=>c<0).length},
      ...(!enough?{ari_unassessed:'Fewer than two clusters represented in both fits on their shared assigned passages.'}:{})};
  }

  async function run(records,fit,progress=async()=>{}) {
    const options=C.options(fit.parameters),s=options.stability;
    const noiseAware=options.algorithm==='hdbscan';
    const method=fit.representation||'pca',name=method.toUpperCase();
    const base={schema:'un.cluster-stability.v1',parameters:s,
      representation:method,algorithm:options.algorithm,algorithm_name:C.algorithmName(options),
      clustering_parameters:{algorithm:options.algorithm,...(noiseAware?{hdbscan:options.hdbscan}:{k:options.k}),...(options.algorithm==='hierarchical'?{linkage:options.linkage}:{})},
      ...(noiseAware?{ari_scope:'Shared assigned passages only; two represented clusters required in each fit. Assignment coverage and status transitions reported separately.'}:{}),
      procedure:`Uniform group subsampling without replacement; TF-IDF vocabulary/IDF, ${name} and ${C.algorithmName(options)} refitted in each sample; UMAP excluded`,
      interpretation:'Sensitivity to omitted groups and refitting; not a confidence interval, population estimate, reviewed label or policy agreement probability',
      reference_ids:fit.points.map(p=>p.id),reference_clusters:fit.points.map(p=>p.cluster),warnings:[]};
    if(!s.enabled)return {...base,skipped:'Stability assessment was not selected.'};
    if(records.some(r=>typeof r.text!=='string'))return {...base,skipped:'Source text is required to refit TF-IDF during resampling.'};
    let grouped;
    try {grouped=groupRecords(records,s.unit);} catch(error){return {...base,skipped:error.message};}
    const groups=grouped.groups,G=groups.length,count=Math.max(0,Math.min(G-1,Math.ceil(s.fraction*G)));
    base.group_count=G;base.sample_group_count=count;base.effective_group_fraction=G?count/G:0;
    base.groups=groups.map(g=>({key:g.key,label:g.label,ids:g.indices.map(i=>records[i].id)}));
    if(G<3)return {...base,skipped:'Stability assessment needs at least three groups. Widen the collection or choose another grouping unit; the full-data clustering is retained.'};
    if(G<10)base.warnings.push(`Only ${G} groups are available. Repeated samples can reuse the same omissions; repetition does not add independent source evidence.`);
    if(grouped.fallback)base.warnings.push(`${grouped.fallback} passages use date, scope and meeting title as the grouping key because a UN asset identifier was unavailable.`);
    if(grouped.unknown)base.warnings.push(`${grouped.unknown} passages with unknown affiliations are kept together in one group. Recorded affiliations are not verified speaker identities.`);
    const indexById=new Map(fit.points.map((p,i)=>[p.id,i])),clusterIds=fit.clusters.map(c=>c.cluster);
    const runs=[],subsets=new Set();
    const random=C.rng(s.seed);
    for(let attempt=0;attempt<s.replicates;attempt++) {
      const message=`Stability · sample ${attempt+1} of ${s.replicates}`;
      await progress(message+' · refitting TF-IDF and '+name);
      const chosen=sampleGroups(G,count,random);subsets.add(chosen.join(','));
      // Preserve corpus row order; never let sampled-group order drive ties.
      const selected=new Set(chosen.flatMap(g=>groups[g].indices));
      const subset=records.filter((_,i)=>selected.has(i)),terms=A.tfidf(subset);
      const rows=subset.flatMap((r,i)=>terms.vectors[i].size&&indexById.has(r.id)?[i]:[]);
      const replicate={attempt:attempt+1,groups:chosen,selected_count:subset.length,
        indices:rows.map(i=>indexById.get(subset[i].id)),
        excluded_ids:subset.filter((r,i)=>!terms.vectors[i].size||!indexById.has(r.id)).map(r=>r.id),
        ...(options.algorithm==='kmeans'?{kmeans_seed:(s.seed+Math.imul(attempt+1,0x85ebca6b))>>>0}:{})};
      if(rows.length<4||(!noiseAware&&rows.length<=options.k)){runs.push({...replicate,skipped:'Too few usable passages for the selected clustering settings.'});continue;}
      const representation=C.represent(rows.map(i=>terms.vectors[i]),options.components,method,false);
      Object.assign(replicate,{vocabulary:terms.vocabulary,[method+'_components']:representation.components,[method+'_rank']:representation.rank,
        retained_variance:representation.retained_variance,...(method==='lsa'?{retained_energy:representation.retained_energy}:{})});
      if(!representation.rank){runs.push({...replicate,skipped:'No measurable TF-IDF variation.'});continue;}
      const fitted=await C.fitPartition(representation.scores,{...options,seed:replicate.kmeans_seed??options.seed},
        async step=>progress(message+' · '+step));
      if(fitted.skipped){runs.push({...replicate,skipped:fitted.skipped});continue;}
      const labels=fitted.labels,reference=replicate.indices.map(i=>fit.points[i].cluster),d=fitted.diagnostics;
      const diagnostics=noiseAware?{hdbscan:{clusters:new Set(labels.filter(c=>c>=0)).size,assigned_count:d.assigned_count,unassigned_count:d.unassigned_count,selected_nodes:d.selected_nodes}}:
        options.algorithm==='kmeans'?{converged_starts:d.converged_starts,inertia:d.inertia}:
        options.algorithm==='pam'?{pam:{total_distance:d.total_distance,mean_distance:d.mean_distance,swaps:d.swaps,
          medoid_ids:fitted.medoids.map(i=>subset[rows[i]].id),tolerance:d.tolerance}}:
        {hierarchical:{linkage:d.linkage,cut_height:d.cut_height,next_merge_height:d.next_merge_height,tied_cut:d.tied_cut}};
      runs.push({...replicate,labels,...diagnostics,
        ...(noiseAware?assignmentAgreement(reference,labels):{ari:C.ari(reference,labels)}),jaccards:jaccards(reference,labels,clusterIds,noiseAware)});
    }
    const successful=runs.filter(r=>!r.skipped),matrix=consensus(base.reference_clusters,runs,noiseAware);
    if(successful.length<s.replicates)base.warnings.push(`${s.replicates-successful.length} samples could not be fitted. Agreement and pair counts use successful samples only; inspect the failure record.`);
    if(successful.length<10)base.warnings.push('Fewer than ten successful samples are available. Inspect coverage before interpreting agreement.');
    return {...base,attempted:runs.length,successful:successful.length,unique_group_samples:subsets.size,
      ...(successful.length<2?{skipped:'Fewer than two samples could be fitted; stability summaries are withheld.'}:{
        ari:summary(successful.map(r=>r.ari)),
        clusters:clusterIds.map(cluster=>({cluster,...summary(successful.map(r=>r.jaccards.find(c=>c.cluster===cluster).jaccard))}))}),
      consensus:matrix,runs};
  }
  const api={pairIndex,groupRecords,sampleGroups,summary,jaccards,consensus,assignmentAgreement,run};
  if(isNode)module.exports=api;else root.UNClusterStability=api;
})(globalThis);
