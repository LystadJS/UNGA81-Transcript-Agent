/* Local explicit-policy comparison. No sentiment, embeddings, votes or carry-forward. */
(function(root){
'use strict';
const T=typeof module!=='undefined'&&module.exports?require('./text-units.js'):root.UNTextUnits;
const P=typeof module!=='undefined'&&module.exports?require('./passage-labels.js'):root.UNPassageLabels;
const POLICIES=[
 {id:'humanitarian_access',label:'Allow humanitarian access',target:/\b(?:humanitarian access|aid access|(?:unhindered|unimpeded|unrestricted|safe) (?:delivery|provision|distribution) of humanitarian (?:aid|assistance))\b/i},
 {id:'civilian_protection',label:'Protect civilians',target:/\b(?:protect(?:ing)? civilians|protection of civilians|civilian protection)\b/i},
 {id:'ceasefire',label:'Establish a ceasefire',target:/\b(?:ceasefire|cessation of hostilities)\b/i},
 {id:'two_state',label:'A two-state solution',target:/\btwo[ -]state solution\b/i},
 {id:'tpnw',label:'Treaty on the Prohibition of Nuclear Weapons',global:true,target:/\b(?:TPNW|Treaty on the Prohibition of Nuclear Weapons)\b/i},
 {id:'ctbt',label:'Comprehensive Nuclear-Test-Ban Treaty',global:true,target:/\b(?:CTBT|Comprehensive (?:Nuclear[ -])?Test[ -]Ban Treaty)\b/i},
 {id:'cuba_embargo',label:'Lift the embargo on Cuba',cuba:true,target:/\b(?:lift(?:ing)?|end(?:ing)?|remov(?:e|ing|al of))\b[^.!?]{0,55}\b(?:embargo|blockade)\b/i}
];
const CONTEXTS=[{id:'sudan',label:'Sudan',pattern:/(?:(?<!South )\bSudan\b|\b(?:Darfur|Kordofan|Al[ -](?:Fasher|Obeid))\b)/i},{id:'gaza',label:'Gaza',pattern:/\bGaza\b/i},{id:'west_bank',label:'West Bank',pattern:/\bWest Bank\b/i},{id:'ukraine',label:'Ukraine',pattern:/\b(?:Ukraine|Ukrainian)\b/i},{id:'myanmar',label:'Myanmar',pattern:/\b(?:Myanmar|Burma)\b/i},{id:'lebanon',label:'Lebanon',pattern:/\bLebanon\b/i},{id:'cuba',label:'Cuba',pattern:/\bCuba(?:n)?\b/i},{id:'south_sudan',label:'South Sudan',pattern:/\bSouth Sudan\b/i},{id:'yemen',label:'Yemen',pattern:/\bYemen\b/i},{id:'syria',label:'Syria',pattern:/\bSyria\b/i},{id:'haiti',label:'Haiti',pattern:/\bHaiti\b/i},{id:'afghanistan',label:'Afghanistan',pattern:/\bAfghanistan\b/i},{id:'global',label:'Global treaty (TPNW / CTBT)'}];
const US='United States';
const isUS=c=>/^(?:United States(?: of America)?|U\.?S\.?A?\.?)$/i.test(String(c||'').trim());
const country=r=>isUS(r.country)?US:r.country;
const safe=u=>{try{const v=new URL(u);return v.origin==='https://transcripts.un.org'&&!v.username&&!v.password&&!v.hash?v.href:null;}catch{return null;}};
function options(p){
 const positionPolicy=p.positionPolicy===undefined?'humanitarian_access':p.positionPolicy;
 const policy=POLICIES.find(x=>x.id===positionPolicy);if(!policy)throw Error('Choose a supported explicit policy question.');
 const positionContext=p.positionContext===undefined?(policy.global?'global':policy.cuba?'cuba':'sudan'):p.positionContext;
 if(!CONTEXTS.some(x=>x.id===positionContext)||(policy.global&&positionContext!=='global')||(!policy.global&&positionContext==='global')||(policy.cuba&&positionContext!=='cuba'))throw Error('Choose a valid context for this policy question.');
 const positionCountry=p.positionCountry===undefined?'':p.positionCountry;
 if(typeof positionCountry!=='string'||positionCountry.length>120||isUS(positionCountry))throw Error('Choose a comparison country other than the U.S. baseline.');
 return {positionPolicy,positionContext,positionCountry};
}
function national(r){
 const a=P.attribution(r),fn=String(r.speaker_metadata?.function||'');
 const nationalCapacity=/\b(?:in (?:my|our) national capacity|in my capacity as (?:the )?representative of)\b/i.test(r.text||'');
 return r.attribution?.country_status==='registry_mapped'&&r.region!=='Unmapped'&&typeof r.country==='string'&&!['collective','mixed_or_ambiguous','institutional'].includes(a.kind)&&
  (!/\b(?:chair|presiding|moderator|rapporteur|secretariat|journalist|civil society|press|president of (?:the )?(?:council|assembly|committee))\b/i.test(fn)||nationalCapacity)&&!/^(?:President|National President)$/i.test(fn.trim());
}
function context(line,r,policy){
 if(policy.global)return {id:'global',basis:'named_global_treaty'};
 const hits=text=>CONTEXTS.filter(c=>c.pattern?.test(text));
 const places=[...line.matchAll(/\b(?:in|throughout|across|within)\s+(?:(?:the|occupied|northern|southern|eastern|western)\s+)*([A-Z][\p{L}'-]+(?:\s+[A-Z][\p{L}'-]+){0,3})/gu)];
 if(places.some(m=>!hits(m[1]).length))return null;
 const direct=hits(line);if(direct.length===1)return {id:direct[0].id,basis:'explicit_sentence'};if(direct.length>1)return null;
 const meeting=hits(r.meeting||''),segment=hits(r.text||'');
 if(segment.length>1)return null;
 if(segment.length===1)return meeting.some(c=>c.id===segment[0].id)?{id:segment[0].id,basis:'single_segment_context_matching_recorded_meeting_title'}:null;
 return meeting.length===1?{id:meeting[0].id,basis:'recorded_meeting_title'}:null;
}
function direction(line,policy){
 if(!policy.target.test(line)||!T.summaryEvidenceSentence(line)||T.unclearWording(line))return null;
 // Reported advocacy and quotations are not the speaker's own declaration.
 if(/\b(?:according to|said|says|stated|claims?|quoted|believes?|argues?|maintains?|asserts?|announced|the report|the resolution|the declaration)\b|[“”\"]/i.test(line))return null;
 const qualified=/\b(?:if|unless|provided that|subject to|only|when|on condition|with the consent|would|could|might|temporary|conditional|unilateral|partial|limited|excluding|except|not all)\b/i.test(line);
 const uncertainObject=/\bwithout\s+(?!(?:delay|restrictions?|obstruction)\b)/i.test(line);
 const states=[];
 for(let clause of line.split(/;|\b(?:but|however|although)\b|,\s*(?=(?:we|i|our delegation|my delegation)\b)/i)){
  clause=clause.trim().replace(/^(?:in this (?:context|regard),\s*|(?:first|second|third),\s*)/i,'');
  const action=/^(?:we|i|our delegation|my delegation|our government|my government)\s+(?:(?:strongly|fully|firmly|also|continue to)\s+){0,3}(do not support|cannot support|oppose|reject|object to|support|endorse|welcome|call for|call on|urge|demand|advocate|stress the need for|stress the need to)\b\s*([^.!?]+)/i.exec(clause);
  if(action){
   const object=action[2],at=object.search(policy.target),prefix=object.slice(0,at);
   if(at<0||T.wordCount(prefix)>14)continue;
   if(/\b(?:report|resolution|declaration|statement|proposal|that|which|whether|who|because|while|sanctions?|attacks?|violence|obstruction|restrictions?|denial|obstruct(?:ing|ion)?|restrict(?:ing)?|imped(?:e|ing)|prevent(?:ing)?|block(?:ing)?|deny(?:ing)?|denying|withdraw(?:al|ing)?|violate|violat(?:ing|ions?)|rejection|opposition|abolition|cancellation|termination|military|intervention)\b/i.test(prefix))continue;
   if(/\b(?:no|not|without|rather than|instead of|neither|nor|lift|lifting|removal|ending)\b/i.test(prefix)&&!policy.cuba){states.push('qualified');continue;}
   if(/\band\s+(?:oppose|reject|support|do not support)\b/i.test(object.slice(at)))states.push('qualified');
   else {const negative=/^(?:do not|cannot|oppose|reject|object)/i.test(action[1]);states.push(negative&&prefix.replace(/\b(?:the|a|an)\b/ig,'').trim()?'qualified':negative?'oppose':'support');}
  }else if(!policy.cuba){
   const at=clause.search(policy.target);if(at<0)continue;
   const before=clause.slice(0,at),after=clause.slice(at);
   if(/\b(?:must|should|need to)\s+(?:(?:ensure|facilitate|allow|guarantee|protect|establish|achieve|secure|provide|respect|implement|uphold)\s+(?:(?:full|safe|rapid|sustained|unhindered|unimpeded|and|the|a|an)[, ]+)*)?$/i.test(before)||/^(?:humanitarian access|aid access|protection of civilians|civilian protection|(?:a |an |the )?(?:immediate |permanent |durable )?(?:ceasefire|cessation of hostilities))\s+(?:must|should|needs? to)\s+(?:be (?:ensured|allowed|facilitated|protected|established|achieved|guaranteed)|remain (?:unhindered|unimpeded))/i.test(after))states.push('support');
  }
 }
 if(!states.length)return null;
 if(qualified||uncertainObject||states.includes('qualified'))return 'qualified';
 return new Set(states).size===1?states[0]:'mixed';
}
function evidence(records,p){
 const policy=POLICIES.find(x=>x.id===p.positionPolicy),found=[],withheld={attribution:0,context:0,unclear:0};const seen=new Set();
 for(const r of records){
  if(!policy.target.test(r.text||''))continue;
  if(!national(r)){withheld.attribution++;continue;}
  if(P.unresolved(r)){withheld.unclear++;continue;}
  T.sentences(r.text).forEach((line,index)=>{
   const stance=direction(line,policy);if(!stance)return;
   const c=context(line,r,policy);if(!c||c.id!==p.positionContext){withheld.context++;return;}
   if(policy.cuba&&!/\bCuba(?:n)?\b/i.test(r.text))return;
   const url=safe(r.source_url);if(!url)return;
   const key=[country(r),r.date,line.toLowerCase().replace(/\s+/g,' ')].join('|');if(seen.has(key))return;seen.add(key);
   found.push({record_id:r.id,text_sha256:r.text_sha256,raw_sha256:r.raw_sha256||null,json_pointer:r.json_pointer||null,country:country(r),date:r.date,policy:policy.id,context:c.id,context_basis:c.basis,stance,excerpt:line,sentence_index:index,source_url:url,attribution:'Recorded country affiliation; automatic provisional expression, not a verified government position'});
  });
 }
 return {found,withheld};
}
function state(rows){const dirs=new Set(rows.map(x=>x.stance));if(!rows.length)return 'missing';if(dirs.size===1)return [...dirs][0];return 'mixed';}
function build(records,baselineRecords,settings){
 const p={...settings,...options(settings)},policy=POLICIES.find(x=>x.id===p.positionPolicy),a=evidence(records,p),b=evidence(baselineRecords.filter(r=>isUS(r.country)),p);
 const withheldRecords=records.filter(r=>policy.target.test(r.text||'')&&(!national(r)||P.unresolved(r))).map(r=>({record_id:r.id,source_url:safe(r.source_url),attribution:P.attribution(r),reason:!national(r)?'not_an_unambiguous_national_statement':'unresolved_wording'}));
 if(!Number.isFinite(Date.parse(p.start))||!Number.isFinite(Date.parse(p.end))||p.end<p.start||(Date.parse(p.end)-Date.parse(p.start))/86400000>30)throw Error('Use an inclusive position comparison period of at most 31 days.');
 const dates=[];for(let t=Date.parse(p.start);t<=Date.parse(p.end);t+=86400000)dates.push(new Date(t).toISOString().slice(0,10));
 const names=[...new Set(records.filter(national).map(country))].filter(c=>c!==US).sort();if(p.positionCountry&&!names.includes(p.positionCountry))names.push(p.positionCountry);
 const ownIndex=new Map(),usIndex=new Map();
 for(const row of a.found){const key=row.country+'|'+row.date;if(!ownIndex.has(key))ownIndex.set(key,[]);ownIndex.get(key).push(row);}
 for(const row of b.found){if(!usIndex.has(row.date))usIndex.set(row.date,[]);usIndex.get(row.date).push(row);}
 const daysFor=name=>dates.map(date=>{
  const own=ownIndex.get(name+'|'+date)||[],us=usIndex.get(date)||[],ownState=state(own),usState=state(us);
  const comparable=['support','oppose'].includes(ownState)&&['support','oppose'].includes(usState);
  const comparison=comparable?(ownState===usState?'same_direction':'opposite_direction'):ownState==='missing'&&usState==='missing'?'both_missing':ownState==='missing'?'country_missing':usState==='missing'?'us_missing':'qualified_or_mixed';
  return {date,country_state:ownState,us_state:usState,comparison,value:comparable?(ownState===usState?0:1):null,country_evidence:own,us_evidence:us};
 });
 const countries=names.map(name=>{const days=daysFor(name),withEvidence=days.filter(d=>d.country_evidence.length),latest=withEvidence.at(-1);return {country:name,days,latest:latest||null,comparable_days:days.filter(d=>d.value!==null).length,gap_days:days.filter(d=>d.value===null).length};});
 const best=countries.slice().sort((x,y)=>y.comparable_days-x.comparable_days||y.days.filter(d=>d.country_evidence.length).length-x.days.filter(d=>d.country_evidence.length).length||x.country.localeCompare(y.country))[0];
 const selected=p.positionCountry||best?.country||null;
 return {schema:'un.explicit-position-comparison.v1',method:'bounded_policy_rules_same_day_no_imputation_v1',policy:{id:policy.id,label:policy.label},context:{id:p.positionContext,label:CONTEXTS.find(c=>c.id===p.positionContext).label},baseline:US,selected_country:selected,start:p.start,end:p.end,countries,trajectory:countries.find(c=>c.country===selected)?.days||dates.map(date=>{const us=usIndex.get(date)||[];return {date,comparison:us.length?'country_missing':'both_missing',value:null,country_evidence:[],us_evidence:us,country_state:'missing',us_state:state(us)};}),us_days:dates.map(date=>({date,state:state(usIndex.get(date)||[]),evidence:usIndex.get(date)||[]})),withheld:a.withheld,withheld_records:withheldRecords,baseline_source_count:baselineRecords.filter(r=>isUS(r.country)).length,baseline_evidence_count:b.found.length,status:'automatic_provisional_not_human_reviewed',limitations:['Only expressed direction on the selected bounded policy question and context is compared. This is not overall diplomatic alignment or agreement on every condition, scope or implementation detail.','Position evidence is deduplicated separately within each country and date; identical wording from different countries is retained.','The U.S. baseline uses the same retained collection, dates, meeting scope, topic and exclusions, but ignores the speaker-region filter.','Both countries need explicit, unqualified evidence on the same calendar date. No past statement is carried forward and no missing value is interpolated.','Qualified, conflicting, collective, institutional, unresolved and merely descriptive wording cannot establish national alignment.','A change can come from the country, the U.S., or both. Inspect both dated statements; the chart does not establish a country policy shift.','These automatic rules cover a small, declared policy catalogue and can miss valid positions. Source affiliations and automatic transcript wording are not independently verified.'],external_ai_calls:0};
}

function overview(records,baselineRecords,settings){
 const questions=[];
 for(const policy of POLICIES){
  if(!records.concat(baselineRecords).some(r=>policy.target.test(r.text||'')))continue;
  for(const ctx of CONTEXTS.filter(c=>policy.global?c.id==='global':policy.cuba?c.id==='cuba':c.id!=='global')){
   const q=build(records,baselineRecords,{...settings,positionPolicy:policy.id,positionContext:ctx.id,positionCountry:''});
   if(q.baseline_evidence_count||q.countries.some(c=>c.latest))questions.push(q);
  }
 }
 const names=[...new Set(records.filter(r=>r.country&&r.region!=='Unmapped').map(country))];
 if(baselineRecords.some(r=>isUS(r.country))&&!names.includes(US))names.push(US);
 const countries=names.sort().map(name=>{
  const positions=questions.flatMap(q=>{
   const days=name===US?q.us_days.map(d=>({date:d.date,country_state:d.state,country_evidence:d.evidence,us_state:d.state,us_evidence:d.evidence,comparison:'reference',value:null})):q.countries.find(c=>c.country===name)?.days||[];
   if(!days.some(d=>d.country_evidence.length))return [];
   return [{policy:q.policy,context:q.context,days,same:days.filter(d=>d.comparison==='same_direction').length,opposite:days.filter(d=>d.comparison==='opposite_direction').length,gaps:days.filter(d=>d.value===null).length}];
  });
  const same=positions.reduce((n,p)=>n+p.same,0),opposite=positions.reduce((n,p)=>n+p.opposite,0);
  return {country:name,positions,comparable_question_dates:same+opposite,same_direction:same,opposite_direction:opposite,agreement_percent:same+opposite?100*same/(same+opposite):null};
 });
 return {schema:'un.country-position-overview.v1',status:'automatic_provisional_not_human_reviewed',baseline:US,start:settings.start,end:settings.end,countries,questions,countries_with_positions:countries.filter(c=>c.positions.length).length,countries_comparable:countries.filter(c=>c.comparable_question_dates).length,weighting:'One comparison per policy question, context and calendar date, with equal weight. Source repetition adds no weight.',limitations:['This covers the declared policy catalogue, not every possible opinion in a meeting. Unrecognized or ambiguous positions remain unestablished.','Agreement is the share of comparable question-dates with the same expressed direction. It is not overall diplomatic alignment. Different countries can have different comparison coverage.','Only explicit national expressions are compared. Group statements, unresolved wording and missing U.S. evidence cannot establish agreement.','No position is carried forward or interpolated. Statements on the same question and date are consolidated; conflicting or qualified evidence remains a gap.'],external_ai_calls:0};
}
const api={POLICIES,CONTEXTS,US,isUS,options,national,context,direction,evidence,build,overview};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNPositions=api;
})(typeof globalThis!=='undefined'?globalThis:this);
