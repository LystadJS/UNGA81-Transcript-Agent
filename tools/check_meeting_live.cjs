'use strict';
/* Live public-source check, separate from deterministic acceptance. No source text is saved. */
const fs=require('node:fs'),path=require('node:path'),P=require('../site/meeting-picker-core.js'),C=require('../site/collector.js'),A=require('../site/analysis-core.js');
(async()=>{
 const date=process.argv[2]||'2026-09-24',out=process.argv[3]||'live-meeting-validation.json';
 const validation={checked_at:new Date().toISOString(),date,source:'https://transcripts.un.org',mocked:false,source_text_saved:false};
 try{
  const inventory=await P.list(date);validation.inventory_meetings=inventory.total;validation.inventory_pages=inventory.pages;
  const available=inventory.meetings.find(m=>m.hasTranscript);
  if(!available)throw Error('No transcript-present meeting is currently listed for this date.');
  validation.selected_meeting={slug:available.slug,title:available.title,date:available.date};
  const countries=JSON.parse(fs.readFileSync(path.join(__dirname,'../site/countries.json'),'utf8'));
  const p={...P.selection(date,available),topic:'',region:'All regions',methods:['frequency','tfidf']};
  const corpus=await C.collect(p,countries);
  const report=await A.analyze(corpus,p);
  if(corpus.collection.selected_meetings!==1||corpus.collection.selected_meeting_slug!==available.slug||corpus.records.some(r=>r.meeting_slug!==available.slug))throw Error('Single-meeting isolation check failed.');
  validation.coverage=corpus.coverage;validation.collected_passages=corpus.records.length;validation.analyzed_passages=report.counts.matched;validation.selection_isolated=true;
  if(!corpus.records.length)throw Error('Selected meeting has no usable English text; inspect source coverage.');
  validation.status='PASS';
 }catch(error){validation.status='UNAVAILABLE_OR_FAILED';validation.error=error.message;}
 fs.writeFileSync(out,JSON.stringify(validation,null,2));console.log(JSON.stringify(validation));
 if(process.env.REQUIRE_LIVE_MEETING==='1'&&validation.status!=='PASS')process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
