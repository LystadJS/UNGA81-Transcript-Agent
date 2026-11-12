/* Source-bound reporting; no trained stance model or external AI calls. */
(function(root){
  'use strict';
  const node=typeof module!=='undefined'&&module.exports;
  const Collector=node?require('./collector.js'):root.UNCollector;
  const Reader=node?require('./meeting-quick-reader.js'):root.UNMeetingQuickReader;
  const Picker=node?require('./meeting-picker-core.js'):root.UNMeetingPickerCore;
  const VERSION='un.meeting-report.v2',LEGACY_VERSION='un.meeting-report.v1';
  const TEMPLATES=Object.freeze({brief:'Mission briefing',negotiation:'Negotiation record',evidence:'Evidence digest'});
  const LIMIT=25000000;
  const PREFERENCES_VERSION='un.mission-preferences.v1',PREFERENCES_LIMIT=8192,PREFERENCE_KEYS=['template','mission','title','priorities'];
  const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function settings(value={}){
    const out={template:value.template||'brief',mission:value.mission||'',title:value.title||'Meeting briefing',priorities:value.priorities||'',notes:value.notes||''};
    if(!Object.hasOwn(TEMPLATES,out.template))throw Error('Unknown report template.');
    for(const [key,max] of [['mission',160],['title',200],['priorities',300],['notes',8000]])if(typeof out[key]!=='string'||out[key].length>max)throw Error('Invalid report setting: '+key);
    return out;
  }
  function exclusions(value){
    if(value?.schema!=='un.reporting-exclusions.v1'||!Array.isArray(value.dates)||!Array.isArray(value.meetings)||value.meetings.length!==37||new Set(value.meetings).size!==37||value.dates.some(d=>!Picker.dateOK(d))||value.meetings.some(m=>!Picker.validSlug(m)))throw Error('Reporting exclusions could not be verified.');
    return value;
  }
  function exportPreferences(options){
    const checked=settings(Object.fromEntries(PREFERENCE_KEYS.map(k=>[k,options[k]])));
    return {schema:PREFERENCES_VERSION,settings:Object.fromEntries(PREFERENCE_KEYS.map(k=>[k,checked[k]]))};
  }
  function importPreferences(value){
    if(!value||value.schema!==PREFERENCES_VERSION||Object.keys(value).some(k=>!['schema','settings'].includes(k))||!value.settings||Object.keys(value.settings).length!==PREFERENCE_KEYS.length||PREFERENCE_KEYS.some(k=>!Object.hasOwn(value.settings,k)||typeof value.settings[k]!=='string')||!Object.hasOwn(TEMPLATES,value.settings.template))throw Error('Use a supported mission-preferences file with only format, mission, title and priority words.');
    if(new TextEncoder().encode(JSON.stringify(value)).length>PREFERENCES_LIMIT)throw Error('Mission preferences exceed 8 KiB.');
    return exportPreferences(value.settings).settings;
  }
  function allowed(date,slug,policy){
    exclusions(policy);
    return Picker.dateOK(date)&&(!slug||Picker.validSlug(slug))&&!policy.dates.includes(date)&&!policy.meetings.includes(slug);
  }
  async function validateCorpora(corpora,policy,countries){
    exclusions(policy);
    if(!Array.isArray(countries)||!countries.length)throw Error('Country registry unavailable.');
    const aliases=new Map();for(const c of countries)for(const name of [c.country,c.iso3,...c.aliases.split('|')])aliases.set(name.toLowerCase(),c);
    if(!Array.isArray(corpora)||!corpora.length||corpora.length>10||new TextEncoder().encode(JSON.stringify(corpora)).length>LIMIT)throw Error('Use a collection under 25 MB and at most ten source bundles.');
    const meetingIds=new Set(),recordIds=new Set();let total=0;
    for(const c of corpora){
      if(c?.schema!=='un.browser.corpus.v1'||!Array.isArray(c.records)||!Array.isArray(c.coverage)||!Array.isArray(c.provenance?.sources))throw Error('A source-bound browser collection is required.');
      if(!Picker.dateOK(c.collection?.start)||!Picker.dateOK(c.collection?.end)||c.collection.start>c.collection.end||policy.dates.some(d=>d>=c.collection.start&&d<=c.collection.end))throw Error('Reserved or invalid collection dates are not eligible for reporting.');
      const sources=new Map(c.provenance.sources.map(s=>[s.source_id+'|'+s.sha256,s])),parsed=new Map(),inventory=new Map();
      for(const s of sources.values())if(typeof s.raw==='string'){
        const original=JSON.parse(s.raw.replace(/^\uFEFF/,''));parsed.set(s.source_id+'|'+s.sha256,original);
        if(s.kind==='inventory')for(const m of original.meetings||[])inventory.set(m.slug,m);
      }
      const coverage=new Map();
      for(const row of c.coverage){
        if(!row.slug)continue;
        if(!allowed(row.date,row.slug,policy)||row.date<c.collection.start||row.date>c.collection.end||meetingIds.has(row.slug)||coverage.has(row.slug))throw Error('Reserved, invalid or duplicated meeting.');
        const original=inventory.get(row.slug);
        if(!original||original.date?.slice(0,10)!==row.date||original.title!==row.title||Collector.sourceURL(original.pageUrl)!==row.source_url)throw Error('Meeting metadata differs from its original inventory.');
        coverage.set(row.slug,row);meetingIds.add(row.slug);
      }
      for(const r of c.records){
        const source=sources.get(r.source_id+'|'+r.raw_sha256),row=coverage.get(r.meeting_slug);
        if(!row||row.date!==r.date||!allowed(r.date,r.meeting_slug,policy)||r.language!=='en'||r.legacy_provenance_unavailable||typeof r.id!=='string'||recordIds.has(r.id)||typeof r.text!=='string'||!source||typeof source.raw!=='string')throw Error('Passage lacks an eligible original source or unique meeting identity.');
        if(!Reader.safeURL(r.source_url))throw Error('Unsupported passage source link.');
        const original=parsed.get(r.source_id+'|'+r.raw_sha256);
        if(original.video?.date?.slice(0,10)!==r.date||original.transcript?.language!=='en')throw Error('Passage date or language differs from its original source.');
        const index=Number(String(r.json_pointer).match(/^\/transcript\/data\/(\d+)$/)?.[1]),speaker=original.transcript.data?.[index]?.speaker||{};
        if(r.id!==r.meeting_slug+'#'+index||r.meeting!==row.title||r.source_url!==Collector.sourceURL(original.transcript.data?.[index]?.pageUrl||row.source_url)||r.source_id!==Collector.sourceURL(inventory.get(r.meeting_slug).jsonUrl))throw Error('Passage identity or locator differs from its original source.');
        const affiliation=speaker.affiliation||speaker.affiliation_full||'',country=aliases.get(affiliation.toLowerCase())||aliases.get((speaker.affiliation_full||'').toLowerCase());
        if(r.country!==(country?.country||affiliation||'Unidentified')||r.region!==(country?.region||'Unmapped')||r.attribution?.country_status!==(country?'registry_mapped':'unresolved'))throw Error('Recorded affiliation differs from the source and registry.');
        for(const key of ['affiliation','affiliation_full','function','group','name','id'])if((r.speaker_metadata?.[key]??null)!==(typeof speaker[key]==='string'?speaker[key].slice(0,240):null))throw Error('Recorded speaker metadata differs from the original source.');
        recordIds.add(r.id);if(++total>15000)throw Error('Too many source passages.');
      }
      await Collector.verifyProvenance(c);
    }
    if(!meetingIds.size||meetingIds.size>100)throw Error('Select between one and 100 meetings.');
    return corpora;
  }
  function search(records,query){
    const terms=String(query||'').trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    return records.filter(r=>terms.every(term=>[r.text,r.country,r.meeting,r.speaker_metadata?.name,r.speaker_metadata?.group].join(' ').toLocaleLowerCase().includes(term)));
  }
  function meetingSelection(corpora,selected){
    const known=new Set(corpora.flatMap(c=>c.coverage).map(r=>r.slug));
    if(!Array.isArray(selected)||!selected.length||new Set(selected).size!==selected.length||selected.some(id=>typeof id!=='string'||!known.has(id)))throw Error('Invalid saved meeting selection. Select at least one loaded meeting.');
    return new Set(selected);
  }
  function appendixSelection(value,records){
    if(value===undefined)value={mode:'template',record_ids:[]};
    if(!value||Object.keys(value).length!==2||!['template','selected'].includes(value.mode)||!Array.isArray(value.record_ids)||value.record_ids.length>15000||new Set(value.record_ids).size!==value.record_ids.length||(value.mode==='template'&&value.record_ids.length))throw Error('Invalid evidence appendix selection.');
    const known=new Set(records.map(r=>r.id));
    if(value.record_ids.some(id=>typeof id!=='string'||!known.has(id)))throw Error('Appendix passage does not belong to the selected source meetings.');
    const chosen=new Set(value.record_ids);
    return {mode:value.mode,record_ids:records.filter(r=>chosen.has(r.id)).map(r=>r.id)};
  }
  async function openSaved(value,policy,countries){
    let corpora,prefs=null,selected=null,appendix;
    if([VERSION,LEGACY_VERSION].includes(value?.schema)){
      corpora=value.corpora;prefs=settings(value.settings);selected=value.selected_meetings;
      if(value.schema===VERSION){if(!Object.hasOwn(value,'appendix'))throw Error('Saved report is missing its appendix selection.');appendix=value.appendix;}
      else if(Object.hasOwn(value,'appendix'))throw Error('A v1 report cannot contain a v2 appendix selection.');
    }else if(value?.schema==='un.browser.corpus.v1')corpora=[value];else throw Error('Unsupported saved report or collection version.');
    await validateCorpora(corpora,policy,countries);
    const ids=meetingSelection(corpora,value.schema==='un.browser.corpus.v1'?corpora.flatMap(c=>c.coverage).filter(r=>r.slug).map(r=>r.slug):selected);
    appendix=appendixSelection(appendix,corpora.flatMap(c=>c.records).filter(r=>ids.has(r.meeting_slug)));
    return {corpora,settings:prefs,selected:[...ids],appendix};
  }
  function savedReport(report,corpora){
    return {schema:VERSION,engine:report.engine,generated_at:report.generated_at,settings:report.settings,selected_meetings:report.selected_meetings,appendix:report.appendix,corpora};
  }
  function build(corpora,selected,options={},appendix){
    const prefs=settings(options),ids=meetingSelection(corpora,selected),coverage=corpora.flatMap(c=>c.coverage).filter(r=>ids.has(r.slug));
    if(!coverage.length)throw Error('Select at least one loaded meeting.');
    const records=corpora.flatMap(c=>c.records).filter(r=>ids.has(r.meeting_slug));
    const chosen=appendixSelection(appendix,records),appendixIds=new Set(chosen.record_ids);
    const meetings=coverage.map(m=>({slug:m.slug,date:m.date,title:m.title||m.slug,status:m.status,source_url:Reader.safeURL(m.source_url),
      summary:Reader.build(records,{meeting_slug:m.slug,meeting_date:m.date,title:m.title})}));
    return {schema:VERSION,engine:'source-bound-reporting-1.1',generated_at:new Date().toISOString(),settings:prefs,appendix:chosen,
      appendix_records:chosen.mode==='selected'?records.filter(r=>appendixIds.has(r.id)):prefs.template==='evidence'?records:[],
      selected_meetings:meetings.map(m=>m.slug),meetings,records,priority_evidence:search(records,prefs.priorities),
      collections:corpora.map(c=>({collected_at:c.collection.collected_at,checked_at:c.collection.checked_at,partial:c.collection.partial})),
      model_status:'withheld_not_accepted',method:'Existing deterministic quick reader plus literal all-term evidence search; not generative AI.',
      limitations:['English source segments may contain ASR or interpretation errors and are not necessarily complete speeches.',
        'Recorded expressions are provisional rule-based extracts, not validated five-class stance estimates or official positions.',
        'Search results are a subset of the loaded selected meetings. A missing match does not establish silence or neutrality.',
        'Mission priorities organize evidence only. Analyst notes are user-authored and are not source statements.']};
  }
  const link=(url,label)=>Reader.safeURL(url)?'<a href="'+escape(url)+'" target="_blank" rel="noopener noreferrer">'+escape(label)+'</a>':escape(label);
  function evidenceHTML(rows){
    return rows.map(r=>'<article class="evidence"><h4>'+escape(r.country||'Unresolved attribution')+' · '+escape(r.date)+'</h4><p>'+link(r.source_url,r.meeting||r.meeting_slug)+'</p><blockquote>'+escape(r.text)+'</blockquote><details><summary>Source identity</summary><p>'+escape(r.id)+' · '+escape(r.json_pointer)+'<br>Source SHA-256: '+escape(r.raw_sha256)+'<br>Text SHA-256: '+escape(r.text_sha256)+'</p></details></article>').join('');
  }
  function reportHTML(report,{preview=false}={}){
    const {settings:p,meetings,records}=report;
    const appendix=rows=>evidenceHTML(preview?rows.slice(0,50):rows)+(preview&&rows.length>50?'<p>Preview shows the first 50 passages. The HTML export includes all '+rows.length+' passages.</p>':'');
    const body=meetings.map(m=>{
      const s=m.summary,meetingRecords=records.filter(r=>r.meeting_slug===m.slug);
      const affiliations=[...new Set(meetingRecords.map(r=>r.country||'Unresolved attribution'))].sort();
      const countryRows=affiliations.map(country=>{
        const positions=s.positions.filter(x=>x.country===country),national=meetingRecords.filter(r=>r.country===country&&!Reader.collectiveAttribution(r));
        const us=s.positions.filter(x=>x.country==='United States');
        const comparisons=positions.filter(x=>us.some(u=>u.issue_id===x.issue_id&&u.expression_object.toLowerCase()===x.expression_object.toLowerCase()));
        const comparison=country==='United States'?'U.S. recorded expressions':comparisons.length?'Matching policy wording appears in the U.S. extracts below; no agreement score is assigned.':'No matching U.S. policy-object extract in this meeting. This is a comparison gap.';
        return '<tr><th scope="row">'+escape(country)+'</th><td>'+(!national.length?'Collective statement; no national position assigned.':positions.length?positions.map(x=>escape(x.expression_label)+' '+escape(x.expression_object)+'<br>'+x.evidence.map(e=>link(e.source_url,e.excerpt)).join('<br>')).join('<hr>'):'No eligible object-specific expression extracted.')+'</td><td>'+escape(comparison)+'</td></tr>';
      }).join('');
      const themes='<h3>Subjects mentioned</h3><p>'+escape(s.themes.map(t=>t.label+' ('+t.segments+' source segments)').join('; ')||'No fixed-dictionary theme found.')+'</p>';
      const countries='<h3>Recorded country expressions and U.S. comparison coverage</h3><div class="report-table"><table><thead><tr><th>Recorded affiliation</th><th>Expression or gap</th><th>U.S. comparison</th></tr></thead><tbody>'+countryRows+'</tbody></table></div>';
      return '<section><h2>'+escape(m.date)+' · '+link(m.source_url,m.title)+'</h2><p>'+escape(s.paragraphs.join(' '))+'</p><p>'+s.stats.source_segments+' source segments; '+s.stats.recorded_countries+' recorded country labels; '+s.stats.withheld_collective_segments+' collective segments withheld from national positions. Collection outcome: '+escape(m.status)+'.</p>'+(p.template==='negotiation'?countries+themes:themes+countries)+'</section>';
    }).join('');
    return '<h1>'+escape(p.title)+'</h1><p>'+escape(p.mission||'Mission not specified')+' · '+escape(TEMPLATES[p.template])+'</p><p>'+meetings.length+' selected meetings; '+records.length+' English source segments. Prepared '+escape(report.generated_at)+'.</p><p class="notice">Source-linked draft. Automatic five-class stance estimates remain withheld. Review the evidence before circulation.</p>'+body+
      (p.priorities?'<section><h2>Mission priority evidence</h2><p>Literal search: '+escape(p.priorities)+'. '+report.priority_evidence.length+' matching source segments; this does not change the all-meeting overview.</p>'+appendix(report.priority_evidence)+'</section>':'')+
      (report.appendix.mode==='selected'||p.template==='evidence'?'<section class="evidence-appendix"><h2>Evidence appendix</h2><p>'+(report.appendix.mode==='selected'?'Analyst-selected passages: ':'All passages: ')+report.appendix_records.length+' of '+records.length+' source segments from the selected meetings. The overview, country expressions and coverage counts use all '+records.length+' segments.</p>'+(report.appendix_records.length?appendix(report.appendix_records):'<p>No appendix passages selected. This does not establish absence of relevant evidence.</p>')+'</section>':'')+
      '<section><h2>Analyst notes</h2><p class="analyst-notes">'+escape(p.notes||'No analyst notes supplied.')+'</p><p>User-authored; not extracted from the transcript.</p></section><section><h2>Methods and coverage</h2><p>'+escape(report.method)+'</p><ul>'+report.limitations.map(x=>'<li>'+escape(x)+'</li>').join('')+'</ul><p>Source checks: '+escape(report.collections.map(c=>c.checked_at||c.collected_at||'Unknown').join('; '))+'. '+report.collections.filter(c=>c.partial).length+' collection bundles report incomplete retrieval.</p></section>';
  }
  function standalone(report){return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>'+escape(report.settings.title)+'</title><style>body{font:16px/1.6 system-ui;max-width:1050px;margin:32px auto;padding:20px;color:#182b40}table{border-collapse:collapse;width:100%}td,th{padding:12px;border:1px solid #cbd5df;text-align:left;vertical-align:top}blockquote{white-space:pre-wrap;margin:16px 0;padding:16px;background:#f4f6f8}.report-table{overflow:auto}p,td,th{overflow-wrap:anywhere}.analyst-notes{white-space:pre-wrap}.notice{border-left:4px solid #805900;padding:12px;background:#fff7e8}section{margin-top:30px}@media print{details{display:block}section{break-inside:auto}}</style>'+reportHTML(report)+'</html>';}
  function evidenceCSV(records){
    const cols=['id','meeting_slug','date','country','text','source_url','source_id','source_version','raw_sha256','text_sha256','json_pointer'];
    const cell=x=>'"'+String(/^[\s]*[=+\-@]/.test(String(x??''))?"'"+x:x??'').replace(/"/g,'""')+'"';
    return [cols,...records.map(r=>cols.map(k=>r[k]))].map(row=>row.map(cell).join(',')).join('\r\n');
  }
  const api={VERSION,LEGACY_VERSION,TEMPLATES,LIMIT,PREFERENCES_VERSION,PREFERENCES_LIMIT,exportPreferences,importPreferences,settings,exclusions,allowed,validateCorpora,search,meetingSelection,appendixSelection,openSaved,savedReport,build,reportHTML,evidenceHTML,standalone,evidenceCSV};
  if(node)module.exports=api;else root.UNMeetingReport=api;
})(globalThis);
