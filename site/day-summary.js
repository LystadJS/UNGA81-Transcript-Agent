/* Deterministic, source-bound day synthesis. Runs locally; no model or network call. */
(function(root){
  'use strict';
  const TextUnits=typeof module!=='undefined'&&module.exports?require('./text-units.js'):root.UNTextUnits;
  const CATALOG=Object.freeze([
    {id:'gaza_ceasefire',label:'Ceasefire in Gaza',patterns:[/\b(?:ceasefire|truce|cessation of hostilities|halt (?:the )?fighting)\b[^.!?]{0,100}\b(?:gaza|palestin|israel)/i,/\b(?:gaza|palestin|israel)[^.!?]{0,100}\b(?:ceasefire|truce|cessation of hostilities|halt (?:the )?fighting)\b/i]},
    {id:'humanitarian_access',label:'Humanitarian access and relief delivery',patterns:[/\b(?:humanitarian access|unimpeded access|aid access|relief (?:access|delivery|corridor)|delivery of (?:humanitarian )?aid)\b/i]},
    {id:'civilian_protection',label:'Protection of civilians in armed conflict',patterns:[/\b(?:protection of civilians|protect civilians|civilian protection|civilian casualties|attacks? on civilians)\b/i]},
    {id:'refugees_displacement',label:'Refugees and forced displacement',patterns:[/\b(?:refugees?|internally displaced|forced displacement|displaced persons?|asylum seekers?)\b/i]},
    {id:'ukraine_war',label:'War in Ukraine',patterns:[/\b(?:war|conflict|aggression|invasion) (?:against|in|of) ukraine\b|\bukrain(?:e|ian)[^.!?]{0,80}\b(?:war|conflict|aggression|invasion|occupation)\b/i]},
    {id:'nuclear_disarmament',label:'Nuclear disarmament and non-proliferation',patterns:[/\b(?:nuclear disarmament|nuclear non-proliferation|nonproliferation of nuclear|nuclear weapons?|nuclear-weapon-free)\b/i]},
    {id:'peacekeeping',label:'United Nations peacekeeping',patterns:[/\b(?:peacekeeping|peacekeepers?|blue helmets?|peace operations?)\b/i]},
    {id:'security_council_reform',label:'Security Council reform',patterns:[/\b(?:security council reform|reform of the security council|security council (?:membership|representation|veto))\b/i]},
    {id:'climate_mitigation',label:'Emissions reduction and climate mitigation',patterns:[/\b(?:emissions? reductions?|reduce (?:greenhouse gas |carbon )?emissions?|climate mitigation|decarboni[sz]ation|net[- ]zero)\b/i]},
    {id:'climate_finance',label:'Climate finance',patterns:[/\b(?:climate finance|climate financing|loss and damage fund|green climate fund|financing for (?:climate|adaptation))\b/i]},
    {id:'climate_adaptation',label:'Climate adaptation and resilience',patterns:[/\b(?:climate adaptation|adaptation finance|climate resilience|resilien(?:ce|t) to climate)\b/i]},
    {id:'sdg_finance',label:'Financing for sustainable development',patterns:[/\b(?:financing for development|development financ(?:e|ing)|sdg financing|sustainable development financ(?:e|ing)|debt architecture)\b/i]},
    {id:'food_security',label:'Food security and hunger',patterns:[/\b(?:food security|food insecurity|zero hunger|famine|acute hunger|malnutrition)\b/i]},
    {id:'global_health',label:'Global health and pandemic preparedness',patterns:[/\b(?:global health|pandemic (?:preparedness|prevention|response)|universal health coverage|public health emergency)\b/i]},
    {id:'education',label:'Access to education',patterns:[/\b(?:access to education|right to education|quality education|education for all|school enrollment)\b/i]},
    {id:'gender_equality',label:'Gender equality and women’s rights',patterns:[/\b(?:gender equality|women'?s rights|rights of women|empowerment of women|women and girls)\b/i]},
    {id:'human_rights_accountability',label:'Human rights accountability',patterns:[/\b(?:human rights violations?|accountability for (?:violations|abuses|atrocities)|international accountability|impunity for)\b/i]},
    {id:'digital_governance',label:'Digital and artificial-intelligence governance',patterns:[/\b(?:artificial intelligence governance|governance of artificial intelligence|ai governance|digital governance|global digital compact|responsible ai)\b/i]},
    {id:'technology_transfer',label:'Technology transfer and the digital divide',patterns:[/\b(?:technology transfer|digital divide|digital inclusion|access to technology|technological capacity)\b/i]},
    {id:'cuba_embargo',label:'Embargo and economic restrictions concerning Cuba',patterns:[/\b(?:cuba|cuban)[^.!?]{0,100}\b(?:embargo|blockade|sanctions?|financial restrictions?)\b/i,/\b(?:embargo|blockade|sanctions?|financial restrictions?)[^.!?]{0,100}\b(?:cuba|cuban)\b/i]},
    {id:'unilateral_sanctions',label:'Unilateral sanctions and coercive measures',patterns:[/\b(?:unilateral coercive measures?|unilateral sanctions?|extraterritorial sanctions?)\b/i]},
    {id:'decolonization',label:'Decolonization and self-determination',patterns:[/\b(?:decoloni[sz]ation|non-self-governing territor|colonial rule|right to self-determination)\b/i]},
    {id:'terrorism',label:'Counter-terrorism policy',patterns:[/\b(?:counter-?terrorism|combat(?:ing)? terrorism|terrorist threats?|terrorism financing)\b/i]},
    {id:'organized_crime',label:'Transnational organized crime',patterns:[/\b(?:transnational organized crime|organised criminal|illicit trafficking networks?)\b/i]},
    {id:'migration',label:'International migration policy',patterns:[/\b(?:safe,? orderly and regular migration|global compact for migration|migration governance|migrant workers?|irregular migration)\b/i]}
  ]);
  const PROPOSAL=/\b(?:call(?:s|ed|ing)? for|urge(?:s|d)?|propose(?:s|d)?|recommend(?:s|ed)?|request(?:s|ed)?|advocate(?:s|d)?|must|should|need(?:s|ed)? to|commit(?:s|ted)? to)\b/i;
  const DISAGREEMENT=/\b(?:oppose(?:s|d)?|reject(?:s|ed)?|object(?:s|ed)? to|condemn(?:s|ed)?|cannot support|do not support|disagree(?:s|d)?|criticize(?:s|d)?|deep concern|serious concern)\b/i;
  const DEVELOPMENT=/\b(?:adopt(?:s|ed)|agree(?:s|d) (?:on|to)|launch(?:es|ed)|sign(?:s|ed)|ratif(?:y|ies|ied)|enter(?:s|ed) into force|establish(?:es|ed)|create(?:s|d)|announce(?:s|d)|suspend(?:s|ed)|withdraw(?:s|n)?|deploy(?:s|ed)|release(?:s|d)|approve(?:s|d))\b/i;
  const CEREMONIAL=/^(?:it is (?:an? )?(?:honou?r|privilege|pleasure)|we (?:congratulate|commend) (?:you|the president)|allow me to congratulate|on behalf of .{0,80},? i (?:congratulate|thank)|i wish (?:you|the assembly) every success|distinguished (?:delegates|colleagues)|excellencies)\b/i;
  const ACTION_OBJECT=/\b(?:call(?:s|ed|ing)? for|propose(?:s|d)?|recommend(?:s|ed)?|urge(?:s|d)?(?: [^.!?]{0,50}? to)?|advocate(?:s|d)?(?: for)?)\s+(?:an? |the )?([^.;!?]{4,100})/i;
  const GENERIC_STOP=/^(?:action|support|efforts?|cooperation|dialogue|peace|implementation|the international community|member states?|all parties|countries)$/i;
  const clean=value=>String(value||'').replace(/\s+/g,' ').trim();
  function safeURL(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&!u.hash?u.href:null;}catch{return null;}}
  function meetingKey(record){return clean(record.meeting_slug||String(record.id||'').split('#')[0]||record.meeting||'unknown');}
  function country(record){const value=clean(record.attribution?.label||record.country);return value&&value!=='Unknown'?value:'Recorded speaker not resolved to a country';}
  function evidence(record,sentence){const id=meetingKey(record);return {record_id:clean(record.id),meeting_id:id,meeting_slug:id,meeting_title:clean(record.meeting)||id,date:clean(record.date)||null,country:country(record),source_url:safeURL(record.source_url),excerpt:clean(sentence).slice(0,500)};}
  function substantive(sentence){return TextUnits.summaryEvidenceSentence(sentence)&&!TextUnits.unclearWording(sentence)&&!CEREMONIAL.test(clean(sentence))&&TextUnits.wordCount(sentence)>=7;}
  function knownTopics(sentence){return CATALOG.filter(topic=>topic.patterns.some(pattern=>pattern.test(sentence)));}
  function derivedTopic(sentence){
    const match=clean(sentence).match(ACTION_OBJECT);if(!match)return null;
    let phrase=match[1].replace(/\b(?:in order to|as soon as possible|immediately)\b/gi,'').replace(/\s+/g,' ').trim();
    phrase=phrase.replace(/^(?:all |greater |further |immediate |urgent )+/i,'').replace(/\s+(?:by|from|while|because|so that)\b.*$/i,'').slice(0,90).trim();
    if(TextUnits.wordCount(phrase)<2||GENERIC_STOP.test(phrase))return null;
    const key=TextUnits.tokens(phrase).map(t=>({cessation:'ceasefire',hostilities:'fighting'}[t]||t)).join('_').slice(0,80);
    return key?{id:'source_'+key,label:phrase.charAt(0).toUpperCase()+phrase.slice(1),derived:true}:null;
  }
  function claim(kind,topic,item){
    const verbs={proposal:'records a proposal or requested action on',disagreement:'records disagreement or concern on',development:'records an explicit development on',position:'discusses'};
    return {kind,text:`${item.country} ${verbs[kind]} ${topic.label}.`,evidence:[item.evidence]};
  }
  function summarizeDay(records,options={}){
    if(!Array.isArray(records))throw Error('Day summary requires transcript records.');
    const date=clean(options.date||records[0]?.date);if(!/^\d{4}-\d{2}-\d{2}$/.test(date))throw Error('Day summary requires one ISO date.');
    const selected=records.filter(r=>r&&r.language==='en'&&r.date===date&&clean(r.text)&&safeURL(r.source_url));
    const meetings=new Map(), buckets=new Map();let procedural=0,ceremonial=0,substantiveSentences=0;
    for(const record of selected){
      const key=meetingKey(record);if(!meetings.has(key))meetings.set(key,{meeting_id:key,title:clean(record.meeting)||key,source_segments:0,substantive_sentences:0,procedural_or_ceremonial_sentences:0,topic_ids:new Set()});
      const meeting=meetings.get(key);meeting.source_segments++;
      for(const sentence of TextUnits.sentences(record.text)){
        if(TextUnits.proceduralSentence(sentence)){procedural++;meeting.procedural_or_ceremonial_sentences++;continue;}
        if(CEREMONIAL.test(clean(sentence))){ceremonial++;meeting.procedural_or_ceremonial_sentences++;continue;}
        if(!substantive(sentence))continue;substantiveSentences++;meeting.substantive_sentences++;
        let topics=knownTopics(sentence);
        if(!topics.length){const derived=derivedTopic(sentence);if(derived)topics=[derived];}
        for(const topic of topics){
          if(!buckets.has(topic.id))buckets.set(topic.id,{id:topic.id,label:topic.label,source_derived:!!topic.derived,items:[]});
          const item={sentence:clean(sentence),country:country(record),meeting_id:key,evidence:evidence(record,sentence)};
          buckets.get(topic.id).items.push(item);meeting.topic_ids.add(topic.id);
        }
      }
    }
    const topics=[...buckets.values()].map(topic=>{
      const unique=[];const seen=new Set();for(const item of topic.items){const k=item.evidence.record_id+'|'+item.sentence;if(!seen.has(k)){seen.add(k);unique.push(item);}}
      const proposals=unique.filter(x=>PROPOSAL.test(x.sentence)).slice(0,6).map(x=>claim('proposal',topic,x));
      const disagreements=unique.filter(x=>DISAGREEMENT.test(x.sentence)).slice(0,6).map(x=>claim('disagreement',topic,x));
      const developments=unique.filter(x=>DEVELOPMENT.test(x.sentence)).slice(0,6).map(x=>claim('development',topic,x));
      const claims=[...proposals,...disagreements];
      if(!claims.length&&unique.length)claims.push(claim('position',topic,unique[0]));
      const participants=[...new Set(unique.map(x=>x.country))].sort();
      const meetingBreakdown=[...new Set(unique.map(x=>x.meeting_id))].sort().map(id=>({meeting_id:id,meeting_slug:id,passages:unique.filter(x=>x.meeting_id===id).length}));
      const segments=new Set(unique.map(x=>x.evidence.record_id)).size;
      return {id:topic.id,label:topic.label,policy_question:topic.label,source_derived:topic.source_derived,coverage:{source_segments:segments,segments,meetings:new Set(unique.map(x=>x.meeting_id)).size,countries:participants.length},participating_countries:participants,participants,meeting_breakdown:meetingBreakdown,meetings:meetingBreakdown,supporting_passages:unique.map(item=>item.evidence),principal_proposals:proposals,proposals,disagreements,claims,consequential_developments:developments,developments};
    }).sort((a,b)=>b.coverage.meetings-a.coverage.meetings||b.coverage.source_segments-a.coverage.source_segments||a.label.localeCompare(b.label));
    const meetingRows=[...meetings.values()].map(m=>{
      const topicIds=[...m.topic_ids].sort();
      return {...m,meeting_slug:m.meeting_id,substantive_passages:m.substantive_sentences,
        topics:topicIds.map(id=>buckets.get(id)?.label).filter(Boolean),topic_ids:topicIds};
    });
    const stats={eligible_english_segments:selected.length,source_segments:selected.length,meetings:meetingRows.length,procedural_sentences:procedural,ceremonial_sentences:ceremonial,procedural_or_ceremonial:procedural+ceremonial,procedural_segments:procedural+ceremonial,substantive_sentences:substantiveSentences,substantive_passages:substantiveSentences,substantive_segments:substantiveSentences};
    const chartTopics=topics.map(topic=>({id:topic.id,label:topic.label}));
    const mappedCountries=[...new Set(topics.flatMap(t=>t.supporting_passages.map(e=>e.country)).filter(value=>value&&value!=='Recorded speaker not resolved to a country'))].sort();
    const dedupeEvidence=rows=>{const seen=new Set();return rows.filter(item=>{const key=clean(item.excerpt).toLocaleLowerCase();if(!key||seen.has(key))return false;seen.add(key);return true;});};
    const distribution=topics.map(topic=>{const evidence=dedupeEvidence(topic.supporting_passages);return {topic_id:topic.id,label:topic.label,value:evidence.length,evidence};});
    const countryCells=mappedCountries.flatMap(country=>topics.map(topic=>{const evidence=topic.supporting_passages.filter(item=>item.country===country);return {country,topic_id:topic.id,value:evidence.length?1:0,evidence};}));
    const meetingCells=meetingRows.flatMap(meeting=>topics.map(topic=>{const evidence=dedupeEvidence(topic.supporting_passages.filter(item=>item.meeting_id===meeting.meeting_id));return {meeting_id:meeting.meeting_id,topic_id:topic.id,value:evidence.length,evidence};}));
    const visualizations={
      topic_distribution:{status:distribution.length?'available':'insufficient',reason:distribution.length?null:'No source-linked substantive topics were identified.',unit:'distinct supporting passages',deduplication:'Exact repeated passage wording counts once per topic.',rows:distribution},
      topic_country_matrix:{status:mappedCountries.length&&topics.length?'available':'insufficient',reason:mappedCountries.length&&topics.length?null:'No topic has a mapped recorded-country attribution.',unit:'recorded country participation (binary presence)',deduplication:'Each country counts at most once per topic. Repeated passages do not increase participation.',countries:mappedCountries,topics:chartTopics,cells:countryCells},
      meeting_topic_overview:{status:meetingRows.length&&topics.length?'available':'insufficient',reason:meetingRows.length&&topics.length?null:'Meeting-topic evidence is unavailable for this collection.',unit:'distinct supporting passages',deduplication:'Exact repeated passage wording counts once within each meeting and topic.',meetings:meetingRows.map(m=>({id:m.meeting_id,label:m.title})),topics:chartTopics,cells:meetingCells}
    };
    return {schema:'un.day-summary.v1',engine:'un.day-summary.v1.1-deterministic-source-bound-charts',date,method:'browser_local_deterministic_topic_and_claim_extraction',methodology:{processing_location:'browser',backend_required:false,network_calls_during_summary:false,data_handling:'Uses the collected English records already held in the browser. It neither uploads transcript text nor changes source records.',topic_method:'A versioned policy-question catalog groups explicit synonyms. Uncatalogued action objects remain narrow source-derived topics.',claim_method:'Templates describe explicit sentence cues and retain the exact supporting passage and source URL.'},stats,sources:{eligible_english_segments:selected.length,meetings:meetingRows.length},noise:{procedural_sentences:procedural,ceremonial_sentences:ceremonial,substantive_sentences:substantiveSentences},meetings:meetingRows,topics,visualizations,coverage_order:topics.map(t=>({topic_id:t.id,label:t.label,...t.coverage})),consequential_developments:topics.flatMap(t=>t.consequential_developments.map(c=>({topic_id:t.id,topic_label:t.label,...c}))),interpretation:{coverage_order:'Ordered by meeting coverage, then distinct source segments. This measures recorded discussion volume, not policy importance.',consequential_developments:'Listed only when source wording contains an explicit action or outcome cue. Inclusion is not an independent verification of the event or a ranking of importance.',attribution:'Country labels are retained source metadata and are not independently authenticated.'},limitations:['Rules can miss implicit subjects, irony and cross-sentence context.','Source-derived topics are narrow action objects and are not merged automatically; this reduces accidental merging of different policy questions.','Every displayed substantive claim must retain its evidence array and source URL.']};
  }
  const api={CATALOG,summarizeDay,build:summarizeDay,safeURL};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNDaySummary=api;
})(typeof globalThis!=='undefined'?globalThis:this);
