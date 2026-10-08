'use strict';
/** Development-only speaker and institutional-series audit; no fetch or real holdout path. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const Quick=require('../../site/meeting-quick-reader.js');
const EXPECTED='e8fb980cf638e2aef39d0ca3564836c6120201a059e806ccaaee3fd5cc4f593e';
const sha=text=>crypto.createHash('sha256').update(text).digest('hex');
const check=(ok,msg)=>{if(!ok)throw Error(msg)};
function summarize(corpus,{strictDigest=true}={}){
  check(corpus?.schema==='un.passage-corpus.v1','Source corpus schema mismatch');
  if(strictDigest)check(corpus.sha256===EXPECTED,'Development source digest changed');
  check(corpus.frame?.holdout_state==='reserved_not_downloaded','Frame is not reserved');
  check(Array.isArray(corpus.parents)&&Array.isArray(corpus.passages)&&corpus.parents.length<=50000,'Source size or shape changed');
  const parents=new Set(),meetings=new Set(),series=new Map(),roles=new Map(),proxy=new Map(),ledger=[];
  let speakerIds=0,withFunction=0,withAffiliation=0,completeProxy=0,mapped=0,seriesKnown=0;
  for(const p of corpus.parents){
    check(p.split==='development'&&['2026-10-01','2026-10-02'].includes(p.date),'Nondevelopment record rejected');
    check(typeof p.id==='string'&&p.id.startsWith(p.meeting_id+'#')&& !parents.has(p.id),'Invalid source identity');
    check(typeof p.text==='string'&&sha(p.text)===p.text_sha256,'Source text integrity error');
    parents.add(p.id);meetings.add(p.meeting_id);
    const info=Quick.speakerEvidence({speaker_metadata:p.speaker_metadata,attribution:{country_status:p.country?'registry_mapped':'unresolved'},region:p.region});
    const agenda=Quick.agendaSeries(p.meeting_id,p.body);
    if(info.speaker_identity_observed)speakerIds++;
    if(info.recorded_function)withFunction++;
    if(info.recorded_affiliation)withAffiliation++;
    if(info.speaker_proxy){completeProxy++;let key=JSON.stringify(info.speaker_proxy);if(!proxy.has(key))proxy.set(key,new Set());proxy.get(key).add(p.meeting_id);}
    if(p.country)mapped++;
    if(agenda.series){seriesKnown++;series.set(agenda.series,(series.get(agenda.series)||0)+1);}
    roles.set(info.role,(roles.get(info.role)||0)+1);
    ledger.push({source_segment_id:p.id,text_sha256:p.text_sha256,meeting_id:p.meeting_id,
      country_label:p.country||null,recorded_speaker_id:info.speaker_identity_observed,affiliation_function_proxy_present:!!info.speaker_proxy,
      role:info.role,agenda_series:agenda.series,agenda_basis:agenda.basis});
  }
  for(const p of corpus.passages)check(p.split==='development'&&['2026-10-01','2026-10-02'].includes(p.date)&&parents.has(p.parent_id),'Unexpected passage or holdout source');
  const aggregate={schema:'un.development-speaker-agenda-audit.v1',source_corpus_sha256:corpus.sha256,
    source_segments:parents.size,source_passages:corpus.passages.length,meetings:meetings.size,known_country_segments:mapped,unknown_country_segments:parents.size-mapped,
    attribution:{explicit_speaker_identifiers:speakerIds,affiliation_recorded:withAffiliation,function_recorded:withFunction,
      complete_affiliation_function_proxies:completeProxy,proxy_values_crossing_meetings:[...proxy.values()].filter(s=>s.size>1).length,
      verified_distinct_persons:null},
    agenda:{canonical_series_segments:seriesKnown,unknown_series_segments:parents.size-seriesKnown,series_counts:Object.fromEntries([...series].sort((a,b)=>a[0].localeCompare(b[0]))),
      limitation:'Institutional series is a source-path proxy, not an independently verified formal agenda.'},
    role_counts:Object.fromEntries([...roles].sort((a,b)=>a[0].localeCompare(b[0]))),
    inference:'No person identification, official country policy or agenda classification inferred from co-occurrence.',
    temporal_holdout_accessed:0,network_requests:0};
  return {aggregate,private_ledger:ledger};
}
function main(){
  if(process.argv.length!==4)throw Error('Usage: node meeting_attribution_audit.cjs CACHED_DEVELOPMENT_CORPUS.json NEW_OUTPUT_DIR');
  const out=path.resolve(process.argv[3]);check(!fs.existsSync(out),'Do not overwrite previous audit');
  const report=summarize(JSON.parse(fs.readFileSync(process.argv[2],'utf8')));
  fs.mkdirSync(out,{recursive:true});
  fs.writeFileSync(path.join(out,'aggregate.json'),JSON.stringify(report.aggregate,null,2)+'\n');
  fs.writeFileSync(path.join(out,'private-ledger.json'),JSON.stringify(report.private_ledger,null,2)+'\n');
  process.stdout.write(JSON.stringify(report.aggregate)+'\n');
}
module.exports={summarize};if(require.main===module){try{main()}catch(e){console.error(e.stack);process.exitCode=1;}}
