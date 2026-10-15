"use strict";
const assert=require("node:assert/strict"),test=require("node:test");
const {audit,VERSION,sha}=require("./audit.cjs");
const h=sha("synthetic bytes");
const fixture=()=>({schema:VERSION,frames:[{id:"early",year:2010,meeting_design:"general",genre:"debate",language:"en",translation_modality:"original",roster_definition:"members",selection_design:"random"},{id:"late",year:2020,meeting_design:"general",genre:"debate",language:"en",translation_modality:"original",roster_definition:"members",selection_design:"random"}],receipts:[{document_id:"doc1",meeting_id:"m1",year:2010,available:true,transcript_available:true,sha256:h,text_sha256:h}],observations:[{id:"s1",frame_id:"early",document_id:"doc1",meeting_id:"m1",speech_id:"speech1",country:"AAA",year:2010,attribution:"verified",outcome_available:true,inclusion_probability:0.5,speech_length:100,text_sha256:h}]});
test("valid metadata remains eligible; private validation not run",()=>{const a=audit(fixture());assert.equal(a.totals.eligible,1);assert.equal(a.private_source_validation,"NOT RUN");assert.equal(a.comparisons[0].status,"uncertain");});
test("original bytes checksum mismatch",()=>{assert.equal(audit(fixture(),{originals:{doc1:Buffer.from("corrupted")}}).counts.checksum_mismatch,1);});
test("invalid checksum format",()=>{const m=fixture();m.receipts[0].sha256="bad";assert.equal(audit(m).counts.invalid_checksum,1);});
test("duplicate document and observation identities",()=>{const m=fixture();m.receipts.push({...m.receipts[0]});m.observations.push({...m.observations[0]});const a=audit(m);assert.equal(a.counts.duplicate_document_identity,1);assert.equal(a.counts.duplicate_observation_identity,1);});
for(const [name,change,expected] of [
["unavailable document",m=>m.receipts[0].available=false,"missing_document"],
["missing transcript",m=>m.receipts[0].transcript_available=false,"missing_transcript"],
["ambiguous speaker",m=>m.observations[0].attribution="ambiguous","ambiguous_attribution"],
["missing year",m=>m.observations[0].year=null,"missing_or_inconsistent_year"],
["missing outcome",m=>m.observations[0].outcome_available=false,"missing_outcome"],
["zero probability",m=>m.observations[0].inclusion_probability=0,"positivity_violation"],
["broken meeting lineage",m=>m.observations[0].meeting_id="other","meeting_document_mismatch"],
["wrong text digest",m=>m.observations[0].text_sha256=sha("other"),"text_provenance_mismatch"]]){
 test(name,()=>{const m=fixture();change(m);assert.equal(audit(m).counts[expected],1);});
}
test("incompatible sampling frame inadmissible",()=>{const m=fixture();m.frames[1].selection_design="convenience";assert.equal(audit(m).comparisons[0].status,"inadmissible");});
test("schema fails closed",()=>assert.throws(()=>audit({schema:"wrong"})));
