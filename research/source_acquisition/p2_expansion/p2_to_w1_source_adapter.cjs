'use strict';
/* Private original-byte authenticated P2-to-W1 source-frame adapter.
 * No network, private transcript export, W1 numerical refits or legacy-v1 relabeling.
 */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const ARCHIVE_SHA='55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5';
const P2='un.p2.original-pv-reconciled.v1';
const HEX=/^[a-f0-9]{64}$/;
const PDF_SYMBOL=/^A\/7[1-8]\/PV\.\d+$/;
function require_(ok,message){if(!ok)throw Error(message);}
function digest(b){return crypto.createHash('sha256').update(b).digest('hex');}
function parse(f){return JSON.parse(fs.readFileSync(f,'utf8'));}
function authenticatedFrame(attestation,originalTexts,originalHarvardTar,{cohortIds=null}={}){
  require_(attestation.schema==='un.p2.authenticated-corpus-PV-w1-input.v1',
    'Authentic P2 attestation contract required');
  require_(attestation.source_schema===P2,'Refuse P2 relabelled to legacy source schema');
  require_(attestation.source_hash_basis==='raw_response_bytes'&&
    attestation.source_sha256===ARCHIVE_SHA,'Publisher original-source identity mismatch');
  require_(digest(fs.readFileSync(originalHarvardTar))===ARCHIVE_SHA,
    'Harvard original archive bytes failed SHA-256 check');
  require_(attestation.reserved_2026_meeting_transcripts_accessed===false,
    'Reserved 2026 evaluation source cannot enter P2');
  const pdfs=new Map();
  for(const [symbol,pdf] of Object.entries(attestation.original_source_meetings)){
    require_(PDF_SYMBOL.test(symbol)&&HEX.test(pdf?.sha256),
      'Unapproved original UN meeting symbol/digest');
    const file=fs.realpathSync(pdf.path),data=fs.readFileSync(file);
    require_(data.length===pdf.bytes&&
      data.subarray(0,5).toString('ascii')==='%PDF-'&&
      data.subarray(-4096).includes(Buffer.from('%%EOF')),
      'Original PDF must be complete with byte-level evidence');
    require_(digest(data)===pdf.sha256,'Original UN PDF hash failure');
    pdfs.set(symbol,pdf.sha256);
  }
  require_(pdfs.size===105,'P2 meeting universe changed; do not silently change selection');
  require_(Array.isArray(attestation.observations)&&attestation.observations.length===792,
    'P2 99-country by 8-year inventory must retain all source states');
  const seen=new Set(),rowIds=new Set(),counts={available:0,unverified:0};
  const verified=[];
  for(const o of attestation.observations){
    require_(o&&/^country-[A-Z]{3}-20\d\d$/.test(o.id)&&
      o.id==='country-'+o.country+'-'+o.year,'Country-session source ID changed');
    require_(!seen.has(o.id),'Duplicate candidate source ID');
    seen.add(o.id);
    require_(Number.isSafeInteger(o.year)&&o.year>=2016&&o.year<=2023,
      'Forbidden 2024+ source period');
    require_(o.recorded_actor_kind==='recorded_affiliation'&&
      o.human_person_authenticated===false,'Source affiliation is not an authenticated person');
    const cy=o.country+'|'+o.year;
    require_(!rowIds.has(cy),'Duplicated country-year source');
    rowIds.add(cy);
    require_(o.source_status==='available'||o.source_status==='unverified',
      'Unknown P2 source status');
    counts[o.source_status]++;
    if(o.source_status==='unverified'){
      require_(o.date===null&&o.meeting_id===null&&o.original_pdf_sha256===null&&
        o.harvard_speech_sha256===null&&o.pdf_path===null&&
        typeof o.missing_reason==='string'&&o.missing_reason.length>0,
        'Do not invent source/date/meeting for unverified inventory cell');
      require_(!Object.hasOwn(originalTexts,o.id),
        'An unverified source has unexpected observed transcript text');
      continue;
    }
    require_(/^20\d\d-\d\d-\d\d$/.test(o.date)&&Number(o.date.slice(0,4))===o.year&&
      ['independent_UN_index','official_UN_PV_header'].includes(o.date_basis),
      'Original event date or authority missing');
    require_(PDF_SYMBOL.test(o.meeting_id)&&o.source_family_id===o.meeting_id,
      'Source meeting and original-source family identity changed');
    require_(pdfs.get(o.meeting_id)===o.original_pdf_sha256,
      'Source PDF SHA mismatches independently verified meeting manifest');
    require_(o.pdf_path&&digest(fs.readFileSync(o.pdf_path))===o.original_pdf_sha256,
      'Observed row PDF bytes fail SHA');
    const text=originalTexts[o.id];
    require_(typeof text==='string'&&text.length>=300&&
      digest(Buffer.from(text,'utf8'))===o.harvard_speech_sha256,
      'Original Harvard UTF-8 transcript content failed SHA check');
    require_(o.source_verification==='full_original_verified'&&
      o.seven_shingle_coverage>=.9&&o.deciles>=8&&
      o.opening>=.4&&o.ending>=.4,
      'Full original UN PV speech correspondence not independently supported');
    verified.push(o);
  }
  require_(counts.available===790&&counts.unverified===2&&
    Object.keys(originalTexts).length===790,'Whole original P2 population denominator changed');
  const retained=cohortIds?verified.filter(o=>cohortIds.has(o.id)):verified;
  if(cohortIds)require_(retained.length===cohortIds.size,
    'Requested W1 cohort contains unverified, unknown or duplicate sources');
  const observations=retained.map(o=>({
    id:o.id,split:'development',source_status:'available',exclusion_reasons:[],
    text:originalTexts[o.id],text_sha256:o.harvard_speech_sha256,
    parent_id:null,parent_text_sha256:null,
    meeting_id:o.meeting_id,source_family_id:o.meeting_id,
    date:o.date,country:o.country,affiliation:o.country,
    genre:'general_debate',role:'recorded_affiliation_not_verified_person',
    review_status:'unreviewed',speech_id:null,
    source_url:'https://documents.un.org/api/symbol/access?l=en&s='+
      encodeURIComponent(o.meeting_id)+'&t=pdf',
    start:null,end:null,json_pointer:null,unit:'source_segment',
    p2_original_pdf_sha256:o.original_pdf_sha256,
    p2_full_speech_verified:true,
    p2_date_basis:o.date_basis,
    p2_original_source_hash_basis:'raw_response_bytes',
    p2_verification_method:'original_UN_PV_full_speech_7gram_10decile_v1'
  })).sort((a,b)=>a.id.localeCompare(b.id));
  const selection=digest(JSON.stringify(observations.map(o=>[o.id,o.text_sha256])));
  const frame={schema:'un.source-validation.frame.v1',
    split:'development',source_schema:P2,
    source_engine:'P2_original_UN_full_PV_Harvard_v14_readonly_adapter',
    source_hash_basis:'raw_response_bytes',source_sha256:ARCHIVE_SHA,
    selection_sha256:selection,unit:'source_segment',
    inventory_meetings:pdfs.size,
    original_p2_source_provenance:{
      verified_original_meeting_count:pdfs.size,
      full_candidate_country_year_cells:792,source_verified:790,unverified:2,
      original_archive_sha256:ARCHIVE_SHA,selection_sha256:selection},
    observations};
  return {frame,receipt:{
    schema:'un.p2.to_w1.source_authenticated.v1',
    original_harvard_archive_sha256:ARCHIVE_SHA,
    full_original_PV_files_sha256_verified:pdfs.size,
    candidate_source_cells:792,source_verified_cells:790,unverified_cells:2,
    selected_W1_eligible_observations:observations.length,
    selection_sha256:selection,
    person_identity_authenticated:false,
    legacy_analytic_v1_binding:'WITHHELD',
    original_text_public_export:false,publication_eligible:false,
    reserved_2026_meeting_reads:0}};
}
function main(args){
  function get(k){const i=args.indexOf(k);return i<0?null:args[i+1];}
  require_(['--attestation','--texts','--harvard-tar','--output'].every(k=>get(k)),
    'Required --attestation --texts --harvard-tar --output');
  const evidence=parse(get('--attestation')),texts=parse(get('--texts'));
  let ids=null;
  if(get('--cohort-ids')){
    const declared=parse(get('--cohort-ids')),values=declared.ids??declared.selection;
    require_(Array.isArray(values),'Original selection manifest required');
    ids=new Set(values.map(v=>Array.isArray(v)?v[0]:v));
    require_(ids.size===values.length,'Repeated source selection ID');
  }
  const {frame,receipt}=authenticatedFrame(evidence,texts,get('--harvard-tar'),{cohortIds:ids});
  const out=path.resolve(get('--output'));
  const root=path.resolve(__dirname,'../../..');
  require_(out!==root&&!out.startsWith(root+path.sep),
    'Original source-text frame output cannot enter the public repository');
  fs.writeFileSync(out,JSON.stringify(frame,null,2)+'\n',{flag:'wx',mode:0o600});
  console.log(JSON.stringify(receipt));
}
if(require.main===module){
  try{main(process.argv.slice(2));}
  catch(e){console.error('P2 original source authentication refused: '+
    String(e.message||e).slice(0,250));process.exitCode=2;}
}
module.exports={authenticatedFrame,digest};
