/* Local, dependency-free report ZIP. No uploads, compression or source requests. */
(function(root){
  'use strict';
  const node=typeof module!=='undefined'&&module.exports;
  const Core=node?require('./meeting-report-core.js'):root.UNMeetingReport;
  const crypto=node?require('node:crypto').webcrypto:root.crypto,encoder=new TextEncoder();
  const table=Uint32Array.from({length:256},(_,n)=>{for(let i=0;i<8;i++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
  const crc=bytes=>{let n=0xffffffff;for(const b of bytes)n=table[(n^b)&255]^(n>>>8);return (n^0xffffffff)>>>0;};
  const guide=`UN Transcript Agent — report package

Open report.html to read or print the report. Open this ZIP directly in the
reporting workspace to continue editing, or extract report.json and open it
separately. Package checksums and original sources are revalidated; imported HTML
is never executed.

evidence.csv contains every source segment from the selected meetings, regardless
of search or appendix selection. Analyst notes appear only in HTML and JSON.
Briefing questions include literal source matches or explicit unanswered gaps;
they are not generated answers. Questions are saved in report.json and reusable
mission preferences. They do not change country comparisons or the evidence CSV.
JSON preserves all loaded source bundles, including meetings not selected for
this report. This package can contain source text and sensitive analyst notes.
Review its contents before sharing. It is not encrypted. Nothing is uploaded.

CSV dictionary (UTF-8, quoted cells, CRLF; one row per selected source segment):
id: meeting slug plus original zero-based segment index; unique segment key.
meeting_slug: stable source meeting identity; date: dated source, YYYY-MM-DD.
country: recorded affiliation or registry mapping; not verified national capacity.
text: source text; source_url: original passage or meeting locator.
source_id: original response locator; source_version: response SHA-256.
raw_sha256: original response hash; text_sha256: normalized segment text hash.
json_pointer: segment path within the original response JSON.
Cells starting with a potential spreadsheet formula receive an apostrophe.
Use report.json when exact original string values are required.

manifest.json records the preparation time, method, selected meeting IDs,
source revisions, file byte counts and SHA-256 checksums of the four other files.
Checksums detect changed bytes; they do not authenticate the source or speaker.
There is no self-checksum for the manifest. The ZIP uses uncompressed entries
with a fixed 1980 container timestamp; use manifest.generated_at for report time.

Automatic five-class stance estimates remain withheld. Country expressions are
provisional rule extracts. Missing evidence is not neutrality; collective capacity
does not establish a national position. Repetition does not add policy weight.
Research CSV releases, private owner annotations and model acceptance are separate.
`;
  function zip(files,label='Report package',{limit=Core?.LIMIT??25000000,notebook=false}={}){
    if(!Number.isSafeInteger(limit)||limit<1||limit>25000000)throw Error('Invalid archive byte limit.');
    // Shared bounded ZIP writer for report packages and native Office documents.
    const names=new Set();
    if(!Array.isArray(files)||!files.length||files.length>65535)throw Error('Invalid archive file count.');
    for(const f of files){
      if(typeof f.name!=='string'||!/^[A-Za-z0-9_.[\]\/-]+$/.test(f.name)||f.name.length>240||f.name.startsWith('/')||f.name.split('/').some(p=>!p||p==='.'||p==='..')||names.has(f.name.toLowerCase())||!(f.bytes instanceof Uint8Array))throw Error('Invalid archive entry.');
      names.add(f.name.toLowerCase());
    }
    const size=22+files.reduce((n,f)=>n+76+2*f.name.length+f.bytes.length,0);
    if(size>limit)throw Error(!notebook?label+' exceeds 25 MB. Choose fewer meetings or use individual downloads. Current work has not changed.':label+' exceeds 1 MiB; nothing was truncated. Keep notebook JSON separately.');
    const out=new Uint8Array(size),view=new DataView(out.buffer);let at=0;
    const u16=n=>{view.setUint16(at,n,true);at+=2;},u32=n=>{view.setUint32(at,n,true);at+=4;};
    const raw=bytes=>{out.set(bytes,at);at+=bytes.length;};
    for(const f of files){
      f.offset=at;f.crc=crc(f.bytes);f.nameBytes=encoder.encode(f.name);
      u32(0x04034b50);u16(20);u16(0x800);u16(0);u16(0);u16(33);u32(f.crc);u32(f.bytes.length);u32(f.bytes.length);u16(f.nameBytes.length);u16(0);raw(f.nameBytes);raw(f.bytes);
    }
    const start=at;
    for(const f of files){
      u32(0x02014b50);u16(20);u16(20);u16(0x800);u16(0);u16(0);u16(33);u32(f.crc);u32(f.bytes.length);u32(f.bytes.length);u16(f.nameBytes.length);u16(0);u16(0);u16(0);u16(0);u32(0);u32(f.offset);raw(f.nameBytes);
    }
    const length=at-start;u32(0x06054b50);u16(0);u16(0);u16(files.length);u16(files.length);u32(length);u32(start);u16(0);
    return out;
  }
  async function build(report,corpora){
    const files=[['report.html',Core.standalone(report)],['report.json',JSON.stringify(Core.savedReport(report,corpora))],['evidence.csv',Core.evidenceCSV(report.records)],['README.txt',guide]].map(([name,text])=>({name,bytes:encoder.encode(text)}));
    if(files.reduce((n,f)=>n+f.bytes.length,0)>Core.LIMIT)throw Error('Report package exceeds 25 MB. Choose fewer meetings or use individual downloads. Current work has not changed.');
    const manifest={schema:'un.meeting-report-package.v1',generated_at:report.generated_at,engine:report.engine,method:report.method,report_schema:report.schema,model_status:report.model_status,selected_meetings:report.selected_meetings,selected_segment_count:report.records.length,saved_source_scope:'all_loaded_bundles',source_revisions:[],files:[]};
    const seen=new Set();
    for(const source of corpora.flatMap(c=>c.provenance.sources)){
      const key=source.source_id+'|'+source.sha256;if(seen.has(key))continue;seen.add(key);
      manifest.source_revisions.push({source_id:source.source_id,sha256:source.sha256});
    }
    for(const f of files){
      const hash=await crypto.subtle.digest('SHA-256',f.bytes);
      manifest.files.push({path:f.name,bytes:f.bytes.length,sha256:[...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join('')});
    }
    files.push({name:'manifest.json',bytes:encoder.encode(JSON.stringify(manifest,null,2)+'\n')});
    return zip(files);
  }
  async function read(bytes){
    const fail=()=>{throw Error('Invalid report package. Use an original uncompressed report-package ZIP or its report.json.');};
    if(!(bytes instanceof Uint8Array)||bytes.length<22)fail();
    if(bytes.length>Core.LIMIT)throw Error('Use a report package under 25 MB.');
    const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),end=bytes.length-22;
    const u16=at=>{if(at<0||at+2>bytes.length)fail();return view.getUint16(at,true);};
    const u32=at=>{if(at<0||at+4>bytes.length)fail();return view.getUint32(at,true);};
    if(u32(end)!==0x06054b50||u16(end+4)||u16(end+6)||u16(end+8)!==5||u16(end+10)!==5||u16(end+20))fail();
    const start=u32(end+16),size=u32(end+12);if(start+size!==end)fail();
    const names=['report.html','report.json','evidence.csv','README.txt','manifest.json'],files=new Map();
    let at=start,offset=0;
    for(const name of names){
      if(at+46>end||u32(at)!==0x02014b50||u16(at+4)!==20||u16(at+6)!==20||u16(at+8)!==0x800||u16(at+10)!==0||u16(at+30)||u16(at+32)||u16(at+34)||u16(at+36)||u32(at+38))fail();
      const length=u32(at+24),nameLength=u16(at+28),local=u32(at+42);
      if(u32(at+20)!==length||nameLength!==name.length||at+46+nameLength>end||local!==offset||local+30+nameLength+length>start)fail();
      const nameBytes=encoder.encode(name);
      if(!nameBytes.every((b,i)=>bytes[at+46+i]===b)||u32(local)!==0x04034b50||u16(local+4)!==20||u16(local+6)!==0x800||u16(local+8)!==0||u16(local+26)!==nameLength||u16(local+28))fail();
      // Local and central headers must describe the same contiguous payload.
      for(const [l,c] of [[10,12],[12,14],[14,16],[18,20],[22,24]]){
        if((l<14?u16(local+l)!==u16(at+c):u32(local+l)!==u32(at+c)))fail();
      }
      if(!nameBytes.every((b,i)=>bytes[local+30+i]===b))fail();
      const payload=bytes.subarray(local+30+nameLength,local+30+nameLength+length);
      if(crc(payload)!==u32(at+16))throw Error('Report package CRC mismatch. Current work kept.');
      files.set(name,payload);offset=local+30+nameLength+length;at+=46+nameLength;
    }
    if(offset!==start||at!==end)fail();
    const decode=name=>new TextDecoder('utf-8',{fatal:true}).decode(files.get(name));
    let manifest,saved;try{manifest=JSON.parse(decode('manifest.json'));saved=JSON.parse(decode('report.json'));}catch{fail();}
    if(manifest?.schema!=='un.meeting-report-package.v1'||!Array.isArray(manifest.files)||manifest.files.length!==4)fail();
    for(let i=0;i<4;i++){
      const item=manifest.files[i],payload=files.get(names[i]);
      if(!item||Object.keys(item).length!==3||item.path!==names[i]||item.bytes!==payload.length||typeof item.sha256!=='string'||!/^[a-f0-9]{64}$/.test(item.sha256))fail();
      const digest=await crypto.subtle.digest('SHA-256',payload),actual=[...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join('');
      if(actual!==item.sha256)throw Error('Report package SHA-256 mismatch. Current work kept.');
    }
    if(!saved||!Array.isArray(saved.corpora)||!Array.isArray(saved.selected_meetings)||manifest.report_schema!==saved.schema||manifest.engine!==saved.engine||manifest.generated_at!==saved.generated_at||manifest.saved_source_scope!=='all_loaded_bundles'||manifest.model_status!=='withheld_not_accepted'||typeof manifest.method!=='string'||!manifest.method||manifest.method.length>1000||JSON.stringify(manifest.selected_meetings)!==JSON.stringify(saved.selected_meetings))fail();
    const selected=new Set(saved.selected_meetings),revisions=[],seen=new Set();let count=0;
    for(const corpus of saved.corpora){
      if(!Array.isArray(corpus?.records)||!Array.isArray(corpus?.provenance?.sources))fail();
      count+=corpus.records.filter(r=>selected.has(r?.meeting_slug)).length;
      for(const source of corpus.provenance.sources){
        if(!source||typeof source.source_id!=='string'||typeof source.sha256!=='string')fail();
        const key=source.source_id+'|'+source.sha256;if(seen.has(key))continue;seen.add(key);revisions.push({source_id:source.source_id,sha256:source.sha256});
      }
    }
    if(manifest.selected_segment_count!==count||JSON.stringify(manifest.source_revisions)!==JSON.stringify(revisions))fail();
    // Checksums establish byte consistency only. The caller must revalidate sources
    // with Core.openSaved/appendSaved and rebuild every displayed derived claim.
    return saved;
  }
  const api={BOUNDED_ZIP_VERSION:1,build,zip,read};if(node)module.exports=api;else root.UNMeetingReportPackage=api;
})(globalThis);
