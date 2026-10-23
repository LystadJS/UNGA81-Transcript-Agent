'use strict';
const assert=require('node:assert/strict'),{createHash}=require('node:crypto');
const H=require('../site/issue-history-client');
async function run(){
 const shard={schema:'un.issue-history.shard.v1',snapshot_id:'one',sources:[{id:'s',revision:'r',body:'SC'}],observations:[{country:'A',date:'2020-01-01',policy:'access',context:'Sudan',source_id:'s',source_revision:'r'}],votes:[]},bytes=Buffer.from(JSON.stringify(shard)),sha256=createHash('sha256').update(bytes).digest('hex');
 const manifest={schema:'un.issue-history.manifest.v1',snapshot_id:'one',shards:[{id:'one',url:'one.json',sha256}]},cache=new H.MemoryCache();let downloads=0;
 const fetcher=async url=>url.endsWith('manifest.json')?{ok:true,json:async()=>manifest}:{ok:true,headers:{get:()=>null},arrayBuffer:async()=>{downloads++;return bytes;}};
 const client=new H.Client({cache,fetcher});const snapshot=await client.load('https://example.org/manifest.json');
 assert.equal(H.query(snapshot,{bodies:['SC'],start:'2019-01-01',end:'2021-01-01'}).observations.length,1);
 assert.equal(H.query(snapshot,{bodies:['GA']}).observations.length,0);assert.equal(H.query(snapshot,{as_of:'2019-01-01'}).observations.length,0);
 await client.load('https://example.org/manifest.json');assert.equal(downloads,1,'hash cache avoids recomputing unchanged downloads');
 await cache.put('shard:'+sha256,new Uint8Array([1,2]));await client.load('https://example.org/manifest.json');assert.equal(downloads,2,'damaged cache refetched');
 assert.deepEqual(await client.reopen('one'),snapshot);
 const spec={snapshot_id:'one',ontology_version:'1',extractor_version:'1',model_version:'1',estimand:'explicit',policy:'access',context:'Sudan',start:'2020-01-01',end:'2020-02-01',as_of:'2020-02-01',scope:'SC',parameters:{b:2,a:1}};
 assert.equal(H.cacheKey(spec),H.cacheKey({...spec,parameters:{a:1,b:2}}));assert.notEqual(H.cacheKey(spec),H.cacheKey({...spec,snapshot_id:'two'}));assert.throws(()=>H.cacheKey({}),/Incomplete/);
 const report=H.freezeReport({inputs:spec,snapshot_id:'one',versions:{schema:1},evidence:snapshot,results:{model:'observed'},exclusions:['unresolved']});assert.deepEqual(H.reopenReport(JSON.parse(JSON.stringify(report))),report);
 const badClient=new H.Client({cache:new H.MemoryCache(),fetcher:async url=>url.endsWith('manifest.json')?{ok:true,json:async()=>manifest}:{ok:true,headers:{get:()=>null},arrayBuffer:async()=>Buffer.from('bad')}});
 await assert.rejects(badClient.load('https://example.org/manifest.json'),/integrity/);await assert.rejects(badClient.reopen('one'),/unavailable/);
 const cancelled=new AbortController();cancelled.abort();await assert.rejects(client.load('https://example.org/manifest.json',{signal:cancelled.signal}),/cancelled/);
 const cross={...manifest,snapshot_id:'other',shards:[{...manifest.shards[0],url:'https://other.org/a',sha256:'0'.repeat(64)}]};await assert.rejects(new H.Client({cache:new H.MemoryCache(),fetcher:async()=>({ok:true,json:async()=>cross})}).load('https://example.org/manifest.json'),/origin/);
 console.log('Issue history client: integrity, cache recovery, query scopes, cancellation and reproducible reports passed.');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
