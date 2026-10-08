#!/usr/bin/env node
'use strict';
/** Synthetic-only, production-schema fixture: calls the real corpus validator and partitioner.
 * No fetching, no real meeting slug, no reserved date, no actual testimony.
 */
const fs=require('node:fs');const path=require('node:path');const C=require('../corpus/contract.cjs');
const assert=C.assert;
const FAKE_DATE='2099-01-05', FUTURE_FAKE_DATE='2099-01-06';
const PREFIX='synthetic_fixture_';
const roleGenres=['General Assembly','Human Rights Council','Security Council','Press Conferences','High-level Meetings','Events'];
const topics=[
  'technical cooperation and education development programmes',
  'public health infrastructure and sustainable water supply',
  'renewable energy transition and environmental monitoring',
  'economic development investment and technical assistance',
  'civilian protection humanitarian coordination and assistance',
  'data quality and scientific innovation collaboration'];
function meeting(i){const slug=`${PREFIX}/meeting_${String(i).padStart(2,'0')}`;const avail=i!==32&&i!==33;
  return {slug,title:`SYNTHETIC FIXTURE ${i}`,date:FAKE_DATE,category:roleGenres[i%roleGenres.length],body:'SYNTHETIC_BODY',hasTranscript:avail,
    pageUrl:`https://transcripts.un.org/en/${slug}`,jsonUrl:avail?`https://transcripts.un.org/en/${slug}.json`:null};}
function textFor(i,j){
  const topic=topics[(i+j)%topics.length];
  if(j===0)return 'The meeting is called to order. I now give the floor to the next participant.';
  if(j===1)return 'Thank you, Chair.';
  if(j===2)return 'Thank you for your patience. [inaudible] The recording requires further verification.';
  if(j===3)return 'Thank you for the question on regional coordination and communication. We will provide an update through the usual channels.';
  let sentence=`Thank you, Chair. In this synthetic discussion, the participants describe ${topic}. We consider reliable public information, careful statistical methods, and transparent institutional procedures important for an accurate scientific assessment.`;
  sentence+=' '+Array(4).fill('The simulated briefing records statistical observations and discusses public information with institutions in several technical working sessions.').join(' ');
  if(j===4&&i<2)sentence+=' '+Array(12).fill('The simulated report describes cooperation, institutional resources, shared scientific evidence, and public access to documentation.').join(' ');
  return sentence+` This statement is artificially generated and contains no actual diplomatic testimony. Example identifier ${i} and ${j}.`;
}
function response(i){const data=[];
  for(let j=0;j<13;j++){
    let role='delegate', affiliation=j%4===0?'':`SIM-COUNTRY-${String((i+j)%26).padStart(2,'0')}`;
    if(j===0){role='chair';affiliation='SIM-SECRETARIAT';}
    if(j===3){role='journalist';affiliation='SIM-MEDIA';}
    let t=j===12?'':textFor(i,j);
    data.push({speaker:{function:role,affiliation,affiliation_full:affiliation},paragraphs:[{sentences:
      t?[{text:t.slice(0,Math.ceil(t.length/2))},{text:t.slice(Math.ceil(t.length/2))}]:[]}],start:j*1000,end:(j+1)*1000});
  }
  return {video:{slug:meeting(i).slug,date:FAKE_DATE,title:`SYNTHETIC FIXTURE ${i}`},
    transcript:{language:i>=35?'fr':'en',timestamps_flagged:i%7===0,data}};
}
function generate(){
  const all=Array.from({length:37},(_,i)=>meeting(i));
  const phantom={slug:`${PREFIX}/phantom`,title:'FAKE FUTURE FRAME SENTINEL',date:FUTURE_FAKE_DATE,hasTranscript:false,category:'SYNTHETIC',pageUrl:`https://transcripts.un.org/en/${PREFIX}/phantom`};
  const plan={schema:'un.passage-plan.v1',selection_rule:'SYNTHETIC generated fixture only; no requests to UN',development_dates:[FAKE_DATE],holdout_dates:[FUTURE_FAKE_DATE],split_unit:'whole_meeting',fit_weighting:'equal_passage',partition:{algorithm:'balanced_whitespace_v1',max_tokens:120,min_tokens:12},language:'en',duplicate_policy:'retain_and_audit',review_policy:'explicit_speech_boundaries',country_missing:'withhold'};
  const inventory={schema:'un.inventory-frame.v1',transcripts_opened:0,retrieved_at:'2099-01-01T00:00:00Z',dates:[
    {date:FAKE_DATE,pages:[{url:`https://transcripts.un.org/en/meetings.json?date=${FAKE_DATE}&xlang=1&page=1`,sha256:C.sha('SYNTHETIC_INVENTORY'),data:{page:1,total:37,hasMore:false,meetings:all}}]},
    {date:FUTURE_FAKE_DATE,pages:[{url:`https://transcripts.un.org/en/meetings.json?date=${FUTURE_FAKE_DATE}&xlang=1&page=1`,sha256:C.sha('SYNTHETIC_SENTINEL'),data:{page:1,total:1,hasMore:false,meetings:[phantom]}}]}]};
  const frame=C.makeFrame(inventory,plan);
  const fakeRaw=all.map((m,i)=>{
    if(!m.hasTranscript)return {meeting_id:m.slug,status:'inventory_unavailable'};
    if(i===34)return {meeting_id:m.slug,status:'failed',error:'SYNTHETIC simulated retrieval timeout'};
    const bytes=Buffer.from(JSON.stringify(response(i)),'utf8');
    return {meeting_id:m.slug,status:'downloaded',raw_base64:bytes.toString('base64'),raw_sha256:C.sha(bytes)};
  });
  const registry=Array.from({length:26},(_,i)=>({country:`SIM-COUNTRY-${String(i).padStart(2,'0')}`,region:'Synthetic region',aliases:[]}));
  const bundle=C.makeBundle(frame,fakeRaw,registry),corpus=C.build(frame,bundle);
  const statuses=Object.fromEntries([...new Set(corpus.coverage.map(x=>x.status))].map(s=>[s,corpus.coverage.filter(r=>r.status===s).length]));
  assert(corpus.coverage.length===37&&corpus.counts.reserved_meetings===1,'Synthetic 37-meeting source accounting failure');
  assert(corpus.parents.every(r=>r.id.startsWith(PREFIX+'/')),'Real identity entered fixture');
  assert(corpus.passages.every(p=>p.split==='development'&&p.date===FAKE_DATE),'Synthetic split violation');
  return {corpus,summary:{schema:'un.production-shape-synthetic-fixture.v1',synthetic:true,source_parser:'research/corpus/contract.cjs::build',fake_date:FAKE_DATE,source_meetings:37,reported_sources:corpus.coverage.length,source_statuses:statuses,source_parents:corpus.parents.length,passages:corpus.passages.length,eligible_source_passages:corpus.counts.source_segment_eligible,non_english_parents:corpus.parents.filter(p=>p.language!=='en').length,timestamp_flagged:corpus.parents.filter(p=>p.timestamps_flagged).length,sha256:corpus.sha256,real_holdout_requests:0}};
}
function main(){
  if(process.argv.length!==3)throw Error('Usage: node synthetic_un_fixture.cjs NEW_OUTPUT_DIRECTORY');
  const output=path.resolve(process.argv[2]);assert(!fs.existsSync(output),'Cannot overwrite fixture');
  const {corpus,summary}=generate();fs.mkdirSync(output,{recursive:true});
  fs.writeFileSync(path.join(output,'corpus.json'),JSON.stringify(corpus));fs.writeFileSync(path.join(output,'summary.json'),JSON.stringify(summary,null,2)+'\n');
  console.log(JSON.stringify(summary));
}
if(require.main===module){try{main()}catch(e){console.error(e.stack);process.exitCode=1;}}
module.exports={generate,response,meeting,FAKE_DATE,FUTURE_FAKE_DATE,PREFIX};
