const assert=require('node:assert/strict'),C=require('../site/passage-pilot-core.js'),R=require('../site/reviewed-units.js'),A=require('../site/analysis-core.js'),S=require('../site/cluster-stability.js');
const encode=v=>new TextEncoder().encode(JSON.stringify(v)),clone=v=>JSON.parse(JSON.stringify(v));
(async()=>{
  const records=[];for(let i=0;i<3;i++){
    const text='A 😀 café. Speech '+i+' energy climate oceans. Final original sentence.';
    records.push({id:'asset/test/source'+i+'#1',text,text_sha256:await C.digest(text),raw_sha256:'b'.repeat(64),date:'2026-09-22',country:'Country '+i,region:'Asia-Pacific',language:'en',scope:'general_debate',meeting:'General Debate '+i,source_url:'https://transcripts.un.org/en/asset/test/source'+i});
  }
  const source='\uFEFF'+JSON.stringify({schema:'un.browser.corpus.v1',records,coverage:[]},null,2).replace(/\n/g,'\r\n');
  const passages=[];for(const [i,r] of records.entries())for(const [j,[start,end]] of [[2,8],[10,40]].entries())passages.push({id:'P'+i+j,parent_id:r.id,start,end,text_sha256:await C.digest(C.slice(r.text,start,end))});
  const audio={id:'A01',parent_id:records[0].id,parent_text_sha256:records[0].text_sha256,start:2,end:8,original_excerpt:'😀 café',video_url:'https://webtv.un.org/en/asset/test/source0',source_url:records[0].source_url,clip_start_seconds:0,clip_end_seconds:5,clip_sha256:await C.digest('abc'),audio_base64:'YWJj'};
  const packet={schema:'un.speech-pilot-packet.v1',corpus_sha256:await C.digest(source),selection:'Synthetic engineering fixture',parents:records.map(r=>({...r,reviewed_type:'substantive_speech'})),passages,audio:[audio]};
  audio.source_snapshot_sha256=records[0].raw_sha256;
  const packetText=JSON.stringify(packet),ctx=await C.load(new TextEncoder().encode(packetText)),confirmed={confirmed:true,reviewer:'ENGINEERING TEST ONLY',reviewed_at:'2020-01-01T00:00:00Z',note:''};
  const review={schema:'un.speech-pilot-review.v1',packet_sha256:ctx.packet_sha256,corpus_sha256:packet.corpus_sha256,choices:[{...confirmed,kind:'audio',id:'A01',decision:'supported',listened:true},...passages.map(p=>({...confirmed,kind:'passage',id:p.id,decision:'include',start:p.start,end:p.end}))]};
  const good=await R.create(source,packetText,JSON.stringify(review),A.validateCorpus),bundle=JSON.parse(new TextDecoder().decode(good.bytes));
  assert.deepEqual(good.corpus.reviewed_units.input,{passages:6,parent_speeches:3,meetings:3});
  assert.ok(Object.isFrozen(good.corpus.records[0]));assert.equal(good.units.records[0].utf8_end,12);
  assert.equal(good.corpus.records[0].scope,'general_debate');assert.match(good.corpus.records[0].review_scope,/not full audio verification/);
  for(const unit of ['meeting','country']){const grouped=S.groupRecords(good.corpus.records,unit);assert.equal(grouped.groups.length,3);assert.ok(grouped.groups.every(g=>g.indices.length===2));}
  const params={topic:'',start:'2026-09-22',end:'2026-09-28',region:'All regions',scope:'general_debate',methods:['frequency','tfidf']};
  const result=await A.analyze(good.corpus,params);
  assert.equal(result.counts.duplicates,2);assert.equal(result.reviewed_units.included.passages,4);assert.equal(result.reviewed_units.included.parent_speeches,3);
  assert.ok(result.duplicates.every(r=>r.parent_id));
  const filtered=await A.analyze(good.corpus,{...params,region:'Africa'});assert.equal(filtered.reviewed_units.included.parent_speeches,0);
  await assert.rejects(()=>A.analyze(clone(good.corpus),params),/validated analysis bundle/);
  await assert.rejects(()=>A.analyze(good.corpus,{...params,passageSelection:{policy:'substantive'}}),/mask/);
  for(const mutation of [
    b=>b.source_json+=' ',b=>b.units.records[0].text+='x',b=>b.units.records[0].start++,
    b=>b.units.records[0].utf8_end++,b=>b.units.records[0].parent_id='wrong',b=>b.units.records[0].id='wrong',
    b=>b.units.records[0].reviewer='',b=>b.units.records.push(b.units.records[0]),
    b=>{const r=JSON.parse(b.review_json);r.choices.pop();b.review_json=JSON.stringify(r);},
    b=>{const r=JSON.parse(b.review_json);r.choices[0].listened=false;b.review_json=JSON.stringify(r);},
    b=>{const p=JSON.parse(b.packet_json);p.parents[0].country='Altered';b.packet_json=JSON.stringify(p);},
    b=>{const p=JSON.parse(b.packet_json);p.audio[0].audio_base64='YWJk';b.packet_json=JSON.stringify(p);}
  ]){const bad=clone(bundle);mutation(bad);await assert.rejects(()=>R.load(encode(bad),A.validateCorpus));}
  const mismatch=clone(review);mismatch.choices[0].decision='mismatch';mismatch.choices[0].note='Only a partial suggested correction';
  const rejected=await R.create(source,packetText,JSON.stringify(mismatch),A.validateCorpus);assert.equal(rejected.units.records.length,5);assert.equal(rejected.units.withheld[0].id,'P00');
  assert.equal(rejected.ledger.records[0].replacement_text,null);assert.equal(rejected.ledger.records[0].reviewer_note,mismatch.choices[0].note);assert.equal(rejected.ledger.records[0].original_excerpt,'😀 café');
  const cancelled=async()=>{throw new Error('Cancelled');};await assert.rejects(()=>R.load(good.bytes,A.validateCorpus,cancelled),/Cancelled/);
  assert.equal(JSON.parse(new TextDecoder().decode(good.bytes)).source_json,source);
  console.log('PASS reviewed-unit import: exact source/UTF-8 offsets, BOM/CRLF, immutable validation, parent/meeting grouping, filter/dedup denominators, disputed spans, correction provenance, corruption and cancellation refusal');
})().catch(e=>{console.error(e);process.exitCode=1;});
