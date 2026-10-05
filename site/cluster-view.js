/* Linked SVGs remain usable in the downloaded, script-free report. */
(function(root){
  'use strict';
  const colors=['#002d74','#b13d34','#1f716c','#7a5299','#99651b','#426b38','#a44877','#48677e','#715447','#686622','#5c55af','#31728e'];
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const percent=v=>v===null?'Not assessed':(100*v).toFixed(1)+'%';
  const number=v=>v===null||v===undefined?'Not assessed':v.toFixed(3);
  const color=c=>c>0?colors[(c-1)%colors.length]:'#667580';
  const label=c=>c>0?'Cluster '+c:'Unassigned';
  function render(fit,records,table,chart){
    if(fit.comparison)return root.UNComparisonView.render(fit,records,table,chart,render);
    const method=fit.representation||'pca',name=method.toUpperCase(),axis=method==='lsa'?'LS':'PC',rep=fit[method];
    if(fit.skipped)return `<h3>Text clusters${fit.representation?' · '+name:''}</h3><p class="warning">${esc(fit.skipped)}</p>`;
    const algorithm=fit.clustering?.name||'k-means',partition=fit.clustering||fit.kmeans;
    const largest=Math.max(0,...fit.clusters.map(c=>c.size))/fit.analyzed_count;
    const diagnostics=fit.gmm?[['Covariance model',fit.gmm.covariance_type],['Variance regularization',fit.gmm.regularization],['Converged starts',fit.gmm.converged_starts+' / '+fit.gmm.starts],['Mean normalized entropy',number(fit.gmm.mean_entropy)]]:fit.hdbscan?[
      ['Minimum cluster size',fit.hdbscan.min_cluster_size],['Density neighbors (including self)',fit.hdbscan.min_samples],
      ['Selection',fit.hdbscan.selection.toUpperCase()],['Assigned / unassigned passages',`${fit.hdbscan.assigned_count} / ${fit.hdbscan.unassigned_count}`],
      ['Silhouette coverage',`${partition.silhouette_count} of ${fit.analyzed_count} included passages`]
    ]:fit.pam?[
      ['Total / mean distance to medoids',`${fit.pam.total_distance.toFixed(5)} / ${fit.pam.mean_distance.toFixed(5)}`],
      ['Improving swaps',fit.pam.swaps],['Initialization / optimization','Deterministic BUILD / best SWAP'],
      ['Medoid passage IDs',fit.pam.medoid_ids.join(' · ')]
    ]:fit.hierarchical?[
      ['Linkage',fit.hierarchical.linkage],['Completed merges',fit.hierarchical.merges.length],
      ['Last included / next merge height',`${fit.hierarchical.cut_height.toFixed(5)} / ${fit.hierarchical.next_merge_height.toFixed(5)}`],
      ['Cut',fit.hierarchical.cut_rule]
    ]:[
      ['K-means inertia',fit.kmeans.inertia.toFixed(5)],
      ['Converged starts',`${fit.kmeans.converged_starts} / ${fit.kmeans.starts}`],
      ['Restart agreement: mean / minimum ARI',`${fit.kmeans.mean_ari_to_selected.toFixed(3)} / ${fit.kmeans.min_ari_to_selected.toFixed(3)}`],
      ['K-means seed',fit.parameters.seed]
    ];
    const description=fit.gmm?'Gaussian mixtures use regularized diagonal or spherical covariance and the highest-likelihood converged start. Map colors use highest model-conditioned membership. All soft memberships remain available; no noise category is inferred.':fit.hdbscan?'HDBSCAN builds an exact mutual-reachability hierarchy, prunes branches below the minimum cluster size and selects dense groups. No cluster count is forced. Silhouette excludes unassigned passages and requires at least two groups. Membership strength describes density within the selected hierarchy; it is not calibrated confidence or relevance.':
      fit.pam?'PAM minimizes total Euclidean distance to actual passage medoids using BUILD and improving SWAP steps. The result is a single-swap local optimum; global optimality is not guaranteed.':
      fit.hierarchical?`Hierarchical clustering uses ${fit.hierarchical.linkage} linkage and an exact-k cut. ${fit.hierarchical.height_definition}.`:
      'K-means uses Euclidean distance, k-means++ initialization and the lowest-inertia converged result from ten starts.';
    const byId=new Map(records.map(r=>[r.id,r]));
    function scatter(key,title){
      const rows=fit.points.map(p=>({...p,xy:[p[key][0]||0,p[key][1]||0]}));
      const min=[0,1].map(d=>Math.min(...rows.map(r=>r.xy[d]))),max=[0,1].map(d=>Math.max(...rows.map(r=>r.xy[d])));
      const unit=Math.min(802/((max[0]-min[0])||1),406/((max[1]-min[1])||1));
      const position=(v,d)=>(v-(min[d]+max[d])/2)*unit;
      return `<div class="cluster-map"><svg viewBox="0 0 900 500" role="group" aria-label="${esc(title)}"><title>${esc(title)}</title>
        <rect x="42" y="18" width="828" height="436" fill="#f5f7fa"/>
        ${rows.map(p=>{const r=byId.get(p.id),name=`${label(p.cluster)} · ${r.country} · ${r.date} · ${r.id}`,cx=455+position(p.xy[0],0),cy=237-position(p.xy[1],1),title=esc(name+'\n'+r.text.slice(0,220));
          return `<a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(name)}">${p.cluster===0?`<path d="M ${cx-3} ${cy-3} l 6 6 m -6 0 l 6 -6" stroke="${color(0)}" stroke-width="1.5"><title>${title}</title></path>`:`<circle cx="${cx.toFixed(2)}" cy="${cy.toFixed(2)}" r="5" fill="${color(p.cluster)}" stroke="#fff" stroke-width="0.8" opacity="0.85"><title>${title}</title></circle>`}</a>`;
        }).join('')}
        <text x="450" y="485" text-anchor="middle" font-size="14">${key==='umap'?'UMAP 1':axis+' 1'}</text>
        <text x="15" y="235" transform="rotate(-90 15 235)" text-anchor="middle" font-size="14">${key==='umap'?'UMAP 2':rep.components>1?axis+' 2':axis+' 2 unavailable (rank 1)'}</text>
        </svg></div>`;
    }
    return `<section class="cluster-section" aria-label="${name} ${algorithm} UMAP results"><h3>Text clusters · ${name} · ${algorithm}</h3>
      <div class="cluster-sequence"><div><span>Representation</span><strong>${name} · ${rep.components} components</strong></div><div><span>Clustering</span><strong>${algorithm} · ${partition.k} groups</strong></div><div><span>Visualization</span><strong>UMAP · 2 dimensions</strong></div></div>
      <p>${name} retains ${percent(rep.retained_variance)} of the centered TF-IDF variation in ${fit.analyzed_count} passages. The colors show ${algorithm} assignments computed from those ${name} scores.</p>
      ${method==='lsa'?`<p class="method-note">LSA fits uncentered TF-IDF and retains ${percent(rep.retained_energy)} of its squared matrix norm. This energy percentage includes the average term profile and differs from centered variance.</p>`:''}
      <p class="method-note">UMAP changes the display, not the groups. Map distances and gaps do not establish political alignment or separation. Select a point to open its source.</p>
      ${fit.hdbscan?`<p class="assignment-coverage"><strong>${fit.hdbscan.assigned_count} assigned · ${fit.hdbscan.unassigned_count} unassigned</strong> (${percent(fit.hdbscan.unassigned_count/fit.analyzed_count)}). Gray crosses remain in the maps, source list and exports. Unassigned means this density setting did not place the passage in a group; it does not mean irrelevant or erroneous.</p>${partition.k===0?'<p class="warning">No groups met these settings. All usable passages are unassigned; this is a valid result. Inspect the sources and compare density settings.</p>':''}`:''}
      ${largest>=0.9?`<p class="warning">One group contains ${percent(largest)} of included passages. Inspect its sources and the small remaining groups before treating this partition as a useful summary.</p>`:''}
      ${fit.excluded.length?`<p class="warning">${fit.excluded.length} passages had no usable terms and were excluded from clustering. Their identifiers remain in the data export.</p>`:''}
      ${rep.retained_variance!==null&&rep.retained_variance<0.5?'<p class="warning">These components retain less than half of the centered text variation. Compare a larger component count before interpreting the groups.</p>':''}
      ${scatter('umap','UMAP view of '+name+' scores, colored by '+algorithm+' cluster')}
      <div class="cluster-legend">${fit.clusters.map(c=>`<span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="6" fill="${color(c.cluster)}"/></svg> Cluster ${c.cluster} · ${c.size}</span>`).join('')}${fit.hdbscan?`<span>× Unassigned · ${fit.hdbscan.unassigned_count}</span>`:''}</div>
      ${partition.k>colors.length?'<p class="method-note">Colors repeat across groups; use the cluster numbers and source links to distinguish them.</p>':''}
      <details><summary>Compare the first two ${name} components</summary>${scatter(method,'First two '+name+' components with the same cluster assignments')}<p class="method-note">Clustering uses all ${rep.components} retained components, not just these two.</p></details>
      <details><summary>${name} variance and clustering diagnostics</summary>
        ${chart('Centered variance retained by component',rep.explained_variance_ratio.filter(r=>r!==null).map((r,i)=>({name:axis+' '+(i+1),value:r*100})),r=>r.name,r=>r.value,'%')}
        ${table(['Measure','Value'],[
          ['Components requested / retained',`${rep.requested_components} / ${rep.components} (rank ${rep.rank})`],
          ...(method==='lsa'?[['Uncentered energy retained',percent(rep.retained_energy)],['Relative reconstruction error',rep.relative_reconstruction_error.toFixed(3)]]:[]),
          ...diagnostics,['Mean silhouette ('+name+' space)',number(partition.silhouette)],
          ['UMAP seed',fit.umap.seed],
          ['UMAP neighbors requested / used',`${fit.umap.requested_neighbors} / ${fit.umap.neighbors}`],
          ['UMAP minimum distance / epochs',`${fit.umap.min_dist} / ${fit.umap.epochs}`]])}
        <p class="method-note">${method==='pca'?'PCA centers TF-IDF features without whitening.':'LSA retains leading singular components without centering, whitening or score renormalization.'} ${description} Silhouette describes geometric separation, not validated diplomatic categories. UMAP uses the same scores, Euclidean distance and an independent random initialization. Neighbor counts are capped at one less than the number of usable passages.</p>
        ${fit.pam||fit.hierarchical||fit.hdbscan?'<p class="method-note">This clustering method is deterministic for fixed scores and source order. Ties can depend on row order. Grouped stability measures sensitivity to omitted source groups; repeated identical fits are not independent evidence.</p>':''}
        ${fit.hdbscan?'<p class="method-note">Equal reachability distances can produce different binary merge orders across implementations, affecting assignments or membership strengths. The JSON retains the exact tree and tie rule. Tree selection stability differs from the grouped resampling assessment below.</p>':''}
      </details>
      ${fit.mds?root.UNMDSView.render(fit,records,table):''}
      ${fit.gmm?root.UNGaussianView.render(fit,records,table):''}
      ${fit.hierarchical?root.UNHierarchyView.render(fit,records,table):''}
      ${fit.fidelity?root.UNComparisonView.fidelity(fit,table):''}
      ${rep.component_terms?`<details><summary>LSA component vocabulary</summary><p class="method-note">Largest positive and negative term loadings on each axis. Signs can flip without changing the representation; these are descriptors, not reviewed themes or stances.</p>${table(['Component','Positive loadings','Negative loadings'],rep.component_terms.map(c=>['LS '+c.component,c.positive.map(t=>t.term+' ('+t.weight.toFixed(3)+')').join(' · '),c.negative.map(t=>t.term+' ('+t.weight.toFixed(3)+')').join(' · ')||'None']))}</details>`:''}
      ${fit.stability?root.UNStabilityView.render(fit.stability,records,table):''}
      ${fit.hdbscan?`<details class="unassigned-passages"><summary>Unassigned passages · ${fit.hdbscan.unassigned_count}</summary><p class="method-note">These passages were analyzed. Zero-term exclusions are listed separately. No unassigned pool is treated as a cluster.</p>${fit.points.filter(p=>p.cluster===0).map(p=>{const r=byId.get(p.id);return `<details><summary>${esc(r.country)} · ${esc(r.date)} · ${esc(p.id)}</summary><blockquote>${esc(r.text)}</blockquote><a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">Open unassigned passage source ↗</a></details>`;}).join('')||'<p>Every usable passage was assigned under these settings.</p>'}</details>`:''}
      <h4>Cluster vocabulary and examples</h4><p class="method-note">${fit.gmm?'Terms are ranked by membership-weighted mean TF-IDF for each component. Counts and map colors use highest-membership assignments.':'Terms are ranked by mean TF-IDF weight within each group.'} They are descriptors, not reviewed topic labels.</p>
      <div class="cluster-cards">${fit.clusters.map(c=>{const r=byId.get(c.representative_id);return `<div><h4>Cluster ${c.cluster} <span>· ${c.size} passages</span></h4><p>${c.terms.map(t=>esc(t.term)).join(' · ')}</p><p class="method-note">${esc(c.representative_role||'Nearest passage to the centroid')}: ${esc(r.country)} · ${esc(r.date)}</p><blockquote>${esc(r.text.slice(0,300))}${r.text.length>300?'…':''}</blockquote><a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a></div>`;}).join('')}</div>
      <details><summary>Point assignments and coordinates</summary>${table(['Passage','Country','Cluster',...(fit.hdbscan?['Membership strength']:[]),axis+' 1',axis+' 2','UMAP 1','UMAP 2'],fit.points.map(p=>[p.id,byId.get(p.id).country,p.cluster||'Unassigned',...(fit.hdbscan?[number(p.membership_strength)]:[]),p[method][0].toFixed(4),p[method].length>1?p[method][1].toFixed(4):'Not retained',...p.umap.map(v=>v.toFixed(4))]))}</details>
      </section>`;
  }
  root.UNClusterView={render,colors,color,label};
})(globalThis);
