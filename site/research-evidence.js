/* C5: synthetic-only W2 and W4 source-evidence bridge.
 * Research browser integration, not a statistical kernel or release gate.
 * Nothing is fetched, uploaded, refitted, geocoded or interpreted as stance.
 */
(function(root,factory){
  'use strict';
  const api=factory(root);
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.UNResearchEvidence=api;
})(typeof globalThis==='object'?globalThis:this,function(root){
  'use strict';
  const EXPECTED_W4=Object.freeze([
    'w4-source-panel.json','w4-analysis.json','w4-envelope.json','w4-panel.json'
  ]);
  const SHA=/^[a-f0-9]{64}$/;
  const MAX_BYTES=16*1024*1024;
  const check=(yes,why)=>{if(!yes)throw Error('C5 evidence refused: '+why);};
  const oknum=n=>typeof n==='number'&&Number.isFinite(n);
  const approx=(a,b,tol=1e-7)=>oknum(a)&&oknum(b)&&Math.abs(a-b)<=tol;
  const pairKey=(a,b)=>[a,b].sort().join('\u0000');
  const syntheticURL=x=>{
    if(x===null)return true;
    try{
      const u=new URL(x);
      return u.protocol==='https:'&&u.hostname==='example.invalid'&&
        !u.username&&!u.password;
    }catch(_){return false;}
  };
  const hashOk=x=>typeof x==='string'&&SHA.test(x);
  const own=(v,k)=>Object.prototype.hasOwnProperty.call(v,k);
  function renderer(){
    const V=root.UNResearchEvidenceRenderer ||
      (typeof module==='object'&&module.exports?require('../research/integration/w2_w4_w6/evidence_renderer.cjs'):null);
    check(V&&typeof V.renderPanel==='function'&&typeof V.mount==='function',
      'Accepted standalone W2/W4 renderer is unavailable.');
    return V;
  }
  function toW2Panel(data){
    const e=data?.env,report=data?.sidecar,ids=data?.ids;
    check(e&&report&&Array.isArray(ids)&&Array.isArray(report.pairs)&&
      Array.isArray(report.family_weight_audit),'W2 original validated sidecar and source frame required.');
    check(e.producer.workstream_id==='W2'&&
      e.producer.fixture_kind==='synthetic'&&e.cohort.split==='synthetic'&&
      e.upstream.source_hash_basis==='synthetic'&&e.upstream.source_schema==='synthetic.v1'&&
      e.publication_eligible===false&&report.publication_eligible===false,
      'W2 files must be synthetic engineering-only.');
    const source=new Map(e.observations.map(o=>[o.id,o]));
    const expected=e.observations.filter(o=>o.source_status==='available'&&!o.exclusion_reasons.length);
    check(expected.length===ids.length&&new Set(ids).size===ids.length&&
      ids.every(id=>source.has(id)),'Original W2 eligible source identities are incomplete.');
    check(report.pairs.length===ids.length*(ids.length+1)/2,
      'W2 complete pair frame missing.');
    const limited=ids.length>35,model=e.models[0];
    check(model&&model.representation_id==='w2-hard-assignment-identity-join-v1',
      'W2 imported representation identity missing.');
    const ambiguous=new Set(report.ambiguous_members.map(a=>a.observation_id));
    const panel={
      kind:'consensus',pair_mode:'w2_weighted_conditional',
      status:limited?'withheld':'ready',
      reason:limited?'Full '+ids.length+'-observation W2 source matrix exceeds 35 display IDs; all original pairs retained without sampling.':null,
      measure:'Native W2 source-linked weighted conditional co-assignment: preplanned co-assignment weight divided by assigned-both fit weight. Planned-fit coverage, missing/noise, failures and method-family support remain distinct. NOT null-calibrated significance or political positions.',
      identity:{
        source_schema:e.upstream.source_schema,source_hash_basis:e.upstream.source_hash_basis,
        source_sha256:e.upstream.source_sha256,selection_sha256:e.upstream.selection_sha256,
        unit:e.cohort.unit,weighting:e.cohort.weighting,
        representation_id:model.representation_id,representation_version:model.representation_version,
        observation_refs:expected.map(o=>({id:o.id,text_sha256:o.text_sha256}))
      },
      coverage:{frame:e.cohort.total_in_frame,eligible:e.cohort.eligible,
        included:limited?0:ids.length,excluded:e.coverage.excluded,missing:e.coverage.unavailable_sources},
      warnings:[
        'Engineering synthetic W2 results; exact weighted ratio, never W6 illustrative family-rate averaging.',
        'W2 grouped-refit spreads represent descriptive source sensitivity, not confidence intervals, null significance or independent replication.',
        report.uncertainty.source_groups+' declared source groups; '+report.uncertainty.design+
          '. '+report.ambiguous_members.length+' ambiguous membership records; '+
          report.source_restricted_groups.length+' source-restricted groups withheld.'
      ],
      family_weight_audit:report.family_weight_audit.map(f=>({
        family:f.method_family,planned_weight:f.total_weight,
        configurations:f.configurations,models:f.models,
        failed_fit_records:f.completely_failed_fit_records,
        internal_failures:f.internal_failures
      })),
      observation_ids:limited?[]:ids.slice(),
      pairs:limited?[]:report.pairs.filter(p=>p.observation_a!==p.observation_b).map(p=>({
        a:p.observation_a,b:p.observation_b,
        coassigned_count:p.coassigned_count,assigned_both_count:p.assigned_both_count,
        planned_count:p.planned_count,missing_pair_count:p.missing_pair_count,
        noise_pair_count:p.noise_pair_count,different_cluster_count:p.different_cluster_count,
        failed_fit_count:p.failed_fit_count,coassigned_weight:p.coassigned_weight,
        assigned_both_weight:p.assigned_both_weight,planned_weight:p.planned_weight,
        association:p.association,assignment_coverage:p.assignment_coverage,
        contributing_families:p.contributing_families.slice(),
        unstable:ambiguous.has(p.observation_a)||ambiguous.has(p.observation_b),
        missing_reason:p.association===null?
          'No jointly assigned W2 fit weight; association withheld.':null
      }))
    };
    const V=renderer();
    V.validatePanel(e,panel,V.validateEnvelope(e));
    if(panel.status==='ready')V.renderPanel(e,panel);
    return panel;
  }
  async function sha256(bytes){
    const subtle=root.crypto?.subtle||
      (typeof module==='object'&&module.exports?require('node:crypto').webcrypto.subtle:null);
    check(subtle,'SHA-256 unavailable: use HTTPS or localhost.');
    const digest=await subtle.digest('SHA-256',bytes);
    return Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
  }
  async function digestJSON(value){
    return sha256(new TextEncoder().encode(JSON.stringify(value)));
  }
  function equal(a,b){return JSON.stringify(a)===JSON.stringify(b);}
  const mean=xs=>{check(xs.length>0,'Empty source aggregation.');return xs[0].map((_,i)=>
    xs.reduce((total,x)=>total+x[i],0)/xs.length);};
  function groupedPosition(sourceRows,aligned){
    const byGenre=new Map();
    for(const row of sourceRows){
      const kind=row.genre;
      if(!byGenre.has(kind))byGenre.set(kind,new Map());
      const byMeeting=byGenre.get(kind);
      if(!byMeeting.has(row.meeting_id))byMeeting.set(row.meeting_id,[]);
      byMeeting.get(row.meeting_id).push(aligned.get(row.id));
    }
    return mean([...byGenre.values()].map(byMeeting=>
      mean([...byMeeting.values()].map(vectors=>mean(vectors)))));
  }
  function alignment2D(row,mode,model){
    if(mode!=='rigid_full_refit'||row.period===model.before)return row.map;
    const rot=model.rotation,shift=model.translation;
    return [
      row.map[0]*rot[0][0]+row.map[1]*rot[1][0]+shift[0],
      row.map[0]*rot[0][1]+row.map[1]*rot[1][1]+shift[1]
    ];
  }
  function checkSavedAlignment(s,analysis,eligible){
    const mode=analysis.alignment?.mode,prior=analysis.before,later=analysis.after;
    check(mode==='rigid_full_refit'||mode==='identity_pinned_transform',
      'Original W4 comparison has no approved source-preserving map alignment.');
    const dim=s.map_space.dimension;
    check(dim===2,'C5 longitudinal renderer requires a genuine 2D saved map.');
    if(mode==='identity_pinned_transform'){
      check(s.feature_space.fit_policy==='transformed_reference'&&
        analysis.alignment.anchor_count===0&&
        new Set(eligible.map(r=>r.map_fit_id)).size===1,
        'W4 pinned reference must reuse the same saved transform, without new anchors.');
    }else{
      check(s.feature_space.fit_policy==='full_refit','Rigid full-refit mode contradicts source map policy.');
      const d=analysis.alignment,rot=d.rotation,shift=d.translation;
      check(Array.isArray(rot)&&rot.length===2&&rot.every(x=>Array.isArray(x)&&x.length===2&&x.every(oknum))&&
        Array.isArray(shift)&&shift.length===2&&shift.every(oknum),
        'Saved W4 rigid map coefficients missing.');
      const [a,b,c,d0]=[rot[0][0],rot[0][1],rot[1][0],rot[1][1]];
      check(approx(a*a+b*b,1)&&approx(c*c+d0*d0,1)&&approx(a*c+b*d0,0)&&
        approx(a*d0-b*c,1)&&analysis.alignment.scaling_applied===false,
        'W4 alignment must be unscaled and proper orthonormal.');
      const anchors=analysis.alignment.anchor_ids||[];
      check(new Set(anchors).size===anchors.length&&anchors.length>=4&&
        anchors.length===analysis.alignment.anchor_count,
        'W4 independent fit anchor denominator invalid.');
      const matched=new Map();
      for(const actor of anchors){
        const p=eligible.filter(r=>r.actor_id===actor&&r.period===prior);
        const q=eligible.filter(r=>r.actor_id===actor&&r.period===later);
        const shared=new Set(p.map(r=>r.genre).filter(g=>q.some(v=>v.genre===g)));
        check(shared.size>0,'External W4 anchor lacks comparable source genre.');
        matched.set(actor,[groupedPosition(p.filter(r=>shared.has(r.genre)),
          new Map(p.map(r=>[r.id,r.map]))),
          groupedPosition(q.filter(r=>shared.has(r.genre)),
            new Map(q.map(r=>[r.id,r.map])))]);
      }
      const orig=[...matched.values()].map(v=>v[0]),base=mean(orig);
      const aligned=[...matched.values()].map(v=>alignment2D({map:v[1],period:later},mode,{
        before:prior,rotation:rot,translation:shift
      }));
      const rmse=Math.sqrt(mean(orig.map((v,i)=>[
        (aligned[i][0]-v[0])**2+(aligned[i][1]-v[1])**2
      ]))[0]);
      const radius=Math.sqrt(mean(orig.map(v=>[
        (v[0]-base[0])**2+(v[1]-base[1])**2
      ]))[0]);
      const ratio=rmse/Math.max(radius,1e-12);
      check(approx(ratio,analysis.alignment.anchor_relative_rmse,1e-6)&&ratio<=.15,
        'Saved W4 anchor residual cannot be reproduced.');
    }
    return {mode,before:prior,after:later,
      rotation:analysis.alignment.rotation,translation:analysis.alignment.translation};
  }
  async function validateW4(bundle){
    const source=bundle['w4-source-panel.json'],analysis=bundle['w4-analysis.json'],
      e=bundle['w4-envelope.json'],p=bundle['w4-panel.json'];
    check(source?.schema==='un.longitudinal-panel.v1'&&source.split==='synthetic'&&
      e?.schema==='un.parallel-analysis.v1'&&e.contract_version==='1.0.0'&&
      e.producer?.workstream_id==='W4'&&e.producer.fixture_kind==='synthetic'&&
      e.upstream?.source_schema==='synthetic.v1'&&e.upstream.source_hash_basis==='synthetic'&&
      e.evaluation_role==='engineering_only'&&e.publication_eligible===false&&
      analysis?.schema==='un.longitudinal-comparison.v1'&&analysis.split==='synthetic'&&
      analysis.evaluation_role==='engineering_only'&&analysis.publication_eligible===false&&
      p?.kind==='longitudinal',
      'Original W4 source, comparison and output must all be synthetic engineering-only.');
    check(Array.isArray(source.observations)&&source.observations.length>0&&
      source.observations.length<=600&&Array.isArray(e.observations)&&
      Array.isArray(analysis.aligned_coordinates)&&Array.isArray(p.actors)&&
      p.actors.length<=30,'W4 source frame / actor display boundedness invalid.');
    check(Array.isArray(source.periods)&&source.periods.length>=2&&
      source.feature_space?.fingerprint&&hashOk(source.feature_space.fingerprint),
      'Frozen W4 representation fingerprint or period declaration missing.');
    const periods=new Map(source.periods.map(period=>[period.id,period]));
    check(periods.size===source.periods.length&&
      periods.has(analysis.before)&&periods.has(analysis.after)&&analysis.before!==analysis.after,
      'Original W4 periods are mismatched or repeated.');
    const order=source.observations.filter(r=>r.period===analysis.before||r.period===analysis.after);
    check(equal(order.map(r=>r.id),analysis.provenance?.included_observation_ids)&&
      equal(order.map(r=>r.id),e.observations.map(r=>r.id)),
      'Original W4 comparison/frame observation sequence changed.');
    const seen=new Set(),sourceMap=new Map();
    for(let i=0;i<order.length;i++){
      const r=order[i],o=e.observations[i],period=periods.get(r.period);
      check(r.id&&!seen.has(r.id)&&period&&r.date>=period.start&&r.date<=period.end&&
        /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(r.date)&&
        r.source_hash_basis==='synthetic'&&syntheticURL(r.source_url)&&
        !own(r,'text')&&!own(r,'transcript')&&!own(r,'source_text')&&!own(r,'quote')&&
        r.actor_kind==='synthetic'&&r.speaker_id===null&&
        r.country===null&&r.parent_id===null&&r.speech_id===null,
        'W4 original source is not a fictional fully specified source row.');
      seen.add(r.id);sourceMap.set(r.id,r);
      check(['available','unavailable'].includes(r.source_status)&&
        (r.source_status!=='available'||hashOk(r.text_sha256)&&hashOk(r.source_sha256)&&
          r.representation_id===source.feature_space.id&&
          r.representation_version===source.feature_space.version&&
          r.representation_fingerprint===source.feature_space.fingerprint),
        'W4 available source representation or hash basis differs.');
      for(const key of ['id','text_sha256','parent_id','meeting_id','source_family_id',
        'source_url','json_pointer','date','country']){
        check(o[key]===r[key],'W4 original/interchange source pointer differs: '+key);
      }
      check(o.source_status===r.source_status&&!own(o,'text')&&!own(o,'source_text')&&
        syntheticURL(o.source_url),'W4 source availability or text privacy changed.');
    }
    check(e.observations.length===order.length&&e.cohort.eligible===
      order.filter(r=>r.source_status==='available').length&&
      e.cohort.weighting==='equal_meeting','W4 original source eligibility/weighting changed.');
    check(e.upstream.source_sha256===await digestJSON(order.map(r=>[r.id,r.source_sha256]))&&
      e.upstream.selection_sha256===await digestJSON(order.map(r=>r.id)),
      'Original W4 source and selection SHA-256 inconsistent.');
    const V=renderer();
    const lookup=V.validateEnvelope(e);
    V.validatePanel(e,p,lookup);
    const originalIDs=e.observations.filter(o=>o.source_status==='available'&&!o.exclusion_reasons.length)
      .map(o=>o.id);
    check(equal(p.identity.observation_refs.map(r=>r.id),originalIDs)&&
      e.models.length===2&&e.models.every(m=>m.method_family==='imported_partition'&&
        m.method==='saved_source_linked_cluster_assignment'&&
        m.representation_id===source.feature_space.id&&
        m.representation_version===source.feature_space.version)&&
      e.coverage.models.every(x=>x.attempted_fits===0&&x.successful_fits===0&&x.failed_fits===0),
      'Imported W4 fit identities or zero fitted-attempt ledger altered.');
    // The browser does not represent fresh numerical fitting. It checks the
    // actual source mapping and all native saved geometries independently.
    const available=order.filter(r=>r.source_status==='available'),
      aligned=new Map(),mode=analysis.alignment?.mode;
    check(analysis.comparison_status!=='withheld'&&
      ['identity_pinned_transform','rigid_full_refit'].includes(mode),
      'W4 original comparison did not establish aligned source coordinates.');
    const model=checkSavedAlignment(source,analysis,available);
    for(const row of analysis.aligned_coordinates){
      const original=sourceMap.get(row.observation_id);
      check(original&&original.source_status==='available'&&!aligned.has(row.observation_id)&&
        row.period===original.period&&row.actor_id===original.actor_id&&
        row.meeting_id===original.meeting_id&&
        row.source_family_id===original.source_family_id&&
        row.map_fit_id===original.map_fit_id&&row.coordinate_kind==='aligned_display_only'&&
        Array.isArray(row.coordinates)&&row.coordinates.length===2&&row.coordinates.every(oknum),
        'Original W4 aligned source linkage differs or duplicates.');
      const expected=alignment2D(original,model.mode,model);
      check(row.coordinates.every((v,i)=>approx(v,expected[i],1e-7)),
        'Saved W4 coordinate fails independent source-map transform replay.');
      aligned.set(row.observation_id,row.coordinates);
    }
    check(aligned.size===available.length,'W4 saved alignment silently omitted eligible source observations.');
    const familyA=new Set(available.filter(r=>r.period===analysis.before).map(r=>r.source_family_id)),
      familyB=new Set(available.filter(r=>r.period===analysis.after).map(r=>r.source_family_id));
    const shared=[...familyA].filter(v=>familyB.has(v));
    check(shared.length>0,'W4 periods lack paired synthetic source-family series.');
    check(p.periods.length===2&&p.periods[0]===analysis.before&&p.periods[1]===analysis.after&&
      p.alignments.length===1&&p.alignments[0].mode===mode&&
      p.alignments[0].status==='passed'&&
      p.alignments[0].selection_comparability==='checked'&&p.status==='ready'&&
      p.alignments[0].reference_basis===source.feature_space.id,
      'W4 period alignment or selection status is withheld/inconsistent.');
    for(const period of source.periods.filter(x=>p.periods.includes(x.id))){
      check(p.period_bounds?.[period.id]?.start===period.start&&
        p.period_bounds?.[period.id]?.end===period.end,
        'Original W4 period date range drifted.');
    }
    const actorSet=new Set(available.map(r=>r.actor_id).filter(Boolean));
    check(p.actors.length===actorSet.size&&
      p.actors.every(a=>actorSet.has(a.id)&&a.attribution_status.includes('Synthetic')),
      'W4 actor roster contains unsupported identifiers.');
    let displayed=0;
    for(const actor of p.actors){
      check(actor.positions?.length===2&&new Set(actor.positions.map(q=>q.period)).size===2,
        'W4 actor-period position rows incomplete.');
      const inBefore=available.filter(r=>r.actor_id===actor.id&&r.period===analysis.before),
        inAfter=available.filter(r=>r.actor_id===actor.id&&r.period===analysis.after),
        common=new Set(inBefore.map(r=>r.genre).filter(g=>inAfter.some(y=>y.genre===g)));
      for(const q of actor.positions){
        const present=q.period===analysis.before?inBefore:inAfter,
          selected=inBefore.length&&inAfter.length?present.filter(r=>common.has(r.genre)):present,
          claimed=q.observation_ids;
        check(Array.isArray(claimed)&&new Set(claimed).size===claimed.length&&q.n===claimed.length&&
          equal(claimed,selected.map(r=>r.id)),
          'W4 actor/period evidence IDs or declared meeting/genre sample changed.');
        if(!selected.length){
          check(q.xy===null&&['withheld','missing'].includes(q.status),
            'Missing/withheld W4 actor cannot have fabricated coordinates.');
        }else{
          const expected=groupedPosition(selected,aligned);
          check(q.status==='observed'&&Array.isArray(q.xy)&&q.xy.length===2&&
            q.xy.every((v,i)=>approx(v,expected[i],1e-7))&&q.radius===null,
            'W4 actor score deviates from original equal meeting/genre weighted coordinates.');
          displayed+=q.n;
        }
      }
    }
    check(p.coverage.included===displayed&&p.coverage.included<=e.coverage.eligible&&
      p.coverage.excluded===e.coverage.excluded&&
      p.coverage.missing===e.coverage.unavailable_sources,
      'W4 displayed/missing/eligible denominators shifted.');
    V.renderPanel(e,p);
    return {envelope:e,panel:p,source,analysis,
      provenance:{method:mode,eligible:originalIDs.length,
        unavailable_rows:e.coverage.excluded,
        unavailable_source_groups:e.coverage.unavailable_sources,
        actors:p.actors.length,source_families_shared:shared.length,
        publication_eligible:false}};
  }
  async function loadW4Files(files){
    check(files&&files.length===5,'Select exactly SHA256.json and four original W4 synthetic JSON exports.');
    const entries=new Map();
    for(const file of files){
      check(file&&typeof file.name==='string'&&!entries.has(file.name)&&
        (file.name==='SHA256.json'||EXPECTED_W4.includes(file.name))&&
        Number.isSafeInteger(file.size)&&file.size>0&&file.size<=MAX_BYTES,
        'Duplicate, oversized or unexpected W4 input: '+(file?.name||'unnamed'));
      entries.set(file.name,file);
    }
    check(entries.size===5&&entries.has('SHA256.json')&&
      EXPECTED_W4.every(x=>entries.has(x)),'Original W4 manifest or source files missing.');
    const decode=bytes=>new TextDecoder('utf-8',{fatal:true}).decode(bytes).replace(/^\uFEFF/,'');
    const manifest=JSON.parse(decode(await entries.get('SHA256.json').arrayBuffer()));
    check(manifest&&typeof manifest==='object'&&!Array.isArray(manifest)&&
      Object.keys(manifest).length===4&&EXPECTED_W4.every(n=>hashOk(manifest[n])),
      'W4 four-file SHA256 manifest invalid.');
    const out={};
    for(const name of EXPECTED_W4){
      const bytes=await entries.get(name).arrayBuffer();
      check(await sha256(bytes)===manifest[name],
        'W4 exact-file SHA256 mismatch: '+name);
      out[name]=JSON.parse(decode(bytes));
    }
    return validateW4(out);
  }
  function setup(){
    const doc=root.document;
    if(!doc||!doc.getElementById('research-w4-import'))return;
    const V=renderer(),w2Details=doc.getElementById('research-w2-evidence'),
      w2Host=doc.getElementById('research-w2-evidence-chart'),
      w2Status=doc.getElementById('research-w2-evidence-status'),
      w4Input=doc.getElementById('research-w4-files'),
      w4Button=doc.getElementById('research-w4-import'),
      w4Host=doc.getElementById('research-w4-chart'),
      w4Status=doc.getElementById('research-w4-status'),
      w2Svg=doc.getElementById('research-w2-evidence-svg'),
      w2Html=doc.getElementById('research-w2-evidence-html'),
      w4Svg=doc.getElementById('research-w4-svg'),
      w4Html=doc.getElementById('research-w4-html');
    let w2Verified=null,w2Epoch=0,w4Epoch=0,w2View=null,w4View=null;
    function download(name,body,type){
      check(body&&typeof body==='string','No verified source-linked chart available to export.');
      const url=URL.createObjectURL(new Blob([body],{type}));
      const a=doc.createElement('a');a.href=url;a.download=name;
      doc.body.append(a);a.click();a.remove();
      root.setTimeout(()=>URL.revokeObjectURL(url),1000);
    }
    const exportTo=(view,format,name)=>{
      check(view,'Complete source-backed verification is required before export.');
      if(format==='svg')download(name+'.svg',view.svg,'image/svg+xml;charset=utf-8');
      else download(name+'.html',V.htmlDocument(view),'text/html;charset=utf-8');
    };
    w2Svg.addEventListener('click',()=>exportTo(w2View,'svg','w2-weighted-consensus-synthetic'));
    w2Html.addEventListener('click',()=>exportTo(w2View,'html','w2-weighted-consensus-synthetic'));
    w4Svg.addEventListener('click',()=>exportTo(w4View,'svg','w4-longitudinal-synthetic'));
    w4Html.addEventListener('click',()=>exportTo(w4View,'html','w4-longitudinal-synthetic'));
    const clearW2=()=>{
      w2Epoch++;w2Verified=null;w2View=null;w2Host.replaceChildren();
      w2Svg.disabled=true;w2Html.disabled=true;
      w2Status.textContent='Import original synthetic W2 results in the section above.';
    };
    async function showW2(){
      const ticket=++w2Epoch;
      w2Host.replaceChildren();w2View=null;w2Svg.disabled=true;w2Html.disabled=true;
      if(!w2Verified){w2Status.textContent='No validated W2 source available.';return;}
      w2Status.textContent='Independently checking weighted pair and source identities…';
      try{
        const C=root.UNResearchConsensus;
        check(C?.validate,'Original W2 source validator is unavailable.');
        const verified=await C.validate(w2Verified.env,w2Verified.sidecar);
        if(ticket!==w2Epoch)return;
        const panel=toW2Panel(verified);
        w2View=V.mount(w2Host,verified.env,[panel])[0];
        w2Svg.disabled=false;w2Html.disabled=false;
        w2Status.textContent=panel.status==='withheld'?panel.reason:
          'Original source-bound W2 conditional weighted heatmap verified. Inspect any pair; no refit or policy inference.';
      }catch(error){
        if(ticket===w2Epoch){
          w2Host.replaceChildren();
          w2Status.textContent=String(error.message||error);
        }
      }
    }
    root.addEventListener('un:c5-w2-clear',clearW2);
    root.addEventListener('un:c5-w2-verified',event=>{
      clearW2();
      w2Verified=event.detail;
      w2Status.textContent='Weighted W2 import verified. Expand the evidence chart to inspect original numerator/denominators.';
      if(w2Details.open)void showW2();
    });
    w2Details.addEventListener('toggle',()=>{
      if(w2Details.open)void showW2();
    });
    const clearW4=()=>{
      w4Epoch++;w4Host.replaceChildren();w4View=null;
      w4Svg.disabled=true;w4Html.disabled=true;
      w4Status.textContent='No original W4 source and aligned synthetic output verified.';
    };
    w4Input.addEventListener('change',clearW4);
    w4Button.addEventListener('click',async()=>{
      const ticket=++w4Epoch;
      w4Host.replaceChildren();w4View=null;
      w4Svg.disabled=true;w4Html.disabled=true;
      w4Button.disabled=true;
      w4Status.textContent='Checking original W4 synthetic SHA256, source, imported fits, saved map alignment and actor weighting…';
      try{
        const result=await loadW4Files(w4Input.files);
        if(ticket!==w4Epoch)return;
        w4View=V.mount(w4Host,result.envelope,[result.panel])[0];
        w4Svg.disabled=false;w4Html.disabled=false;
        w4Status.textContent='Verified original W4 frozen basis and '+result.provenance.eligible+
          ' eligible synthetic observations; '+result.provenance.actors+
          ' source-linked actors; '+result.provenance.source_families_shared+
          ' paired source-family series. Descriptive display only.';
      }catch(error){
        if(ticket===w4Epoch){
          w4Host.replaceChildren();
          w4Status.textContent=String(error.message||error);
        }
      }finally{w4Button.disabled=false;}
    });
  }
  if(root.document){
    if(root.document.readyState==='loading')
      root.document.addEventListener('DOMContentLoaded',setup,{once:true});
    else setup();
  }
  return Object.freeze({VERSION:'c5-synthetic-source-bound-0.1.0',
    toW2Panel,validateW4,loadW4Files,sha256,groupedPosition});
});
