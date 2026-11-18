/* Local reporting workspace; source loading is explicit and bounded. */
(()=>{
  'use strict';
  const $=id=>document.getElementById(id),Core=UNMeetingReport;
  let policy,countries,inventory=[],corpora=[],report=null,controller=null,shown=10,dirty=false,handoff=null,appendixIds=new Set(),notes=new Map();
  let workspaceRevision=0,replacementSerial=0,packaging=false,deviceBusy=false,deviceAvailable=false,deviceSaved=false,deviceLibrary=[],deviceId='current';
  const setStatus=(message,error=false)=>{$('status').textContent=message;$('status').classList.toggle('error',error);};
  const selected=()=>[...$('loadedMeetings').querySelectorAll('input:checked')].map(e=>e.value);
  const options=()=>({template:$('reportTemplate').value,mission:$('mission').value,title:$('reportTitle').value,priorities:$('priorities').value,notes:$('analystNotes').value,questions:readQuestions()});
  const appendix=()=>({mode:$('appendixMode').value,record_ids:[...appendixIds]});
  const passageNotes=()=>[...notes].map(([record_id,text])=>({record_id,text}));
  function readQuestions(){return [...$('briefingQuestions').children].map(row=>({heading:row.querySelector('[data-heading]').value,query:row.querySelector('[data-query]').value}));}
  function questionCount(){const count=$('briefingQuestions').children.length;$('questionCount').textContent=count+' of 8 questions.';$('addBriefingQuestion').disabled=count>=8;}
  function addQuestion(value={heading:'',query:''},focus=false){
    if($('briefingQuestions').children.length>=8)return;
    const row=document.createElement('fieldset'),legend=document.createElement('legend');legend.textContent='Briefing question';row.append(legend);
    for(const [key,label,max] of [['heading','Question or section heading',160],['query','Search words for supporting evidence',300]]){
      const wrapper=document.createElement('label'),input=document.createElement('input');wrapper.textContent=label;input.type='text';input.maxLength=max;input.value=value[key];input.dataset[key]='';input.addEventListener('input',invalidate);wrapper.append(input);row.append(wrapper);
    }
    const remove=document.createElement('button');remove.type='button';remove.className='secondary';remove.textContent='Remove question';remove.onclick=()=>{const next=row.nextElementSibling?.querySelector('input')||row.previousElementSibling?.querySelector('input')||$('addBriefingQuestion');row.remove();questionCount();invalidate();next.focus();};row.append(remove);$('briefingQuestions').append(row);questionCount();if(focus)row.querySelector('input').focus();
  }
  function setQuestions(values=[]){$('briefingQuestions').replaceChildren();for(const q of values)addQuestion(q);questionCount();}
  $('addBriefingQuestion').onclick=()=>{addQuestion(undefined,true);invalidate();};
  function save(data,name,mime){const blob=new Blob([data],{type:mime});if(blob.size>Core.LIMIT){setStatus('Download exceeds 25 MB. Choose fewer meetings or shorter notes before exporting. Current work has not changed.',true);return false;}const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);return true;}
  function reportName(suffix){return 'un-meeting-report-'+report.generated_at.replace(/[-:.]/g,'')+suffix;}
  function invalidate(){workspaceRevision++;report=null;$('expressionEvidence').close();$('expressionEvidenceBody').replaceChildren();$('reportPreview').replaceChildren();for(const id of ['downloadReport','saveReport','downloadEvidence','downloadPackage','saveDeviceReport'])$(id).disabled=true;$('packageStatus').textContent='Prepare the report before downloading its package.';$('reportState').textContent='Settings or selection changed. Prepare the report to update its exports.';dirty=!!corpora.length;deviceControls();}
  function replacementCurrent(ticket){
    if(ticket.id!==replacementSerial)return false;
    if(ticket.revision!==workspaceRevision){setStatus('Your report changed while sources were being checked. Current work kept; try loading again when ready.');return false;}
    return true;
  }
  function confirmReplacement(message,force=false){
    if(!corpora.length||(!dirty&&!force))return Promise.resolve(true);
    const dialog=$('replaceReport');if(dialog.open)return Promise.resolve(false);
    $('replaceReportMessage').textContent=message;dialog.returnValue='keep';
    return new Promise(resolve=>{dialog.addEventListener('close',()=>resolve(dialog.returnValue==='replace'),{once:true});dialog.showModal();});
  }
  $('keepCurrentReport').onclick=()=>$('replaceReport').close('keep');
  $('replaceCurrentReport').onclick=()=>$('replaceReport').close('replace');
  // JSON values keep missing metadata distinct from any literal recorded name.
  function evidenceValue(record,key){return JSON.stringify((key==='country'?record.country:record.speaker_metadata?.name)||null);}
  function refreshEvidenceFilters(reset=false){
    const ids=new Set(selected()),records=corpora.flatMap(c=>c.records).filter(r=>ids.has(r.meeting_slug));
    for(const [id,key,all,missing] of [['evidenceCountry','country','All recorded affiliations','No recorded country affiliation'],['evidenceSpeaker','speaker','All recorded names','No recorded speaker name']]){
      const control=$(id),previous=reset?'':control.value,values=[...new Set(records.map(r=>evidenceValue(r,key)))];
      values.sort((a,b)=>String(JSON.parse(a)||'').localeCompare(String(JSON.parse(b)||'')));
      control.replaceChildren(new Option(all,''));
      for(const value of values)control.append(new Option(key==='speaker'&&JSON.parse(value)?'Recorded: '+JSON.parse(value):JSON.parse(value)||missing,value));
      control.value=values.includes(previous)?previous:'';
    }
    $('evidenceFilters').disabled=!records.length;
  }
  function search(){
    const ids=new Set(selected()),all=corpora.flatMap(c=>c.records).filter(r=>ids.has(r.meeting_slug));
    const rows=Core.search(all.filter(r=>(!$('evidenceCountry').value||evidenceValue(r,'country')===$('evidenceCountry').value)&&(!$('evidenceSpeaker').value||evidenceValue(r,'speaker')===$('evidenceSpeaker').value)&&(!$('onlySelectedEvidence').checked||appendixIds.has(r.id))),$('evidenceSearch').value);
    $('evidenceCount').textContent=rows.length+' matching source segments in '+ids.size+' selected meetings ('+all.length+' source segments before search and filters). Showing '+Math.min(rows.length,shown)+'.';
    $('evidenceResults').innerHTML=Core.evidenceHTML(rows.slice(0,shown));$('moreEvidence').hidden=rows.length<=shown;
    for(const [i,article] of [...$('evidenceResults').children].entries()){
      const record=rows[i],label=document.createElement('label'),input=document.createElement('input');
      label.className='appendix-choice';input.type='checkbox';input.checked=appendixIds.has(record.id);input.setAttribute('aria-label','Include passage '+record.id+' in appendix');
      input.onchange=()=>{if(input.checked)appendixIds.add(record.id);else appendixIds.delete(record.id);$('appendixMode').value='selected';invalidate();appendixCount();if($('onlySelectedEvidence').checked)search();};
      label.append(input,document.createTextNode('Include in evidence appendix'));article.prepend(label);
      const context=document.createElement('details'),contextTitle=document.createElement('summary'),contextBody=document.createElement('div');
      context.className='passage-context';contextTitle.textContent='Read neighboring source passages';contextBody.setAttribute('role','region');contextBody.setAttribute('aria-label','Source context for '+record.id);
      context.ontoggle=()=>{if(context.open&&!contextBody.hasChildNodes()){try{contextBody.innerHTML=Core.contextHTML(Core.contextWindow(all,record.id));}catch(e){contextBody.textContent='Context unavailable: '+e.message;}}};
      context.append(contextTitle,contextBody);article.append(context);
      const details=document.createElement('details'),summary=document.createElement('summary'),noteLabel=document.createElement('label'),note=document.createElement('textarea');
      details.className='passage-note-editor';details.open=notes.has(record.id);summary.textContent='Your note on this passage';noteLabel.textContent='Your interpretation or follow-up (up to '+Core.NOTE_LIMIT+' characters)';
      note.rows=3;note.maxLength=Core.NOTE_LIMIT;note.value=notes.get(record.id)||'';note.setAttribute('aria-label','Your note on passage '+record.id);
      note.oninput=()=>{
        if(note.value.length>Core.NOTE_LIMIT||(!notes.has(record.id)&&note.value.trim()&&notes.size>=Core.NOTES_LIMIT)){note.value=notes.get(record.id)||'';setStatus('Use at most '+Core.NOTES_LIMIT+' passage notes, each up to '+Core.NOTE_LIMIT+' characters.',true);return;}
        if(note.value.trim())notes.set(record.id,note.value);else notes.delete(record.id);
        invalidate();notesCount();
      };
      noteLabel.append(note);details.append(summary,noteLabel);article.append(details);
    }
    appendixCount();notesCount();
  }
  function notesCount(){$('passageNotesCount').textContent=notes.size+' passage '+(notes.size===1?'note':'notes')+'. Saved in report HTML and JSON, separately from source text. The full evidence CSV and reusable preferences exclude your notes. Removing a meeting removes its notes.';}
  function appendixCount(){
    $('appendixCount').textContent=$('appendixMode').value==='selected'?appendixIds.size+(appendixIds.size===1?' passage selected for the appendix.':' passages selected for the appendix.')+' Summaries, country expressions and the full evidence CSV still use all passages from selected meetings.':'Template default: the evidence digest includes all passages; other templates omit the appendix. Select a passage to create a custom appendix.';
  }
  function pruneAppendix(){
    const meetings=new Set(selected()),known=new Set(corpora.flatMap(c=>c.records).filter(r=>meetings.has(r.meeting_slug)).map(r=>r.id));
    appendixIds=new Set([...appendixIds].filter(id=>known.has(id)));
    notes=new Map([...notes].filter(([id])=>known.has(id)));
  }
  function checkbox(row,loaded=false,checked=false){
    const label=document.createElement('label'),input=document.createElement('input'),span=document.createElement('span');input.type='checkbox';input.value=row.slug;input.checked=checked;
    input.setAttribute('aria-label',(loaded?'Include ':'Select ')+row.title);
    input.disabled=!Core.allowed(row.date.slice(0,10),row.slug,policy)||(!loaded&&!row.hasTranscript);
    span.textContent=row.date.slice(0,10)+' · '+row.title+' · '+(loaded?row.status:input.disabled?'Unavailable or excluded':'Transcript listed');
    input.addEventListener('change',()=>{if(loaded){pruneAppendix();refreshEvidenceFilters();invalidate();shown=10;search();}else $('loadMeetings').disabled=!document.querySelector('#inventory input:checked');});
    label.append(input,span);return label;
  }
  function setCollection(next,prefs=null,selection=null,chosen={mode:'template',record_ids:[]},passage_notes=[]){
    corpora=next;$('loadedMeetings').replaceChildren();
    appendixIds=new Set(chosen.record_ids);$('appendixMode').value=chosen.mode;$('onlySelectedEvidence').checked=false;
    notes=new Map(passage_notes.map(n=>[n.record_id,n.text]));
    for(const row of corpora.flatMap(c=>c.coverage).filter(r=>r.slug))$('loadedMeetings').append(checkbox(row,true,!selection||selection.includes(row.slug)));
    if(prefs)setQuestions(prefs.questions);
    if(prefs){for(const [id,key] of [['reportTemplate','template'],['mission','mission'],['reportTitle','title'],['priorities','priorities'],['analystNotes','notes']])$(id).value=prefs[key];}
    else $('analystNotes').value='';
    $('reportControls').disabled=false;$('evidenceSearch').disabled=false;$('appendixControls').disabled=false;
    $('collectionStatus').textContent=corpora.flatMap(c=>c.coverage).filter(r=>r.slug).length+' loaded meeting records; '+corpora.reduce((n,c)=>n+c.records.length,0)+' English source segments. Original response hashes verified. Last source check: '+corpora.map(c=>c.collection.checked_at||c.collection.collected_at||'Unknown').join('; ')+'.';
    refreshEvidenceFilters(true);invalidate();shown=10;search();
  }
  function busy(value){$('sourceControls').disabled=value;$('loadMeetings').disabled=value||!document.querySelector('#inventory input:checked');$('cancelLoad').hidden=!value;for(const e of $('inventory').querySelectorAll('input'))e.disabled=value||!inventory.find(m=>m.slug===e.value)?.hasTranscript;}
  function clearHandoff(){handoff=null;$('archiveSelection').hidden=true;}
  $('checkArchiveSelection').onclick=async()=>{
    if(!handoff)return;
    try{
      const requested=UNMeetingReportSelection.validate(handoff,policy).meetings;
      controller=new AbortController();busy(true);inventory=[];$('inventory').replaceChildren();
      const next=[];
      for(const date of [...new Set(requested.map(m=>m.date))]){
        const listed=await UNMeetingPickerCore.list(date,{signal:controller.signal,progress:setStatus});
        for(const wanted of requested.filter(m=>m.date===date))next.push(listed.meetings.find(m=>m.slug===wanted.meeting_id)||{slug:wanted.meeting_id,date,title:wanted.meeting_id+' (not in current inventory)',hasTranscript:false});
      }
      inventory=next;
      for(const m of inventory)$('inventory').append(checkbox(m,false,m.hasTranscript));
      const available=inventory.filter(m=>m.hasTranscript).length;
      setStatus(available+' of '+requested.length+' selected meetings currently list transcripts. '+(requested.length-available)+' are unavailable or absent. Load the checked meetings explicitly; the loaded revision may differ from the archive snapshot.');
    }catch(e){setStatus(e.name==='AbortError'?'Selection check cancelled.':e.message,true);}finally{controller=null;busy(false);}
  };
  $('findMeetings').onclick=async()=>{
    clearHandoff();
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
  $('meetingDate').oninput=()=>{clearHandoff();inventory=[];$('inventory').replaceChildren();$('loadMeetings').disabled=true;};
  $('loadMeetings').onclick=async()=>{
    const ids=new Set([...$('inventory').querySelectorAll('input:checked')].map(e=>e.value)),chosen=inventory.filter(m=>ids.has(m.slug));
    if(!chosen.length||chosen.length>5){setStatus('Select between one and five meetings per load.',true);return;}
    const ticket={id:++replacementSerial,revision:workspaceRevision};
    if(!await confirmReplacement('Loading these meetings will replace your current sources, appendix selections and notes.')){if(ticket.id===replacementSerial)setStatus('Current report kept. No transcripts requested.');return;}
    if(!replacementCurrent(ticket))return;
    const next=[],loading=new AbortController();let failure=null,cancelled=false;
    try{
      controller=loading;busy(true);
      for(const m of chosen){
        if(loading.signal.aborted||ticket.id!==replacementSerial||ticket.revision!==workspaceRevision)break;
        if(!Core.allowed(m.date.slice(0,10),m.slug,policy))throw Error('Reserved meeting blocked.');
        const c=await UNCollector.collect(UNMeetingPickerCore.selection(m.date.slice(0,10),m),countries,{signal:loading.signal,progress:message=>{if(ticket.id===replacementSerial)setStatus(message);}});
        await Core.validateCorpora([...next,c],policy,countries);next.push(c);
      }
    }catch(e){cancelled=e.name==='AbortError';failure=cancelled?'Loading cancelled.':e.message;}
    finally{if(controller===loading){controller=null;busy(false);}}
    if(ticket.id!==replacementSerial)return;
    if(loading.signal.aborted||cancelled){setStatus('Loading cancelled. Current work kept; no replacement applied.');return;}
    if(!replacementCurrent(ticket))return;
    const partial=!!failure||next.some(c=>c.collection.partial);
    if(next.length&&partial&&!await confirmReplacement(next.length+' of '+chosen.length+' meeting bundles loaded; retrieval is incomplete. Replace your current report with these available sources?',true)){if(ticket.id===replacementSerial)setStatus('Current report kept. Incomplete replacement was not applied.');return;}
    if(!replacementCurrent(ticket))return;
    if(next.length)setCollection(next);
    setStatus(failure?(failure+' '+next.length+' meeting bundles applied; current work is unchanged if none completed.'):'Retrieval finished.'+(partial?' Coverage is incomplete.':'')+' Check each meeting outcome, search available evidence, and prepare a report.',!!failure);
  };
  $('cancelLoad').onclick=()=>controller?.abort();
  $('openCollection').onchange=async event=>{
    const file=event.target.files[0];if(!file)return;
    const ticket={id:++replacementSerial,revision:workspaceRevision};setStatus('Checking saved sources…');
    try{
      if(file.size>Core.LIMIT)throw Error('Use a JSON export under 25 MB.');
      const opened=await Core.openSaved(JSON.parse(await file.text()),policy,countries);
      if(!replacementCurrent(ticket))return;
      if(!await confirmReplacement('Opening this file will replace your current sources, appendix selections and notes.')){if(ticket.id===replacementSerial)setStatus('Current report kept. The selected file was not applied.');return;}
      if(!replacementCurrent(ticket))return;
      setCollection(opened.corpora,opened.settings,opened.selected,opened.appendix,opened.passage_notes);setStatus('Saved sources verified. Prepare the report to rebuild its summaries; saved derived claims are not trusted.');
    }catch(e){if(ticket.id===replacementSerial)setStatus('Could not open file: '+e.message,true);}finally{if(ticket.id===replacementSerial)event.target.value='';}
  };
  for(const id of ['reportTemplate','mission','reportTitle','priorities','analystNotes'])$(id).addEventListener('input',invalidate);
  $('savePreferences').onclick=()=>{try{save(JSON.stringify(Core.exportPreferences(options()),null,2),'un-mission-preferences.json','application/json');$('preferencesStatus').textContent='Mission preferences saved. Transcript text, selected meetings and analyst notes are excluded.';}catch(e){$('preferencesStatus').textContent=e.message;}};
  $('openPreferences').onchange=async event=>{
    const file=event.target.files[0];if(!file)return;
    try{
      if(file.size>Core.PREFERENCES_LIMIT)throw Error('Use a mission-preferences JSON file under 8 KiB.');
      const prefs=Core.importPreferences(JSON.parse(await file.text()));
      for(const [id,key] of [['reportTemplate','template'],['mission','mission'],['reportTitle','title'],['priorities','priorities']])$(id).value=prefs[key];
      setQuestions(prefs.questions);invalidate();$('preferencesStatus').textContent='Mission preferences applied. Your loaded sources, meeting selection and analyst notes are unchanged. Prepare the report again to update its exports.';
    }catch(e){$('preferencesStatus').textContent='Could not open mission preferences: '+e.message;}finally{event.target.value='';}
  };
  for(const id of ['evidenceCountry','evidenceSpeaker'])$(id).onchange=()=>{shown=10;search();};
  $('clearEvidenceFilters').onclick=()=>{$('evidenceSearch').value='';$('evidenceCountry').value='';$('evidenceSpeaker').value='';$('onlySelectedEvidence').checked=false;shown=10;search();$('evidenceSearch').focus();};
  $('evidenceSearch').oninput=()=>{shown=10;search();};$('moreEvidence').onclick=()=>{shown+=10;search();};
  $('onlySelectedEvidence').onchange=()=>{shown=10;search();};
  $('appendixMode').onchange=()=>{if($('appendixMode').value==='template')appendixIds.clear();invalidate();search();};
  $('clearAppendix').onclick=()=>{appendixIds.clear();$('appendixMode').value='selected';invalidate();search();};
  $('prepareReport').onclick=()=>{try{report=Core.build(corpora,selected(),options(),appendix(),passageNotes());workspaceRevision++;$('reportPreview').innerHTML=Core.reportHTML(report,{preview:true});for(const id of ['downloadReport','saveReport','downloadEvidence','downloadPackage','saveDeviceReport'])$(id).disabled=false;$('downloadPackage').disabled=packaging;if(!packaging)$('packageStatus').textContent='Ready to download a report package.';$('reportState').textContent='Report ready: '+report.meetings.length+' meetings. Review source evidence before circulation.';dirty=true;deviceControls();}catch(e){invalidate();setStatus(e.message,true);}};
  $('reportPreview').onclick=event=>{
    const button=event.target.closest('button[data-evidence-id]');
    if(!button||!$('reportPreview').contains(button)||!report)return;
    try{
      $('expressionEvidenceBody').innerHTML=Core.contextHTML(Core.contextWindow(report.records,button.dataset.evidenceId));
      $('expressionEvidence').showModal();
    }catch(e){setStatus('Source context unavailable: '+e.message,true);}
  };
  $('closeExpressionEvidence').onclick=()=>$('expressionEvidence').close();
  $('expressionEvidence').addEventListener('close',()=>{if(!$('expressionEvidence').open)$('expressionEvidenceBody').replaceChildren();});
  $('downloadReport').onclick=()=>{if(report)save(Core.standalone(report),reportName('.html'),'text/html');};
  $('saveReport').onclick=()=>{if(report&&save(JSON.stringify(Core.savedReport(report,corpora)),reportName('.json'),'application/json'))dirty=false;};
  $('downloadEvidence').onclick=()=>{if(report)save(Core.evidenceCSV(report.records),reportName('-evidence.csv'),'text/csv;charset=utf-8');};
  $('downloadPackage').onclick=async()=>{
    if(!report||packaging)return;
    const prepared=report,revision=workspaceRevision,name=reportName('.zip');packaging=true;$('downloadPackage').disabled=true;$('packageStatus').textContent='Preparing report package…';
    try{
      const bytes=await UNMeetingReportPackage.build(prepared,corpora);
      if(report!==prepared||workspaceRevision!==revision){$('packageStatus').textContent='Your report changed. No package was downloaded; prepare the report again.';return;}
      if(save(bytes,name,'application/zip')){dirty=false;$('packageStatus').textContent='Report package downloaded. Extract it and open report.json to resume editing. Review source text and notes before sharing.';}
    }catch(e){$('packageStatus').textContent='Could not create report package: '+e.message;}
    finally{packaging=false;$('downloadPackage').disabled=!report;}
  };
  const selectedDeviceReport=()=>deviceLibrary.find(r=>r.id===deviceId);
  function deviceControls(){
    deviceSaved=!!selectedDeviceReport();
    $('deviceReportChoice').disabled=deviceBusy||!deviceAvailable||!deviceLibrary.length;
    $('refreshDeviceReports').disabled=deviceBusy;$('recoverDeviceReport').disabled=deviceBusy;
    $('openDeviceReport').disabled=deviceBusy||!deviceAvailable||!deviceSaved||!policy||!countries;
    $('deleteDeviceReport').disabled=deviceBusy||!deviceAvailable||!deviceSaved;
    $('saveDeviceReport').disabled=deviceBusy||!deviceAvailable||!report;
    $('saveDeviceReport').textContent=deviceSaved?'Replace selected device report':'Save on this device';
    $('saveNewDeviceReport').disabled=deviceBusy||!deviceAvailable||!report||!deviceLibrary.length||deviceLibrary.length>=UNReportStorage.MAX_REPORTS;
  }
  function showDeviceLibrary(){
    $('deviceReportChoice').replaceChildren();
    if(!deviceLibrary.some(r=>r.id===deviceId))deviceId=deviceLibrary[0]?.id||'current';
    for(const row of deviceLibrary){const option=document.createElement('option'),date=row.saved_at?new Date(row.saved_at):null,time=date&&Number.isFinite(date.getTime())?new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(date):'Save time unavailable (earlier device copy)';option.value=row.id;option.textContent=row.title+' · '+time+' · '+row.bytes.toLocaleString('en-US')+' bytes';$('deviceReportChoice').append(option);}
    $('deviceReportChoice').value=deviceId;deviceControls();
  }
  const deviceUsage=()=>deviceLibrary.length+' of 8 reports saved; '+deviceLibrary.reduce((n,r)=>n+r.bytes,0)+' of 25,000,000 report JSON bytes.';
  async function checkDeviceReport(){
    if(deviceBusy)return;deviceBusy=true;deviceControls();
    try{deviceLibrary=await UNReportStorage.list();deviceAvailable=true;$('recoverDeviceReport').hidden=true;showDeviceLibrary();$('deviceReportStatus').textContent=deviceLibrary.length?deviceUsage()+' Open a report explicitly to verify its sources.':'No report saved on this device. Prepare a report and choose Save on this device.';}
    catch(e){deviceAvailable=false;$('recoverDeviceReport').hidden=!e.legacy_recovery;$('deviceReportStatus').textContent=e.message;}
    finally{deviceBusy=false;deviceControls();}
  }
  $('recoverDeviceReport').onclick=async()=>{
    if(deviceBusy)return;deviceBusy=true;deviceControls();
    try{const text=await UNReportStorage.legacy();if(typeof text!=='string')throw Error('No earlier device JSON copy is available.');if(save(text,'un-device-report-recovery.json','application/json'))deviceSaveStatus('Earlier device copy downloaded unchanged. It has not been verified or removed; open the JSON file to verify its sources.');}
    catch(e){deviceSaveStatus('Could not recover earlier device copy: '+e.message);}
    finally{deviceBusy=false;deviceControls();}
  };
  $('refreshDeviceReports').onclick=checkDeviceReport;
  $('deviceReportChoice').onchange=()=>{deviceId=$('deviceReportChoice').value;deviceControls();};
  function deviceSaveStatus(message){$('deviceReportStatus').textContent=message;$('deviceSaveStatus').textContent=message;}
  async function saveDeviceReport(asNew=false){
    if(!report||deviceBusy||!deviceAvailable)return;
    const previous=asNew?null:selectedDeviceReport(),id=asNew?crypto.randomUUID():deviceId;
    if(previous&&!window.confirm('Replace “'+previous.title+'” in this browser profile? Download its JSON first if you need to retain it.'))return;
    const prepared=report,revision=workspaceRevision;deviceBusy=true;deviceControls();
    try{
      const saved=await UNReportStorage.write(JSON.stringify(Core.savedReport(prepared,corpora)),id,previous?.version||0);
      deviceLibrary=[saved,...deviceLibrary.filter(r=>r.id!==id)];deviceId=id;showDeviceLibrary();
      if(report===prepared&&workspaceRevision===revision){dirty=false;deviceSaveStatus('Report saved in this browser profile. '+deviceUsage()+' Nothing was uploaded. Download JSON for a portable copy.');}
      else deviceSaveStatus('The earlier prepared report was saved. Your newer edits remain unsaved; prepare and save again.');
    }catch(e){deviceSaveStatus('Could not save on this device: '+e.message);}
    finally{deviceBusy=false;deviceControls();}
  }
  $('saveDeviceReport').onclick=()=>saveDeviceReport();$('saveNewDeviceReport').onclick=()=>saveDeviceReport(true);
  $('openDeviceReport').onclick=async()=>{
    if(deviceBusy||!deviceAvailable)return;
    const chosen=selectedDeviceReport();if(!chosen)return;
    const ticket={id:++replacementSerial,revision:workspaceRevision};deviceBusy=true;deviceControls();
    try{
      const text=await UNReportStorage.read(chosen.id,chosen.version);if(typeof text!=='string'||new TextEncoder().encode(text).length>Core.LIMIT)throw Error('No supported device report found. Open a downloaded JSON copy instead.');
      const opened=await Core.openSaved(JSON.parse(text),policy,countries);
      if(!replacementCurrent(ticket))return;
      if(!await confirmReplacement('Opening the device report will replace your current sources, appendix selections and notes.'))return;
      if(!replacementCurrent(ticket))return;
      setCollection(opened.corpora,opened.settings,opened.selected,opened.appendix,opened.passage_notes);dirty=false;
      $('deviceReportStatus').textContent='Device report verified and opened. Prepare the report to rebuild its summaries.';
    }catch(e){$('deviceReportStatus').textContent='Could not open device report: '+e.message;}
    finally{deviceBusy=false;deviceControls();}
  };
  $('deleteDeviceReport').onclick=async()=>{
    const chosen=selectedDeviceReport();
    if(deviceBusy||!deviceAvailable||!chosen||!window.confirm('Remove “'+chosen.title+'” from this browser profile? Your currently open work and downloaded files will remain.'))return;
    deviceBusy=true;deviceControls();
    try{await UNReportStorage.remove(chosen.id,chosen.version);deviceLibrary=deviceLibrary.filter(r=>r.id!==chosen.id);showDeviceLibrary();dirty=!!corpora.length;deviceSaveStatus('Device copy removed. '+deviceUsage()+' Your currently open work and downloaded files are unchanged.');}
    catch(e){$('deviceReportStatus').textContent='Could not remove device copy: '+e.message;}
    finally{deviceBusy=false;deviceControls();}
  };
  checkDeviceReport();
  window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
  (async()=>{try{
    const read=async path=>{const r=await fetch(path,{credentials:'omit'});if(!r.ok)throw Error('Reporting setup unavailable.');return r.json();};
    [policy,countries]=await Promise.all([read('reporting-exclusions.json'),read('countries.json')]);Core.exclusions(policy);deviceControls();
    const now=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());$('meetingDate').value=now;
    $('sourceControls').disabled=false;
    try{handoff=UNMeetingReportSelection.read(location.search,policy);}catch(e){setStatus('Could not open meeting selection: '+e.message+' Choose a date or saved collection instead.',true);return;}
    if(handoff){$('archiveSelection').hidden=false;$('archiveSelectionInfo').textContent=handoff.meetings.length+' meetings selected'+(handoff.snapshot_id?' from archive snapshot '+handoff.snapshot_id:'')+'. Check the current official inventory before loading. Only public identifiers were transferred.';setStatus('Ready. Check the selected meetings. No transcript has been requested.');}
    else setStatus('Ready. Choose a meeting date or open a saved collection.');
  }catch(e){setStatus(e.message,true);}})();
})();
