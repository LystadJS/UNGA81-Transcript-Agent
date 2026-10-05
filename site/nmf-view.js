/* Script-free report sections, also used in downloaded HTML and audit reports. */
(function(root){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number=v=>v===null||v===undefined?'Not assessed':v.toFixed(3);
  const link=(source,label)=>source&&/^https:\/\//.test(source)?`<a href="${esc(source)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`:esc(label);
  function bars(title,items,label,value,max=1){
    const h=items.length*32+40;
    return `<div class="chart-wrap"><svg viewBox="0 0 850 ${h}" role="img" aria-label="${esc(title)}"><title>${esc(title)}; bars start at zero</title>${items.map((d,i)=>`<text x="0" y="${i*32+24}">${esc(label(d))}</text><rect x="210" y="${i*32+8}" width="${Math.max(0,value(d)/max*500)}" height="21" fill="#002d74"/><text x="730" y="${i*32+24}">${number(value(d))}</text>`).join('')}<text x="210" y="${h-1}">0</text><text x="710" y="${h-1}" text-anchor="end">${number(max)}</text></svg></div>`;
  }
  function render(fit,records,table){
    if(fit.skipped)return `<section class="result-section"><h3>NMF components</h3><p class="warning">${esc(fit.skipped)}</p></section>`;
    const byId=new Map(records.map(r=>[r.id,r])),d=fit.diagnostics,s=fit.stability;
    let html=`<section class="result-section nmf-report"><h3>NMF · overlapping components</h3><p>${fit.usable_count} usable passages · ${fit.components.length} components · ${fit.vocabulary_count.toLocaleString()} terms.</p><p>Each passage can draw on several components. These are lexical patterns; names and political interpretations require source review. Mixture shares are normalized weights, not probabilities.</p>`;
    html+=fit.warnings.map(w=>`<p class="warning">${esc(w)}</p>`).join('');
    html+=bars('Mean normalized component weight across usable passages',fit.components,c=>'Component '+c.component,c=>c.mean_share);
    html+=`<p class="hint">Each usable passage has equal weight. Undefined mixtures contribute zero and remain identified in the data. Reconstruction captured ${(100*d.squared_reconstruction_fraction).toFixed(1)}% of squared TF-IDF magnitude; this is an in-sample reconstruction measure, not explained variance or predictive accuracy.</p>`;
    html+=`<details><summary>Optimization and starting-point sensitivity</summary><p>Lowest residual of ${d.starts.length} starts. Relative residual: ${number(d.relative_residual)}. ${esc(d.convergence_rule)}</p>${table(['Seed','Iterations','Stopping rule met','Residual','Aligned cosine to selected fit','Mixture L1 difference'],d.starts.map(r=>[r.seed,r.iterations,r.converged?'Yes':'No',number(r.residual),number(r.alignment.mean_cosine),number(r.alignment.mean_mixture_l1)]))}</details>`;
    if(s.skipped)html+=`<p class="hint">${esc(s.skipped)}</p>`;
    else{
      html+=`<h4>Component stability</h4><p>${s.successful}/${s.attempted} samples fitted; ${s.converged} met the stopping rule. ${s.unique_group_samples} distinct group samples. Mean aligned cosine: ${number(s.cosine.mean)}; converged-only: ${number(s.converged_cosine.mean)}. Mean mixture L1 difference: ${number(s.mixture_l1.mean)} (0–2).</p>`;
      html+=s.warnings.map(w=>`<p class="warning">${esc(w)}</p>`).join('');
      html+=bars('Mean aligned component cosine in grouped refits',s.components,c=>'Component '+c.component,c=>c.mean??0);
      html+=`<details><summary>Stability values and sample coverage</summary><p>${esc(s.procedure)} Cosine uses a 0–1 scale; higher means more similar term weights. Stability does not validate a theme.</p>${table(['Component','Assessable samples','Mean cosine','Minimum','Maximum'],s.components.map(c=>[c.component,c.count,number(c.mean),number(c.min),number(c.max)]))}${table(['Sample','Usable','Stopping rule met','Mean cosine','Mixture L1'],s.runs.map(r=>[r.attempt,r.usable_count??r.selected_count,r.skipped??(r.converged?'Yes':'No'),number(r.mean_cosine),number(r.mean_mixture_l1)]))}</details>`;
    }
    for(const c of fit.components){
      html+=`<details class="nmf-component"><summary>Component ${c.component} · ${esc(c.terms.slice(0,5).map(t=>t.term).join(', '))}</summary>${bars('Component '+c.component+' term weights',c.terms,t=>t.term,t=>t.weight,Math.max(...c.terms.map(t=>t.weight),EPS))}<p>Terms use unit-length component weights. Sources below have the largest absolute loading on this component. ${records.some(r=>r.text)?'Excerpts show the start of each original passage.':'Follow a source link to inspect the original passage.'}</p><ol>`;
      for(const p of c.sources){const r=byId.get(p.id);html+=`<li>${link(r?.source_url,(r?.country||p.id)+' · '+(r?.date||''))} · loading ${number(p.weight)} · share ${number(p.share)}${r?.text?`<blockquote>${esc(r.text.slice(0,650))}${r.text.length>650?'…':''}</blockquote>`:''}<small>${esc(p.id)}</small></li>`;}
      html+='</ol></details>';
    }
    if(fit.excluded.length)html+=`<details><summary>${fit.excluded.length} zero-term exclusions</summary>${table(['Source ID','Reason'],fit.excluded.map(p=>[p.id,p.reason]))}</details>`;
    return html+'</section>';
  }
  const EPS=1e-16,api={render,bars};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNNMFView=api;
})(globalThis);
