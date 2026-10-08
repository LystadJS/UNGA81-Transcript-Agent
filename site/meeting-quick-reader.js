/* Deterministic, local-only meeting quick read. No external AI or speaker inference. */
(function (root) {
  'use strict';
  const ISSUES = Object.freeze([
    {id:'human_rights',label:'Human rights and accountability',pattern:/\b(?:human rights|civil liberties|civil rights|racial discrimination|accountability|humanitarian law|fundamental freedom|rights violation)\b/i},
    {id:'humanitarian',label:'Humanitarian assistance',pattern:/\b(?:humanitarian|refugees?|displaced persons|food security|relief efforts?|humanitarian access|civilian protection|humanitarian assistance)\b/i},
    {id:'peace_security',label:'Peace and security',pattern:/\b(?:ceasefire|disarmament|peacekeeping|armed conflict|nuclear weapon|nuclear disarmament|security council|military intervention|peace process)\b/i},
    {id:'development',label:'Development and economic cooperation',pattern:/\b(?:sustainable development|economic development|technical assistance|financing|poverty|public infrastructure|economic growth|education|trade cooperation|development cooperation)\b/i},
    {id:'climate',label:'Climate and the environment',pattern:/\b(?:climate change|climate action|greenhouse gas|biodiversity|renewable energy|environmental protection|energy transition|emissions)\b/i},
    {id:'technology',label:'Technology and AI',pattern:/\b(?:artificial intelligence|machine learning|digital governance|cybersecurity|data protection|digital transformation|technology transfer)\b/i},
    {id:'institutions',label:'UN institutions and international rules',pattern:/\b(?:multilateralism|international law|treaty bodies|institutional reform|international cooperation|un resolution|treaty implementation)\b/i},
    {id:'sanctions',label:'Sanctions and economic restrictions',pattern:/\b(?:sanctions?|embargo(?:es)?|economic blockade|financial restrictions)\b/i}
  ]);
  const SKIP = /^(?:(?:thank you|i thank|i now (?:give|invite)|the meeting is (?:called|adjourned)|the floor is (?:given|yours)|we shall now|next speaker|i (?:give|yield) the floor|good (?:morning|afternoon))\b)/i;
  const FIRST = /\b(?:we|our delegation|my delegation|our government|my government|our country|i)\b/i;
  const POSITIVE = /\b(?:support|endorse|welcome|call for|urge|advocate|favor|favour|commit to|back the|stand behind)\b/i;
  const NEGATIVE = /\b(?:oppose|reject|object to|condemn|deep concern|serious concern|deplore|cannot support|do not support|are against)\b/i;
  const NEGATION = /\b(?:do not|don't|cannot|can't|never|not)\s+(?:fully\s+)?(?:support|endorse|welcome|back|favor|favour)\b/i;
  const ALLOW = /^https:\/\/transcripts\.un\.org(?:\/|$)/i;
  const wordCount = text => (String(text||'').match(/\S+/g)||[]).length;
  const sentences = text => String(text||'').replace(/\s+/g,' ').trim().split(/(?<=[.!?])\s+(?=[\p{Lu}\d"“])/u).filter(Boolean).slice(0,350);
  const trimmed = value => typeof value==='string' ? value.trim().slice(0,240) : '';
  const safeURL = value => {
    try {const url=new URL(value);return ALLOW.test(url.href)&&!url.username&&!url.password&&!url.hash?url.href:null;}
    catch {return null;}
  };
  function role(record){
    const s=record.speaker_metadata||{};
    const fn=String(s.function||'').toLowerCase();
    const group=String(s.group||'').toLowerCase();
    if (/\b(?:press|journalist|media)\b/.test(fn+' '+group)) return 'press';
    if (/\b(?:non.governmental|ngo|civil society)\b/.test(group+' '+fn)) return 'civil_society';
    // President of a country is NOT the chair of a UN meeting. An ambiguous
    // bare "President" is withheld rather than assigned a governmental stance.
    if (/^(?:president|national president)$/.test(fn.trim())) return 'unresolved';
    if (/\b(?:chair|chairperson|moderator|vice.president|secretariat|presiding|rapporteur|high commissioner|spokesperson|pga)\b/.test(fn) ||
        /president of (?:the )?(?:security council|general assembly|human rights council|committee)/.test(fn)) return 'presiding_or_official';
    if (record.attribution?.country_status==='registry_mapped') return 'country_affiliated';
    return 'unresolved';
  }
  function speakerEvidence(record){
    const s=record.speaker_metadata||{};
    const a=trimmed(s.affiliation_full||s.affiliation), fn=trimmed(s.function), name=trimmed(s.name);
    const proxy=a&&fn?[a.toLowerCase(),fn.toLowerCase()]:null;
    return {recorded_name:name||null,recorded_affiliation:a||null,recorded_function:fn||null,
      speaker_identity_observed:!!trimmed(s.id),speaker_proxy:proxy,role:role(record)};
  }
  function agendaSeries(meetingId,title){
    const path=String(meetingId||'').split('/');
    if(path[0]==='ga'&&/^c[1-6]$/.test(path[1]||''))return {series:'ga:'+path[1],basis:'source_path',label:'General Assembly '+path[1].toUpperCase()+' committee'};
    if(path[0]==='ga')return {series:'ga:plenary',basis:'source_path',label:'General Assembly plenary'};
    if(path[0]==='hrc'&&/^\d+$/.test(path[1]||''))return {series:'hrc:'+path[1],basis:'source_path',label:'Human Rights Council session '+path[1]};
    if(path[0]==='asset')return {series:null,basis:'not_established',label:'Agenda series not established'};
    return {series:null,basis:'meeting_title_only',label:trimmed(title)||'Agenda series not established'};
  }
  function isSubstantive(text){return wordCount(text)>=12 && !SKIP.test(String(text).trim())};
  function stance(sentence,issue){
    // The first-person actor, an evaluative action, and the topic must occur in
    // the same clause. Quoted assertions or third-party descriptions are withheld.
    const pieces=sentence.split(/[,;:]|\b(?:but|however|although)\b/i);
    const candidates=[];
    for(const piece of pieces){
      const part=piece.trim();if(!issue.pattern.test(part))continue;
      const actor=part.match(/^(?:we|i|our delegation|my delegation|our government|my government|our country)\b\s*/i);
      if(!actor)continue;
      const action=part.slice(actor[0].length).match(/^(?:(?:strongly|fully|firmly|clearly|also|continue to|repeatedly|deeply)\s+){0,3}(do not support|cannot support|are against|express concern|are concerned|have concerns|stand behind|call for|commit to|object to|endorse|support(?:s)?|welcome(?:s)?|urge(?:s)?|advocate(?:s)?|favor(?:s)?|favour(?:s)?|oppose(?:s)?|reject(?:s)?|condemn(?:s)?|deplore(?:s)?|back(?:s)?)\b/i);
      if(!action)continue;
      const verb=action[1].toLowerCase();
      candidates.push(/^(?:do not|cannot|are against|express concern|are concerned|have concerns|object to|oppose|reject|condemn|deplore)/.test(verb)?'concern_or_opposition_expressed':'support_or_advocacy_expressed');
    }
    return new Set(candidates).size>1?'qualified_or_mixed':(candidates[0]||null);
  }
  function build(records, options={}){
    if(!Array.isArray(records))throw Error('Quick reader requires original meeting records.');
    const slug=String(options.meeting_slug||'');
    if(!slug||!/^[-\w]+(?:\/[-\w]+){1,5}$/.test(slug))throw Error('A validated single meeting identity is required.');
    const selected=records.filter(r=>r&&r.language==='en'&&(r.meeting_slug||String(r.id||'').split('#')[0])===slug);
    const counted=new Set(),verified=selected.filter(r=>r.attribution?.country_status==='registry_mapped'&&r.region!=='Unmapped');
    verified.forEach(r=>counted.add(r.country));
    const counts=new Map(ISSUES.map(i=>[i.id,{...i,count:0,evidence:[]}]));
    const positionIndex=new Map();let substantive=0,unknown=0,words=[],withSpeakerId=0,withSpeakerProxy=0;
    for(const record of selected){
      const text=String(record.text||'');words.push(wordCount(text));
      const speaker=speakerEvidence(record);if(speaker.speaker_identity_observed)withSpeakerId++;if(speaker.speaker_proxy)withSpeakerProxy++;
      if(record.attribution?.country_status!=='registry_mapped')unknown++;
      if(!isSubstantive(text))continue;
      substantive++;
      const lines=sentences(text);
      for(const issue of ISSUES){
        const hits=lines.filter(s=>issue.pattern.test(s));
        if(!hits.length)continue;
        const bucket=counts.get(issue.id);bucket.count++;
        if(bucket.evidence.length<2 && safeURL(record.source_url))bucket.evidence.push({record_id:record.id,source_url:safeURL(record.source_url),excerpt:hits[0].slice(0,240)});
        if(record.attribution?.country_status!=='registry_mapped'||record.region==='Unmapped'||role(record)!=='country_affiliated')continue;
        for(const line of hits){
          // Do not promote issue co-occurrence or reported third-party views to a country stance.
          if(!FIRST.test(line))continue;
          const detected=stance(line,issue);
          if(!detected)continue;
          const key=record.country+'\0'+issue.id;
          const existing=positionIndex.get(key)||{country:record.country,issue:issue.label,issue_id:issue.id,labels:new Set(),evidence:[],source_segments:new Set()};
          existing.labels.add(detected);existing.source_segments.add(record.id);
          if(existing.evidence.length<2&&safeURL(record.source_url))existing.evidence.push({record_id:record.id,source_url:safeURL(record.source_url),excerpt:line.slice(0,260)});
          positionIndex.set(key,existing);
        }
      }
    }
    const themes=[...counts.values()].filter(x=>x.count>0).sort((a,b)=>b.count-a.count||a.label.localeCompare(b.label));
    const positions=[...positionIndex.values()].map(v=>({country:v.country,issue:v.issue,issue_id:v.issue_id,
      classification:v.labels.size>1||v.labels.has('qualified_or_mixed')?'mixed_or_qualified':[...v.labels][0],
      source_segment_count:v.source_segments.size,evidence:v.evidence}))
      .sort((a,b)=>a.country.localeCompare(b.country)||a.issue.localeCompare(b.issue));
    const sortedWords=words.slice().sort((a,b)=>a-b);
    const median=sortedWords.length?(sortedWords.length%2?sortedWords[(sortedWords.length-1)/2]:(sortedWords[sortedWords.length/2-1]+sortedWords[sortedWords.length/2])/2):null;
    const recorded=selected.length, date=options.meeting_date||selected[0]?.date||null;
    const title=trimmed(options.title||selected[0]?.meeting||'Individual meeting');
    const topic=themes.slice(0,2).map(x=>x.label.toLowerCase());
    const prose=themes.length?
      [`The available English record most often addresses ${topic.join(' and ')}. This is a description of recurring language in ${substantive} substantive-looking source segments, not a finding about the meeting's formal decisions.`,
       positions.length?`The transcript contains ${positions.length} issue-level expressions of support, concern, or qualification attributed to ${new Set(positions.map(p=>p.country)).size} countries. The table links each provisional classification to its recorded wording; it does not establish a government-wide position or meeting consensus.`:
       'The available wording does not support a reliable country-position summary. The source passages below remain available for attribution and substantive review.']:
      ['The available English record does not identify a recurring substantive subject under the fixed issue dictionary. A missing theme is not evidence that an issue was absent from the meeting.',
       'No country position is classified without an attributed first-person statement on a specific issue. Source limitations and unresolved affiliations remain visible below.'];
    return {schema:'un.meeting-quick-reader.v1',method:'offline_deterministic_extract_with_source_links',single_meeting:true,meeting_slug:slug,meeting_date:date,meeting_title:title,agenda:agendaSeries(slug,title),
      sources:'all_english_source_segments_in_exact_selected_meeting_before_topic_filter',
      stats:{source_segments:recorded,substantive_looking_segments:substantive,median_words_per_segment:median,mapped_country_segments:verified.length,unresolved_country_segments:unknown,recorded_countries:counted.size,records_with_explicit_speaker_id:withSpeakerId,records_with_affiliation_function_proxy:withSpeakerProxy,explicit_issue_country_positions:positions.length},
      paragraphs:prose,themes:themes.map(({id,label,count,evidence})=>({id,label,segments:count,evidence})).slice(0,6),positions,
      limitations:['Automatic UN transcripts and recorded speaker metadata are not independently authenticated.','One source segment is not necessarily one speaker or a complete speech; affiliation and function are not person identifiers.','Country affiliation and first-person language are provisional attribution, not verified governmental stance.','Keyword themes and short stance cues are rule-based and should be checked against original context.','Topic-filtered figures below may use fewer passages than this all-meeting quick read.'],
      external_ai_calls:0};
  }
  const api={build,agendaSeries,speakerEvidence,role,safeURL,ISSUES};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNMeetingQuickReader=api;
})(typeof globalThis!=='undefined'?globalThis:this);
