#!/usr/bin/env node
'use strict';
// Independent transport/accounting oracles; all network entry points throw.
const assert=require('node:assert/strict'),crypto=require('node:crypto');
let networkAttempts=0;
function blocked(){networkAttempts++;throw Error('Network forbidden in synthetic acceptance');}
for(const mod of ['node:http','node:https'])for(const key of ['request','get'])require(mod)[key]=blocked;
for(const key of ['connect','createConnection'])require('node:net')[key]=blocked;
for(const key of ['lookup','resolve'])require('node:dns')[key]=blocked;
global.fetch=blocked;
const R=require('./roster_adapter.cjs');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const checks=[];
async function test(name,fn){try{await fn();checks.push({name,status:'PASS'});}catch(e){checks.push({name,status:'FAIL',error:String(e.stack)});}}
function unsigned(r){const c=structuredClone(r);delete c.sha256;return c;}
async function fault(mutator){
  const s=R.makeScenario(),m=s.roster.meetings[0];
  const r=s.replies.get(m.endpoint)[0];mutator(r);
  s.replies.set(m.endpoint,[r]);
  const out=await R.collect(s.roster,new R.FixtureTransport(s.roster,s.replies));
  assert.equal(out.receipt.rows[0].status,'failed');assert.equal(out.receipt.rows.length,37);
  assert.equal(out.receipt.rows.filter(x=>x.status==='downloaded').length,33);
  assert(!out.corpus.parents.some(p=>p.meeting_id===m.meeting_id));
  return out;
}
async function main(){
  const s=R.makeScenario(),transport=new R.FixtureTransport(s.roster,s.replies),result=await R.collect(s.roster,transport);
  await test('37 exact ordered slots and frozen metadata digest',()=>{
    assert.equal(result.receipt.rows.length,37);
    assert.deepEqual(result.receipt.rows.map(r=>r.slot),Array.from({length:37},(_,i)=>i));
    assert.equal(s.roster.reserved_roster_sha256,'24aa39883fabc777ba4fb9e54b6792f1eda063c0fc6bc8fbe4bf453c50048671');
    assert.equal(new Set(s.roster.meetings.map(m=>m.reserved_slot_sha256)).size,37);
  });
  await test('exact available endpoint set; unavailable never requested',()=>{
    const expected=s.roster.meetings.filter(m=>m.available).map(m=>m.endpoint).sort();
    assert.deepEqual([...new Set(transport.calls.map(c=>c.url))].sort(),expected);
    assert(transport.calls.every(c=>c.url.startsWith('https://un-fixture.invalid/')));
    assert.equal(transport.calls.length,36);
  });
  await test('successful, failed and unavailable totals conserved',()=>{
    const totals=result.receipt.rows.reduce((a,r)=>(a[r.status]=(a[r.status]||0)+1,a),{});
    assert.deepEqual(totals,{downloaded:34,inventory_unavailable:2,failed:1});
    assert.equal(result.corpus.coverage.length,37);
  });
  await test('raw hashes and sentence/Unicode span reconstruction independent of parser',()=>{
    const sources=new Map(result.corpus.source_bundle.sources.map(s=>[s.meeting_id,s]));
    for(const p of result.corpus.parents){
      const source=sources.get(p.meeting_id),bytes=Buffer.from(source.raw_base64,'base64');
      assert.equal(hash(bytes),source.raw_sha256);
      const raw=JSON.parse(bytes),index=Number(p.id.split('#').at(-1));
      const expected=raw.transcript.data[index].paragraphs.flatMap(p=>p.sentences.map(s=>s.text)).join(' ');
      assert.equal(p.text,expected);assert.equal(hash(Buffer.from(expected)),p.text_sha256);
    }
    const parents=new Map(result.corpus.parents.map(p=>[p.id,p]));
    for(const p of result.corpus.passages){
      const parent=parents.get(p.parent_id);
      const start=p.parent_start??p.start,end=p.parent_end??p.end;
      assert.equal(p.text,Array.from(parent.text).slice(start,end).join(''));
    }
  });
  await test('repeat run is byte-identical without silent substitution',async()=>{
    const again=await R.collect(s.roster,new R.FixtureTransport(s.roster,s.replies));assert.deepEqual(again,result);
  });
  for(const [name,mutate] of [
    ['missing_slot',r=>r.meetings.pop()],['duplicate_slot',r=>r.meetings[1]=r.meetings[0]],
    ['reorder',r=>r.meetings.reverse()],['real_date',r=>r.meetings[0].date='2026-10-05'],
    ['real_endpoint',r=>r.meetings[0].endpoint='https://transcripts.un.org/en/forbidden.json'],
    ['encoded_traversal',r=>r.meetings[0].endpoint+='/%2e%2e'],['query_substitution',r=>r.meetings[0].endpoint+='?redirect=1'],
    ['slot_commitment',r=>r.meetings[0].reserved_slot_sha256='0'.repeat(64)],
    ['roster_commitment',r=>r.reserved_roster_sha256='0'.repeat(64)],['real_id',r=>r.meetings[0].meeting_id='ga/81/20']]){
    await test('reject roster '+name+' before any request',async()=>{
      const altered=unsigned(s.roster);mutate(altered);const t=new R.FixtureTransport(s.roster,s.replies);
      await assert.rejects(R.collect(R.seal(altered),t));assert.equal(t.calls.length,0);
    });
  }
  for(const [name,mutate] of [
    ['redirect',r=>{r.status=302;r.url='https://transcripts.un.org/';}],
    ['response_substitution',r=>{r.url+='other';}],['redirect_flag',r=>{r.redirected=true;}],
    ['bad_hash',r=>{r.bytes=Buffer.from('{}');}],['content_type',r=>{r.contentType='text/html';}],
    ['missing_body',r=>{delete r.bytes;}],['oversize',r=>{r.bytes=Buffer.alloc(R.MAX_BYTES+1);}],
    ['not_found',r=>{r.status=404;}],['timeout',r=>{r.error='timeout';}]]){
    await test('quarantine response '+name+' with full roster accounting',()=>fault(mutate));
  }
  for(const [name,mutate] of [
    ['wrong_identity',d=>d.video.slug='synthetic_fixture_/meeting_01'],['wrong_date',d=>d.video.date='2026-10-06'],
    ['timestamp_order',d=>d.transcript.data[0].end=-1],['flag_type',d=>d.transcript.timestamps_flagged='false'],
    ['malformed_sentence',d=>d.transcript.data[0].paragraphs[0].sentences[0].text={} ]]){
    await test('reject valid-hash invalid-schema '+name,async()=>{
      const q=R.makeScenario(),u=unsigned(q.roster),m=u.meetings[0],r=q.replies.get(m.endpoint)[0];
      const d=JSON.parse(r.bytes);mutate(d);r.bytes=Buffer.from(JSON.stringify(d));m.expected_sha256=hash(r.bytes);
      const roster=R.seal(u),out=await R.collect(roster,new R.FixtureTransport(roster,q.replies));
      assert.equal(out.receipt.rows[0].status,'failed');assert.equal(out.receipt.rows.length,37);
    });
  }
  await test('transient retries use exactly the original endpoint',async()=>{
    const q=R.makeScenario(),url=q.roster.meetings[0].endpoint,ok=q.replies.get(url)[0];
    q.replies.set(url,[{status:429},ok]);const t=new R.FixtureTransport(q.roster,q.replies);
    const out=await R.collect(q.roster,t);assert.equal(out.receipt.rows[0].status,'downloaded');
    assert.deepEqual(t.calls.filter(c=>c.slot===0).map(c=>c.attempt),[1,2]);
  });
  await test('arbitrary callback cannot replace offline transport',async()=>{await assert.rejects(R.collect(s.roster,{request:blocked}));});
  await test('overridden transport callback rejected',async()=>{
    const t=new R.FixtureTransport(s.roster,s.replies);t.request=blocked;
    await assert.rejects(R.collect(s.roster,t));
  });
  await test('used transport cannot replay hidden request state',async()=>{
    const t=new R.FixtureTransport(s.roster,s.replies);await t.request(s.roster.meetings[0].endpoint,1);
    await assert.rejects(R.collect(s.roster,t));assert.equal(t.calls.length,1);
  });
  await test('duplicate retry index rejected',async()=>{
    const t=new R.FixtureTransport(s.roster,s.replies);await t.request(s.roster.meetings[0].endpoint,1);
    await assert.rejects(t.request(s.roster.meetings[0].endpoint,1));assert.equal(t.calls.length,1);
  });
  await test('no network or reserved-content calls',()=>assert.equal(networkAttempts,0));
  const report={schema:'un.roster-independent-tests.v1',passed:checks.filter(c=>c.status==='PASS').length,
    failed:checks.filter(c=>c.status==='FAIL').length,network_attempts:networkAttempts,checks};
  console.log(JSON.stringify(report,null,2));if(report.failed)process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
