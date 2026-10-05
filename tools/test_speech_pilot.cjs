const assert=require('node:assert/strict'),fs=require('node:fs'),C=require('../site/passage-pilot-core.js');
const encode=d=>new TextEncoder().encode(JSON.stringify(d)),clone=d=>JSON.parse(JSON.stringify(d));
(async()=>{
 const text='A 😀 café. Second sentence. Third sentence.',parent={id:'asset/test#1',text,text_sha256:await C.digest(text),raw_sha256:'b'.repeat(64),source_url:'https://transcripts.un.org/en/asset/test',reviewed_type:'substantive_speech',country:'Test',date:'2026-09-22'};
 const make=(id,start,end)=>({id,parent_id:parent.id,start,end,text_sha256:null});const p1=make('P01',2,8),p2=make('P02',10,26);
 for(const p of [p1,p2])p.text_sha256=await C.digest(C.slice(text,p.start,p.end));
 const audio={id:'A01',parent_id:parent.id,parent_text_sha256:parent.text_sha256,start:10,end:16,original_excerpt:C.slice(text,10,16),video_url:'https://webtv.un.org/en/asset/test',clip_start_seconds:0,clip_end_seconds:10,audio_base64:'YWJj',clip_sha256:await C.digest('abc')};
 const packet={schema:'un.speech-pilot-packet.v1',corpus_sha256:'a'.repeat(64),parents:[parent],passages:[p1,p2],audio:[audio],selection:'Synthetic engineering fixture'};const ctx=await C.load(encode(packet));
 const record={confirmed:true,reviewer:'ENGINEERING FIXTURE',reviewed_at:new Date().toISOString(),note:''};
 const review={schema:'un.speech-pilot-review.v1',packet_sha256:ctx.packet_sha256,corpus_sha256:packet.corpus_sha256,choices:[{...record,id:'A01',kind:'audio',decision:'unclear',listened:false},...[p1,p2].map(p=>({...record,id:p.id,kind:'passage',decision:'include',start:p.start,end:p.end}))]};
 const result=await C.derive(ctx,review);assert.equal(result.records.length,1);assert.equal(result.withheld[0].id,'P02');assert.equal(result.records[0].text,'😀 café');assert.equal(result.records[0].utf8_start,2);assert.equal(result.records[0].utf8_end,12);assert.equal(result.records[0].parent_id,parent.id);
 const supported=clone(review);supported.choices[0].decision='supported';assert.throws(()=>C.review(ctx,supported),/Listen/);supported.choices[0].listened=true;assert.equal((await C.derive(ctx,supported)).records.length,2);
 const overlap=clone(supported);overlap.choices[2].start=3;await assert.rejects(()=>C.derive(ctx,overlap),/overlap/);
 const mismatch=clone(supported);mismatch.choices[0].decision='mismatch';assert.throws(()=>C.review(ctx,mismatch),/Describe/);mismatch.choices[0].note='Different wording';assert.equal((await C.derive(ctx,mismatch)).records.length,1);
 for(const change of [r=>r.choices.pop(),r=>r.packet_sha256='0'.repeat(64),r=>r.choices.push(r.choices[0]),r=>r.choices[1].end=200,r=>r.choices[1].reviewer='',r=>r.choices[1].reviewed_at='2999-01-01T00:00:00Z']){const r=clone(review);change(r);await assert.rejects(()=>C.derive(ctx,r));}
 for(const change of [p=>p.parents[0].text+='x',p=>p.audio[0].audio_base64='YWJk',p=>p.passages[0].end++,p=>p.parents[0].source_url='javascript:alert(1)',p=>p.parents[0].reviewed_type='procedure']){const p=clone(packet);change(p);await assert.rejects(()=>C.load(encode(p)));}
 if(process.argv[2]){const actual=await C.load(fs.readFileSync(process.argv[2]));assert.equal(actual.data.passages.length,12);assert.equal(actual.data.audio.length,12);assert.ok(actual.data.audio.every(a=>a.human_reviewed===false));await assert.rejects(()=>C.derive(actual,{schema:'un.speech-pilot-review.v1',packet_sha256:actual.packet_sha256,corpus_sha256:actual.data.corpus_sha256,choices:[]}));}
 console.log('PASS Unicode offsets, source/audio integrity, explicit decisions, unresolved-span exclusion, overlap and incomplete-review rejection; no human decisions inferred');
})().catch(e=>{console.error(e);process.exitCode=1;});
