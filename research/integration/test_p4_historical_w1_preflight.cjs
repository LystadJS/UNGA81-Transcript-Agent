'use strict';
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const {auditPrivateP3}=require('./p4_historical_w1_preflight.cjs');
const F=require('../validation_framework/frame.cjs');
const fakeHash=x=>crypto.createHash('sha256').update('FICTION_ONLY:'+x).digest('hex');
const sum=[7,9,6,7,7,7,7,5];
function fixture(){
  const result=[],symbols=new Set();
  // Three invented index gaps at the same years as the private official PV
  // review; no real country identities or meeting text occur in this fixture.
  for(let i=0;i<99;i++){
    const country='X'+String.fromCharCode(65+Math.floor(i/26))+String.fromCharCode(65+i%26);
    const keep=new Set([i%4,(i+1)%4,4+i%4,4+(i+1)%4]);
    if(i<54)keep.add((i+2)%4);
    if(i<73)keep.add(4+(i+2)%4);
    for(let j=0;j<8;j++){
      const year=2016+j,verified=keep.has(j);
      const symbol='A/'+(year-1945)+'/PV.'+(1+i%sum[j]);
      const isUndated=verified&&((i===0&&(year===2016||year===2017))||
        (i===3&&year===2023));
      const state=!verified?'original_PV_not_verified_not_speech_absence':
          isUndated?'source_corroborated_date_unverified':
          'source_and_index_date_corroborated_hash_only';
      const source=verified;
      if(source)symbols.add(symbol);
      result.push({
        id:'gd:'+year+':'+country,country,year,period:j<4?'2016-2019':'2020-2023',
        date:!source||isUndated?null:year+'-09-24',
        source_status:state,
        W1_model_fit_eligible:false,W4_model_fit_eligible:false,
        W1_source_provenance_preflight:source,
        actor_kind:'recorded_affiliation',review_status:source?
          'source_only_no_person_gold':'source_not_verified',
        genre:'general_debate',independently_authenticated_person_id:null,
        verified_speech_id:null,harvard_original_raw_text_rechecked_now:false,
        training_representation_frozen:false,speech_source_role_authenticated:false,
        meeting_id:source?symbol:null,source_family_id:source?'original:'+symbol:null,
        original_source_pdf_sha256:source?fakeHash('pdf:'+symbol):null,
        original_source_full_text_sha256:source?fakeHash('pv_text:'+symbol):null,
        speech_text_sha256:source?fakeHash('harvard:'+country+':'+year):null,
        speech_hash_basis:source?'harvard_v14_utf8_original_txt_file_bytes':null,
        source_url:source?'https://documents.un.org/fiction/'+symbol:null,
        parent_id:null,parent_start:null,parent_end:null
      });
    }
  }
  assert.equal(symbols.size,55);
  return {
    schema:'un.w1.p3.longitudinal-source-inventory.v1',
    split:'private_development_inventory',
    upstream:{P2_source_selection_sha256:'3ebec834635e4d493e8035aeede3321efb951aa22f2f61d81f6ac7a0f65a4c89',
       harvard_v14_original_tar_expected_sha256:'55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5',
       harvard_v14_raw_text_file_bytes_accessible_now:false},
    release_gates:{reserved_37_meetings_opened:0,publication_eligible:false,
       W1_real_model_fit:'NOT_RUN',W4_descriptive_fit:'WITHHELD'},
    observations:result
  };
}
function refuses(mutator,match){
  const v=fixture();
  mutator(v);
  assert.throws(()=>auditPrivateP3(v),match);
}
function run(){
  let passed=0;
  function checkCase(title,handler){handler();passed++;process.stdout.write('PASS '+title+'\n');}
  checkCase('full fake 792 cell source frame and native W1 grouping',()=>{
    const a=auditPrivateP3(fixture());
    assert.equal(a.inventory_cells,792);
    assert.equal(a.source_date_verified,520);
    assert.equal(a.source_date_unresolved,3);
    assert.equal(a.original_source_unverified,269);
    assert.equal(a.original_PV_meeting_groups,55);
    assert.equal(a.meeting_grouping.groups,55);
    assert.equal(a.meeting_grouping.attempted,20);
    assert.equal(a.affiliation_grouping.groups,1);
    assert.equal(a.affiliation_grouping.attempted,0);
    assert.equal(a.affiliation_grouping.status,'skipped');
    assert.equal(a.native_W1_validateFrame_with_empirical_text_executed,false);
    assert.equal(a.W1_model_fits,0);
    assert.equal(a.year_leave_one_out.length,8);
  });
  checkCase('determinism/replay identity for source-only schedules',()=>{
    const x=auditPrivateP3(fixture());
    const y=auditPrivateP3(fixture());
    assert.deepEqual(x,y);
    assert.match(x.deterministic_aggregate_sha256,/^[a-f0-9]{64}$/);
  });
  checkCase('source SHA per official PDF meeting must remain stable',()=>{
    refuses(v=>{const x=v.observations.find(x=>x.meeting_id);x.original_source_pdf_sha256=fakeHash('wrong')},/conflicting original PDF/);
  });
  checkCase('unverified cells cannot gain original sources',()=>{
    refuses(v=>{const x=v.observations.find(x=>x.meeting_id===null);x.original_source_pdf_sha256=fakeHash('wrong')},/not an observed speech or a zero/);
  });
  checkCase('date-unverified cell cannot receive guessed dates',()=>{
    refuses(v=>{const x=v.observations.find(x=>x.source_status==='source_corroborated_date_unverified');x.date=x.year+'-09-24'},/invented date/);
  });
  checkCase('explicit unverified cells must remain in total population',()=>{
    refuses(v=>{v.observations=v.observations.filter(x=>x.source_status!=='original_PV_not_verified_not_speech_absence')},/792-cell/);
  });
  checkCase('duplicate country-year and forged actor identity refused',()=>{
    refuses(v=>{v.observations[0]=structuredClone(v.observations[1])},/Duplicate country-year/);
    refuses(v=>{v.observations[0].verified_speech_id='fake-human-speech'},/human gold/);
  });
  checkCase('frozen W1 and holdout release gates cannot change',()=>{
    refuses(v=>{v.release_gates.reserved_37_meetings_opened=1},/Frozen scientific/);
    refuses(v=>{v.observations[0].W1_model_fit_eligible=true},/prematurely promoted/);
  });
  checkCase('unsupported raw-Harvard status must not be forged',()=>{
    refuses(v=>{v.observations[0].harvard_original_raw_text_rechecked_now=true},/prematurely promoted/);
  });
  checkCase('unrecognized source schema refused by native W1 fit input',()=>{
    assert.throws(()=>F.validateFrame({...fixture(),schema:'un.source-validation.frame.v1',
      split:'development',source_schema:'un.historical-gd-pv.v1',
      source_sha256:fakeHash('source'),source_hash_basis:'canonical_source_text',
      source_engine:'historical-PV-metadata-only'}),/Unsupported source schema/);
  });
  process.stdout.write(JSON.stringify({suite:'p4-historical-source-preflight-synthetic',
    tests:passed,failed:0,fixture_country_year_slots:792,
    meeting_groups:55,affiliation_source_transitive_groups:1,
    raw_original_harvard_speeches_read:0,frozen_heldout_opened:0})+'\n');
}
if(require.main===module){try{run()}catch(err){process.stderr.write(err.stack+'\n');process.exitCode=1;}}
module.exports={fixture};
