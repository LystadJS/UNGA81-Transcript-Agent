'use strict';
const assert=require('node:assert/strict'),C=require('../site/collector.js');
const date='2026-09-24',hash='a'.repeat(64),p={start:date,end:date,scope:'all'};
const meetings=['one','two','three'].map(name=>({slug:'asset/synthetic/'+name,title:name,date,pageUrl:'/en/asset/synthetic/'+name,jsonUrl:'/en/asset/synthetic/'+name+'.json',hasTranscript:true}));
const inventory={hash,data:{page:1,total:meetings.length,hasMore:false,meetings}};
const transcript=meeting=>({hash,data:{video:{slug:meeting.slug,date},transcript:{language:'en',data:[{paragraphs:[{sentences:[{text:'Synthetic recovery fixture '+meeting.title}]}]}]}}});
(async()=>{
 let fail=true;const fetched=[];
 const request=async url=>{if(url.includes('meetings.json'))return inventory;const m=meetings.find(m=>url.endsWith(m.jsonUrl));fetched.push(m.slug);if(fail&&m===meetings[1])throw Error('Synthetic network outage');return transcript(m);};
 const initial=await C.collect(p,[],{request});assert.equal(initial.records.length,2);assert.equal(initial.coverage[1].status,'failed');
 fail=false;fetched.length=0;const resumed=await C.collect(p,[],{request,resume:initial});
 assert.deepEqual(fetched,[meetings[1].slug]);assert.equal(resumed.records.length,3);assert.equal(new Set(resumed.records.map(r=>r.id)).size,3);assert.equal(resumed.collection.collected_meetings,3);assert.deepEqual(resumed.records.find(r=>r.meeting_slug===meetings[0].slug),initial.records[0]);
 const extra={...meetings[0],slug:'asset/synthetic/unselected',jsonUrl:'/en/asset/synthetic/unselected.json'};
 fetched.length=0;
 await C.collect(p,[],{resume:resumed,request:async url=>url.includes('meetings.json')?{hash,data:{page:1,total:4,hasMore:false,meetings:[...meetings,extra]}}:request(url)});
 assert.deepEqual(fetched,[],'Retry must not add newly listed transcript sources');
 let snapshots=[];const controller=new AbortController();
 await assert.rejects(()=>C.collect(p,[],{request,signal:controller.signal,checkpoint:value=>{snapshots.push(value);if(value.records.length===1)controller.abort();}}),e=>e.name==='AbortError');
 assert.equal(snapshots.at(-1).records.length,1);assert.equal(snapshots[0].records.length,1);
 const cancelledResume=await C.collect(p,[],{request,resume:snapshots.at(-1)});assert.equal(cancelledResume.records.length,3);
 let requests=0;await assert.rejects(()=>C.collect({...p,end:'2026-09-25'},[],{resume:initial,request:async()=>{requests++;}}),/original collection/);assert.equal(requests,0);
 // Failure part way through a retry must not discard a completed response later in inventory order.
 const interrupted=new AbortController();let saved;
 await assert.rejects(()=>C.collect(p,[],{resume:initial,request:async url=>{if(url.endsWith(meetings[1].jsonUrl)){interrupted.abort();throw new DOMException('Cancelled','AbortError');}return request(url);},signal:interrupted.signal,checkpoint:value=>{saved=value;}}),e=>e.name==='AbortError');
 assert.equal(saved.records.length,2);assert.ok(saved.records.some(r=>r.meeting_slug===meetings[2].slug));
 console.log(JSON.stringify({status:'PASS',synthetic_only:true,checks:['retry downloads failed source only','completed bytes and identities preserved','cancelled collection has exportable checkpoint','resume fills unfinished meetings','changed selection refused before network','interrupted retry retains later successes']}));
})().catch(e=>{console.error(e);process.exitCode=1;});
