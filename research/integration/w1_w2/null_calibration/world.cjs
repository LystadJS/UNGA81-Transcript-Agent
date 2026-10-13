'use strict';
/*
 * Entirely invented lexical nuisance worlds. Original text never enters.
 * Source metadata belongs to a fictional design, never a UN speaker.
 */
const {digest,validateFrame}=require('../../../validation_framework/frame.cjs');
const {rng,normal}=require('./lock.cjs');
const check=(x,m)=>{if(!x)throw Error('synthetic-null-world: '+m);};
const group=(name,key,n=10)=>Array.from({length:n},(_,i)=>
  name+String(key).replace(/[^a-z0-9]/gi,'')+'lex'+i);
const TOKENS={
 common:group('common','fictional',18),
 genre:[group('genre','address'),group('genre','dialogue')],
 role:[group('role','presenter'),group('role','respondent')],
 language:[group('lang','mora'),group('lang','sina')],
 yearPositive:group('chron','rise'),
 yearNegative:group('chron','fall')
};
function choose(weights,random){
 let total=0;
 for(const w of weights){check(Number.isFinite(w.weight)&&w.weight>=0,'invalid category weight');total+=w.weight;}
 check(total>0,'nonpositive synthetic lexical mixture');
 let p=random()*total;
 for(const w of weights){p-=w.weight;if(p<=0)return w.pool[Math.floor(random()*w.pool.length)];}
 const last=weights.at(-1).pool;
 return last[Math.floor(random()*last.length)];
}
function design(scenario){
 check(scenario&&/^[NP]\d/.test(scenario.id)&&
   Array.isArray(scenario.group_sizes)&&scenario.group_sizes.length===scenario.meetings,
   'frozen scenario required');
 const planned=[];
 let index=0,duplicateDone=0;
 for(let m=0;m<scenario.meetings;m++)for(let j=0;j<scenario.group_sizes[m];j++){
   const affiliation=j%scenario.affiliations;
   const genre=(m+j)%2,language=(m+j*3)%2,role=j%2;
   const agenda=(m+j%2)%scenario.agenda_categories;
   const yearIndex=m%scenario.year_count;
   const absent=scenario.nonrandom_attendance && j===2 && m%2===1;
   const same=scenario.duplicate_pairs_within_meeting>duplicateDone && j===1;
   if(same)duplicateDone++;
   const parentKey='fictional-parent-'+m+'-'+(same?0:j);
   const familyKey='family-'+m+'-'+(same?0:j);
   const cross=scenario.source_family_cross_meeting&&j===0&&(m===0||m===1);
   const p={
     id:scenario.id+'-m'+String(m).padStart(2,'0')+'-r'+j,
     design_order:index++,meeting_index:m,
     meeting_id:'fictional-meeting-'+m,year_index:yearIndex,
     date:String(scenario.year_start+yearIndex)+'-01-10',
     parent_id:parentKey,parent_text_sha256:digest(parentKey),
     source_family_id:cross?'invented-cross-meeting-source-family':familyKey,
     affiliation_index:affiliation,affiliation:'fictional-affiliation-'+affiliation,
     country:affiliation===scenario.affiliations-1&&m===0?null:'fictional-affiliation-'+affiliation,
     agenda_index:agenda,genre_index:genre,role_index:role,language_index:language,
     genre:genre===0?'fictional-address':'fictional-dialogue',
     role:role===0?'fictional-presenter':'fictional-respondent',
     language:language===0?'fictional-mora':'fictional-sina',
     token_length:14+(3*j+7*m)%17,
     duplicate_with_previous:same,unavailable:absent
   };
   if(same){
     const previous=planned.at(-1);
     check(previous.meeting_id===p.meeting_id,'duplicate cannot cross meeting');
     p.token_length=previous.token_length;
   }
   planned.push(p);
 }
 const unavailableTail=Array.from({length:scenario.unavailable_rows},(_,i)=>({
   id:scenario.id+'-unavailable-'+i,meeting_id:'fictional-unknown-source-'+i,
   source_status:'unavailable',text_sha256:null,exclusion_reasons:['source_not_collected'],
   missing_reason:'Invented unavailable source, not a zero issue mention',
   date:null,parent_id:null,parent_text_sha256:null,source_family_id:null
 }));
 return Object.freeze({schema:'un.w1-w2.synthetic-null.design.v1',scenario_id:scenario.id,
   planned,unavailableTail,planned_total:planned.length+unavailableTail.length,
   eligible:planned.filter(x=>!x.unavailable).length,
   unavailable:planned.filter(x=>x.unavailable).length+unavailableTail.length,
   declared_source_meetings:scenario.meetings,year_count:scenario.year_count,
   attendance_fingerprint:digest(planned.map(x=>[x.id,x.meeting_id,x.date,
     x.unavailable,x.token_length,x.parent_id,x.source_family_id,
     x.genre,x.role,x.language,x.agenda_index,x.affiliation]))});
}
function generate(scenario,seed,{nullReference=false}={}){
 check(Number.isSafeInteger(seed)&&seed>=0&&seed<=0xffffffff,'unsigned seed required');
 const blueprint=design(scenario),random=rng(seed);
 const meetingEffects=Array.from({length:scenario.meetings},()=>normal(random));
 const affiliationEffects=Array.from({length:scenario.affiliations},()=>normal(random));
 const years=[];
 for(let y=0;y<scenario.year_count;y++){
   const shock=normal(random);
   years.push(y===0?shock:scenario.year_rho*years[y-1]+
     Math.sqrt(1-scenario.year_rho**2)*shock);
 }
 const agendaPools=Array.from({length:scenario.agenda_categories},(_,a)=>group('agenda',a,12));
 const meetingPools=Array.from({length:scenario.meetings},(_,m)=>group('meeting',m,12));
 const affiliationPools=Array.from({length:scenario.affiliations},(_,a)=>group('actor',a,10));
 const latentPools=Array.from({length:3},(_,t)=>group('planted',t,12));
 const texts=new Map(),rows=[],signals=new Map();
 for(const p of blueprint.planned){
   const absent=p.unavailable;
   let text=null,truth=null;
   if(!absent){
     truth=(p.meeting_index+p.design_order%scenario.affiliations)%3;
     const previous=blueprint.planned[p.design_order-1];
     if(p.duplicate_with_previous)text=texts.get(previous.id);
     else{
       const yearShock=years[p.year_index],addSignal=nullReference?0:scenario.signal_strength;
       const pools=[
         {pool:TOKENS.common,weight:0.48},
         {pool:agendaPools[p.agenda_index],weight:scenario.agenda_strength},
         {pool:meetingPools[p.meeting_index],weight:scenario.meeting_strength*
            (0.35+Math.abs(meetingEffects[p.meeting_index]))},
         {pool:affiliationPools[p.affiliation_index],weight:scenario.affiliation_strength*
            (0.4+Math.abs(affiliationEffects[p.affiliation_index]))},
         {pool:yearShock>=0?TOKENS.yearPositive:TOKENS.yearNegative,
           weight:scenario.year_strength*(0.15+Math.abs(yearShock))},
         {pool:TOKENS.genre[p.genre_index],weight:0.35},
         {pool:TOKENS.role[p.role_index],weight:0.25},
         {pool:TOKENS.language[p.language_index],weight:0.4},
         {pool:latentPools[truth],weight:addSignal*1.6}
       ];
       text=Array.from({length:p.token_length},()=>choose(pools,random)).join(' ');
     }
     check(text.split(' ').length===p.token_length,
       'frozen token length/within-meeting duplicates changed');
     texts.set(p.id,text);
     signals.set(p.id,truth);
   }
   rows.push({
     id:p.id,split:'synthetic',source_status:absent?'unavailable':'available',
     exclusion_reasons:absent?['fictional_attendance_missing']:[],
     missing_reason:absent?'Fictional nonrandom attendance missing, not absence':null,
     text_sha256:text===null?null:digest(text),...(text===null?{}:{text}),
     parent_id:absent?null:p.parent_id,parent_text_sha256:absent?null:p.parent_text_sha256,
     meeting_id:p.meeting_id,source_family_id:absent?null:p.source_family_id,
     date:p.date,country:absent?null:p.country,affiliation:absent?null:p.affiliation,
     genre:p.genre,role:p.role,language:p.language,source_url:null,
     review_status:'not_applicable',json_pointer:absent?null:'/invented/'+p.design_order,
     start:text===null?null:0,end:text===null?null:[...text].length,unit:'synthetic'
   });
 }
 for(const p of blueprint.unavailableTail)rows.push({
   ...p,split:'synthetic',date:'2000-01-11',
   country:null,affiliation:null,genre:null,role:null,language:null,
   source_url:null,review_status:'not_applicable',
   json_pointer:null,start:null,end:null,unit:'synthetic'
 });
 const sourceHash=digest(JSON.stringify({
   fictional_scenario:scenario.id,world_seed:seed,
   inventory:rows.map(r=>[r.id,r.text_sha256,r.source_status,r.meeting_id]),
   null_reference:nullReference
 }));
 const frame={
   schema:'un.source-validation.frame.v1',split:'synthetic',
   source_schema:'un.source-validation.synthetic.v1',
   source_engine:'prospective-synthetic-nuisance-oracle-v1',
   source_hash_basis:'synthetic',source_sha256:sourceHash,
   unit:'synthetic',inventory_meetings:scenario.meetings+blueprint.unavailableTail.length,
   observations:rows
 };
 const validated=validateFrame(frame);
 check(validated.eligible.length===blueprint.eligible&&
   validated.rows.length===blueprint.planned_total,
   'eligible/unavailable source ledger differs from frozen design');
 return {frame,design:blueprint,truth:signals,year_shocks:years.slice(),receipt:{
   schema:'un.w1-w2.synthetic-null.world.v1',scenario_id:scenario.id,
   source_hash_basis:'synthetic',source_sha256:sourceHash,
   selection_sha256:validated.selection_sha256,
   attendance_fingerprint:blueprint.attendance_fingerprint,
   seed,reference_signal_strength:nullReference?0:scenario.signal_strength,
   total:validated.rows.length,eligible:validated.eligible.length,
   unavailable:validated.excluded.length,meetings:scenario.meetings,
   null_reference:nullReference,publication_eligible:false}};
}
function dependences(world,scenario){
 const eligible=world.frame.observations.filter(x=>x.source_status==='available');
 const counts=new Map(),familyMeeting=new Map(),familyAcross=new Set();
 for(const r of eligible){
   counts.set(r.meeting_id,(counts.get(r.meeting_id)||0)+1);
   if(r.source_family_id){
     if(familyMeeting.has(r.source_family_id)&&familyMeeting.get(r.source_family_id)!==r.meeting_id)
       familyAcross.add(r.source_family_id);
     familyMeeting.set(r.source_family_id,r.meeting_id);
   }
 }
 const duplicated=new Map(),aff=new Map();
 for(const r of eligible){
   duplicated.set(r.text_sha256,(duplicated.get(r.text_sha256)||0)+1);
   if(r.affiliation)aff.set(r.affiliation,(aff.get(r.affiliation)||0)+1);
 }
 const dominant=Math.max(...counts.values())/Math.max(1,eligible.length);
 const flags=[];
 if(familyAcross.size)flags.push('cross_meeting_original_source_family_closure');
 if(scenario.year_count===8&&scenario.meetings===8)
   flags.push('four_years_per_era_insufficient_for_year_cluster_asymptotics');
 if(scenario.year_rho!==0)flags.push('serial_year_dependence_present');
 if(dominant>0.35)flags.push('largest_source_group_concentration');
 if(scenario.nonrandom_attendance)flags.push('fixed_nonrandom_year_affiliation_attendance');
 return {
   source_group_count:counts.size,group_sizes:[...counts.values()].sort((a,b)=>a-b),
   largest_group_share:dominant,distinct_recorded_affiliations:aff.size,
   recurring_affiliations:[...aff.values()].filter(n=>n>1).length,
   duplicate_text_groups:[...duplicated.values()].filter(n=>n>1).length,
   cross_meeting_source_families:familyAcross.size,
   year_count:scenario.year_count,year_rho_oracle_parameter:scenario.year_rho,
   nonrandom_attendance:scenario.nonrandom_attendance,flags,
   group_refit_admissible:familyAcross.size===0,
   source_group_exchangeability_verified:false,
   few_year_inference_eligible:false,inferential_release_eligible:false
 };
}
module.exports={design,generate,dependences};
