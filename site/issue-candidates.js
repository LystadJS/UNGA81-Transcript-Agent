/* Experimental recency-weighted categorical evidence distributions, never accepted trajectories. */
(function(root){'use strict';
const STATES=['support','oppose','qualified'],VERSION='un.issue-candidates.experimental.v1';
const registry=Object.freeze([
 {id:'categorical_discounted_evidence_v1',estimand:'dated_national_statement_state',status:'experimental_not_accepted',description:'Dirichlet-smoothed exponentially discounted past observed categories; no fitted state-transition process.'},
 {id:'categorical_one_sided_kernel_v1',estimand:'dated_national_statement_state',status:'experimental_not_accepted',description:'Dirichlet-smoothed one-sided Gaussian kernel over past observed categories; not a GAM.'}
]);
const day=x=>{if(typeof x!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(x)||!Number.isFinite(Date.parse(x))||new Date(x).toISOString().slice(0,10)!==x)throw Error('Invalid candidate date.');return Date.parse(x+'T00:00:00Z')/86400000;};
const isUS=x=>['US','USA','United States','United States of America'].includes(x);
const name=x=>isUS(x)?'United States':x;
function options(spec){
 const settings={half_life_days:90,bandwidth_days:90,max_gap_days:180,min_dates:3,min_weight:1,prior_per_category:0.5,max_events:100000,...spec.parameters};
 if(!registry.some(m=>m.id===spec.method))throw Error('Unknown experimental candidate.');
 for(const k of ['half_life_days','bandwidth_days','max_gap_days','min_dates','min_weight','prior_per_category','max_events'])if(!Number.isFinite(settings[k])||settings[k]<=0)throw Error('Positive finite parameter required: '+k);
 if(!Number.isInteger(settings.max_events)||settings.max_events>100000||!Number.isInteger(settings.min_dates))throw Error('Candidate resource/date limits must be bounded integers.');
 if(day(spec.date)>day(spec.cutoff))throw Error('Forecasting beyond the historical cutoff is disabled.');
 if(!spec.country_id||!spec.policy_id||!spec.context_id||['unspecified','domestic'].includes(spec.context_id))throw Error('Explicit country, policy and context required.');
 return settings;
}
function estimate(events,spec){
 const config=options(spec),target=day(spec.date),cutoff=day(spec.cutoff);if(!Array.isArray(events)||events.length>config.max_events)throw Error('Candidate event resource limit exceeded.');
 const cells=new Map(),identities=new Map(),bad=new Set(),exclusions=new Set(spec.excluded_source_groups||[]);
 for(const e of events){const id=e.id||e.observation_id;if(!id)continue;const fingerprint=JSON.stringify([e.country_id||e.country,e.policy_id||e.policy,e.context_id||e.context,e.date,e.stance,e.source_id,e.source_revision||e.source_revision_id,e.attribution,e.unresolved,e.source_kind]);if(identities.has(id)&&identities.get(id)!==fingerprint)bad.add(id);identities.set(id,fingerprint);}
 let withheld=0;const seen=new Set();
 for(const e of events){const id=e.id||e.observation_id;if(!id||bad.has(id)||seen.has(id)){withheld++;continue;}seen.add(id);
  const country=name(e.country_id||e.country),policy=e.policy_id||e.policy,context=e.context_id||e.context;
  if(country!==name(spec.country_id)||policy!==spec.policy_id||context!==spec.context_id)continue;
  let date;try{date=day(e.date);}catch{withheld++;continue;}
  if(date>=target||date>cutoff)continue; // A test-date expression is never its own training label.
  if(!['national','national_explicit'].includes(e.attribution)||!STATES.includes(e.stance)||e.unresolved||!e.source_id||!(e.source_revision||e.source_revision_id)||exclusions.size&&!e.source_group||exclusions.has(e.source_group)||e.source_kind&&e.source_kind!=='un_statement'||e.evidence_kind&&e.evidence_kind!=='statement'){withheld++;continue;}
  if(!cells.has(e.date))cells.set(e.date,{date,states:new Set(),sources:new Map()});const c=cells.get(e.date);c.states.add(e.stance);c.sources.set(e.source_id+'|'+(e.source_revision||e.source_revision_id),{id:e.source_id,revision:e.source_revision||e.source_revision_id});
 }
 const eligible=[...cells.values()].filter(c=>c.states.size===1).sort((a,b)=>a.date-b.date),latest=eligible.at(-1),gap=latest?target-latest.date:null;
 const base={schema:VERSION,method:spec.method,estimand:'dated_national_statement_state',status:'experimental_not_accepted',calibrated:false,accepted:false,date:spec.date,cutoff:spec.cutoff,country_id:name(spec.country_id),policy_id:spec.policy_id,context_id:spec.context_id,parameters:config,training_dates:eligible.length,last_observation_gap_days:gap,withheld,conflicting_dates:[...cells.values()].filter(c=>c.states.size>1).length,probabilities:null,prediction_set:null,limitations:['Probabilities summarize a recency-weighted past evidence distribution, not a validated latent government position.','No held-out calibration or interval acceptance has been established. Missing and stale evidence produce gaps.','Each eligible country/policy/context/date contributes once; political and source dependence still require empirical assessment.']};
 if(eligible.length<config.min_dates)return {...base,reason:'insufficient_distinct_training_dates'};
 if(gap>config.max_gap_days)return {...base,reason:'historical_evidence_gap'};
 const mass=Object.fromEntries(STATES.map(s=>[s,config.prior_per_category]));let weight=0;for(const c of eligible){const age=target-c.date,w=spec.method==='categorical_discounted_evidence_v1'?Math.exp(-Math.LN2*age/config.half_life_days):Math.exp(-0.5*(age/config.bandwidth_days)**2);mass[[...c.states][0]]+=w;weight+=w;}
 if(weight<config.min_weight)return {...base,effective_weight:weight,reason:'insufficient_recent_evidence_weight'};
 const total=Object.values(mass).reduce((a,b)=>a+b,0),probabilities=Object.fromEntries(STATES.map(s=>[s,mass[s]/total]));
 return {...base,reason:'experimental_distribution_only',effective_weight:weight,probabilities,source_dependencies:[...new Map(eligible.flatMap(c=>[...c.sources.entries()])).values()]};
}
function compare(events,spec){
 const country=estimate(events,spec),us=estimate(events,{...spec,country_id:'United States'});
 if(!country.probabilities||!us.probabilities)return {schema:VERSION,status:'withheld',reason:'Both country and U.S. need supported recent training evidence.',country,us,relationship_distribution:null};
 const a=country.probabilities,b=us.probabilities,same=a.support*b.support+a.oppose*b.oppose,opposite=a.support*b.oppose+a.oppose*b.support;
 return {schema:VERSION,status:'experimental_not_accepted',accepted:false,calibrated:false,country,us,relationship_distribution:{same_clear_direction:same,opposite_clear_direction:opposite,qualified_or_unresolved:Math.max(0,1-same-opposite)},interval:null,assumption:'Joint category mass assumes conditional independence of the two evidence distributions. It propagates U.S. category uncertainty but is not calibrated agreement probability or a confidence interval.'};
}
const api={VERSION,registry,estimate,compare};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNIssueCandidates=api;
})(typeof globalThis!=='undefined'?globalThis:this);
