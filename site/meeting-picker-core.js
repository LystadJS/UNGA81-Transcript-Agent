/* Date -> complete UN inventory -> explicit single-meeting selection. */
(function(root){
  'use strict';
  const node=typeof module!=='undefined'&&module.exports;
  const C=node?require('./collector.js'):root.UNCollector;
  const S=node?require('./meeting-scopes.js'):root.UNMeetingScopes;
  function dateOK(date){return typeof date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(date)&&Number.isFinite(Date.parse(date))&&new Date(date).toISOString().slice(0,10)===date;}
  function validSlug(slug){return typeof slug==='string'&&/^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+){1,5}$/.test(slug);}
  function checkMeeting(m,date){
    if(!m||!validSlug(m.slug)||typeof m.title!=='string'||!m.title.trim()||typeof m.date!=='string'||m.date.slice(0,10)!==date||typeof m.hasTranscript!=='boolean')throw Error('Unexpected meeting identity, title, date or availability.');
    C.sourceURL(m.pageUrl);
    if(m.hasTranscript){if(typeof m.jsonUrl!=='string'||!m.jsonUrl)throw Error('Available meeting lacks a transcript endpoint.');C.sourceURL(m.jsonUrl);}
    return m;
  }
  async function list(date,{signal,request=C.readJSON,progress=()=>{}}={}){
    if(!dateOK(date))throw Error('Choose a valid meeting date.');
    const check=()=>{if(signal?.aborted)throw new DOMException('Cancelled','AbortError');};
    const rows=[],pages=[];let expected=null,complete=false;
    for(let page=1;page<=50;page++){
      check();progress('Finding meetings · '+date+' · page '+page);
      const {data,hash}=await request(`https://transcripts.un.org/en/meetings.json?date=${date}&xlang=1&page=${page}`,signal);check();
      if(!data||!Array.isArray(data.meetings)||data.page!==page||!Number.isSafeInteger(data.total)||data.total<0||data.total>15000||typeof data.hasMore!=='boolean')throw Error('Unexpected UN inventory format.');
      if(expected===null)expected=data.total;
      if(data.total!==expected)throw Error('The inventory changed while listing meetings. Search the date again.');
      for(const meeting of data.meetings)checkMeeting(meeting,date);
      rows.push(...data.meetings);pages.push({date,page,sha256:hash});
      if(rows.length>expected)throw Error('The inventory returned too many meetings.');
      if(!data.hasMore){complete=true;break;}
    }
    if(!complete||rows.length!==expected||new Set(rows.map(m=>m.slug)).size!==expected)throw Error('Meeting inventory is incomplete or contains duplicate identities. Search the date again.');
    return {schema:'un.meeting-list.v1',date,retrieved_at:new Date().toISOString(),total:rows.length,pages,meetings:rows.map(m=>({slug:m.slug,title:m.title,date:m.date,hasTranscript:m.hasTranscript,pageUrl:C.sourceURL(m.pageUrl),jsonUrl:m.hasTranscript?C.sourceURL(m.jsonUrl):null,scope:S.classifyMeeting(m)})),note:'Inventory flags do not guarantee usable English text. The selected transcript is checked during collection.'};
  }
  function selection(date,meeting){
    if(!dateOK(date))throw Error('Choose a valid meeting date.');
    checkMeeting(meeting,date);
    if(!meeting.hasTranscript)throw Error('The UN inventory does not yet list a transcript for this meeting.');
    return {start:date,end:date,scope:'all',meeting_slug:meeting.slug,meeting_date:date};
  }
  const api={dateOK,validSlug,list,selection,checkMeeting};if(node)module.exports=api;else root.UNMeetingPickerCore=api;
})(globalThis);
