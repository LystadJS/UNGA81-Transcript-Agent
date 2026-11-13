'use strict';
const assert=require('node:assert/strict'),R=require('../site/meeting-report-core.js'),F=require('./meeting_report_fixture.cjs');
(async()=>{
 const a=await F.corpus(),b=await F.corpus(1),rows=[...a.records,...b.records],original=JSON.stringify(rows),id=a.records[2].id;
 const window=R.contextWindow(rows,id);
 assert.equal(window.previous,a.records[1]);assert.equal(window.focus,a.records[2]);assert.equal(window.next,a.records[3]);assert.equal(window.at_start,false);
 const first=R.contextWindow(rows,a.records[0].id);assert.equal(first.previous,null);assert.equal(first.at_start,true);assert.equal(first.next,a.records[1]);
 const last=R.contextWindow(rows,a.records[3].id);assert.equal(last.next,null);assert.match(R.contextHTML(last),/does not establish source completeness/);
 const gap=R.contextWindow([a.records[0],a.records[2]],id);assert.equal(gap.previous,null);assert.equal(gap.next,null);assert.match(R.contextHTML(gap),/immediately preceding segment is not loaded/);
 for(const key of ['meeting_slug','date','language','source_id','source_version','raw_sha256']){
  const foreign={...a.records[1],[key]:'different-revision-or-meeting'};
  assert.equal(R.contextWindow([a.records[2],foreign],id).previous,null,key);
 }
 assert.throws(()=>R.contextWindow(rows,'unknown#0'));
 assert.throws(()=>R.contextWindow([...rows,a.records[2]],id));
 assert.throws(()=>R.contextWindow([{...a.records[2],raw_sha256:''}],id));
 for(const json_pointer of ['/transcript/data/02','/transcript/data/-1','/transcript/data/9007199254740992','/not-a-segment/2'])assert.throws(()=>R.contextWindow([{...a.records[2],json_pointer}],id));
 assert.throws(()=>R.contextWindow([a.records[2],{...a.records[1],id:'renamed'}],id));
 const html=R.contextHTML(window);assert(html.includes('United States delegate'));assert(html.includes('Example Group'));assert(html.includes('Collective capacity indicated'));assert(html.includes('Speaking capacity is not verified'));assert(html.includes(a.records[1].raw_sha256));assert(html.includes(a.records[3].json_pointer));assert(!html.includes('<img'));assert(html.includes('&lt;img'));
 const missing=R.speakerHTML({text:'An ordinary statement.',speaker_metadata:{}});assert(missing.includes('Not supplied'));assert(missing.includes('not verified'));assert(!missing.includes('Collective capacity indicated'));
 const hostile=R.speakerHTML({text:'',speaker_metadata:{name:'<img onerror=bad>',function:'<script>bad</script>',group:'<svg>'}});assert(!hostile.includes('<img'));assert(!hostile.includes('<script>'));assert(hostile.includes('&lt;svg&gt;'));
 const report=R.build([a],[a.coverage[0].slug]),preview=R.reportHTML(report,{preview:true});
 assert(preview.includes('data-evidence-id='));assert(!R.standalone(report).includes('data-evidence-id='));
 const positions=report.meetings[0].summary.positions,extract=positions[0].evidence[0],good=JSON.stringify(extract);
 for(const key of ['record_id','text_sha256','json_pointer','source_url']){extract[key]='unknown';const changed=R.reportHTML(report,{preview:true});assert((changed.match(/data-evidence-id=/g)||[]).length<(preview.match(/data-evidence-id=/g)||[]).length,key);Object.assign(extract,JSON.parse(good));}
 assert.equal(JSON.stringify(rows),original);
 console.log('PASS: immediate source-index neighbors, meeting/date/language/revision isolation, missing context, strict identities, separate speaker/capacity metadata, escaped output and immutable inputs');
})().catch(e=>{console.error(e);process.exitCode=1;});
