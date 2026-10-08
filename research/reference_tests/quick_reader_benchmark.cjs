'use strict';
/** Exact-development, source-bound, partial-review adjudication benchmark.
 * Zero network calls, no holdout source reader. Provisional assistant reviews never become human decisions.
 */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const Q=require('../../site/meeting-quick-reader.js');
const DIGEST='e8fb980cf638e2aef39d0ca3564836c6120201a059e806ccaaee3fd5cc4f593e';
const ORIGINAL_SAMPLE=['ga/81/16','ga/c3/81/2','ga/c4/81/1','hrc/63/37','briefing/sg/2026-10-02','asset/k1o/k1o86tmojq','asset/k1y/k1yeh656yd'];
const SEED='quick-reader-adjudication-additional-2026-10-08-v1';
const ABSTENTION_SEED='qr-bench-abstention-2026-10-08';
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const assert=(ok,s)=>{if(!ok)throw Error(s)};
const cmp=(a,b)=>a.localeCompare(b);
const unique=x=>[...new Set(x)];
const bindingFor=(body)=>hash(JSON.stringify({schema:body.schema,corpus_sha256:body.corpus_sha256,cases:body.cases.map(x=>[x.id,x.kind,x.meeting_id,x.source_id,x.source_sha256,x.current_classification??null,x.visible_in_quick_reader??null,x.match_probes??null])}));
function row(p,m){return {id:p.id,meeting_slug:p.meeting_id,date:p.date,language:p.language,country:p.country||p.affiliation_raw||'Unidentified',region:p.region||'Unmapped',meeting:m.title,scope:'all',text:p.text,text_sha256:p.text_sha256,source_url:p.source_url,json_pointer:p.json_pointer,
  attribution:{country_status:p.country?'registry_mapped':'unresolved'},speaker_metadata:p.speaker_metadata,timestamps_flagged:p.timestamps_flagged};}
function checked(corpus){
 assert(corpus?.schema==='un.passage-corpus.v1'&&corpus.sha256===DIGEST,'Exact development corpus digest required');
 assert(corpus.frame?.holdout_state==='reserved_not_downloaded' && corpus.frame.meetings.filter(m=>m.split==='holdout').length===37,'Frozen reserved metadata state/count mismatch');
 assert(corpus.parents.length===1293&&corpus.passages.length===2596,'Source counts differ from frozen development');
 const parents=new Map();for(const p of corpus.parents){
  assert(p.split==='development'&&['2026-10-01','2026-10-02'].includes(p.date) && p.id.startsWith(p.meeting_id+'#'), 'Nondevelopment source rejected');
  assert(typeof p.text==='string'&&hash(p.text)===p.text_sha256&&!parents.has(p.id),'Source hash/key collision');
  parents.set(p.id,p);
 }
 for(const p of corpus.passages){
  const parent=parents.get(p.parent_id);assert(p.split==='development'&&parent,'Nondevelopment or orphan passage');
  assert(p.parent_text_sha256===parent.text_sha256&&p.meeting_id===parent.meeting_id,'Passage parent mismatch');
  assert(p.parent_start>=0&&p.parent_end>=p.parent_start&&Number.isInteger(p.parent_start)&&Number.isInteger(p.parent_end),'Invalid source spans');
  const slice=Array.from(parent.text).slice(p.parent_start,p.parent_end).join('');
  assert(slice===p.text&&hash(p.text)===p.text_sha256,'Original Unicode passage bytes/offsets differ');
 }
 const sourceMeetings=corpus.frame.meetings.filter(m=>m.split==='development'&&m.has_transcript&&corpus.parents.some(p=>p.meeting_id===m.meeting_id));
 assert(sourceMeetings.length===20&&ORIGINAL_SAMPLE.every(id=>sourceMeetings.some(m=>m.meeting_id===id)),'Original cohort is not reproducible');
 const additional=sourceMeetings.filter(m=>!ORIGINAL_SAMPLE.includes(m.meeting_id)).sort((a,b)=>cmp(a.meeting_id,b.meeting_id));
 assert(additional.length===13&&additional.reduce((n,m)=>n+corpus.parents.filter(p=>p.meeting_id===m.meeting_id).length,0)===923,'Additional meeting/source count mismatch');
 return {parents,additional,sourceMeetings};
}
function collect(corpus,baseline,anchors){
 const {parents,additional,sourceMeetings}=checked(corpus);
 assert(baseline?.schema==='un.quick-reader-saved-predictions.v1'&&baseline.corpus_sha256===DIGEST,'Original candidate output not bound to development corpus');
 const original=baseline.meetings;
 assert(Array.isArray(original)&&original.length===20&&unique(original.map(m=>m.meeting_id)).length===20,'Original output meeting frame mismatch');
 assert(sourceMeetings.every(m=>original.some(x=>x.meeting_id===m.meeting_id)),'Original output meeting IDs mismatch');
 const current=[],positions=[],abstentions=[],contexts=[],privateSources=[],coverage=[];
 assert(Array.isArray(anchors)&&anchors.length>=13&&unique(anchors.map(a=>a.id)).length===anchors.length,'Missing or repeated source-context anchors');
 const anchorMeetings=new Set(anchors.map(a=>a.record_id.split('#')[0]));
 assert(additional.every(m=>anchorMeetings.has(m.meeting_id)),'Context anchors omit development meeting');
 for(const m of additional){
  const psAll=corpus.parents.filter(p=>p.meeting_id===m.meeting_id);const ps=psAll.filter(p=>p.language==='en');const rows=ps.map(p=>row(p,m));
  const now=Q.build(rows,{meeting_slug:m.meeting_id,meeting_date:m.date,title:m.title});
  const old=original.find(x=>x.meeting_id===m.meeting_id);
  assert(old?.records===psAll.length&&old.date===m.date,'Original population/meeting mismatch');
  const oldParents=new Set();
  for(const pos of old.positions){
   const ids=unique(pos.evidence.map(e=>e.record_id));
   assert(ids.length&&ids.every(id=>parents.get(id)?.meeting_id===m.meeting_id),'Position evidence outside source meeting');
   const first=parents.get(ids[0]);
   assert(first.country===pos.country,'Country changed relative to source-linked evidence');
   assert(pos.evidence.every(e=>{const source=parents.get(e.record_id);return typeof e.source_url==='string'&&e.source_url===source?.source_url && source.text.replace(/\s+/g,' ').includes(String(e.excerpt).replace(/\s+/g,' ').slice(0,60));}), 'Position original evidence/source link mismatch');
   const id='position:'+m.meeting_id+':'+pos.country+':'+pos.issue_id;
   positions.push({id,kind:'position',meeting_id:m.meeting_id,source_id:first.id,source_sha256:first.text_sha256,source_url:first.source_url,json_pointer:first.json_pointer,
     recorded_country:pos.country,issue_id:pos.issue_id,original_classification:pos.classification,original_source_ids:ids,
     current_classification:now.positions.find(p=>p.country===pos.country&&p.issue_id===pos.issue_id)?.classification||null,
     source_excerpt:first.text.slice(0,900),original_evidence:pos.evidence.map(e=>({record_id:e.record_id,excerpt:e.excerpt,text_sha256:parents.get(e.record_id).text_sha256}))});
   ids.forEach(id=>oldParents.add(id));
  }
  const candidates=ps.filter(p=>p.country&&p.region&&Q.isSubstantive(p.text)&&Q.ISSUES.some(issue=>issue.pattern.test(p.text))&&!oldParents.has(p.id));
  candidates.sort((a,b)=>cmp(hash(ABSTENTION_SEED+'|'+a.id),hash(ABSTENTION_SEED+'|'+b.id)));
  const sampled=candidates.slice(0,4);
  for(const p of sampled){const r=row(p,m);abstentions.push({id:'abstention:'+p.id,kind:'abstention',meeting_id:m.meeting_id,source_id:p.id,source_sha256:p.text_sha256,
    source_url:p.source_url,json_pointer:p.json_pointer,recorded_country:p.country,role:Q.role(r),collective_cue:Q.collectiveAttribution(r),
    source_excerpt:p.text.slice(0,900),possible_issues:Q.ISSUES.filter(i=>i.pattern.test(p.text)).map(i=>i.id)});}
  current.push({meeting_id:m.meeting_id,title:m.title,genre:m.genre,date:m.date,source_segments:psAll.length,english_source_segments:ps.length,positions:now.positions.map(p=>({country:p.country,issue_id:p.issue_id,classification:p.classification})),agenda_cues:now.agenda_cues.map(x=>({record_id:x.record_id,excerpt:x.excerpt})),stats:now.stats,paragraphs:now.paragraphs});
  coverage.push({meeting_id:m.meeting_id,source_segments:psAll.length,english_source_segments:ps.length,original_positions:old.positions.length,revised_positions:now.positions.length,
   candidate_abstentions:candidates.length,abstention_sample:sampled.length,unresolved_country_segments:now.stats.unresolved_country_segments,
   explicit_speaker_ids:now.stats.records_with_explicit_speaker_id});
  privateSources.push(...ps.map(p=>({id:p.id,meeting_id:p.meeting_id,text_sha256:p.text_sha256,source_url:p.source_url,json_pointer:p.json_pointer,text:p.text,speaker_metadata:p.speaker_metadata,country:p.country,genre:p.genre})));
 }
 for(const anchor of anchors){
  assert(typeof anchor.term==='string'&&anchor.term.length>2&&anchor.term.length<150&&Array.isArray(anchor.probes)&&anchor.probes.length>0,'Invalid context anchor terms');
  const p=parents.get(anchor.record_id);assert(p&&additional.some(m=>m.meeting_id===p.meeting_id),'Context anchor not in additional development cohort');
  assert(p.text.toLowerCase().includes(anchor.term.toLowerCase()),'Context anchor not supported in original source: '+anchor.id);
  const now=current.find(m=>m.meeting_id===p.meeting_id);
  const visible=[...now.paragraphs,...now.agenda_cues.map(c=>c.excerpt)].join(' ').toLowerCase();
  const captured=anchor.probes.some(term=>visible.includes(String(term).toLowerCase()));
  contexts.push({id:'context:'+anchor.id,kind:'context',meeting_id:p.meeting_id,source_id:p.id,source_sha256:p.text_sha256,source_url:p.source_url,
    json_pointer:p.json_pointer,anchor_label:anchor.label,source_phrase:anchor.term,match_probes:anchor.probes,visible_in_quick_reader:captured,
    source_excerpt:p.text.slice(Math.max(0,p.text.toLowerCase().indexOf(anchor.term.toLowerCase())-130),p.text.toLowerCase().indexOf(anchor.term.toLowerCase())+anchor.term.length+220)});
 }
 const all=[...positions,...abstentions,...contexts];assert(unique(all.map(x=>x.id)).length===all.length,'Repeated benchmark case ID');
 const publicStats={schema:'un.quick-reader-expanded-benchmark-coverage.v1',source_corpus_sha256:DIGEST,reference_kind:'assistant_provisional_not_owner_confirmed',
  sample_rule:'all 13 previously unaudited transcript-present development meetings, original seven retained as separate prior audit',
  original_meetings:7,additional_meetings:additional.length,all_development_meetings:20,
  additional_source_segments:coverage.reduce((s,x)=>s+x.source_segments,0),original_position_candidates:positions.length,revised_position_candidates:coverage.reduce((s,x)=>s+x.revised_positions,0),
  original_abstention_opportunities:coverage.reduce((s,x)=>s+x.candidate_abstentions,0),sampled_abstentions:abstentions.length,curated_context_anchors:contexts.length,
  meeting_counts:coverage,real_heldout_transcripts_opened:0,network_requests:0};
 const body={schema:'un.quick-reader-adjudication-benchmark.v1',corpus_sha256:DIGEST,selection_seed:SEED,baseline_source_label:'frozen_pre_correction_quick_reader_code_on_same_development_corpus',
  prior_seven:ORIGINAL_SAMPLE.slice(),meetings:current,coverage:publicStats,cases:all,adjudication_status:'pending_user_or_independent_review_provisional_assistant_labels_separate',
  source_policy:'cached_development_only; do not include reserved source records',heldout_transcripts_opened:0};
 const binding=bindingFor(body);
 return {packet:{...body,case_binding_sha256:binding},privateSources,publicStats};
}
const VERDICTS={position:{attribution:['individual_country','collective_or_non_country','uncertain'],stance:['supported_expression','unsupported_or_wrong_object','uncertain']},
 abstention:{abstention:['appropriate_withhold','possible_missed_expression','uncertain']},context:{context:['covered','missed','uncertain']}};
function evaluate(packet,review,{allowHuman=false}={}){
 assert(packet?.schema==='un.quick-reader-adjudication-benchmark.v1'&&packet.corpus_sha256===DIGEST,'Incorrect benchmark packet');
 assert(packet.case_binding_sha256===bindingFor(packet),'Benchmark source/prediction binding corrupted');
 assert(review?.schema==='un.quick-reader-adjudication-choices.v1'&&review.case_binding_sha256===packet.case_binding_sha256,'Review missing source-bound identity');
 assert(review.reviewer_type==='assistant_provisional'||(allowHuman&&review.reviewer_type==='owner_human'),'Human reviews require a separate explicitly authorized source');
 if(review.reviewer_type==='owner_human'){
  assert(review.owner_confirmation===true && typeof review.reviewer_name==='string'&&review.reviewer_name.trim().length>=2,'Human review must identify an affirmative reviewer confirmation');
  assert(typeof review.reviewed_at==='string'&&Number.isFinite(Date.parse(review.reviewed_at)),'Human review requires a timestamp');
 }
 assert(Array.isArray(review.choices),'Review choices missing');
 const catalog=new Map(packet.cases.map(c=>[c.id,c]));const seen=new Set();let assessed=[];
 for(const item of review.choices){
  const spec=catalog.get(item.id);assert(spec&&!seen.has(item.id),'Out-of-set or duplicate review choice');seen.add(item.id);
  assert(item.source_sha256===spec.source_sha256 && item.source_id===spec.source_id,'Source identity/hash mismatch');
  assert(item.labels&&Object.entries(item.labels).length===Object.keys(VERDICTS[spec.kind]).length,'Review must name every task for case');
  for(const [task,allowed] of Object.entries(VERDICTS[spec.kind]))assert(allowed.includes(item.labels[task]),'Unsupported review label '+item.id+' '+task);
  assert(typeof item.note==='string'&&item.note.trim().length>=8,'Every provisional decision requires reasoning');
  assessed.push({case_id:item.id,kind:spec.kind,labels:item.labels,note:item.note});
 }
 const bykind=k=>assessed.filter(x=>x.kind===k);
 const p=bykind('position'),a=bykind('abstention'),c=bykind('context');
 const precision=(rows,label,yes,no)=>{
  const approved=rows.filter(x=>x.labels[label]===yes).length;
  const rejected=rows.filter(x=>x.labels[label]===no).length;
  const uncertain=rows.filter(x=>x.labels[label]==='uncertain').length;
  return {supported:approved,unsupported:rejected,uncertain,reviewed:rows.length,assessable:approved+rejected,
    value:approved+rejected>0?approved/(approved+rejected):null};
 };
 const attribution=precision(p,'attribution','individual_country','collective_or_non_country');
 const stance=precision(p,'stance','supported_expression','unsupported_or_wrong_object');
 const joint=p.filter(x=>x.labels.attribution==='individual_country'&&x.labels.stance==='supported_expression');
 const conditional= p.filter(x=>x.labels.attribution!=='uncertain'&&x.labels.stance!=='uncertain');
 const proposed=new Map(packet.cases.filter(x=>x.kind==='position').map(x=>[x.id,x.current_classification!==null]));
 const revised=p.filter(x=>proposed.get(x.case_id));const revisedAssessed=revised.filter(x=>x.labels.attribution!=='uncertain'&&x.labels.stance!=='uncertain');
 const ctxt=precision(c,'context','covered','missed');const abst=precision(a,'abstention','appropriate_withhold','possible_missed_expression');
 return {schema:'un.quick-reader-adjudication-metrics.v1',development_only:true,reviewer_type:review.reviewer_type,
  binding:packet.case_binding_sha256,scoped_meetings:packet.coverage.additional_meetings,candidates_by_task:{attribution:packet.cases.filter(x=>x.kind==='position').length,
  stance:packet.cases.filter(x=>x.kind==='position').length,context:packet.cases.filter(x=>x.kind==='context').length,abstention:packet.cases.filter(x=>x.kind==='abstention').length},
  attribution_precision:attribution,stance_precision:stance,
  joint_correct:{supported:joint.length,assessable:conditional.length,share:conditional.length?joint.length/conditional.length:null},
  revised_joint_correct:{supported:revisedAssessed.filter(x=>x.labels.attribution==='individual_country'&&x.labels.stance==='supported_expression').length,assessable:revisedAssessed.length,
   share:revisedAssessed.length?revisedAssessed.filter(x=>x.labels.attribution==='individual_country'&&x.labels.stance==='supported_expression').length/revisedAssessed.length:null,
   note:'Same development cases reviewed after observing and correcting errors; not a held-out precision estimate.'},
  context_coverage:ctxt,abstention_correct_withhold_fraction:abst,
  coverage:{reviewed_choices:assessed.length,total_cases:packet.cases.length,unreviewed:packet.cases.length-assessed.length},
  interpretation:'Assistant-provisional judgments are not human gold labels; deliberately selected development units are dependent and not population-level accuracy estimates. Empty denominators are null, not 100%.',
  real_heldout_transcripts_opened:0};
}
function main(){
 const [operation,...args]=process.argv.slice(2);
 if(operation==='prepare'){
  assert(args.length===4,'Usage: prepare DEV_CORPUS PRE_CORRECTION_MEETINGS_JSON CONTEXT_ANCHORS_JSON NEW_DIR');
  const [a,b,c,out]=args;assert(!fs.existsSync(out),'Never overwrite an adjudication packet');
  const raw=JSON.parse(fs.readFileSync(b,'utf8'));const baseline=raw.schema==='un.quick-reader-saved-predictions.v1'?raw:{schema:'un.quick-reader-saved-predictions.v1',corpus_sha256:DIGEST,meetings:raw};
  const r=collect(JSON.parse(fs.readFileSync(a,'utf8')),baseline,JSON.parse(fs.readFileSync(c,'utf8')));
  fs.mkdirSync(out,{recursive:true});for(const [key,value] of Object.entries({benchmark:r.packet,'private-source-evidence':r.privateSources,'public-coverage':r.publicStats}))fs.writeFileSync(path.join(out,key+'.json'),JSON.stringify(value,null,2)+'\n');
  const template={schema:'un.quick-reader-adjudication-choices.v1',case_binding_sha256:r.packet.case_binding_sha256,reviewer_type:'assistant_provisional',choices:[]};
  fs.writeFileSync(path.join(out,'review-template.json'),JSON.stringify(template,null,2)+'\n');console.log(JSON.stringify(r.publicStats));
 }else if(operation==='score'){
  assert(args.length===3||(args.length===4&&args[3]==='--human'),'Usage: score BENCHMARK REVIEW NEW_METRICS.json [--human]');const [bench,review,out]=args;
  assert(!fs.existsSync(out),'No overwrite');let packet=JSON.parse(fs.readFileSync(bench,'utf8'));let labels=JSON.parse(fs.readFileSync(review,'utf8'));
  fs.writeFileSync(out,JSON.stringify(evaluate(packet,labels,{allowHuman:args[3]==='--human'}),null,2)+'\n');console.log(JSON.stringify({saved:out}));
 }else throw Error('Valid commands: prepare, score');
}
if(require.main===module){try{main()}catch(e){console.error(e.stack);process.exitCode=1;}}
module.exports={checked,collect,evaluate,bindingFor,ORIGINAL_SAMPLE,SEED,DIGEST};
