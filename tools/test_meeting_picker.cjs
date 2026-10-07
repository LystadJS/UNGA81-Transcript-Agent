'use strict';
const assert=require('node:assert/strict'),P=require('../site/meeting-picker-core.js'),C=require('../site/collector.js'),A=require('../site/analysis-core.js');
const date='2026-09-24',hash='a'.repeat(64);
const meetings=[
  {slug:'asset/test/first',title:'First Committee — same day',date,pageUrl:'/en/asset/test/first',jsonUrl:'/en/asset/test/first.json',hasTranscript:true},
  {slug:'asset/test/second',title:'Second Committee — same day',date,pageUrl:'/en/asset/test/second',jsonUrl:'/en/asset/test/second.json',hasTranscript:true},
  {slug:'asset/test/pending',title:'Meeting with pending transcript',date,pageUrl:'/en/asset/test/pending',hasTranscript:false}
];
const transcript=slug=>({video:{slug,date},transcript:{language:'en',data:[{speaker:{affiliation:'TEST'},paragraphs:[{sentences:[{text:'Climate finance and security policy evidence.'}]}],pageUrl:'/en/'+slug}]}});
(async()=>{
 const passed=[];async function check(name,fn){await fn();passed.push(name);console.log('PASS '+name);}
 const calls=[];
 const request=async url=>{calls.push(url);const u=new URL(url);if(u.pathname==='/en/meetings.json'){const page=Number(u.searchParams.get('page'));return {hash,data:{page,total:3,hasMore:page===1,meetings:page===1?[meetings[0]]:meetings.slice(1)}};}return {hash,data:transcript(u.pathname.includes('second')?meetings[1].slug:meetings[0].slug)};};
 const list=await P.list(date,{request});
 await check('list all paginated meetings without fetching transcripts',async()=>{assert.equal(list.total,3);assert.equal(list.pages.length,2);assert.equal(calls.length,2);assert.ok(calls.every(url=>url.includes('/meetings.json?')));assert.equal(list.meetings[2].hasTranscript,false);});
 const p={...P.selection(date,list.meetings[1]),topic:'',region:'All regions',methods:['frequency','tfidf']};
 calls.length=0;const corpus=await C.collect(p,[],{request});
 await check('only selected second-page meeting downloaded',async()=>{const transcripts=calls.filter(url=>!url.includes('meetings.json'));assert.deepEqual(transcripts,['https://transcripts.un.org/en/asset/test/second.json']);assert.equal(corpus.collection.selected_meetings,1);assert.equal(corpus.collection.selected_meeting_slug,meetings[1].slug);assert.equal(corpus.coverage.length,1);assert.ok(corpus.records.every(r=>r.meeting_slug===meetings[1].slug));});
 await check('analysis and denominator limited to the selected identity',async()=>{const other={...corpus.records[0],id:meetings[0].slug+'#0',meeting_slug:meetings[0].slug};const report=await A.analyze({...corpus,records:[other,...corpus.records]},p);assert.equal(report.counts.eligible_before_dedup,1);assert.equal(report.counts.matched,1);assert.equal(report.matched[0].id,meetings[1].slug+'#0');assert.equal(report.parameters.meeting_slug,meetings[1].slug);});
 await check('pending transcript selection is refused',async()=>{assert.throws(()=>P.selection(date,list.meetings[2]),/not yet/);});
 await check('invalid dates and meeting IDs rejected before network',async()=>{let requests=0;await assert.rejects(()=>P.list('2026-02-30',{request:async()=>{requests++;}}),/valid/);assert.equal(requests,0);assert.throws(()=>A.parameters({...p,meeting_slug:'../wrong'}),/Individual meeting/);await assert.rejects(()=>C.collect({...p,end:'2026-09-25'},[],{request}),/one meeting/);});
 await check('missing selection does not substitute another meeting',async()=>{let downloaded=0;await assert.rejects(()=>C.collect(p,[],{request:async url=>{if(!url.includes('meetings.json'))downloaded++;return {hash,data:{page:1,total:1,hasMore:false,meetings:[meetings[0]]}};}}),/no other meeting/);assert.equal(downloaded,0);});
 await check('inventory failure is not a zero-meeting list',async()=>{await assert.rejects(()=>P.list(date,{request:async()=>{throw Error('service unavailable');}}),/service unavailable/);await assert.rejects(()=>C.collect(p,[],{request:async()=>{throw Error('service unavailable');}}),/complete inventory/);});
 await check('wrong date, duplicate IDs and inconsistent totals rejected',async()=>{for(const data of [{page:1,total:2,hasMore:false,meetings:[meetings[0],meetings[0]]},{page:1,total:1,hasMore:false,meetings:[{...meetings[0],date:'2026-09-25'}]},{page:1,total:4,hasMore:false,meetings}])await assert.rejects(()=>P.list(date,{request:async()=>({hash,data})}));});
 await check('external source endpoints rejected',async()=>{await assert.rejects(()=>P.list(date,{request:async()=>({hash,data:{page:1,total:1,hasMore:false,meetings:[{...meetings[0],jsonUrl:'https://example.invalid/data'}]}})}),/Unexpected transcript host/);});
 await check('single-meeting non-English and empty transcripts keep coverage',async()=>{for(const mode of ['language','empty']){const r=await C.collect(p,[],{request:async url=>{if(url.includes('meetings.json'))return {hash,data:{page:1,total:1,hasMore:false,meetings:[meetings[1]]}};const data=transcript(meetings[1].slug);if(mode==='language')data.transcript.language='fr';else data.transcript.data=[];return {hash,data};}});assert.equal(r.records.length,0);assert.equal(r.coverage[0].status,mode==='language'?'excluded_language':'empty_transcript');}});
 await check('cancelled inventory publishes no partial list',async()=>{const c=new AbortController();c.abort();await assert.rejects(()=>P.list(date,{signal:c.signal,request}),e=>e.name==='AbortError');});
 await check('canonical non-asset HRC and treaty-body meeting routes are supported',async()=>{
  for(const slug of ['hrc/63/25','ced/593','ga/81/1']){
   const m={...meetings[0],slug,pageUrl:'/en/'+slug,jsonUrl:'/en/'+slug+'.json'};
   const inventory=await P.list(date,{request:async()=>({hash,data:{page:1,total:1,hasMore:false,meetings:[m]}})});
   const params={...P.selection(date,inventory.meetings[0]),topic:'',region:'All regions',methods:['frequency']};
   const collected=await C.collect(params,[],{request:async url=>url.includes('meetings.json')?{hash,data:{page:1,total:1,hasMore:false,meetings:[m]}}:{hash,data:transcript(slug)}});
   assert.equal(collected.records[0].meeting_slug,slug);assert.equal((await A.analyze(collected,params)).counts.matched,1);
  }
  for(const slug of ['../hrc/63','hrc//25','/hrc/63/25','hrc/63/25?x=1','https://example.test/hrc','hrc/%2e%2e/25'])assert.equal(P.validSlug(slug),false,slug);
 });
 console.log(JSON.stringify({status:'PASS',synthetic_only:true,checks:passed.length,passed,node:process.version}));
})().catch(e=>{console.error(e);process.exitCode=1;});
