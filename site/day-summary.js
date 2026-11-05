/* Deterministic, source-bound day synthesis. Runs locally; no model or network call. */
(function(root){
  'use strict';
  const TextUnits=typeof module!=='undefined'&&module.exports?require('./text-units.js'):root.UNTextUnits;
  const CATALOG=Object.freeze([
    {id:'gaza_ceasefire',label:'Ceasefire in Gaza',patterns:[/\b(?:ceasefire|truce|cessation of hostilities|halt (?:the )?fighting)\b[^.!?]{0,100}\b(?:gaza|palestin|israel)/i,/\b(?:gaza|palestin|israel)[^.!?]{0,100}\b(?:ceasefire|truce|cessation of hostilities|halt (?:the )?fighting)\b/i]},
    {id:'humanitarian_access',label:'Humanitarian access and relief delivery',patterns:[/\b(?:humanitarian access|humanitarian assistance|unimpeded access|unhindered access|aid access|relief (?:access|delivery|corridor)|delivery of (?:humanitarian )?aid|supply of humanitarian aid)\b/i]},
    {id:'civilian_protection',label:'Protection of civilians in armed conflict',patterns:[/\b(?:protection of civilians|protect civilians|civilian protection|civilian casualties|attacks? on civilians)\b/i]},
    {id:'refugees_displacement',label:'Refugees and forced displacement',patterns:[/\b(?:refugees?|internally displaced|forced displacement|displaced persons?|asylum seekers?)\b/i]},
    {id:'ukraine_war',label:'War in Ukraine',patterns:[/\b(?:war|conflict|aggression|invasion) (?:against|in|of) ukraine\b|\bukrain(?:e|ian)[^.!?]{0,80}\b(?:war|conflict|aggression|invasion|occupation)\b/i]},
    {id:'iran_nuclear_compliance',label:'Iranian nuclear safeguards and non-proliferation compliance',patterns:[/\biran(?:ian)?\b[^.!?]{0,140}\b(?:iaea|safeguards?|non-?compliance|non-?proliferation|nuclear (?:weapons?|programme|program)|resolution 2231|1737 (?:committee|panel))\b/i,/\b(?:iaea|safeguards?|non-?compliance|non-?proliferation|nuclear (?:weapons?|programme|program)|resolution 2231|1737 (?:committee|panel))\b[^.!?]{0,140}\biran(?:ian)?\b/i]},
    {id:'nuclear_safeguards',label:'Nuclear safeguards and cooperation with the IAEA',patterns:[/\b(?:iaea|international atomic energy agency)\b[^.!?]{0,150}\b(?:safeguards?|obligations?|cooperat|negotiated solution)\b/i,/\b(?:safeguards?|obligations?|cooperat|negotiated solution)\b[^.!?]{0,150}\b(?:iaea|international atomic energy agency)\b/i]},
    {id:'nuclear_disarmament',label:'Nuclear disarmament and non-proliferation',patterns:[/\b(?:nuclear disarmament|nuclear non-proliferation|nonproliferation of nuclear|nuclear weapons?|nuclear-weapon-free|nuclear arsenals?|nuclear powers?)\b/i]},
    {id:'haiti_security_mission',label:'Haiti security mission and Gang Suppression Force',patterns:[/\b(?:haiti|haitian|gang suppression force|\bgsf\b)[^.!?]{0,220}\b(?:gang suppression force|\bgsf\b|security mission|contingents?|deployment|mandate|national police|capacity building|national governance|protecting its people)\b/i,/\b(?:gang suppression force|\bgsf\b|security mission|contingents?|deployment|mandate|national police|capacity building|national governance|protecting its people)\b[^.!?]{0,220}\b(?:haiti|haitian)\b/i]},
    {id:'drc_peace_process',label:'Conflict and peace process in the Democratic Republic of the Congo',patterns:[/\b(?:democratic republic of the congo|\bdrc\b|congolese|monusco|fdlr)\b[^.!?]{0,260}\b(?:armed groups?|ceasefire|disarmament|doha|washington|peace process|verification|monitoring of commitments|civic space|human rights defenders?)\b/i,/\b(?:armed groups?|ceasefire|disarmament|doha|washington|peace process|verification|monitoring of commitments|civic space|human rights defenders?)\b[^.!?]{0,260}\b(?:democratic republic of the congo|\bdrc\b|congolese|monusco|fdlr)\b/i]},
    {id:'peacekeeping_troop_participation',label:'Troop participation in United Nations peace operations',patterns:[/\b(?:suspend|suspension|participation|deployment|rotation|withdrawal)\b[^.!?]{0,100}\b(?:contingents?|troops?|peace operations?|peacekeeping)\b/i]},
    {id:'peacekeeping_mandate_resources',label:'Mandates and resources for United Nations peace operations',patterns:[/\b(?:peacekeeping|peace operations?|mission|monusco)\b[^.!?]{0,120}\b(?:mandate|resources?|means|capacity|civilian protection)\b/i,/\b(?:mandate|resources?|means|capacity)\b[^.!?]{0,120}\b(?:peacekeeping|peace operations?|mission|monusco)\b/i]},
    {id:'peacekeeping',label:'United Nations peacekeeping',patterns:[/\b(?:peacekeeping|peacekeepers?|blue helmets?|peace operations?)\b/i]},
    {id:'security_council_veto',label:'Security Council veto use and restraint',patterns:[/\b(?:veto|veto power)\b[^.!?]{0,120}\b(?:abolish|limit|restraint|abuse|exercise|explanation|deadlock)\b/i,/\b(?:abolish|limit|restraint|abuse|exercise|explanation)\b[^.!?]{0,120}\b(?:veto|veto power)\b/i]},
    {id:'security_council_working_methods',label:'Security Council working methods and effectiveness',patterns:[/\b(?:security council|the council)\b[^.!?]{0,130}\b(?:working methods?|disunity|function as intended|note 507|fulfil its mandate|fulfill its mandate)\b/i]},
    {id:'security_council_reform',label:'Security Council membership and representation reform',patterns:[/\b(?:security council reform|reform of the security council|security council (?:membership|representation))\b/i]},
    {id:'un_commemoration_working_methods',label:'United Nations rules for establishing international commemorations',patterns:[/\b(?:international days?|weeks?|months?|years?|commemoration)\b[^.!?]{0,180}\b(?:proclamation requests?|operative paragraph|put on hold|single resolution)\b/i,/\b(?:proclamation requests?|operative paragraph|put on hold|single resolution)\b[^.!?]{0,180}\b(?:international days?|weeks?|months?|years?|commemoration)\b/i]},
    {id:'un_meeting_mandates',label:'United Nations mandates for thematic and commemorative meetings',patterns:[/\b(?:new mandates?|mandated meetings?)\b[^.!?]{0,180}\b(?:overlap|thematic|commemorative|number of high-level)\b/i]},
    {id:'climate_mitigation',label:'Emissions reduction and climate mitigation',patterns:[/\b(?:emissions? reductions?|reduce (?:greenhouse gas |carbon )?emissions?|climate mitigation|decarboni[sz]ation|net[- ]zero)\b/i]},
    {id:'climate_finance',label:'Climate finance',patterns:[/\b(?:climate finance|climate financing|loss and damage fund|green climate fund|financing for (?:climate|adaptation))\b/i]},
    {id:'climate_adaptation',label:'Climate adaptation and resilience',patterns:[/\b(?:climate adaptation|adaptation finance|climate resilience|resilien(?:ce|t) to climate)\b/i]},
    {id:'sdg_finance',label:'Financing for sustainable development',patterns:[/\b(?:financing for development|development financ(?:e|ing)|sdg financing|sustainable development financ(?:e|ing)|debt architecture)\b/i]},
    {id:'peaceful_nuclear_uses',label:'Peaceful nuclear applications for health, food and water',patterns:[/\b(?:iaea|nuclear (?:science|technology|applications?))\b[^.!?]{0,160}\b(?:cancer care|food security|water management|agriculture)\b/i]},
    {id:'economic_energy_food_spillovers',label:'Economic, energy and food-security spillovers of conflict',patterns:[/\bspillover effects?\b[^.!?]{0,120}\b(?:economy|energy|food security)\b/i]},
    {id:'food_security',label:'Food insecurity and hunger response',patterns:[/\b(?:food insecurity|zero hunger|famine|acute hunger|malnutrition|hunger crisis|food-security crisis)\b/i]},
    {id:'global_health',label:'Global health and pandemic preparedness',patterns:[/\b(?:global health|pandemic (?:preparedness|prevention|response)|universal health coverage|public health emergency)\b/i]},
    {id:'education',label:'Access to education',patterns:[/\b(?:access to education|right to education|quality education|education for all|school enrollment)\b/i]},
    {id:'gender_equality',label:'Gender equality and women’s rights',patterns:[/\b(?:gender equality|gender stereotypes?|structural discrimination|maternal health care|women'?s rights|rights of women|empowerment of women|women and girls)\b/i]},
    {id:'gender_apartheid',label:'Recognition and codification of gender apartheid',patterns:[/\bgender apartheid\b|\bcrimes against humanity treaty\b[^.!?]{0,140}\bgender\b/i]},
    {id:'conflict_sexual_violence',label:'Conflict-related sexual violence and victim redress',patterns:[/\b(?:sexual violence as a weapon of war|conflict-related sexual violence|justice and reparation for victims)\b/i]},
    {id:'human_rights_accountability',label:'Human rights accountability',patterns:[/\b(?:human rights violations?|accountability for (?:violations|abuses|atrocities)|international accountability|impunity for)\b/i]},
    {id:'digital_governance',label:'Digital and artificial-intelligence governance',patterns:[/\b(?:artificial intelligence governance|governance of artificial intelligence|ai governance|digital governance|global digital compact|responsible ai|ict responsibly|responsible use of (?:digital technologies|ict))\b/i]},
    {id:'technology_transfer',label:'Technology transfer and the digital divide',patterns:[/\b(?:technology transfer|digital divide|digital inclusion|access to (?:appropriate )?technology|technological capacity|affordable broadband access|digital entrepreneurship|e-governance)\b/i]},
    {id:'cuba_embargo',label:'Embargo and economic restrictions concerning Cuba',patterns:[/\b(?:cuba|cuban)[^.!?]{0,100}\b(?:embargo|blockade|sanctions?|financial restrictions?)\b/i,/\b(?:embargo|blockade|sanctions?|financial restrictions?)[^.!?]{0,100}\b(?:cuba|cuban)\b/i]},
    {id:'unilateral_sanctions',label:'Unilateral sanctions and coercive measures',patterns:[/\b(?:unilateral coercive measures?|unilateral sanctions?|extraterritorial sanctions?)\b/i]},
    {id:'occupied_territory_business_accountability',label:'Business involvement in the occupied Palestinian territory',patterns:[/\b(?:business(?:es| enterprises)?|companies|database)\b[^.!?]{0,160}\b(?:settlements?|occupied palestinian territory|\bopt\b|occupation|self-determination)\b/i]},
    {id:'israeli_occupation',label:'Israeli occupation and settlements in the Palestinian territory',patterns:[/\b(?:israel|israeli|palestin(?:e|ian)?|occupied palestinian territory|\bopt\b)\b[^.!?]{0,160}\b(?:occupation|settlements?|annexation)\b/i,/\b(?:occupation|settlements?|annexation)\b[^.!?]{0,160}\b(?:israel|israeli|palestin(?:e|ian)?|occupied palestinian territory|\bopt\b)\b/i]},
    {id:'palestinian_statehood',label:'Palestinian statehood and the two-state solution',patterns:[/\b(?:palestinian state|state of palestine|two-state solution|pre-?1967 borders?|1967 borders?|east jerusalem)\b/i]},
    {id:'israel_palestine_accountability',label:'Accountability for alleged violations in Israel and the Palestinian territory',patterns:[/\b(?:israel|israeli|palestin(?:e|ian)?|occupied palestinian territory|\bopt\b)\b[^.!?]{0,260}\b(?:investigat(?:e|ion)|accountability|allegations?|international law|genocide)\b/i,/\b(?:investigat(?:e|ion)|accountability|allegations?|international law|genocide)\b[^.!?]{0,260}\b(?:israel|israeli|palestin(?:e|ian)?|occupied palestinian territory|\bopt\b)\b/i]},
    {id:'israel_un_obligations',label:'Israeli compliance with United Nations resolutions and mandates',patterns:[/\bisrael\b[^.!?]{0,180}\b(?:security council resolutions?|united nations resolutions?|cooperate with|unrwa|council mandates?)\b/i]},
    {id:'israel_normalization',label:'Normalization of relations with Israel',patterns:[/\bnormalization with israel\b/i]},
    {id:'decolonization',label:'Decolonization of non-self-governing territories',patterns:[/\b(?:decoloni[sz]ation|non-self-governing territor|colonial rule)\b/i]},
    {id:'terrorism',label:'Counter-terrorism policy',patterns:[/\b(?:counter-?terrorism|combat(?:ing)? terrorism|terrorist threats?|terrorism financing)\b/i]},
    {id:'human_trafficking',label:'Prevention and eradication of human trafficking',patterns:[/\b(?:human trafficking|trafficking in persons|trafficked for forced criminality)\b/i]},
    {id:'untoc_review',label:'Review of the UN Convention against Transnational Organized Crime',patterns:[/\b(?:implementation review mechanism|review mechanism)\b[^.!?]{0,100}\b(?:transnational organized crime|untoc|convention)\b/i,/\b(?:transnational organized crime|untoc|convention)\b[^.!?]{0,100}\b(?:implementation review mechanism|review mechanism)\b/i]},
    {id:'criminal_justice_cooperation',label:'International criminal-justice cooperation and evidence exchange',patterns:[/\b(?:mutual legal assistance|extradition|joint investigations?|exchange of (?:electronic )?evidence|international judicial cooperation|international cooperation in criminal matters|asset recovery)\b/i]},
    {id:'online_scams',label:'Prevention and prosecution of transnational online scams',patterns:[/\b(?:online scams?|scam centres?|scam centers?|forced criminality)\b/i]},
    {id:'illicit_financial_flows',label:'International cooperation against illicit financial flows',patterns:[/\b(?:illicit financial flows?|criminal proceeds?)\b[^.!?]{0,160}\b(?:international cooperation|trace|freeze|seize|confiscate)\b/i,/\b(?:international cooperation|trace|freeze|seize|confiscate)\b[^.!?]{0,160}\b(?:illicit financial flows?|criminal proceeds?)\b/i]},
    {id:'cross_border_biometrics',label:'Cross-border biometric information sharing for criminal justice',patterns:[/\b(?:biometric|biometrics)\b[^.!?]{0,120}\b(?:sharing|information|law enforcement|criminal justice|ccpcj)\b/i]},
    {id:'organized_crime',label:'Transnational organized-crime policy',patterns:[/\b(?:transnational organized crime|organised criminal|illicit trafficking networks?)\b/i]},
    {id:'sexual_reproductive_rights',label:'Sexual and reproductive autonomy and rights',patterns:[/\b(?:sexual and reproductive|reproductive autonomy|abortion|same-sex relations|sex work)\b/i]},
    {id:'death_penalty',label:'Death penalty policy and administration',patterns:[/\b(?:death penalty|capital punishment)\b/i]},
    {id:'gendered_arms_violence',label:'Gendered harms associated with the arms industry',patterns:[/\b(?:gun industry|arms industry|firearms?)\b[^.!?]{0,140}\b(?:gender|manhood|masculin|women|violence)\b/i]},
    {id:'disarmament_demobilization_reintegration',label:'Disarmament, demobilization and reintegration',patterns:[/\b(?:\bddr\b|disarmament,? demobilization and reintegration)\b/i]},
    {id:'un_charter_implementation',label:'Implementation of the United Nations Charter',patterns:[/\b(?:implement|implementation|adhere to)\b[^.!?]{0,100}\b(?:article 27|provisions of the charter|united nations charter)\b/i]},
    {id:'gulf_deescalation',label:'Ceasefire, negotiations and navigation in the Persian Gulf',patterns:[/\b(?:iran|persian gulf|strait of hormuz|gulf)\b[^.!?]{0,180}\b(?:ceasefire|negotiations?|dialogue|navigation|reopen|de-?escalation)\b/i,/\b(?:ceasefire|negotiations?|dialogue|navigation|reopen|de-?escalation)\b[^.!?]{0,180}\b(?:iran|persian gulf|strait of hormuz|gulf)\b/i]},
    {id:'migration',label:'International migration policy',patterns:[/\b(?:safe,? orderly and regular migration|global compact for migration|migration governance|migrant workers?|irregular migration)\b/i]}
  ]);
  const PROPOSAL=/\b(?:call(?:s|ed|ing)? for|urge(?:s|d)?|propose(?:s|d)?|recommend(?:s|ed)?|request(?:s|ed)?|advocate(?:s|d)?|must|should|need(?:s|ed)? to|commit(?:s|ted)? to)\b/i;
  const DISAGREEMENT=/\b(?:oppose(?:s|d)?|reject(?:s|ed)?|object(?:s|ed)? to|condemn(?:s|ed)?|cannot support|do not support|disagree(?:s|d)?|criticize(?:s|d)?|deep concern|serious concern)\b/i;
  const DEVELOPMENT=/\b(?:adopt(?:s|ed)|agree(?:s|d) (?:on|to)|launch(?:es|ed)|sign(?:s|ed)|ratif(?:y|ies|ied)|enter(?:s|ed) into force|establish(?:es|ed)|create(?:s|d)|announce(?:s|d)|suspend(?:s|ed)|withdraw(?:s|n)?|deploy(?:s|ed)|release(?:s|d)|approve(?:s|d))\b/i;
  const CEREMONIAL=/^(?:it is (?:an? )?(?:honou?r|privilege|pleasure)|we (?:congratulate|commend) (?:you|the president)|allow me to congratulate|on behalf of .{0,80},? i (?:congratulate|thank)|i wish (?:you|the assembly) every success|distinguished (?:delegates|colleagues)|excellencies)\b/i;
  const GENERIC_STOP=/^(?:action|support|efforts?|cooperation|dialogue|peace|implementation|the international community|member states?|all parties|countries|international standards)$/i;
  const ANAPHORIC_OBJECT=/^(?:it|its|this|that|these|those|they|their|them|there|here|by|to\b|inputs?\b|the u\b|the council\b|the committee\b)/i;
  const INCOMPLETE_OBJECT=/(?:\b(?:and|or|the|a|an|to|for|of|with|under|by|from|on|in|at|as|that|which|who|whose)|[,;:])$/i;
  const ADMINISTRATIVE_OBJECT=/\b(?:agenda item|programme of work|program of work|organization of work|give the floor|time limits? for statements|credentials|footnote|paragraph|technical (?:addition|amendment|edit)|draft report|document [a-z]\/?|meeting be held|held in person|speaker list|chairmanship|call for inputs?|right of reply|inscription|microphones?)\b/i;
  const clean=value=>String(value||'').replace(/\s+/g,' ').trim();
  function safeURL(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&!u.hash?u.href:null;}catch{return null;}}
  function meetingKey(record){return clean(record.meeting_slug||String(record.id||'').split('#')[0]||record.meeting||'unknown');}
  function recordedCountry(record){const value=clean(record.attribution?.label||record.country);return value&&value!=='Unknown'?value:'Recorded speaker not resolved to a country';}
  function attribution(record){
    const recorded=recordedCountry(record),speaker=record.speaker_metadata||{},group=clean(speaker.group),affiliation=clean(speaker.affiliation_full||speaker.affiliation);
    const generic=/^(?:national delegation|country delegation|national representative)$/i;
    if(group&&!generic.test(group)&&group.toLocaleLowerCase()!==affiliation.toLocaleLowerCase())return {kind:'collective',label:group,recorded_country:recorded,group};
    const text=clean(record.text),explicit=text.match(/\b(?:on behalf of|speaking for)\s+(?:the\s+)?([A-Z][A-Za-z&'’ -]{2,80}?)(?:[,.]|\s+(?:states?|countries|group)\b)/);
    if(explicit)return {kind:'collective',label:clean(explicit[1]),recorded_country:recorded,group:clean(explicit[1])};
    if(record.attribution?.country_status==='registry_mapped'&&recorded!=='Recorded speaker not resolved to a country')return {kind:'individual_country',label:recorded,recorded_country:recorded,group:null};
    return {kind:'unresolved',label:recorded,recorded_country:recorded,group:null};
  }
  function evidence(record,sentence,who=attribution(record)){const id=meetingKey(record);return {record_id:clean(record.id),meeting_id:id,meeting_slug:id,meeting_title:clean(record.meeting)||id,date:clean(record.date)||null,country:who.label,recorded_country:who.recorded_country,attribution_kind:who.kind,group:who.group,source_url:safeURL(record.source_url),excerpt:clean(sentence).slice(0,500)};}
  function substantive(sentence){return TextUnits.summaryEvidenceSentence(sentence)&&!TextUnits.unclearWording(sentence)&&!CEREMONIAL.test(clean(sentence))&&TextUnits.wordCount(sentence)>=7;}
  function proposalSentence(sentence){
    const text=clean(sentence);
    return PROPOSAL.test(text)&&
      !/\b(?:should be under no illusion|one should (?:also )?mention|should be noted|must be recalled|needless to say)\b/i.test(text)&&
      !/\b(?:leading|long-standing|strong) advocate for\b|\bAdvocates for Human Rights\b/i.test(text)&&
      !/\battention is drawn to paragraph\b[^.!?]{0,180}\b(?:decided|requested)\b/i.test(text);
  }
  function disagreementSentence(sentence){
    const text=clean(sentence);if(!DISAGREEMENT.test(text))return false;
    if(/\b(?:call(?:s|ed|ing)? (?:for|on)|urge(?:s|d)?|request(?:s|ed)?|recommend(?:s|ed)?)\b[^.!?]{0,100}\b(?:condemn|oppose|reject)\b/i.test(text)&&!/^\s*(?:we|i|the [^,.]{1,60})\s+(?:also )?(?:oppose|reject|condemn|object|criticize)/i.test(text))return false;
    return true;
  }
  function knownTopics(sentence,record){
    const meeting=clean(record?.meeting),context=clean(meeting+' '+sentence),found=CATALOG.filter(topic=>topic.patterns.some(pattern=>pattern.test(context))),ids=new Set(found.map(topic=>topic.id));
    const add=id=>{if(!ids.has(id)){const topic=CATALOG.find(row=>row.id===id);if(topic){found.push(topic);ids.add(id);}}};
    if(/democratic republic of the congo/i.test(meeting)&&/\b(?:doha|washington|peace process|verif(?:y|ied|ication)|monitoring of commitments|civic space|human rights defenders?|armed groups?|disarmament)\b/i.test(sentence))add('drc_peace_process');
    if(/\bhaiti\b/i.test(meeting)&&/\b(?:gang suppression force|\bgsf\b|contingents?|deployment|mandate|national police|capacity building|national governance|protecting its people)\b/i.test(sentence))add('haiti_security_mission');
    const suppress=new Set();
    if(ids.has('iran_nuclear_compliance')){suppress.add('nuclear_disarmament');suppress.add('nuclear_safeguards');}
    else if(ids.has('nuclear_safeguards'))suppress.add('nuclear_disarmament');
    if(ids.has('haiti_security_mission')){suppress.add('peacekeeping');suppress.add('peacekeeping_troop_participation');suppress.add('peacekeeping_mandate_resources');}
    if(ids.has('drc_peace_process')||ids.has('peacekeeping_troop_participation')||ids.has('peacekeeping_mandate_resources'))suppress.add('peacekeeping');
    if(ids.has('security_council_veto')||ids.has('security_council_working_methods'))suppress.add('security_council_reform');
    if(ids.has('peaceful_nuclear_uses')||ids.has('economic_energy_food_spillovers'))suppress.add('food_security');
    if(ids.has('occupied_territory_business_accountability')||ids.has('israeli_occupation')||ids.has('palestinian_statehood')||ids.has('israel_palestine_accountability'))suppress.add('decolonization');
    if(ids.has('human_trafficking')||ids.has('untoc_review')||ids.has('criminal_justice_cooperation')||ids.has('online_scams'))suppress.add('organized_crime');
    return found.filter(topic=>!suppress.has(topic.id));
  }
  function actionObject(sentence){
    const text=clean(sentence);let phrase='';
    let match=text.match(/\b(?:call(?:s|ed|ing)? for|propose(?:s|d)?(?: that)?|recommend(?:s|ed)?(?: that)?|advocate(?:s|d)? for)\s+([^.!?]+)/i);
    if(match)phrase=match[1];
    else {match=text.match(/\burge(?:s|d)?\s+(?:[^.!?]{0,70}?\s+to|for)\s+([^.!?]+)/i);if(match)phrase=match[1];}
    if(!phrase)return null;
    phrase=phrase.replace(/\b(?:in order to|as soon as possible|immediately)\b/gi,'').replace(/\s+/g,' ').trim();
    phrase=phrase.replace(/^(?:that |all |greater |further |immediate |urgent )+/i,'').replace(/\s+(?:because|so that)\b.*$/i,'').replace(/[,:;\s]+$/,'').trim();
    if(phrase.length>140){phrase=phrase.slice(0,140).replace(/\s+\S*$/,'').trim();}
    if(TextUnits.wordCount(phrase)<3||TextUnits.wordCount(phrase)>24||GENERIC_STOP.test(phrase)||ANAPHORIC_OBJECT.test(phrase)||INCOMPLETE_OBJECT.test(phrase)||ADMINISTRATIVE_OBJECT.test(phrase))return null;
    return phrase;
  }
  function derivedTopic(sentence){
    const phrase=actionObject(sentence);if(!phrase)return null;
    const normalized=TextUnits.tokens(phrase).filter(t=>!['the','a','an','its','their','our','all','immediate','urgent','full','fully'].includes(t)).map(t=>({cessation:'ceasefire',hostilities:'fighting',negotiations:'negotiation',commitments:'commitment'}[t]||t));
    const key=normalized.join('_').slice(0,96).replace(/_+$/,'');
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
        let topics=knownTopics(sentence,record);
        if(!topics.length){const derived=derivedTopic(sentence);if(derived)topics=[derived];}
        for(const topic of topics){
          if(!buckets.has(topic.id))buckets.set(topic.id,{id:topic.id,label:topic.label,source_derived:!!topic.derived,items:[]});
          const who=attribution(record),item={sentence:clean(sentence),country:who.label,attribution:who,meeting_id:key,evidence:evidence(record,sentence,who)};
          buckets.get(topic.id).items.push(item);meeting.topic_ids.add(topic.id);
        }
      }
    }
    const topics=[...buckets.values()].map(topic=>{
      const unique=[];const seen=new Set();for(const item of topic.items){const k=item.evidence.record_id+'|'+item.sentence;if(!seen.has(k)){seen.add(k);unique.push(item);}}
      const proposals=unique.filter(x=>proposalSentence(x.sentence)).slice(0,6).map(x=>claim('proposal',topic,x));
      const disagreements=unique.filter(x=>disagreementSentence(x.sentence)).slice(0,6).map(x=>claim('disagreement',topic,x));
      const developments=unique.filter(x=>DEVELOPMENT.test(x.sentence)).slice(0,6).map(x=>claim('development',topic,x));
      const claims=[...proposals,...disagreements];
      if(!claims.length&&unique.length)claims.push(claim('position',topic,unique[0]));
      const participants=[...new Set(unique.filter(x=>x.attribution.kind==='individual_country').map(x=>x.country))].sort();
      const collectives=[...new Set(unique.filter(x=>x.attribution.kind==='collective').map(x=>x.country))].sort();
      const meetingBreakdown=[...new Set(unique.map(x=>x.meeting_id))].sort().map(id=>({meeting_id:id,meeting_slug:id,passages:unique.filter(x=>x.meeting_id===id).length}));
      const segments=new Set(unique.map(x=>x.evidence.record_id)).size;
      return {id:topic.id,label:topic.label,policy_question:topic.label,source_derived:topic.source_derived,coverage:{source_segments:segments,segments,meetings:new Set(unique.map(x=>x.meeting_id)).size,countries:participants.length,collectives:collectives.length},participating_countries:participants,participants,participating_collectives:collectives,meeting_breakdown:meetingBreakdown,meetings:meetingBreakdown,supporting_passages:unique.map(item=>item.evidence),principal_proposals:proposals,proposals,disagreements,claims,consequential_developments:developments,developments};
    }).sort((a,b)=>b.coverage.meetings-a.coverage.meetings||b.coverage.source_segments-a.coverage.source_segments||a.label.localeCompare(b.label));
    const meetingRows=[...meetings.values()].map(m=>{
      const topicIds=[...m.topic_ids].sort();
      return {...m,meeting_slug:m.meeting_id,substantive_passages:m.substantive_sentences,
        topics:topicIds.map(id=>buckets.get(id)?.label).filter(Boolean),topic_ids:topicIds};
    });
    const stats={eligible_english_segments:selected.length,source_segments:selected.length,meetings:meetingRows.length,procedural_sentences:procedural,ceremonial_sentences:ceremonial,procedural_or_ceremonial:procedural+ceremonial,procedural_segments:procedural+ceremonial,substantive_sentences:substantiveSentences,substantive_passages:substantiveSentences,substantive_segments:substantiveSentences};
    const chartTopics=topics.map(topic=>({id:topic.id,label:topic.label}));
    const mappedCountries=[...new Set(topics.flatMap(t=>t.supporting_passages.filter(e=>e.attribution_kind==='individual_country').map(e=>e.country)).filter(value=>value&&value!=='Recorded speaker not resolved to a country'))].sort();
    const dedupeEvidence=rows=>{const seen=new Set();return rows.filter(item=>{const key=clean(item.excerpt).toLocaleLowerCase();if(!key||seen.has(key))return false;seen.add(key);return true;});};
    const distribution=topics.map(topic=>{const evidence=dedupeEvidence(topic.supporting_passages);return {topic_id:topic.id,label:topic.label,value:evidence.length,evidence};});
    const countryCells=mappedCountries.flatMap(country=>topics.map(topic=>{const evidence=topic.supporting_passages.filter(item=>item.country===country);return {country,topic_id:topic.id,value:evidence.length?1:0,evidence};}));
    const meetingCells=meetingRows.flatMap(meeting=>topics.map(topic=>{const evidence=dedupeEvidence(topic.supporting_passages.filter(item=>item.meeting_id===meeting.meeting_id));return {meeting_id:meeting.meeting_id,topic_id:topic.id,value:evidence.length,evidence};}));
    const visualizations={
      topic_distribution:{status:distribution.length?'available':'insufficient',reason:distribution.length?null:'No source-linked substantive topics were identified.',unit:'distinct supporting passages',deduplication:'Exact repeated passage wording counts once per topic.',rows:distribution},
      topic_country_matrix:{status:mappedCountries.length&&topics.length?'available':'insufficient',reason:mappedCountries.length&&topics.length?null:'No topic has a mapped recorded-country attribution.',unit:'recorded country participation (binary presence)',deduplication:'Each country counts at most once per topic. Repeated passages do not increase participation.',countries:mappedCountries,topics:chartTopics,cells:countryCells},
      meeting_topic_overview:{status:meetingRows.length&&topics.length?'available':'insufficient',reason:meetingRows.length&&topics.length?null:'Meeting-topic evidence is unavailable for this collection.',unit:'distinct supporting passages',deduplication:'Exact repeated passage wording counts once within each meeting and topic.',meetings:meetingRows.map(m=>({id:m.meeting_id,label:m.title})),topics:chartTopics,cells:meetingCells}
    };
    return {schema:'un.day-summary.v1',engine:'un.day-summary.v1.2-reviewed-policy-questions',date,method:'browser_local_deterministic_topic_and_claim_extraction',methodology:{processing_location:'browser',backend_required:false,network_calls_during_summary:false,data_handling:'Uses the collected English records already held in the browser. It neither uploads transcript text nor changes source records.',topic_method:'A versioned policy-question catalog groups reviewed synonyms, splits broad subjects into distinct policy objects, and admits only self-contained uncatalogued action objects.',claim_method:'Templates describe explicit sentence cues and retain the exact supporting passage and source URL. Collective interventions retain their group identity instead of inheriting a national affiliation.'},stats,sources:{eligible_english_segments:selected.length,meetings:meetingRows.length},noise:{procedural_sentences:procedural,ceremonial_sentences:ceremonial,substantive_sentences:substantiveSentences},meetings:meetingRows,topics,visualizations,coverage_order:topics.map(t=>({topic_id:t.id,label:t.label,...t.coverage})),consequential_developments:topics.flatMap(t=>t.consequential_developments.map(c=>({topic_id:t.id,topic_label:t.label,...c}))),interpretation:{coverage_order:'Ordered by meeting coverage, then distinct source segments. This measures recorded discussion volume, not policy importance.',consequential_developments:'Listed only when source wording contains an explicit action or outcome cue. Inclusion is not an independent verification of the event or a ranking of importance.',attribution:'Individual-country and collective recorded affiliations remain separate. Neither is independently authenticated.'},limitations:['Rules can miss implicit subjects, irony and cross-sentence context.','Source-derived topics require a self-contained action object; ambiguous fragments are withheld for review.','Broad subjects are split when the local wording identifies different policy questions.','Every displayed substantive claim must retain its evidence array and source URL.']};
  }
  const api={CATALOG,summarizeDay,build:summarizeDay,safeURL,attribution,actionObject,proposalSentence,disagreementSentence};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNDaySummary=api;
})(typeof globalThis!=='undefined'?globalThis:this);
