/* Source-bound comparison orchestration; existing numerical engines and D1 gates are unchanged. */
(function (root) {
  'use strict';
  const VERSION = 'latent-comparison-1.0.0';
  const LIMIT = 128 * 1024 * 1024;
  const encoder = new TextEncoder();
  const node = typeof module !== 'undefined' && module.exports;
  const dependency = (file, name) => node ? require('./' + file) : root[name];
  const assert = (ok, message) => { if (!ok) throw Error(message); };
  const parse = text => JSON.parse(text.replace(/^\uFEFF/, ''));
  const clone = value => JSON.parse(JSON.stringify(value));
  const finite = value => Number.isFinite(value) ? value : null;
  const mean = values => { const v = values.filter(Number.isFinite); return v.length ? v.reduce((a,b) => a+b,0)/v.length : null; };
  function stable(value) {
    if (Array.isArray(value)) return '[' + value.map(stable).join(',') + ']';
    if (value && typeof value === 'object') return '{' + Object.keys(value).filter(k=>value[k]!==undefined).sort().map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',') + '}';
    return JSON.stringify(value);
  }
  async function hash(text) {
    const bytes = typeof text === 'string' ? encoder.encode(text) : text;
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), n=>n.toString(16).padStart(2,'0')).join('');
  }
  function freeze(value) {
    if (value && typeof value === 'object' && !Object.isFrozen(value)) { Object.values(value).forEach(freeze); Object.freeze(value); }
    return value;
  }
  function validatePlan(value) {
    assert(value && value.schema === 'un.latent-plan.v1', 'Use an un.latent-plan.v1 settings file.');
    assert(typeof value.compare_parents === 'boolean', 'Choose whether to compare full parents.');
    assert(Array.isArray(value.settings) && value.settings.length > 0 && value.settings.length <= 12, 'A comparison requires 1–12 settings, or at most 24 fits with parents.');
    const A = dependency('analysis-core.js', 'UNAnalysis');
    const s = {enabled:false,unit:'meeting',replicates:30,fraction:0.8,seed:31415,...value.stability};
    const seen = new Set();
    const settings = value.settings.map((row, i) => {
      assert(row && ['clusters','nmf'].includes(row.method), 'Unknown comparison method.');
      assert(typeof row.label === 'string' && row.label.trim().length > 0 && row.label.length <= 100, 'Give each setting a label of 1–100 characters.');
      const key = row.method === 'clusters' ? 'clustering' : 'nmf';
      const p = A.parameters({...value.base,methods:[row.method],[key]:{...row.options,stability:s}});
      const options = p[key];
      assert(options.representation !== 'compare', 'Use separate PCA and LSA rows in a comparison plan.');
      const identity = stable({method:row.method,options});
      assert(!seen.has(identity), 'Duplicate numerical setting at row ' + (i+1) + '.');
      seen.add(identity);
      return {label:row.label.trim(),method:row.method,options};
    });
    const base = A.parameters({...value.base,methods:['frequency']});
    const {topic,phrases,exclude,start,end,region,scope} = base;
    return {schema:value.schema,base:{topic,phrases,exclude,start,end,region,scope},compare_parents:value.compare_parents,stability:s,settings};
  }
  async function input(payload, progress = async()=>{}) {
    assert(payload && ['corpus','reviewed'].includes(payload.kind) && typeof payload.text === 'string', 'Choose a collected corpus or reviewed analysis bundle.');
    assert(encoder.encode(payload.text).length <= 40*1024*1024, 'Input exceeds the 40 MB comparison limit.');
    assert(!payload.review_text || (typeof payload.review_text==='string' && encoder.encode(payload.review_text).length<=4*1024*1024), 'Passage review exceeds 4 MB.');
    const A = dependency('analysis-core.js','UNAnalysis');
    const source_hash = await hash(payload.text);
    let corpus, original, selection;
    if (payload.kind === 'reviewed') {
      assert(!payload.review_text && !payload.policy, 'Reviewed excerpts cannot receive a parent passage-type mask.');
      const R = dependency('reviewed-units.js','UNReviewedUnits');
      const bundle = parse(payload.text);
      corpus = (await R.load(encoder.encode(payload.text), A.validateCorpus, progress)).corpus;
      original = A.validateCorpus(parse(bundle.source_json));
    } else {
      corpus = A.validateCorpus(parse(payload.text));
      assert(!corpus.reviewed_units && !corpus.records.some(r=>r.parent_id), 'Derived excerpts require their validated reviewed analysis bundle.');
      for (const r of corpus.records) assert(await hash(r.text)===r.text_sha256, 'Source text hash mismatch: '+r.id);
      original = corpus;
      if (payload.policy) {
        assert(typeof payload.review_text === 'string', 'A reviewed inclusion policy requires the completed review file.');
        selection = {policy:payload.policy,review:parse(payload.review_text),corpus_sha256:source_hash,review_sha256:await hash(payload.review_text)};
        dependency('passage-selection.js','UNPassageSelection').validate(corpus,selection);
      } else assert(!payload.review_text, 'Choose the inclusion policy for this passage review.');
    }
    return {corpus,original,selection,source_hash};
  }
  const manifest = records => records.map(r=>({id:r.id,text_sha256:r.text_sha256,parent_id:r.parent_id||null,date:r.date,country:r.country,region:r.region,language:r.language,scope:r.scope,meeting:r.meeting,source_url:r.source_url,start:r.start??null,end:r.end??null}));
  function parentCoverage(records, original) {
    const parents = new Map(original.records.map(r=>[r.id,r]));
    const groups = new Map();
    for (const r of records) {
      assert(parents.has(r.parent_id), 'Missing parent for '+r.id);
      if (!groups.has(r.parent_id)) groups.set(r.parent_id,[]);
      groups.get(r.parent_id).push(r);
    }
    return Array.from(groups, ([id,children]) => {
      const p = parents.get(id), length = Array.from(p.text).length;
      const spans = children.map(r=>[r.start,r.end]).sort((a,b)=>a[0]-b[0]);
      let covered=0,end=-1;
      for (const [a,b] of spans) { assert(Number.isInteger(a)&&Number.isInteger(b)&&a>=0&&b>a&&b<=length, 'Invalid excerpt span.'); covered+=Math.max(0,b-Math.max(a,end)); end=Math.max(end,b); }
      return {parent_id:id,country:p.country,source_url:p.source_url,passages:children.length,selected_code_points:covered,parent_code_points:length,coverage_fraction:length?covered/length:null,passage_weight:children.length/(records.length||1),equal_parent_summary_weight:1/groups.size,ids:children.map(r=>r.id)};
    });
  }
  function summarize(entry) {
    const result = entry.result;
    if (!result) return {id:entry.id,label:entry.label,unit:entry.unit,status:'failed',reason:entry.error};
    const method = result.methods[entry.method];
    const base = {id:entry.id,label:entry.label,unit:entry.unit,method:entry.method,matched:result.counts.matched,duplicates:result.counts.duplicates,parents:new Set(result.matched.map(r=>r.parent_id||r.id)).size,status:method?.skipped?'withheld':'fitted',reason:method?.skipped||null};
    if (!method || method.skipped) return base;
    const points = method.points || [];
    if (entry.method==='nmf') return {...base,usable:points.length,components:method.parameters.components,converged:method.diagnostics?.converged??null,relative_residual:finite(method.diagnostics?.relative_residual),refit_cosine:finite(method.stability?.cosine?.mean),refits:method.stability?.successful??null,distinct_omissions:method.stability?.unique_group_samples??null};
    const assigned = points.filter(p=>p.cluster>0);
    const counts = new Map(); assigned.forEach(p=>counts.set(p.cluster,(counts.get(p.cluster)||0)+1));
    return {...base,usable:points.length,representation:method.representation,algorithm:method.algorithm,components:method[method.representation]?.components,assigned:assigned.length,assignment_fraction:points.length?assigned.length/points.length:null,largest_fraction:points.length?Math.max(0,...counts.values())/points.length:null,silhouette:finite(method.clustering?.silhouette),silhouette_denominator:method.clustering?.silhouette_count??points.length,retained_variance:finite(method[method.representation]?.retained_variance??method[method.representation]?.centered_variance_retained),mean_ari:mean((method.stability?.runs||[]).map(r=>r.skipped?null:r.ari)),assessable_ari:(method.stability?.runs||[]).filter(r=>!r.skipped&&Number.isFinite(r.ari)).length,refits:method.stability?.successful??null,distinct_omissions:method.stability?.unique_group_samples??null};
  }
  // Composition is a summary of a fitted model, not a weighted refit.
  function compositions(entry) {
    const fit=entry.result?.methods?.[entry.method];
    if (!fit?.points || entry.method!=='clusters') return null;
    const records=new Map(entry.result.matched.map(r=>[r.id,r]));
    const groups=new Map();
    for (const p of fit.points) { const r=records.get(p.id),id=r.parent_id||r.id; if(!groups.has(id))groups.set(id,[]); groups.get(id).push(p); }
    const labels=[...new Set(fit.points.map(p=>p.cluster))].sort((a,b)=>a-b);
    return {role:'Hard-assignment composition, not a weighted refit; cluster 0 is unassigned, not a theme.',parent_count:groups.size,passage_count:fit.points.length,rows:Array.from(groups,([parent_id,points])=>({parent_id,passages:points.length,shares:labels.map(cluster=>({cluster,share:points.filter(p=>p.cluster===cluster).length/points.length}))})),totals:labels.map(cluster=>({cluster,passage_weighted:fit.points.filter(p=>p.cluster===cluster).length/fit.points.length,parent_balanced:mean(Array.from(groups.values(),ps=>ps.filter(p=>p.cluster===cluster).length/ps.length))}))};
  }
  function ari(a,b) {
    assert(a.length===b.length,'Paired labels required.');
    if (a.length<2) return null;
    const rows=new Map(),cols=new Map(),cells=new Map(),choose=n=>n*(n-1)/2;
    a.forEach((v,i)=>{rows.set(v,(rows.get(v)||0)+1);cols.set(b[i],(cols.get(b[i])||0)+1);const k=JSON.stringify([v,b[i]]);cells.set(k,(cells.get(k)||0)+1);});
    // Integer pair-count products avoid unnecessary fractional cancellation (n <= 600).
    const sum=m=>Array.from(m.values()).reduce((s,n)=>s+choose(n),0);
    const pairs=choose(a.length),row=sum(rows),col=sum(cols),numerator=2*(sum(cells)*pairs-row*col),denominator=(row+col)*pairs-2*row*col;
    return denominator===0?1:numerator/denominator;
  }
  function paired(left,right) {
    const base={left:left.id,right:right.id,scope:'Identical selected source identities and hashes only; not evidence of policy agreement.'};
    if (left.unit!==right.unit) return {...base,withheld:'Different analytical units. Parent and excerpt cluster IDs cannot be compared.'};
    if (!left.result||!right.result) return {...base,withheld:'At least one analysis failed.'};
    const l=left.result.methods[left.method],r=right.result.methods[right.method];
    if (!l?.points||!r?.points) return {...base,withheld:'At least one numerical fit is withheld.'};
    const lsel=manifest(left.result.matched),rsel=manifest(right.result.matched);
    const by=new Map(r.points.map(p=>[p.id,p]));
    const shared=l.points.filter(p=>by.get(p.id)?.text_sha256===p.text_sha256);
    if (stable(lsel)!==stable(rsel)||shared.length!==l.points.length||shared.length!==r.points.length) return {...base,shared_usable:shared.length,left_usable:l.points.length,right_usable:r.points.length,withheld:'Source population, order or usable vectors changed. No like-for-like score is reported.'};
    if (left.method!==right.method) return {...base,withheld:'NMF components and hard partitions are different quantities.'};
    if (left.method==='nmf') {
      if(l.parameters.components!==r.parameters.components)return {...base,withheld:'Different NMF ranks; no forced one-to-one component correspondence.'};
      return {...base,nmf:dependency('nmf-core.js','UNNMF').align(l,r)};
    }
    const lp=l.points,rp=lp.map(p=>by.get(p.id)),both=lp.flatMap((p,i)=>p.cluster>0&&rp[i].cluster>0?[i]:[]);
    const a=both.map(i=>lp[i].cluster),b=both.map(i=>rp[i].cluster);
    const enough=both.length>=2&&new Set(a).size>=2&&new Set(b).size>=2;
    const transitions={assigned_both:0,left_only:0,right_only:0,unassigned_both:0};
    lp.forEach((p,i)=>{const x=p.cluster>0,y=rp[i].cluster>0;transitions[x&&y?'assigned_both':x?'left_only':y?'right_only':'unassigned_both']++;});
    const row_labels=[...new Set(lp.map(p=>p.cluster))].sort((a,b)=>a-b),column_labels=[...new Set(rp.map(p=>p.cluster))].sort((a,b)=>a-b);
    const counts=row_labels.map(()=>column_labels.map(()=>0));
    lp.forEach((p,i)=>counts[row_labels.indexOf(p.cluster)][column_labels.indexOf(rp[i].cluster)]++);
    const geometryEqual=l.representation===r.representation&&stable(lp.map(p=>p[l.representation]))===stable(rp.map(p=>p[r.representation]));
    const labelsEqual=lp.every((p,i)=>p.cluster===rp[i].cluster);
    const leftRuns=l.stability?.runs||[],rightRuns=r.stability?.runs||[];
    const schedulePaired=leftRuns.length>0&&leftRuns.length===rightRuns.length&&stable(leftRuns.map(x=>x.groups))===stable(rightRuns.map(x=>x.groups))&&stable(l.stability?.groups)===stable(r.stability?.groups);
    const result={...base,usable:lp.length,ari:enough?ari(a,b):null,ari_denominator:both.length,ari_reason:enough?null:'Requires two represented assigned groups in each fit.',transitions,row_labels,column_labels,counts,geometry_identical:geometryEqual,labels_identical:labelsEqual,paired_group_schedule:schedulePaired,umap_identical:stable(lp.map(p=>p.umap))===stable(rp.map(p=>p.umap))};
    if(l.algorithm==='gmm'&&r.algorithm==='gmm'&&l.parameters.k===r.parameters.k)result.soft=dependency('gmm-core.js','UNGaussianMixture').align(lp.map(p=>p.memberships),rp.map(p=>p.memberships));
    return result;
  }
  async function run(payload, requested, runtime={}, progress=async()=>{}) {
    const plan=validatePlan(requested),ctx=await input(payload,progress),A=dependency('analysis-core.js','UNAnalysis');
    assert(!plan.compare_parents||payload.kind==='reviewed','Full-parent comparison requires a reviewed analysis bundle.');
    const p={...plan.base,methods:['frequency'],...(ctx.selection?{passageSelection:ctx.selection}:{})};
    const selected=await A.analyze(ctx.corpus,p,progress);
    assert(selected.matched.length<=600,'Comparison supports at most 600 selected passages. Narrow the selection; no sampling is applied.');
    const coverage=payload.kind==='reviewed'?parentCoverage(selected.matched,ctx.original):[];
    const parentIds=new Set(coverage.map(r=>r.parent_id));
    const parentCorpus=plan.compare_parents?{...ctx.original,records:ctx.original.records.filter(r=>parentIds.has(r.id))}:null;
    const units=[{unit:payload.kind==='reviewed'?'excerpt':'source',corpus:ctx.corpus,base:p}];
    if(parentCorpus)units.push({unit:'parent',corpus:parentCorpus,base:{...plan.base,topic:'',phrases:[],exclude:[],methods:['frequency']}});
    const entries=[];
    for (const u of units) for (let i=0;i<plan.settings.length;i++) {
      const row=plan.settings[i],key=row.method==='clusters'?'clustering':'nmf';
      await progress(`Fit ${entries.length+1}/${units.length*plan.settings.length}: ${u.unit} · ${row.label}`);
      const parameters={...u.base,methods:[row.method],[key]:row.options};
      const result=await A.analyze(u.corpus,parameters,progress,(rs,vs,o,pr)=>dependency('cluster-core.js','UNClusters').run(rs,vs,o,pr),(rs,vs,o,pr)=>dependency('nmf-core.js','UNNMF').run(rs,vs,o,pr));
      const entry={id:u.unit+'-'+(i+1),label:row.label,unit:u.unit,method:row.method,result};
      entry.summary=summarize(entry);entry.composition=compositions(entry);entries.push(entry);
    }
    const pairs=[];
    for(let i=0;i<entries.length;i++)for(let j=i+1;j<entries.length;j++)if(entries[i].unit===entries[j].unit)pairs.push(paired(entries[i],entries[j]));
    return {schema:'un.latent-comparison.v1',engine:VERSION,created_at:new Date().toISOString(),runtime,plan,source_hash:ctx.source_hash,selection_hash:await hash(stable(manifest(selected.matched))),selection:manifest(selected.matched),counts:selected.counts,duplicates:selected.duplicates,coverage,entries,pairs,limits:{max_settings:12,max_selected:600},interpretation:'Exploratory sensitivity, not a significance test, confidence interval, political alignment or independent replication. No automatic method winner.',weighting:'Existing fits retain equal unique-passage weight. Parent-balanced cluster composition is a separate summary, not a refitted weighted model.',parent_comparison:'Only full parents of retained, query-matching excerpts are analyzed. The parent baseline has no topic filter. Missing or deduplicated children and partial text coverage remain explicit. Different units have different fitted vocabularies and no cross-unit ARI.'};
  }
  function validateResult(result) {
    assert(result && result.schema==='un.latent-comparison.v1'&&Array.isArray(result.entries)&&result.entries.length<=24,'Invalid saved comparison result.');
    const ids=new Set();
    for(const e of result.entries){
      assert(e && typeof e.id==='string'&&!ids.has(e.id)&&['source','parent','excerpt'].includes(e.unit)&&['nmf','clusters'].includes(e.method),'Invalid saved fit identity.');ids.add(e.id);
      assert(e.result&&Array.isArray(e.result.matched)&&e.result.matched.length<=600&&e.result.methods,'Invalid saved analysis.');
      const by=new Map(e.result.matched.map(r=>[r.id,r]));assert(by.size===e.result.matched.length,'Duplicate saved passage identity.');
      const fit=e.result.methods[e.method];assert(fit&&typeof fit==='object','Missing saved method.');
      if(fit.skipped)continue;
      assert(Array.isArray(fit.points)&&fit.points.length<=600,'Invalid saved points.');
      const pointIds=new Set();
      for(const p of fit.points){assert(by.has(p.id)&&by.get(p.id).text_sha256===p.text_sha256&&!pointIds.has(p.id),'Changed saved point identity.');pointIds.add(p.id);
        if(e.method==='clusters'){assert(Number.isInteger(p.cluster)&&p.cluster>=0,'Invalid saved assignment.');for(const key of [fit.representation,'umap',...(p.mds?['mds']:[])])assert(Array.isArray(p[key])&&(key===fit.representation?p[key].length>=1:p[key].length===2)&&p[key].every(Number.isFinite),'Invalid saved coordinates.');}
      }
    }
    return result;
  }
  async function pack(payload, result) {
    validateResult(result);
    const input_json=JSON.stringify(payload),result_json=JSON.stringify(result);
    const archive={schema:'un.latent-saved-run.v1',input_json,result_json,input_sha256:await hash(input_json),result_sha256:await hash(result_json)};
    const text=JSON.stringify(archive);
    assert(encoder.encode(text).length<=LIMIT,'Saved comparison exceeds 128 MB. Reduce the settings or corpus.');
    return text;
  }
  async function restore(text, progress=async()=>{}) {
    assert(typeof text==='string'&&encoder.encode(text).length<=LIMIT,'Saved run exceeds 128 MB.');
    const archive=parse(text);assert(archive.schema==='un.latent-saved-run.v1'&&typeof archive.input_json==='string'&&typeof archive.result_json==='string','Use a saved-run archive, not a bare analysis JSON.');
    assert(await hash(archive.input_json)===archive.input_sha256&&await hash(archive.result_json)===archive.result_sha256,'Saved-run integrity check failed.');
    const payload=parse(archive.input_json),result=validateResult(parse(archive.result_json)),ctx=await input(payload,progress),plan=validatePlan(result.plan);
    assert(ctx.source_hash===result.source_hash,'Saved source hash changed.');
    const A=dependency('analysis-core.js','UNAnalysis'),selected=await A.analyze(ctx.corpus,{...plan.base,methods:['frequency'],...(ctx.selection?{passageSelection:ctx.selection}:{})},progress);
    assert(await hash(stable(manifest(selected.matched)))===result.selection_hash&&stable(manifest(selected.matched))===stable(result.selection),'Saved population differs from the input and selection policy.');
    const parents=new Set(selected.matched.map(r=>r.parent_id));
    const sourceBy=new Map(ctx.original.records.map(r=>[r.id,r])),selectedBy=new Map(selected.matched.map(r=>[r.id,r]));
    for(const e of result.entries)for(const r of e.result.matched){const expected=e.unit==='parent'?sourceBy.get(r.id):selectedBy.get(r.id);assert(expected&&stable(expected)===stable(r)&&(e.unit!=='parent'||parents.has(r.id)),'Saved evidence differs from source lineage.');}
    return {payload:freeze(payload),result:freeze(result),archive_text:text,replay:'Stored result and coordinates restored without refitting. Hashes verify consistency, not reviewer authentication or mathematical correctness.'};
  }
  const api={VERSION,LIMIT,stable,hash,parse,validatePlan,input,manifest,parentCoverage,summarize,compositions,ari,paired,run,validateResult,pack,restore};
  if(node)module.exports=api;else root.UNLatent=api;
})(globalThis);
