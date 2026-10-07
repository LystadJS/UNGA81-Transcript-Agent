#!/usr/bin/env node
'use strict';
/** Build a local review packet by re-deriving the saved development corpus. No fetch API. */
const fs = require('node:fs');
const path = require('node:path');
const C = require('../research/corpus/contract.cjs');
const B = require('../research/corpus/boundary-review.js');
const CLI = require('./passage_corpus.cjs');
const assets = path.join(__dirname, '../research/corpus/review-assets');
const read = file => JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(fs.readFileSync(file)).replace(/^\uFEFF/, ''));
const write = (file, value) => fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n', {flag: 'wx', mode: 0o600});
const fields = (r, keys) => Object.fromEntries(keys.map(k => [k, r[k]]));
const safeJSON = x => JSON.stringify(x).replace(/[<>&\u2028\u2029]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
function model(corpus) {
  const c = C.load(corpus); // Rebuild every source record and exact partition from original response bytes.
  const coverage = new Map(c.coverage.map(m => [m.meeting_id, m]));
  const sources = new Map(c.source_bundle.sources.map(s => [s.meeting_id, s]));
  const meetings = c.frame.meetings.filter(m => m.split === 'development').map((m, i) => {
    const cv = coverage.get(m.meeting_id), src = sources.get(m.meeting_id);
    C.assert(cv && src, 'Missing development acquisition account');
    return {...fields(m, ['meeting_id', 'date', 'title', 'genre', 'body', 'source_url', 'split']),
      status: cv.status, error: cv.error, raw_sha256: cv.raw_sha256,
      raw_file: src.status === 'downloaded' ? 'sources/m' + String(i + 1).padStart(3, '0') + '.json' : null,
      source_segments: cv.source_segments, timestamps_flagged: cv.timestamps_flagged || false};
  });
  const order = new Map(meetings.map((m, i) => [m.meeting_id, i]));
  const groups = new Map();
  for (const p of c.passages) {
    if (!groups.has(p.parent_id)) groups.set(p.parent_id, []);
    groups.get(p.parent_id).push(fields(p, ['id', 'parent_start', 'parent_end', 'tokens', 'text_sha256', 'exclusions', 'speech_exclusions']));
  }
  const records = c.parents.map(r => ({...fields(r, ['id', 'meeting_id', 'date', 'split', 'genre', 'body', 'source_url',
    'json_pointer', 'raw_sha256', 'text', 'text_sha256', 'sentences', 'speaker_metadata', 'affiliation_raw', 'country',
    'region', 'language', 'timestamps_flagged']), source_index: Number(r.json_pointer.split('/').at(-1)),
    partitions: groups.get(r.id) || [], initial_choice: r.review_choice || null}))
    .sort((a, b) => order.get(a.meeting_id) - order.get(b.meeting_id) || a.source_index - b.source_index);
  const out = C.seal({schema: 'un.boundary-packet.v1', engine: B.VERSION,
    corpus_engine: C.VERSION, corpus_sha256: c.sha256, source_bundle_sha256: c.source_bundle.sha256,
    frame_sha256: c.frame.sha256, plan_sha256: c.frame.plan.sha256,
    development_dates: c.frame.plan.development_dates, meetings, records,
    counts: {meetings: meetings.length, cached_sources: meetings.filter(m => m.raw_file).length,
      source_segments: records.length, passages: c.passages.length,
      existing_confirmed: records.filter(r => r.initial_choice?.confirmed).length,
      source_segment_eligible: c.counts.source_segment_eligible,
      unavailable_meetings: meetings.filter(m => m.status !== 'collected').length},
    holdout: {meetings: c.counts.reserved_meetings, dates: c.frame.plan.holdout_dates,
      transcripts_opened: 0, state: 'reserved_not_downloaded',
      scope: 'No held-out IDs, titles, links or text are placed in this packet.'},
    offset_unit: 'Unicode code points; zero-based; end-exclusive',
    review_scope: 'Whole source-segment classification and speech identity/extent only. Internal boundary editing, correction and country adjudication remain separate.'});
  return {corpus: c, packet: out};
}
function render(packet) {
  const core = fs.readFileSync(path.join(__dirname, '../research/corpus/boundary-review.js'), 'utf8');
  const ui = fs.readFileSync(path.join(assets, 'review.js'), 'utf8');
  const css = fs.readFileSync(path.join(assets, 'review.css'), 'utf8');
  const b64sha = s => Buffer.from(C.sha(s), 'hex').toString('base64');
  const csp = "default-src 'none'; script-src 'sha256-" + b64sha(core) + "' 'sha256-" + b64sha(ui) +
    "'; style-src 'sha256-" + b64sha(css) + "'; connect-src 'none'; img-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
  const html = fs.readFileSync(path.join(assets, 'review.html'), 'utf8');
  const replacements = {CSP: csp, CSS: css, PACKET: safeJSON(packet), CORE: core, UI: ui};
  return html.replace(/\{\{(CSP|CSS|PACKET|CORE|UI)\}\}/g, (_, key) => replacements[key]);
}
async function build(input, output) {
  C.assert(typeof output === 'string' && !fs.existsSync(output), 'Use a NEW output directory; no review packet is overwritten.');
  const {corpus, packet} = model(input);
  await B.validatePacket(packet);
  fs.mkdirSync(output, {mode: 0o700});
  fs.mkdirSync(path.join(output, 'sources'), {mode: 0o700});
  const sources = new Map(corpus.source_bundle.sources.map(s => [s.meeting_id, s]));
  for (const m of packet.meetings) {
    if (!m.raw_file) continue;
    const raw = Buffer.from(sources.get(m.meeting_id).raw_base64, 'base64');
    C.assert(C.sha(raw) === m.raw_sha256, 'Cached raw source digest mismatch');
    fs.writeFileSync(path.join(output, m.raw_file), raw, {flag: 'wx', mode: 0o600});
  }
  fs.writeFileSync(path.join(output, 'index.html'), render(packet), {flag: 'wx', mode: 0o600});
  write(path.join(output, 'review-template.json'), B.seed(packet));
  CLI.csv(path.join(output, 'review-queue.csv'), packet.records.map((r, i) => ({queue: i + 1,
    ...r, partitions: r.partitions.length, confirmed: r.initial_choice?.confirmed || false})),
    ['queue', 'id', 'date', 'meeting_id', 'affiliation_raw', 'country', 'language', 'partitions', 'confirmed', 'text_sha256', 'raw_sha256', 'json_pointer', 'source_url']);
  const receipt = {schema: 'un.boundary-packet-receipt.v1', engine: B.VERSION, status: 'PASS',
    packet_sha256: packet.sha256, corpus_sha256: packet.corpus_sha256,
    source_bundle_sha256: packet.source_bundle_sha256, frame_sha256: packet.frame_sha256,
    counts: packet.counts, holdout: packet.holdout,
    original_source_rederivation: true, all_source_segments_included: true,
    all_partition_code_points_accounted: true, decisions_generated: 0,
    new_source_requests: 0, link_validation: 'Exact frozen development identity and cached-byte verification; no HTTP availability probe.',
    owner_pilot_modified: false, source_text_modified: false,
    implementation_sha256: Object.fromEntries(['research/corpus/boundary-review.js', 'tools/boundary_packet.cjs',
      ...['review.html', 'review.css', 'review.js'].map(n => 'research/corpus/review-assets/' + n)]
      .map(n => [n, C.sha(fs.readFileSync(path.join(__dirname, '..', n)))]))};
  write(path.join(output, 'manifest.json'), receipt);
  fs.writeFileSync(path.join(output, 'START_HERE.txt'), instructions(packet), {flag: 'wx', mode: 0o600});
  const names = ['index.html', 'review-template.json', 'review-queue.csv', 'manifest.json', 'START_HERE.txt',
    ...packet.meetings.flatMap(m => m.raw_file ? [m.raw_file] : [])].sort();
  fs.writeFileSync(path.join(output, 'SHA256SUMS.txt'), names.map(n => C.sha(fs.readFileSync(path.join(output, n))) + '  ' + n).join('\n') + '\n', {flag: 'wx'});
  return receipt;
}
function instructions(p) {
  return `DEVELOPMENT BOUNDARY REVIEW\n\nExtract the ZIP first. Open index.html in a current desktop browser. No installation, server or internet connection is required for the packet.\n\n1. Enter your reviewer name. Choose a meeting, then read each original segment and its previous/next context.\n2. Choose the source type and observed speech extent. Use a speech ID only when the source supports it. The ID button fills an ID but does not confirm a decision.\n3. Add notes for incomplete, uncertain, mixed-speaker or transcription problems. Internal split/editing and country correction are not performed here.\n4. Select Confirm and next. Your click, name and time are recorded. Nothing is pre-confirmed.\n5. Select Save review JSON before closing. The browser cache is only a convenience, not a backup. Resume by importing that saved JSON. Upload the JSON to the project when ready; partial reviews are accepted.\n\nCOVERAGE\n${p.counts.source_segments} source-segment decisions, ${p.counts.passages} exact technical passage windows, ${p.counts.meetings} development meetings (${p.counts.cached_sources} cached original responses). The unavailable meeting remains visible but has no invented review task. Every stored segment, including short/procedural/uncertain text, remains in the queue.\n\nThe ${p.holdout.meetings} held-out meetings remain unopened. This packet contains no held-out text, meeting links or meeting titles. All source links refer only to development meetings. Clicking an original UN source opens that development page; timestamps are not represented as verified audio boundaries.\n\nWHAT YOU ARE REVIEWING\nA source segment is not necessarily a complete speech. Balanced token windows are technical partitions, not reviewed topic boundaries. A substantive speech may span several segments; assign the same explicit ID only when meeting/speaker/affiliation metadata are consistent and your review supports that identity. Source wording, country metadata and raw responses are read-only. Existing owner pilot decisions are outside this packet.\n\nType guide:\n- Substantive speech: policy content from the recorded intervention.\n- Mixed speech/procedure: substantive and procedural material; not permission to treat multiple speakers as one.\n- Right of reply: identify from context, not keywords alone.\n- Procedure: introductions, floor management, voting mechanics or administrative remarks.\n- Speech fragment: only a partial intervention is observed.\n- Suspected transcription issue: record the problem; do not silently correct the text.\n- Uncertain / internal boundary problem: retain the uncertainty and describe the split needed.\n\nExtent guide:\nComplete / near-complete needs an explicit speech ID. Near-complete needs a coverage note. Fragment / unknown remains outside the reviewed complete-speech population. Confirmation records a review decision; it does not necessarily make a passage analytically eligible.\n\nFOR REPRODUCTION\nFrom the source repository, using the existing checkpoint:\n  node tools/boundary_packet.cjs build path/to/work/build/corpus.json NEW_packet_directory\nCheck returned choices without changing sources:\n  node tools/boundary_packet.cjs validate path/to/work/build/corpus.json saved-review.json\nThen rebuild into a NEW output directory through tools/passage_corpus.cjs with the original frame, source bundle and returned review. No held-out collection is needed.\n\nManifest: ${p.sha256}\nOriginal corpus: ${p.corpus_sha256}\nSource bundle: ${p.source_bundle_sha256}\n`;
}
async function validate(corpus, review) {
  const {corpus: original, packet} = model(corpus);
  const normalized = B.validateReview(packet, review);
  const updated = C.build(original.frame, original.source_bundle, normalized);
  C.assert(updated.parents.length === original.parents.length && updated.passages.length === original.passages.length, 'Review changed source coverage');
  C.assert(C.stable(updated.source_bundle) === C.stable(original.source_bundle), 'Review altered source bytes');
  return {status: 'PASS', confirmed: normalized.choices.filter(c => c.confirmed).length,
    pending: normalized.choices.filter(c => !c.confirmed).length, total: normalized.choices.length,
    reviewed_speech_eligible: updated.counts.reviewed_speech_eligible,
    heldout_opened: false, original_source_bundle_sha256: original.source_bundle.sha256,
    reviewed_corpus_sha256: updated.sha256};
}
if (require.main === module) (async () => {
  const [command, input, output] = process.argv.slice(2);
  C.assert(['build', 'validate'].includes(command) && input && output,
    'Usage: node tools/boundary_packet.cjs build CORPUS NEW_DIRECTORY | validate CORPUS REVIEW_JSON');
  const result = command === 'build' ? await build(read(input), output) : await validate(read(input), read(output));
  console.log(JSON.stringify(result, null, 2));
})().catch(e => { console.error(e.message); process.exitCode = 1; });
module.exports = {model, build, render, validate, read, safeJSON};
