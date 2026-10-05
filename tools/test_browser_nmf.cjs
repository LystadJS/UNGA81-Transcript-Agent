const assert=require('node:assert/strict');
const N=require('../site/nmf-core.js'),A=require('../site/analysis-core.js'),P=require('../site/passage-selection.js'),V=require('../site/nmf-view.js');
const close=(a,b,t=1e-8)=>assert.ok(Math.abs(a-b)<t,`${a} != ${b}`);
(async()=>{
  // Rank-two nonnegative matrix with exact known reconstruction, including mixtures.
  const rows=[[1,0,0],[0,1,1],[1,1,1],[2,0,0],[0,2,2],[2,1,1]],vectors=rows.map(r=>new Map(r.map((v,j)=>['t'+j,v])));
  const records=rows.map((_,i)=>({id:'p'+i,text_sha256:'a'.repeat(64),text:i%2?'peace security diplomacy':'climate energy emissions',date:'2026-09-22',scope:'general_debate',country:'Example',meeting:'Meeting '+i%3,source_url:'https://example.org/'+i}));
  const f=await N.run(records,vectors,{components:2,maxIterations:1000,tolerance:1e-6});
  assert.ok(f.diagnostics.relative_residual<0.003);
  // MU approaches exact zeros slowly: low residual alone must not imply convergence.
  assert.equal(f.diagnostics.converged,false);assert.match(f.warnings.join(' '),/iteration limit/);
  for(const c of f.components)close(c.norm,1);for(const p of f.points)close(p.shares.reduce((a,b)=>a+b,0),1);
  assert.deepEqual(f,await N.run(records,vectors,{components:2,maxIterations:1000,tolerance:1e-6}));
  for(const s of f.diagnostics.starts)for(let i=1;i<s.history.length;i++)assert.ok(s.history[i].residual<=s.history[i-1].residual+1e-9);
  const perm={...f,factors:{H:[...f.factors.H].reverse()},points:f.points.map(p=>({...p,shares:[...p.shares].reverse()}))};
  const aligned=N.align(f,perm);close(aligned.mean_cosine,1);close(aligned.mean_mixture_l1,0);assert.deepEqual(aligned.components.map(c=>c.matched_component),[2,1]);
  const missing={components:[{},{}],vocabulary:['other'],factors:{H:[[1],[1]]},points:[]};close(N.align(f,missing).mean_cosine,0);assert.equal(N.align(f,missing).mean_mixture_l1,null);
  // Brute-force reference for non-greedy one-to-one alignment.
  assert.deepEqual(N.assignment([[.9,.8,.1],[.89,.1,0],[0,.2,.95]]),[1,0,2]);
  const zero=await N.run([...records,{id:'empty'}],[...vectors,new Map()],{components:2});assert.equal(zero.excluded[0].id,'empty');
  assert.ok((await N.run(records.slice(0,3),vectors.slice(0,3),{components:2})).skipped);
  assert.ok((await N.run(records,vectors,{components:6})).skipped);
  assert.ok((await N.run(Array(601).fill(records[0]),[],{components:2})).skipped);
  await assert.rejects(()=>N.run(records,[new Map([['x',-1]]),...vectors.slice(1)],{components:2}),/nonnegative/);
  await assert.rejects(()=>N.run(records,vectors,{components:2},async()=>{throw Error('cancel');}),/cancel/);
  assert.throws(()=>N.options({components:1}));assert.throws(()=>N.options({stability:{enabled:true,replicates:2}}));
  const stable=await N.run(records,A.tfidf(records).vectors,{components:2,stability:{enabled:true,replicates:10}});
  assert.equal(stable.stability.attempted,10);assert.equal(stable.stability.successful,10);assert.equal(stable.stability.sample_group_count,2);
  assert.ok(stable.stability.unique_group_samples<=3);assert.equal(stable.stability.components[0].count,10);
  const corpus={schema:'un.browser.corpus.v1',coverage:[],records:records.map((r,i)=>({...r,language:'en',region:'Unmapped',text:r.text+' distinct'+i}))};
  const review={schema:'un.passage-type-review.v1',corpus_sha256:'b'.repeat(64),choices:corpus.records.map((r,i)=>({id:r.id,text_sha256:r.text_sha256,type:i<4?'substantive_speech':'procedure',confirmed:true,reviewer:'Synthetic reviewer',reviewed_at:'2026-09-28T12:00:00Z'}))};
  const selection={policy:'substantive',review,corpus_sha256:review.corpus_sha256};assert.equal(P.validate(corpus,selection).selected.size,4);
  for(const bad of [{...selection,corpus_sha256:'0'.repeat(64)},{...selection,review:{...review,choices:review.choices.slice(1)}},{...selection,review:{...review,choices:review.choices.map((c,i)=>i?c:{...c,confirmed:false})}}])assert.throws(()=>P.validate(corpus,bad));
  const analysis=await A.analyze(corpus,{topic:'',start:'2026-09-22',end:'2026-09-22',region:'All regions',scope:'all',methods:['nmf'],nmf:{components:2},passageSelection:selection});
  assert.equal(analysis.counts.input,6);assert.equal(analysis.counts.eligible,4);assert.equal(analysis.methods.nmf.usable_count,4);assert.equal(corpus.records.length,6);assert.equal(analysis.passage_selection.excluded_ids.length,2);
  const escaped=structuredClone(f);escaped.components[0].terms[0].term='<script>x</script>';
  const html=V.render(escaped,records,()=>'<table></table>');assert.ok(!html.includes('<script>'));assert.ok(html.includes('&lt;script&gt;'));assert.ok(html.includes('https://example.org/'));
  console.log('PASS NMF reconstruction, monotonic error, scaling, reproducibility, permutation alignment, vocabulary changes, source limits, cancellation, grouped refits, reviewed selection and safe rendering');
})().catch(e=>{console.error(e);process.exitCode=1;});
