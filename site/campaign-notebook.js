/* Browser-session campaign notebook; persistence is an explicit JSON download. */
(()=>{
 'use strict';
 const $=id=>document.getElementById(id),Core=UNCampaignNotebook,campaignKeys=['title','candidate','body','election_date','notes'],entryKeys=['country','contact','role','email','status','status_date','follow_up_date','reference','notes'];
 let registry,entries=[],editing=null,dirty=false,entryDirty=false,revision=0,actionSerial=0,fileSerial=0,exportRevision=-1,exportStamp='';
 const status=(message,error=false)=>{$('notebookStatus').textContent=message;$('notebookStatus').classList.toggle('error',error);};
 const read=(prefix,keys)=>Object.fromEntries(keys.map(k=>{const input=$(prefix+k);if(input.validity?.badInput)throw Error('Complete or clear the date input before applying or exporting.');return [k,input.value];}));
 const data=()=>({schema:Core.SCHEMA,campaign:read('campaign_',campaignKeys),entries});
 function state(){for(const id of ['saveNotebook','downloadNotebookCSV','downloadNotebookHTML'])$(id).disabled=entryDirty;$('notebookSaveState').textContent=entryDirty?'Apply or discard the country form before exporting.':dirty?'Unsaved notebook changes. Download JSON to keep them.':'Current notebook has no unsaved applied changes.';$('entryState').textContent=entryDirty?'Unapplied country form changes.':editing?'Editing '+editing+'. Country identity stays fixed.':'Choose a place to add a record.';}
 function changed(form=false){revision++;if(form)entryDirty=true;else dirty=true;state();}
 function ticket(){const t={action:++actionSerial,revision};if($('notebookConfirm').open)$('notebookConfirm').close('keep');return t;}
 function current(t){if(t.action!==actionSerial)return false;if(t.revision!==revision){status('Your notebook changed while the action was pending. Current work kept.');return false;}return true;}
 function ask(message,proceed,needed=true){
  if(!needed)return Promise.resolve(true);
  const dialog=$('notebookConfirm');$('notebookConfirmMessage').textContent=message;$('notebookProceed').textContent=proceed;dialog.returnValue='keep';
  return new Promise(resolve=>{dialog.addEventListener('close',()=>resolve(dialog.returnValue==='proceed'),{once:true});dialog.showModal();});
 }
 async function approve(t,message,label,needed=true){const proceed=await ask(message,label,needed);if(!current(t))return false;if(!proceed){status('Current notebook and country form kept.');return false;}return true;}
 $('notebookKeep').onclick=()=>$('notebookConfirm').close('keep');$('notebookProceed').onclick=()=>$('notebookConfirm').close('proceed');
 function clearForm(){editing=null;entryDirty=false;for(const key of entryKeys)$('entry_'+key).value=key==='status'?'unrecorded':'';$('entry_country').disabled=false;state();}
 function render(){
  $('notebookTotal').textContent=entries.length+' country/territory records. Each contributes one current outreach status.';
  $('notebookSummary').replaceChildren();for(const [key,count] of Object.entries(Core.summary(entries))){const li=document.createElement('li');li.textContent=Core.STATUSES[key]+': '+count;$('notebookSummary').append(li);}
  let rows;try{if($('notebookDueFilter').validity.badInput)throw Error('Complete or clear the follow-up filter date.');rows=Core.view(entries,{query:$('notebookSearch').value,status:$('notebookStatusFilter').value,due:$('notebookDueFilter').value});}catch(e){$('notebookListCount').textContent='Check the list filters: '+e.message;$('notebookRecords').replaceChildren();return;}$('notebookListCount').textContent='Showing '+rows.length+' of '+entries.length+' records. Downloads include all records.';$('notebookRecords').replaceChildren();
  if(!rows.length){const p=document.createElement('p');p.textContent=entries.length?'No records match these list filters.':'No country/territory record has been added. This does not describe unrecorded outreach.';$('notebookRecords').append(p);}
  for(const e of rows){
   const article=document.createElement('article');article.className='notebook-record';const heading=document.createElement('h3');heading.textContent=e.country;article.append(heading);
   for(const text of [Core.STATUSES[e.status]+' · Status date: '+(e.status_date||'Not recorded'),'Follow-up: '+(e.follow_up_date||'Not recorded'),'Lead contact (user-entered): '+(e.contact||'Not recorded')]){const p=document.createElement('p');p.textContent=text;article.append(p);}
   const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Contact and source notes';details.append(summary);for(const [label,value] of [['Role / organization',e.role],['Contact address (unverified)',e.email],['Source / conversation reference',e.reference],['Country notes',e.notes]]){const p=document.createElement('p');p.className='notebook-notes';p.textContent=label+': '+(value||'Not recorded');details.append(p);}article.append(details);
   const edit=document.createElement('button');edit.type='button';edit.className='secondary';edit.textContent='Edit '+e.country;edit.onclick=()=>editEntry(e.country);const remove=document.createElement('button');remove.type='button';remove.className='secondary';remove.textContent='Remove '+e.country;remove.onclick=()=>removeEntry(e.country);article.append(edit,remove);$('notebookRecords').append(article);
  }
 }
 function apply(value){for(const key of campaignKeys)$('campaign_'+key).value=value.campaign[key];entries=value.entries;revision++;dirty=false;clearForm();$('notebookSearch').value='';$('notebookStatusFilter').value='';$('notebookDueFilter').value='';render();state();}
 async function editEntry(country){const t=ticket();if(!await approve(t,'Editing another record will discard the current country form. Applied notebook records stay intact.','Discard form and edit',entryDirty))return;const e=entries.find(e=>e.country===country);if(!e){status('This record is no longer in the notebook.',true);return;}clearForm();editing=country;for(const key of entryKeys)$('entry_'+key).value=e[key];$('entry_country').disabled=true;revision++;state();$('entry_contact').focus();}
 async function removeEntry(country){
  const t=ticket();if(entryDirty){status('Apply or discard country form changes before removing a record.',true);return;}
  if(!await approve(t,'Remove the current outreach record for '+country+'? Downloaded files remain separate.','Remove record'))return;
  try{const next=Core.withoutEntry(data(),country,registry);entries=next.entries;if(editing===country)clearForm();changed();render();$('notebookListHeading').focus();status('Country record removed from this session. Download JSON to keep the change.');}catch(e){if(current(t))status(e.message,true);}
 }
 for(const key of campaignKeys)$('campaign_'+key).oninput=()=>changed();for(const key of entryKeys)$('entry_'+key).oninput=()=>changed(true);
 $('entryForm').onsubmit=event=>{event.preventDefault();ticket();try{const next=Core.withEntry(data(),read('entry_',entryKeys),registry,editing);entries=next.entries;clearForm();changed();render();status('Country record applied in this session. Download JSON to keep it.');$('entry_country').focus();}catch(e){status(e.message,true);}};
 $('discardEntry').onclick=async()=>{const t=ticket();if(!await approve(t,'Discard the unapplied country form changes? Applied notebook records stay intact.','Discard form',entryDirty))return;clearForm();revision++;state();status('Country form cleared. Applied notebook records kept.');$('entry_country').focus();};
 $('newNotebook').onclick=async()=>{const t=ticket();if(!await approve(t,'A new notebook will replace the current campaign and country form. Download JSON first if you need this version.','Start new notebook',dirty||entryDirty))return;apply(Core.empty());status('New notebook ready. Nothing is saved automatically.');$('campaign_title').focus();};
 $('openNotebook').onchange=async event=>{
  const selection=++fileSerial,t=ticket(),file=event.target.files[0];if(!file){status('No notebook file selected. Current work kept.');return;}status('Checking campaign notebook…');
  try{if(file.size>Core.LIMIT)throw Error('Use a campaign notebook JSON file no larger than 1 MiB.');const bytes=await file.arrayBuffer();if(!current(t))return;if(bytes.byteLength>Core.LIMIT)throw Error('Notebook exceeds 1 MiB.');const raw=new TextDecoder('utf-8',{fatal:true}).decode(bytes),next=Core.validate(JSON.parse(raw),registry);if(!current(t))return;if(!await approve(t,'Opening this file will replace the campaign, country records and any country form. Download JSON first if you need this version.','Replace notebook',dirty||entryDirty))return;apply(next);status('Campaign notebook opened. Records are user-entered, not verified votes or identities.');}
  catch(e){if(current(t))status('Could not open notebook: '+e.message+' Current work kept.',true);}
  finally{if(selection===fileSerial&&event.target.files[0]===file)event.target.value='';}
 };
 function save(bytes,name,mime){let url;const release=()=>{if(url)try{URL.revokeObjectURL(url);}catch{}};try{const blob=new Blob([bytes],{type:mime});if(blob.size>Core.LIMIT)throw Error('Download exceeds 1 MiB; nothing was truncated.');url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(release,1000);return true;}catch(e){release();status('Could not start download: '+e.message+' Current work kept.',true);return false;}}
 function snapshot(){if(entryDirty)throw Error('Apply or discard the country form before exporting.');const value=Core.validate(data(),registry);if(exportRevision!==revision){exportRevision=revision;exportStamp=new Date().toISOString().replace(/[-:.]/g,'');}return {value,name:'un-campaign-notebook-'+exportStamp,revision};}
 $('saveNotebook').onclick=()=>{try{const s=snapshot();if(save(JSON.stringify(s.value),s.name+'.json','application/json')){if(s.revision===revision)dirty=false;state();status('Notebook JSON download started. Check your downloads before closing.');}}catch(e){status(e.message,true);}};
 $('downloadNotebookCSV').onclick=()=>{try{const s=snapshot();if(save(Core.csv(s.value,registry),s.name+'-countries.csv','text/csv;charset=utf-8'))status('All-country CSV download started. Keep JSON separately to reopen; campaign-level notes are excluded from CSV.');}catch(e){status(e.message,true);}};
 $('downloadNotebookHTML').onclick=()=>{try{const s=snapshot();if(save(Core.html(s.value,registry),s.name+'.html','text/html'))status('Complete reading HTML download started. Keep JSON separately to reopen work.');}catch(e){status(e.message,true);}};
 for(const id of ['notebookSearch','notebookStatusFilter','notebookDueFilter'])$(id).oninput=()=>{try{render();}catch(e){status(e.message,true);}};
 $('clearNotebookFilters').onclick=()=>{$('notebookSearch').value='';$('notebookStatusFilter').value='';$('notebookDueFilter').value='';render();$('notebookSearch').focus();};
 window.addEventListener('beforeunload',event=>{if(dirty||entryDirty){event.preventDefault();event.returnValue='';}});
 (async()=>{try{const response=await fetch('countries.json');if(!response.ok)throw Error('Country/territory registry could not be loaded.');registry=await response.json();for(const country of Core.countries(registry)){const option=document.createElement('option');option.value=country;option.textContent=country;$('entry_country').append(option);}for(const [key,label] of Object.entries(Core.STATUSES)){for(const id of ['entry_status','notebookStatusFilter']){const option=document.createElement('option');option.value=key;option.textContent=label;$(id).append(option);}}apply(Core.empty());$('notebookWorkspace').disabled=false;status('Ready. Records stay in this session until you download JSON.');}catch(e){status(e.message+' Reload the page to try again.',true);}})();
})();
