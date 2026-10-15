/* Coordinator W2 source-bound inspection. Displays original weighted W2 statistics;
 * never recomputes consensus as the W6 illustrative equal-family mean. */
(function(root, factory){
  'use strict';
  const api=factory(root);
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.UNResearchConsensus=api;
})(typeof globalThis==='object'?globalThis:this, function(root){
  'use strict';
  const C=typeof module==='object'&&module.exports ?
    require('./parallel/w05-browser/experimental/method-lab/contracts.js') :
    root.UNMethodLabContracts;
  const V=typeof module==='object'&&module.exports ?
    require('./experimental/evidence-viz/evidence-viz.js') :
    root.UNEvidenceViz;
  const assert=(condition,message)=>{if(!condition)throw Error('W2 import refused: '+message);};
  const SHA=/^[a-f0-9]{64}$/;
  const count=n=>Number.isSafeInteger(n)&&n>=0;
  const finite=n=>typeof n==='number'&&Number.isFinite(n);
  const approx=(a,b)=>Math.abs(a-b)<=1e-8;
  const stable=x=>Array.isArray(x)?'['+x.map(stable).join(',')+']':
    x&&typeof x==='object'?
      '{'+Object.keys(x).filter(k=>x[k]!==undefined).sort().map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')+'}':
      JSON.stringify(x);
  const key=(a,b)=>[a,b].sort().join('\u0000');
  function syntheticLink(value) {
    if(value===null)return true;
    try {
      const u=new URL(value);
      return u.protocol==='https:' && u.hostname==='example.invalid' &&
        !u.username && !u.password;
    } catch(_) { return false; }
  }

  async function sha256(text){
    const subtle=root.crypto&&root.crypto.subtle ||
      (typeof module==='object'&&module.exports?require('node:crypto').webcrypto.subtle:null);
    assert(subtle,'SHA-256 unavailable; use HTTPS or localhost.');
    const result=await subtle.digest('SHA-256',new TextEncoder().encode(text));
    return Array.from(new Uint8Array(result),b=>b.toString(16).padStart(2,'0')).join('');
  }
  function allIDsEqual(a,b){return stable(a)===stable(b);}
  const integerFields=['coassigned_count','assigned_both_count','planned_count',
    'missing_pair_count','noise_pair_count','different_cluster_count','failed_fit_count'];
  const weightedFields=['coassigned_weight','assigned_both_weight','planned_weight'];
  const matrixFields=['association','coassigned_count','assigned_both_count','planned_count',
    'coassigned_weight','assigned_both_weight','planned_weight','assignment_coverage'];

  async function validate(env,sidecar){
    assert(C&&V,'W5/W6 independent validators unavailable.');
    C.validateParallel(env);V.validateEnvelope(env);
    assert(env.producer.workstream_id==='W2' && env.producer.fixture_kind==='synthetic' &&
      env.upstream.source_schema==='synthetic.v1' && env.upstream.source_hash_basis==='synthetic' &&
      env.cohort.split==='synthetic' && env.evaluation_role==='engineering_only' &&
      env.publication_eligible===false && env.contract_version==='1.0.0',
      'Public research import requires engineering-only synthetic W2 v1.');
    assert(env.observations.every(o=>syntheticLink(o.source_url) &&
      !['text','quote','source_text','transcript'].some(k=>Object.hasOwn(o,k))),
      'Public preview refuses real source URLs or text-bearing observations.');
    assert(sidecar && sidecar.schema==='un.consensus.v1' &&
      sidecar.version==='0.1.0' && sidecar.contract_schema==='un.parallel-analysis.v1' &&
      sidecar.publication_eligible===false && sidecar.evaluation_role==='engineering_only',
      'Unsupported consensus sidecar schema/version/publication flags.');
    assert(sidecar.source && sidecar.source.cohort &&
      Array.isArray(sidecar.source.observation_keys) &&
      Array.isArray(sidecar.observation_ids) && Array.isArray(sidecar.pairs) &&
      Array.isArray(sidecar.family_weight_audit) &&
      Array.isArray(sidecar.reproducible_groups) &&
      Array.isArray(sidecar.ungrouped_observations) &&
      Array.isArray(sidecar.unsupported_pair_ledger) &&
      sidecar.matrix && sidecar.thresholds,'Incomplete W2 source and pair ledgers.');
    for(const field of ['source_schema','source_engine','source_hash_basis','source_sha256',
      'frame_sha256','corpus_sha256','selection_sha256','review_sha256','missing_reason']){
      assert(sidecar.source[field]===env.upstream[field],
        'Original source '+field+' differs between W2 sidecar and v1 model.');
    }
    for(const field of ['split','population','unit','selection_policy','weighting',
      'source_group_unit','duplicate_policy','total_in_frame','eligible']){
      assert(sidecar.source.cohort[field]===env.cohort[field],
        'W2 sidecar cohort '+field+' mismatch.');
    }
    assert(env.models.length===1 &&
      env.models[0].method_family==='ensemble' &&
      env.models[0].method==='descriptive_complete_link_consensus' &&
      env.models[0].representation_id==='w2-hard-assignment-identity-join-v1' &&
      env.models[0].fit_version===sidecar.version &&
      env.models[0].training_selection_sha256===env.upstream.selection_sha256,
      'W2 v1 fitted identity/version mismatch.');
    assert(env.models[0].parameters_sha256===await sha256(stable(sidecar.thresholds)),
      'W2 threshold parameter SHA-256 does not match the original sidecar.');
    const eligible=env.observations.filter(o=>o.source_status==='available'&&!o.exclusion_reasons.length)
      .sort((a,b)=>a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
    const ids=eligible.map(o=>o.id), observed=new Map(eligible.map(o=>[o.id,o]));
    assert(ids.length>0&&ids.length<=256 && allIDsEqual(ids,sidecar.observation_ids),
      'W2 eligible observation IDs/order are incomplete or exceed producer bounds.');
    assert(sidecar.source.observation_keys.length===ids.length,
      'Original W2 source-key count differs from v1.');
    for(let i=0;i<ids.length;i++){
      const original=sidecar.source.observation_keys[i],row=eligible[i];
      assert(original.id===row.id && SHA.test(original.text_sha256) &&
        ['text_sha256','parent_id','meeting_id','source_url','json_pointer','start','end']
          .every(k=>(original[k]??null)===(row[k]??null)),
        'W2 original observation ID/hash/source-offset lineage changed.');
      assert(syntheticLink(original.source_url) &&
        !['text','quote','source_text','transcript'].some(k=>Object.hasOwn(original,k)),
        'W2 sidecar refuses real source URLs or public source text.');
    }
    const pairMap=new Map(),n=ids.length;
    assert(sidecar.pairs.length===n*(n+1)/2,
      'Incomplete W2 pair frame; missing pairs cannot be silently omitted.');
    for(const p of sidecar.pairs){
      assert(p && observed.has(p.observation_a) && observed.has(p.observation_b) &&
        p.observation_a<=p.observation_b,'Unknown or unordered W2 observation pair.');
      const k=key(p.observation_a,p.observation_b);
      assert(!pairMap.has(k),'Duplicated W2 pair identity.');
      pairMap.set(k,p);
      assert(integerFields.every(f=>count(p[f])) &&
        p.coassigned_count<=p.assigned_both_count &&
        p.assigned_both_count<=p.planned_count &&
        p.planned_count===p.assigned_both_count+p.noise_pair_count+p.missing_pair_count &&
        p.coassigned_count+p.different_cluster_count===p.assigned_both_count &&
        p.failed_fit_count<=p.missing_pair_count,
        'W2 raw coassignment/planned/noise/failure counts do not reconcile.');
      assert(weightedFields.every(f=>finite(p[f])&&p[f]>=0) &&
        p.coassigned_weight<=p.assigned_both_weight+1e-8 &&
        p.assigned_both_weight<=p.planned_weight+1e-8,
        'W2 weighted pair numerator/denominator invalid.');
      assert((p.assigned_both_count===0)===(p.association===null) &&
        (p.association===null || finite(p.association)&&p.association>=0 &&
         p.association<=1&&p.assigned_both_weight>0 &&
         approx(p.association,p.coassigned_weight/p.assigned_both_weight)),
        'W2 conditional weighted association was changed.');
      assert((p.planned_weight===0&&p.assignment_coverage===null) ||
        p.planned_weight>0 && finite(p.assignment_coverage) &&
        approx(p.assignment_coverage,p.assigned_both_weight/p.planned_weight),
        'W2 eligible-pair opportunity coverage changed.');
      assert(Array.isArray(p.contributing_families) &&
        new Set(p.contributing_families).size===p.contributing_families.length,
        'Duplicate W2 method-family contribution.');
    }
    assert(matrixFields.every(f=>Array.isArray(sidecar.matrix[f]) &&
      sidecar.matrix[f].length===n),'Missing W2 original matrix.');
    for(const field of matrixFields)for(let i=0;i<n;i++){
      assert(Array.isArray(sidecar.matrix[field][i]) &&
        sidecar.matrix[field][i].length===n,
        'Original W2 matrix dimensions mismatch.');
      for(let j=0;j<n;j++){
        const p=pairMap.get(key(ids[i],ids[j]));
        assert(p&&sidecar.matrix[field][i][j]===p[field],
          'Original W2 matrix differs from the pair ledger: '+field+'.');
      }
    }
    const audit=sidecar.family_weight_audit,seenFamilies=new Set();
    assert(audit.length>0 && approx(audit.reduce((n,f)=>n+f.total_weight,0),1),
      'Planned family weights do not sum to one.');
    for(const f of audit){
      assert(typeof f.method_family==='string'&&!seenFamilies.has(f.method_family) &&
        finite(f.total_weight)&&f.total_weight>0&&Array.isArray(f.records) &&
        f.records.every(r=>finite(r.planned_weight)&&r.planned_weight>=0) &&
        approx(f.records.reduce((n,r)=>n+r.planned_weight,0),f.total_weight),
        'Original W2 family/method/configuration/seed weights are inconsistent.');
      seenFamilies.add(f.method_family);
    }
    for(const p of sidecar.pairs){
      assert(p.contributing_families.every(f=>seenFamilies.has(f)),
        'W2 pair references an unknown voting method family.');
    }
    const thresholds=sidecar.thresholds;
    assert(finite(thresholds.min_association) && thresholds.min_association>=0 &&
      thresholds.min_association<=1 && finite(thresholds.min_coverage) &&
      thresholds.min_coverage>=0 && thresholds.min_coverage<=1 &&
      count(thresholds.min_families) && count(thresholds.min_source_groups),
      'Invalid descriptive support thresholds.');
    const used=new Set();
    for(const [i,g] of sidecar.reproducible_groups.entries()){
      assert(g.group_id==='G'+String(i+1).padStart(3,'0') &&
        Array.isArray(g.members) && g.members.length>=2 &&
        count(g.source_group_count) && g.source_group_count>=thresholds.min_source_groups,
        'Invalid source-supported complete-link group.');
      for(const id of g.members){
        assert(observed.has(id)&&!used.has(id),'Repeated or unknown W2 group member.');
        used.add(id);
        for(const other of g.members){
          if(id>=other)continue;
          const p=pairMap.get(key(id,other));
          assert(p&&p.association!==null&&p.association>=thresholds.min_association &&
            p.assignment_coverage>=thresholds.min_coverage &&
            p.contributing_families.length>=thresholds.min_families,
            'Unsupported pair included in an alleged complete-link reproducible group.');
        }
      }
    }
    assert(sidecar.ungrouped_observations.length+used.size===n &&
      sidecar.ungrouped_observations.every(id=>observed.has(id)&&!used.has(id)) &&
      new Set(sidecar.ungrouped_observations).size===sidecar.ungrouped_observations.length,
      'Ambiguous/ungrouped source observations were lost.');
    const fitted=new Map(env.results.filter(r=>r.model_id===env.models[0].model_id)
      .map(r=>[r.observation_id,r]));
    const assignment=new Map(sidecar.reproducible_groups.flatMap((g,i)=>
      g.members.map(id=>[id,i+1])));
    for(const row of eligible){
      const fit=fitted.get(row.id);
      assert(fit && fit.cluster===(assignment.get(row.id)||0) &&
        fit.status===(assignment.has(row.id)?'assigned':'unassigned'),
        'W2 v1 group assignment does not match the source-weighted sidecar.');
    }
    return {env,sidecar,ids,pairMap,eligible,
      coverage:env.coverage,
      pairs_total:sidecar.pairs.length,eligible_off_diagonal:n*(n-1)/2};
  }
  function sampleFreeSummary(data){
    const side=data.sidecar;
    return {eligible:data.ids.length,excluded:data.env.coverage.excluded,
      unavailable:data.env.coverage.unavailable_sources,
      pair_opportunities:data.eligible_off_diagonal,
      groups:side.reproducible_groups.length,
      ungrouped:side.ungrouped_observations.length,
      family_count:side.family_weight_audit.length,
      uncertainty:side.uncertainty?.design || 'not_estimated',
      heatmap_state:data.ids.length>35?'withheld_above_35_full_ledger_retained':'available'};
  }

  function setup(){
    const doc=root.document;
    if(!doc||!doc.getElementById('research-w2-import'))return;
    const inputA=doc.getElementById('research-w2-sidecar');
    const inputB=doc.getElementById('research-w2-v1');
    const button=doc.getElementById('research-w2-import');
    const status=doc.getElementById('research-w2-status');
    const info=doc.getElementById('research-w2-summary');
    const chart=doc.getElementById('research-w2-matrix');
    const inspection=doc.getElementById('research-w2-inspection');
    let epoch=0;
    const n=(tag,label)=>{const e=doc.createElement(tag);if(label!==undefined)e.textContent=String(label);return e;};
    const set=(target,msg)=>{target.replaceChildren();if(msg)target.append(n('p',msg));};
    const wipe=()=>{
      // Independently staged C5 views must never outlive changed source files.
      root.dispatchEvent(new CustomEvent('un:c5-w2-clear'));
      epoch++;set(info,'No source-validated W2 consensus displayed.');
      chart.replaceChildren();inspection.replaceChildren();status.textContent='Choose original W2 synthetic output files.';};
    inputA.addEventListener('change',wipe);inputB.addEventListener('change',wipe);
    function recordPair(data,a,b){
      const p=data.pairMap.get(key(a,b));
      inspection.replaceChildren();
      if(!p)return;
      const title=n('h3','Pair · '+a+' / '+b),dl=n('dl');
      const show=(label,value)=>{dl.append(n('dt',label),n('dd',value===null?'Not estimated':value));};
      show('Conditional weighted association',p.association===null?'N/A — no assigned-both evidence':
        (100*p.association).toFixed(1)+'%');
      show('Weighted coassigned / assigned-both / planned',
        p.coassigned_weight+' / '+p.assigned_both_weight+' / '+p.planned_weight);
      show('Raw coassigned / assigned-both / planned',
        p.coassigned_count+' / '+p.assigned_both_count+' / '+p.planned_count);
      show('Assigned-both coverage',p.assignment_coverage===null?'N/A':(100*p.assignment_coverage).toFixed(1)+'%');
      show('Missing / noise / distinct-cluster / failed-fit opportunities',
        [p.missing_pair_count,p.noise_pair_count,p.different_cluster_count,p.failed_fit_count].join(' / '));
      show('Contributing method families',p.contributing_families.join(', ')||'none');
      for(const id of [a,b]){
        const o=data.eligible.find(x=>x.id===id);
        show('Original synthetic observation '+id,'SHA-256: '+o.text_sha256+' · meeting: '+
          (o.meeting_id||'unknown')+' · parent: '+(o.parent_id||'unknown'));
      }
      inspection.append(title,dl,n('p','W2 values are imported without recalculation. Grouped resampling spread is not a confidence interval.'));
    }
    function display(data){
      const s=sampleFreeSummary(data);
      set(info,s.eligible+' eligible synthetic observations; '+s.excluded+' excluded ('+
        s.unavailable+' unavailable); '+s.eligible_off_diagonal+
        ' off-diagonal source pairs, '+s.family_count+' method families; '+
        s.groups+' reproducible descriptive groups and '+s.ungrouped+' ungrouped. '+
        'W2 planned-weight co-assignment is shown directly, not W6’s illustrative equal-rate average.');
      chart.replaceChildren();inspection.replaceChildren();
      if(s.heatmap_state==='withheld_above_35_full_ledger_retained'){
        chart.append(n('p','WITHHELD: '+s.eligible+' eligible observations exceed the 35-ID interactive pair-matrix limit. All '+
          s.pair_opportunities+' pair records were validated and retained without sampling.'));
      }else{
        const wrap=n('div');wrap.className='research-w2-scroll';
        const table=n('table');table.className='research-w2-table';
        table.setAttribute('aria-label','W2 weighted conditional consensus coassignment by observation');
        const thead=n('thead'),head=n('tr');head.append(n('th','Observation ID'));
        for(const id of data.ids)head.append(n('th',id));
        thead.append(head);table.append(thead);
        const tbody=n('tbody');
        for(const a of data.ids){
          const tr=n('tr'),heading=n('th',a);heading.scope='row';tr.append(heading);
          for(const b of data.ids){
            const td=n('td');
            if(a===b){td.textContent='—';}
            else{
              const p=data.pairMap.get(key(a,b)),button=n('button',p.association===null?
                'N/A':(p.association*100).toFixed(0)+'%');
              button.type='button';button.className='research-w2-pair';
              button.setAttribute('aria-label',a+' and '+b+': '+(p.association===null?
                'no eligible coassignment':'weighted coassignment '+(p.association*100).toFixed(1)+' percent'));
              button.addEventListener('click',()=>recordPair(data,a,b));
              td.append(button);
            }
            tr.append(td);
          }
          tbody.append(tr);
        }
        table.append(tbody);wrap.append(table);chart.append(wrap);
        chart.append(n('p','N/A means no assigned-both pair opportunity; 0% means assessed but never coassigned. Select any non-diagonal cell to inspect source hashes and denominators.'));
      }
      const details=n('details'),summary=n('summary','Complete group and method-family weighting ledger');
      const pre=n('pre',JSON.stringify({
        groups:data.sidecar.reproducible_groups,
        ambiguous:data.sidecar.ambiguous_members,
        ungrouped:data.sidecar.ungrouped_observations,
        family_weights:data.sidecar.family_weight_audit,
        resampling:data.sidecar.uncertainty,
        sensitivity:data.sidecar.sensitivity_report,
        thresholds:data.sidecar.thresholds
      },null,2));
      pre.className='research-w2-pre';details.append(summary,pre);chart.append(details);
      status.textContent='Source and W2 model/weighted-pair ledgers verified in this browser. No refit, inference or network upload.';
    }
    async function read(file,label){
      assert(file&&file.size>0&&file.size<=64*1024*1024,
        'Select '+label+' (1 byte to 64 MiB; no sampling).');
      return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer()).replace(/^\uFEFF/,''));
    }
    button.addEventListener('click',async()=>{
      const ticket=++epoch;
      root.dispatchEvent(new CustomEvent('un:c5-w2-clear'));
      chart.replaceChildren();inspection.replaceChildren();
      button.disabled=true;status.textContent='Checking synthetic source identity, v1 model and original W2 weighted pair accounting…';
      try{
        const [sidecar,envelope]=await Promise.all([
          read(inputA.files[0],'consensus-v1.json'),
          read(inputB.files[0],'standardized-interchange-v1.json')]);
        const data=await validate(envelope,sidecar);
        if(ticket!==epoch)return;
        display(data);
        // C5 independently revalidates the exact original W2 sidecar/envelope
        // before rendering. Synthetic engineering only; never a refit.
        root.dispatchEvent(new CustomEvent('un:c5-w2-verified',{
          detail:{env:data.env,sidecar:data.sidecar}
        }));
      }catch(error){
        if(ticket===epoch){
          set(info,'No verified consensus is displayed.');chart.replaceChildren();inspection.replaceChildren();
          status.textContent=String(error.message||error);
        }
      }finally{button.disabled=false;}
    });
  }
  if(root.document){
    if(root.document.readyState==='loading')root.document.addEventListener('DOMContentLoaded',setup,{once:true});
    else setup();
  }
  return Object.freeze({VERSION:'coordinator-w2-readonly-0.1.0',validate,sampleFreeSummary,sha256});
});
