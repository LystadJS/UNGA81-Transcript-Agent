/* Deterministic invented engineering workload. No national political claims. */
'use strict';
const crypto=require('node:crypto');
function fixture(){
 const snapshotId='synthetic-performance-193x2x11-v1',countries=['United States',...Array.from({length:192},(_,i)=>'Fictional country '+String(i+1).padStart(3,'0'))],files=new Map(),manifest={schema:'un.issue-history.manifest.v1',snapshot_id:snapshotId,selection_protocol:'policy-year-body-v1',versions:{ontology_version:['humanitarian-ontology-1'],extractor_version:['synthetic-perf-rules-1']},shards:[]};
 const add=(id,policy,year,data)=>{const content=Buffer.from(JSON.stringify({schema:'un.issue-history.shard.v1',snapshot_id:snapshotId,sources:[],observations:[],votes:[],memberships:[],roster:[],...data})),url=id+'.json';files.set('/'+url,content);manifest.shards.push({id,url,policy,year:String(year),body:'GA_C3',bytes:content.length,sha256:crypto.createHash('sha256').update(content).digest('hex')});};
 let observationCount=0,sourceCount=0;
 for(let year=2016;year<=2026;year++){
  const date=year===2016?'2016-11-01':year+'-06-01',context=year%2?'sudan':'israel_palestine',sources=countries.map((country,i)=>({id:'synthetic-source-'+year+'-'+i,revision:'r1',published_date:date,body:'GA_C3',family:'un_statement',countries:[country],url:'https://example.invalid/fixture/'+year+'/'+i}));sourceCount+=sources.length;
  for(const [pi,policy] of ['humanitarian_access','civilian_protection'].entries()){
   const observations=countries.map((country,i)=>({id:'synthetic-event-'+year+'-'+pi+'-'+i,source_id:sources[i].id,source_revision:'r1',country,date,policy,context,stance:i===0?'support':(i+year+pi)%13===0?'qualified':(i+year+pi)%5===0?'oppose':'support',attribution:'national',review_state:'assistant_provisional',ontology_version:'humanitarian-ontology-1',extractor_version:'synthetic-perf-rules-1',qualification_codes:(i+year+pi)%13===0?['subject_to_law']:[]}));observationCount+=observations.length;add(policy+'-'+year,policy,year,{sources,observations});
  }
  add('roster-'+year,'_roster',year,{roster:[{date,body:'GA_C3',family:'un_statement',countries,source_count:sources.length}]});
 }
 return {manifest,files,countries,observationCount,sourceCount,inputs:{start:'2026-06-01',end:'2026-10-23',as_of:'2026-10-23',topic:'Humanitarian access and civilian protection',bodies:['GA_C3'],exclusions:[]}};
}
module.exports={fixture};
