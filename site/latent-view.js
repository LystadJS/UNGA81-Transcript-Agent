/* Script-free exports and escaped, source-linked comparison views. */
(function(root){
  'use strict';
  const e=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const n=value=>Number.isFinite(value)?value.toFixed(3):'—';
  const pct=value=>Number.isFinite(value)?(100*value).toFixed(1)+'%':'—';
  const source=(url,label)=>/^https:\/\//.test(url||'')?`<a href="${e(url)}" target="_blank" rel="noopener noreferrer">${e(label)}</a>`:e(label);
  function table(headers,rows){return `<div class="table-scroll"><table><thead><tr>${headers.map(h=>`<th scope="col">${e(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>'<tr>'+row.map(x=>`<td>${x}</td>`).join('')+'</tr>').join('')}</tbody></table></div>`;}
  function scatter(entry,key){
    const fit=entry.result.methods.clusters,points=fit.points;
    if(!points?.length||!points.every(p=>Array.isArray(p[key])))return '';
    const records=new Map(entry.result.matched.map(r=>[r.id,r]));
    const xs=points.map(p=>p[key][0]),ys=points.map(p=>p[key][1]||0),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);
    const span=Math.max(xmax-xmin,ymax-ymin,1e-12),cx=(xmin+xmax)/2,cy=(ymin+ymax)/2;
    const marks=points.map(p=>{const r=records.get(p.id),x=210+350*(p[key][0]-cx)/span,y=210-350*((p[key][1]||0)-cy)/span,label=`${r?.country||''} · ${p.id} · ${p.cluster?'group '+p.cluster:'unassigned'}`,shape=p.cluster?`<circle class="c${(p.cluster-1)%8}" cx="${x}" cy="${y}" r="3.5"/>`:`<path class="noise" d="M${x-3},${y-3}l6,6m-6,0l6,-6"/>`;
      return `<a href="${e(r.source_url)}" target="_blank" rel="noopener noreferrer"><title>${e(label)}</title>${shape}</a>`;}).join('');
    return `<figure><figcaption>${e(entry.id)} · ${e(key.toUpperCase())} · ${points.length} passages</figcaption><svg viewBox="0 0 420 420" role="img" aria-label="${e(key)} display with source-linked points; equal axis scaling"><rect class="plot-frame" x="20" y="20" width="380" height="380"/>${marks}</svg><p class="hint">Equal axis units. Colors are local fitted group IDs, not diplomatic labels. Crosses remain unassigned. ${key==='umap'||key==='mds'?'Display only; the plotted coordinates did not determine groups.':'Only the first two retained axes are displayed; fitting used every retained axis.'}</p></figure>`;
  }
  function heatmap(result,unit){
    const entries=result.entries.filter(r=>r.unit===unit&&r.method==='clusters');if(entries.length<2)return '';
    const pairs=new Map(result.pairs.map(p=>[[p.left,p.right].sort().join('|'),p]));
    const size=entries.length,cell=30,width=130+cell*size;
    let marks='';
    for(let i=0;i<size;i++)for(let j=0;j<size;j++){
      const p=pairs.get([entries[i].id,entries[j].id].sort().join('|')),value=i===j?null:p?.ari;
      const cls=i===j?'diagonal':!Number.isFinite(value)?'missing':value<0?'negative':'agreement';
      const opacity=Number.isFinite(value)?0.15+0.85*Math.abs(value):1;
      marks+=`<rect class="${cls}" fill-opacity="${opacity}" x="${110+j*cell}" y="${35+i*cell}" width="28" height="28"><title>${e(entries[i].id)} / ${e(entries[j].id)}: ${i===j?'self comparison not shown':Number.isFinite(value)?n(value)+'; shared assigned n='+p.ari_denominator:e(p?.withheld||p?.ari_reason||'Not assessed')}</title></rect>`;
    }
    entries.forEach((r,i)=>{marks+=`<text x="105" y="${54+i*cell}" text-anchor="end">${e(r.id)}</text><text x="${124+i*cell}" y="25" text-anchor="middle">${i+1}</text>`;});
    return `<figure><figcaption>${e(unit)} · cross-setting assignment agreement</figcaption><svg viewBox="0 0 ${width} ${50+size*cell}" role="img" aria-label="Adjusted Rand agreement across settings">${marks}</svg><p class="hint">Navy: ARI from 0 to 1; red: negative ARI. Gray: withheld; white: self comparison. Exact values and assigned-passage denominators appear below. Higher agreement is not a validity score.</p></figure>`;
  }
  function html(result){
    const rows=result.entries.map(entry=>{const s=entry.summary||{};return [e(entry.id),e(entry.label),e(entry.unit),e(s.usable??'—'),pct(s.assignment_fraction),pct(s.largest_fraction),n(s.silhouette),n(s.mean_ari),e(s.assessable_ari??'—'),e(s.refits??'—'),e(s.distinct_omissions??'—'),e(s.reason||s.status||'')];});
    let output=`<p class="notice">${e(result.interpretation||'Exploratory settings comparison, not a significance test or policy-alignment model.')}</p><p>${e(result.weighting||'Each fit retains its documented weighting. No automatic model winner is selected.')}</p>`;
    if(result.plan)output+=`<p><strong>Selection:</strong> ${e(result.plan.base.start)} to ${e(result.plan.base.end)} · ${e(result.plan.base.scope)} · ${e(result.plan.base.region)} · ${e(result.plan.base.topic||'all passages')}.</p>`;
    if(result.counts)output+=`<p><strong>Observed source accounting:</strong> ${result.counts.input} input records; ${result.counts.eligible_before_dedup} eligible before deduplication; ${result.counts.duplicates} duplicate exclusions; ${result.counts.matched} retained matches. Missing inventory is not issue absence.</p>`;
    if(result.coverage?.length){
      output+='<h3>Parent coverage and weighting</h3><p>'+e(result.parent_comparison)+'</p>';
      output+=table(['Parent speech','Retained excerpts','Original text covered','Share of excerpt observations','Equal-parent summary weight'],result.coverage.map(r=>[source(r.source_url,r.country+' · '+r.parent_id),e(r.passages),pct(r.coverage_fraction),pct(r.passage_weight),pct(r.equal_parent_summary_weight)]));
    }
    output+='<h3>Settings diagnostics</h3>'+table(['Fit','Setting','Unit','Usable','Assigned','Largest group / all usable','Silhouette','Mean refit ARI','Assessable ARIs','Fitted refits','Distinct omissions','Status'],rows);
    const nmf=result.entries.filter(r=>r.method==='nmf');
    if(nmf.length)output+='<h3>NMF reconstruction and component sensitivity</h3>'+table(['Fit','Rank','Relative residual','Converged','Refit component cosine'],nmf.map(r=>[e(r.id),e(r.summary.components??'—'),n(r.summary.relative_residual),e(r.summary.converged??'—'),n(r.summary.refit_cosine)]))+'<p class="hint">Residuals describe each fitted matrix, not predictive accuracy. Changing the population changes the comparison. Iteration-limited results remain provisional.</p>';
    output+='<div class="plots">'+[...new Set(result.entries.map(r=>r.unit))].map(u=>heatmap(result,u)).join('')+'</div>';
    output+='<h3>Paired comparisons</h3>'+table(['Left','Right','ARI','Assigned in both','Left only','Right only','Unassigned in both','Same scores','Same labels','Same UMAP','Paired omission schedule','Other comparison / withheld reason'],result.pairs.map(p=>[e(p.left),e(p.right),n(p.ari),e(p.ari_denominator??'—'),e(p.transitions?.left_only??'—'),e(p.transitions?.right_only??'—'),e(p.transitions?.unassigned_both??'—'),e(p.geometry_identical??'—'),e(p.labels_identical??'—'),e(p.umap_identical??'—'),e(p.paired_group_schedule??'—'),e(p.withheld||p.ari_reason||(p.nmf?'NMF cosine '+n(p.nmf.mean_cosine)+'; mixture L1 '+n(p.nmf.mean_mixture_l1)+'; n='+p.nmf.shared_passages:p.soft?'Aligned soft memberships retained in JSON.':''))]));
    for(const entry of result.entries){
      const fit=entry.result?.methods?.[entry.method];
      output+=`<details><summary>${e(entry.id)} · ${e(entry.label)} · inspect sources, maps and diagnostics</summary>`;
      if(fit?.skipped){output+=`<p>${e(fit.skipped)}</p></details>`;continue;}
      if(entry.method==='clusters'){
        output+='<div class="plots">'+scatter(entry,fit.representation)+scatter(entry,'umap')+scatter(entry,'mds')+'</div>';
        const by=new Map(entry.result.matched.map(r=>[r.id,r]));
        output+=table(['Group','Size','Example source','Highest-weight terms'],fit.clusters.map(c=>[e(c.cluster),e(c.size),source(by.get(c.representative_id)?.source_url,c.representative_id),e(c.terms.map(t=>t.term).join(', '))]));
        if(entry.composition){output+='<h4>Passage-weighted versus parent-balanced composition</h4><p>'+e(entry.composition.role)+'</p>'+table(['Group','Passage weighted','Parent balanced'],entry.composition.totals.map(r=>[e(r.cluster||'Unassigned'),pct(r.passage_weighted),pct(r.parent_balanced)]));}
        output+='<details><summary>Representation, display and refit diagnostics</summary><pre>'+e(JSON.stringify({representation:fit[fit.representation],fidelity:fit.fidelity?{representation:{...fit.fidelity.representation,points:undefined},display:{...fit.fidelity.display,points:undefined}}:null,clustering:fit.clustering,gmm:fit.gmm?{warnings:fit.gmm.warnings,entropy:fit.gmm.mean_entropy}:undefined,mds:fit.mds?{...fit.mds,starts:undefined,history:undefined}:undefined,stability:fit.stability?{...fit.stability,runs:undefined,pairs:undefined,consensus:undefined,points:undefined,groups:undefined}:null},null,2))+'</pre></details>';
      }else if(fit?.components){
        const by=new Map(entry.result.matched.map(r=>[r.id,r]));
        output+=table(['Component','Mean descriptive share','Terms','Source examples'],fit.components.map(c=>[e(c.component),pct(c.mean_share),e(c.terms.map(t=>t.term).join(', ')),c.sources.slice(0,3).map(p=>source(by.get(p.id)?.source_url,p.id)).join('<br>')]));
      }
      output+='<details><summary>Exact run settings and evidence counts</summary><pre>'+e(JSON.stringify({parameters:entry.result.parameters,counts:entry.result.counts,excluded:fit?.excluded,warnings:fit?.warnings,source_coverage:entry.result.coverage},null,2))+'</pre></details></details>';
    }
    output+='<details><summary>Runtime and source fingerprints</summary><pre>'+e(JSON.stringify({engine:result.engine,runtime:result.runtime,source_hash:result.source_hash,selection_hash:result.selection_hash},null,2))+'</pre></details>';
    return output;
  }
  function csv(result){
    const keys=['id','label','unit','method','status','reason','matched','duplicates','parents','usable','representation','algorithm','components','assigned','assignment_fraction','largest_fraction','silhouette','silhouette_denominator','retained_variance','mean_ari','assessable_ari','refits','distinct_omissions','converged','relative_residual','refit_cosine'];
    const cell=value=>{let s=String(value??'');if(/^[=+@\t\r]/.test(s)||(/^\s*-/.test(s)&&!Number.isFinite(value)))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};
    return '\uFEFF'+[keys,...result.entries.map(r=>keys.map(k=>r.summary?.[k]??''))].map(row=>row.map(cell).join(',')).join('\r\n')+'\r\n';
  }
  const api={escape:e,html,csv,scatter};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNLatentView=api;
})(globalThis);
