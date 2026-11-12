/* Public identifiers only. Selection never authorizes a remote URL or source download. */
(function(root){
  'use strict';
  const SCHEMA='un.meeting-selection.v1',MAX=5;
  const dateOK=d=>typeof d==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(d)&&Number.isFinite(Date.parse(d))&&new Date(d).toISOString().slice(0,10)===d;
  const slugOK=s=>typeof s==='string'&&s.length<=160&&/^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+){1,5}$/.test(s);
  function policy(value){if(value?.schema!=='un.reporting-exclusions.v1'||!Array.isArray(value.dates)||!Array.isArray(value.meetings)||value.meetings.length!==37||new Set(value.meetings).size!==37||value.dates.some(d=>!dateOK(d))||value.meetings.some(m=>!slugOK(m)))throw Error('Reporting exclusions unavailable.');return value;}
  function eligible(m,p){policy(p);return !!m&&dateOK(m.date)&&slugOK(m.meeting_id)&&!p.dates.includes(m.date)&&!p.meetings.includes(m.meeting_id);}
  function validate(value,p){
    policy(p);
    if(!value||value.schema!==SCHEMA||Object.keys(value).some(k=>!['schema','snapshot_id','meetings'].includes(k))||!Array.isArray(value.meetings)||!value.meetings.length||value.meetings.length>MAX)throw Error('Select between one and five eligible meetings.');
    if(value.snapshot_id!==undefined&&(typeof value.snapshot_id!=='string'||!/^[A-Za-z0-9_.:-]{1,160}$/.test(value.snapshot_id)))throw Error('Invalid archive snapshot identifier.');
    const seen=new Set();
    for(const m of value.meetings){if(!eligible(m,p)||Object.keys(m).some(k=>!['date','meeting_id'].includes(k))||seen.has(m.meeting_id))throw Error('Invalid, duplicated or reserved meeting selection.');seen.add(m.meeting_id);}
    return {schema:SCHEMA,...(value.snapshot_id===undefined?{}:{snapshot_id:value.snapshot_id}),meetings:value.meetings.map(m=>({date:m.date,meeting_id:m.meeting_id}))};
  }
  function read(search,p){const params=new URLSearchParams(search),values=params.getAll('selection');if(!values.length)return null;if(values.length!==1||values[0].length>2500)throw Error('Invalid meeting-selection link.');return validate(JSON.parse(values[0]),p);}
  function link(value,p){return 'meeting-reports.html?selection='+encodeURIComponent(JSON.stringify(validate(value,p)));}
  const api={SCHEMA,MAX,policy,eligible,validate,read,link};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNMeetingReportSelection=api;
})(globalThis);
