/* Script-free MDS comparison, with equal axis scaling and source identities. */
(function(root){
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number=v=>v===null||v===undefined?'Not assessed':v.toFixed(3);
  const colors=['#002d74','#b13d34','#1f716c','#7a5299','#99651b','#426b38','#a44877','#48677e','#715447','#686622','#5c55af','#31728e'];
  function scatter(points,records,key='mds',title='Metric MDS · fixed memberships'){
    const byId=new Map(records.map(r=>[r.id,r])),lo=[0,1].map(d=>Math.min(...points.map(p=>p[key][d]))),hi=[0,1].map(d=>Math.max(...points.map(p=>p[key][d])));
    const unit=Math.min(800/(hi[0]-lo[0]||1),390/(hi[1]-lo[1]||1)),x=v=>450+(v-(lo[0]+hi[0])/2)*unit,y=v=>218-(v-(lo[1]+hi[1])/2)*unit;
    return `<div class="cluster-map"><svg viewBox="0 0 900 490" role="group" aria-label="${esc(title)}"><title>${esc(title)}; equal scale on both axes</title><rect x="35" y="12" width="830" height="414" fill="#f5f7fa"/>
      ${points.map(p=>{const r=byId.get(p.id),cx=x(p[key][0]),cy=y(p[key][1]);return `<a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(r.country+' · '+p.id)}">${p.cluster===0?`<path d="M ${cx-3} ${cy-3} l 6 6 m -6 0 l 6 -6" stroke="#667580"/>`:`<circle cx="${cx}" cy="${cy}" r="4" stroke="#fff" stroke-width=".6" fill="${colors[(p.cluster-1)%colors.length]}"/>`}<title>${esc(r.country+' · '+r.date+' · '+p.id+' · '+(p.cluster?'Group '+p.cluster:'Unassigned'))}</title></a>`;}).join('')}
      <text x="450" y="477" text-anchor="middle">${key==='mds'?'MDS':'UMAP'} 1</text><text x="17" y="230" transform="rotate(-90 17 230)" text-anchor="middle">${key==='mds'?'MDS':'UMAP'} 2</text></svg></div>`;
  }
  function shepard(m){
    const limit=Math.max(...m.bins.flatMap(b=>[b.upper,b.max]))||1,x=v=>70+420*v/limit,y=v=>450-420*v/limit;
    return `<div class="chart-wrap"><svg viewBox="0 0 580 520" role="img" aria-label="Binned target and MDS distances; all passage pairs"><title>All pairs binned by target distance; marks are means, lines are observed minimum–maximum</title><path d="M 70 30 V 450 H 490 M 70 450 L 490 30" fill="none" stroke="#677789"/>
      ${[0,.25,.5,.75,1].map(t=>`<text x="${x(t*limit)}" y="474" text-anchor="middle" font-size="12">${number(t*limit)}</text><text x="60" y="${y(t*limit)+4}" text-anchor="end" font-size="12">${number(t*limit)}</text>`).join('')}
      ${m.bins.map(b=>`<line x1="${x(b.target_mean)}" x2="${x(b.target_mean)}" y1="${y(b.min)}" y2="${y(b.max)}" stroke="#a1acb7"/><circle cx="${x(b.target_mean)}" cy="${y(b.display_mean)}" r="4" fill="#002d74"><title>${b.count} pairs; target mean ${number(b.target_mean)}, display mean ${number(b.display_mean)}</title></circle>`).join('')}
      <text x="280" y="508" text-anchor="middle">Retained-score distance</text><text x="15" y="250" transform="rotate(-90 15 250)" text-anchor="middle">MDS distance</text></svg></div>`;
  }
  function render(fit,records,table){
    const m=fit.mds;if(!m)return '';let out='<section class="mds-section"><h4>Metric MDS comparison</h4>';
    if(m.skipped)return out+`<p class="warning">${esc(m.skipped)}</p></section>`;
    const byId=new Map(records.map(r=>[r.id,r]));
    out+=`<p>MDS fits pairwise Euclidean distances in all retained ${fit.representation.toUpperCase()} dimensions. Colors and unassigned markers retain the original clustering. Positions, gaps and axes are a geometric display, not validated political relationships.</p>${m.warnings.map(w=>`<p class="warning">${esc(w)}</p>`).join('')}${scatter(fit.points,records)}
      ${table(['Measure','UMAP','Metric MDS'],[['Ten-neighbor overlap (or smaller available set)',number(fit.fidelity.display.neighbor_overlap),number(m.fidelity.neighbor_overlap)],['Trustworthiness',number(fit.fidelity.display.trustworthiness),number(m.fidelity.trustworthiness)],['Continuity',number(fit.fidelity.display.continuity),number(m.fidelity.continuity)]])}
      <p class="method-note">Both comparisons use ${m.fidelity.neighbors} nearest neighbors in the same retained representation. Higher values preserve more local geometry. MDS instead optimizes raw distance stress across all pairs; neither objective establishes substantive validity.</p>
      <details><summary>Distance error and optimization</summary>${table(['Measure','Value'],[['Raw stress',number(m.stress)],['Relative distance error: target denominator',number(m.relative_distance_error)],['Stress-1: display denominator',number(m.stress1)],['Selected seed',m.seed],['Iterations',m.iterations],['Stopping rule met',m.converged?'Yes':'No — provisional'],['Unordered pairs',m.pair_count],['Zero-distance pairs retained',m.zero_target_pairs]])}
      <p class="method-note">Raw stress is the sum of squared differences between target and displayed distances. Relative distance error divides by squared target distances before taking the square root; Stress-1 uses squared displayed distances. No categorical quality cutoff is applied. Coordinates are in retained-score distance units; each plot has its own orientation and bounds.</p>${shepard(m)}<p class="method-note">Every pair enters one of twenty equal-width target-distance bins. Dots are bin means; vertical lines show observed minimum–maximum, not confidence intervals. The diagonal is exact preservation.</p>
      ${table(['Seed','Iterations','Converged','Raw stress','Relative distance error','Status'],m.runs.map(r=>[r.seed,r.iterations??'—',r.converged?'Yes':'No',number(r.stress),number(r.relative_distance_error),r.skipped||(r.converged?'Fitted':'Iteration limit')]))}<p class="method-note">${esc(m.selection)}. ${esc(m.convergence_rule)}. Local convergence does not prove a global optimum. Complete histories and coordinates remain in JSON.</p></details>
      <details><summary>Passages with the largest distance distortion</summary><p class="method-note">Per-passage root mean squared distance error, divided by the global root mean squared target distance. These are display-inspection leads; no membership or source is changed.</p>${table(['Passage','Country','Relative error','MDS 1','MDS 2'],fit.points.map((p,i)=>({...p,error:m.point_relative_error[i]})).sort((a,b)=>b.error-a.error||a.id.localeCompare(b.id)).slice(0,10).map(p=>[p.id,byId.get(p.id).country,number(p.error),number(p.mds[0]),number(p.mds[1])]))}</details>`;
    return out+'</section>';
  }
  const api={render,scatter,shepard};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNMDSView=api;
})(globalThis);
