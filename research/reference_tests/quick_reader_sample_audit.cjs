'use strict';
/** Deterministic seven-stratum development-only QA. Never fetches sources. Private samples stay local. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const Quick=require('../../site/meeting-quick-reader.js');
const EXPECTED='e8fb980cf638e2aef39d0ca3564836c6120201a059e806ccaaee3fd5cc4f593e';
const SEED='quick-reader-check-2026-10-08-pre-output';
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const assert=(value,message)=>{if(!value)throw Error(message);};
const strata={
  ga_plenary:m=>/^ga\/\d+\/\d+$/.test(m.meeting_id),
  ga_third:m=>/^ga\/c3\//.test(m.meeting_id),
  ga_fourth:m=>/^ga\/c4\//.test(m.meeting_id),
  human_rights_council:m=>/^hrc\//.test(m.meeting_id),
  press:m=>m.genre==='Press Conferences',
  conferences:m=>m.genre==='Conferences',
  treaty_body:m=>m.genre==='Human Rights Treaty Bodies'
};
const oldSkip=/^(?:(?:thank you|i thank|i now (?:give|invite)|the meeting is (?:called|adjourned)|the floor is (?:given|yours)|we shall now|next speaker|i (?:give|yield) the floor|good (?:morning|afternoon))\b)/i;
function audit(corpus){
  assert(corpus?.schema==='un.passage-corpus.v1'&&corpus.sha256===EXPECTED,'Exact development corpus required');
  assert(corpus.frame?.holdout_state==='reserved_not_downloaded','Reserved metadata status differs');
  assert(corpus.frame.meetings.filter(m=>m.split==='holdout').length===37,'Frozen holdout metadata count mismatch');
  assert(corpus.parents.length===1293&&corpus.passages.length===2596,'Development source size mismatch');
  const meetings=corpus.frame.meetings.filter(m=>m.split==='development'&&m.has_transcript);
  const picks=[],privateRows=[];
  let nSelected=0,nOldExcludedLong=0,nRecoveredLong=0,nSourceErrors=0,nNewPositions=0;
  for(const [stratum,predicate] of Object.entries(strata)){
    const options=meetings.filter(predicate).sort((a,b)=>sha(SEED+'|'+stratum+'|'+a.meeting_id).localeCompare(sha(SEED+'|'+stratum+'|'+b.meeting_id)));
    assert(options.length>0,'Missing population for '+stratum);
    const m=options[0];
    assert(m.split==='development'&&['2026-10-01','2026-10-02'].includes(m.date),'Not a development meeting');
    const selected=corpus.parents.filter(p=>p.meeting_id===m.meeting_id);
    const rows=selected.map(p=>{
      assert(p.split==='development' && p.id.startsWith(p.meeting_id+'#') && sha(p.text)===p.text_sha256,'Parent integrity violation');
      return {id:p.id,meeting_slug:p.meeting_id,date:p.date,language:p.language,country:p.country||p.affiliation_raw||'Unidentified',region:p.region||'Unmapped',
        meeting:m.title,scope:'all',text:p.text,text_sha256:p.text_sha256,source_url:p.source_url,json_pointer:p.json_pointer,
        attribution:{country_status:p.country?'registry_mapped':'unresolved'},speaker_metadata:p.speaker_metadata,timestamps_flagged:p.timestamps_flagged};
    });
    const report=Quick.build(rows,{meeting_slug:m.meeting_id,meeting_date:m.date,title:m.title});
    let longBefore=0,longAfter=0;
    for(const row of rows){
      const oldWouldDrop=(row.text.match(/\S+/g)||[]).length>=40&&oldSkip.test(row.text.trim());
      if(oldWouldDrop){longBefore++;if(Quick.isSubstantive(row.text))longAfter++;}
      if(!Quick.safeURL(row.source_url))nSourceErrors++;
    }
    assert(longBefore===longAfter,'Long substantive passage still excluded under courtesy-only rule');
    const count=report.stats;
    assert(count.mapped_country_segments+count.unresolved_country_segments===count.source_segments,'Unreconciled country coverage');
    assert(report.positions.every(x=>x.evidence.every(e=>e.record_id.startsWith(m.meeting_id+'#'))),'Evidence crosses meeting');
    nSelected+=rows.length;nOldExcludedLong+=longBefore;nRecoveredLong+=longAfter;nNewPositions+=report.positions.length;
    picks.push({stratum,meeting_id:m.meeting_id,title:m.title,date:m.date,genre:m.genre,source_segments:rows.length,
      old_long_prefix_excluded:longBefore,recovered_long:longAfter,substantive_looking_segments:count.substantive_looking_segments,
      mapped:count.mapped_country_segments,unresolved:count.unresolved_country_segments,
      group_cue_segments:count.withheld_collective_segments,agenda_cue_count:report.agenda_cues.length,
      themes:report.themes.map(t=>({id:t.id,segments:t.segments})),positions:report.positions.map(p=>({country:p.country,issue:p.issue,classification:p.classification,source_segments:p.source_segment_count}))});
    privateRows.push({stratum,meeting:m,report,rows:rows.map((r,i)=>({...r,preceding:rows[i-1]?.text?.slice(0,450)||null,following:rows[i+1]?.text?.slice(0,450)||null}))});
  }
  const hrc=privateRows.find(x=>x.stratum==='human_rights_council').report;
  assert(hrc.agenda_cues.length===2&&/Haiti/i.test(hrc.agenda_cues[0].excerpt)&&/Cambodia/i.test(hrc.agenda_cues[1].excerpt),'Multi-part HRC agenda context missing');
  assert(privateRows.find(x=>x.stratum==='ga_fourth').report.themes.some(x=>x.id==='decolonization'),'Fourth committee context still lost');
  assert(!privateRows.some(x=>x.report.positions.some(p=>p.country==='Finland'&&x.stratum==='human_rights_council')),'Group speaker attributed to Finland');
  assert(!privateRows.some(x=>x.report.positions.some(p=>p.country==='Iran'&&x.stratum==='ga_fourth')),'Group speaker attributed to Iran');
  assert(!privateRows.some(x=>x.report.positions.some(p=>p.country==='Bulgaria'&&p.issue_id==='peace_security')),'Distant supported measure promoted to peace/security position');
  assert(nSourceErrors===0,'Unsafe source link');
  const aggregate={schema:'un.quick-reader-development-sample-audit.v1',development_corpus_sha256:corpus.sha256,
    source:'cached_development_only',selection_seed:SEED,sampling:'one meeting per seven metadata strata; minimum SHA256(seed|stratum|meeting_id) before evaluating outputs',
    meetings:picks.length,source_segments:nSelected,original_long_procedural_prefix_exclusions:nOldExcludedLong,
    recovered_long_segments:nRecoveredLong,positions_after_guardrails:nNewPositions,
    prior_unmodified_output_positions_in_same_sample:9,heldout_meetings_in_frame_metadata_only:37,heldout_content_read:0,network_requests:0,
    observed_issues:['unconditional prefix exclusion','group spokesperson assigned to individual country','verb object too far from matched subject','generic issue dictionary omitted decolonization and criminal justice','no explicit Haiti/Cambodia transition','one mapped-but-unmapped segment not counted as unresolved'],
    meetings_aggregate:picks,
    interpretation:'Source-segment counts are not independently verified speeches or people. Assistant-conducted provisional QA is not owner adjudication, precision estimation or official country-position validation.'};
  return {aggregate,privateRows};
}
function main(){
  assert(process.argv.length===4,'Usage: node quick_reader_sample_audit.cjs PRIVATE_DEVELOPMENT_CORPUS.json NEW_OUTPUT_DIRECTORY');
  const out=path.resolve(process.argv[3]);assert(!fs.existsSync(out),'Never overwrite earlier evidence');
  const {aggregate,privateRows}=audit(JSON.parse(fs.readFileSync(process.argv[2],'utf8')));
  fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'aggregate.json'),JSON.stringify(aggregate,null,2)+'\n');
  fs.writeFileSync(path.join(out,'private-evidence.json'),JSON.stringify(privateRows));console.log(JSON.stringify({...aggregate,meetings_aggregate:undefined}));
}
if(require.main===module){try{main()}catch(e){console.error(e.stack);process.exitCode=1;}}
module.exports={audit,strata,SEED};
