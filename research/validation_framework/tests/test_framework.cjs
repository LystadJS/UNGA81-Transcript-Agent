'use strict';
const assert=require('node:assert/strict');
const C=require('../../../site/cluster-core.js');
const M=require('../metrics.cjs');
const F=require('../frame.cjs');
const {run,fitOne,publicAggregate}=require('../runner.cjs');
const {toInterchangeV1,validateRelational}=require('../interchange.cjs');
const {makeFixture,SETTINGS}=require('../examples/synthetic_fixture.cjs');
let tests=0;
function test(label,fn){return Promise.resolve().then(fn).then(()=>{tests++;process.stdout.write('PASS '+label+'\n');});}
function rejection(fn,fragment){assert.throws(fn,e=>String(e.message).includes(fragment));}
(async()=>{
  await test('independent sklearn ARI/AMI: relabeling',()=>{
    const a=[1,1,2,2,3,3],b=[3,3,1,1,2,2];
    assert.equal(C.ari(a,b),1);assert(Math.abs(M.adjustedMutualInformation(a,b)-1)<1e-10);
  });
  await test('independent sklearn ARI/AMI: crossed three-way partition',()=>{
    const a=[1,1,2,2,3,3],b=[1,2,1,2,3,3];
    assert(Math.abs(C.ari(a,b)-1/6)<1e-12);
    assert(Math.abs(M.adjustedMutualInformation(a,b)-1/6)<1e-10);
  });
  await test('independent sklearn ARI/AMI: unequal contingency',()=>{
    const a=[1,1,1,2,2,2],b=[1,1,2,2,3,3];
    assert(Math.abs(C.ari(a,b)-0.24242424242424243)<1e-12);
    assert(Math.abs(M.adjustedMutualInformation(a,b)-0.2987924581708901)<1e-10);
  });
  await test('independent sklearn degenerate control',()=>{
    assert.equal(M.adjustedMutualInformation([1,1,1,1],[2,2,2,2]),1);
    assert.equal(M.adjustedMutualInformation([1,1,1,1],[1,2,1,2]),0);
    assert.equal(M.evaluateAssignments([0,0,0],[0,0,0]).ari,null);
  });
  await test('noise is abstention, not a jointly assigned class',()=>{
    const m=M.evaluateAssignments([1,1,2,2,0],[1,2,1,2,0]);
    assert.equal(m.assigned_both,4);
    assert.equal(m.pair_opportunities_all,10);
    assert.equal(m.pair_opportunities_assigned_both,6);
    assert.equal(m.assignment_status_agreement,1);
    assert.equal(m.pairwise_assignment_consistency,2/6);
  });
  await test('positive synthetic frame + explicit unavailable inventory',()=>{
    const {frame}=makeFixture();const c=F.validateFrame(frame);
    assert.equal(c.eligible.length,24);assert.equal(c.excluded.length,1);assert.equal(c.inventory_meetings,7);
    assert.equal(new Set(c.eligible.map(r=>r.id)).size,24);
  });
  await test('refuse population changes and invalid source hashes',()=>{
    const {frame}=makeFixture();frame.selection_sha256=F.validateFrame(frame).selection_sha256;
    frame.observations[0].text+='bad';
    rejection(()=>F.validateFrame(frame),'Provided text');
    frame.observations[0].text=makeFixture().frame.observations[0].text;
    frame.observations.reverse();
    rejection(()=>F.validateFrame(frame),'Population');
  });
  await test('refuse held-out dates, duplicate IDs, broken parent digests and spans',()=>{
    for(const [mutate,msg] of [
      [x=>x.observations[0].date='2026-10-05','Reserved'],
      [x=>x.observations[1].id=x.observations[0].id,'duplicate'],
      [x=>x.observations[1].parent_text_sha256=null,'Parent'],
      [x=>x.observations[1].start=x.observations[1].end,'source span'],
      [x=>x.observations[1].source_url='http://unsafe.example.org','HTTPS']
    ]){const {frame}=makeFixture();mutate(frame);rejection(()=>F.validateFrame(frame),msg);}
  });
  await test('refuse unsourced development attribution and unconfirmed speech',()=>{
    const {frame}=makeFixture();frame.split='development';
    frame.source_schema='un.browser.corpus.v1';frame.source_hash_basis='utf8_corpus_export';
    frame.observations.forEach(r=>r.split='development');
    frame.observations[0].meeting_id=null;
    rejection(()=>F.validateFrame(frame),'Development observations');
    frame.observations[0].meeting_id='verified';
    frame.observations[0].date='2026-10-07';
    rejection(()=>F.validateFrame(frame),'pre-holdout');
    frame.observations[0].date='2026-01-01';
    frame.observations[0].speech_id='unverified-person';
    rejection(()=>F.validateFrame(frame),'Unverified speech');
  });
  await test('identical saved-vector cohort and transformation identity',()=>{
    const {frame,saved}=makeFixture(),cohort=F.validateFrame(frame);
    assert.equal(F.alignScores(cohort,saved).values.length,24);
    const broken=structuredClone(saved);broken.rows[3].text_sha256=F.digest('not-original');
    rejection(()=>F.alignScores(cohort,broken),'mismatch');
    broken.rows=broken.rows.slice(1);
    rejection(()=>F.alignScores(cohort,broken),'exactly');
  });
  await test('meeting and affiliation groups preserve source segments',()=>{
    const {frame}=makeFixture(),rows=F.validateFrame(frame).eligible;
    const m=F.unionGroups(rows,'meeting'),a=F.unionGroups(rows,'affiliation');
    assert.equal(m.groups.length,6);
    assert(a.groups.length>=3);
    assert(m.groups.every(group=>new Set(group.map(i=>rows[i].meeting_id)).size===1));
    const copy=structuredClone(rows);
    copy[0].source_family_id='joint-source';copy[1].source_family_id='joint-source';
    // Distinct parents but identical original source family must still be grouped.
    const joined=F.unionGroups(copy,'affiliation');
    assert(joined.groups.some(group=>group.includes(0)&&group.includes(1)),'Multi-affiliation source segment must remain together.');
  });
  await test('insufficient groups are recorded and never resampled as passages',()=>{
    const {frame}=makeFixture(),rows=F.validateFrame(frame).eligible.map(x=>({...x,meeting_id:'single-meeting'}));
    const s=F.schedule(rows,'meeting',12,0.8,9);
    assert.equal(s.status,'skipped');assert.equal(s.attempted,0);assert.equal(s.groups,1);
  });
  await test('group schedules deterministic and paired across settings',()=>{
    const {frame}=makeFixture(),r=F.validateFrame(frame).eligible;
    const a=F.schedule(r,'meeting',10,0.8,8),b=F.schedule(r,'meeting',10,0.8,8);
    assert.equal(a.schedule_sha256,b.schedule_sha256);
    assert.equal(a.attempted,10);assert.equal(a.samples.length,10);
    assert(a.samples.every(x=>x.selected_count===20));
  });
  await test('duplicate-heavy and dominant-source audits',()=>{
    const {frame}=makeFixture(),r=F.validateFrame(frame).eligible.map(o=>({...o}));
    r.slice(0,7).forEach(x=>x.text_sha256=r[0].text_sha256);
    r.slice(0,16).forEach(x=>x.meeting_id='dominant');
    const audit=F.auditSources(r);
    assert(audit.duplicate_text_groups>=1);assert(audit.largest_meeting_share>0.5);
    assert(audit.warnings.length>=2);
  });
  await test('known-cluster numeric fixture with existing PAM and Ward kernels',async()=>{
    const x=[[0,0],[0.1,0.1],[8,0],[8.1,0.1],[0,9],[0.1,9.1]];
    for(const method of ['pam','hierarchical']){
      const fit=await C.fitPartition(x,C.options({algorithm:method,k:3,seed:8,linkage:'ward'}));
      assert(!fit.skipped,method+' skipped');
      assert.equal(new Set(fit.labels).size,3);
      assert(C.ari(fit.labels,[1,1,2,2,3,3])>0.9);
    }
  });
  await test('no-structure controls do not fake a stable partition',async()=>{
    const {frame}=makeFixture(),r=F.validateFrame(frame).eligible.slice(0,8).map(x=>({...x}));
    r.forEach(x=>{x.text='identical invented words';x.text_sha256=F.digest(x.text);});
    const spec={representation_requested:'lsa',algorithm:'pam',k:3,components:3,seed:4,linkage:'ward'};
    const out=await fitOne(r,spec,null);
    assert.notEqual(out.status,'fitted');
    assert.equal(out.assignments,null);
  });
  await test('high-noise density control retains noise as zero, never missing',async()=>{
    const x=Array.from({length:20},(_,i)=>[i*1000, Math.cos(i)*1000]);
    const out=await C.fitPartition(x,C.options({algorithm:'hdbscan',hdbscan:{minClusterSize:12,minSamples:5,selection:'eom'}}));
    assert(!out.skipped,'Density kernel should return explicit noise/labels');
    assert(out.labels.every(x=>Number.isInteger(x)&&x>=-1));
    assert(out.labels.some(x=>x===-1),'High noise should yield explicit unassigned observations');
  });
  await test('failed numerical fit is non-delivery, no fallback labels',async()=>{
    const {frame}=makeFixture();const rows=F.validateFrame(frame).eligible;
    const fn=C.fitPartition;C.fitPartition=async()=>{throw Error('synthetic fitting failure');};
    try{const fit=await fitOne(rows,{representation_requested:'lsa',algorithm:'pam',components:3,k:3,seed:3},null);
      assert.equal(fit.status,'failed');assert.equal(fit.assignments,null);
      assert.equal(fit.failed_fit,1);assert.equal(fit.attempted_fit,1);
    }finally{C.fitPartition=fn;}
  });
  await test('five existing methods, paired representation and v1 ledger',async()=>{
    const {frame,saved}=makeFixture();
    const out=await run(frame,SETTINGS,{saved,replicates:10,group_seed:31});
    assert.equal(out.fit_records.length,5);
    assert.equal(out.comparisons.length,10);
    assert.equal(out.frame.eligible,24);
    assert(out.fit_records.filter(x=>x.status==='fitted').length>=3,'At least three reference fits should converge.');
    assert(out.comparisons.some(x=>x.status==='descriptive'));
    assert(!JSON.stringify(out).includes('Harbor ferry'),'Raw source text must not serialize.');
    const v1=toInterchangeV1(out);
    assert(validateRelational(v1));assert.equal(v1.coverage.eligible,24);assert.equal(v1.coverage.excluded,1);
    assert.equal(v1.results.length,25*5);
    assert(v1.coverage.models.every(m=>m.attempted_fits===m.successful_fits+m.failed_fits));
    assert(v1.coverage.models.every(m=>m.assigned+m.unassigned+m.not_fitted===m.eligible));
    assert.equal(v1.publication_eligible,false);
    const summary=publicAggregate(out);
    assert(!JSON.stringify(summary).includes('synthetic-01'),'Public summary must not contain observation IDs.');
    assert.equal(summary.models.length,5);
    process.stdout.write('VALIDATION_AGGREGATE '+JSON.stringify({fitted:out.fit_records.filter(x=>x.status==='fitted').length,
      cases:out.source_linked_cases.length,failed_or_skipped:out.failure_ledger.length,
      group_units:Object.keys(out.schedules)})+'\n');
  });
  await test('private-development public export refused',async()=>{
    const {frame}=makeFixture(); const cohort=F.validateFrame(frame);
    const object={frame:{split:'development'}};rejection(()=>publicAggregate(object),'Public export refused');
    assert(cohort.population_hash);
  });
  process.stdout.write(JSON.stringify({suite:'source-aware-validation-synthetic',tests,failed:0,
    held_out_opened:0,private_transcript_text_published:0})+'\n');
})().catch(e=>{process.stderr.write('FAIL '+(e.stack||e)+'\n');process.exitCode=1;});
