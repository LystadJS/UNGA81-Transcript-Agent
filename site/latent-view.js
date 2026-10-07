/* Script-free exports and escaped, source-linked comparison views. */
(function(root){
  'use strict';
  const e=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const n=value=>Number.isFinite(value)?value.toFixed(3):'—';
  const pct=value=>Number.isFinite(value)?(100*value).toFixed(1)+'%':'—';
  const source=(url,label)=>/^https:\/\//.test(url||'')?`<a href="${e(url)}" target="_blank" rel="noopener noreferrer">${e(label)}</a>`:e(label);
  function table(headers,rows){return `<div class="table-scroll"><table><thead><tr>${headers.map(h=>`<th scope="col">${e(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>'<tr>'+row.map(x=>`<td>${x}</td>`).join('')+'</tr>').join('')}</tbody></table></div>`;}
  const width=value=>Math.max(0,Math.min(1,Number.isFinite(value)?value:0))*500;
  function coverageBars(rows,label='Selected excerpts'){
    if(!rows?.length)return '';
    return `<figure class="coverage-chart"><figcaption>${e(label)} · original speech text covered</figcaption><p class="hint">Every bar spans 0–100% of its original speech. Navy is retained text; gray is omitted text. Coverage measures source characters, not audio accuracy.</p>${rows.map(r=>`<div class="coverage-row"><div class="bar-label">${source(r.source_url,r.country)}<span>${pct(r.coverage_fraction)} · ${r.passages} excerpts</span></div><svg viewBox="0 0 500 16" preserveAspectRatio="none" role="img" aria-label="${e(r.country)}: ${pct(r.coverage_fraction)} retained, ${pct(1-r.coverage_fraction)} omitted"><rect class="bar-background" width="500" height="16"/><rect class="passage-bar" width="${width(r.coverage_fraction)}" height="16"/></svg></div>`).join('')}</figure>`;
  }
  function weightingBars(rows,title,key='cluster',balance='Parent balanced'){
    return `<figure class="weighting-chart"><figcaption>${e(title)}</figcaption><p class="hint">Common 0–100% scale. Upper navy bars: passage weighted. Lower gold bars: ${e(balance.toLowerCase())}. These are summaries of the same fit.</p>${rows.map(r=>`<div class="weighting-row"><strong>${key==='cluster'?(r.cluster?'Group '+r.cluster:'Unassigned'):'Component '+r.component}</strong><div class="bar-label"><span>Passage weighted ${pct(r.passage_weighted)}</span><span>${e(balance)} ${pct(r.parent_balanced)}</span></div><svg viewBox="0 0 500 32" preserveAspectRatio="none" role="img" aria-label="Passage weighted ${pct(r.passage_weighted)}; ${e(balance)} ${pct(r.parent_balanced)}"><rect class="bar-background" width="500" height="12"/><rect class="bar-background" y="20" width="500" height="12"/><rect class="passage-bar" width="${width(r.passage_weighted)}" height="12"/><rect class="parent-bar" y="20" width="${width(r.parent_balanced)}" height="12"/></svg></div>`).join('')}</figure>`;
  }
  function mixtureView(entry){
    const L=typeof module!=='undefined'&&module.exports?require('./latent-core.js'):root.UNLatent;
    const m=entry.mixture===undefined?L.mixtures(entry):entry.mixture;if(!m)return '';
    const group=entry.unit==='source'?'source records':'parents',balance=entry.unit==='source'?'Source-record balanced':'Parent balanced';
    return `<h4>Overlapping component weights</h4><p>${e(m.role)} ${e(m.fitting)}</p><p>${m.defined_passages} of ${m.passage_count} usable passages and ${m.defined_parents} of ${m.parent_count} represented ${group} have defined shares. Undefined shares are excluded from these summaries.${entry.unit==='source'?' Original source records are not verified complete speeches.':''}</p>`+
      weightingBars(m.totals,'Component composition under two summary weights','component',balance)+
      `<details><summary>Component profiles and sources</summary><p class="hint">Means within represented ${group}, conditional on defined passage shares. Components are local to this fit; they are not reviewed theme or stance labels. Showing ${Math.min(30,m.rows.length)} of ${m.rows.length} ${group} in source order; JSON retains every row.</p>`+
      table(['Original source','Defined / usable observations',...m.totals.map(r=>'Component '+r.component)],m.rows.slice(0,30).map(r=>[source(r.source_url,(r.country||'Source')+' · '+r.parent_id),r.defined+' / '+r.usable,...r.shares.map(v=>`<span class="profile-cell ${Number.isFinite(v)?'shade-'+Math.min(4,Math.floor(v*5)):'undefined-share'}">${pct(v)}</span>`)]))+'</details>';
  }
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
    const rows=result.entries.map(entry=>{const s=entry.summary||{};return [e(entry.id),e(entry.label),e(entry.unit),e(s.matched??'—'),e(s.parents??'—'),e(s.usable??'—'),pct(s.assignment_fraction),pct(s.largest_fraction),n(s.silhouette),n(s.mean_ari),e(s.assessable_ari??'—'),e(s.refits??'—'),e(s.distinct_omissions??'—'),e(s.reason||s.status||'')];});
    let output=`<p class="notice">${e(result.interpretation||'Exploratory settings comparison, not a significance test or policy-alignment model.')}</p><p>${e(result.weighting||'Each fit retains its documented weighting. No automatic model winner is selected.')}</p>`;
    if(result.plan)output+=`<p><strong>Selection:</strong> ${e(result.plan.base.start)} to ${e(result.plan.base.end)} · ${e(result.plan.base.scope)} · ${e(result.plan.base.region)} · ${e(result.plan.base.topic||'all passages')}.</p>`;
    if(result.counts)output+=`<p><strong>Observed source accounting:</strong> ${result.counts.input} input records; ${result.counts.eligible_before_dedup} eligible before deduplication; ${result.counts.duplicates} duplicate exclusions; ${result.counts.matched} retained matches. Missing inventory is not issue absence.</p>`;
    if(result.coverage?.length){
      output+='<h3>Parent coverage and weighting</h3><p>'+e(result.parent_comparison)+'</p>';
      output+=coverageBars(result.coverage);
      output+=table(['Parent speech','Retained excerpts','Original text covered','Share of excerpt observations','Equal-parent summary weight'],result.coverage.map(r=>[source(r.source_url,r.country+' · '+r.parent_id),e(r.passages),pct(r.coverage_fraction),pct(r.passage_weight),pct(r.equal_parent_summary_weight)]));
    }
    if(result.snapshots){
      output+='<h3>Saved-run coverage and weighting</h3><div class="snapshot-grid">'+result.snapshots.map(s=>`<section class="saved-snapshot"><h4>Run ${e(s.label)}</h4><p>${e(s.plan.base.start)}–${e(s.plan.base.end)} · ${e(s.plan.base.topic||'All passages')} · ${e(s.plan.base.region)}</p><p>${s.counts.matched} retained matches; ${s.counts.duplicates} duplicate exclusions. ${s.coverage.length} parent speeches in the reviewed-excerpt coverage table.</p>${coverageBars(s.coverage,'Run '+s.label)}<details><summary>Run ${e(s.label)} selection and weights</summary><p>${e(s.parent_comparison||'Original source-segment analysis.')}</p><p>${e(s.weighting)}</p>${table(['Parent','Retained excerpts','Text covered','Observation share','Equal-parent summary weight'],s.coverage.map(r=>[source(r.source_url,r.country+' · '+r.parent_id),e(r.passages),pct(r.coverage_fraction),pct(r.passage_weight),pct(r.equal_parent_summary_weight)]))}<p class="hint">Source SHA-256 ${e(s.source_hash)}<br>Selection SHA-256 ${e(s.selection_hash)}</p></details></section>`).join('')+'</div>';
      if(result.coverage_change?.length)output+='<h4>Coverage changes between archived runs</h4><p class="hint">Changes are percentage points, B minus A. An absent parent is outside that retained cohort, not evidence of zero issue coverage. Changed original text prevents a like-for-like coverage difference.</p>'+table(['Parent','A text covered','B text covered','Coverage change','Observation-share change','Comparison status'],result.coverage_change.map(r=>[e(r.country+' · '+r.parent_id),pct(r.left?.coverage_fraction),pct(r.right?.coverage_fraction),Number.isFinite(r.coverage_change)?e((100*r.coverage_change).toFixed(1)+' pp'):'—',Number.isFinite(r.observation_share_change)?e((100*r.observation_share_change).toFixed(1)+' pp'):'—',e(r.reason||'Same original parent text')]));
    }
    const parentFits=result.entries.filter(r=>r.unit==='parent');
    if(parentFits.length&&parentFits.every(r=>r.summary?.status==='withheld'))output+='<p class="notice parent-withheld"><strong>Whole-speech models were withheld.</strong> Coverage and weighting comparisons remain available. Inspect the fit reasons below; additional excerpts from these same parents do not increase the number of speeches.</p>';
    output+='<h3>Settings diagnostics</h3>'+table(['Fit','Setting','Unit','Retained','Parents / source records','Usable vectors','Assigned','Largest group / all usable','Silhouette','Mean refit ARI','Assessable ARIs','Fitted refits','Distinct omissions','Status'],rows);
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
        if(entry.composition){output+='<h4>Composition under two summary weights</h4><p>'+e(entry.composition.role)+'</p>'+weightingBars(entry.composition.totals,'Hard-assignment composition under two summary weights','cluster',entry.unit==='source'?'Source-record balanced':'Parent balanced');}
        output+='<details><summary>Representation, display and refit diagnostics</summary><pre>'+e(JSON.stringify({representation:fit[fit.representation],fidelity:fit.fidelity?{representation:{...fit.fidelity.representation,points:undefined},display:{...fit.fidelity.display,points:undefined}}:null,clustering:fit.clustering,gmm:fit.gmm?{warnings:fit.gmm.warnings,entropy:fit.gmm.mean_entropy}:undefined,mds:fit.mds?{...fit.mds,starts:undefined,history:undefined}:undefined,stability:fit.stability?{...fit.stability,runs:undefined,pairs:undefined,consensus:undefined,points:undefined,groups:undefined}:null},null,2))+'</pre></details>';
      }else if(fit?.components){
        const by=new Map(entry.result.matched.map(r=>[r.id,r]));
        output+=table(['Component','Mean descriptive share','Terms','Source examples'],fit.components.map(c=>[e(c.component),pct(c.mean_share),e(c.terms.map(t=>t.term).join(', ')),c.sources.slice(0,3).map(p=>source(by.get(p.id)?.source_url,p.id)).join('<br>')]));
      }
      output+=mixtureView(entry);
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
  function rowsCSV(rows){
    const cell=value=>{let s=String(value??'');if(/^[=+@\t\r]/.test(s)||(/^\s*-/.test(s)&&!Number.isFinite(value)))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};
    return '\uFEFF'+rows.map(row=>row.map(cell).join(',')).join('\r\n')+'\r\n';
  }
  function coverageCSV(result){
    const snapshots=result.snapshots||[{label:'Current',coverage:result.coverage||[]}];
    return rowsCSV([['run','parent_id','parent_text_sha256','country','source_url','retained_excerpts','selected_code_points','parent_code_points','coverage_fraction','passage_weight','equal_parent_summary_weight'],...snapshots.flatMap(s=>s.coverage.map(r=>[s.label,r.parent_id,r.parent_text_sha256,r.country,r.source_url,r.passages,r.selected_code_points,r.parent_code_points,r.coverage_fraction,r.passage_weight,r.equal_parent_summary_weight]))]);
  }
  function weightsCSV(result){
    const L=typeof module!=='undefined'&&module.exports?require('./latent-core.js'):root.UNLatent;
    return rowsCSV([['fit','unit','method','quantity','component_or_group','passage_weighted','balanced_share','defined_passages','defined_groups','undefined_shares','balance_unit'],...result.entries.flatMap(entry=>{
      const m=entry.mixture===undefined?L.mixtures(entry):entry.mixture,c=entry.composition;
      const balance=entry.unit==='source'?'original_source_record':'parent_speech';
      return [...(c?c.totals.map(r=>[entry.id,entry.unit,entry.method,'hard_assignment',r.cluster,r.passage_weighted,r.parent_balanced,c.passage_count,c.parent_count,0,balance]):[]),...(m?m.totals.map(r=>[entry.id,entry.unit,entry.method,m.kind,r.component,r.passage_weighted,r.parent_balanced,m.defined_passages,m.defined_parents,m.undefined_ids.length,balance]):[])];
    })]);
  }
  const api={escape:e,html,csv,coverageCSV,weightsCSV,scatter,coverageBars,weightingBars};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNLatentView=api;
})(globalThis);
