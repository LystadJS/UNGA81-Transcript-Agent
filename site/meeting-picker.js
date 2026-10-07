/* Single-meeting controls reuse the existing collector, analyses and report exports. */
(function(){
  'use strict';
  const $=id=>document.getElementById(id),C=UNMeetingPickerCore;
  let inventory=null,lookup=null,generation=0,selected=null;
  const panel=document.createElement('fieldset');panel.className='meeting-picker';
  panel.innerHTML='<legend>Choose what to analyze</legend><label>Selection mode<select id="meetingSelectionMode"><option value="range">Dates and meeting scope</option><option value="single">One individual meeting</option></select></label><div id="singleMeetingControls" hidden><div class="analysis-grid"><label>Meeting date<input id="singleMeetingDate" type="date"></label><div class="meeting-picker-actions"><button id="findMeetings" type="button">Find meetings</button><button id="cancelMeetingLookup" type="button" disabled>Cancel search</button></div></div><p id="meetingListStatus" role="status" aria-live="polite">Choose a date to list the meetings in the UN transcript inventory.</p><label>Meeting<select id="individualMeeting" disabled><option value="">Select a meeting after searching</option></select></label><p id="selectedMeetingInfo"></p><p class="method-note">The list includes every meeting returned for the date, not only General Debate. A transcript may be pending or unavailable in English. Selecting a meeting resets the date range, scope and region; an optional topic can still narrow the report.</p></div>';
  $('analysisForm').prepend(panel);
  const dateParts=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
  const part=k=>dateParts.find(p=>p.type===k).value;$('singleMeetingDate').value=part('year')+'-'+part('month')+'-'+part('day');
  function changed(){panel.dispatchEvent(new Event('input',{bubbles:true}));}
  function cancel(){generation++;lookup?.abort();lookup=null;}
  function clear(message){cancel();inventory=null;selected=null;$('individualMeeting').replaceChildren(new Option('Select a meeting after searching',''));$('selectedMeetingInfo').replaceChildren();$('meetingListStatus').textContent=message;changed();refresh();}
  function refresh(){
    const single=$('meetingSelectionMode').value==='single';$('singleMeetingControls').hidden=!single;
    $('findMeetings').disabled=!!lookup;$('cancelMeetingLookup').disabled=!lookup;
    $('individualMeeting').disabled=!inventory||!!lookup;
    if(single){$('startDate').disabled=true;$('endDate').disabled=true;$('meetingScope').disabled=true;$('recentDates').disabled=true;$('debateDates').disabled=true;}
    else{for(const id of ['startDate','endDate','meetingScope','recentDates','debateDates'])$(id).disabled=false;}
  }
  function apply(){
    if(!selected)return;
    $('startDate').value=inventory.date;$('endDate').value=inventory.date;$('meetingScope').value='all';$('corpusSource').value='live';$('region').value='All regions';
    $('corpusSource').dispatchEvent(new Event('change',{bubbles:true}));
    $('dateRangeNote').textContent='Individual meeting selected for '+inventory.date+'. Only this meeting will be collected.';
    $('selectedMeetingInfo').replaceChildren();const link=document.createElement('a');link.href=selected.pageUrl;link.textContent=selected.title;link.target='_blank';link.rel='noopener noreferrer';$('selectedMeetingInfo').append('Selected: ',link);
    changed();refresh();
  }
  $('meetingSelectionMode').addEventListener('change',()=>{
    clear('Choose a date to list the meetings in the UN transcript inventory.');
    if($('meetingSelectionMode').value==='single'){$('corpusSource').value='live';$('corpusSource').dispatchEvent(new Event('change',{bubbles:true}));}
    refresh();
  });
  $('singleMeetingDate').addEventListener('input',()=>clear('Date changed. Search again before selecting a meeting.'));
  $('individualMeeting').addEventListener('change',()=>{selected=inventory?.meetings.find(m=>m.slug===$('individualMeeting').value)||null;apply();if(!selected){$('selectedMeetingInfo').replaceChildren();changed();}});
  $('cancelMeetingLookup').addEventListener('click',()=>clear('Meeting search cancelled. No incomplete list was released.'));
  $('findMeetings').addEventListener('click',async()=>{
    clear('Finding meetings…');const date=$('singleMeetingDate').value,token=++generation;lookup=new AbortController();refresh();
    try{
      const result=await C.list(date,{signal:lookup.signal,progress:message=>{$('meetingListStatus').textContent=message;}});
      if(token!==generation)return;inventory=result;
      $('individualMeeting').replaceChildren(new Option('Choose one meeting',''));
      for(const m of result.meetings){const option=new Option(m.title+(m.hasTranscript?'':' — transcript not yet listed'),m.slug);option.disabled=!m.hasTranscript;$('individualMeeting').append(option);}
      $('meetingListStatus').textContent=result.total?result.total+' meetings found for '+date+'. Choose one; transcript availability will be rechecked.':'No meetings are listed for '+date+'. Publication may lag proceedings; this is not proof that no meeting occurred.';
    }catch(error){if(token===generation){inventory=null;selected=null;$('meetingListStatus').textContent=error.name==='AbortError'?'Search cancelled.':'Could not list meetings: '+error.message;}}
    finally{if(token===generation){lookup=null;refresh();}}
  });
  $('corpusSource').addEventListener('change',()=>{if($('corpusSource').value!=='live'&&$('meetingSelectionMode').value==='single'){$('meetingSelectionMode').value='range';clear('Choose live collection to select an individual meeting.');}});
  rootInstall();
  function rootInstall(){window.UNMeetingPicker={refresh,selection:()=>{
    if($('meetingSelectionMode').value!=='single')return {};
    if(lookup||!inventory||!selected||inventory.date!==$('singleMeetingDate').value)throw Error('Find and select an individual meeting before running the report.');
    if($('corpusSource').value!=='live')throw Error('Individual meeting selection requires live collection.');
    return C.selection(inventory.date,selected);
  }};refresh();}
})();
