'use strict';

// Offline, metadata-only audit. No models, original retrieval, or publication.
const fs = require('node:fs');
const crypto = require('node:crypto');
const VERSION = 'un.historical-source-audit.v1';
const CONTRACT_VERSION = '1.1.0';
const HEX = /^[a-f0-9]{64}$/;
const SOURCE_BASES = new Set(['raw_response_bytes', 'source_text_file_bytes', 'canonical_source_text', 'utf8_response_text', 'synthetic']);
const TEXT_BASES = new Set(['utf8_canonical_text', 'source_text_file_bytes', 'synthetic']);
const MISSING = new Set(['unverified', 'unavailable', 'missing_transcript', 'not_sampled', 'structurally_not_at_risk']);
const SENSITIVE_KEYS = new Set(['text', 'raw_text', 'quote', 'passage', 'original_bytes', 'canonical_text', 'vector', 'embedding', 'pdf_path', 'private_path', 'speaker_name']);
const DIMENSIONS = ['meeting_design', 'genre', 'language', 'translation_modality', 'roster_definition', 'selection_design', 'sampling_unit', 'frame_unit'];
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const str = v => typeof v === 'string' && v.trim().length > 0;
const hash = v => typeof v === 'string' && HEX.test(v);
const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const ensure = (condition, reason) => { if (!condition) throw Error(reason); };

function rejectSensitiveFields(value) {
  if (Array.isArray(value)) return value.forEach(rejectSensitiveFields);
  if (!object(value)) return;
  for (const [key, item] of Object.entries(value)) {
    ensure(!SENSITIVE_KEYS.has(key), 'Source-bearing field forbidden in audit manifest: ' + key);
    rejectSensitiveFields(item);
  }
}

function validateManifest(m) {
  ensure(object(m) && m.schema === VERSION && m.contract_version === CONTRACT_VERSION,
    'Unsupported historical audit schema/version (requires v1, 1.1.0)');
  ensure(['synthetic', 'private_development'].includes(m.fixture_kind), 'Missing fixture_kind');
  ensure(Array.isArray(m.frames) && m.frames.length > 0 &&
    Array.isArray(m.receipts) && Array.isArray(m.observations), 'Malformed source manifest');
  ensure(m.publication_eligible === false, 'Publication lock must be false');
  rejectSensitiveFields(m);
}

function readManifest(file) {
  const m = JSON.parse(fs.readFileSync(file, 'utf8'));
  validateManifest(m);
  return m;
}

function audit(m, { originals = null, canonicalTexts = null } = {}) {
  validateManifest(m);
  const detailed = m.fixture_kind === 'synthetic';
  const problems = [], counts = {}, frameById = new Map(), receiptById = new Map();
  const receiptProblems = new Map(), observationProblems = new Map();
  const add = (code, target, id) => {
    counts[code] = (counts[code] || 0) + 1;
    if (detailed) problems.push({ code, target, id });
  };
  const flagReceipt = (id, code) => {
    if (!receiptProblems.has(id)) receiptProblems.set(id, new Set());
    receiptProblems.get(id).add(code);
    add(code, 'receipt', id);
  };
  const flagObservation = (id, code) => {
    if (!observationProblems.has(id)) observationProblems.set(id, new Set());
    observationProblems.get(id).add(code);
    add(code, 'observation', id);
  };

  for (const f of m.frames) {
    ensure(object(f), 'Malformed source frame');
    ensure(str(f.id) && Number.isInteger(f.start_year) && Number.isInteger(f.end_year) &&
      f.start_year >= 2008 && f.end_year <= 2023 && f.start_year <= f.end_year,
      'Invalid historical source-frame identity/years');
    ensure(!frameById.has(f.id), 'Duplicate source frame: ' + f.id);
    for (const k of DIMENSIONS) ensure(str(f[k]), 'Missing source-frame design: ' + k);
    ensure(str(f.source_schema) && SOURCE_BASES.has(f.source_hash_basis) &&
      hash(f.source_sha256) && hash(f.selection_sha256), 'Incomplete original frame provenance');
    if (m.fixture_kind !== 'synthetic') ensure(f.source_hash_basis !== 'synthetic', 'Synthetic source basis in private frame');
    frameById.set(f.id, f);
  }


  const sourceDigestOwners = new Map();
  let checkedBytes = 0, checkedText = 0;
  const getSupplied = (source, id) => source instanceof Map ? source.get(id) : source && Object.hasOwn(source, id) ? source[id] : undefined;
  for (const r of m.receipts) {
    ensure(object(r) && str(r.document_id), 'Invalid original document identity');
    if (receiptById.has(r.document_id)) flagReceipt(r.document_id, 'duplicate_document_identity');
    else receiptById.set(r.document_id, r);
    if (!str(r.meeting_id) || !Number.isInteger(r.year) || r.year < 2008 || r.year > 2023 ||
      !str(r.source_family_id)) flagReceipt(r.document_id, 'invalid_document_lineage');
    if (r.available !== true && r.available !== false && r.available !== null) flagReceipt(r.document_id, 'unknown_document_status');
    if (![true, false, null].includes(r.transcript_available)) flagReceipt(r.document_id, 'unknown_transcript_status');
    if (r.available === true) {
      if (!hash(r.source_sha256)) flagReceipt(r.document_id, 'invalid_checksum');
      if (!hash(r.text_sha256)) flagReceipt(r.document_id, 'invalid_text_checksum');
      if (!SOURCE_BASES.has(r.source_hash_basis) || !TEXT_BASES.has(r.text_hash_basis))
        flagReceipt(r.document_id, 'missing_hash_basis');
      if (!['full_original_verified', 'provisional', 'synthetic'].includes(r.source_verification))
        flagReceipt(r.document_id, 'missing_verification_basis');
      if ((m.fixture_kind === 'synthetic' && r.source_verification !== 'synthetic') ||
          (m.fixture_kind !== 'synthetic' && r.source_verification !== 'full_original_verified'))
        flagReceipt(r.document_id, 'unaccepted_source_verification');
      if (hash(r.source_sha256)) {
        const prev = sourceDigestOwners.get(r.source_sha256);
        if (prev && prev !== r.document_id &&
            (!str(r.duplicate_group) || r.duplicate_group !== receiptById.get(prev)?.duplicate_group)) {
          flagReceipt(prev, 'duplicate_document_content_unresolved');
          flagReceipt(r.document_id, 'duplicate_document_content_unresolved');
        }
        sourceDigestOwners.set(r.source_sha256, r.document_id);
      }
    }
    const bytes = getSupplied(originals, r.document_id);
    if (bytes !== undefined) {
      ensure(Buffer.isBuffer(bytes), 'Original bytes must be supplied as Buffer, never decoded strings');
      checkedBytes++;
      if (!hash(r.source_sha256) || sha(bytes) !== r.source_sha256) flagReceipt(r.document_id, 'checksum_mismatch');
    }
    const text = getSupplied(canonicalTexts, r.document_id);
    if (text !== undefined) {
      ensure(typeof text === 'string' || Buffer.isBuffer(text), 'Canonical text must be a string or Buffer');
      checkedText++;
      if (!hash(r.text_sha256) || sha(Buffer.isBuffer(text) ? text : Buffer.from(text, 'utf8')) !== r.text_sha256)
        flagReceipt(r.document_id, 'text_checksum_mismatch');
    }
  }

  const seenIds = new Set(), speechAttributions = new Map(), summaries = new Map(), rows = [];
  for (const f of m.frames) summaries.set(f.id, {frame_id:f.id, years:{}, total:0, available:0, eligible_metadata:0,
    excluded:0, unverified:0, unavailable:0, missing_transcript:0, not_sampled:0, structurally_not_at_risk:0,
    missing_outcome:0, ambiguous_attribution:0, positive_sampling_unit:0, unknown_sampling:0,
    observed_genre:{},observed_language:{},observed_translation:{},unique_meetings:0,
    unique_countries:0,speech_length_range:null});
  const distinctCountries = new Map(), distinctMeetings = new Map();
  for (const f of m.frames) {distinctCountries.set(f.id,new Set());distinctMeetings.set(f.id,new Set());}
  for (const o of m.observations) {
    ensure(object(o) && str(o.id), 'Invalid observation identity');
    const flag = code => flagObservation(o.id, code);
    if (seenIds.has(o.id)) flag('duplicate_observation_identity');
    seenIds.add(o.id);
    const f = frameById.get(o.frame_id), r = receiptById.get(o.document_id);
    if (!f) flag('unknown_frame');
    if (!Number.isInteger(o.year) || o.year < 2008 || o.year > 2023 ||
      (f && (o.year < f.start_year || o.year > f.end_year))) flag('missing_or_inconsistent_year');
    if (o.event_date !== null && o.event_date !== undefined) {
      const d = new Date(o.event_date + 'T00:00:00Z');
      if (typeof o.event_date !== 'string' || !/^\d{4}-\d\d-\d\d$/.test(o.event_date) ||
        Number.isNaN(d.getTime()) || d.toISOString().slice(0,10) !== o.event_date ||
        Number(o.event_date.slice(0,4)) !== o.year) flag('invalid_event_date');
    }
    if (!['available', ...MISSING].includes(o.source_status)) flag('unknown_source_status');
    const atRisk = o.source_status !== 'structurally_not_at_risk';
    if (o.source_status !== 'available' && !str(o.missing_reason)) flag('missingness_reason_absent');
    if (o.source_status === 'available' && o.missing_reason != null) flag('available_with_missing_reason');
    if (o.source_status === 'available') {
      if (!str(o.event_date)) flag('missing_event_date');
      if (!r || r.available !== true) flag('missing_document');
      if (r && r.transcript_available !== true) flag('missing_transcript');
      if (!str(o.meeting_id) || !str(o.speech_id) || !str(o.country) || !str(o.source_family_id))
        flag('incomplete_lineage');
      if (!r || o.meeting_id !== r.meeting_id || o.source_family_id !== r.source_family_id)
        flag('meeting_document_mismatch');
      if (r && o.year !== r.year) flag('document_year_mismatch');
      if (!r || !hash(o.text_sha256) || o.text_sha256 !== r.text_sha256)
        flag('text_provenance_mismatch');
      if (!r || receiptProblems.has(o.document_id)) flag('document_receipt_invalid');
      if (r && f && r.source_hash_basis !== f.source_hash_basis) flag('original_hash_basis_mismatch');
      if (o.actor_kind !== 'recorded_affiliation' || o.attribution !== 'verified_recorded_affiliation' ||
        !str(o.attribution_receipt_id)) flag('ambiguous_attribution');
      if (o.outcome_status !== 'observed') flag('missing_outcome');
      if (!Number.isSafeInteger(o.speech_length) || o.speech_length <= 0)
        flag('speech_length_unknown');
      for (const dim of ['genre','language','translation_modality'])
        if (!str(o[dim])) flag('missing_observation_' + dim);
      if (str(o.speech_id) && str(o.meeting_id)) {
        const key = o.meeting_id + '\0' + o.speech_id;
        const prior = speechAttributions.get(key);
        if (prior && (prior.country !== o.country || prior.document_id !== o.document_id)) {
          flag('speech_identity_collision');
          flagObservation(prior.id, 'speech_identity_collision');
        } else if (!prior) speechAttributions.set(key, o);
      }
    }
    if (atRisk) {
      if (o.inclusion_probability == null) flag('sampling_probability_unknown');
      else if (typeof o.inclusion_probability !== 'number' || !Number.isFinite(o.inclusion_probability) ||
        o.inclusion_probability <= 0 || o.inclusion_probability > 1) flag('positivity_violation');
      if (o.inclusion_probability != null && f && o.probability_unit !== f.sampling_unit)
        flag('sampling_unit_mismatch');
    }
    const s = summaries.get(o.frame_id);
    if (s) {
      s.total++;
      s.years[o.year == null ? 'unknown' : String(o.year)] ||= {total:0, available:0, missing:0};
      s.years[o.year == null ? 'unknown' : String(o.year)].total++;
      if (o.source_status === 'available') {
        s.available++;s.years[o.year == null ? 'unknown' : String(o.year)].available++;
        if (str(o.country)) distinctCountries.get(o.frame_id).add(o.country);
        if (str(o.meeting_id)) distinctMeetings.get(o.frame_id).add(o.meeting_id);
        for (const [column,dest] of [['genre','observed_genre'],['language','observed_language'],['translation_modality','observed_translation']])
          if(str(o[column]))s[dest][o[column]]=(s[dest][o[column]]||0)+1;
        if(Number.isSafeInteger(o.speech_length)&&o.speech_length>0){
          s.speech_length_range=s.speech_length_range ?
            [Math.min(s.speech_length_range[0],o.speech_length),Math.max(s.speech_length_range[1],o.speech_length)] :
            [o.speech_length,o.speech_length];
        }
      }
      else {if (s[o.source_status] !== undefined) s[o.source_status]++;s.years[o.year == null ? 'unknown':String(o.year)].missing++;}
      if (o.outcome_status === 'missing') s.missing_outcome++;
      if (o.attribution !== 'verified_recorded_affiliation') s.ambiguous_attribution++;
      if (o.inclusion_probability == null && atRisk) s.unknown_sampling++;
      if (atRisk && f && Number.isFinite(o.inclusion_probability) && o.inclusion_probability > 0 && o.inclusion_probability <= 1 && o.probability_unit === f.sampling_unit)
        s.positive_sampling_unit++;
    }
    rows.push({id:o.id, frame_id:o.frame_id, year:o.year, source_status:o.source_status, eligible_metadata:false,
      exclusions:[], source_verified:r?.source_verification ?? 'unverified', original_bytes_checked:getSupplied(originals,o.document_id)!==undefined});
  }
  // A later collision must also invalidate an earlier row. Finalize only after all records.
  for (const row of rows) {
    row.exclusions = [...(observationProblems.get(row.id) || [])];
    row.eligible_metadata = row.source_status === 'available' && row.exclusions.length === 0;
    const s = summaries.get(row.frame_id);
    if (s) {if (row.eligible_metadata)s.eligible_metadata++;else s.excluded++;}
  }
  for(const f of m.frames){
    const s=summaries.get(f.id);
    s.unique_countries=distinctCountries.get(f.id).size;
    s.unique_meetings=distinctMeetings.get(f.id).size;
  }
  const totalEligible = rows.filter(r=>r.eligible_metadata).length;
  const comparisons=[];
  for (let i=0;i<m.frames.length;i++) for(let j=i+1;j<m.frames.length;j++) {
    const a=m.frames[i], b=m.frames[j], aa=m.observations.filter(o=>o.frame_id===a.id),
      bb=m.observations.filter(o=>o.frame_id===b.id);
    const mismatched = DIMENSIONS.filter(d=>a[d]!==b[d]);
    if (a.source_schema !== b.source_schema) mismatched.push('source_schema');
    if (a.source_hash_basis !== b.source_hash_basis) mismatched.push('source_hash_basis');
    const severe = mismatched.filter(d=>['source_schema','source_hash_basis','selection_design','sampling_unit','frame_unit','meeting_design','genre'].includes(d));
    const matched = new Set(aa.map(o=>o.document_id));
    const shared = [...new Set(bb.filter(o=>matched.has(o.document_id)).map(o=>o.document_id))].length;
    const lens = v => v.filter(o=>o.source_status==='available' && Number.isFinite(o.speech_length)).map(o=>o.speech_length);
    const extent = v => v.length ? [Math.min(...v), Math.max(...v)] : null;
    const status = severe.length ? 'inadmissible' : 'uncertain';
    comparisons.push({frames:[a.id,b.id],status,scope:'metadata-only',reason:severe.length ?
      'Incompatible or unauthenticated sampling/source designs' :
      'Separate source populations; original-source, roster, translation and selection bridges not independently validated',
      mismatched_dimensions:mismatched,shared_document_id_count:shared,
      source_populations_independent:true,
      comparison_population:[aa.length,bb.length],
      eligible_metadata:[summaries.get(a.id).eligible_metadata,summaries.get(b.id).eligible_metadata],
      speech_length_ranges:[extent(lens(aa)),extent(lens(bb))],
      year_ranges:[[a.start_year,a.end_year],[b.start_year,b.end_year]],
      observed_language_sets:[[...new Set(aa.map(o=>o.language).filter(str))].sort(),
        [...new Set(bb.map(o=>o.language).filter(str))].sort()],
      observed_translation_sets:[[...new Set(aa.map(o=>o.translation_modality).filter(str))].sort(),
        [...new Set(bb.map(o=>o.translation_modality).filter(str))].sort()]});
  }
  const withinFrameComparisons = [];
  for (const f of m.frames) {
    const yy = Object.keys(summaries.get(f.id).years).filter(y=>/^\d{4}$/.test(y)).sort();
    for(let i=0;i<yy.length;i++)for(let j=i+1;j<yy.length;j++){
      const first=m.observations.filter(o=>o.frame_id===f.id && String(o.year)===yy[i]);
      const second=m.observations.filter(o=>o.frame_id===f.id && String(o.year)===yy[j]);
      const accepted = arr=>arr.some(o=>rows.some(r=>r.id===o.id && r.eligible_metadata));
      const same = key=>[...new Set(first.filter(o=>o.source_status==='available').map(o=>o[key]))].sort().join('|')===
        [...new Set(second.filter(o=>o.source_status==='available').map(o=>o[key]))].sort().join('|');
      const actors=arr=>new Set(arr.filter(o=>o.source_status==='available' && str(o.country)).map(o=>o.country));
      const rosterA=actors(first),rosterB=actors(second);
      const matched=[...rosterA].filter(c=>rosterB.has(c)).length;
      const rosterStable=matched===rosterA.size && matched===rosterB.size && matched>0;
      const ok=accepted(first)&&accepted(second)&&same('genre')&&same('translation_modality')&&same('language')&&rosterStable;
      withinFrameComparisons.push({frame_id:f.id,years:[Number(yy[i]),Number(yy[j])],
        status:ok?'supported':'uncertain',scope:'within-frame descriptive metadata only',
        recorded_affiliations:[rosterA.size,rosterB.size],matched_recorded_affiliations:matched,
        roster_composition_changed:!rosterStable,
        eligible_metadata:[first.filter(o=>rows.some(r=>r.id===o.id && r.eligible_metadata)).length,
          second.filter(o=>rows.some(r=>r.id===o.id && r.eligible_metadata)).length],
        reason:ok?'Both years include comparable eligible metadata and matched affiliations under one declared frame; no inference':'Coverage, roster composition, language, genre or translation may differ'});
    }
  }
  const privateSourceValidation = checkedBytes===0 ? 'NOT RUN' :
    checkedBytes===m.receipts.filter(r=>r.available===true).length && !counts.checksum_mismatch ? 'EXECUTED_FOR_AVAILABLE_RECEIPTS' : 'PARTIAL_OR_FAILED';
  const textValidation = checkedText===0 ? 'NOT RUN' :
    checkedText===m.receipts.filter(r=>r.available===true).length && !counts.text_checksum_mismatch ? 'EXECUTED_FOR_AVAILABLE_RECEIPTS' : 'PARTIAL_OR_FAILED';
  return {schema:VERSION,contract_version:CONTRACT_VERSION,evaluation_role:'engineering_only',
    publication_eligible:false,substantive_fit_performed:false,inference_eligible:false,
    private_source_validation:privateSourceValidation,text_validation:textValidation,
    sampling_inference:'NOT IDENTIFIED: sampling unit probability does not establish speech response or selection ignorability',
    totals:{observations:rows.length,available:rows.filter(r=>r.source_status==='available').length,
      eligible_metadata:totalEligible,excluded:rows.length-totalEligible},
    counts,frames:[...summaries.values()],comparisons,within_frame_comparisons:withinFrameComparisons,
    ...(detailed?{problems,eligibility:rows}:{problems:[],eligibility:[],details_withheld:'Private observation IDs and source-bearing row diagnostics withheld'}),
    limitations:['Metadata eligibility is conditional and does not authenticate private originals.',
      'Different source frames are separate until independently source- and design-validated.',
      'Recorded affiliation is not a verified human identity or diplomatic stance.',
      'First-stage meeting inclusion is not speech-level response probability.',
      'Missing observations are not zero outcomes; annual observations are temporally dependent.',
      'No latent model, estimation, inference or publication is authorized.']};
}

function auditInventory(sidecar) {
  // Validate the accepted coordinator-owned v1 sidecar, without redefining its schema.
  const upstream = require('../../docs/parallel-work/source-inventory-v1.cjs');
  const receipt = upstream.validateInventory(sidecar);
  ensure(sidecar.legacy_v1_binding.mode === 'withheld',
    'A verified legacy v1 binding requires separately supplied coordinator evidence');
  const byYear = {};
  for(const r of sidecar.observations){
    if(r.year < 2008 || r.year > 2023) throw Error('Historical audit limited to 2008–2023');
    const key = String(r.year);
    byYear[key] ||= {total:0,available:0,unverified:0,other_missing:0};
    byYear[key].total++;
    if(r.source_status==='available')byYear[key].available++;
    else if(r.source_status==='unverified')byYear[key].unverified++;
    else byYear[key].other_missing++;
  }
  const buckets = [{id:'historical_2008_2015',start:2008,end:2015},
    {id:'cohort_2016_2023',start:2016,end:2023}].map(f=>{
    const years = Object.entries(byYear).filter(([y])=>Number(y)>=f.start&&Number(y)<=f.end);
    return {id:f.id,start_year:f.start,end_year:f.end,
      total:years.reduce((n,[,x])=>n+x.total,0),
      available:years.reduce((n,[,x])=>n+x.available,0),
      unverified:years.reduce((n,[,x])=>n+x.unverified,0),
      other_missing:years.reduce((n,[,x])=>n+x.other_missing,0)};
  });
  return {schema:VERSION,contract_version:CONTRACT_VERSION,source_schema:sidecar.schema,
    source_manifest_schema:sidecar.upstream.source_schema,source_hash_basis:sidecar.upstream.source_hash_basis,
    original_source_sha256:sidecar.upstream.source_sha256,original_selection_sha256:sidecar.upstream.selection_sha256,
    original_inventory_sha256:sidecar.inventory_sha256,
    validation:receipt.status,private_source_validation:'NOT RUN',speech_lineage_validation:'NOT RUN',
    first_stage_positivity:'NOT RUN',sampling_inference:'NOT IDENTIFIED',
    periods:buckets,year_coverage:byYear,comparisons:[{frames:buckets.map(x=>x.id),
      status:'uncertain',reason:'No independently verified cross-era source-frame and sampling-design bridge'}],
    legacy_v1_binding:'withheld',source_authentication:'INHERITED_UPSTREAM_NOT_REPLAYED',
    publication_eligible:false,inference_eligible:false,evaluation_role:'engineering_only'};
}

module.exports = {VERSION,CONTRACT_VERSION,readManifest,validateManifest,audit,auditInventory,sha};
if (require.main === module) {
  const input = readManifest(process.argv[2]);
  process.stdout.write(JSON.stringify(audit(input),null,2)+'\n');
}
