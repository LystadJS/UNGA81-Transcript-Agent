/* Standalone, synthetic-first evidence displays. No fitting, fetching, or stance inference. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.UNEvidenceViz = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';

  const VERSION = '0.1.0';
  const COLORS = Object.freeze({
    ink: '#182c43', navy: '#062135', blue: '#234e78', gold: '#a88750',
    neutral: '#e1e7ed', pale: '#f6f8fa', grid: '#d5dee6',
    warn: '#944b42', teal: '#397b74'
  });
  const TYPES = ['consensus', 'country-theme', 'network', 'longitudinal'];
  const isNumber = x => typeof x === 'number' && Number.isFinite(x);
  const pct = x => isNumber(x) ? (x * 100).toFixed(0) + '%' : 'N/A';
  const decimal = x => isNumber(x) ? x.toFixed(2) : 'N/A';
  const escape = x => String(x === null || x === undefined ? '' : x)
    .replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const assert = (ok, why) => { if (!ok) throw Error(why); };
  const unique = a => new Set(a).size === a.length;
  const hex64 = x => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
  const own = (a, key) => Object.prototype.hasOwnProperty.call(a, key);
  const range = x => isNumber(x) && x >= 0 && x <= 1;
  const readable = x => String(x === null || x === undefined ? 'not recorded' : x);
  const rows = (header, body) => '<div class="ev-scroll"><table><thead><tr>' +
    header.map(s => '<th scope="col">' + escape(s) + '</th>').join('') +
    '</tr></thead><tbody>' + body.join('') + '</tbody></table></div>';
  const td = s => '<td>' + s + '</td>';
  const tr = a => '<tr>' + a.map(td).join('') + '</tr>';
  const svgText = (x, y, s, attrs) => '<text x="' + x + '" y="' + y + '" ' + (attrs || '') + '>' + escape(s) + '</text>';
  const fill = x => x === null ? COLORS.neutral :
    'rgb(' + [Math.round(240-192*x), Math.round(245-178*x), Math.round(249-126*x)].join(',') + ')';
  const svgWrap = (name, description, width, height, inner) =>
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + width + ' ' + height +
    '" role="img" aria-label="' + escape(name) +
    '" style="font-family:Arial,Helvetica,sans-serif;font-size:12px;max-width:100%;height:auto;background:#fff">' +
    '<title>' + escape(name) + '</title><desc>' + escape(description) + '</desc>' + inner + '</svg>';
  const textLine = (value, cls) => '<p class="' + (cls || 'ev-note') + '">' + escape(value) + '</p>';
  const hit = (id, label) => '<button type="button" class="ev-hit" data-ev-inspect="' +
    escape(id) + '">' + escape(label) + '</button>';

  function validateEnvelope(env) {
    assert(env && env.schema === 'un.parallel-analysis.v1' && /^1\.\d+\.\d+$/.test(env.contract_version || ''),
      'Expected un.parallel-analysis.v1, compatible 1.x.');
    assert(env.publication_eligible === false && env.evaluation_role === 'engineering_only',
      'Only unpublished engineering outputs are accepted.');
    assert(env.producer && env.producer.fixture_kind === 'synthetic',
      'Public visualization prototype accepts synthetic fixtures only; no private development observations.');
    assert(env.upstream && env.cohort && Array.isArray(env.observations) && Array.isArray(env.models),
      'Missing upstream identity, cohort, observations, or models.');
    assert(env.cohort.split === 'synthetic', 'Synthetic-only split required.');
    assert(env.cohort.eligible <= env.cohort.total_in_frame, 'Eligible exceeds total in frame.');
    assert(env.observations.every(o => o && typeof o.id === 'string' && o.id.length &&
      (o.text_sha256 === null || hex64(o.text_sha256)) &&
      typeof o.source_status === 'string' && typeof o.review_status === 'string' &&
      (o.source_url === null || /^https:\/\//.test(o.source_url))),
      'Observation identity, hash, source status, or URL invalid.');
    assert(unique(env.observations.map(o => o.id)), 'Duplicate observation IDs.');
    assert(unique(env.models.map(m => m.model_id)), 'Duplicate model IDs.');
    assert(env.observations.length <= 600, 'Render prototype limits synthetic observations to 600.');
    return new Map(env.observations.map(o => [o.id, o]));
  }

  function validatePanel(env, panel, observations) {
    assert(panel && TYPES.includes(panel.kind), 'Unknown visualization kind.');
    assert(['ready','withheld','failed','empty'].includes(panel.status), 'Explicit panel status required.');
    assert(typeof panel.measure === 'string' && panel.measure.length > 8, 'Measurement definition required.');
    assert(panel.identity && typeof panel.identity === 'object', 'Panel lacks source-bound identity.');
    const b = panel.identity;
    for (const k of ['source_schema','source_hash_basis','source_sha256','selection_sha256']) {
      assert(own(b,k) && b[k] === env.upstream[k], 'Source identity mismatch: ' + k);
    }
    assert(b.unit === env.cohort.unit && b.weighting === env.cohort.weighting,
      'Observation unit / weighting mismatch.');
    assert(Array.isArray(b.observation_refs) && unique(b.observation_refs.map(x => x.id)),
      'Observation refs missing or duplicated.');
    for (const r of b.observation_refs) {
      const o = observations.get(r.id);
      assert(o && r.text_sha256 === o.text_sha256, 'Observation ID/hash mismatch: ' + r.id);
    }
    assert(panel.coverage && ['frame','eligible','included','excluded','missing'].every(k =>
      Number.isInteger(panel.coverage[k]) && panel.coverage[k] >= 0), 'Coverage ledger is required.');
    assert(panel.coverage.frame === env.cohort.total_in_frame &&
      panel.coverage.eligible === env.cohort.eligible &&
      panel.coverage.included <= panel.coverage.eligible &&
      panel.coverage.excluded + panel.coverage.missing + panel.coverage.included <= panel.coverage.frame,
      'Incoherent frame/eligible/missing counts.');
    assert(Array.isArray(panel.warnings), 'Warnings array required.');
    if (panel.status !== 'ready') assert(typeof panel.reason === 'string' && panel.reason.length,
      'Withheld, failed, and empty states require a reason.');
    if (panel.status === 'ready') assert(b.representation_id && b.representation_version,
      'Representation and version required.');
    const index = new Set(b.observation_refs.map(r => r.id));
    const checkIds = ids => {
      assert(Array.isArray(ids) && ids.every(id => index.has(id)), 'Unrecognized evidence observation ID.');
      assert(unique(ids), 'Duplicate evidence IDs in one item.');
    };
    return {checkIds, index};
  }

  function evidenceHTML(env, ids, observations) {
    if (!ids.length) return '<p class="ev-note">No source observations supplied for this mark.</p>';
    return '<ul class="ev-sources">' + ids.map(id => {
      const o = observations.get(id);
      const loc = [o.json_pointer, o.start !== null ? o.start + '–' + o.end : null].filter(x => x !== null).join(' · ');
      return '<li><strong>' + escape(id) + '</strong> · ' + escape(o.date) +
        ' · recorded affiliation: ' + escape(o.country || 'unattributed') +
        ' · review: ' + escape(o.review_status) + ' · source: ' + escape(o.source_status) +
        (loc ? ' · pointer/offset ' + escape(loc) : '') +
        '<span class="ev-note"> · Synthetic fixture; no external source is available.</span></li>';
    }).join('') + '</ul>';
  }

  function frame(env, panel) {
    return 'Frame ' + panel.coverage.frame + ' · eligible ' + panel.coverage.eligible +
      ' · displayed ' + panel.coverage.included + ' · excluded ' + panel.coverage.excluded +
      ' · missing ' + panel.coverage.missing + ' · ' + env.cohort.weighting.replace(/_/g,' ') + '.';
  }

  function panelShell(env, panel, title, content, svg, inspections, observations) {
    const warnings = panel.warnings.map(s => textLine(s, 'ev-warning')).join('');
    const ledger = panel.identity.observation_refs.map(r => r.id);
    const evidence = '<details class="ev-ledger"><summary>Observation identity and source ledger (' +
      ledger.length + ')</summary>' + evidenceHTML(env, ledger, observations) + '</details>';
    const guidance = textLine(panel.measure, 'ev-note');
    const status = panel.status !== 'ready' ?
      '<div class="ev-withheld" role="status"><strong>' + escape(panel.status.toUpperCase()) +
      '</strong> — ' + escape(panel.reason) + '</div>' : '';
    const provenance = '<p class="ev-provenance">Synthetic engineering demonstration · ' +
      escape(frame(env, panel)) + ' · representation ' + escape(panel.identity.representation_id || 'withheld') +
      ' (' + escape(panel.identity.representation_version || 'not applicable') + ')</p>';
    const html = '<section class="ev-panel" data-ev-kind="' + escape(panel.kind) +
      '"><div class="ev-panel-head"><h2>' + escape(title) + '</h2><span class="ev-state">' +
      escape(panel.status) + '</span></div>' + provenance + guidance + warnings + status +
      content + '<div class="ev-inspector" role="status" aria-live="polite">Select an evidence cell or mark to inspect source identities.</div>' +
      evidence + '</section>';
    return {kind:panel.kind, title, html, svg, inspections, evidence, status:panel.status};
  }

  function consensus(env, p, obs, checkIds) {
    const names = p.observation_ids || [];
    assert(unique(names) && names.every(x => obs.has(x)), 'Consensus IDs invalid.');
    checkIds(names);
    assert(names.length <= 35, 'Individual-pair table limited to 35 IDs; provide upstream grouping before rendering.');
    assert(Array.isArray(p.pairs), 'Explicit pair exposures required.');
    const lookup = new Map(), inspector = {};
    const index = new Map(names.map((id,i) => [id,i]));
    for (let z = 0; z < p.pairs.length; z++) {
      const a = p.pairs[z];
      assert(index.has(a.a) && index.has(a.b) && a.a !== a.b, 'Unknown or self pair.');
      const key = [a.a,a.b].sort().join('\u001f');
      assert(!lookup.has(key), 'Duplicate unordered pair.');
      assert(Array.isArray(a.families) && unique(a.families.map(f=>f.family)),
        'Families must be distinct for equal-family balancing.');
      let rates = [], eligible = 0, together = 0, failure = 0;
      for (const f of a.families) {
        assert(typeof f.family === 'string' && Number.isInteger(f.eligible) && f.eligible >= 0 &&
          Number.isInteger(f.together) && f.together >= 0 && f.together <= f.eligible &&
          Number.isInteger(f.failed) && f.failed >= 0, 'Invalid pair fit counts.');
        eligible += f.eligible; together += f.together; failure += f.failed;
        if (f.eligible) rates.push(f.together / f.eligible);
      }
      assert(a.missing_reason === null || typeof a.missing_reason === 'string', 'Pair missing reason required.');
      const value = rates.length ? rates.reduce((x,y)=>x+y,0)/rates.length : null;
      if (!rates.length) assert(a.missing_reason, 'Zero-opportunity pair must carry reason.');
      const r = {value, eligible, together, failure, families:a.families, missing_reason:a.missing_reason,
        unstable:!!a.unstable, a:a.a, b:a.b};
      lookup.set(key,r);
      inspector['cons-' + z] = {
        ids:[a.a,a.b], summary: 'Equal-family average: ' + pct(value) + '. ' +
        together + '/' + eligible + ' eligible pair exposures across ' + rates.length +
        ' assessable families; failed attempts ' + failure + '. ' +
        (r.unstable ? 'Assignment instability flagged upstream. ' : '') +
        (a.missing_reason || '')
      };
      r.key = 'cons-' + z;
    }
    const cell = 70, sx = 146, sy = 92;
    const w = sx + Math.max(1,names.length)*cell + 22, h = sy + Math.max(1,names.length)*cell + 68;
    let marks = svgText(10,20,'OBSERVATION PAIRS · FAMILY-BALANCED', 'font-size="13" font-weight="700" fill="'+COLORS.blue+'"');
    const body = [];
    for (let i=0;i<names.length;i++) {
      marks += svgText(sx+i*cell+cell/2,sy-13,names[i],'text-anchor="middle" font-size="10"');
      marks += svgText(sx-12,sy+i*cell+cell/2+4,names[i],'text-anchor="end" font-size="10"');
      const cells = [];
      for (let j=0;j<names.length;j++) {
        if (i === j) {
          marks += '<rect x="'+(sx+j*cell)+'" y="'+(sy+i*cell)+'" width="'+cell+'" height="'+cell+
            '" fill="#fff" stroke="'+COLORS.grid+'"/>';
          cells.push('<span class="ev-diagonal" aria-label="Diagonal not assessed">—</span>');
          continue;
        }
        const a = lookup.get([names[i],names[j]].sort().join('\u001f'));
        const v = a ? a.value : null;
        marks += '<rect x="'+(sx+j*cell)+'" y="'+(sy+i*cell)+'" width="'+cell+'" height="'+cell+
          '" fill="'+fill(v)+'" stroke="'+COLORS.grid+'"/>' +
          svgText(sx+j*cell+cell/2,sy+i*cell+cell/2+4,v === null?'N/A':pct(v),
            'text-anchor="middle" font-size="11" fill="'+COLORS.ink+'"');
        const desc = !a ? 'No pair record (missing)' : v === null ? 'No eligible pair exposures' :
          pct(v)+' · '+a.together+'/'+a.eligible+' pooled opportunities'+(a.unstable?' · unstable':'');
        cells.push(a ? hit(a.key,desc) : '<span class="ev-missing">Missing pair record</span>');
      }
      body.push('<tr><th scope="row">'+escape(names[i])+'</th>'+cells.map(td).join('')+'</tr>');
    }
    const table = rows(['ID',...names],body);
    const desc = 'Colors summarize equal-family mean co-assignment, not pooled successes / attempts. ' +
      'Cells label values and expose numerator, denominator and family counts. Diagonal omitted.';
    const svg = svgWrap('Consensus stability, synthetic pairs',desc,w,h,marks +
      svgText(sx,h-17,'N/A = missing or zero eligible exposure. Diagonal undefined.','font-size="11"'));
    const content = '<p class="ev-note">Each family has equal influence if eligible; pooled pair counts are shown only as exposure audit. ' +
      'A missing pair, zero opportunities, and 0% co-assignment are different outcomes. Flags denote supplied instability, not significance.</p>' +
      '<div class="ev-figure">'+svg+'</div>'+table;
    return panelShell(env,p,'01 / Consensus and stability',content,svg,inspector,obs);
  }

  function countryTheme(env,p,obs,checkIds) {
    assert(Array.isArray(p.countries) && unique(p.countries) && p.countries.length <= 32,'Country rows invalid.');
    assert(Array.isArray(p.components) && p.components.length>0 &&
      unique(p.components.map(x=>x.id)) && p.components.length<=12,'Component identities invalid.');
    assert(Array.isArray(p.cells) && Number.isInteger(p.unattributed_count) &&
      p.unattributed_count>=0,'Country cells / unattributed count required.');
    const matrix = new Map(),inspect = {};
    for (let i=0;i<p.cells.length;i++) {
      const c=p.cells[i],key=c.country+'\u001f'+c.component;
      assert(p.countries.includes(c.country) && p.components.some(x=>x.id===c.component) && !matrix.has(key),
        'Unknown or duplicate country/component.');
      assert(['observed','missing','withheld'].includes(c.status),'Country cell status invalid.');
      checkIds(c.observation_ids);
      if(c.status==='observed') assert(isNumber(c.weighted_sum) && isNumber(c.weight_total) &&
        c.weighted_sum>=0 && c.weight_total>0 && c.weighted_sum<=c.weight_total+1e-9 &&
        Number.isInteger(c.evidence_count) && c.evidence_count>=0, 'Invalid prevalence numerator/denominator.');
      else assert(c.weighted_sum===null && c.weight_total===null && typeof c.missing_reason==='string' &&
        c.missing_reason.length, 'Missing/withheld is not numerical zero.');
      const v=c.status==='observed'?c.weighted_sum/c.weight_total:null;
      const d={...c,value:v,key:'theme-'+i};
      inspect[d.key]={ids:c.observation_ids,summary: c.status==='observed'?
        'Normalized component-weight summary '+pct(v)+'; weighted numerator '+
        decimal(c.weighted_sum)+' / eligible weighted denominator '+decimal(c.weight_total)+
        '; evidence count '+c.evidence_count+'. Recorded affiliation is not speaker verification.' :
        c.status+': '+c.missing_reason};
      matrix.set(key,d);
    }
    const cw=150, x0=160, y0=72, h=y0+p.countries.length*80+74,
      w=x0+cw*p.components.length+20;
    let marks=svgText(12,20,'LANGUAGE COMPONENTS · WEIGHTED MEANS','font-weight="700" fill="'+COLORS.blue+'"');
    p.components.forEach((c,j)=>{marks+=svgText(x0+cw*j+cw/2,y0-20,c.label,'text-anchor="middle"');});
    const body=p.countries.map((country,i)=>{
      marks+=svgText(x0-12,y0+i*80+39,country,'text-anchor="end" font-size="11"');
      const cells=p.components.map((component,j)=>{
        const c=matrix.get(country+'\u001f'+component.id);
        const v=c?.value??null, x=x0+j*cw, y=y0+i*80;
        marks+='<rect x="'+x+'" y="'+y+'" width="'+cw+'" height="78" fill="'+fill(v)+
          '" stroke="'+COLORS.grid+'"/>'+svgText(x+cw/2,y+31,v===null?'N/A':pct(v),
          'text-anchor="middle" font-size="15" font-weight="700"');
        marks+=svgText(x+cw/2,y+50,c?.status==='observed' ? 'n='+c.evidence_count : 'not observed',
          'text-anchor="middle" font-size="10"');
        return c ? hit(c.key,c.status==='observed'?
          pct(v)+' · '+decimal(c.weighted_sum)+'/'+decimal(c.weight_total)+
          ' · n='+c.evidence_count : c.status+' · '+c.missing_reason) :
          '<span class="ev-missing">Missing cell</span>';
      });
      return '<tr><th scope="row">'+escape(country)+'</th>'+cells.map(td).join('')+'</tr>';
    });
    const svg=svgWrap('Country by latent language component','Percentage is normalized component weight, not political position.',w,h,marks+
      svgText(x0,h-20,'N/A is missing or withheld; observed zero is 0%. Unattributed sources: '+p.unattributed_count,
        'font-size="11"'));
    const content='<p class="ev-note">Components describe fitted language patterns, not endorsed government positions. '+
      'Numerators and denominators use '+escape(env.cohort.weighting.replace(/_/g,' '))+
      ' weights; '+p.unattributed_count+' source observations have unresolved country attribution and are not redistributed.</p>'+
      '<div class="ev-figure">'+svg+'</div>'+rows(['Recorded affiliation',...p.components.map(c=>c.label)],
      body)+'<p class="ev-note">Zero requires an observed numerator of zero with positive eligible weight. Missing data are never recoded to zero.</p>';
    return panelShell(env,p,'02 / Country × latent themes',content,svg,inspect,obs);
  }

  function components(nodes,edges) {
    const adj = new Map(nodes.map(n=>[n.id,[]]));
    for (const e of edges) { adj.get(e.from).push(e.to);adj.get(e.to).push(e.from); }
    const groups=[],visited=new Set();
    for(const n of nodes)if(!visited.has(n.id)){
      const todo=[n.id],group=[];visited.add(n.id);
      while(todo.length){const at=todo.pop();group.push(at);
        for(const nb of adj.get(at))if(!visited.has(nb)){visited.add(nb);todo.push(nb);}
      }
      groups.push(group);
    }
    return groups.sort((a,b)=>b.length-a.length);
  }

  function network(env,p,obs,checkIds) {
    assert(p.graph && isNumber(p.graph.threshold) && p.graph.threshold>=0 &&
      p.graph.threshold<=1 && typeof p.graph.metric==='string' &&
      typeof p.graph.selection_rule==='string' && p.graph.selection_rule.length,
      'Graph threshold, metric and selection rule required.');
    assert(Array.isArray(p.nodes) && unique(p.nodes.map(n=>n.id)) &&
      Array.isArray(p.edges) && p.nodes.length<=50, 'Graph node/edge limit or IDs invalid.');
    const ids=new Set(p.nodes.map(n=>n.id)),inspect={},edgeKey=new Set();
    for(const n of p.nodes) {
      checkIds(n.observation_ids);
      assert(n.observation_ids.length>0 && typeof n.label==='string' &&
        typeof n.affiliation_status==='string', 'Graph nodes need attributed source IDs and status.');
      inspect['node-'+n.id]={ids:n.observation_ids,summary:
        'Descriptive node '+n.label+'; affiliation '+n.affiliation_status+
        '. Layout is illustrative, not a fitted geopolitical map.'};
    }
    for(let i=0;i<p.edges.length;i++){
      const e=p.edges[i],key=[e.from,e.to].sort().join('\u001f');
      assert(ids.has(e.from) && ids.has(e.to) && e.from!==e.to && !edgeKey.has(key) &&
        range(e.strength) && e.strength>=p.graph.threshold &&
        Number.isInteger(e.eligible_pairs) && e.eligible_pairs>0,
        'Graph edge invalid or below declared threshold.');
      assert(['stable','sensitive','not_assessed'].includes(e.duplicate_sensitivity) &&
        ['stable','sensitive','not_assessed'].includes(e.agenda_sensitivity),
        'Explicit duplicate and agenda sensitivity needed.');
      checkIds(e.observation_ids);
      edgeKey.add(key);
      inspect['edge-'+i]={ids:e.observation_ids,summary:
        'Strength '+decimal(e.strength)+' ('+p.graph.metric+'), '+e.eligible_pairs+
        ' eligible comparisons. Duplicate sensitivity '+e.duplicate_sensitivity+
        '; agenda sensitivity '+e.agenda_sensitivity+'. Similarity is not an alliance.'};
    }
    const groups=components(p.nodes,p.edges),byID=new Map(),w=900,h=480;
    p.nodes.forEach((n,i)=>{
      const angle=2*Math.PI*i/Math.max(p.nodes.length,1)-Math.PI/2;
      byID.set(n.id,{x:445+Math.cos(angle)*290,y:222+Math.sin(angle)*167});
    });
    let marks='<rect x="18" y="15" width="864" height="424" fill="'+COLORS.pale+'"/>';
    for(let i=0;i<p.edges.length;i++){
      const e=p.edges[i],a=byID.get(e.from),b=byID.get(e.to);
      marks+='<line x1="'+a.x+'" y1="'+a.y+'" x2="'+b.x+'" y2="'+b.y+
        '" stroke="'+(e.duplicate_sensitivity==='sensitive'||e.agenda_sensitivity==='sensitive'?
          COLORS.warn:COLORS.blue)+'" stroke-width="'+(1+e.strength*5)+
        '" opacity=".70"'+(e.duplicate_sensitivity==='not_assessed'?' stroke-dasharray="5 4"':'')+
        '><title>'+escape(e.from+'–'+e.to+' strength '+decimal(e.strength))+'</title></line>';
    }
    for(const n of p.nodes){
      const v=byID.get(n.id);
      marks+='<circle cx="'+v.x+'" cy="'+v.y+'" r="19" fill="'+COLORS.navy+
        '" stroke="'+COLORS.gold+'" stroke-width="2"><title>'+escape(n.label)+'</title></circle>'+
        svgText(v.x,v.y+4,n.label,'text-anchor="middle" fill="#ffffff" font-size="10" font-weight="700"');
    }
    marks+=svgText(30,466,'Synthetic deterministic circular layout; distance between nodes has no interpretive meaning.',
      'font-size="11"');
    const svg=svgWrap('Discourse similarity network','Edges are representation similarities above a declared threshold, not relationships or alliances.',w,h,marks);
    const body=p.edges.map((e,i)=>tr([hit('edge-'+i,e.from+' ↔ '+e.to),
      escape(decimal(e.strength)),escape(String(e.eligible_pairs)),
      escape(e.duplicate_sensitivity),escape(e.agenda_sensitivity)]));
    const nodeRows=p.nodes.map(n=>tr([hit('node-'+n.id,n.label),escape(n.affiliation_status),
      escape(String(n.observation_ids.length))]));
    const content='<p class="ev-note">Edges: '+escape(p.graph.metric)+' ≥ '+decimal(p.graph.threshold)+
      ' · selection: '+escape(p.graph.selection_rule)+'. Connected component sizes: '+
      groups.map(g=>g.length).join(', ')+'. Nodes are laid out deterministically for inspection, not as geometric evidence.</p>'+
      '<div class="ev-figure">'+svg+'</div><h3>Links and sensitivity</h3>'+
      rows(['Source-linked pair','Strength','Eligible pairs','Duplicate sensitivity','Agenda sensitivity'],body)+
      '<h3>Nodes and attribution</h3>'+rows(['Node','Attribution status','Source observations'],nodeRows)+
      '<p class="ev-note">Thicker links indicate larger recorded similarity. Dashed lines: duplicate sensitivity not assessed; rust lines: sensitivity flagged. Edges do not establish alliance, shared policy, or influence.</p>';
    return panelShell(env,p,'03 / Discourse similarity network',content,svg,inspect,obs);
  }

  function longitudinal(env,p,obs,checkIds) {
    assert(Array.isArray(p.periods) && unique(p.periods) && p.periods.length>=2 &&
      Array.isArray(p.alignments) && Array.isArray(p.actors),'Period and alignment ledgers required.');
    const validEdges=new Set();
    for(const a of p.alignments) {
      assert(p.periods.includes(a.from) && p.periods.includes(a.to) &&
        Number.isInteger(a.anchors) && a.anchors>=0 &&
        typeof a.reference_basis==='string' && typeof a.selection_comparability==='string' &&
        ['passed','failed','not_assessed'].includes(a.status) &&
        typeof a.rank_ok==='boolean' && typeof a.degeneracy_ok==='boolean' &&
        typeof a.uncertainty_status==='string', 'Alignment ledger incomplete.');
      if(a.status==='passed' && a.rank_ok && a.degeneracy_ok && a.anchors>=3 &&
        a.selection_comparability==='checked')validEdges.add(a.from+'\u001f'+a.to);
    }
    const inspect={},lines=[],actors=p.actors, nodeKeys=new Set();
    assert(unique(actors.map(a=>a.id)) && actors.length<=30,'Actor IDs duplicate or too numerous.');
    const w=900,h=470,x0=100,y0=55,xs=660,ys=330;
    const lim=1.5,px=x=>x0+(x+lim)/(2*lim)*xs,py=y=>y0+(lim-y)/(2*lim)*ys;
    let marks='<rect x="'+x0+'" y="'+y0+'" width="'+xs+'" height="'+ys+
      '" fill="'+COLORS.pale+'" stroke="'+COLORS.grid+'"/>'+
      '<path d="M '+px(0)+' '+y0+' V '+(y0+ys)+' M '+x0+' '+py(0)+' H '+(x0+xs)+
      '" stroke="'+COLORS.grid+'" stroke-dasharray="4 4"/>'+
      svgText(x0+xs/2,435,'Aligned latent dimension 1','text-anchor="middle" font-size="12"')+
      svgText(30,222,'Aligned latent dimension 2','transform="rotate(-90 30 222)" text-anchor="middle"');
    const palette=[COLORS.blue,COLORS.teal,COLORS.gold,'#82638c'];
    for(let i=0;i<actors.length;i++){
      const a=actors[i],by=new Map(),color=palette[i%palette.length];
      assert(['matched','arrival','departure','changing_roster'].includes(a.roster_status) &&
        typeof a.attribution_status==='string' &&
        Array.isArray(a.positions), 'Roster and actor positions required.');
      for(const q of a.positions){
        assert(p.periods.includes(q.period) && !by.has(q.period) &&
          Array.isArray(q.observation_ids) && Number.isInteger(q.n) && q.n>=0 &&
          ['observed','missing','withheld'].includes(q.status), 'Actor-period row invalid.');
        checkIds(q.observation_ids);
        if(q.status==='observed')assert(Array.isArray(q.xy) && q.xy.length===2 &&
          q.xy.every(x=>isNumber(x)&&Math.abs(x)<=lim) &&
          (q.radius===null || (isNumber(q.radius)&&q.radius>=0)), 'Invalid aligned score/radius.');
        else assert(q.xy===null && typeof q.reason==='string' && q.reason.length,
          'Missing actor-period coordinates must be null with reason.');
        by.set(q.period,q);
        const k=a.id+'-'+q.period;assert(!nodeKeys.has(k),'Duplicate actor-period.');nodeKeys.add(k);
        inspect['track-'+k]={ids:q.observation_ids,summary:
          a.label+' / '+q.period+' / '+q.status+' / '+q.n+
          ' eligible source observations. '+(q.reason||'')+
          (q.radius!==null?' Diagnostic uncertainty radius '+decimal(q.radius)+' (not automatically a confidence interval).':' Uncertainty not assessed.')};
      }
      const displayed=[];
      for(let j=0;j<p.periods.length;j++){
        const q=by.get(p.periods[j]);
        if(!q || q.status!=='observed')continue;
        const previous=by.get(p.periods[j-1]),key=p.periods[j-1]+'\u001f'+p.periods[j];
        if(j>0&&previous?.status==='observed'&&validEdges.has(key) && a.roster_status==='matched'){
          marks+='<line x1="'+px(previous.xy[0])+'" y1="'+py(previous.xy[1])+
            '" x2="'+px(q.xy[0])+'" y2="'+py(q.xy[1])+
            '" stroke="'+color+'" stroke-width="3"><title>'+escape(a.label+': '+previous.period+' to '+q.period)+'</title></line>';
          displayed.push(previous.period+'→'+q.period);
        }
        if(q.radius!==null)marks+='<circle cx="'+px(q.xy[0])+'" cy="'+py(q.xy[1])+
          '" r="'+(q.radius*xs/(2*lim))+'" fill="'+color+'" opacity=".12" stroke="'+color+'" stroke-dasharray="3 3"/>';
        marks+='<circle cx="'+px(q.xy[0])+'" cy="'+py(q.xy[1])+'" r="6" fill="'+color+
          '" stroke="'+COLORS.navy+'" stroke-width="1.2"><title>'+escape(a.label+' '+q.period)+'</title></circle>'+
          svgText(px(q.xy[0])+10,py(q.xy[1])-8,a.label+' '+q.period.slice(2),
            'font-size="10" font-weight="700"');
      }
      lines.push(tr([escape(a.label),escape(a.roster_status),escape(a.attribution_status),
        displayed.length?escape(displayed.join(', ')):'<strong>Withheld</strong>',
        a.positions.map(q=>hit('track-'+a.id+'-'+q.period,q.period+': '+q.status)).join(' · ')]));
    }
    marks+=svgText(x0,453,'Only adjacent, verified aligned periods are joined; unknown intervals are not interpolated.','font-size="11"');
    const svg=svgWrap('Longitudinal latent positions','Only successfully aligned adjacent periods are connected. Roster and uncertainty are reported.',w,h,marks);
    const alignmentRows=p.alignments.map(a=>tr([escape(a.from+' → '+a.to),
      escape(a.status),escape(String(a.anchors)),escape(a.reference_basis),
      escape(a.selection_comparability),escape(a.uncertainty_status)]));
    const content='<p class="ev-note">Coordinates are supplied aligned latent scores, not diplomatic positions. '+
      'A connecting line requires passing rank/degeneracy checks, ≥3 anchors, checked source-selection comparability, '+
      'and matched actor observations in adjacent periods. Gaps, arrivals and departures remain unconnected.</p>'+
      '<div class="ev-figure">'+svg+'</div>'+
      rows(['Actor / source grouping','Roster','Attribution','Comparable transitions','Inspect periods'],lines)+
      '<h3>Alignment and withholding ledger</h3>'+
      rows(['Period pair','Status','Anchors','Reference','Source comparison','Uncertainty'],alignmentRows);
    return panelShell(env,p,'04 / Longitudinal latent movement',content,svg,inspect,obs);
  }

  function renderPanel(env, panel) {
    const obs=validateEnvelope(env);
    const checks=validatePanel(env,panel,obs);
    if(panel.status!=='ready'){
      const svg=svgWrap(panel.kind+' withheld',panel.reason,700,130,
        svgText(25,58,panel.status.toUpperCase()+': '+panel.reason,'font-size="16"'));
      return panelShell(env,panel,TYPES.indexOf(panel.kind)+1+' / '+panel.kind,'',svg,{},obs);
    }
    if(panel.kind==='consensus')return consensus(env,panel,obs,checks.checkIds);
    if(panel.kind==='country-theme')return countryTheme(env,panel,obs,checks.checkIds);
    if(panel.kind==='network')return network(env,panel,obs,checks.checkIds);
    return longitudinal(env,panel,obs,checks.checkIds);
  }

  function htmlDocument(view) {
    const staticHTML=view.html.replace(/<button\b[^>]*data-ev-inspect="[^"]*"[^>]*>(.*?)<\/button>/g,'<span>$1</span>');
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+
      '<title>'+escape(view.title)+' — synthetic research evidence</title>'+
      '<style>body{font:15px/1.55 Arial,Helvetica,sans-serif;color:#182c43;max-width:1040px;margin:auto;padding:24px}'+
      '.ev-figure{overflow:auto}.ev-figure svg{width:100%;height:auto}.ev-scroll{overflow:auto}'+
      'table{border-collapse:collapse;width:100%}td,th{text-align:left;border:1px solid #d5dee6;padding:8px}'+
      'thead{background:#eef3f7}.ev-hit{border:0;background:transparent}.ev-note,.ev-provenance{color:#526578}'+
      '.ev-panel{padding:20px;border:1px solid #d5dee6}summary{cursor:pointer}.ev-sources{overflow-wrap:anywhere}'+
      '</style><main><p>Offline research snapshot · synthetic · descriptive only · not validated for publication</p>'+
      staticHTML+'<p>Static export: evidence links and observation ledger remain; interactive inspection requires the prototype.</p></main></html>';
  }

  function mount(target, env, panels) {
    assert(target && typeof target.innerHTML === 'string', 'Pass an HTML container.');
    assert(Array.isArray(panels) && unique(panels.map(p=>p.kind)), 'Provide at most one of each chart.');
    validateEnvelope(env);
    const views=panels.map(p=>renderPanel(env,p)),inspections={};
    for(const v of views)for(const key of Object.keys(v.inspections)){
      assert(!own(inspections,key),'Collision in evidence inspector keys.');
      inspections[key]=v.inspections[key];
    }
    target.innerHTML=views.map(v=>v.html).join('');
    target.addEventListener('click',event=>{
      const button=event.target.closest('[data-ev-inspect]');
      if(!button || !target.contains(button))return;
      const entry=inspections[button.getAttribute('data-ev-inspect')];
      if(!entry)return;
      const host=button.closest('.ev-panel')?.querySelector('.ev-inspector');
      if(host)host.innerHTML='<strong>Selected evidence</strong><p>'+escape(entry.summary)+
        '</p>'+evidenceHTML(env,entry.ids,new Map(env.observations.map(o=>[o.id,o])));
    });
    return views;
  }
  return Object.freeze({VERSION,COLORS,TYPES,validateEnvelope,validatePanel,
    renderPanel,mount,htmlDocument,components});
});
