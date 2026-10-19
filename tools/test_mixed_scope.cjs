'use strict';
const assert=require('node:assert/strict'),S=require('../site/meeting-scopes.js'),A=require('../site/analysis-core.js'),C=require('../site/collector.js');
(async()=>{
 const included=[{slug:'ga/c1/81/11',title:'First Committee, 11th meeting'},{slug:'sc/10245',title:'Sudan - Security Council, 10245th meeting'},{slug:'asset/synthetic/climate',title:'(Part 1) Climate Action - Special Event, General Assembly, 81st session'}];
 const excluded=[{slug:'asset/synthetic/press',title:'Press briefing about the General Assembly, 81st session'},{slug:'asset/synthetic/stakeout',title:'Security Council media stakeout'},{slug:'asset/synthetic/other',title:'UNHCR Executive Committee'},{slug:'ga/c1/81/11',pageUrl:'/en/sc/10245',title:'Conflicting metadata'}];
 for(const m of included)assert.ok(S.matchesMeeting(m,'ga_sc'),m.title);
 for(const m of excluded)assert.ok(!S.matchesMeeting(m,'ga_sc'),m.title);
 assert.ok(S.covers('all','ga_sc'));assert.ok(S.covers('ga_sc','committee_1'));assert.ok(S.covers('ga_sc','general_debate'));assert.ok(!S.covers('committee_1','ga_sc'));assert.ok(!S.covers('ga_sc','all'));
 const meetings=[...included,...excluded.slice(0,3)].map(m=>({...m,date:'2026-10-16',pageUrl:'/en/'+m.slug,jsonUrl:'/en/'+m.slug+'.json',hasTranscript:true}));
 const requests=[];
 const corpus=await C.collect({start:'2026-10-16',end:'2026-10-16',scope:'ga_sc'},[],{request:async url=>{
  requests.push(url);if(url.includes('meetings.json'))return {hash:'f'.repeat(64),data:{page:1,total:meetings.length,hasMore:false,meetings}};
  const m=meetings.find(m=>url.endsWith(m.slug+'.json'));assert.ok(included.some(i=>i.slug===m.slug));
  return {hash:'f'.repeat(64),data:{video:{slug:m.slug,date:m.date},transcript:{language:'en',data:[{speaker:{affiliation:'Synthetic'},paragraphs:[{sentences:[{text:'Humanitarian assistance protects civilians '+m.slug}]}]}]}}};
 }});
 assert.equal(corpus.collection.selected_meetings,3);assert.equal(corpus.records.length,3);assert.equal(requests.length,4);
 const full={...corpus,collection:{...corpus.collection,scope:'all'},records:[...corpus.records,{...corpus.records[0],id:'asset/synthetic/extra#0',meeting_slug:'asset/synthetic/extra',source_url:'https://transcripts.un.org/en/asset/synthetic/extra',meeting:'Other UN event',text:'Other source'}]};
 const before=JSON.stringify(full);
 const result=await A.analyze(full,{start:'2026-10-16',end:'2026-10-16',scope:'ga_sc',topic:'',region:'All regions',methods:['frequency']});
 assert.equal(result.counts.matched,3);assert.equal(result.parameters.scope,'ga_sc');assert.equal(JSON.stringify(full),before);
 console.log('PASS GA+SC metadata scope, conflict and briefing exclusion, collection prefilter, saved narrowing and immutable originals');
})().catch(e=>{console.error(e);process.exitCode=1;});
