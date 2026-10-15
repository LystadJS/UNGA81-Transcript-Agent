'use strict';
const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {VERSION, CONTRACT_VERSION, audit, readManifest, sha} = require('./audit.cjs');
const BYTES = Buffer.from('A wholly invented synthetic original PDF surrogate.');
const TEXT = 'Synthetic transcript text, no diplomatic content.';
const hash = sha(BYTES), textHash = sha(Buffer.from(TEXT));
const repeat = x => x.repeat(64);
function frame(id, start, end) {
  return {id, start_year:start, end_year:end, meeting_design:'general_debate',genre:'debate',
    language:'en',translation_modality:'original',roster_definition:'recorded_affiliation',
    selection_design:'probability_meeting_sample',sampling_unit:'meeting',frame_unit:'country_year',
    source_schema:'synthetic.original.v1',source_hash_basis:'synthetic',
    source_sha256:repeat('a'),selection_sha256:repeat(id==='early'?'b':'c')};
}
function receipt(id, meeting, year, digest, thash) {
  return {document_id:id,meeting_id:meeting,year,source_family_id:meeting,
    available:true,transcript_available:true,source_sha256:digest,text_sha256:thash,
    source_hash_basis:'synthetic',text_hash_basis:'synthetic',source_verification:'synthetic'};
}
function row(id, frameId, documentId, meeting, year, digest) {
  return {id,frame_id:frameId,document_id:documentId,meeting_id:meeting,
    source_family_id:meeting,speech_id:'speech-'+id,country:'AAA',year,
    event_date:year+'-09-23',actor_kind:'recorded_affiliation',
    attribution:'verified_recorded_affiliation',attribution_receipt_id:'attestation-'+id,
    source_status:'available',missing_reason:null,outcome_status:'observed',
    inclusion_probability:0.5,probability_unit:'meeting',speech_length:125,
    language:'en',genre:'debate',translation_modality:'original',text_sha256:digest};
}
function fixture() {
  return {schema:VERSION,contract_version:CONTRACT_VERSION,fixture_kind:'synthetic',publication_eligible:false,
    frames:[frame('early',2008,2015),frame('late',2016,2023)],
    receipts:[receipt('doc-a','A/65/PV.1',2010,hash,textHash),receipt('doc-b','A/75/PV.1',2020,repeat('d'),repeat('e'))],
    observations:[row('o-a','early','doc-a','A/65/PV.1',2010,textHash),
      row('o-b','late','doc-b','A/75/PV.1',2020,repeat('e'))]};
}
function mutation(name, action, code, level='observation') {
  test(name,()=>{
    const x=fixture();action(x);
    const out=audit(x);
    assert.equal(out.inference_eligible,false);
    assert.equal(out.publication_eligible,false);
    assert(out.counts[code]>=1, name+' missing diagnostic '+code);
    if(level==='observation')assert(out.totals.eligible_metadata < 2, name+' must withhold metadata eligibility');
  });
}
test('unmodified metadata is conditionally eligible; disjoint eras remain uncertain',()=>{
  const out=audit(fixture());assert.equal(out.totals.eligible_metadata,2);
  assert.equal(out.private_source_validation,'NOT RUN');assert.equal(out.text_validation,'NOT RUN');
  assert.equal(out.comparisons[0].status,'uncertain');assert.equal(out.frames[0].years['2010'].total,1);
  assert.equal(out.sampling_inference.startsWith('NOT IDENTIFIED'),true);
});
test('original and text digests are checked from supplied byte/text bases',()=>{
  const out=audit(fixture(),{originals:{'doc-a':BYTES},canonicalTexts:new Map([['doc-a',TEXT]])});
  assert.equal(out.counts.checksum_mismatch,undefined);
  assert.equal(out.counts.text_checksum_mismatch,undefined);
  assert.equal(out.private_source_validation,'PARTIAL_OR_FAILED');
  assert.equal(out.text_validation,'PARTIAL_OR_FAILED');
});
test('supplied original wrong hash excludes downstream observation',()=>{
  const x=fixture();const out=audit(x,{originals:{'doc-a':Buffer.from('tampered')}});
  assert.equal(out.counts.checksum_mismatch,1);
  assert(out.eligibility[0].exclusions.includes('document_receipt_invalid'));
  assert.equal(out.private_source_validation,'PARTIAL_OR_FAILED');
});
test('supplied changed canonical text excludes downstream observation',()=>{
  const out=audit(fixture(),{canonicalTexts:{'doc-a':'tampered'}});
  assert.equal(out.counts.text_checksum_mismatch,1);
  assert(out.eligibility[0].exclusions.includes('document_receipt_invalid'));
});
mutation('invalid source hash format',x=>x.receipts[0].source_sha256='bad','invalid_checksum','receipt');
mutation('invalid text hash format',x=>x.receipts[0].text_sha256='bad','invalid_text_checksum','receipt');
mutation('duplicate document identity',x=>x.receipts.push({...x.receipts[0]}),'duplicate_document_identity','receipt');
mutation('duplicate observation identity',x=>x.observations.push({...x.observations[0]}),'duplicate_observation_identity');
mutation('unavailable original',x=>x.receipts[0].available=false,'missing_document');
mutation('unavailable transcript',x=>x.receipts[0].transcript_available=false,'missing_transcript');
mutation('ambiguous speaker',x=>x.observations[0].attribution='unreviewed','ambiguous_attribution');
mutation('missing attribution receipt',x=>x.observations[0].attribution_receipt_id=null,'ambiguous_attribution');
mutation('missing year',x=>x.observations[0].year=null,'missing_or_inconsistent_year');
mutation('wrong year',x=>x.observations[0].year=2020,'missing_or_inconsistent_year');
mutation('document-year disagreement',x=>x.receipts[0].year=2011,'document_year_mismatch');
mutation('missing speech ID',x=>x.observations[0].speech_id=null,'incomplete_lineage');
mutation('missing outcome',x=>x.observations[0].outcome_status='missing','missing_outcome');
mutation('missing probability',x=>x.observations[0].inclusion_probability=null,'sampling_probability_unknown');
mutation('zero inclusion probability',x=>x.observations[0].inclusion_probability=0,'positivity_violation');
mutation('negative inclusion probability',x=>x.observations[0].inclusion_probability=-0.1,'positivity_violation');
mutation('inclusion probability greater than one',x=>x.observations[0].inclusion_probability=1.1,'positivity_violation');
mutation('wrong stage of sampling',x=>x.observations[0].probability_unit='speech','sampling_unit_mismatch');
mutation('wrong meeting link',x=>x.observations[0].meeting_id='A/65/PV.2','meeting_document_mismatch');
mutation('wrong text lineage',x=>x.observations[0].text_sha256=repeat('f'),'text_provenance_mismatch');
mutation('missing speech length',x=>x.observations[0].speech_length=null,'speech_length_unknown');
mutation('missing language',x=>x.observations[0].language=null,'missing_observation_language');
mutation('invalid event date',x=>x.observations[0].event_date='2010-02-30','invalid_event_date');
mutation('hash basis mismatch',x=>x.receipts[0].source_hash_basis='raw_response_bytes','original_hash_basis_mismatch');
mutation('unaccepted receipt source verification',x=>x.receipts[0].source_verification='provisional','document_receipt_invalid','receipt');
test('missing and structural non-risk retain distinct denominators and reasons',()=>{
  const x=fixture();x.observations.push({...row('n','early',null,null,2011,null),source_status:'structurally_not_at_risk',
    missing_reason:'not member of the hypothetical organization',inclusion_probability:null});
  x.observations.push({...row('u','early',null,null,2012,null),source_status:'unverified',
    missing_reason:'source missing',inclusion_probability:null});
  const out=audit(x);assert.equal(out.totals.observations,4);assert.equal(out.frames[0].structurally_not_at_risk,1);
  assert.equal(out.frames[0].unverified,1);
  assert.equal(out.counts.sampling_probability_unknown,1);
  assert.equal(out.totals.eligible_metadata,2);
});
test('speech-country collisions invalidate both observations',()=>{
  const x=fixture();x.observations[1].meeting_id=x.observations[0].meeting_id;
  x.observations[1].speech_id=x.observations[0].speech_id;
  x.observations[1].country='BBB';
  const out=audit(x);assert.equal(out.counts.speech_identity_collision,2);
  assert.equal(out.totals.eligible_metadata,0);
});
test('sampling-frame mismatches are inadmissible, not merely uncertain',()=>{
  const x=fixture();x.frames[1].selection_design='convenience';
  const out=audit(x);assert.equal(out.comparisons[0].status,'inadmissible');
  assert(out.comparisons[0].mismatched_dimensions.includes('selection_design'));
});
test('genre differences prevent cross-frame pooling',()=>{
  const x=fixture();x.frames[1].genre='committee';
  assert.equal(audit(x).comparisons[0].status,'inadmissible');
});
test('within-frame year comparisons have descriptive-only supported status',()=>{
  const x=fixture();x.receipts.push(receipt('doc-c','A/66/PV.1',2011,repeat('f'),repeat('0')));
  x.observations.push(row('o-c','early','doc-c','A/66/PV.1',2011,repeat('0')));
  const out=audit(x);assert.equal(out.within_frame_comparisons[0].status,'supported');
  assert.equal(out.within_frame_comparisons[0].scope,'within-frame descriptive metadata only');
});
test('private fixtures never emit source-bearing row identities',()=>{
  const x=fixture();x.fixture_kind='private_development';
  x.frames.forEach(f=>f.source_hash_basis='raw_response_bytes');
  x.receipts.forEach(r=>{r.source_hash_basis='raw_response_bytes';r.source_verification='full_original_verified';});
  const out=audit(x);const serialized=JSON.stringify(out);
  assert.equal(out.eligibility.length,0);assert.equal(out.problems.length,0);
  assert(!serialized.includes('doc-a')&&!serialized.includes('o-a'));
  assert.equal(out.publication_eligible,false);
});
test('manifest rejects embedded original text, embeddings and private paths',()=>{
  for(const [key,val] of [['text','original'],['vector',[1]],['pdf_path','/private/source']]){
    const x=fixture();x.observations[0][key]=val;
    assert.throws(()=>audit(x),/Source-bearing field forbidden/);
  }
});
test('unversioned input, synthetic basis in private records and missing release lock fail closed',()=>{
  for(const mutate of [x=>delete x.contract_version, x=>x.publication_eligible=true,
    x=>{x.fixture_kind='private_development';}, x=>{x.frames[0].start_year=2024;}]){
    const x=fixture();mutate(x);assert.throws(()=>audit(x));
  }
});
test('readManifest provides versioned deterministic JSON replay',()=>{
  const p=path.join(fs.mkdtempSync(path.join(os.tmpdir(),'source-audit-')),'manifest.json');
  try {fs.writeFileSync(p,JSON.stringify(fixture()));const first=JSON.stringify(audit(readManifest(p)));
    assert.equal(first,JSON.stringify(audit(readManifest(p))));}
  finally {fs.rmSync(path.dirname(p),{recursive:true,force:true});}
});
