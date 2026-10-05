/* Model-conditioned soft memberships, linked sources, and explicit ambiguity. */
(function(root){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number=v=>v===null||v===undefined?'Not assessed':v.toFixed(3);
  const colors=['#002d74','#b13d34','#1f716c','#7a5299','#99651b','#426b38','#a44877','#48677e','#715447','#686622','#5c55af','#31728e'];
  function render(fit,records,table){
    if(!fit.gmm)return '';
    const g=fit.gmm,byId=new Map(records.map(r=>[r.id,r]));
    const uncertain=[...fit.points].sort((a,b)=>a.max_membership-b.max_membership||a.id.localeCompare(b.id)).slice(0,12);
    const h=uncertain.length*32+42;
    const plot=`<div class="chart-wrap"><svg viewBox="0 0 880 ${h}" role="img" aria-label="Mixture membership for passages with the lowest maximum membership"><title>Least decisive model memberships; each bar sums to one</title>${uncertain.map((p,i)=>{const r=byId.get(p.id);let left=240;return `<a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer"><text x="0" y="${i*32+24}" font-size="13">${esc(r.country.slice(0,26))}<title>${esc(r.country+' · '+p.id)}</title></text></a>${p.memberships.map((v,j)=>{const start=left;left+=v*480;return `<rect x="${start}" y="${i*32+8}" width="${v*480}" height="22" fill="${colors[j%colors.length]}"><title>Component ${j+1}: ${v.toFixed(5)} · ${esc(p.id)}</title></rect>`;}).join('')}<text x="742" y="${i*32+24}" font-size="12">max ${p.max_membership.toFixed(3)}</text>`;}).join('')}<text x="240" y="${h-2}" font-size="12">0</text><text x="720" y="${h-2}" text-anchor="end" font-size="12">1</text></svg></div>`;
    let html=`<section class="gmm-section"><h4>Overlapping membership</h4><p>Each passage has a conditional membership for every component. Map colors and the ordinary cluster summaries use the largest membership. These values depend on the Gaussian model; they are not calibrated confidence in a stance, topic or policy alignment.</p>
      ${g.weights.length===1?'<p class="method-note">With one component, every membership is 1 and entropy is 0 by construction. This is a single-Gaussian reference, not evidence of a shared theme.</p>':''}
      ${g.warnings.map(w=>`<p class="warning">${esc(w)}</p>`).join('')}
      <p>${g.ambiguous_count} of ${fit.analyzed_count} passages have maximum membership below ${g.ambiguity_threshold.toFixed(2)}. This is an inspection threshold; no passage is removed or declared unassigned. Mean normalized entropy: ${number(g.mean_entropy)} (0 = concentrated, 1 = evenly spread).</p>
      ${table(['Component','Highest-membership count','Soft count','Mixture weight','Dimensions near floor'],fit.clusters.map((c,i)=>[c.cluster,c.size,number(g.soft_counts[i]),number(g.weights[i]),g.near_floor_dimensions[i]]))}
      <p class="method-note">Soft count is the sum of memberships, not a count of independently verified speeches. Near-floor dimensions have variance no more than 1.1 times the regularization setting.</p>
      <h4>Least decisive passages</h4>${plot}<div class="cluster-legend">${g.weights.map((_,i)=>`<span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="6" fill="${colors[i%colors.length]}"/></svg> Component ${i+1}</span>`).join('')}</div>
      <p class="method-note">Up to twelve passages with the lowest maximum membership, even when none falls below the threshold. All membership vectors remain in JSON and Cluster data CSV.</p>
      <details><summary>Inspect ambiguous-source examples</summary>${uncertain.map(p=>{const r=byId.get(p.id);return `<details><summary>${esc(r.country)} · max ${number(p.max_membership)} · entropy ${number(p.normalized_entropy)}</summary><p>${esc(p.id)}</p>${r.text?`<blockquote>${esc(r.text.slice(0,650))}${r.text.length>650?'…':''}</blockquote>`:''}<a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">Open original passage</a>${table(['Component','Membership'],p.memberships.map((v,i)=>[i+1,number(v)]))}</details>`;}).join('')}</details>
      <details><summary>Covariance, likelihood and starting-point checks</summary><p>${esc(g.convergence_rule)}</p>${table(['Measure','Value'],[
        ['Covariance model',g.covariance_type],['Additive variance regularization',g.regularization],['Free parameters',g.parameter_count],['Converged starts',g.converged_starts+' / '+g.starts],['Selected seed',g.selected_seed],['Iterations',g.iterations],['Final log likelihood',number(g.log_likelihood)],['AIC',number(g.aic)],['BIC',number(g.bic)]])}
      <p class="warning">Compare AIC and BIC only for the same observations, dimensions and representation. They do not choose between PCA and LSA, different retained dimensions or different passage subsets. Local optimization, regularization and dependent passages limit formal model-selection claims.</p>
      ${table(['Seed','Converged','Iterations','Log likelihood','Aligned membership change (TV)','Status'],g.runs.map(r=>[r.seed,r.converged?'Yes':'No',r.iterations??'—',number(r.log_likelihood),number(r.soft_agreement?.mean_total_variation),r.skipped||(r.converged?'Eligible':'Iteration limit')]))}</details>`;
    const s=fit.stability;
    if(s?.soft_membership&&!s.skipped){
      const m=s.soft_membership.mean_total_variation;
      html+=`<h4>Membership sensitivity to omitted groups</h4><p>${m.count} fitted samples have mean aligned total variation ${number(m.mean)} (0–1; lower is more consistent). Components are matched one-to-one by posterior overlap on shared passage IDs. PCA/LSA axes are independently refitted, so their means are not aligned directly.</p><p class="method-note">The cluster stability section separately reports highest-membership ARI, Jaccard and co-assignment. These hard summaries can hide changes in overlapping memberships. Repeated source omissions are not independent evidence.</p>
      <details><summary>Passages with largest membership changes</summary>${table(['Passage','Country','Times sampled','Mean TV','Minimum','Maximum'],[...s.soft_membership.points].filter(p=>p.count).sort((a,b)=>b.mean-a.mean||a.id.localeCompare(b.id)).slice(0,20).map(p=>[p.id,byId.get(p.id).country,p.count,number(p.mean),number(p.min),number(p.max)]))}</details>`;
    }
    return html+'</section>';
  }
  const api={render,colors};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNGaussianView=api;
})(globalThis);
