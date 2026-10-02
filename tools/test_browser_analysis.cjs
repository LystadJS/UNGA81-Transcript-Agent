const assert=require('node:assert/strict');
const A=require('../site/analysis-core.js'),C=require('../site/collector.js');
(async()=>{
 const p={topic:'AI',phrases:['AI','artificial intelligence'],exclude:[],start:'2026-09-22',end:'2026-09-23',region:'All regions',scope:'all',methods:A.METHODS};
 const row=(id,text,region='Africa',date='2026-09-22')=>({id,text,region,date,country:'Example',language:'en',scope:'general_debate',meeting:'Fixture',source_url:'https://example.org/',text_sha256:'a'.repeat(64)});
 const records=[row('1','AI safeguards health'),row('2','roads water'),row('3','artificial intelligence health','Asia-Pacific','2026-09-23'),row('4','AI   safeguards health'),{...row('5','AI foreign'),language:'fr'},row('6','AI outside','Africa','2026-09-24'),row('7','chair said fair')];
 const corpus={schema:'un.browser.corpus.v1',records,coverage:[]};
 const r=await A.analyze(corpus,p);assert.equal(r.counts.eligible,4);assert.equal(r.counts.matched,2);assert.equal(r.counts.duplicates,1);assert.equal(r.methods.similarity.compared,1);assert.equal(r.methods.frequency.find(x=>x.name==='Africa').matches,1);assert.equal(r.methods.frequency.find(x=>x.name==='Africa').total,3);assert.equal(r.methods.timeline.find(x=>x.name==='2026-09-23').percent,100);assert.equal(r.methods.length[0].total,2);
 const regional=await A.analyze(corpus,{...p,region:'Africa'});assert.equal(regional.counts.matched,1);
 const excluded=await A.analyze(corpus,{...p,exclude:['safeguards']});assert.equal(excluded.counts.matched,1);
 assert.equal((await A.analyze(corpus,{...p,phrases:['not present']})).counts.matched,0);
 assert.equal(A.hasPhrase(A.canonical('chair said fair'),'AI'),false);
 for(const bad of [{...p,start:'2026-02-30'},{...p,end:'2026-09-21'},{...p,end:'2026-11-01'},{...p,methods:['bert']}])assert.throws(()=>A.parameters(bad));
 assert.throws(()=>C.sourceURL('https://attacker.test/data'));
 assert.throws(()=>A.validateCorpus({...corpus,records:[records[0],records[0]]}));
 const t=A.tfidf([row('a','health health'),row('b','health')]);assert.equal(t.terms[0].mean,1);assert.equal(t.vectors[0].get('health'),1);
 const many=Array.from({length:301},(_,i)=>row(String(i),'AI distinct '+i));assert.ok((await A.analyze({...corpus,records:many},p)).methods.similarity.skipped);
 const countries=[{country:'Example',iso3:'EXA',aliases:'Example',region:'Africa'}];
 const m={date:'2026-09-22T00:00:00Z',slug:'asset/a',title:'General Debate',pageUrl:'/en/asset/a',jsonUrl:'/en/asset/a.json',hasTranscript:true};
 const doc={video:{slug:m.slug,date:m.date},transcript:{language:'en',data:[{speaker:{affiliation:'EXA'},paragraphs:[{sentences:[{text:'AI safeguards'}]}],pageUrl:'/en/asset/a?t=3'}]}};
 const request=async url=>({hash:'f'.repeat(64),data:url.includes('meetings.json')?{page:1,total:1,hasMore:false,meetings:[m]}:doc});
 const out=await C.collect({...p,end:p.start},countries,{request});assert.equal(out.records.length,1);assert.equal(out.records[0].region,'Africa');assert.equal(out.records[0].text_sha256,await C.sha('AI safeguards'));assert.equal(out.coverage[0].status,'collected');
 const failed=await C.collect({...p,end:p.start},countries,{request:async()=>{throw Error('Network failure');}});assert.equal(failed.records.length,0);assert.equal(failed.coverage[0].status,'inventory_failed');
 const mismatch=await C.collect({...p,end:p.start},countries,{request:async url=>{const v=await request(url);return url.includes('meetings.json')?v:{...v,data:{...doc,video:{...doc.video,slug:'wrong'}}};}});assert.equal(mismatch.coverage[0].status,'failed');assert.equal(mismatch.records.length,0);
 const abort=new AbortController();abort.abort();await assert.rejects(()=>C.collect(p,countries,{signal:abort.signal,request}),{name:'AbortError'});
 console.log('PASS: browser analysis arithmetic, boundaries, exclusions, deduplication, TF-IDF, limits, collection provenance, failures and cancellation');
})().catch(e=>{console.error(e);process.exit(1);});

// The existing Pages workflow invokes this file; keep the committee gate here.
require('./test_browser_committees.cjs');
