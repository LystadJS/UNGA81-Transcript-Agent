#!/usr/bin/env node
'use strict';
/** Offline adapter acceptance. No HTTP client or real-roster execution mode. */
const C=require('../corpus/contract.cjs');
const F=require('./synthetic_un_fixture.cjs');
const assert=C.assert;
const ORIGIN='https://un-fixture.invalid';
const MAX_BYTES=2*1024*1024;
const schema='un.synthetic-roster.v1';
const registry=()=>Array.from({length:26},(_,i)=>({country:`SIM-COUNTRY-${String(i).padStart(2,'0')}`,region:'Synthetic region',aliases:[]}));
function seal(x){return C.seal(x);}
function commitment(){
  const fs=require('node:fs'),path=require('node:path');
  const frame=JSON.parse(fs.readFileSync(path.join(__dirname,'../corpus/frame.json'),'utf8'));
  const lock=JSON.parse(fs.readFileSync(path.join(__dirname,'evaluation-lock.json'),'utf8'));
  C.validateFrame(frame);C.verify(lock,'un.heldout-evaluation-lock.v1');
  const roster=frame.meetings.filter(m=>m.split==='holdout').map(m=>[m.meeting_id,m.date]).sort();
  const digest=C.sha(C.stable(roster));
  assert(roster.length===37&&digest===lock.reserved_identifiers_sha256&&frame.sha256===lock.frame_sha256,'Frozen metadata commitment changed');
  assert(lock.sha256==='2c96f479fae0eded4b226882e05462b7f800c32fa066a6bb26df043b5d278039'&&!lock.evaluation_executed,'Frozen evaluation lock changed');
  return {digest,slots:roster.map(r=>C.sha(C.stable(r)))};
}
function expectedURL(id){return `${ORIGIN}/en/${id}.json`;}
function makeScenario(){
  const replies=new Map(),binding=commitment();
  const meetings=Array.from({length:37},(_,i)=>{
    const m=F.meeting(i),bytes=Buffer.from(JSON.stringify(F.response(i)),'utf8');
    const url=expectedURL(m.slug);
    replies.set(url,i===34?[{status:503},{status:503}]:[{status:200,url,contentType:'application/json',bytes}]);
    return {slot:i,reserved_slot_sha256:binding.slots[i],meeting_id:m.slug,date:F.FAKE_DATE,available:m.hasTranscript,genre:m.category,title:m.title,
      endpoint:url,expected_sha256:C.sha(bytes)};
  });
  return {roster:seal({schema,synthetic:true,reserved_roster_sha256:binding.digest,meetings}),replies};
}
function validateRoster(r){
  C.verify(r,schema);
  assert(r.synthetic===true&&Object.keys(r).sort().join('|')==='meetings|reserved_roster_sha256|schema|sha256|synthetic','Synthetic roster fields only');
  assert(Array.isArray(r.meetings)&&r.meetings.length===37,'Exactly 37 synthetic slots required');
  const ids=new Set(),binding=commitment();
  assert(r.reserved_roster_sha256===binding.digest,'Reserved metadata digest mismatch');
  for(let i=0;i<37;i++){
    const m=r.meetings[i];
    assert(Object.keys(m).sort().join('|')==='available|date|endpoint|expected_sha256|genre|meeting_id|reserved_slot_sha256|slot|title','Unexpected roster fields');
    assert(m.slot===i&&m.meeting_id===F.meeting(i).slug&&!ids.has(m.meeting_id),'Roster identity/order differs');
    assert(m.reserved_slot_sha256===binding.slots[i],'Wrong reserved metadata slot');
    assert(m.date===F.FAKE_DATE&&typeof m.available==='boolean','Only fictitious date/availability accepted');
    assert(m.endpoint===expectedURL(m.meeting_id),'Noncanonical or real endpoint rejected');
    assert(/^[a-f0-9]{64}$/.test(m.expected_sha256),'Missing fixture response digest');
    assert(typeof m.genre==='string'&&typeof m.title==='string','Missing source metadata');
    ids.add(m.meeting_id);
  }
  return r;
}
class FixtureTransport{
  #roster; #replies; #calls=[];
  constructor(roster,replies){
    validateRoster(roster);assert(replies instanceof Map,'Fixture response map required');
    this.#roster=structuredClone(roster);this.#replies=new Map();
    const allowed=new Set(roster.meetings.map(m=>m.endpoint));
    for(const [url,rows] of replies){
      assert(allowed.has(url)&&Array.isArray(rows)&&rows.length>0&&rows.length<=2,'Unlisted fixture endpoint or retry series');
      this.#replies.set(url,rows.map(r=>({...r,...(r.bytes?{bytes:Buffer.from(r.bytes)}:{})})));
    }
  }
  get calls(){return this.#calls.map(x=>({...x}));}
  get rosterDigest(){return this.#roster.sha256;}
  async request(url,attempt){
    const m=this.#roster.meetings.find(x=>x.endpoint===url);
    assert(m?.available&&attempt>=1&&attempt<=2&&attempt===this.#calls.filter(c=>c.url===url).length+1,'Out-of-roster request or retry sequence refused');
    this.#calls.push({slot:m.slot,url,attempt});
    const rs=this.#replies.get(url);if(!rs)throw Error('fixture_missing');
    const r=rs[Math.min(attempt-1,rs.length-1)];
    if(r.error)throw Error(r.error==='timeout'?'timeout':'fixture_error');
    return {...r,bytes:r.bytes?Buffer.from(r.bytes):undefined};
  }
}
function validBody(r,m){
  assert(r.url===m.endpoint&&!r.redirected,'Redirect or response URL mismatch');
  assert(r.contentType==='application/json','Unexpected content type');
  assert(Buffer.isBuffer(r.bytes)&&r.bytes.length>0&&r.bytes.length<=MAX_BYTES,'Missing/oversize body');
  assert(C.sha(r.bytes)===m.expected_sha256,'Response SHA256 mismatch');
  const doc=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(r.bytes));
  assert(doc.video?.slug===m.meeting_id&&doc.video?.date===m.date,'Response identity/date mismatch');
  assert(Array.isArray(doc.transcript?.data)&&['en','fr'].includes(doc.transcript.language),'Malformed transcript/language');
  assert(typeof doc.transcript.timestamps_flagged==='boolean','Timestamp flag must be explicit boolean');
  let prior=-Infinity;
  for(const s of doc.transcript.data){
    assert(Number.isFinite(s.start)&&Number.isFinite(s.end)&&s.start>=0&&s.end>=s.start&&s.start>=prior,'Invalid source timestamps');
    prior=s.start;
    assert(Array.isArray(s.paragraphs),'Malformed paragraph array');
    for(const p of s.paragraphs){assert(Array.isArray(p.sentences),'Malformed sentences');for(const t of p.sentences)assert(typeof t.text==='string','Non-string sentence');}
  }
  return r.bytes;
}
function parserFrame(roster){
  // This is only a schema bridge to the historical parser's fixed UN-origin check.
  // No generated UN-origin URL is ever passed to the transport.
  const historical=F.generate().corpus.frame;
  return seal({...Object.fromEntries(Object.entries(historical).filter(([k])=>k!=='sha256')),meetings:historical.meetings.map(m=>{
    const row=roster.meetings.find(r=>r.meeting_id===m.meeting_id);
    return row?{...m,has_transcript:row.available,genre:row.genre,title:row.title,
      json_url:row.available?`https://transcripts.un.org/en/${m.meeting_id}.json`:null}:m;
  })});
}
async function collect(roster,transport){
  validateRoster(roster);
  assert(transport instanceof FixtureTransport&&Object.getPrototypeOf(transport)===FixtureTransport.prototype&&transport.request===FixtureTransport.prototype.request&&transport.rosterDigest===roster.sha256&&transport.calls.length===0,'Transport/roster lock mismatch or transport reused');
  const rows=[],sources=[];
  for(const m of roster.meetings){
    const record={slot:m.slot,meeting_id:m.meeting_id,date:m.date,status:'inventory_unavailable',attempts:[],raw_sha256:null};
    if(!m.available){rows.push(record);sources.push({meeting_id:m.meeting_id,status:'inventory_unavailable'});continue;}
    record.status='failed';let bytes=null;
    for(let attempt=1;attempt<=2;attempt++){
      try{
        const r=await transport.request(m.endpoint,attempt);
        record.attempts.push({attempt,http_status:r.status??null,received_sha256:r.bytes?C.sha(r.bytes):null});
        if([429,503].includes(r.status)){record.error='retryable_http_exhausted';continue;}
        assert(r.status===200,'HTTP status not successful');
        bytes=validBody(r,m);record.status='downloaded';record.raw_sha256=C.sha(bytes);delete record.error;break;
      }catch(e){
        if(!record.attempts.some(r=>r.attempt===attempt))record.attempts.push({attempt,http_status:null,received_sha256:null});
        record.error=String(e.message);if(e.message!=='timeout')break;
      }
    }
    rows.push(record);
    sources.push(bytes?{meeting_id:m.meeting_id,status:'downloaded',raw_base64:bytes.toString('base64'),raw_sha256:record.raw_sha256}:
      {meeting_id:m.meeting_id,status:'failed',error:record.error||'no_valid_response'});
  }
  const frame=parserFrame(roster),bundle=C.makeBundle(frame,sources,registry()),corpus=C.build(frame,bundle);
  const receipt=seal({schema:'un.synthetic-roster-collection.v1',synthetic:true,roster_sha256:roster.sha256,
    source_bundle_sha256:bundle.sha256,corpus_sha256:corpus.sha256,rows,requests:transport.calls,
    network_client_present:false,real_reserved_content_accessed:false});
  return {roster,receipt,corpus};
}
async function main(){
  const fs=require('node:fs'),path=require('node:path');
  assert(process.argv.length===3,'Usage: roster_adapter.cjs NEW_OUTPUT_DIRECTORY');
  const out=path.resolve(process.argv[2]);assert(!fs.existsSync(out),'Output already exists');
  const s=makeScenario(),r=await collect(s.roster,new FixtureTransport(s.roster,s.replies));
  fs.mkdirSync(out,{recursive:true});
  for(const [key,value] of Object.entries(r))fs.writeFileSync(path.join(out,key+'.json'),JSON.stringify(value,null,2)+'\n');
  console.log(JSON.stringify({synthetic:true,slots:r.receipt.rows.length,requests:r.receipt.requests.length,real_requests:0}));
}
module.exports={commitment,makeScenario,validateRoster,FixtureTransport,collect,expectedURL,seal,MAX_BYTES};
if(require.main===module)main().catch(e=>{console.error(e.stack);process.exitCode=1;});
