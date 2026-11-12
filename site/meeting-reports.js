/* Local reporting workspace; source loading is explicit and bounded. */
(()=>{
  'use strict';
  const $=id=>document.getElementById(id),Core=UNMeetingReport;
  let policy,countries,inventory=[],corpora=[],report=null,controller=null,shown=10,dirty=false;
  const setStatus=(message,error=false)=>{$('status').textContent=message;$('status').classList.toggle('error',error);};
  const selected=()=>[...$('loadedMeetings').querySelectorAll('input:checked')].map(e=>e.value);
  const options=()=>({template:$('reportTemplate').value,mission:$('mission').value,title:$('reportTitle').value,priorities:$('priorities').value,notes:$('analystNotes').value});
  function save(data,name,mime){const u=URL.createObjectURL(new Blob([data],{type:mime})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
  function invalidate(){report=null;$('reportPreview').replaceChildren();for(const id of ['downloadReport','saveReport','downloadEvidence'])$(id).disabled=true;$('reportState').textContent='Settings or selection changed. Prepare the report to update its exports.';dirty=!!corpora.length;}
  function search(){
    const ids=new Set(selected()),rows=Core.search(corpora.flatMap(c=>c.records).filter(r=>ids.has(r.meeting_slug)),$('evidenceSearch').value);
    $('evidenceCount').textContent=rows.length+' matching source segments in '+ids.size+' selected meetings. Showing '+Math.min(rows.length,shown)+'.';
    $('evidenceResults').innerHTML=Core.evidenceHTML(rows.slice(0,shown));$('moreEvidence').hidden=rows.length<=shown;
  }
  function checkbox(row,loaded=false,checked=false){
    const label=document.createElement('label'),input=document.createElement('input'),span=document.createElement('span');input.type='checkbox';input.value=row.slug;input.checked=checked;
    input.setAttribute('aria-label',(loaded?'Include ':'Select ')+row.title);
    input.disabled=!Core.allowed(row.date.slice(0,10),row.slug,policy)||(!loaded&&!row.hasTranscript);
    span.textContent=row.date.slice(0,10)+' · '+row.title+' · '+(loaded?row.status:input.disabled?'Unavailable or excluded':'Transcript listed');
    input.addEventListener('change',()=>{if(loaded){invalidate();shown=10;search();}else $('loadMeetings').disabled=!document.querySelector('#inventory input:checked');});
    label.append(input,span);return label;
  }
  function setCollection(next,prefs=null,selection=null){
    corpora=next;$('loadedMeetings').replaceChildren();
    for(const row of corpora.flatMap(c=>c.coverage).filter(r=>r.slug))$('loadedMeetings').append(checkbox(row,true,!selection||selection.includes(row.slug)));
    if(prefs){for(const [id,key] of [['reportTemplate','template'],['mission','mission'],['reportTitle','title'],['priorities','priorities'],['analystNotes','notes']])$(id).value=prefs[key];}
    $('reportControls').disabled=false;$('evidenceSearch').disabled=false;
    $('collectionStatus').textContent=corpora.flatMap(c=>c.coverage).filter(r=>r.slug).length+' loaded meeting records; '+corpora.reduce((n,c)=>n+c.records.length,0)+' English source segments. Original response hashes verified. Last source check: '+corpora.map(c=>c.collection.checked_at||c.collection.collected_at||'Unknown').join('; ')+'.';
    invalidate();shown=10;search();
  }
  function busy(value){$('sourceControls').disabled=value;$('loadMeetings').disabled=value||!document.querySelector('#inventory input:checked');$('cancelLoad').hidden=!value;for(const e of $('inventory').querySelectorAll('input'))e.disabled=value||!inventory.find(m=>m.slug===e.value)?.hasTranscript;}
  $('findMeetings').onclick=async()=>{
    const date=$('meetingDate').value;
    try{
      if(!Core.allowed(date,null,policy))throw Error('Choose an eligible date. The reserved evaluation dates remain closed.');
      controller=new AbortController();busy(true);$('inventory').replaceChildren();inventory=[];
      const listed=await UNMeetingPickerCore.list(date,{signal:controller.signal,progress:setStatus});
      inventory=listed.meetings.filter(m=>Core.allowed(date,m.slug,policy));
      for(const m of inventory)$('inventory').append(checkbox(m));
      setStatus(inventory.length+' eligible meetings found. Select up to five, then load their transcripts.');
    }catch(e){setStatus(e.name==='AbortError'?'Search cancelled.':e.message,true);}finally{controller=null;busy(false);}
  };
  $('meetingDate').oninput=()=>{inventory=[];$('inventory').replaceChildren();$('loadMeetings').disabled=true;};
  $('loadMeetings').onclick=async()=>{
    const ids=new Set([...$('inventory').querySelectorAll('input:checked')].map(e=>e.value)),chosen=inventory.filter(m=>ids.has(m.slug));
    if(!chosen.length||chosen.length>5){setStatus('Select between one and five meetings per load.',true);return;}
    const next=[];let failure=null;
    try{
      controller=new AbortController();busy(true);
      for(const m of chosen){
        if(!Core.allowed(m.date.slice(0,10),m.slug,policy))throw Error('Reserved meeting blocked.');
        const c=await UNCollector.collect(UNMeetingPickerCore.selection(m.date.slice(0,10),m),countries,{signal:controller.signal,progress:setStatus});
        await Core.validateCorpora([...next,c],policy,countries);next.push(c);
      }
    }catch(e){failure=e.name==='AbortError'?'Loading cancelled.':e.message;}
    finally{controller=null;busy(false);}
    if(next.length)setCollection(next);
    setStatus(failure?(failure+' '+next.length+' completed meeting bundles retained; previously loaded work is unchanged if none completed.'):'Retrieval finished. Check each meeting outcome, search available evidence, and prepare a report.',!!failure);
  };
  $('cancelLoad').onclick=()=>controller?.abort();
  $('openCollection').onchange=async event=>{
    const file=event.target.files[0];if(!file)return;
    try{
      if(file.size>Core.LIMIT)throw Error('Use a JSON export under 25 MB.');
      const value=JSON.parse(await file.text());let next,prefs=null,selection=null;
      if(value.schema===Core.VERSION){next=value.corpora;prefs=Core.settings(value.settings);selection=value.selected_meetings;if(!Array.isArray(selection)||!selection.length||new Set(selection).size!==selection.length)throw Error('Invalid saved meeting selection.');}
      else if(value.schema==='un.browser.corpus.v1')next=[value];else throw Error('Unsupported saved report or collection version.');
      await Core.validateCorpora(next,policy,countries);
      if(selection&&!selection.every(id=>next.some(c=>c.coverage.some(r=>r.slug===id))))throw Error('Saved selection does not match its sources.');
      setCollection(next,prefs,selection);setStatus('Saved sources verified. Prepare the report to rebuild its summaries; saved derived claims are not trusted.');
    }catch(e){setStatus('Could not open file: '+e.message,true);}finally{event.target.value='';}
  };
  for(const id of ['reportTemplate','mission','reportTitle','priorities','analystNotes'])$(id).addEventListener('input',invalidate);
  $('evidenceSearch').oninput=()=>{shown=10;search();};$('moreEvidence').onclick=()=>{shown+=10;search();};
  $('prepareReport').onclick=()=>{try{report=Core.build(corpora,selected(),options());$('reportPreview').innerHTML=Core.reportHTML(report,{preview:true});for(const id of ['downloadReport','saveReport','downloadEvidence'])$(id).disabled=false;$('reportState').textContent='Report ready: '+report.meetings.length+' meetings. Review source evidence before circulation.';dirty=true;}catch(e){invalidate();setStatus(e.message,true);}};
  $('downloadReport').onclick=()=>{if(report)save(Core.standalone(report),'un-meeting-report.html','text/html');};
  $('saveReport').onclick=()=>{if(report){const data=JSON.stringify({schema:Core.VERSION,engine:report.engine,generated_at:report.generated_at,settings:report.settings,selected_meetings:report.selected_meetings,corpora});if(new TextEncoder().encode(data).length>Core.LIMIT){setStatus('Report JSON exceeds 25 MB. Load a smaller collection before saving.',true);return;}save(data,'un-meeting-report.json','application/json');dirty=false;}};
  $('downloadEvidence').onclick=()=>{if(report)save(Core.evidenceCSV(report.records),'un-meeting-evidence.csv','text/csv;charset=utf-8');};
  window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
  (async()=>{try{
    const read=async path=>{const r=await fetch(path,{credentials:'omit'});if(!r.ok)throw Error('Reporting setup unavailable.');return r.json();};
    [policy,countries]=await Promise.all([read('reporting-exclusions.json'),read('countries.json')]);Core.exclusions(policy);
    const now=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());$('meetingDate').value=now;
    $('sourceControls').disabled=false;setStatus('Ready. Choose a meeting date or open a saved collection.');
  }catch(e){setStatus(e.message,true);}})();
})();
