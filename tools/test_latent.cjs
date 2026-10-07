'use strict';
const assert=require('node:assert/strict'),L=require('../site/latent-core.js'),V=require('../site/latent-view.js'),{fixture}=require('./latent_fixture.cjs');
const copy=x=>JSON.parse(JSON.stringify(x));
(async()=>{
  const passed=[];const check=async(name,fn)=>{await fn();passed.push(name);console.log('PASS '+name);};
  const f=await fixture(),result=await L.run(f.payload,f.plan,{execution:'Node engineering fixture',node:process.version}),archive=await L.pack(f.payload,result);
  await check('reviewed inputs remain exact; parent and excerpt counts differ',async()=>{assert.equal(result.entries.length,4);assert.equal(result.entries[0].result.counts.matched,18);assert.equal(result.entries[2].result.counts.matched,6);assert.equal(result.coverage.length,6);assert.ok(result.coverage.every(r=>r.coverage_fraction<1&&r.passages===3));assert.equal(result.source_hash,await L.hash(f.payload.text));});
  await check('stored JSON result and coordinates restore without numerical refitting',async()=>{const restored=await L.restore(archive);assert.deepEqual(restored.result,copy(result));assert.equal(JSON.parse(archive).result_json,JSON.stringify(result));assert.equal(restored.archive_text,archive);assert.equal(restored.payload.text,f.payload.text);assert.ok(Object.isFrozen(restored.result.entries[0]));});
  await check('archive and source corruption rejected',async()=>{for(const field of ['input_json','result_json']){const a=JSON.parse(archive);a[field]+=' ';await assert.rejects(()=>L.restore(JSON.stringify(a)),/integrity/);}const p=copy(f.plain),v=L.parse(p.text);v.records[0].text+=' changed';p.text=JSON.stringify(v);await assert.rejects(()=>L.input(p),/hash mismatch/);});
  await check('reviewed derivative offset corruption rejected',async()=>{const p=copy(f.payload),v=L.parse(p.text);v.units.records[0].start++;p.text=JSON.stringify(v);await assert.rejects(()=>L.input(p));});
  await check('cross-unit agreement withheld',async()=>{assert.match(L.paired(result.entries[0],result.entries[2]).withheld,/Different analytical units/);});
  await check('changed populations and text hashes withheld',async()=>{const other=copy(result.entries[1]);other.result.matched.pop();assert.match(L.paired(result.entries[0],other).withheld,/population/);const altered=copy(result.entries[1]);altered.result.methods.clusters.points[0].text_sha256='a'.repeat(64);assert.ok(L.paired(result.entries[0],altered).withheld);});
  await check('ARI matches known contingency examples',async()=>{assert.equal(L.ari([1,1,2,2],[4,4,5,5]),1);assert.equal(L.ari([1,1,2,2],[1,2,1,2]),-0.5);assert.equal(L.ari([1],[2]),null);});
  await check('group identifiers are nominal; identical partitions agree',async()=>{const other=copy(result.entries[0]);other.id='renumbered';other.result.methods.clusters.points.forEach(p=>p.cluster+=10);assert.equal(L.paired(result.entries[0],other).ari,1);});
  await check('three-parent pilot withholds undersized baseline rather than inventing groups',async()=>{const small=await fixture(3),r=await L.run(small.payload,small.plan);assert.equal(r.entries[2].summary.status,'withheld');assert.match(r.entries[2].summary.reason,/four passages/);assert.equal(r.entries[0].result.counts.matched,9);});
  await check('parent-balanced composition is a summary, not a refit',async()=>{const entry={method:'clusters',result:{matched:[{id:'a',parent_id:'one'},{id:'b',parent_id:'one'},{id:'c',parent_id:'one'},{id:'d',parent_id:'two'}],methods:{clusters:{points:[{id:'a',cluster:1},{id:'b',cluster:1},{id:'c',cluster:1},{id:'d',cluster:2}]}}}};const c=L.compositions(entry);assert.equal(c.totals[0].passage_weighted,0.75);assert.equal(c.totals[0].parent_balanced,0.5);});
  await check('display-only changes leave fitted scores and labels unchanged',async()=>{const p=copy(f.plan);p.compare_parents=false;p.settings=[p.settings[0],{...copy(p.settings[0]),label:'different display',options:{...p.settings[0].options,umapSeed:77,neighbors:4}}];const r=await L.run(f.payload,p),pair=r.pairs[0];assert.equal(pair.geometry_identical,true);assert.equal(pair.labels_identical,true);assert.equal(pair.ari,1);});
  await check('all-unassigned HDBSCAN remains visible and has no ARI',async()=>{const p=copy(f.plan);p.compare_parents=false;p.settings.forEach(row=>{row.options.algorithm='hdbscan';row.options.hdbscan={minClusterSize:600,minSamples:3,selection:'eom'};});const r=await L.run(f.payload,p);assert.equal(r.pairs[0].ari,null);assert.equal(r.pairs[0].transitions.unassigned_both,18);assert.equal(r.entries[0].summary.assignment_fraction,0);await L.restore(await L.pack(f.payload,r));});
  await check('NMF uses component alignment rather than a hard partition score',async()=>{const p=copy(f.plan);p.compare_parents=false;p.settings=[42,47].map(seed=>({label:'NMF '+seed,method:'nmf',options:{components:2,seed,starts:1,maxIterations:100}}));const r=await L.run(f.payload,p);assert.ok(Number.isFinite(r.pairs[0].nmf.mean_cosine));assert.equal(r.pairs[0].ari,undefined);await L.restore(await L.pack(f.payload,r));});
  await check('paired omission schedules keep parent children together',async()=>{const p=copy(f.plan);p.compare_parents=false;p.stability.enabled=true;const r=await L.run(f.payload,p);assert.equal(r.pairs[0].paired_group_schedule,true);for(const e of r.entries){const s=e.result.methods.clusters.stability;assert.equal(s.group_count,6);assert.ok(s.groups.every(g=>g.ids.length===3));assert.equal(s.runs.length,10);}});
  await check('plans are bounded and duplicate numerical settings are refused',async()=>{const p=copy(f.plan);p.settings=Array.from({length:13},()=>copy(p.settings[0]));assert.throws(()=>L.validatePlan(p),/1–12/);p.settings=p.settings.slice(0,2);assert.throws(()=>L.validatePlan(p),/Duplicate/);const wrong=copy(f.plan);wrong.settings[0].options.representation='compare';assert.throws(()=>L.validatePlan(wrong),/separate PCA/);});
  await check('ordinary corpus cannot claim reviewed excerpt provenance',async()=>{const p=copy(f.plain),v=L.parse(p.text);v.records[0].parent_id='fake';p.text=JSON.stringify(v);await assert.rejects(()=>L.input(p),/validated reviewed/);await assert.rejects(()=>L.run(f.plain,f.plan),/requires a reviewed/);});
  await check('rendered source labels are escaped and HTML has no script tags',async()=>{const r=copy(result);r.entries[0].label='<script>alert(1)</script>';const html=V.html(r);assert.ok(html.includes('&lt;script&gt;'));assert.ok(!/<script\b/i.test(html));assert.ok(html.includes('Parent coverage'));assert.ok(html.includes('href="https://transcripts.un.org/'));});
  await check('CSV strings cannot become spreadsheet formulas',async()=>{const r=copy(result);r.entries[0].summary.label='=HYPERLINK("https://invalid")';assert.ok(V.csv(r).includes("'=HYPERLINK"));});
  await check('progress cancellation rejects without a completed result',async()=>{await assert.rejects(()=>L.run(f.payload,f.plan,{},async()=>{throw Error('TEST CANCEL');}),/TEST CANCEL/);});
  await check('saved A/B comparison retains separate coverage, weights and cohort changes',async()=>{
    const p=copy(f.plan);p.base={...p.base,topic:'alpha',phrases:['alpha'],exclude:[]};
    const b=await L.run(f.payload,p),bText=await L.pack(f.payload,b);
    const comparison=await L.compareSaved(await L.restore(archive),await L.restore(bText));
    assert.equal(comparison.snapshots[0].coverage.length,6);assert.equal(comparison.snapshots[1].coverage.length,1);
    assert.equal(comparison.coverage_change.filter(r=>r.reason==='Only in A retained cohort').length,5);
    const shared=comparison.coverage_change.find(r=>r.comparable);assert.equal(shared.coverage_change,0);assert.ok(Math.abs(shared.observation_share_change-5/6)<1e-12);
    assert.match(V.html(comparison),/Saved-run coverage and weighting/);assert.match(V.coverageCSV(comparison),/"A"/);assert.match(V.coverageCSV(comparison),/"B"/);
    assert.ok(comparison.pairs.every(r=>r.withheld));
  });
  await check('NMF and Gaussian summaries balance parents without hardening soft membership',async()=>{
    const matched=['a','b','c','d','e'].map((id,i)=>({id,parent_id:i<3?'one':i===3?'two':'undefined',country:'Synthetic',source_url:'https://transcripts.un.org/en/asset/test/group0'}));
    const points=matched.map((r,i)=>({id:r.id,shares:i<3?[.8,.2]:i===3?[.1,.9]:null}));
    const entry={method:'nmf',result:{matched,methods:{nmf:{parameters:{components:2},points}}}};
    const m=L.mixtures(entry);assert.ok(Math.abs(m.totals[0].passage_weighted-.625)<1e-12);assert.ok(Math.abs(m.totals[0].parent_balanced-.45)<1e-12);
    assert.equal(m.parent_count,3);assert.equal(m.defined_parents,2);assert.deepEqual(m.undefined_ids,['e']);assert.equal(m.rows[2].shares[0],null);
    const g={method:'clusters',result:{matched:matched.slice(0,4),methods:{clusters:{algorithm:'gmm',parameters:{k:2},points:points.slice(0,4).map(p=>({id:p.id,memberships:p.shares}))}}}};
    assert.deepEqual(L.mixtures(g).totals,m.totals);g.result.methods.clusters.points[0].memberships=[.8,.8];assert.throws(()=>L.mixtures(g),/Invalid saved mixture/);
    assert.match(V.weightsCSV({entries:[{...entry,id:'test',unit:'excerpt',mixture:m}]}),/defined_groups/);
  });
  await check('recomputed hashes cannot conceal changed cohorts, coverage or cached summaries',async()=>{
    for(const mutate of [r=>r.entries.pop(),r=>r.entries[0].result.matched.pop(),r=>r.coverage[0].coverage_fraction=.001,r=>r.coverage[0].parent_text_sha256='0'.repeat(64),r=>r.entries[0].summary.usable=0,r=>r.entries[0].result.parameters.clustering.seed++]){
      const changed=JSON.parse(archive),r=JSON.parse(changed.result_json);mutate(r);changed.result_json=JSON.stringify(r);changed.result_sha256=await L.hash(changed.result_json);
      await assert.rejects(()=>L.restore(JSON.stringify(changed)),/differ|Changed saved point/);
    }
  });
  await check('legacy archives keep exact results and no numerical method is invoked on restore',async()=>{
    const legacy=copy(result);legacy.engine='latent-comparison-1.0.0';legacy.coverage.forEach(r=>delete r.parent_text_sha256);legacy.entries.forEach(r=>delete r.mixture);
    const text=await L.pack(f.payload,legacy),C=require('../site/cluster-core.js'),N=require('../site/nmf-core.js'),oldC=C.run,oldN=N.run;
    try{C.run=N.run=()=>{throw Error('Unexpected numerical refit');};const restored=await L.restore(text);assert.equal(restored.archive_text,text);assert.deepEqual(restored.result,legacy);}finally{C.run=oldC;N.run=oldN;}
  });
  await check('unchanged excerpt text with changed parent context cannot earn a comparison score',async()=>{
    const changed=copy(result.entries[0]);changed.result.matched[0].parent_text_sha256='0'.repeat(64);assert.match(L.paired(result.entries[0],changed).withheld,/parent text changed/);
  });
  console.log(JSON.stringify({status:'PASS',synthetic_only:true,checks:passed.length,passed,node:process.version,original_private_corpus_used:false}));
})().catch(error=>{console.error(error);process.exitCode=1;});
