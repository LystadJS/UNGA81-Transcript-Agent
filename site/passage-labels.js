/* Provisional, source-bound humanitarian discourse labels. No stance inference. */
(function(root){
 'use strict';
 const T=typeof module!=='undefined'&&module.exports?require('./text-units.js'):root.UNTextUnits;
 const METHOD='humanitarian-discourse-v3';
 const LABELS=['requested_action','reported_condition','claimed_implementation'];
 const NAMES={requested_action:'Requested action',reported_condition:'Reported condition',claimed_implementation:'Claimed implementation'};
 const legacySubject=/\b(?:humanitarian access|aid access|unimpeded access|civilian protection|protection of civilians|protect(?:ing)? civilians|humanitarian (?:aid|assistance)|humanitarian personnel)\b/i;
 function legacyAttribution(r){
  const m=r.speaker_metadata||{},group=String(m.group||'').trim(),aff=String(m.affiliation_full||m.affiliation||r.country||'Unresolved').trim();
  const opening=String(r.text||'').slice(0,700);
  const collective=group&&!/^(?:national delegation|country delegation|national representative)$/i.test(group)||/\b(?:speak|speaking|deliver(?:ing)? (?:this |the |a )?statement)\b[^.!?]{0,110}\bon behalf of\b/i.test(opening)&&!/\bon behalf of (?:my|our) (?:country|delegation|government)\b/i.test(opening);
  if(collective)return {kind:'collective',label:group?`Group statement: ${group} (source affiliation: ${aff})`:`Collective statement (source affiliation: ${aff}; group not established)`,basis:group?'recorded_group':'explicit_collective_opening'};
  if(/^(?:UN|UN Secretariat|OHCHR|UNHCR|UNICEF|WFP|OCHA|CEIRPP|LAS|EU|SMOM)$/i.test(aff)||/\b(?:coordinator|secretary.general|rapporteur|commissioner)\b/i.test(m.function||''))return {kind:'institutional',label:`Institution / source affiliation: ${aff}`,basis:'recorded_affiliation_or_function'};
  return {kind:r.attribution?.country_status==='registry_mapped'?'country_affiliated':'unresolved',label:`Source affiliation: ${aff} (unverified)`,basis:'recorded_affiliation_only'};
 }
 function legacyClassify(r){
  const evidence={};
  T.sentences(r.text||'').forEach((line,index)=>{
   if(!legacySubject.test(line)||!T.summaryEvidenceSentence(line))return;
   if(/\bcivilian protection office\b/i.test(line)||/protection of civilians[.!?]?\s+(?:including[^.!?]{0,100})?must cease/i.test(line))return;
   const requested=/\b(?:call(?:s|ed)? (?:on|upon|for)|demand(?:s|ed)?|urg(?:e|es|ed)|must|should|need(?:s)? to|is (?:essential|required|imperative|necessary)|stress(?:es)? the need|reiterate(?:s)? the (?:importance|need))\b/i.test(line)&&!/\b(?:must not|should not|do not|does not|did not|never|no longer)\b[^.!?]{0,65}(?:facilitate|ensure|protect|grant|allow|call|demand|urge)/i.test(line);
   const condition=/\b(?:restrict(?:ed|ions?)|constrain(?:ed|ts?)|obstruct(?:ed|ion)|disrupt(?:ed|ion)|den(?:ied|ial)|shortages?|blocked|remain(?:s)? (?:severely |deeply )?(?:restricted|critical)|impede(?:s|d)?|violations?|casualties|displacement)\b/i.test(line) && /\b(?:is|are|was|were|has|have|remain(?:s)?|persist(?:s)?|continue(?:s)?|face(?:s)?|suffer(?:s)?|disrupted|impede(?:s|d)|risk(?:s)?|reported)\b/i.test(line);
   const implemented=/\b(?:we|our|my delegation|government|authorities|[A-Z][a-z]+)\b[^.!?]{0,140}\b(?:has|have|had)\s+(?:already\s+)?(?:facilitated|provided|opened|extended|issued|approved|implemented|adopted|established|granted|conducted|supported)|\b(?:government efforts|we|our government|authorities)\b[^.!?]{0,100}\b(?:facilitated|provided|opened|extended|issued|approved|implemented|adopted|established|granted)\b|\b(?:grants|is actively engaged|contributed|have participated|training[^.!?]{0,60}have addressed)\b/i.test(line)&&!/\b(?:will|would|should|must|not|never|alleged)\b/i.test(line);
   for(const [label,hit] of [['requested_action',requested],['reported_condition',condition],['claimed_implementation',implemented]])if(hit){(evidence[label]??=[]);if(evidence[label].length<6)evidence[label].push(index);}
  });
  return {record_id:r.id,text_sha256:r.text_sha256,raw_sha256:r.raw_sha256||null,labels:LABELS.filter(l=>evidence[l]?.length),evidence,attribution:legacyAttribution(r)};
 }

 // Legacy rules remain frozen solely to authenticate existing v1 snapshots.
 function legacySnapshot(records){return {schema:'un.browser.passage-labels.v1',method:'humanitarian-discourse-v1',status:'automatic_provisional_not_human_reviewed',records:records.map(legacyClassify)};}
 function attribution(r){
  const m=r.speaker_metadata||{},group=String(m.group||'').trim(),aff=String(m.affiliation_full||m.affiliation||r.country||'Unresolved').trim();
  const opening=String(r.text||'').slice(0,1000);
  const nationalGroup=/^(?:national delegation|country delegation|national representative)$/i.test(group);
  const delivery=/\b(?:i|we|my delegation|our delegation)\s+(?:(?:have|has) the honou?r (?:to|of)\s+|am (?:honou?red|privileged) to\s+|will\s+)?(?:speak|speaking|deliver(?:ing)? (?:this |the |a )?statement|take the floor)\b[^.!?]{0,100}\bon behalf of\s+([^.!?]{1,180})/i.exec(opening);
  const own=delivery&&/^(?:(?:my|our) (?:country|delegation|government)|the (?:republic|kingdom|state) of\b)/i.test(delivery[1].trim());
  const explicitGroup=delivery&&!own;
  const national=!!own||/\b(?:in (?:my|our|its|their|a) national capacity|(?:remarks|statement) in (?:my|our|its|their) national capacity)\b/i.test(opening);
  const recordedGroup=group&&!nationalGroup;
  if(national&&(explicitGroup||recordedGroup))return {kind:'mixed_or_ambiguous',label:`Mixed or conflicting group / national attribution (source affiliation: ${aff}${recordedGroup?'; recorded group: '+group:''})`,basis:'conflicting_national_and_collective_cues'};
  if(recordedGroup||explicitGroup)return {kind:'collective',label:recordedGroup?`Group statement: ${group} (source affiliation: ${aff})`:`Collective statement (source affiliation: ${aff}; group not established)`,basis:recordedGroup?'recorded_group':'explicit_collective_opening'};
  if(/^(?:UN|United Nations|UN Secretariat|OHCHR|UNHCR|UNICEF|WFP|OCHA|CEIRPP|LAS|EU|SMOM)$/i.test(aff)||/\b(?:coordinator|secretary.general|rapporteur|commissioner)\b/i.test(m.function||''))return {kind:'institutional',label:`Institution / source affiliation: ${aff}`,basis:'recorded_affiliation_or_function'};
  return {kind:r.attribution?.country_status==='registry_mapped'?'country_affiliated':'unresolved',label:`Source affiliation: ${aff} (unverified)`,basis:national?'explicit_national_capacity_and_source_affiliation':'recorded_affiliation_only'};
 }
 function relevant(line){
  // Detention monitoring is not relief access. An institution or document name
  // alone is not an operational protection statement.
  if(/\b(?:detainees?|prisoners? of war|detention|POWs?)\b/i.test(line)&&!/\b(?:humanitarian access|protect(?:ing)? civilians|protection of civilians|civilian protection)\b/i.test(line))return false;
  if(/\bcivilian protection office\b/i.test(line))return false;
  return /\b(?:humanitarian access|aid access|unimpeded access|civilian protection|protection of civilians|protect(?:ing)? civilians|safety of (?:humanitarian|medical) personnel|protection of humanitarian personnel|access for humanitarian assistance)\b/i.test(line)||
   /\b(?:humanitarian (?:aid|assistance))\b[^.!?]{0,100}\b(?:unhindered|unimpeded|without obstruction|reach civilians safely|reach those in need safely)\b/i.test(line)||
   /\b(?:unhindered|unimpeded) (?:(?:delivery|provision|entry|flow) of )?(?:humanitarian (?:aid|assistance))\b/i.test(line)||/\b(?:allow|facilitate)\b[^.!?]{0,40}\bentry of humanitarian (?:aid|assistance)\b|\bprotection of\b[^.!?]{0,65}\bhumanitarian personnel\b/i.test(line);
 }
 function cues(line){
  const unclear=/\b(?:guarantee an impeded humanitarian access|protection of civilians[.!?]?\s+(?:including[^.!?]{0,100})?must cease|multiple for safe)\b/i.test(line);
  if(unclear)return {requested:false,condition:false,implemented:false,flag:'unclear_transcript_wording'};
  const reportedAppeal=/\b(?:the declaration|the resolution|the report)\b[^.!?]{0,100}\b(?:calls? (?:on|for)|called on|recommends?)\b|\b(?:it|the resolution|the report|the declaration)\s+(?:also\s+)?(?:call(?:s|ed)? (?:on|for)|recommend(?:s|ed)?)\b|\b(?:reports? contain[^.!?]{0,50}recommendations|launched a call to action)\b/i.test(line);
  const completed=/\b(?:has|have|had)\s+(?:already\s+)?(?:facilitated|provided|opened|extended|issued|approved|implemented|adopted|established|granted|conducted|organized|amended|enacted|acceded|subscribed)|\b(?:government efforts|we|our government|authorities|[A-Z][a-z]+)\b[^.!?]{0,180}\b(?:facilitated|provided|opened|extended|issued|approved|implemented|adopted|established|granted|organized|amended|enacted|submitted)\b|\b(?:contributed[^.!?]{0,120}(?:submitting|amendments)|training[^.!?]{0,60}have addressed|have participated)\b/i.test(line);
  const requested=!reportedAppeal&&(/\b(?:call(?:s|ing)? (?:on|upon|for)|demand(?:s)?|urg(?:e|es)|must|should|need(?:s)? to|(?:urgent |pressing )?need for|(?:is|it|thus|more|also) (?:essential|required|imperative|necessary)|considers? it essential|(?:stress(?:es)?|reiterate(?:s)?|emphasize(?:s)?|underline(?:s)?) (?:the |its |our )?(?:critical )?(?:importance|imperative|need)|cannot wait)\b/i.test(line)||/^(?:first|second|third|fourth)[,:.]?\s+[^.!?]{0,50}\b(?:safe|unhindered)\b[^.!?]{0,40}\bhumanitarian access\b/i.test(line))&&
   !/\b(?:do not|does not|did not|never|no longer)\b[^.!?]{0,65}(?:call|demand|urge)\b|\b(?:must not|should not)\s+(?:ensure|protect|grant|allow|facilitate)\b/i.test(line)&&
   !(completed&&/\b(?:organized|conducted)\b[^.!?]{0,120}\b(?:conference|training|workshop)\b/i.test(line)&&!/\b(?:we call|we urge|we demand|must|should)\b/i.test(line));
  const denial=/\b(?:never|not|no longer)\s+(?:been\s+)?(?:obstructed|restricted|blocked|denied|impeded)\b/i.test(line);
  const observed=/\b(?:restrict(?:ed|ions?)|constrain(?:ed|ts?)|obstruct(?:ed|ion)|disrupt(?:ed|ion)|den(?:ied|ial)|shortages?|blocked|casualties|displacement)\b/i.test(line)&&
   /\b(?:remains?|persist(?:s)?|continu(?:e|es|ed|ing)|face(?:s)?|suffer(?:s)?|disrupted|imped(?:e|es|ed)|risk(?:s)?|demonstrate(?:s)?|express (?:grave |deep )?concern|is still not delivering)\b/i.test(line)||
   /\b(?:violations? (?:deal|have dealt)|(?:humanitarian access|aid access) (?:is|was|has been) (?:severely )?(?:restricted|blocked|denied|obstructed))\b/i.test(line)||
   /\bis still not delivering\b[^.!?]{0,140}\bhumanitarian access\b/i.test(line);
  const condition=!denial&&observed&&!(/\b(?:must|should|need to|we call|we urge)\b/i.test(line)&&!/\b(?:restrictions?[^.!?]{0,60}(?:persist|continue|have disrupted)|access (?:remains?|continues?)|express (?:grave |deep )?concern|violations? (?:deal|have dealt))\b/i.test(line));
  const implemented=completed&&!reportedAppeal&&!/\b(?:will|would|should|must|not|never|alleged)\b/i.test(line);
  return {requested,condition,implemented,flag:reportedAppeal?'reported_or_quoted_appeal':null};
 }
 function classifyV2(r){
  const evidence={},review_flags=[];
  T.sentences(r.text||'').forEach((line,index)=>{
   if(!relevant(line)){if(/\b(?:unimpeded access|civilian protection office)\b/i.test(line))review_flags.push({sentence_index:index,reason:/civilian protection office/i.test(line)?'institution_name_only':'detention_monitoring_not_relief_access'});return;}
   if(!T.summaryEvidenceSentence(line))return;
   const c=cues(line);
   if(c.flag)review_flags.push({sentence_index:index,reason:c.flag});
   for(const [label,hit] of [['requested_action',c.requested],['reported_condition',c.condition],['claimed_implementation',c.implemented]])if(hit){evidence[label]??=[];if(evidence[label].length<6)evidence[label].push(index);}
  });
  return {record_id:r.id,text_sha256:r.text_sha256,raw_sha256:r.raw_sha256||null,labels:LABELS.filter(l=>evidence[l]?.length),evidence,review_flags,attribution:attribution(r)};
 }
 // Recording checks are machine-assisted audit notes, never human verification.
 // Hash binding prevents a note being applied to a changed or unrelated source.
 const recordingChecks={
  'dfe96db716110b297a3f935e1e89e45794d7083437833d96eef5a948417796fc':{id:'sc/10243/2#1',raw:'0e97df3478d02d45e993c225530fc98209fe3450669047f33a515b1f29ca8b21',url:'https://webtv.un.org/en/asset/k1m/k1mlfdvxdy',seconds:449,timing:'recording_excerpt_located',note:'Local speech models disagree on the unclear civilian-protection wording. No replacement wording is established. Do not quote this sentence as a protection demand.'},
  '20d504cebb5587fc04b8ef8d86b6371a71852f0e2d0e09659a2509bb834f5f57':{id:'ga/c3/81/19#28',raw:'08a8b30cd51482885ccfad00d2a7095a587d6536acb377511754edcb7054e355',url:'https://webtv.un.org/en/asset/k1g/k1gmea6hwe',seconds:2961,timing:'shortened_recording_original_timestamp_unreliable',note:'The source warns that the recording was shortened after transcription. The speech was located separately in the English recording. The access modifier remains unresolved; no replacement wording is established.'},
  'aaff5e0a27a1a9c930c1c3b3a7321dae1f982f026775bb28447be44c24bdf4ec':{id:'ga/c3/81/19#90',raw:'08a8b30cd51482885ccfad00d2a7095a587d6536acb377511754edcb7054e355',url:'https://webtv.un.org/en/asset/k1g/k1gmea6hwe',seconds:7642,timing:'shortened_recording_original_timestamp_unreliable',note:'The source warns that the recording was shortened after transcription. The speech was located separately in the English recording. The malformed action wording remains unresolved; no replacement wording is established.'}
 };
 function classify(r){
  const result=classifyV2(r),check=recordingChecks[r.text_sha256];
  if(check&&r.id===check.id&&r.raw_sha256===check.raw)result.recording_review={status:'unresolved_machine_assisted_not_human_verified',checked_at:'2026-10-19',recording_url:check.url,approximate_recording_seconds:check.seconds,timing_status:check.timing,note:check.note,correction_applied:false,original_preserved:true,method:'Local English-track ASR; base.en, small.en and medium.en. Model disagreement is not a verified correction.'};
  return result;
 }
 function v2Snapshot(records){return {schema:'un.browser.passage-labels.v1',method:'humanitarian-discourse-v2',status:'automatic_provisional_not_human_reviewed',records:records.map(classifyV2)};}
 function snapshot(records){return {schema:'un.browser.passage-labels.v1',method:METHOD,status:'automatic_provisional_not_human_reviewed',records:records.map(classify)};}
 function validate(corpus){
  if(corpus.passage_labels===undefined)return;
  const saved=corpus.passage_labels;
  const expected=saved.method==='humanitarian-discourse-v1'?legacySnapshot(corpus.records):saved.method==='humanitarian-discourse-v2'?v2Snapshot(corpus.records):snapshot(corpus.records);
  if(JSON.stringify(saved)!==JSON.stringify(expected))throw Error('Saved passage labels do not match the retained sources or supported label method. Open the original collection to recompute labels.');
 }
 const api={METHOD,LABELS,NAMES,classify,attribution,snapshot,validate,legacySnapshot,v2Snapshot,cues,relevant};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNPassageLabels=api;
})(typeof globalThis!=='undefined'?globalThis:this);
