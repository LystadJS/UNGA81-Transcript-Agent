/* Provisional, sentence-bound humanitarian discourse labels. No stance inference. */
(function(root){
 'use strict';
 const T=typeof module!=='undefined'&&module.exports?require('./text-units.js'):root.UNTextUnits;
 const METHOD='humanitarian-discourse-v1';
 const LABELS=['requested_action','reported_condition','claimed_implementation'];
 const NAMES={requested_action:'Requested action',reported_condition:'Reported condition',claimed_implementation:'Claimed implementation'};
 const subject=/\b(?:humanitarian access|aid access|unimpeded access|civilian protection|protection of civilians|protect(?:ing)? civilians|humanitarian (?:aid|assistance)|humanitarian personnel)\b/i;
 function attribution(r){
  const m=r.speaker_metadata||{},group=String(m.group||'').trim(),aff=String(m.affiliation_full||m.affiliation||r.country||'Unresolved').trim();
  const opening=String(r.text||'').slice(0,700);
  const collective=group&&!/^(?:national delegation|country delegation|national representative)$/i.test(group)||/\b(?:speak|speaking|deliver(?:ing)? (?:this |the |a )?statement)\b[^.!?]{0,110}\bon behalf of\b/i.test(opening)&&!/\bon behalf of (?:my|our) (?:country|delegation|government)\b/i.test(opening);
  if(collective)return {kind:'collective',label:group?`Group statement: ${group} (source affiliation: ${aff})`:`Collective statement (source affiliation: ${aff}; group not established)`,basis:group?'recorded_group':'explicit_collective_opening'};
  if(/^(?:UN|UN Secretariat|OHCHR|UNHCR|UNICEF|WFP|OCHA|CEIRPP|LAS|EU|SMOM)$/i.test(aff)||/\b(?:coordinator|secretary.general|rapporteur|commissioner)\b/i.test(m.function||''))return {kind:'institutional',label:`Institution / source affiliation: ${aff}`,basis:'recorded_affiliation_or_function'};
  return {kind:r.attribution?.country_status==='registry_mapped'?'country_affiliated':'unresolved',label:`Source affiliation: ${aff} (unverified)`,basis:'recorded_affiliation_only'};
 }
 function classify(r){
  const evidence={};
  T.sentences(r.text||'').forEach((line,index)=>{
   if(!subject.test(line)||!T.summaryEvidenceSentence(line))return;
   if(/\bcivilian protection office\b/i.test(line)||/protection of civilians[.!?]?\s+(?:including[^.!?]{0,100})?must cease/i.test(line))return;
   const requested=/\b(?:call(?:s|ed)? (?:on|upon|for)|demand(?:s|ed)?|urg(?:e|es|ed)|must|should|need(?:s)? to|is (?:essential|required|imperative|necessary)|stress(?:es)? the need|reiterate(?:s)? the (?:importance|need))\b/i.test(line)&&!/\b(?:must not|should not|do not|does not|did not|never|no longer)\b[^.!?]{0,65}(?:facilitate|ensure|protect|grant|allow|call|demand|urge)/i.test(line);
   const condition=/\b(?:restrict(?:ed|ions?)|constrain(?:ed|ts?)|obstruct(?:ed|ion)|disrupt(?:ed|ion)|den(?:ied|ial)|shortages?|blocked|remain(?:s)? (?:severely |deeply )?(?:restricted|critical)|impede(?:s|d)?|violations?|casualties|displacement)\b/i.test(line) && /\b(?:is|are|was|were|has|have|remain(?:s)?|persist(?:s)?|continue(?:s)?|face(?:s)?|suffer(?:s)?|disrupted|impede(?:s|d)|risk(?:s)?|reported)\b/i.test(line);
   const implemented=/\b(?:we|our|my delegation|government|authorities|[A-Z][a-z]+)\b[^.!?]{0,140}\b(?:has|have|had)\s+(?:already\s+)?(?:facilitated|provided|opened|extended|issued|approved|implemented|adopted|established|granted|conducted|supported)|\b(?:government efforts|we|our government|authorities)\b[^.!?]{0,100}\b(?:facilitated|provided|opened|extended|issued|approved|implemented|adopted|established|granted)\b|\b(?:grants|is actively engaged|contributed|have participated|training[^.!?]{0,60}have addressed)\b/i.test(line)&&!/\b(?:will|would|should|must|not|never|alleged)\b/i.test(line);
   for(const [label,hit] of [['requested_action',requested],['reported_condition',condition],['claimed_implementation',implemented]])if(hit){(evidence[label]??=[]);if(evidence[label].length<6)evidence[label].push(index);}
  });
  return {record_id:r.id,text_sha256:r.text_sha256,raw_sha256:r.raw_sha256||null,labels:LABELS.filter(l=>evidence[l]?.length),evidence,attribution:attribution(r)};
 }
 function snapshot(records){return {schema:'un.browser.passage-labels.v1',method:METHOD,status:'automatic_provisional_not_human_reviewed',records:records.map(classify)};}
 function validate(corpus){
  if(corpus.passage_labels!==undefined&&JSON.stringify(corpus.passage_labels)!==JSON.stringify(snapshot(corpus.records)))throw Error('Saved passage labels do not match the retained sources or supported label method. Open the original collection to recompute labels.');
 }
 const api={METHOD,LABELS,NAMES,classify,attribution,snapshot,validate};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNPassageLabels=api;
})(typeof globalThis!=='undefined'?globalThis:this);
