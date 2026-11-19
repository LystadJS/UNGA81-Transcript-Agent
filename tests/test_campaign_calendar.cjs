/* Independent campaign calendar checks use fictional contacts and manual dates. */
'use strict';
const assert=require('node:assert/strict'),{spawnSync}=require('node:child_process'),C=require('../site/campaign-notebook-core.js'),Calendar=require('../site/meeting-report-calendar.js'),registry=require('../site/countries.json');
const entry=(country,date)=>({country,contact:'PRIVATE LEAD',role:'PRIVATE ROLE',email:'private@example.invalid',status:'unrecorded',status_date:'',follow_up_date:date,reference:'Fictional source reference',notes:'Country notes 😀\r\nBEGIN:VEVENT\nATTENDEE:never@example.invalid',contacts:[{id:'p',name:'PRIVATE PROFILE',role:'',email:'',notes:'PRIVATE PROFILE NOTES'}],interactions:[{id:'i',date:'2026-11-19',kind:'meeting',contact:'PRIVATE CONVERSATION CONTACT',email:'',summary:'PRIVATE CONVERSATION',reference:''}]});
(async()=>{
 const n=C.empty();n.campaign.title='Fictional title, semi; slash \\ '+('é😀'.repeat(35));n.campaign.notes='PRIVATE CAMPAIGN NOTES';n.entries=[entry('Kenya','2028-02-29'),entry('United States','2026-10-05'),entry('France','')];const original=JSON.stringify(n),generatedAt='2026-11-19T03:30:00.123Z',options={generatedAt};
 const plain=await Calendar.buildCampaign(n,registry,options),notes=await Calendar.buildCampaign(n,registry,{...options,includeCountryNotes:true}),cutoff=await Calendar.buildCampaign(n,registry,{...options,through:'2026-10-05'});assert.deepEqual(await Calendar.buildCampaign(n,registry,options),plain);assert.notDeepEqual(plain,notes);
 const check=spawnSync('python3',['-c',String.raw`
import base64,json,re,sys,datetime
v=json.load(sys.stdin)
def parse(value):
 raw=base64.b64decode(value);assert raw.endswith(b'\r\n');assert b'\n' not in raw.replace(b'\r\n',b'');physical=raw[:-2].split(b'\r\n');assert all(len(line)<=75 for line in physical)
 for line in physical:line.decode('utf-8')
 lines=re.sub(rb'\r\n[ \t]',b'',raw).decode('utf-8').split('\r\n')[:-1];assert lines.count('BEGIN:VCALENDAR')==lines.count('END:VCALENDAR')==1;assert not any(x.startswith(('ATTENDEE:','ORGANIZER:','METHOD:','BEGIN:VALARM')) for x in lines)
 events=[];event=None
 for line in lines:
  if line=='BEGIN:VEVENT':event={}
  elif line=='END:VEVENT':events.append(event);event=None
  elif event is not None:
   key,value=line.split(':',1);assert key not in event;event[key]=value
 return events
def unescape(value):
 result='';i=0
 while i<len(value):
  if value[i]=='\\':i+=1;result+='\n' if value[i] in 'nN' else value[i]
  else:result+=value[i]
  i+=1
 return result
p=parse(v['plain']);n=parse(v['notes']);c=parse(v['cutoff']);assert len(p)==len(n)==2 and len(c)==1;assert p[0]['DTSTART;VALUE=DATE']=='20261005';assert p[0]['DTEND;VALUE=DATE']=='20261006';assert p[1]['DTSTART;VALUE=DATE']=='20280229';assert p[1]['DTEND;VALUE=DATE']=='20280301';assert [x['UID'] for x in p]==[x['UID'] for x in n];assert c[0]['UID']==p[0]['UID'];assert len(set(x['UID'] for x in p))==2
for e in p:
 assert e['CLASS']=='PRIVATE' and e['TRANSP']=='TRANSPARENT';assert re.fullmatch(r'[a-f0-9]{64}@un-transcript-agent.invalid',e['UID']);datetime.datetime.strptime(e['DTSTAMP'],'%Y%m%dT%H%M%SZ');assert v['title'] in unescape(e['SUMMARY']);assert 'manual follow-up' in unescape(e['DESCRIPTION']);assert 'PRIVATE' not in unescape(e['DESCRIPTION']);assert 'Country notes' not in unescape(e['DESCRIPTION'])
for e in n:assert v['countryNotes'].replace('\r\n','\n') in unescape(e['DESCRIPTION']);assert 'PRIVATE CAMPAIGN' not in unescape(e['DESCRIPTION']);assert 'PRIVATE LEAD' not in unescape(e['DESCRIPTION']);assert 'PRIVATE PROFILE' not in unescape(e['DESCRIPTION']);assert 'PRIVATE CONVERSATION' not in unescape(e['DESCRIPTION'])
print('PASS: independent multi-event ICS unfolding/UTF-8 75-octet lines, escaped text, privacy scope, explicit cutoff, leap dates, stable prepared IDs and no invitations/alarms')
`],{input:JSON.stringify({plain:Buffer.from(plain).toString('base64'),notes:Buffer.from(notes).toString('base64'),cutoff:Buffer.from(cutoff).toString('base64'),title:n.campaign.title,countryNotes:n.entries[0].notes}),encoding:'utf8'});assert.equal(check.status,0,check.stderr);process.stdout.write(check.stdout);
 for(const bad of [{through:'2026-02-30'},{through:0},{includeCountryNotes:'yes'},{generatedAt:'bad'},{generatedAt:'0000-01-01T00:00:00.000Z'}])await assert.rejects(Calendar.buildCampaign(n,registry,{...options,...bad}),/valid follow-up cutoff/);await assert.rejects(Calendar.buildCampaign(n,registry,{...options,through:'1900-01-01'}),/No dated/);await assert.rejects(Calendar.buildCampaign(C.empty(),registry,options),/No dated/);
 const last=C.empty();last.entries=[entry('Kenya','9998-12-31')];assert(new TextDecoder().decode(await Calendar.buildCampaign(last,registry,options)).includes('DTEND;VALUE=DATE:99990101'));
 const unsupported=structuredClone(n);unsupported.entries[0].notes='Unsupported note \uffff';assert(await Calendar.buildCampaign(unsupported,registry,options));await assert.rejects(Calendar.buildCampaign(unsupported,registry,{...options,includeCountryNotes:true}),/unsupported text/);
 const limit=C.LIMIT;try{C.LIMIT=plain.length;assert.equal((await Calendar.buildCampaign(n,registry,options)).length,plain.length);C.LIMIT=plain.length-1;await assert.rejects(Calendar.buildCampaign(n,registry,options),/1 MiB/);}finally{C.LIMIT=limit;}
 const changed=await Calendar.buildCampaign(n,registry,{...options,generatedAt:'2026-11-19T03:31:00.123Z'});assert.notDeepEqual(changed,plain);assert.equal(JSON.stringify(n),original);console.log('PASS: strict options, no invented dates, end-of-year range, exact byte bound without truncation and immutable notebook');
})().catch(e=>{console.error(e);process.exitCode=1;});
