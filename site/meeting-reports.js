/* Local reporting workspace; source loading is explicit and bounded. */
(()=>{
  'use strict';
  const $=id=>document.getElementById(id),Core=UNMeetingReport;
  let policy,countries,inventory=[],corpora=[],report=null,controller=null,shown=10,dirty=false,handoff=null,appendixIds=new Set(),notes=new Map(),bulkUndo=null;
  let printing=false,printTitle=null,printSnapshot=null;
  let workspaceRevision=0,replacementSerial=0,packaging=false,calendarExporting=false,deviceBusy=false,deviceAvailable=false,deviceSaved=false,deviceLibrary=[],deviceId='current';
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
  function invalidate(){workspaceRevision++;report=null;$('expressionEvidence').close();$('expressionEvidenceBody').replaceChildren();$('printStatus').textContent='Prepare the report before printing.';$('wordStatus').textContent='Prepare the report before downloading Word.';$('reportPreview').replaceChildren();for(const id of ['downloadReport','downloadWord','printReportButton','saveReport','downloadEvidence','downloadPassageNotes','downloadPackage','saveDeviceReport','downloadReviewEntry'])$(id).disabled=true;$('passageNotesExportStatus').textContent='Prepare a report containing passage notes.';$('calendarStatus').textContent='Prepare the report and choose a review date.';$('packageStatus').textContent='Prepare the report before downloading its package.';$('reportState').textContent='Settings or selection changed. Prepare the report to update its exports.';dirty=!!corpora.length;deviceControls();}
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
    bulkControls(rows);
    $('evidenceResults').innerHTML=Core.evidenceHTML(rows.slice(0,shown));$('moreEvidence').hidden=rows.length<=shown;
    for(const [i,article] of [...$('evidenceResults').children].entries()){
      const record=rows[i],label=document.createElement('label'),input=document.createElement('input');
      label.className='appendix-choice';input.type='checkbox';input.checked=appendixIds.has(record.id);input.setAttribute('aria-label','Include passage '+record.id+' in appendix');
      input.onchange=()=>{clearBulkUndo();if(input.checked)appendixIds.add(record.id);else appendixIds.delete(record.id);$('appendixMode').value='selected';invalidate();appendixCount();if($('onlySelectedEvidence').checked)search();else bulkControls(rows);};
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
  function clearBulkUndo(){bulkUndo=null;$('undoBulkAppendix').hidden=true;$('undoBulkAppendix').disabled=true;}
  function rememberBulk(){bulkUndo={mode:$('appendixMode').value,record_ids:[...appendixIds]};$('undoBulkAppendix').hidden=false;$('undoBulkAppendix').disabled=false;}
  function bulkControls(rows){
    const missing=rows.filter(r=>!appendixIds.has(r.id)).length,present=rows.length-missing;
    $('addMatchingAppendix').textContent='Add '+missing+' new '+(missing===1?'match':'matches');$('addMatchingAppendix').disabled=!missing;
    $('removeMatchingAppendix').textContent='Remove '+present+' selected '+(present===1?'match':'matches');$('removeMatchingAppendix').disabled=!present;
    const change=add=>{
      if(!rows.some(r=>appendixIds.has(r.id)!==add))return;
      rememberBulk();for(const r of rows){if(add)appendixIds.add(r.id);else appendixIds.delete(r.id);}
      $('appendixMode').value='selected';invalidate();search();
    };
    $('addMatchingAppendix').onclick=()=>change(true);$('removeMatchingAppendix').onclick=()=>change(false);
  }
  $('undoBulkAppendix').onclick=()=>{
    if(!bulkUndo)return;appendixIds=new Set(bulkUndo.record_ids);$('appendixMode').value=bulkUndo.mode;clearBulkUndo();invalidate();search();$('clearAppendix').focus();
  };
  function notesCount(){$('passageNotesCount').textContent=notes.size+' passage '+(notes.size===1?'note':'notes')+'. Saved in report HTML and JSON, separately from source text. The full evidence CSV and reusable preferences exclude your notes. Removing a meeting removes its notes.';}
  function appendixCount(){
    $('appendixCount').textContent=$('appendixMode').value==='selected'?appendixIds.size+(appendixIds.size===1?' passage selected for the appendix.':' passages selected for the appendix.')+' Summaries, country expressions and the full evidence CSV still use all passages from selected meetings.':'Template default: the evidence digest includes all passages; other templates omit the appendix. Select a passage to create a custom appendix.';
  }
  function pruneAppendix(){
    clearBulkUndo();
    const meetings=new Set(selected()),known=new Set(corpora.flatMap(c=>c.records).filter(r=>meetings.has(r.meeting_slug)).map(r=>r.id));
    appendixIds=new Set([...appendixIds].filter(id=>known.has(id)));
    notes=new Map([...notes].filter(([id])=>known.has(id)));
  }
  function checkbox(row,loaded=false,checked=false){
    const label=document.createElement('label'),input=document.createElement('input'),span=document.createElement('span');input.type='checkbox';input.value=row.slug;input.checked=checked;
    input.setAttribute('aria-label',(loaded?'Include ':'Select ')+row.title);
    input.disabled=!Core.allowed(row.date.slice(0,10),row.slug,policy)||(!loaded&&!row.hasTranscript);
    span.textContent=row.date.slice(0,10)+' · '+row.title+' · '+(loaded?row.status:input.disabled?'Unavailable or excluded':'Transcript listed');
    input.addEventListener('change',()=>{if(loaded){pruneAppendix();refreshEvidenceFilters();invalidate();shown=10;search();}else loadButtons();});
    label.append(input,span);return label;
  }
  function setCollection(next,prefs=null,selection=null,chosen={mode:'template',record_ids:[]},passage_notes=[],preserveSettings=false){
    clearBulkUndo();corpora=next;$('addCollection').disabled=!corpora.length;loadButtons();$('loadedMeetings').replaceChildren();
    appendixIds=new Set(chosen.record_ids);$('appendixMode').value=chosen.mode;$('onlySelectedEvidence').checked=false;
    notes=new Map(passage_notes.map(n=>[n.record_id,n.text]));
    for(const row of corpora.flatMap(c=>c.coverage).filter(r=>r.slug))$('loadedMeetings').append(checkbox(row,true,!selection||selection.includes(row.slug)));
    if(!preserveSettings||!corpora.length){$('reviewDate').value='';$('calendarAssessment').checked=false;}
    if(!preserveSettings){
      if(prefs)setQuestions(prefs.questions);
      if(prefs){for(const [id,key] of [['reportTemplate','template'],['mission','mission'],['reportTitle','title'],['priorities','priorities'],['analystNotes','notes']])$(id).value=prefs[key];}
      else $('analystNotes').value='';
    }
    $('reportControls').disabled=!corpora.length;$('evidenceSearch').disabled=!corpora.length;$('appendixControls').disabled=!corpora.length;
    $('collectionStatus').textContent=corpora.flatMap(c=>c.coverage).filter(r=>r.slug).length+' loaded meeting records; '+corpora.reduce((n,c)=>n+c.records.length,0)+' English source segments. Original response hashes verified. Last source check: '+corpora.map(c=>c.collection.checked_at||c.collection.collected_at||'Unknown').join('; ')+'.';
    if(!corpora.length)$('collectionStatus').textContent='No collection loaded.';
    showSourceCollections();refreshEvidenceFilters(true);invalidate();shown=10;search();
  }
  function showSourceCollections(){
    $('manageSources').hidden=!corpora.length;$('sourceCollections').replaceChildren();
    corpora.forEach((c,index)=>{
      const row=document.createElement('div'),label=document.createElement('p'),titles=document.createElement('p'),button=document.createElement('button'),meetings=c.coverage.filter(m=>m.slug);
      row.className='source-collection';label.textContent='Collection '+(index+1)+' · '+meetings.length+' meeting'+(meetings.length===1?'':'s')+' · '+c.records.length+' source segments · '+new TextEncoder().encode(JSON.stringify(c)).length.toLocaleString('en-US')+' source JSON bytes';
      titles.textContent=meetings.slice(0,2).map(m=>m.date+' · '+String(m.title||m.slug).slice(0,160)).join('; ')+(meetings.length>2?'; '+(meetings.length-2)+' more meetings':'');
      button.type='button';button.className='secondary';button.textContent='Remove collection '+(index+1);button.onclick=()=>removeSourceCollection(c,button);
      row.append(label,titles,button);$('sourceCollections').append(row);
    });
  }
  $('keepSources').onclick=()=>$('removeSources').close('keep');
  $('confirmRemoveSources').onclick=()=>$('removeSources').close('remove');
  async function removeSourceCollection(collection,button){
    if($('removeSources').open)return;
    const ticket={id:++replacementSerial,revision:workspaceRevision};
    try{
      const plan=Core.planSourceRemoval(corpora,corpora.indexOf(collection),{selected:selected(),appendix:appendix(),passage_notes:passageNotes()});
      $('removeSourcesMessage').textContent=plan.removed_meetings.length+' meeting'+(plan.removed_meetings.length===1?'':'s')+', '+plan.removed_notes+' passage note'+(plan.removed_notes===1?'':'s')+' and '+plan.removed_appendix+' appendix selection'+(plan.removed_appendix===1?'':'s')+' will be removed from current work. '+(plan.clear_assessment?'This is the last collection: the current assessment will also be cleared. Reusable mission settings and questions stay.':'The current assessment, mission settings and annotations on remaining sources stay.');
      $('removeSourcesMeetings').replaceChildren();for(const m of plan.removed_meetings){const item=document.createElement('li');item.textContent=m.date+' · '+m.title;$('removeSourcesMeetings').append(item);}
      const dialog=$('removeSources');dialog.returnValue='keep';
      const choice=await new Promise(resolve=>{dialog.addEventListener('close',()=>resolve(dialog.returnValue),{once:true});dialog.showModal();});
      if(!replacementCurrent(ticket))return;
      if(choice!=='remove'){setStatus('Sources kept. Current work is unchanged.');if(button.isConnected)button.focus();return;}
      if(plan.clear_assessment)$('analystNotes').value='';
      setCollection(plan.corpora,null,plan.selected,plan.appendix,plan.passage_notes,true);
      setStatus(plan.clear_assessment?'Current sources and assessment cleared. Mission settings and questions kept. Open a collection or report to continue.':'Source collection removed. Remaining notes and settings kept. Select meetings as needed and prepare the report again.');
      ($('sourceCollections').querySelector('button')||$('openCollection')).focus();
    }catch(e){if(ticket.id===replacementSerial)setStatus('Could not remove sources: '+e.message+' Current work kept.',true);}
  }
  function loadButtons(loading=!!controller){
    const checked=!!document.querySelector('#inventory input:checked');
    $('loadMeetings').disabled=loading||!checked;$('addSelectedMeetings').disabled=loading||!checked||!corpora.length;
  }
  function busy(value){$('sourceControls').disabled=value;loadButtons(value);$('cancelLoad').hidden=!value;for(const e of $('inventory').querySelectorAll('input')){const m=inventory.find(m=>m.slug===e.value);e.disabled=value||!m?.hasTranscript||!Core.allowed(m.date.slice(0,10),m.slug,policy);}}

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
  $('meetingDate').oninput=()=>{clearHandoff();inventory=[];$('inventory').replaceChildren();loadButtons();};
  async function loadSelected(add=false){
    const ids=new Set([...$('inventory').querySelectorAll('input:checked')].map(e=>e.value)),chosen=inventory.filter(m=>ids.has(m.slug));
    if(!chosen.length||chosen.length>5){setStatus('Select between one and five meetings per load.',true);return;}
    if(add){
      if(!corpora.length){setStatus('Open or load a report before adding transcripts.',true);return;}
      const loaded=new Set(corpora.flatMap(c=>c.coverage).filter(m=>m.slug).map(m=>m.slug));
      if(chosen.some(m=>loaded.has(m.slug))){setStatus('Already loaded meeting selected. Uncheck it before adding; current sources and revisions are kept.',true);return;}
      if(corpora.length+chosen.length>10||loaded.size+chosen.length>100){setStatus('Addition exceeds ten source bundles or 100 meetings. Remove loaded collections or use a separate report. Current work kept.',true);return;}
      if(chosen.some(m=>!m.hasTranscript||!Core.allowed(m.date.slice(0,10),m.slug,policy))){setStatus('Unavailable or reserved meeting blocked. No transcripts requested.',true);return;}
    }
    const ticket={id:++replacementSerial,revision:workspaceRevision};
    if(!add&&!await confirmReplacement('Loading these meetings will replace your current sources, appendix selections and notes.')){if(ticket.id===replacementSerial)setStatus('Current report kept. No transcripts requested.');return;}
    if(!replacementCurrent(ticket))return;
    const next=[],loading=new AbortController();let failure=null,cancelled=false;
    try{
      controller=loading;busy(true);
      for(const m of chosen){
        if(loading.signal.aborted||ticket.id!==replacementSerial||ticket.revision!==workspaceRevision)break;
        if(!Core.allowed(m.date.slice(0,10),m.slug,policy))throw Error('Reserved meeting blocked.');
        const c=await UNCollector.collect(UNMeetingPickerCore.selection(m.date.slice(0,10),m),countries,{signal:loading.signal,progress:message=>{if(ticket.id===replacementSerial)setStatus(message);}});
        await Core.validateCorpora([...(add?corpora:[]),...next,c],policy,countries);next.push(c);
      }
    }catch(e){cancelled=e.name==='AbortError';failure=cancelled?'Loading cancelled.':e.message;}
    finally{if(controller===loading){controller=null;busy(false);}}
    if(ticket.id!==replacementSerial)return;
    if(loading.signal.aborted||cancelled){setStatus('Loading cancelled. Current work kept; no replacement applied.');return;}
    if(!replacementCurrent(ticket))return;
    const partial=!!failure||next.some(c=>c.collection.partial);
    if(add){
      if(partial||next.length!==chosen.length){setStatus('No sources added: '+(failure||'retrieval is incomplete.')+' Current work kept. Use a separate report to inspect incomplete sources.',true);return;}
      try{
        const combined=[...corpora,...next],selection=[...selected(),...next.flatMap(c=>c.coverage).filter(m=>m.slug).map(m=>m.slug)],prefs=options(),chosenAppendix=appendix(),passage_notes=passageNotes();
        if(Core.savedStateBytes(combined,{settings:prefs,selected:selection,appendix:chosenAppendix,passage_notes})>Core.LIMIT)throw Error('Combined saved report exceeds 25 MB, including your notes and selections.');
        setCollection(combined,null,selection,chosenAppendix,passage_notes,true);
        for(const input of $('inventory').querySelectorAll('input:checked'))input.checked=false;loadButtons();
        setStatus('Transcripts added: '+next.length+' meeting bundles. Current notes, settings and previous selections kept. Prepare the report again and save JSON or ZIP to retain the addition.');
      }catch(e){setStatus('No sources added: '+e.message+' Current work kept.',true);}
      return;
    }
    if(next.length&&partial&&!await confirmReplacement(next.length+' of '+chosen.length+' meeting bundles loaded; retrieval is incomplete. Replace your current report with these available sources?',true)){if(ticket.id===replacementSerial)setStatus('Current report kept. Incomplete replacement was not applied.');return;}
    if(!replacementCurrent(ticket))return;
    if(next.length)setCollection(next);
    setStatus(failure?(failure+' '+next.length+' meeting bundles applied; current work is unchanged if none completed.'):'Retrieval finished.'+(partial?' Coverage is incomplete.':'')+' Check each meeting outcome, search available evidence, and prepare a report.',!!failure);
  };
  $('loadMeetings').onclick=()=>loadSelected();
  $('addSelectedMeetings').onclick=()=>loadSelected(true);
  $('cancelLoad').onclick=()=>controller?.abort();
  async function readSavedFile(file){
    if(file.size>Core.LIMIT)throw Error('Use a JSON export or report-package ZIP under 25 MB.');
    const header=new Uint8Array(await file.slice(0,4).arrayBuffer());
    if(/\.zip$/i.test(file.name)||(header[0]===0x50&&header[1]===0x4b))return UNMeetingReportPackage.read(new Uint8Array(await file.arrayBuffer()));
    return JSON.parse(await file.text());
  }
  $('openCollection').onchange=async event=>{
    const file=event.target.files[0];if(!file)return;
    const ticket={id:++replacementSerial,revision:workspaceRevision};setStatus('Checking saved sources…');
    try{
      const opened=await Core.openSaved(await readSavedFile(file),policy,countries);
      if(!replacementCurrent(ticket))return;
      if(!await confirmReplacement('Opening this file will replace your current sources, appendix selections and notes.')){if(ticket.id===replacementSerial)setStatus('Current report kept. The selected file was not applied.');return;}
      if(!replacementCurrent(ticket))return;
      setCollection(opened.corpora,opened.settings,opened.selected,opened.appendix,opened.passage_notes);setStatus('Saved sources verified. Prepare the report to rebuild its summaries; saved derived claims are not trusted.');
    }catch(e){if(ticket.id===replacementSerial)setStatus('Could not open file: '+e.message,true);}finally{if(event.target.files[0]===file)event.target.value='';}
  };
  $('addCollection').onchange=async event=>{
    const file=event.target.files[0];if(!file)return;
    const ticket={id:++replacementSerial,revision:workspaceRevision};setStatus('Checking sources to add…');
    try{
      const added=await Core.appendSaved(corpora,await readSavedFile(file),policy,countries);
      if(!replacementCurrent(ticket))return;
      const selection=[...new Set([...selected(),...added.selected_added])],prefs=options(),chosen=appendix(),passage_notes=passageNotes();
      if(Core.savedStateBytes(added.corpora,{settings:prefs,selected:selection,appendix:chosen,passage_notes})>Core.LIMIT)throw Error('Combined saved report exceeds 25 MB, including your notes and selections. Use fewer sources or a separate report.');
      setCollection(added.corpora,null,selection,chosen,passage_notes,true);
      setStatus('Sources added: '+added.selected_added.length+(added.selected_added.length===1?' meeting selection.':' meeting selections.')+' Current notes, settings and existing meeting selections kept.'+(added.incoming_report?' Notes and settings from the added report were not copied.':'')+' Prepare the report again to include the added evidence.');
    }catch(e){if(ticket.id===replacementSerial)setStatus('Could not add sources: '+e.message+' Current work kept.',true);}
    finally{if(event.target.files[0]===file)event.target.value='';}
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
  $('appendixMode').onchange=()=>{clearBulkUndo();if($('appendixMode').value==='template')appendixIds.clear();invalidate();search();};
  $('clearAppendix').onclick=()=>{if(appendixIds.size||$('appendixMode').value!=='selected')rememberBulk();appendixIds.clear();$('appendixMode').value='selected';invalidate();search();};
  $('prepareReport').onclick=()=>{try{report=Core.build(corpora,selected(),options(),appendix(),passageNotes());workspaceRevision++;$('reportPreview').innerHTML=Core.reportHTML(report,{preview:true});for(const id of ['downloadReport','downloadWord','printReportButton','saveReport','downloadEvidence','downloadPackage','saveDeviceReport'])$(id).disabled=false;$('downloadPackage').disabled=packaging;if(!packaging)$('packageStatus').textContent='Ready to download a report package.';$('reportState').textContent='Report ready: '+report.meetings.length+' meetings. Review source evidence before circulation.';$('printReportButton').disabled=printing;$('printStatus').textContent='Ready to print the complete report or use the browser’s PDF destination.';$('wordStatus').textContent='Ready to download an editable Word reading copy.';$('downloadPassageNotes').disabled=!report.passage_notes.length;$('passageNotesExportStatus').textContent=report.passage_notes.length?report.passage_notes.length+' passage notes from the selected meetings. Ready to download.':'No passage notes in this prepared report.';dirty=true;deviceControls();calendarControls(true);}catch(e){invalidate();setStatus(e.message,true);}};
  function calendarControls(announce=false){
    const calendar=globalThis.UNMeetingReportCalendar,valid=!!calendar&&calendar.validDate($('reviewDate').value);
    $('downloadReviewEntry').disabled=calendarExporting||!report||!valid;
    if(announce)$('calendarStatus').textContent=!report?'Prepare the report and choose a review date.':!calendar?'Calendar export is unavailable in this browser session.':valid?'Ready to download a personal review entry.':'Choose a valid personal review date from 1900 through 9998.';
  }
  for(const id of ['reviewDate','calendarAssessment'])$(id).oninput=()=>calendarControls(true);
  $('downloadReviewEntry').onclick=async()=>{
    if(!report||calendarExporting)return;
    const prepared=report,revision=workspaceRevision,date=$('reviewDate').value,includeAssessment=$('calendarAssessment').checked,name=reportName('-review-'+date+'.ics');calendarExporting=true;calendarControls();
    try{
      const bytes=await UNMeetingReportCalendar.build(prepared,date,{includeAssessment});
      if(report!==prepared||workspaceRevision!==revision||$('reviewDate').value!==date||$('calendarAssessment').checked!==includeAssessment){$('calendarStatus').textContent='Your report or calendar options changed. No calendar file downloaded; prepare again if needed.';return;}
      if(save(bytes,name,'text/calendar;charset=utf-8'))$('calendarStatus').textContent='Personal review entry downloaded. Import the ICS in your calendar app and check its date and visibility. Save JSON or ZIP separately to resume the report.';
    }catch(e){$('calendarStatus').textContent='Could not create calendar entry: '+e.message+' Current work kept.';}
    finally{calendarExporting=false;calendarControls();}
  };
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
  function preparePrint(){
    if(printing&&printSnapshot===report&&report)return;
    if(printing)clearPrint();
    if(!report)throw Error('Prepare a report before printing.');
    const html=Core.reportHTML(report),area=$('printReport');
    if(new TextEncoder().encode(html).length>Core.LIMIT)throw Error('Printable report exceeds 25 MB. Choose fewer meetings; no truncated report was printed.');
    area.innerHTML=html;
    // Keep PDF destinations distinct from the same headings in the screen preview.
    const anchors=new Map();
    for(const node of area.querySelectorAll('[id]')){const old=node.id;node.id='print-'+old;anchors.set(old,node.id);}
    for(const link of area.querySelectorAll('a[href^="#"]')){const next=anchors.get(link.getAttribute('href').slice(1));if(next)link.setAttribute('href','#'+next);}
    for(const node of area.querySelectorAll('[aria-labelledby],[aria-describedby]'))for(const attr of ['aria-labelledby','aria-describedby'])if(node.hasAttribute(attr))node.setAttribute(attr,node.getAttribute(attr).split(/\s+/).map(id=>anchors.get(id)||id).join(' '));
    for(const details of area.querySelectorAll('details'))details.open=true;
    printTitle=document.title;document.title=reportName('');printing=true;printSnapshot=report;
    $('printReportButton').disabled=true;$('returnFromPrint').hidden=false;
  }
  function clearPrint(){
    $('printReport').replaceChildren();if(printTitle!==null)document.title=printTitle;
    printTitle=null;printing=false;printSnapshot=null;$('printReportButton').disabled=!report;$('returnFromPrint').hidden=true;
  }
  window.addEventListener('beforeprint',()=>{
    try{preparePrint();}
    catch(e){clearPrint();$('printReport').textContent='Report not printed: '+e.message;$('printStatus').textContent=e.message;}
  });
  function finishPrint(){const active=printing;clearPrint();if(active)$('printStatus').textContent='Print view closed. Check your printer or PDF file. Save JSON or ZIP separately to resume work.';}
  window.addEventListener('afterprint',finishPrint);
  $('returnFromPrint').onclick=finishPrint;
  $('printReportButton').onclick=()=>{
    if(!report||printing)return;
    try{preparePrint();$('printStatus').textContent='Choose your printer or the browser’s PDF destination. If controls do not reset after closing the dialog, choose Return to report.';window.print();}
    catch(e){clearPrint();$('printStatus').textContent='Could not print: '+e.message+' Download HTML to print it separately.';}
  };
  $('downloadWord').onclick=()=>{
    if(!report)return;
    try{if(save(UNMeetingReportWord.build(report),reportName('.docx'),'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))$('wordStatus').textContent='Word reading copy downloaded.';}
    catch(e){$('wordStatus').textContent='Could not create Word report: '+e.message;}
  };
  $('downloadReport').onclick=()=>{if(report)save(Core.standalone(report),reportName('.html'),'text/html');};
  $('saveReport').onclick=()=>{if(report&&save(JSON.stringify(Core.savedReport(report,corpora)),reportName('.json'),'application/json'))dirty=false;};
  $('downloadEvidence').onclick=()=>{if(report)save(Core.evidenceCSV(report.records),reportName('-evidence.csv'),'text/csv;charset=utf-8');};
  $('downloadPassageNotes').onclick=()=>{
    if(!report||!report.passage_notes.length)return;
    try{if(save(Core.passageNotesCSV(report),reportName('-passage-notes.csv'),'text/csv;charset=utf-8'))$('passageNotesExportStatus').textContent='Passage notes downloaded. Save JSON or ZIP separately to resume work.';}
    catch(e){$('passageNotesExportStatus').textContent='Could not export passage notes: '+e.message+' Current work kept.';}
  };
  $('downloadPackage').onclick=async()=>{
    if(!report||packaging)return;
    const prepared=report,revision=workspaceRevision,name=reportName('.zip');packaging=true;$('downloadPackage').disabled=true;$('packageStatus').textContent='Preparing report package…';
    try{
      const bytes=await UNMeetingReportPackage.build(prepared,corpora);
      if(report!==prepared||workspaceRevision!==revision){$('packageStatus').textContent='Your report changed. No package was downloaded; prepare the report again.';return;}
      if(save(bytes,name,'application/zip')){dirty=false;$('packageStatus').textContent='Report package downloaded. Open this ZIP in the reporting workspace to resume editing. Review source text and notes before sharing.';}
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
