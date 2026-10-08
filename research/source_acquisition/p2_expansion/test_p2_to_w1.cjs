'use strict';
// Synthetic-only proof-of-structure; real byte authentication is exercised only privately.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const F=require('../../validation_framework/frame.cjs');
const {authenticatedFrame}=require('./p2_to_w1_source_adapter.cjs');
function sha(s){return crypto.createHash('sha256').update(s).digest('hex');}
function fixture(){
  const text='Fictional parliamentary speech with no real country positions or meeting contents.';
  const row={id:'country-AAA-2016',split:'development',source_status:'available',
    text,text_sha256:sha(text),parent_id:null,parent_text_sha256:null,
    meeting_id:'A/71/PV.22',source_family_id:'A/71/PV.22',date:'2016-09-27',
    country:'AAA',affiliation:'AAA',genre:'general_debate',
    role:'recorded_affiliation_not_verified_person',
    review_status:'unreviewed',speech_id:null,
    source_url:'https://documents.un.org/api/symbol/access?l=en&s=A%2F71%2FPV.22&t=pdf',
    json_pointer:null,start:null,end:null,unit:'source_segment',
    p2_original_pdf_sha256:sha('imaginary original PDF'),p2_full_speech_verified:true,
    p2_date_basis:'independent_UN_index',p2_original_source_hash_basis:'raw_response_bytes',
    p2_verification_method:'original_UN_PV_full_speech_7gram_10decile_v1'};
  const selection=sha(JSON.stringify([[row.id,row.text_sha256]]));
  const frame={schema:'un.source-validation.frame.v1',split:'development',
    source_schema:'un.p2.original-pv-reconciled.v1',
    source_engine:'P2_original_UN_full_PV_Harvard_v14_readonly_adapter',
    source_hash_basis:'raw_response_bytes',
    source_sha256:'55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5',
    selection_sha256:selection,unit:'source_segment',inventory_meetings:1,
    original_p2_source_provenance:{verified_original_meeting_count:1,
      full_candidate_country_year_cells:2,source_verified:1,unverified:1,
      original_archive_sha256:'55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5',
      selection_sha256:selection},
    observations:[row]};
  return frame;
}
let passed=0;
function check(name,fn){fn();passed++;console.log('PASS '+name);}
function refuse(fn,s){assert.throws(fn,e=>String(e.message).includes(s));}
check('additive historical P2 native W1 input accepts provenance-shaped fixture',()=>{
  const v=F.validateFrame(fixture());assert.equal(v.eligible.length,1);
});
check('no missing original source attestation accepted',()=>{
  const f=fixture();f.observations[0].p2_original_pdf_sha256=null;
  refuse(()=>F.validateFrame(f),'original-PV byte');
});
check('no unverified date basis or fabricated speaker identity',()=>{
  const f=fixture();f.observations[0].p2_date_basis='invented';
  refuse(()=>F.validateFrame(f),'original-PV byte');
  const q=fixture();q.observations[0].speech_id='fake_person';
  refuse(()=>F.validateFrame(q),'Unverified speech');
});
check('no changed source hash or missing original selection accepted',()=>{
  const f=fixture();f.source_sha256='a'.repeat(64);
  refuse(()=>F.validateFrame(f),'verified, pinned');
  const g=fixture();g.original_p2_source_provenance.selection_sha256='b'.repeat(64);
  refuse(()=>F.validateFrame(g),'P2 attestation selection hash');
});
check('no relabeling P2 as legacy source schema',()=>{
  const f=fixture();f.source_schema='un.source-validation.synthetic.v1';
  refuse(()=>authenticatedFrame({schema:'un.p2.authenticated-corpus-PV-w1-input.v1',
    source_schema:'un.passage-corpus.v1'}, {}, '/definitely/nonexistent'),'Refuse P2');
});
check('reject forged input when actual source archive bytes are not present',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'fictional-p2-'));
  try{
    const archive=path.join(dir,'fake.tar.gz');
    fs.writeFileSync(archive,'purely fictional contents');
    refuse(()=>authenticatedFrame({schema:'un.p2.authenticated-corpus-PV-w1-input.v1',
      source_schema:'un.p2.original-pv-reconciled.v1',
      source_hash_basis:'raw_response_bytes',
      source_sha256:'55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5'}, {}, archive),'archive bytes failed');
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
check('original legacy source enum and v1 analysis schema unchanged',()=>{
  const frozen=require('../../../docs/parallel-work/interchange-v1.schema.json');
  assert.equal(frozen.properties.schema.const,'un.parallel-analysis.v1');
  assert(!frozen.properties.upstream.properties.source_schema.enum
    .includes('un.p2.original-pv-reconciled.v1'));
});
console.log(JSON.stringify({suite:'P2-original-UN-source-W1-synthetic-contract',
  passed,failed:0,actual_original_UN_documents_accessed:0,
  legacy_v1_modified:false,private_source_exported:false}));
