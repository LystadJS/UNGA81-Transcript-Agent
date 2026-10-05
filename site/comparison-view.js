/* Matched-corpus comparison. Colors in both overview maps refer to PCA only. */
(function(root){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number=v=>v===null||v===undefined?'Not assessed':v.toFixed(3);
  const percent=v=>v===null||v===undefined?'Not assessed':(100*v).toFixed(1)+'%';
  function map(fit,byId,reference){
    const points=fit.points,method=fit.representation.toUpperCase();
    const min=[0,1].map(d=>Math.min(...points.map(p=>p.umap[d]))),max=[0,1].map(d=>Math.max(...points.map(p=>p.umap[d])));
    const unit=Math.min(802/((max[0]-min[0])||1),406/((max[1]-min[1])||1));
    const xy=(v,d)=>(v-(min[d]+max[d])/2)*unit;
    return `<div class="cluster-map"><svg viewBox="0 0 900 500" role="group" aria-label="UMAP from ${method}, using PCA reference colors"><title>UMAP from ${method}; colors follow the PCA reference</title><rect x="42" y="18" width="828" height="436" fill="#f5f7fa"/>
      ${points.map(p=>{const r=byId.get(p.id),cluster=reference.get(p.id),label=`${r.country} · ${r.date} · PCA cluster ${cluster} · ${method} cluster ${p.cluster} · ${r.id}`;
        return `<a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(label)}"><circle cx="${455+xy(p.umap[0],0)}" cy="${237-xy(p.umap[1],1)}" r="5" stroke="#fff" stroke-width="0.8" fill="${root.UNClusterView.colors[cluster-1]}"><title>${esc(label+'\n'+r.text.slice(0,220))}</title></circle></a>`;}).join('')}
      <text x="450" y="485" text-anchor="middle" font-size="18">UMAP 1</text><text x="15" y="235" transform="rotate(-90 15 235)" text-anchor="middle" font-size="18">UMAP 2</text></svg></div>`;
  }
  function fidelity(fit,table){
    const f=fit.fidelity,name=(fit.representation||'pca').toUpperCase();
    return `<details><summary>Neighborhood preservation</summary>
      ${table(['Comparison','Neighbors preserved','Trustworthiness','Continuity'],[
        [`TF-IDF → ${name}`,percent(f.representation.neighbor_overlap),number(f.representation.trustworthiness),number(f.representation.continuity)],
        [`${name} → UMAP`,percent(f.display.neighbor_overlap),number(f.display.trustworthiness),number(f.display.continuity)]])}
      <p class="method-note">These measures compare the ${f.representation.neighbors} nearest neighbors of each passage. Trustworthiness penalizes neighbors introduced by the reduction; continuity penalizes neighbors lost. All range from 0 to 1 (higher preserves more local structure). They measure geometry, not semantic accuracy. Euclidean distances use all retained dimensions; input TF-IDF is L2-normalized. Ties use rounded squared distances and source row order. Per-passage neighbor IDs remain in JSON.</p></details>`;
  }
  function render(fit,records,table,chart,single){
    const c=fit.comparison,right=c.alternative,byId=new Map(records.map(r=>[r.id,r]));
    let html='<section class="representation-comparison" aria-label="PCA and LSA comparison"><h3>PCA and LSA</h3>';
    if(c.skipped)html+=`<p class="warning">${esc(c.skipped)}</p>`;
    else {
      const reference=new Map(fit.points.map(p=>[p.id,p.cluster]));
      html+=`<p>Both representations use the same ${fit.analyzed_count} passages, TF-IDF vectors, requested dimensions, cluster count and random seeds. PCA subtracts the average term profile; LSA keeps it.</p>
        ${table(['Measure','PCA','LSA'],[
          ['Retained dimensions',fit.pca.components,right.lsa.components],
          ['Centered TF-IDF variance retained',percent(fit.pca.retained_variance),percent(right.lsa.retained_variance)],
          [`Original neighbors preserved (${c.neighbors} per passage)`,percent(fit.fidelity.representation.neighbor_overlap),percent(right.fidelity.representation.neighbor_overlap)],
          ['Silhouette in each representation',number(fit.kmeans.silhouette),number(right.kmeans.silhouette)],
          ...(fit.stability&&right.stability?[
            ['Successful stability samples',fit.stability.successful??'Not assessed',right.stability.successful??'Not assessed'],
            ['Mean stability ARI',number(fit.stability.ari?.mean),number(right.stability.ari?.mean)]]:[])])}
        <p><strong>Cluster agreement across representations: ${number(c.between_cluster_ari)} ARI.</strong> A value of 1 means the memberships match after relabeling. This comparison does not select a preferred method.</p>
        <div class="representation-maps"><div><h4>UMAP from PCA</h4>${map(fit,byId,reference)}</div><div><h4>UMAP from LSA</h4>${map(right,byId,reference)}</div></div>
        <p class="method-note">Both maps use the PCA reference colors to track the same passages. The right map's colors are not LSA assignments. Each layout has its own axes and orientation; compare neighbors and memberships rather than shapes or map distances. Open an individual result below to see its own cluster colors.</p>
        <div class="cluster-legend">${fit.clusters.map(g=>`<span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="6" fill="${root.UNClusterView.colors[g.cluster-1]}"/></svg> PCA cluster ${g.cluster} · ${g.size}</span>`).join('')}</div>
        <details><summary>Cluster membership correspondence</summary>${table(['PCA cluster',...right.clusters.map(g=>'LSA '+g.cluster)],c.membership_counts.map((row,i)=>[i+1,...row]))}<p class="method-note">Cells count shared passages. Cluster numbers are local to each fit and have no intrinsic correspondence.</p></details>
        <details><summary>Where nearest neighbors differ</summary><p class="method-note">The two representations share ${percent(c.mean_neighbor_overlap)} of their ${c.neighbors} nearest neighbors on average. These are up to ten passages with the least overlap; inspect their sources before interpreting the difference.</p>
        ${[...c.points].sort((a,b)=>a.neighbor_overlap-b.neighbor_overlap||a.id.localeCompare(b.id)).slice(0,10).map(p=>{const r=byId.get(p.id);return `<details><summary>${esc(r.country)} · ${esc(r.date)} · ${percent(p.neighbor_overlap)} shared neighbors</summary><blockquote>${esc(r.text)}</blockquote><a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">Open passage source ↗</a>${['pca','lsa'].map(method=>`<p><strong>${method.toUpperCase()} neighbors</strong></p><ul>${p[method+'_neighbors'].map(id=>{const n=byId.get(id);return `<li><a href="${esc(n.source_url)}" target="_blank" rel="noopener noreferrer" title="${esc(n.text.slice(0,220))}">${esc(n.country)} · ${esc(id)}</a></li>`;}).join('')}</ul>`).join('')}</details>`;}).join('')}</details>
        ${fit.stability?`<details><summary>Paired stability comparison</summary><p>${c.paired_stability.count} identical group samples fitted under both representations. Mean LSA-minus-PCA stability ARI: ${number(c.paired_stability.mean_ari_difference)}. Each ARI compares the resample with its own full-data reference; greater consistency does not establish substantive validity.</p>${table(['Sample','PCA ARI','LSA ARI','Difference'],c.paired_stability.samples.map(r=>[r.attempt,number(r.pca_ari),number(r.lsa_ari),number(r.lsa_minus_pca)]))}</details>`:''}`;
    }
    // Remove the wrapper before calling the shared single-fit renderer.
    const {comparison:ignored,...left}=fit;
    return html+`<details class="representation-result"><summary>Inspect PCA results</summary>${single(left,records,table,chart)}</details><details class="representation-result"><summary>Inspect LSA results</summary>${single(right,records,table,chart)}</details></section>`;
  }
  root.UNComparisonView={render,fidelity};
})(globalThis);
