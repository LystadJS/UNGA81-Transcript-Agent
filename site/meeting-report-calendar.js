/* Personal all-day review entries; no calendar connection or source requests. */
(function(root){
 'use strict';
 const node=typeof module!=='undefined'&&module.exports,Core=node?require('./meeting-report-core.js'):root.UNMeetingReport,crypto=node?require('node:crypto').webcrypto:root.crypto,encoder=new TextEncoder();
 function validDate(value){
  if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value)||+value.slice(0,4)<1900||+value.slice(0,4)>9998)return false;
  const d=new Date(value+'T00:00:00Z');return Number.isFinite(+d)&&d.toISOString().slice(0,10)===value;
 }
 function text(value){
  if(typeof value!=='string')throw Error('Invalid calendar text.');
  for(const char of value){const n=char.codePointAt(0);if((n<32&&![9,10,13].includes(n))||(n>=0xd800&&n<=0xdfff)||n===0xfffe||n===0xffff)throw Error('Calendar cannot preserve an unsupported text character. Use JSON for exact saved work.');}
  return value.replace(/\\/g,'\\\\').replace(/\r\n|\r|\n/g,'\\n').replace(/;/g,'\\;').replace(/,/g,'\\,');
 }
 function fold(line){
  const parts=[];let part='',bytes=0,first=true;
  for(const char of line){const size=encoder.encode(char).length;if(bytes+size>(first?75:74)){parts.push((first?'':' ')+part);first=false;part='';bytes=0;}part+=char;bytes+=size;}
  parts.push((first?'':' ')+part);return parts.join('\r\n');
 }
 async function build(report,date,{includeAssessment=false}={}){
  if(!validDate(date))throw Error('Choose a valid personal review date from 1900 through 9998.');
  if(typeof includeAssessment!=='boolean'||!report||typeof report.settings?.title!=='string'||!Array.isArray(report.meetings)||!report.meetings.length||!Array.isArray(report.selected_meetings)||typeof report.generated_at!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(report.generated_at)||new Date(report.generated_at).toISOString()!==report.generated_at)throw Error('Prepare a valid report before creating its review entry.');
  const end=new Date(date+'T00:00:00Z');end.setUTCDate(end.getUTCDate()+1);
  const description=['Personal all-day report review.','Prepared report: '+report.settings.title,'Prepared UTC: '+report.generated_at,'Selected source meetings:'];
  for(const m of report.meetings){if(typeof m.date!=='string'||typeof m.title!=='string'||typeof m.slug!=='string')throw Error('Invalid source meeting metadata.');description.push(m.date+' · '+m.title+' ('+m.slug+')');if(m.source_url)description.push(m.source_url);}
  if(includeAssessment){if(typeof report.settings.notes!=='string')throw Error('Invalid assessment text.');description.push('User assessment:',report.settings.notes||'No assessment supplied.');}
  description.push('Keep report JSON or ZIP separately to resume editing. Calendar alerts and imports are controlled by your calendar application.');
  const summary=text('Review: '+report.settings.title),details=text(description.join('\n'));
  const identity=encoder.encode(JSON.stringify([report.generated_at,report.selected_meetings,date,report.settings.title]));
  if(identity.length+encoder.encode(summary).length+encoder.encode(details).length>Core.LIMIT)throw Error('Calendar entry exceeds 25 MB. Current work kept.');
  const digest=await crypto.subtle.digest('SHA-256',identity),uid=[...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join('')+'@un-transcript-agent.invalid';
  const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//UN Transcript Agent//Personal report review//EN','CALSCALE:GREGORIAN','BEGIN:VEVENT','UID:'+uid,'DTSTAMP:'+report.generated_at.slice(0,19).replace(/[-:]/g,'')+'Z','DTSTART;VALUE=DATE:'+date.replace(/-/g,''),'DTEND;VALUE=DATE:'+end.toISOString().slice(0,10).replace(/-/g,''),'SUMMARY:'+summary,'DESCRIPTION:'+details,'CLASS:PRIVATE','TRANSP:TRANSPARENT','END:VEVENT','END:VCALENDAR'];
  const bytes=encoder.encode(lines.map(fold).join('\r\n')+'\r\n');if(bytes.length>Core.LIMIT)throw Error('Calendar entry exceeds 25 MB. Current work kept.');return bytes;
 }
 const api={build,validDate};if(node)module.exports=api;else root.UNMeetingReportCalendar=api;
})(globalThis);
