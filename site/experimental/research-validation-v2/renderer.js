/* UNGA81 research-validation-v2: synthetic-only read-only display; no statistical fitting. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.UNResearchValidationV2 = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';
  const VERSION = '2.0.0';
  const SHA = /^[a-f0-9]{64}$/;
  const KINDS = ['consensus', 'country-theme', 'longitudinal', 'method-comparison'];
  const STATES = ['ready', 'withheld', 'failed', 'empty'];
  const ERROR = message => { throw Error('Research display refused: ' + message); };
  const must = (value, message) => { if (!value) ERROR(message); };
  const integer = value => Number.isSafeInteger(value) && value >= 0;
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const ratio = value => finite(value) && value >= 0 && value <= 1;
  const string = value => typeof value === 'string' && value.length > 0 && value.length <= 500;
  const unique = xs => Array.isArray(xs) && new Set(xs).size === xs.length;
  const esc = value => String(value === null || value === undefined ? 'N/A' : value)
    .replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const approx = (a,b) => Math.abs(a-b) <= 1e-8;
  const key = (a,b) => [a,b].sort().join('\u001f');
  const pct = x => x === null || x === undefined ? 'N/A' : (x*100).toFixed(1)+'%';
  const coords = xs => Array.isArray(xs) && xs.length === 2 && xs.every(finite);
  const sourceURL = x => x === null || (typeof x === 'string' && /^https:\/\/example\.invalid(?:\/|$)/.test(x));
  const unsafeKeys = ['text','quote','transcript','source_text','raw_text','passage_text','content'];
  const noText = x => !unsafeKeys.some(k => Object.prototype.hasOwnProperty.call(x,k));

  function validate(data) {
    must(data && data.schema === 'un.research-validation-v2.synthetic' &&
      data.fixture_kind === 'synthetic' && data.publication_eligible === false &&
      data.evaluation_role === 'engineering_only', 'Synthetic engineering-only v2 contract required');
    must(data.source && data.source.source_schema === 'synthetic.v1' &&
      data.source.source_hash_basis === 'synthetic' && SHA.test(data.source.source_sha256) &&
      SHA.test(data.source.selection_sha256), 'Source/hash basis/selection fingerprint required');
    must(Array.isArray(data.sources) && data.sources.length <= 100 &&
      Array.isArray(data.panels) && data.panels.length > 0 && data.panels.length <= 8,
      'Source frame/panel size missing or exceeded');
    const sources = new Map(), eligible = new Set();
    for (const s of data.sources) {
      must(s && string(s.id) && !sources.has(s.id) &&
        ['available','missing','failed','excluded'].includes(s.status) &&
        string(s.review_status) && (s.country === null || string(s.country)) &&
        (s.period === null || string(s.period)) && sourceURL(s.source_url) && noText(s),
        'Invalid/duplicate source, review, attribution, or unsafe source content');
      must(s.status === 'available' ? SHA.test(s.sha256) :
        (s.sha256 === null || SHA.test(s.sha256)) && string(s.missing_reason),
        'Source hash or nonavailability reason invalid');
      sources.set(s.id,s);
      if (s.status === 'available') eligible.add(s.id);
    }
    const counts = {frame:sources.size, eligible:eligible.size,
      excluded:sources.size-eligible.size,
      missing:data.sources.filter(s=>s.status==='missing'||s.status==='failed').length};
    const expectedIDs = new Set(sources.keys()), kinds = new Set();
    const linked = (ids, label, allowExcluded=true) => {
      must(unique(ids) && ids.every(id=>sources.has(id)) &&
        (allowExcluded || ids.every(id=>eligible.has(id))),label+' identities invalid');
    };
    for (const p of data.panels) {
      must(p && KINDS.includes(p.kind) && !kinds.has(p.kind) && STATES.includes(p.status) &&
        string(p.measure) && Array.isArray(p.warnings) && p.warnings.every(string) &&
        p.identity && p.coverage && Array.isArray(p.rows), 'Panel fields, status, or measurement invalid');
      kinds.add(p.kind);
      must(p.status === 'ready' || string(p.reason), 'Non-ready panel requires visible reason');
      const id = p.identity, c = p.coverage;
      must(string(id.population) && string(id.weighting) && string(id.unit) &&
        string(id.representation_id) && string(id.representation_version) &&
        id.source_hash_basis === data.source.source_hash_basis &&
        id.source_sha256 === data.source.source_sha256 &&
        id.selection_sha256 === data.source.selection_sha256,
        'Panel source/selection, representation and population identity mismatch');
      linked(id.source_ids,'Full source frame');
      must(id.source_ids.length === expectedIDs.size && id.source_ids.every(x=>expectedIDs.has(x)),
        'Panel dropped a missing, failed, excluded, or available source');
      must(['frame','eligible','excluded','missing','included'].every(k=>integer(c[k])) &&
        c.frame===counts.frame && c.eligible===counts.eligible && c.excluded===counts.excluded &&
        c.missing===counts.missing && c.included<=c.eligible,
        'Panel coverage differs from complete source inventory');
      if (p.status !== 'ready') continue;
      for (const row of p.rows) {
        must(row && noText(row),'Untrusted source-text field in result');
        linked(row.source_ids,'Row source');
      }
      if (p.kind === 'consensus') checkConsensus(p,sources,eligible);
      if (p.kind === 'country-theme') checkThemes(p,sources,eligible);
      if (p.kind === 'longitudinal') checkTemporal(p,sources,eligible);
      if (p.kind === 'method-comparison') checkMethods(p,sources);
    }
    return data;
  }

  function checkConsensus(p,sources,eligible) {
    must(unique(p.pair_population_ids) && p.pair_population_ids.length===eligible.size &&
      p.pair_population_ids.every(id=>eligible.has(id)) && p.pair_population_ids.length<=35 &&
      p.rows.length===eligible.size*(eligible.size-1)/2,
      'Consensus pair population or complete unordered pair frame missing');
    const seen=new Set();
    must(Array.isArray(p.family_weight_audit) && unique(p.family_weight_audit.map(f=>f.family)),
      'Family weight audit missing/duplicated');
    let familyWeight=0;
    for (const f of p.family_weight_audit) {
      must(string(f.family) && ratio(f.planned_weight) &&
        ((f.attempted===null && f.successful===null && f.failed===null && f.skipped===null) ||
        (integer(f.attempted) && integer(f.successful) && integer(f.failed) &&
         integer(f.skipped) && f.successful+f.failed===f.attempted)), 'Family attempts/weight invalid');
      familyWeight+=f.planned_weight;
    }
    must(approx(familyWeight,1), 'Original method-family planned weights must sum to one');
    const families=new Set(p.family_weight_audit.map(f=>f.family));
    for (const row of p.rows) {
      must(string(row.a) && string(row.b) && row.a!==row.b &&
        eligible.has(row.a) && eligible.has(row.b) && !seen.has(key(row.a,row.b)) &&
        row.source_ids.length===2 && row.source_ids.includes(row.a) && row.source_ids.includes(row.b),
        'Unordered pair duplicated, dropped, or unlinked');
      seen.add(key(row.a,row.b));
      must(['observed','zero_opportunity','missing_pair'].includes(row.record_status) &&
        typeof row.unstable==='boolean' &&
        unique(row.contributing_families) && row.contributing_families.every(f=>families.has(f)),
        'Pair state/instability/method family invalid');
      for (const k of ['coassigned_count','assigned_both_count','planned_count',
        'missing_pair_count','noise_pair_count','different_cluster_count','failed_fit_count'])
        must(integer(row[k]),'Missing/negative pair count: '+k);
      must(row.coassigned_count<=row.assigned_both_count &&
        row.assigned_both_count<=row.planned_count &&
        row.coassigned_count+row.different_cluster_count===row.assigned_both_count &&
        row.planned_count===row.assigned_both_count+row.missing_pair_count+row.noise_pair_count &&
        row.failed_fit_count<=row.missing_pair_count,
        'Original W2 planned/assigned/noise/missing/failed denominators inconsistent');
      must(['coassigned_weight','assigned_both_weight','planned_weight'].every(k=>finite(row[k])&&row[k]>=0) &&
        row.coassigned_weight<=row.assigned_both_weight+1e-9 &&
        row.assigned_both_weight<=row.planned_weight+1e-9,
        'Original weighted pair counts inconsistent');
      if (row.record_status === 'observed')
        must(row.assigned_both_count>0 && row.assigned_both_weight>0 && ratio(row.association) &&
          approx(row.association,row.coassigned_weight/row.assigned_both_weight),
          'Observed weighted conditional association contradicts original W2 ratio');
      else must(row.association===null && row.assigned_both_count===0 &&
        row.assigned_both_weight===0 && string(row.missing_reason),
        'Unassessed pair must remain explicitly missing, not numerical zero');
      if (row.record_status==='missing_pair') must(row.planned_count===0 && row.planned_weight===0,
        'Missing pair record cannot contain invented planned opportunities');
      must((row.planned_weight===0 && row.assignment_coverage===null) ||
        (row.planned_weight>0 && ratio(row.assignment_coverage) &&
          approx(row.assignment_coverage,row.assigned_both_weight/row.planned_weight)),
        'Pair assignment coverage changed');
    }
  }

  function checkThemes(p,sources,eligible) {
    must(unique(p.countries) && Array.isArray(p.themes) &&
      unique(p.themes.map(t=>t.id)) && p.themes.every(t=>string(t.id)&&string(t.label)) &&
      integer(p.unattributed_count) &&
      p.unattributed_count===Array.from(eligible).filter(id=>sources.get(id).country===null).length &&
      p.rows.length===p.countries.length*p.themes.length,
      'Theme population/component grid or unattributed coverage invalid');
    const seen=new Set();
    for(const r of p.rows){
      const k=key(r.country,r.theme);
      must(p.countries.includes(r.country) && p.themes.some(t=>t.id===r.theme) &&
        !seen.has(k) && ['observed','missing','withheld'].includes(r.status),
        'Theme cell identity/status invalid');
      seen.add(k);
      must(r.source_ids.every(id=>eligible.has(id) && sources.get(id).country===r.country),
        'Unverified country linkage or unavailable source used as observed');
      if(r.status==='observed'){
        must(finite(r.weighted_sum)&&r.weighted_sum>=0 &&
          finite(r.weight_total)&&r.weight_total>0 &&
          r.weighted_sum<=r.weight_total+1e-9 &&
          integer(r.evidence_count)&&r.evidence_count===r.source_ids.length,
          'Theme numerator/eligible weight/evidence count invalid');
      } else must(r.weighted_sum===null && r.weight_total===null && string(r.reason),
        'Missing/withheld theme must not be plotted as observed zero');
    }
  }

  function checkTemporal(p,sources,eligible) {
    must(unique(p.periods) && p.periods.length>=2 && p.periods.length<=12 &&
      Array.isArray(p.alignments) && p.alignments.length===p.periods.length-1 &&
      unique(p.actors.map(a=>a.id)) && p.actors.every(a=>string(a.id)&&string(a.label)&&
        string(a.attribution_status)&&string(a.roster_status)) &&
      p.rows.length===p.actors.length*p.periods.length,
      'Incomplete temporal periods, actor roster, or source coverage');
    for(let i=0;i<p.alignments.length;i++){
      const a=p.alignments[i];
      must(a.from===p.periods[i]&&a.to===p.periods[i+1] &&
        ['passed','withheld','failed'].includes(a.status) &&
        integer(a.anchors) && string(a.reference_basis) &&
        ['checked','not_assessed','failed'].includes(a.selection_comparability) &&
        typeof a.rank_ok==='boolean' && typeof a.degeneracy_ok==='boolean' &&
        (a.status!=='passed' || a.rank_ok&&a.degeneracy_ok&&a.selection_comparability==='checked') &&
        (a.status==='passed'||string(a.reason)),
        'Temporal alignment/selection diagnostic invalid');
      must(a.reference_basis===p.identity.representation_id,
        'Temporal alignment representation differs from panel basis');
    }
    const seen=new Set();
    for(const r of p.rows){
      const k=r.actor+'\u001f'+r.period;
      must(p.actors.some(a=>a.id===r.actor) && p.periods.includes(r.period) &&
        !seen.has(k) && ['observed','missing','withheld'].includes(r.status) &&
        integer(r.n) && r.n===r.source_ids.length &&
        r.source_ids.every(id=>eligible.has(id)&&sources.get(id).period===r.period),
        'Temporal actor-period/source identity or count invalid');
      seen.add(k);
      if(r.status==='observed') must(coords(r.xy) &&
        (r.uncertainty_radius===null || finite(r.uncertainty_radius)&&r.uncertainty_radius>=0) &&
        r.n>0 && string(r.composition), 'Observed temporal coordinate/uncertainty/composition invalid');
      else must(r.xy===null && r.uncertainty_radius===null && string(r.reason),
        'Missing/withheld coordinates must not be inferred');
    }
  }

  function checkMethods(p,sources) {
    must(p.rows.length>0 && unique(p.rows.map(r=>r.method)), 'Method comparison rows missing/duplicated');
    for(const r of p.rows){
      must(string(r.method)&&string(r.method_family)&&string(r.settings_sha256)&&
        SHA.test(r.settings_sha256)&&string(r.representation_id)&&
        r.representation_id===p.identity.representation_id,
        'Method settings/representation identity invalid');
      for(const k of ['attempted','successful','failed','skipped','excluded','not_fitted','unassigned'])
        must(integer(r[k]),'Invalid method attempt/coverage count: '+k);
      must(r.successful+r.failed===r.attempted &&
        typeof r.comparable==='boolean' &&
        (r.comparable ? r.stability===null||ratio(r.stability) : r.stability===null&&string(r.reason)),
        'Failed/skipped/unstable/incompatible method accounting invalid');
    }
  }

  function svgWrap(title,desc,width,height,body) {
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+width+' '+height+'" role="img" aria-label="'+esc(title)+'"><title>'+esc(title)+'</title><desc>'+esc(desc)+'</desc>'+body+'</svg>';
  }
  const label=(x,y,s,props='')=>'<text x="'+x+'" y="'+y+'" '+props+'>'+esc(s)+'</text>';
  const rect=(x,y,w,h,fill,props='')=>'<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" fill="'+fill+'" '+props+'/>';
  const fill=x=>x===null?'#e4e5e7':`rgb(${Math.round(236-145*x)},${Math.round(244-105*x)},${Math.round(250-66*x)})`;
  function consensusSVG(p) {
    const names=p.pair_population_ids, n=names.length,sz=76,left=112,top=64;
    const pair=new Map(p.rows.map(r=>[key(r.a,r.b),r]));let marks='';
    for(let i=0;i<n;i++){
      marks+=label(left+i*sz+sz/2,top-14,names[i],'text-anchor="middle" font-size="11"');
      marks+=label(left-12,top+i*sz+sz/2,names[i],'text-anchor="end" font-size="11"');
      for(let j=0;j<n;j++){
        const r=i===j?null:pair.get(key(names[i],names[j]));
        const v=r?.association??null, x=left+j*sz,y=top+i*sz;
        marks+=rect(x,y,sz-2,sz-2,i===j?'#fff':fill(v),'stroke="#adb6bd"');
        marks+=label(x+sz/2,y+sz/2-3,i===j?'—':v===null?'N/A':pct(v),
          'text-anchor="middle" font-weight="700" font-size="13"');
        if(r?.unstable)marks+=label(x+sz/2,y+sz/2+18,'unstable','text-anchor="middle" font-size="10"');
        else if(r?.record_status==='missing_pair')marks+=label(x+sz/2,y+sz/2+18,'missing pair','text-anchor="middle" font-size="10"');
        else if(r?.record_status==='zero_opportunity')marks+=label(x+sz/2,y+sz/2+18,'no joint fit','text-anchor="middle" font-size="10"');
      }
    }
    return svgWrap('Synthetic W2 weighted conditional consensus',
      'Original supplied associations are displayed, not recomputed as mean family rates; N/A is not zero.',
      left+n*sz+20,top+n*sz+42,marks+label(18,top+n*sz+25,'Observed zero ≠ zero opportunity ≠ missing pair; diagonal excluded.','font-size="11"'));
  }
  function themeSVG(p) {
    const cw=140,ch=64,left=130,top=65;
    const lookup=new Map(p.rows.map(r=>[r.country+'\u001f'+r.theme,r]));let marks='';
    for(let j=0;j<p.themes.length;j++)marks+=label(left+j*cw+cw/2,top-12,p.themes[j].label,'text-anchor="middle" font-size="12"');
    for(let i=0;i<p.countries.length;i++){
      marks+=label(left-12,top+i*ch+35,p.countries[i],'text-anchor="end" font-size="11"');
      for(let j=0;j<p.themes.length;j++){
        const r=lookup.get(p.countries[i]+'\u001f'+p.themes[j].id);
        const v=r.status==='observed'?r.weighted_sum/r.weight_total:null;
        const x=left+j*cw,y=top+i*ch;
        marks+=rect(x,y,cw-2,ch-2,fill(v),'stroke="#adb6bd"');
        marks+=label(x+cw/2,y+26,r.status==='observed'?pct(v):r.status.toUpperCase(),
          'font-size="14" text-anchor="middle" font-weight="700"');
        marks+=label(x+cw/2,y+46,r.status==='observed'?'n='+r.evidence_count:'not assessed','font-size="11" text-anchor="middle"');
      }
    }
    return svgWrap('Synthetic country-affiliation by latent component',
      'Weighted normalized language component shares, not verified speaker stances or policy positions.',
      left+p.themes.length*cw+12,top+p.countries.length*ch+32,marks);
  }
  function temporalSVG(p) {
    const width=850,top=66,height=360,left=110,step=290/Math.max(1,p.periods.length-1);
    const positions=new Map(p.rows.map(r=>[r.actor+'\u001f'+r.period,r]));
    const valid=p.rows.filter(r=>r.status==='observed');
    const min=Math.min(-1,...valid.map(r=>r.xy[0]- (r.uncertainty_radius||0)));
    const max=Math.max(1,...valid.map(r=>r.xy[0]+ (r.uncertainty_radius||0)));
    const yFor=x=>top+40+(max-x)/(max-min)*210;
    const xFor=i=>left+i*step*2;
    let marks=label(14,25,'Aligned component X · descriptive spread only','font-weight="700" font-size="13"');
    for(let j=0;j<p.periods.length;j++)marks+=label(xFor(j),height-24,p.periods[j],'text-anchor="middle" font-size="12"');
    for(let i=0;i<p.actors.length;i++){
      const a=p.actors[i];marks+=label(14,top+21+i*18,a.label,'font-size="11"');
      for(let j=0;j<p.periods.length;j++){
        const r=positions.get(a.id+'\u001f'+p.periods[j]);
        const safe=j===0||p.alignments.slice(0,j).every(z=>z.status==='passed');
        if(!safe||r.status!=='observed')continue;
        const x=xFor(j),y=yFor(r.xy[0]);
        if(j>0 && p.alignments[j-1].status==='passed'){
          const prev=positions.get(a.id+'\u001f'+p.periods[j-1]);
          if(prev.status==='observed') marks+='<path d="M '+xFor(j-1)+' '+yFor(prev.xy[0])+' L '+x+' '+y+'" fill="none" stroke="#214968" stroke-width="1.7" stroke-dasharray="'+(r.composition==='matched'?'0':'5 3')+'"/>';
        }
        if(r.uncertainty_radius!==null){const ry1=yFor(r.xy[0]-r.uncertainty_radius),ry2=yFor(r.xy[0]+r.uncertainty_radius);
          marks+='<line x1="'+x+'" y1="'+ry1+'" x2="'+x+'" y2="'+ry2+'" stroke="#8e5d16" stroke-width="4"/>';}
        marks+='<circle cx="'+x+'" cy="'+y+'" r="6" fill="#214968"><title>'+esc(a.label+' '+r.period+' n='+r.n+' '+r.composition)+'</title></circle>';
      }
    }
    for(let j=1;j<p.periods.length;j++)if(p.alignments[j-1].status!=='passed'){
      marks+=rect(xFor(j)-75,top+30,145,230,'#efeded','opacity="0.72"');
      marks+=label(xFor(j),top+150,'WITHHELD','text-anchor="middle" font-weight="700" font-size="13"');
    }
    return svgWrap('Synthetic longitudinal aligned actor profile',
      'Supplied aligned X coordinates with descriptive uncertainty, no interpolation across failed source-comparability gates.',
      width,height,marks+label(20,height-6,'A gap denotes failed alignment or missing coverage; dashed movement denotes composition change.','font-size="11"'));
  }
  function methodSVG(p) {
    const w=780,left=195,top=58,h=top+p.rows.length*72+40,scale=370/Math.max(1,...p.rows.map(r=>r.attempted+r.skipped));let marks='';
    for(let i=0;i<p.rows.length;i++){
      const r=p.rows[i],y=top+i*72,x=left;
      marks+=label(left-12,y+16,r.method,'text-anchor="end" font-size="12"');
      marks+=rect(x,y,r.successful*scale,25,'#386b86');
      marks+=rect(x+r.successful*scale,y,r.failed*scale,25,'#9a4e45');
      marks+=rect(x+r.attempted*scale,y,r.skipped*scale,25,'#c9c9c9');
      marks+=label(x,y+46,'success '+r.successful+' · failed '+r.failed+' · skipped '+r.skipped+ ' · unassigned '+r.unassigned,'font-size="11"');
      marks+=label(left+390,y+16,r.comparable?(r.stability===null?'stability N/A':'stability '+pct(r.stability)):'INCOMPATIBLE','font-size="11" font-weight="700"');
    }
    return svgWrap('Synthetic method and failure comparison',
      'Source-supplied attempted, successful, failed and skipped fits; stability is not significance.',w,h,marks);
  }
  function renderPanel(p){
    must(p && KINDS.includes(p.kind),'Unknown panel');
    if(p.status!=='ready')return svgWrap(p.kind.toUpperCase()+' — '+p.status,p.reason,680,100,
      label(16,42,p.status.toUpperCase()+': '+p.reason,'font-size="13"'));
    switch(p.kind){
      case 'consensus': return consensusSVG(p);
      case 'country-theme': return themeSVG(p);
      case 'longitudinal': return temporalSVG(p);
      case 'method-comparison': return methodSVG(p);
    }
  }
  function table(heads,rows,caption) {
    return '<div class="rv-scroll"><table><caption>'+esc(caption)+'</caption><thead><tr>'+heads.map(k=>'<th scope="col">'+esc(k)+'</th>').join('')+'</tr></thead><tbody>'+
      rows.map(a=>'<tr>'+a.map(v=>'<td>'+esc(v===undefined?'not recorded':v)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>';
  }
  function rowSummary(p){
    if(p.kind==='consensus')return [['Pair','Weighted association','Numerator weight','Assigned-both denominator weight','Planned weight','Raw coassigned/assigned-both/planned','Missing/noise/failed','Families','Flag','Sources'],
      p.rows.map(r=>[r.a+' / '+r.b,pct(r.association),r.coassigned_weight,r.assigned_both_weight,r.planned_weight,
      r.coassigned_count+'/'+r.assigned_both_count+'/'+r.planned_count,
      r.missing_pair_count+'/'+r.noise_pair_count+'/'+r.failed_fit_count,
      r.contributing_families.join(', ')||'none',r.unstable?'unstable':r.record_status,r.source_ids.join(', ')])];
    if(p.kind==='country-theme')return [['Affiliation','Latent component','Status','Weighted numerator','Eligible weight denominator','Source observations','Source IDs','Reason'],
      p.rows.map(r=>[r.country,r.theme,r.status,r.weighted_sum,r.weight_total,r.evidence_count,r.source_ids.join(', '),r.reason])];
    if(p.kind==='longitudinal')return [['Actor','Period','Status','Aligned X','Aligned Y','Descriptive radius','Source n','Composition','Sources','Reason'],
      p.rows.map(r=>[r.actor,r.period,r.status,r.xy?.[0],r.xy?.[1],r.uncertainty_radius,r.n,r.composition,r.source_ids.join(', '),r.reason])];
    return [['Method','Family','Attempted','Successful','Failed','Skipped','Unassigned','Not fitted','Excluded','Stability','Comparable','Settings SHA-256','Reason'],
      p.rows.map(r=>[r.method,r.method_family,r.attempted,r.successful,r.failed,r.skipped,r.unassigned,r.not_fitted,r.excluded,
        pct(r.stability),r.comparable?'yes':'no',r.settings_sha256,r.reason])];
  }
  function staticHTML(data) {
    validate(data);
    const sections=data.panels.map(p=>{
      const c=p.coverage;
      const provenance='<p class="rv-meta">Population: '+esc(p.identity.population)+' · unit: '+esc(p.identity.unit)+' · weighting: '+esc(p.identity.weighting)+
        ' · representation: '+esc(p.identity.representation_id)+'@'+esc(p.identity.representation_version)+
        ' · source hash basis: '+esc(p.identity.source_hash_basis)+'</p>';
      const counts='<p class="rv-meta">Frame '+c.frame+' · eligible '+c.eligible+' · included '+c.included+' · excluded '+c.excluded+
        ' · missing/failed '+c.missing+' (subset of excluded, not an additional population)</p>';
      const status=p.status==='ready'?'<div class="rv-figure">'+renderPanel(p)+'</div>':
        '<p class="rv-abstain" role="status">ABSTAIN — '+esc(p.status)+': '+esc(p.reason)+'</p>';
      const [cols,rows]=rowSummary(p);
      const tab=p.status==='ready'?table(cols,rows,p.kind+' accessible source-bound table'):'<p>No result marks released.</p>';
      const extra=p.kind==='consensus'?'<p>Original weighted association values are supplied by W2; this renderer does not compute a family-average substitute.</p>':'';
      const align=p.kind==='longitudinal'?table(['From','To','Alignment gate','Anchors','Selection comparable','Rank OK','Degeneracy OK','Reason'],
        p.alignments.map(a=>[a.from,a.to,a.status,a.anchors,a.selection_comparability,a.rank_ok,a.degeneracy_ok,a.reason]),'Period alignment and failed-gate ledger'):'';
      return '<section class="rv-panel" data-kind="'+esc(p.kind)+'"><h2>'+esc(p.kind)+
        ' <small>'+esc(p.status)+'</small></h2>'+provenance+counts+'<p>'+esc(p.measure)+'</p>'+extra+
        p.warnings.map(w=>'<p class="rv-warning">'+esc(w)+'</p>').join('')+status+tab+align+'</section>';
    }).join('');
    const sourceRows=data.sources.map(s=>[s.id,s.sha256,s.status,s.missing_reason,s.country,s.period,s.meeting_id,s.review_status,s.json_pointer,s.source_url]);
    const ledger='<details><summary>Full source, country-attribution, and review ledger ('+data.sources.length+')</summary>'+
      '<p>SHA values and source records are imported claims from synthetic fixtures; no original document authentication is performed here.</p>'+table(
        ['Source ID','SHA-256','Status','Nonavailability reason','Recorded affiliation (not stance)','Period','Meeting','Review','Pointer','Synthetic URL'],sourceRows,
        'Complete source inventory, including exclusions and unavailable groups')+'</details>';
    return '<h1>UNGA81 research validation v2 — synthetic engineering demo</h1>'+
      '<p class="rv-warning">No diplomatic transcripts, verified governmental stances, political relationships, statistical significance, or causal influence. No re-fitting.</p>'+sections+ledger;
  }
  function mount(host,data){
    validate(data);
    must(host&&typeof host.replaceChildren==='function','DOM mounting host required');
    const content=document.createElement('div');content.innerHTML=staticHTML(data);host.replaceChildren(content);
    const aside=document.createElement('p');aside.className='rv-meta';aside.textContent='Replay and SVG/HTML exports preserve the validated synthetic values; exports contain no scripts.';host.append(aside);
    return host;
  }
  function exportJSON(data){validate(data);return JSON.stringify(data,null,2)+'\n';}
  function htmlDocument(data){return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+
    '<title>UNGA81 synthetic research validation export</title><style>body{font:16px system-ui;max-width:1100px;margin:auto;padding:1rem}svg{width:100%;height:auto}table{border-collapse:collapse}td,th{border:1px solid #888;padding:.35rem}.rv-scroll{overflow:auto}section{margin:2rem 0}summary{cursor:pointer}</style>'+staticHTML(data)+'</html>';}
  return Object.freeze({VERSION,validate,check:validate,renderPanel,mount,exportJSON,htmlDocument});
});
