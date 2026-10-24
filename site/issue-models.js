/* Observed comparisons and explicit assessment gates. No fitted model is shipped. */
(function(root){'use strict';
const VERSION='un.issue-models.v1', STATES=['support','oppose','qualified'];
const registry=Object.freeze([
 {id:'observed_exact_date_v1',estimand:'observed_same_policy_context_date_direction',status:'implemented_descriptive'},
 {id:'categorical_state_space_v1',estimand:'dated_national_statement_state',status:'not_implemented'},
 {id:'categorical_smooth_v1',estimand:'dated_national_statement_state',status:'not_implemented'},
 {id:'observed_vote_alignment_v1',estimand:'observed_same_resolution_vote_alignment',status:'implemented_descriptive'},
 {id:'dynamic_vote_v1',estimand:'dated_resolution_vote',status:'not_implemented'}
]);
const date=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&!isNaN(Date.parse(x))&&new Date(x).toISOString().slice(0,10)===x;
const us=x=>/^(USA|US|United States(?: of America)?)$/i.test(x);
function canonical(x){if(Array.isArray(x))return '['+x.map(v=>v===undefined?'null':canonical(v)).join(',')+']';if(x&&typeof x==='object')return '{'+Object.keys(x).filter(k=>x[k]!==undefined).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';return JSON.stringify(x);}
function state(rows){const values=[...new Set(rows.map(r=>r.stance))];return values.length===0?'missing':values.length===1?values[0]:'conflicting';}
function panel(events,options={}){
 const start=options.start,end=options.end;if(!date(start)||!date(end)||start>end)throw Error('Valid panel dates are required.');
 const countries=new Set((options.countries||[]).map(c=>us(c)?'United States':c)), cells=new Map(),withheld=[], identities=new Map(),conflicts=new Set();
 for(const e of events){if(!e||typeof e!=='object'){withheld.push({reason:'invalid_event'});continue;}const id=e.id||e.event_id||e.observation_id;if(!id){withheld.push({reason:'missing_identity'});continue;}const fingerprint=canonical(e);if(identities.has(id)&&identities.get(id)!==fingerprint)conflicts.add(id);identities.set(id,fingerprint);}
 const seen=new Set();for(const e of events){if(!e||typeof e!=='object')continue;const id=e.id||e.event_id||e.observation_id;if(!id)continue;if(seen.has(id))continue;seen.add(id);
  const affiliation=e.country_id||e.country,country=us(affiliation)?'United States':affiliation,policy=e.policy_id||e.policy,context=e.context_id||e.context,kind=e.evidence_kind||(e.source_kind==='un_statement'?'statement':e.source_kind)||'statement';
  let reason=null;if(conflicts.has(id))reason='conflicting_event_identity';else if(kind!=='statement')reason='separate_evidence_kind';else if(!country||!policy||!context||['unspecified','domestic'].includes(context))reason='missing_comparable_identity';else if(!date(e.date)||e.date<start||e.date>end)reason='outside_window';else if(!['national_explicit','national'].includes(e.attribution))reason='national_attribution_not_established';else if(e.unresolved)reason='unresolved';else if(!['support','oppose','qualified','conflicting'].includes(e.stance))reason='no_explicit_position';else if(!e.source_id||!(e.source_revision||e.source_revision_id))reason='missing_source_revision';
  if(reason){withheld.push({id,reason});continue;}countries.add(country);const key=canonical([country,policy,context,e.date]);if(!cells.has(key))cells.set(key,{country_id:country,policy_id:policy,context_id:context,date:e.date,events:[]});cells.get(key).events.push(e);
 }
 const observations=[...cells.values()].map(c=>({...c,state:state(c.events),source_ids:[...new Set(c.events.map(e=>e.source_id))].sort()})).sort((a,b)=>canonical([a.country_id,a.policy_id,a.context_id,a.date]).localeCompare(canonical([b.country_id,b.policy_id,b.context_id,b.date])));
 return {schema:VERSION,start,end,countries:[...countries].sort(),observations,withheld,missingness:'No expression is missing evidence, never a neutral or stable position.'};
}
function observed(panelData){
 const reference=new Map(panelData.observations.filter(r=>us(r.country_id)).map(r=>[canonical([r.policy_id,r.context_id,r.date]),r]));
 const countries=panelData.countries.filter(c=>!us(c)).map(country_id=>({country_id,comparisons:panelData.observations.filter(r=>r.country_id===country_id).map(r=>{const ref=reference.get(canonical([r.policy_id,r.context_id,r.date])),clear=s=>s==='support'||s==='oppose';return {date:r.date,policy_id:r.policy_id,context_id:r.context_id,country_state:r.state,us_state:ref?.state||'missing',relationship:!ref?'missing_us':!clear(r.state)||!clear(ref.state)?'qualified_or_conflicting':r.state===ref.state?'same_direction':'opposite_direction',country_source_ids:r.source_ids,us_source_ids:ref?.source_ids||[]};})}));
 return {schema:VERSION,method:'observed_exact_date_v1',modeled:false,start:panelData.start,end:panelData.end,countries,us_reference:[...reference.values()],interpolation:false};
}
function votes(input){
 const rows=input.map(r=>({...r,country_id:us(r.country_id||r.country)?'United States':r.country_id||r.country,resolution_id:r.resolution_id||r.resolution,resolution_revision:r.resolution_revision||r.resolution_version}));
 const eligible=['yes','no','abstain'];const seen=new Map(),conflict=new Set();
 for(const r of rows){const k=canonical([r.resolution_id,r.resolution_revision,r.stage,r.country_id]);if(seen.has(k)&&canonical(seen.get(k))!==canonical(r))conflict.add(k);seen.set(k,r);}
 const valid=[...seen.entries()].filter(([k,r])=>!conflict.has(k)&&r.resolution_id&&r.resolution_revision&&r.stage==='adopted_resolution'&&r.eligible===true&&eligible.includes(r.vote)&&r.source_id&&r.source_revision&&date(r.date)).map(([,r])=>r);
 const refs=new Map(valid.filter(r=>us(r.country_id)).map(r=>[canonical([r.resolution_id,r.resolution_revision,r.date]),r]));
 return {schema:VERSION,method:'observed_vote_alignment_v1',modeled:false,comparisons:valid.filter(r=>!us(r.country_id)).map(r=>{const ref=refs.get(canonical([r.resolution_id,r.resolution_revision,r.date]));return {...r,us_vote:ref?.vote||null,relationship:!ref?'missing_us':r.vote===ref.vote?'same_recorded_vote':'different_recorded_vote'};}),withheld_count:rows.length-valid.length,limitations:['Abstention is retained as its own category. Absence, ineligibility, consensus and amendment votes do not enter this baseline. Matching votes do not establish agreement on the complete issue.']};
}
const defaultGates=Object.freeze({min_test:30,min_countries:5,min_dates:5,min_source_groups:5,max_brier:0.5,max_calibration_error:0.15,min_interval_coverage:0.85,max_interval_coverage:0.99,max_runtime_ms:10000,max_stability_delta:0.1});
function assess(candidate,benchmark,gates={}){
 const g={...defaultGates,...gates},reasons=[],samples=benchmark?.test||[],predictions=new Map((candidate.predictions||[]).map(p=>[p.id,p]));
 if(!candidate.id||typeof candidate.id!=='string')reasons.push('missing_candidate_identity');
 if(Object.values(g).some(v=>!Number.isFinite(v)||v<0))reasons.push('invalid_gate_configuration');
 if(benchmark?.label_status!=='owner_confirmed')reasons.push('benchmark_not_owner_confirmed');
 if(candidate.estimand!==benchmark?.estimand)reasons.push('incompatible_estimand');
 if(!candidate.version||!candidate.evaluation_version||!benchmark?.version)reasons.push('unversioned_assessment');
 const train=benchmark?.train||[],validation=benchmark?.validation||[];
 if(!benchmark?.snapshot_id||[...train,...validation,...samples].some(s=>!s.source_id||!s.source_revision||s.review_state!=='owner_confirmed'))reasons.push('unverified_benchmark_provenance');
 const testMin=samples.map(s=>s.date).sort()[0],validationMin=validation.map(s=>s.date).sort()[0],max=a=>a.map(s=>s.date).sort().at(-1);
 if(!train.length||!validation.length||!samples.length||[...train,...validation,...samples].some(s=>!date(s.date))||!(max(train)<validationMin&&max(validation)<testMin))reasons.push('invalid_temporal_split');
 const groups=a=>new Set(a.map(s=>s.source_group));const tg=groups(train),vg=groups(validation),eg=groups(samples);
 if([...train,...validation,...samples].some(s=>!s.id||!s.source_group)||[...eg].some(s=>tg.has(s)||vg.has(s))||[...vg].some(s=>tg.has(s)))reasons.push('source_group_leakage');
 if(new Set([...train,...validation,...samples].map(s=>s.id)).size!==train.length+validation.length+samples.length)reasons.push('duplicate_sample_identity');
 if(samples.length<g.min_test||new Set(samples.map(s=>s.country_id)).size<g.min_countries||new Set(samples.map(s=>s.date)).size<g.min_dates||eg.size<g.min_source_groups)reasons.push('insufficient_test_support');
 if(!Number.isFinite(candidate.runtime_ms)||candidate.runtime_ms<0||candidate.runtime_ms>g.max_runtime_ms)reasons.push('runtime_gate');
 if(!Number.isFinite(candidate.stability_delta)||candidate.stability_delta<0||candidate.stability_delta>g.max_stability_delta)reasons.push('stability_gate');
 if(new Set((candidate.predictions||[]).map(p=>p.id)).size!==(candidate.predictions||[]).length)reasons.push('duplicate_prediction');
 let brier=0,logloss=0,covered=0,valid=0;const bins=Array.from({length:10},()=>({n:0,p:0,correct:0}));
 for(const s of samples){const p=predictions.get(s.id),prob=p?.probabilities,values=STATES.map(k=>prob?.[k]);if(!STATES.includes(s.label)||!p||values.some(v=>!Number.isFinite(v)||v<0||v>1)||Math.abs(values.reduce((a,b)=>a+b,0)-1)>1e-6||!Array.isArray(p.prediction_set)||!p.prediction_set.length||p.prediction_set.some(k=>!STATES.includes(k))){reasons.push('invalid_or_missing_prediction');continue;}valid++;brier+=values.reduce((n,v,i)=>n+(v-(s.label===STATES[i]?1:0))**2,0);logloss-=Math.log(Math.max(1e-15,prob[s.label]));covered+=Number(p.prediction_set.includes(s.label));const best=STATES.reduce((a,b)=>prob[a]>=prob[b]?a:b),confidence=prob[best],bin=bins[Math.min(9,Math.floor(confidence*10))];bin.n++;bin.p+=confidence;bin.correct+=Number(best===s.label);}
 const metrics={test_samples:samples.length,evaluated_samples:valid,brier:valid?brier/valid:null,log_loss:valid?logloss/valid:null,calibration_error:valid?bins.reduce((n,b)=>n+Math.abs(b.correct-b.p),0)/valid:null,prediction_set_coverage:valid?covered/valid:null,runtime_ms:candidate.runtime_ms};
 if(valid){if(metrics.brier>g.max_brier)reasons.push('brier_gate');if(metrics.calibration_error>g.max_calibration_error)reasons.push('calibration_gate');if(metrics.prediction_set_coverage<g.min_interval_coverage||metrics.prediction_set_coverage>g.max_interval_coverage)reasons.push('prediction_set_coverage_gate');}
 return {id:candidate.id,version:candidate.version,estimand:candidate.estimand,eligible:reasons.length===0,reasons:[...new Set(reasons)],metrics,benchmark_version:benchmark?.version,evaluation_version:candidate.evaluation_version,gates:g};
}
function tournament(candidates,benchmark,gates){const assessments=candidates.map(c=>assess(c,benchmark,gates));const eligible=assessments.filter(a=>a.eligible).sort((a,b)=>a.metrics.log_loss-b.metrics.log_loss||a.metrics.brier-b.metrics.brier||a.metrics.runtime_ms-b.metrics.runtime_ms||a.id.localeCompare(b.id));return {schema:VERSION,status:eligible.length?'accepted_on_supplied_benchmark':'observed_baseline_only',selected:eligible[0]?.id||'observed_exact_date_v1',assessments,selection_rule:'Eligible same-estimand candidates only: held-out log loss, Brier score, runtime, stable identifier. No candidates are fitted by this module.'};}
function cacheKey(spec){for(const k of ['snapshot','ontology','extractor','panel','method','evaluation','as_of','start','end','scope','policy_id','context_id','parameters'])if(spec[k]===undefined||spec[k]===null)throw Error('Missing artifact identity: '+k);if(!date(spec.as_of)||!date(spec.start)||!date(spec.end)||spec.start>spec.end||spec.end>spec.as_of)throw Error('Invalid artifact dates.');return VERSION+'|'+canonical(spec);}
function artifact(spec,result,assessment,sourceDependencies){if(!Array.isArray(sourceDependencies)||sourceDependencies.some(s=>!s.id||!s.revision))throw Error('Versioned source dependencies are required.');return {schema:'un.issue-model-artifact.v1',key:cacheKey(spec),spec:JSON.parse(canonical(spec)),source_dependencies:JSON.parse(canonical(sourceDependencies)),result:JSON.parse(canonical(result)),assessment:JSON.parse(canonical(assessment))};}
function invalidated(artifactData,changes){return artifactData.source_dependencies.some(s=>changes.some(c=>c.id===s.id&&c.revision!==s.revision));}
const api={VERSION,registry,defaultGates,panel,observed,votes,assess,tournament,cacheKey,artifact,invalidated};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNIssueModels=api;
})(typeof globalThis!=='undefined'?globalThis:this);
