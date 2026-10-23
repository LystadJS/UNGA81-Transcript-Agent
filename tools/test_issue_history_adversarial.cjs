'use strict';
// Invented metadata only. These checks exercise the actual browser cache module.
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const H = require('../site/issue-history-client.js');
const source = {id:'s',revision:'r',body:'SC',countries:['Example','UnknownExample'],published_date:'2024-01-01'};
const observation = {id:'o',country:'Example',date:'2024-01-01',policy:'humanitarian_access',context:'sudan',stance:'support',attribution:'national',review_state:'assistant_provisional',source_id:'s',source_revision:'r'};
const shard = (extra={}) => ({schema:'un.issue-history.shard.v1',snapshot_id:'one',sources:[source],observations:[observation],votes:[],...extra});
function fixture(payloads, overrides={}) {
 const files=new Map();
 const shards=payloads.map((payload,i)=>{const bytes=Buffer.from(JSON.stringify(payload)),url=`${i}.json`;files.set(url,bytes);return {id:String(i),url,sha256:createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length};});
 const manifest={schema:'un.issue-history.manifest.v1',snapshot_id:'one',shards,...overrides};
 const raw=Buffer.from(JSON.stringify(manifest));
 const fetcher=async url=>{
  if(url.endsWith('/manifest.json'))return {ok:true,headers:{get:()=>String(raw.length)},json:async()=>manifest,text:async()=>raw.toString(),arrayBuffer:async()=>raw};
  const bytes=files.get(new URL(url).pathname.split('/').pop());
  return {ok:!!bytes,status:bytes?200:404,headers:{get:()=>bytes?String(bytes.length):null},arrayBuffer:async()=>bytes};
 };
 return {manifest,files,fetcher};
}
const url='https://example.invalid/manifest.json';
async function run(){
 const tests=[
  ['snapshot mismatch',async()=>{const f=fixture([shard({snapshot_id:'other'})]);await assert.rejects(new H.Client({cache:new H.MemoryCache(),fetcher:f.fetcher}).load(url));}],
  ['aggregate download bound',async()=>{const f=fixture([shard(),shard({observations:[{...observation,id:'o2'}]})]);const total=[...f.files.values()].reduce((n,b)=>n+b.length,0);await assert.rejects(new H.Client({cache:new H.MemoryCache(),fetcher:f.fetcher,maxBytes:total,maxTotalBytes:total-1}).load(url));}],
  ['declared manifest bound',async()=>{const f=fixture([shard()],{padding:'x'.repeat(2048)});await assert.rejects(new H.Client({cache:new H.MemoryCache(),fetcher:f.fetcher,maxManifestBytes:1024}).load(url));}],
  ['undeclared manifest bound',async()=>{const f=fixture([shard()],{padding:'x'.repeat(2048)}),wrapped=async(...args)=>{const response=await f.fetcher(...args);return args[0].endsWith('/manifest.json')?{...response,headers:{get:()=>null}}:response;};await assert.rejects(new H.Client({cache:new H.MemoryCache(),fetcher:wrapped,maxManifestBytes:1024}).load(url));}],
  ['corrupted cached reopen',async()=>{const f=fixture([shard()]),cache=new H.MemoryCache(),client=new H.Client({cache,fetcher:f.fetcher});await client.load(url);const saved=await cache.get('snapshot:one');saved.observations[0].stance='oppose';await cache.put('snapshot:one',saved);const recovered=await client.reopen('one');assert.equal(recovered.observations[0].stance,'support','reopen reconstructs from hash-verified shard rather than damaged flattened cache');}],
  ['deduplicate shared source references',async()=>{const f=fixture([shard(),shard({observations:[{...observation,id:'o2',policy:'civilian_protection'}]})]);const snapshot=await new H.Client({cache:new H.MemoryCache(),fetcher:f.fetcher}).load(url);assert.equal(snapshot.sources.length,1);assert.equal(snapshot.sources[0].countries.length,2);assert.equal(snapshot.observations.length,2);assert.equal(H.query(snapshot,{policies:['humanitarian_access']}).observations.length,1);}],
  ['failed load preserves previous valid snapshot',async()=>{const cache=new H.MemoryCache(),good=fixture([shard()]);await new H.Client({cache,fetcher:good.fetcher}).load(url);const bad=fixture([shard({snapshot_id:'wrong'})],{snapshot_id:'two'});await assert.rejects(new H.Client({cache,fetcher:bad.fetcher}).load(url));assert.equal(await cache.get('latest:'+url),'one');assert.equal((await cache.get('snapshot:one')).observations[0].stance,'support');}]
 ];
 const failed=[];
 for(const [name,test] of tests){try{await test();console.log('PASS '+name);}catch(error){failed.push(name);console.error('FAIL '+name+': '+error.message);}}
 if(failed.length)throw Error(failed.length+' adversarial cases failed: '+failed.join(', '));
 console.log('Issue history adversarial checks passed.');
}
run().catch(error=>{console.error(error.message);process.exitCode=1;});
