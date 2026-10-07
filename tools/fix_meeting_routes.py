"""One-time exact patch for actual UN meeting route families; no source text changes."""
from pathlib import Path
old=r'^asset\/[A-Za-z0-9_-]+\/[A-Za-z0-9_-]+$'
new=r'^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+){1,5}$'
for name in ['site/meeting-picker-core.js','site/collector.js','site/analysis-core.js']:
 p=Path(name);s=p.read_text();assert s.count(old)==1,name;p.write_text(s.replace(old,new))
for name in ['site/index.html','site/analysis-core.js','site/analysis-ui.js','site/cluster-worker.js','site/nmf-worker.js','site/release.json']:
 p=Path(name);p.write_text(p.read_text().replace('1.12.0','1.12.1'))
p=Path('site/index.html');s=p.read_text();assert 'collector.js?v=1.2.0' in s;p.write_text(s.replace('collector.js?v=1.2.0','collector.js?v=1.12.1'))
p=Path('tools/test_meeting_picker.cjs');s=p.read_text();anchor=" console.log(JSON.stringify({status:'PASS',synthetic_only:true,checks:passed.length,passed,node:process.version}));"
assert s.count(anchor)==1
extra=""" await check('canonical non-asset HRC and treaty-body meeting routes are supported',async()=>{
  for(const slug of ['hrc/63/25','ced/593','ga/81/1']){
   const m={...meetings[0],slug,pageUrl:'/en/'+slug,jsonUrl:'/en/'+slug+'.json'};
   const inventory=await P.list(date,{request:async()=>({hash,data:{page:1,total:1,hasMore:false,meetings:[m]}})});
   const params={...P.selection(date,inventory.meetings[0]),topic:'',region:'All regions',methods:['frequency']};
   const collected=await C.collect(params,[],{request:async url=>url.includes('meetings.json')?{hash,data:{page:1,total:1,hasMore:false,meetings:[m]}}:{hash,data:transcript(slug)}});
   assert.equal(collected.records[0].meeting_slug,slug);assert.equal((await A.analyze(collected,params)).counts.matched,1);
  }
  for(const slug of ['../hrc/63','hrc//25','/hrc/63/25','hrc/63/25?x=1','https://example.test/hrc','hrc/%2e%2e/25'])assert.equal(P.validSlug(slug),false,slug);
 });
"""
p.write_text(s.replace(anchor,extra+anchor))
p=Path('tools/test_meeting_picker_ui.cjs');p.write_text(p.read_text().replace('asset/test/second','hrc/63/25').replace("u.pathname.includes('second')","u.pathname.includes('hrc/63/25')"))
p=Path('docs/INDIVIDUAL_MEETINGS.md');p.write_text(p.read_text()+'''\n## Live source route correction — 7 October 2026\n\nThe live inventory includes canonical routes such as `hrc/63/25` and `ced/593`,\nnot only `asset/...` video routes. Browser 1.12.1 accepts safe multi-segment IDs\nfrom the verified UN inventory, still rejects traversal/queries/arbitrary URLs,\nand rechecks the exact selected ID at collection. The regression fixtures now\ninclude HRC and treaty-body routes. The initial asset-only assumption was found\nby the separate live check, not silently classified as missing transcript data.\n''')
print('Patched canonical meeting ID validation and cache versions; added non-asset route regression coverage.')
