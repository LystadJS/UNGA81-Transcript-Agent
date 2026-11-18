/* Calendar reading copies preserve RFC text/byte boundaries without changing reports. */
'use strict';
const assert=require('node:assert/strict'),{spawnSync}=require('node:child_process'),R=require('../site/meeting-report-core.js'),Calendar=require('../site/meeting-report-calendar.js'),F=require('./meeting_report_fixture.cjs');
(async()=>{
 const corpus=await F.corpus(),report=R.build([corpus],[F.meetings[0].slug],{title:'Review title, semicolon; slash \\ emoji 😀 '+('é😀'.repeat(45)),notes:'Private assessment\r\nBEGIN:VEVENT\nATTENDEE:never@example.invalid'}),original=JSON.stringify(report);
 const bytes=await Calendar.build(report,'2028-02-29'),withNotes=await Calendar.build(report,'2028-02-29',{includeAssessment:true});assert.deepEqual(await Calendar.build(report,'2028-02-29'),bytes);assert.notDeepEqual(withNotes,bytes);assert(!new TextDecoder().decode(bytes).includes('Private assessment'));
 const check=spawnSync('python3',['-c',`
import base64,json,re,sys,datetime
v=json.load(sys.stdin)
def parse(encoded):
 raw=base64.b64decode(encoded);assert raw.endswith(b'\\r\\n');assert b'\\n' not in raw.replace(b'\\r\\n',b'');physical=raw[:-2].split(b'\\r\\n');assert all(len(line)<=75 for line in physical)
 for line in physical:line.decode('utf-8')
 logical=re.sub(rb'\\r\\n[ \\t]',b'',raw).decode('utf-8').split('\\r\\n')[:-1];assert logical.count('BEGIN:VCALENDAR')==logical.count('END:VCALENDAR')==logical.count('BEGIN:VEVENT')==logical.count('END:VEVENT')==1
 assert not any(line.startswith(('ATTENDEE:','ORGANIZER:','METHOD:','BEGIN:VALARM')) for line in logical)
 return dict(line.split(':',1) for line in logical if ':' in line)
def unescape(s):
 out='';i=0
 while i<len(s):
  if s[i]=='\\\\':i+=1;out+='\\n' if s[i] in 'nN' else s[i]
  else:out+=s[i]
  i+=1
 return out
p=parse(v['plain']);n=parse(v['notes']);assert p['DTSTART;VALUE=DATE']=='20280229' and p['DTEND;VALUE=DATE']=='20280301';assert p['CLASS']=='PRIVATE' and p['TRANSP']=='TRANSPARENT';assert re.fullmatch(r'[a-f0-9]{64}@un-transcript-agent.invalid',p['UID']);datetime.datetime.strptime(p['DTSTAMP'],'%Y%m%dT%H%M%SZ');assert unescape(p['SUMMARY'])=='Review: '+v['title'];assert v['notesText'].replace('\\r\\n','\\n') in unescape(n['DESCRIPTION']);assert p['UID']==n['UID'];assert 'Private assessment' not in unescape(p['DESCRIPTION']);assert v['source'] in unescape(p['DESCRIPTION']);print('PASS: independent CRLF/UTF-8 75-octet unfolding, all-day leap boundary, exact escaped Unicode/text, injection refusal, private/no-invitation semantics and optional assessment')
`],{input:JSON.stringify({plain:Buffer.from(bytes).toString('base64'),notes:Buffer.from(withNotes).toString('base64'),title:report.settings.title,notesText:report.settings.notes,source:report.meetings[0].source_url}),encoding:'utf8'});assert.equal(check.status,0,check.stderr);process.stdout.write(check.stdout);
 for(const date of ['','2026-02-29','2026-13-01','2026-11-31','2026-1-01','1899-12-31','9999-01-01','2026-11-18T00:00:00Z']){assert.equal(Calendar.validDate(date),false);await assert.rejects(Calendar.build(report,date),/valid personal review date/);}
 assert(Calendar.validDate('2026-10-05'));const year=await Calendar.build(report,'2026-12-31');assert(new TextDecoder().decode(year).includes('DTEND;VALUE=DATE:20270101'));
 await assert.rejects(Calendar.build({...report,settings:{...report.settings,title:'bad\u0001text'}},'2026-12-31'),/unsupported/);await assert.rejects(Calendar.build({...report,settings:{...report.settings,title:'bad\ud800'}},'2026-12-31'),/unsupported/);
 const limit=R.LIMIT;try{R.LIMIT=bytes.length;assert.equal((await Calendar.build(report,'2028-02-29')).length,bytes.length);R.LIMIT=bytes.length-1;await assert.rejects(Calendar.build(report,'2028-02-29'),/exceeds 25 MB/);}finally{R.LIMIT=limit;}
 assert.equal(JSON.stringify(report),original);console.log('PASS: deterministic calendar, exact byte bounds, invalid dates/controls/surrogates refused, year rollover and immutable source report');
})().catch(error=>{console.error(error);process.exitCode=1;});
