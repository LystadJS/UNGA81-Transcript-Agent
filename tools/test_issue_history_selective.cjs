'use strict';
const assert=require('node:assert/strict'),{createHash}=require('node:crypto'),H=require('../site/issue-history-client');
async function run(){
 const files=new Map(),refs=[],snapshot_id='selective_fixture';
 const add=(id,policy,year,body,extra={})=>{const value={schema:'un.issue-history.shard.v1',snapshot_id,observations:[],sources:[],votes:[],roster:[],...extra},bytes=Buffer.from(JSON.stringify(value));files.set(id+'.json',bytes);const ref={id,url:id+'.json',sha256:createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length,policy,year,body};refs.push(ref);return ref;};
 const observation=(id,date,body,policy='access')=>({observations:[{id,country:'Kenya',date,policy,context:'sudan',source_id:id,source_revision:'r1'}],sources:[{id,revision:'r1',published_date:date,body}]});
 add('access2018','access','2018','GA_C3',observation('a','2018-01-01','GA_C3'));
 add('roster2018','_roster','2018','GA_C3',{roster:[{date:'2018-01-01',body:'GA_C3',family:'un_statement',countries:['Kenya','Ghana','United States'],source_count:2}]});
 add('access2020','access','2020','GA_C3',observation('b','2020-12-31','GA_C3'));
 add('roster2020','_roster','2020','GA_C3',{roster:[{date:'2020-12-31',body:'GA_C3',family:'un_statement',countries:['Malta'],source_count:1}]});
 add('eligibility','_eligibility','all','GA_C3',{memberships:[{country:'Kenya',start:'2010-01-01',end:'2030-01-01',body:'GA_C3'}]});
 add('coverage','_coverage','2018','GA_C3',{sources:[{id:'coverage',revision:'r1',published_date:'2018-01-01',body:'GA_C3'}]});
 add('otherpolicy','protection','2018','GA_C3',observation('p','2018-01-01','GA_C3','protection'));
 add('old','access','2017','GA_C3',observation('old','2017-12-31','GA_C3'));
 add('sc','access','2018','SC',observation('sc','2018-01-01','SC'));
 add('legacy',undefined,undefined,undefined,{sources:[{id:'legacy',revision:'r1'}]});
 refs.push({id:'huge',url:'huge.json',sha256:'a'.repeat(64),bytes:80000000,policy:'unrelated','year':'2018',body:'GA_C3'});
 let manifest={schema:'un.issue-history.manifest.v1',snapshot_id,selection_protocol:'policy-year-body-v1',shards:refs},requests=[];
 const fetcher=async url=>{requests.push(url);if(url.endsWith('manifest.json'))return {ok:true,json:async()=>manifest};const data=files.get(url.split('/').at(-1));assert.ok(data,'unexpected shard fetch '+url);return {ok:true,headers:{get:()=>null},arrayBuffer:async()=>data};};
 const cache=new H.MemoryCache(),client=new H.Client({cache,fetcher}),selection={start:'2018-06-15',end:'2020-05-15',policies:['access'],bodies:['GA']};
 const a=await client.load('https://example.org/manifest.json',{selection});
 assert.deepEqual(a.selected_shards.map(s=>s.id),['access2018','roster2018','access2020','roster2020','eligibility','legacy']);
 assert.equal(a.manifest.shards.length,refs.length,'full authoritative manifest retained');assert.equal(a.roster.length,2);assert.ok(a.roster[0].countries.includes('Ghana'),'unknown countries retained independently from policy');assert.equal(a.memberships.length,1);assert.equal(a.observations.length,2,'partial endpoint years loaded intact');assert.equal(H.query(a,{...selection,start:selection.start,end:selection.end}).observations.length,0,'exact dates applied after retrieval');assert.ok(!requests.some(u=>u.endsWith('huge.json')),'unrelated >60MB shard neither fetched nor charged');assert.ok(a.cache_identity.includes('::selection:'));
 assert.deepEqual(await client.reopen(a.cache_identity),a);await assert.rejects(client.reopen(snapshot_id),/unavailable/,'subset must not masquerade as a complete global snapshot');
 const same=await client.load('https://example.org/manifest.json',{selection:{...selection,bodies:['GA','GA'],policies:['access','access']}});assert.equal(same.cache_identity,a.cache_identity);
 const b=await client.load('https://example.org/manifest.json',{selection:{...selection,policies:['protection']}});assert.notEqual(a.cache_identity,b.cache_identity);assert.ok(b.observations.some(o=>o.policy==='protection'));assert.deepEqual(await client.reopen(a.cache_identity),a,'another subset cannot overwrite prior selection');
 const original=await cache.get('snapshot:'+a.cache_identity);await cache.put('snapshot:'+a.cache_identity,{...original,selection:{...selection,bodies:['SC']}});await assert.rejects(client.reopen(a.cache_identity),/selection identity/);await cache.put('snapshot:'+a.cache_identity,original);
 await cache.put('shard:'+a.selected_shards[0].sha256,new Uint8Array([1,2]));await assert.rejects(client.reopen(a.cache_identity),/integrity/);const restored=await client.load('https://example.org/manifest.json',{selection});assert.deepEqual(restored,a);
 const abort=new AbortController();abort.abort();await assert.rejects(client.load('https://example.org/manifest.json',{selection,signal:abort.signal}),/cancelled/);
 await assert.rejects(client.load('https://example.org/manifest.json',{selection:{...selection,start:'2018-02-30'}}),/selection dates/);
 // Unknown protocols and dimensionless legacy manifests must load everything.
 manifest={...manifest,selection_protocol:'future-protocol',shards:refs.filter(r=>r.id!=='huge')};const legacy=await client.load('https://example.org/manifest.json',{selection});assert.equal(legacy.observations.length,5);assert.equal(legacy.cache_identity,undefined);assert.deepEqual(await client.reopen(snapshot_id),legacy);
 // A selected ref claiming a different partition must fail, even with correct bytes/hash.
 manifest={...manifest,selection_protocol:'policy-year-body-v1',shards:[{...refs[0],year:'2019'}]};await assert.rejects(client.load('https://example.org/manifest.json',{selection}),/dimension mismatch/);
 manifest={...manifest,shards:[refs.find(r=>r.id==='huge')]};await assert.rejects(client.load('https://example.org/manifest.json',{selection:{...selection,policies:['unrelated']}}),/total byte limit/);
 console.log('PASS selective policy/year/body retrieval, independent unknown roster, GA committee hierarchy, endpoint years, selected byte budgets, legacy fallback, immutable subset identities, integrity/replay and cancellation');
}
module.exports=run;if(require.main===module)run().catch(e=>{console.error(e);process.exitCode=1;});
