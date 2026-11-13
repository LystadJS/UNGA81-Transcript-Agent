/* Local, dependency-free report ZIP. No uploads, compression or source requests. */
(function(root){
  'use strict';
  const node=typeof module!=='undefined'&&module.exports;
  const Core=node?require('./meeting-report-core.js'):root.UNMeetingReport;
  const crypto=node?require('node:crypto').webcrypto:root.crypto,encoder=new TextEncoder();
  const table=Uint32Array.from({length:256},(_,n)=>{for(let i=0;i<8;i++)n=n&1?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
  const crc=bytes=>{let n=0xffffffff;for(const b of bytes)n=table[(n^b)&255]^(n>>>8);return (n^0xffffffff)>>>0;};
  const guide=`UN Transcript Agent — report package

Open report.html to read or print the report. Extract report.json and open it in
the reporting workspace to continue editing; original sources are revalidated.
evidence.csv contains every source segment from the selected meetings, regardless
of search or appendix selection. Analyst notes appear only in HTML and JSON.
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
  function zip(files){
    // Fixed internal ASCII filenames; callers cannot supply ZIP paths.
    const size=22+files.reduce((n,f)=>n+76+2*f.name.length+f.bytes.length,0);
    if(size>Core.LIMIT)throw Error('Report package exceeds 25 MB. Choose fewer meetings or use individual downloads. Current work has not changed.');
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
  const api={build};if(node)module.exports=api;else root.UNMeetingReportPackage=api;
})(globalThis);
