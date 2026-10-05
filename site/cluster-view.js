/* Linked SVGs remain usable in the downloaded, script-free report. */
(function(root){
  'use strict';
  const colors=['#002d74','#b13d34','#1f716c','#7a5299','#99651b','#426b38','#a44877','#48677e','#715447','#686622','#5c55af','#31728e'];
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const percent=v=>v===null?'Not assessed':(100*v).toFixed(1)+'%';
  function render(fit,records,table,chart){
    if(fit.comparison)return root.UNComparisonView.render(fit,records,table,chart,render);
    const method=fit.representation||'pca',name=method.toUpperCase(),axis=method==='lsa'?'LS':'PC',rep=fit[method];
    if(fit.skipped)return `<h3>Text clusters${fit.representation?' · '+name:''}</h3><p class="warning">${esc(fit.skipped)}</p>`;
    const byId=new Map(records.map(r=>[r.id,r]));
    function scatter(key,title){
      const rows=fit.points.map(p=>({...p,xy:[p[key][0]||0,p[key][1]||0]}));
      const min=[0,1].map(d=>Math.min(...rows.map(r=>r.xy[d]))),max=[0,1].map(d=>Math.max(...rows.map(r=>r.xy[d])));
      const unit=Math.min(802/((max[0]-min[0])||1),406/((max[1]-min[1])||1));
      const position=(v,d)=>(v-(min[d]+max[d])/2)*unit;
      return `<div class="cluster-map"><svg viewBox="0 0 900 500" role="group" aria-label="${esc(title)}"><title>${esc(title)}</title>
        <rect x="42" y="18" width="828" height="436" fill="#f5f7fa"/>
        ${rows.map(p=>{const r=byId.get(p.id),name=`Cluster ${p.cluster} · ${r.country} · ${r.date} · ${r.id}`;
          return `<a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(name)}"><circle cx="${(455+position(p.xy[0],0)).toFixed(2)}" cy="${(237-position(p.xy[1],1)).toFixed(2)}" r="5" fill="${colors[p.cluster-1]}" stroke="#fff" stroke-width="0.8" opacity="0.85"><title>${esc(name+'\n'+r.text.slice(0,220))}</title></circle></a>`;
        }).join('')}
        <text x="450" y="485" text-anchor="middle" font-size="14">${key==='umap'?'UMAP 1':axis+' 1'}</text>
        <text x="15" y="235" transform="rotate(-90 15 235)" text-anchor="middle" font-size="14">${key==='umap'?'UMAP 2':rep.components>1?axis+' 2':axis+' 2 unavailable (rank 1)'}</text>
        </svg></div>`;
    }
    return `<section class="cluster-section" aria-label="${name} k-means UMAP results"><h3>Text clusters · ${name}</h3>
      <div class="cluster-sequence"><div><span>Representation</span><strong>${name} · ${rep.components} components</strong></div><div><span>Clustering</span><strong>k-means · ${fit.kmeans.k} groups</strong></div><div><span>Visualization</span><strong>UMAP · 2 dimensions</strong></div></div>
      <p>${name} retains ${percent(rep.retained_variance)} of the centered TF-IDF variation in ${fit.analyzed_count} passages. The colors show k-means assignments computed from those ${name} scores.</p>
      ${method==='lsa'?`<p class="method-note">LSA fits uncentered TF-IDF and retains ${percent(rep.retained_energy)} of its squared matrix norm. This energy percentage includes the average term profile and differs from centered variance.</p>`:''}
      <p class="method-note">UMAP changes the display, not the groups. Map distances and gaps do not establish political alignment or separation. Select a point to open its source.</p>
      ${fit.excluded.length?`<p class="warning">${fit.excluded.length} passages had no usable terms and were excluded from clustering. Their identifiers remain in the data export.</p>`:''}
      ${rep.retained_variance!==null&&rep.retained_variance<0.5?'<p class="warning">These components retain less than half of the centered text variation. Compare a larger component count before interpreting the groups.</p>':''}
      ${scatter('umap','UMAP view of '+name+' scores, colored by k-means cluster')}
      <div class="cluster-legend">${fit.clusters.map(c=>`<span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="6" fill="${colors[c.cluster-1]}"/></svg> Cluster ${c.cluster} · ${c.size}</span>`).join('')}</div>
      <details><summary>Compare the first two ${name} components</summary>${scatter(method,'First two '+name+' components with the same cluster assignments')}<p class="method-note">Clustering uses all ${rep.components} retained components, not just these two.</p></details>
      <details><summary>${name} variance and clustering diagnostics</summary>
        ${chart('Centered variance retained by component',rep.explained_variance_ratio.filter(r=>r!==null).map((r,i)=>({name:axis+' '+(i+1),value:r*100})),r=>r.name,r=>r.value,'%')}
        ${table(['Measure','Value'],[
          ['Components requested / retained',`${rep.requested_components} / ${rep.components} (rank ${rep.rank})`],
          ...(method==='lsa'?[['Uncentered energy retained',percent(rep.retained_energy)],['Relative reconstruction error',rep.relative_reconstruction_error.toFixed(3)]]:[]),
          ['K-means inertia',fit.kmeans.inertia.toFixed(5)],['Mean silhouette ('+name+' space)',fit.kmeans.silhouette.toFixed(3)],
          ['Converged starts',`${fit.kmeans.converged_starts} / ${fit.kmeans.starts}`],
          ['Restart agreement: mean / minimum ARI',`${fit.kmeans.mean_ari_to_selected.toFixed(3)} / ${fit.kmeans.min_ari_to_selected.toFixed(3)}`],
          ['K-means seed / UMAP seed',`${fit.parameters.seed} / ${fit.umap.seed}`],
          ['UMAP neighbors requested / used',`${fit.umap.requested_neighbors} / ${fit.umap.neighbors}`],
          ['UMAP minimum distance / epochs',`${fit.umap.min_dist} / ${fit.umap.epochs}`]])}
        <p class="method-note">${method==='pca'?'PCA centers TF-IDF features without whitening.':'LSA retains leading singular components without centering, whitening or score renormalization.'} K-means uses Euclidean distance, k-means++ initialization and the lowest-inertia converged result from ten starts. Silhouette and restart agreement describe this fit; they do not validate diplomatic categories. UMAP uses the same scores, Euclidean distance and an independent random initialization. Neighbor counts are capped at one less than the number of usable passages.</p>
      </details>
      ${fit.fidelity?root.UNComparisonView.fidelity(fit,table):''}
      ${rep.component_terms?`<details><summary>LSA component vocabulary</summary><p class="method-note">Largest positive and negative term loadings on each axis. Signs can flip without changing the representation; these are descriptors, not reviewed themes or stances.</p>${table(['Component','Positive loadings','Negative loadings'],rep.component_terms.map(c=>['LS '+c.component,c.positive.map(t=>t.term+' ('+t.weight.toFixed(3)+')').join(' · '),c.negative.map(t=>t.term+' ('+t.weight.toFixed(3)+')').join(' · ')||'None']))}</details>`:''}
      ${fit.stability?root.UNStabilityView.render(fit.stability,records,table):''}
      <h4>Cluster vocabulary and examples</h4><p class="method-note">Terms are ranked by mean TF-IDF weight within each group. They are descriptors, not reviewed topic labels.</p>
      <div class="cluster-cards">${fit.clusters.map(c=>{const r=byId.get(c.representative_id);return `<div><h4>Cluster ${c.cluster} <span>· ${c.size} passages</span></h4><p>${c.terms.map(t=>esc(t.term)).join(' · ')}</p><p class="method-note">Nearest passage to the centroid: ${esc(r.country)} · ${esc(r.date)}</p><blockquote>${esc(r.text.slice(0,300))}${r.text.length>300?'…':''}</blockquote><a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a></div>`;}).join('')}</div>
      <details><summary>Point assignments and coordinates</summary>${table(['Passage','Country','Cluster',axis+' 1',axis+' 2','UMAP 1','UMAP 2'],fit.points.map(p=>[p.id,byId.get(p.id).country,p.cluster,p[method][0].toFixed(4),p[method].length>1?p[method][1].toFixed(4):'Not retained',...p.umap.map(v=>v.toFixed(4))]))}</details>
      </section>`;
  }
  root.UNClusterView={render,colors};
})(globalThis);
