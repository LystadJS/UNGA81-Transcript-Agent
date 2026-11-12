'use strict';
const Collector=require('../site/collector.js');
const countries=[{country:'Kenya',iso3:'KEN',aliases:'Kenya',region:'Africa'},{country:'United States',iso3:'USA',aliases:'United States of America',region:'Americas'}];
const date='2026-11-10';
const meetings=[{slug:'ga/81/900',title:'Synthetic development discussion',date,hasTranscript:true,pageUrl:'/en/ga/81/900',jsonUrl:'/en/ga/81/900.json'},{slug:'sc/10900',title:'Synthetic humanitarian discussion',date,hasTranscript:true,pageUrl:'/en/sc/10900',jsonUrl:'/en/sc/10900.json'}];
const passage=(affiliation,text,group=null)=>({speaker:{affiliation,affiliation_full:affiliation,function:'Representative',group,name:affiliation+' delegate',id:affiliation},paragraphs:[{sentences:[{text}]}]});
const transcript=m=>({video:{slug:m.slug,date:m.date},transcript:{language:'en',data:[
  passage('Kenya','We support sustainable development financing for schools and hospitals, with transparent implementation and safeguards for local communities.'),
  passage('United States','We support sustainable development financing for schools and hospitals, with transparent implementation and safeguards for local communities.'),
  passage('Kenya','We speak on behalf of the Example Group. We support humanitarian access for civilians and urge protection for relief workers.','Example Group'),
  passage('Kenya','Literal <img src=x onerror=alert(1)> evidence 😀 includes humanitarian access, but does not establish an expressed position.')
]}});
async function request(url){
  const u=new URL(url),data=u.pathname.endsWith('meetings.json')?{meetings,total:meetings.length,page:1,hasMore:false}:transcript(meetings.find(m=>'/en/'+m.slug+'.json'===u.pathname));
  const raw=JSON.stringify(data);return {data,raw,hash:await Collector.sha(raw),retrieved_at:'2026-11-12T20:00:00Z'};
}
async function corpus(index=0){const m=meetings[index];return Collector.collect({start:date,end:date,scope:'all',meeting_slug:m.slug,meeting_date:date},countries,{request});}
module.exports={countries,date,meetings,transcript,corpus};
