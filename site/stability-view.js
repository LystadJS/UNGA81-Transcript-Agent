/* Script-free, source-linked stability views for the page and HTML export. */
(function(root) {
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number=v=>v===null||v===undefined?'Not assessed':v.toFixed(3);
  const pairIndex=(i,j)=>{const a=Math.max(i,j),b=Math.min(i,j);return a*(a-1)/2+b;};

  function heatmap(s) {
    const {co_observed:observed,co_clustered:together}=s.consensus;
    // Contiguous bins stay inside reference clusters. All pairs contribute;
    // this is aggregation for readability, never a subsample of passages.
    const size=Math.max(1,Math.ceil(s.reference_ids.length/48)),bins=[];
    for(const c of [...new Set(s.reference_clusters)].sort((a,b)=>a-b)) {
      const rows=s.reference_ids.map((id,i)=>({id,i})).filter(r=>s.reference_clusters[r.i]===c).sort((a,b)=>a.id.localeCompare(b.id));
      for(let start=0;start<rows.length;start+=size)bins.push({cluster:c,indices:rows.slice(start,start+size).map(r=>r.i)});
    }
    const cell=600/bins.length,rects=[];
    for(let y=0;y<bins.length;y++)for(let x=0;x<bins.length;x++) {
      let count=0,same=0,never=0,pairs=0;
      for(const i of bins[y].indices)for(const j of bins[x].indices)if(i!==j&&(x!==y||i>j)) {
        const p=pairIndex(i,j);count+=observed[p];same+=together[p];pairs++;if(!observed[p])never++;
      }
      const rate=count?same/count:null;
      const color=rate===null?'#d6dce2':`rgb(${Math.round(245-243*rate)},${Math.round(248-203*rate)},${Math.round(251-135*rate)})`;
      const title=`Bin ${y+1} × ${x+1}: ${number(rate)} co-assignment; ${count} pair observations across ${pairs} distinct pairs; ${never} never observed together`;
      rects.push(`<rect x="${70+x*cell}" y="${25+y*cell}" width="${cell+0.1}" height="${cell+0.1}" fill="${color}"><title>${esc(title)}</title></rect>`);
    }
    const clusters=[...new Set(bins.map(b=>b.cluster))];
    const labels=clusters.map(c=>{
      const first=bins.findIndex(b=>b.cluster===c),last=bins.findLastIndex(b=>b.cluster===c),mid=(first+last+1)/2;
      return `<text x="${70+mid*cell}" y="651" text-anchor="middle" font-size="12">C${c}</text>
        <text x="58" y="${29+mid*cell}" text-anchor="end" font-size="12">C${c}</text>
        <path d="M ${70+first*cell} 25 V 625 M 70 ${25+first*cell} H 670" stroke="#7d8b99" stroke-width="0.7" fill="none"/>`;
    }).join('');
    return {html:`<div class="consensus-map"><svg viewBox="0 0 700 680" role="img" aria-label="Consensus heatmap, ordered by reference cluster; gray means no observed pairs"><title>Consensus heatmap: share of successful joint samples assigned to the same cluster</title>${rects.join('')}${labels}</svg></div>
      <p class="method-note">White → navy: 0 → 1 co-assignment. Gray: no observed pairs, including single-passage diagonal cells. Each bin contains up to ${size} passages from one reference cluster. Cells pool pair counts; group sizes and joint exposure can differ. Every passage pair is available in JSON and Consensus pairs CSV.</p>`,bins};
  }

  function intervalChart(s) {
    const height=50+s.clusters.length*42;
    return `<div class="chart-wrap"><svg viewBox="0 0 850 ${height}" role="img" aria-label="Cluster Jaccard stability: mean and observed minimum to maximum"><title>Jaccard overlap across samples; observed ranges, not confidence intervals</title>
      ${[0,.25,.5,.75,1].map(v=>`<path d="M ${200+500*v} 20 V ${height-25}" stroke="#d9e0e5"/><text x="${200+500*v}" y="15" text-anchor="middle" font-size="12">${v}</text>`).join('')}
      ${s.clusters.map((c,i)=>{const y=40+i*42;return `<text x="0" y="${y+4}" font-size="13">Cluster ${c.cluster}</text>${c.count?`<line x1="${200+500*c.min}" x2="${200+500*c.max}" y1="${y}" y2="${y}" stroke="#839bb8" stroke-width="4"/><circle cx="${200+500*c.mean}" cy="${y}" r="5" fill="#002d74"/><text x="720" y="${y+4}" font-size="12">${c.mean.toFixed(3)} (${c.count})</text>`:`<text x="200" y="${y+4}" font-size="12">Not assessed</text>`}`;}).join('')}
      </svg></div>`;
  }

  function render(s,records,table) {
    let html='<section class="stability-section" aria-label="Cluster stability"><h4>Cluster stability</h4>';
    if(s.skipped)return html+`<p class="warning">${esc(s.skipped)}</p>${s.attempted?`<p>${s.successful} of ${s.attempted} samples fitted. Attempt details remain in the analysis JSON.</p>`:''}</section>`;
    const unit=s.parameters.unit==='meeting'?'meetings':'recorded affiliations';
    const matrix=heatmap(s),coverage=s.consensus.pair_coverage;
    const byId=new Map(records.map(r=>[r.id,r]));
    html+=`<p>${s.successful} of ${s.attempted} samples fitted, retaining ${s.sample_group_count} of ${s.group_count} ${unit} per sample (${(100*s.effective_group_fraction).toFixed(1)}%). TF-IDF, ${esc((s.representation||'pca').toUpperCase())} and ${esc(s.algorithm_name||'k-means')} were refitted each time.</p>
      <p class="method-note">Agreement describes sensitivity to omitted groups. It does not establish a shared position, a validated category or performance on future speeches.</p>
      ${s.warnings.map(w=>`<p class="warning">${esc(w)}</p>`).join('')}
      ${intervalChart(s)}
      <p class="method-note">Dots show mean Jaccard overlap with the best matching sampled cluster. Lines show observed minimum–maximum; parentheses give evaluable samples. These ranges are not confidence intervals. Clusters with fewer than two retained members are not assessed in that sample.</p>
      <details><summary>Agreement and sample coverage</summary>
      ${table(['Measure','Value'],[
        ['Adjusted Rand agreement: mean / min / max',`${number(s.ari.mean)} / ${number(s.ari.min)} / ${number(s.ari.max)}`],
        ['Distinct group subsets',`${s.unique_group_samples} across ${s.attempted} repetitions`],
        ['Pairs observed at least once',`${coverage.observed} of ${coverage.total}`],
        ['Pairs never observed together',coverage.never_observed],
        ['Joint samples per pair: min / mean / max',`${coverage.min} / ${number(coverage.mean)} / ${coverage.max}`],
        ['Group share requested / used',`${(100*s.parameters.fraction).toFixed(1)}% / ${(100*s.effective_group_fraction).toFixed(1)}%`],
        ['Resampling seed',s.parameters.seed]])}
      ${table(['Cluster','Evaluable samples','Mean Jaccard','Median','Min','Max'],s.clusters.map(c=>[c.cluster,c.count,number(c.mean),number(c.median),number(c.min),number(c.max)]))}
      <p class="method-note">Adjusted Rand agreement is invariant to cluster numbering. Jaccard matches use only passages present in each sample; matches may be many-to-one. Subsamples select groups uniformly without replacement, while passages retain their original weights within groups. This does not establish independence between groups. The reference fit and UMAP display stay unchanged.</p></details>
      <details open><summary>Which passages stay together?</summary>${matrix.html}
        <details><summary>Heatmap bin identifiers</summary>${table(['Bin','Reference cluster','Passage IDs'],matrix.bins.map((b,i)=>[i+1,b.cluster,b.indices.map(j=>s.reference_ids[j]).join(' · ')]))}</details>
      </details>`;
    const candidates=s.consensus.points.filter(p=>p.margin!==null).sort((a,b)=>a.margin-b.margin||a.included-b.included||a.index-b.index).slice(0,10);
    html+=`<h4>Passages to inspect</h4><p class="method-note">Up to ten passages with the smallest difference between within-cluster co-assignment and their strongest alternative cluster. Low or negative differences suggest a closer look; limited sample coverage can also affect this ranking. These are review leads, not detected errors.</p>`;
    if(!candidates.length)html+='<p>No passages have enough comparisons for this ranking.</p>';
    else html+=`<div class="stability-review">${candidates.map(p=>{const id=s.reference_ids[p.index],r=byId.get(id);return `<details><summary>${esc(r.country)} · ${esc(r.date)} · difference ${number(p.margin)}</summary>
      <p class="method-note">${esc(id)} · reference cluster ${s.reference_clusters[p.index]} · included in ${p.included} successful samples; ${p.observed_peers} of ${s.reference_ids.length-1} peers compared. Within-cluster ${number(p.within_cluster)}; strongest alternative ${number(p.strongest_other)} (cluster ${p.strongest_other_cluster}).</p>
      <blockquote>${esc(r.text)}</blockquote><a href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer">Open original source ↗</a></details>`;}).join('')}</div>`;
    const unranked=s.consensus.points.filter(p=>p.margin===null).length;
    if(unranked)html+=`<p class="warning">${unranked} passages lack within-cluster or alternative-cluster comparisons and cannot be ranked. Their missing values and inclusion counts remain in the exports.</p>`;
    html+=`<details><summary>Resampling record</summary>${table(['Sample','Passages used','Components','ARI','Status'],s.runs.map(r=>[r.attempt,r.indices.length,r[(s.representation||'pca')+'_components']??'—',number(r.ari),r.skipped||'Fitted']))}</details></section>`;
    return html;
  }
  const api={heatmap,render};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNStabilityView=api;
})(globalThis);
