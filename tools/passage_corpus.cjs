#!/usr/bin/env node
'use strict';
/** Local/offline corpus preparation plus explicitly development-only acquisition. */
const fs=require('node:fs'),path=require('node:path');
const C=require('../research/corpus/contract.cjs');
const read=p=>JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(fs.readFileSync(p)).replace(/^\uFEFF/,''));
const write=(p,x)=>fs.writeFileSync(p,JSON.stringify(x,null,2)+'\n',{flag:'wx',mode:0o600});
function directory(p){C.assert(p,'A NEW output directory is required');fs.mkdirSync(p,{recursive:false,mode:0o700});return p;}
function cell(x){let s=x==null?'':typeof x==='object'?C.stable(x):String(x);if(/^[=+\-@\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';}
function csv(file,rows,fields){fs.writeFileSync(file,[fields.map(cell).join(','),...rows.map(r=>fields.map(k=>cell(r[k])).join(','))].join('\r\n')+'\r\n',{flag:'wx',mode:0o600});}
async function fetchBytes(url){
  const u=new URL(url);C.assert(u.origin==='https://transcripts.un.org'&&!u.search&&!u.hash&&!u.username&&!u.password,'Unapproved transcript endpoint');
  const response=await fetch(u,{redirect:'error',credentials:'omit',signal:AbortSignal.timeout(30000),headers:{Accept:'application/json'}});
  C.assert(response.ok,'Source HTTP '+response.status);
  C.assert(/application\/json/i.test(response.headers.get('content-type')||''),'Source did not return JSON');
  const reader=response.body.getReader(),parts=[];let count=0;
  try{while(true){const {done,value}=await reader.read();if(done)break;count+=value.length;C.assert(count<=12*1024*1024,'Source exceeds 12 MB limit');parts.push(Buffer.from(value));}}finally{await reader.cancel().catch(()=>{});}
  return Buffer.concat(parts);
}
async function collect(frame,output,request=fetchBytes){
  C.validateFrame(frame);const out=directory(output),responses=[],requested=[];
  // This interface has deliberately no split switch. A reserved endpoint is never fetched.
  for(const m of frame.meetings.filter(m=>m.split==='development')){
    if(!m.has_transcript){responses.push({meeting_id:m.meeting_id,status:'inventory_unavailable'});continue;}
    const row={meeting_id:m.meeting_id,status:'failed',retrieved_at:new Date().toISOString()};
    try{
      C.assert(m.json_url===`https://transcripts.un.org/en/${m.meeting_id}.json`,'Frozen endpoint mismatch');
      requested.push(m.meeting_id);const raw=await request(m.json_url);
      const doc=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw).replace(/^\uFEFF/,''));
      C.assert(doc.video?.slug===m.meeting_id&&doc.video?.date?.slice(0,10)===m.date,'Raw meeting identity/date mismatch');
      Object.assign(row,{status:'downloaded',raw_base64:raw.toString('base64'),raw_sha256:C.sha(raw)});
    }catch(error){row.error=error.message;}
    responses.push(row);
  }
  const registry=read(path.join(__dirname,'../site/countries.json')).map(r=>({...r,aliases:Array.isArray(r.aliases)?r.aliases:String(r.aliases||'').split('|')}));
  const bundle=C.makeBundle(frame,responses,registry);write(path.join(out,'source-bundle.json'),bundle);
  write(path.join(out,'acquisition.json'),{schema:'un.corpus-acquisition.v1',frame_sha256:frame.sha256,source_bundle_sha256:bundle.sha256,requested_meeting_ids:requested,requested_transcripts:requested.length,reserved_transcripts_requested:0,downloaded:responses.filter(r=>r.status==='downloaded').length,failed:responses.filter(r=>r.status==='failed').length,inventory_unavailable:responses.filter(r=>r.status==='inventory_unavailable').length,failures:responses.filter(r=>r.status==='failed'),raw_sources_preserved:true});
  return bundle;
}
function writeCorpus(out,corpus){
  write(path.join(out,'corpus.json'),corpus);const audit=C.audit(corpus);write(path.join(out,'audit.json'),audit);
  csv(path.join(out,'passages.csv'),corpus.passages,['id','parent_id','meeting_id','speech_id','date','genre','country','language','parent_start','parent_end','tokens','text_sha256','parent_text_sha256','raw_sha256','json_pointer','review_status','review_type','extent','exclusions','speech_exclusions']);
  csv(path.join(out,'coverage.csv'),corpus.coverage,['meeting_id','date','genre','body','status','language','source_segments','empty_segments','timestamps_flagged','raw_sha256','error']);
  csv(path.join(out,'parent-coverage.csv'),corpus.parent_coverage,['parent_id','meeting_id','speech_id','observed_code_points','partitioned_code_points','source_eligible_code_points','speech_eligible_code_points','partitions','review_status','extent','coverage_basis']);
  const tables=[];for(const population of ['source_segments','reviewed_speeches'])for(const scheme of ['equal_passage','equal_meeting','equal_speech','equal_country']){const table=C.weights(C.select(corpus,{population}),scheme);for(const row of table.rows)tables.push({population,scheme,...row});}
  csv(path.join(out,'weights.csv'),tables,['population','scheme','id','meeting_id','speech_id','country','weight','text_sha256']);
  write(path.join(out,'boundary-review-template.json'),{schema:'un.corpus-boundary-review.v1',source_bundle_sha256:corpus.source_bundle.sha256,scope:'Whole original source-segment boundaries only. A segment is not automatically a complete speech. Existing owner pilot decisions are separate and unchanged.',choices:corpus.parents.map(r=>({id:r.id,text_sha256:r.text_sha256,confirmed:false,type:null,extent:'unknown',speech_id:null,reviewer:'',reviewed_at:'',note:''}))});
  return audit;
}
async function analyze(corpus,options={}){
  const c=C.load(corpus),s=C.select(c,options);
  C.assert((options.fit_weighting||'equal_passage')==='equal_passage','Weighted fitting is unsupported; only summary weights are enabled');
  const base={schema:'un.expanded-development-analysis.v1',corpus_sha256:c.sha256,frame_sha256:c.frame.sha256,population:s.population,selection_sha256:s.selection_sha256,review_warning:s.review_warning,fit_weighting:'equal_passage',publication_status:'audit_only',holdout_opened:false};
  const K=require('../site/cluster-core.js');
  if(s.rows.length<4||s.rows.length>K.MAX_RECORDS)return {...base,status:'withheld',reason:`The existing clustering kernel requires 4–${K.MAX_RECORDS} selected observations; ${s.rows.length} were selected. No sampling performed.`};
  C.assert(!options.clustering?.stability?.enabled,'Grouped refits require a separately validated frozen-reference adapter; not enabled in this contract phase');
  const reference=C.fitReference(c,options),vectors=C.transform(reference,s.rows);
  const fit=await K.run(s.rows.map(r=>({...r,source_group:r.meeting_id,meeting:r.meeting_id,country:r.country||'Unidentified'})),vectors.map(r=>new Map(r.vector)),{...options.clustering,stability:{enabled:false}});
  return {...base,status:fit.skipped?'withheld':'fitted',reference,fit,composition:['equal_passage','equal_meeting','equal_speech','equal_country'].map(scheme=>C.composition(s,fit.points||[],scheme))};
}
async function main(args){
  const [command,...a]=args;
  if(command==='freeze'){
    C.assert(a.length===3,'Usage: freeze INVENTORY.json PLAN.json NEW_DIR');const frame=C.makeFrame(read(a[0]),read(a[1])),out=directory(a[2]);write(path.join(out,'frame.json'),frame);console.log(C.stable({frame_sha256:frame.sha256,meetings:frame.meetings.length}));
  }else if(command==='collect-development'){
    C.assert(a.length===2,'Usage: collect-development FRAME.json NEW_DIR');const b=await collect(read(a[0]),a[1]);console.log(C.stable({source_bundle_sha256:b.sha256,development_meetings:b.sources.length,holdout_requested:0}));
  }else if(command==='build'){
    C.assert(a.length===3||a.length===4,'Usage: build FRAME.json SOURCE_BUNDLE.json NEW_DIR [BOUNDARY_REVIEW.json]');const c=C.build(read(a[0]),read(a[1]),a[3]?read(a[3]):null),out=directory(a[2]);console.log(C.stable(writeCorpus(out,c)));
  }else if(command==='audit'){
    C.assert(a.length===1,'Usage: audit CORPUS.json');console.log(JSON.stringify(C.audit(read(a[0])),null,2));
  }else if(command==='reference'){
    C.assert(a.length===3,'Usage: reference CORPUS.json OPTIONS.json NEW_REFERENCE.json');const ref=C.fitReference(read(a[0]),read(a[1]));write(a[2],ref);console.log(C.stable({reference_sha256:ref.sha256,development_observations:ref.training_ids.length,vocabulary:ref.vocabulary.length}));
  }else if(command==='analyze-development'){
    C.assert(a.length===3,'Usage: analyze-development CORPUS.json OPTIONS.json NEW_ANALYSIS.json');const result=await analyze(read(a[0]),read(a[1]));write(a[2],result);console.log(C.stable({status:result.status,reason:result.reason??null,holdout_opened:false}));
  }else if(command==='lock-comparison'){
    C.assert(a.length===4,'Usage: lock-comparison FRAME.json REFERENCE.json SETTINGS.json NEW_LOCK.json');const lock=C.comparisonLock(read(a[0]),read(a[1]),read(a[2]));write(a[3],lock);console.log(C.stable({lock_sha256:lock.sha256,holdout_meetings:lock.holdout_ids.length}));
  }else throw Error('Commands: freeze, collect-development, build, audit, reference, analyze-development, lock-comparison. All outputs must be new; no implicit overwrite or held-out collection.');
}
module.exports={collect,writeCorpus,analyze,main,csv};
if(require.main===module)main(process.argv.slice(2)).catch(error=>{console.error(error.message);process.exitCode=1;});
