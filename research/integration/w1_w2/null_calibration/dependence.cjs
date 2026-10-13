'use strict';
/* Typed fictional dependence closure, not proof of exchangeable samples. */
const {dependences}=require('./world.cjs');
const check=(x,m)=>{if(!x)throw Error('synthetic-null-dependence: '+m);};
function closure(rows,fields){
 const n=rows.length,p=Array.from({length:n},(_,i)=>i),seen=new Map();
 const find=i=>{while(p[i]!==i){p[i]=p[p[i]];i=p[i];}return i;};
 const union=(a,b)=>{let x=find(a),y=find(b);if(x!==y)p[y]=x;};
 const edges=Object.fromEntries(fields.map(x=>[x,0]));
 rows.forEach((r,i)=>{
   for(const field of fields){
     const value=r[field];
     if(value==null||value==='')continue;
     const key=field+'\u001f'+value;
     if(seen.has(key)){union(i,seen.get(key));edges[field]++;}
     else seen.set(key,i);
   }
 });
 const counts=new Map();
 for(let i=0;i<n;i++){const x=find(i);counts.set(x,(counts.get(x)||0)+1);}
 return {components:counts.size,largest_component:Math.max(0,...counts.values()),
   component_sizes:[...counts.values()].sort((a,b)=>b-a),edge_counts:edges};
}
function audit(world,scenario){
 check(world&&world.frame&&world.design&&scenario,
   'world and frozen nuisance scenario required');
 const rows=world.frame.observations.filter(x=>x.source_status==='available');
 const raw=dependences(world,scenario);
 check(rows.length===world.design.eligible,'source/dependence denominator mismatch');
 const meeting=closure(rows,['meeting_id','parent_id','source_family_id']);
 const affiliation=closure(rows,['meeting_id','parent_id','source_family_id','affiliation']);
 // Date_year must be explicit, not synthesized as a one-off property that
 // silently yields no matches. Use a separate immutable derived view.
 const yearRows=rows.map(r=>({...r,date_year:r.date?.slice(0,4)}));
 const yearClosure=closure(yearRows,['meeting_id','parent_id','source_family_id','date_year']);
 const repeated=rows.length>0?affiliation.largest_component/rows.length:0;
 const hardRefusal=raw.cross_meeting_source_families>0;
 const riskFlags=[
   ...raw.flags,
   ...(affiliation.components<meeting.components?
     ['recorded_affiliation_connects_distinct_meeting_groups']:[]),
   ...(yearClosure.components<meeting.components?
     ['calendar_year_connects_distinct_meetings']:[])
 ];
 return {
   schema:'un.w1-w2.synthetic-dependence-audit.v1',
   scenario_id:scenario.id,source_split:'synthetic',
   inventory_observations:world.frame.observations.length,eligible:rows.length,
   unavailable:world.frame.observations.length-rows.length,
   distinct_meeting_labels:raw.source_group_count,
   recorded_affiliation_count:raw.distinct_recorded_affiliations,
   within_meeting_duplicate_text_groups:raw.duplicate_text_groups,
   cross_meeting_original_source_family_links:raw.cross_meeting_source_families,
   meeting_parent_family_closure:meeting,
   affiliation_augmented_closure:affiliation,
   year_augmented_closure:yearClosure,
   largest_affiliation_connected_share:repeated,
   year_shock_oracle_rho:scenario.year_rho,
   four_years_per_era:scenario.year_count===8,
   nonrandom_attendance:scenario.nonrandom_attendance,
   risk_flags:[...new Set(riskFlags)],
   group_refit_admissible:!hardRefusal,
   effectively_independent_meetings_established:false,
   source_group_exchangeability_verified:false,
   inferential_eligible:false,
   withheld_reason:hardRefusal?
      'Original source family crosses declared meeting boundaries; do not split group refits or assert independent meeting opportunities.':
      'Nuisance oracle/source-group graph is fictional and does not establish empirical exchangeability.'
 };
}
module.exports={audit,closure};
