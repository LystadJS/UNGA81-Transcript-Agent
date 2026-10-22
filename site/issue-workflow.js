/* Source-bound humanitarian policy observations; no fitting or interpolation. */
(function(root){'use strict';
const P=typeof module!=='undefined'&&module.exports?require('./position-comparison'):root.UNPositions;
const L=typeof module!=='undefined'&&module.exports?require('./passage-labels'):root.UNPassageLabels;
const S=typeof module!=='undefined'&&module.exports?require('./meeting-scopes'):root.UNMeetingScopes;
const policies=['humanitarian_access','civilian_protection'];
const validDate=x=>typeof x==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(x).toISOString().slice(0,10)===x;
function bounds(asOf){if(!validDate(asOf))throw Error('Choose a valid historical as-of date.');const end=new Date(asOf+'T00:00:00Z'),year=end.getUTCFullYear()-10,month=end.getUTCMonth(),day=Math.min(end.getUTCDate(),new Date(Date.UTC(year,month+1,0)).getUTCDate()),start=new Date(Date.UTC(year,month,day+1));return {start:start.toISOString().slice(0,10),end:asOf};}
function state(rows){if(!rows.length)return 'missing';const s=new Set(rows.map(r=>r.stance));return s.size===1?[...s][0]:'mixed';}
const clear=s=>s==='support'||s==='oppose';
function build(corpus,history,settings){
 const window=bounds(settings.as_of);if(!validDate(settings.start)||!validDate(settings.end)||settings.end<settings.start||settings.end>window.end)throw Error('Choose a current briefing period ending on or before the historical as-of date.');
 if(!S.isValid(settings.scope||'all'))throw Error('Invalid issue meeting scope.');
 const scope=settings.scope||'all',region=settings.region||'All regions',exclude=settings.excludeUnresolved!==false;
 // Primary and historical collections stay intact. This union removes only exact source identities.
 const union=new Map(),hashes=new Map(),conflictIds=new Set();for(const r of [...(history?.records||[]),...corpus.records]){const key=r.id+'|'+r.text_sha256;if(union.has(key))continue;if(hashes.has(r.id)&&hashes.get(r.id)!==r.text_sha256)conflictIds.add(r.id);hashes.set(r.id,r.text_sha256);union.set(key,r);}
 const all=[...union.values()];
 const eligible=all.filter(r=>!conflictIds.has(r.id)&&r.language==='en'&&r.date>=window.start&&r.date<=window.end&&S.matchesRecord(r,scope)&&(!exclude||!L.unresolved(r)));
 const names=[...new Set(all.filter(r=>r.date>=window.start&&r.date<=window.end&&r.country&&r.attribution?.country_status==='registry_mapped'&&S.matchesRecord(r,scope)&&(region==='All regions'||r.region===region||P.isUS(r.country))).map(r=>P.isUS(r.country)?P.US:r.country))].sort();
 const currentIds=new Set(corpus.records.map(r=>r.id+'|'+r.text_sha256));
 const meeting=corpus.collection?.selection_mode==='single_meeting'?corpus.collection.selected_meeting_slug:null;
 const currentEligible=eligible.filter(r=>currentIds.has(r.id+'|'+r.text_sha256)&&(!meeting||(r.meeting_slug||r.id.split('#')[0])===meeting));
 const months=[];for(let d=new Date(window.start.slice(0,7)+'-01T00:00:00Z');d.toISOString().slice(0,7)<=window.end.slice(0,7);d.setUTCMonth(d.getUTCMonth()+1))months.push(d.toISOString().slice(0,7));
 const years=[...new Set(months.map(m=>m.slice(0,4)))];const questions=[];let withheld={attribution:0,context:0,unclear:0};
 for(const id of policies){const extracted=P.evidence(eligible,{positionPolicy:id,positionContext:'*'}),currentEvidence=P.evidence(currentEligible,{positionPolicy:id,positionContext:'*'}).found;for(const k in withheld)withheld[k]+=extracted.withheld[k];const contexts=[...new Set(extracted.found.map(r=>r.context))].sort();if(!contexts.length)contexts.push('unspecified');
  for(const context of contexts){const evidence=extracted.found.filter(r=>r.context===context),index=new Map();for(const r of evidence){const k=r.country+'|'+r.date;if(!index.has(k))index.set(k,[]);index.get(k).push(r);}
   const usDates=[...new Set(evidence.filter(r=>P.isUS(r.country)).map(r=>r.date))].sort();const us=new Map(usDates.map(d=>[d,index.get(P.US+'|'+d)||[]]));
   const countries=names.map(country=>{
    const own=evidence.filter(r=>r.country===country),dates=[...new Set(own.map(r=>r.date))].sort();
    const observations=dates.map(date=>({date,state:state(index.get(country+'|'+date)||[]),sources:index.get(country+'|'+date)||[]}));
    const selectedRows=currentEvidence.filter(o=>o.country===country&&o.context===context&&o.date>=settings.start&&o.date<=settings.end),latestDate=selectedRows.map(o=>o.date).sort().at(-1),latestSources=selectedRows.filter(o=>o.date===latestDate),latest=latestDate?{date:latestDate,state:state(latestSources),sources:latestSources}:null;
    const comparisons=dates.filter(d=>us.has(d)).map(date=>{const a=state(index.get(country+'|'+date)||[]),b=state(us.get(date));return {date,country_state:a,us_state:b,relationship:context==='unspecified'||context==='domestic'?'context_gap':clear(a)&&clear(b)?a===b?'same_direction':'opposite_direction':'qualified_or_mixed',country_sources:index.get(country+'|'+date)||[],us_sources:us.get(date)};});
    const trajectory=months.map(month=>{const rows=comparisons.filter(r=>r.date.startsWith(month)),same=rows.filter(r=>r.relationship==='same_direction').length,opposite=rows.filter(r=>r.relationship==='opposite_direction').length;return {month,same,opposite,comparable_dates:same+opposite,same_direction_percent:same+opposite?100*same/(same+opposite):null};});
    return {country,current_state:latest?.state||'missing',current_date:latest?.date||null,current_sources:latest?.sources||[],observations,comparisons,trajectory,years:years.map(year=>({year,observed_dates:observations.filter(o=>o.date.startsWith(year)).length})),comparable_dates:trajectory.reduce((n,r)=>n+r.comparable_dates,0)};
   });
   const population=countries.filter(c=>!P.isUS(c.country)),counts=Object.fromEntries(['support','oppose','qualified','mixed','missing'].map(k=>[k,population.filter(c=>c.current_state===k).length]));
   questions.push({policy:{id,label:P.POLICIES.find(p=>p.id===id).label},context:{id:context,label:P.CONTEXTS.find(c=>c.id===context)?.label||context},counts,population:population.length,countries,us_history:usDates.map(date=>({date,state:state(us.get(date)),sources:us.get(date)}))});
  }
 }
 const yearsCoverage=years.map(year=>{const rows=eligible.filter(r=>r.date.startsWith(year));return {year,source_meetings:new Set(rows.map(r=>r.meeting_slug||r.id.split('#')[0])).size,recorded_countries:new Set(rows.map(r=>r.country)).size,policy_countries:new Set(questions.flatMap(q=>q.countries.filter(c=>c.years.some(y=>y.year===year&&y.observed_dates)).map(c=>c.country))).size};});
 return {schema:'un.humanitarian-issue-workflow.v1',issue:'Humanitarian access and civilian protection',window,current:{start:settings.start,end:settings.end},settings:{...settings,scope,region,excludeUnresolved:exclude},months,years,countries:names,questions,years_coverage:yearsCoverage,withheld,conflicting_source_ids:[...conflictIds],historical_archive_loaded:!!history,model:{status:'withheld_not_fitted',reason:'Observed explicit positions only. No validated ten-year policy-trajectory estimator or calibrated uncertainty is deployed.'},summary:{recorded_affiliations:names.length,countries_with_current_positions:new Set(questions.flatMap(q=>q.countries.filter(c=>!P.isUS(c.country)&&c.current_state!=='missing').map(c=>c.country))).size,countries_with_comparisons:new Set(questions.flatMap(q=>q.countries.filter(c=>!P.isUS(c.country)&&c.comparable_dates).map(c=>c.country))).size,years_with_sources:yearsCoverage.filter(y=>y.source_meetings).length,calendar_years:years.length},limitations:['The population is recorded affiliations in the loaded source collections, not all UN members or a representative sample of governments.','Current opinion counts use each country’s latest explicit expression within the selected briefing period, once per policy and context; dates can differ. Unknowns stay in the denominator.','Historical comparisons require the same policy, context and date. Qualified, conflicting, domestic and unspecified-context expressions do not enter direction percentages.','Charts show monthly shares of comparable observed dates, not modeled ideology, policy agreement probabilities, forecasts or positions between statements.','The rolling window includes partial endpoint calendar years/months. Empty periods mean missing loaded evidence, not silence, neutrality or policy stability.','Historical coverage is not certified complete. Official documentary notes are excluded from country-position statistics. Group attribution and unresolved wording safeguards remain in force.'],external_ai_calls:0};
}
const api={build,bounds,validDate,policies};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNIssueWorkflow=api;
})(typeof globalThis!=='undefined'?globalThis:this);
