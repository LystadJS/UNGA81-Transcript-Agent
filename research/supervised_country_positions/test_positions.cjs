'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { makeSyntheticFrame } = require('./synthetic_fixture.cjs');
const core = require('./position_core.cjs');
const codebook = JSON.parse(fs.readFileSync(path.join(__dirname, 'propositions.v1.json'), 'utf8'));
let tests = 0;
function check(name, fn) {
  try { fn(); tests++; process.stdout.write('PASS ' + name + '\n'); }
  catch (error) { process.stderr.write('FAIL ' + name + ': ' + error.stack + '\n'); process.exitCode = 1; }
}
function reject(fn, pattern) { assert.throws(fn, pattern); }
const newFrame = () => makeSyntheticFrame(codebook);
const newReport = () => core.summarize(newFrame(), codebook);
const cell = (r, iso3, year, prop) =>
  r.profiles.find(x => x.iso3 === iso3 && x.year === year && x.proposition_id === prop);

check('draft proposition schema and all six unique policy objects', () => {
  assert.equal(core.validateCodebook(codebook).size, 6);
  assert.equal(new Set(codebook.propositions.map(x => x.issue_id)).size, 3);
});
check('codebook cannot pretend to be approved', () => {
  const bad = structuredClone(codebook); bad.release_status = 'approved';
  reject(() => core.validateCodebook(bad), /unpublished draft/);
});
check('complete synthetic fixture validates parent Unicode source offsets', () => {
  const frame = newFrame();
  assert.equal(core.validateFrame(frame, codebook).sources.size, 15);
});
check('real and publication-eligible source frames refused', () => {
  const f = newFrame(); f.dataset_kind = 'real';
  reject(() => core.summarize(f, codebook), /not eligible/);
  const g = newFrame(); g.publication_eligible = true;
  reject(() => core.summarize(g, codebook), /not eligible/);
});
check('unknown or unversioned propositions refused', () => {
  const f = newFrame(); f.observations[0].proposition_id = 'other';
  reject(() => core.summarize(f, codebook), /unknown proposition/);
  const g = newFrame(); g.codebook_version = '2.0.0';
  reject(() => core.summarize(g, codebook), /version mismatch/);
});
check('forged quote/offset and missing source hash refused', () => {
  const f = newFrame(); f.observations[0].quote = 'not the original text';
  reject(() => core.summarize(f, codebook), /does not match/);
  const g = newFrame(); g.sources[0].text_sha256 = null;
  reject(() => core.summarize(g, codebook), /hash/);
});
check('source-family crossing actors or years rejected', () => {
  const f = newFrame();
  const source = f.sources.find(x => x.iso3 === 'CNX');
  source.source_family_id = f.sources[0].source_family_id;
  reject(() => core.summarize(f, codebook), /Source family crosses/);
});
check('all country-period-proposition cells retained including unknowns', () => {
  const r = newReport();
  assert.equal(r.profiles.length, 72);
  assert.equal(cell(r, 'DRL', 2026, 'ukr_force').stance, null);
  assert.equal(cell(r, 'DRL', 2026, 'ukr_force').reason, 'no_observed_statement');
});
check('duplicated translation counted as one source family', () => {
  const r = newReport();
  assert.equal(cell(r, 'USX', 2026, 'ukr_sovereignty').source_family_count, 1);
  assert.equal(cell(r, 'USX', 2026, 'ukr_sovereignty').stance, 'support');
});
check('collective and unverified statements explicitly excluded', () => {
  const r = newReport();
  assert.equal(r.coverage.excluded_observations, 2);
  assert.equal(cell(r, 'ALP', 2026, 'cub_embargo').stance, 'support');
  assert.equal(cell(r, 'DRL', 2026, 'ukr_force').stance, null);
});
check('conditional and descriptive positions are not counted as agreements', () => {
  const r = newReport();
  assert.equal(cell(r, 'USX', 2026, 'ai_binding').stance, null);
  assert.equal(cell(r, 'USX', 2026, 'ai_military').stance, null);
  for (const edge of r.edges)
    assert.ok(edge.shared_proposition_ids.every(p =>
      cell(r, edge.country_a, edge.year, p).stance !== null &&
      cell(r, edge.country_b, edge.year, p).stance !== null));
});
check('within-family conflicting statements withheld', () => {
  const f = newFrame(), s = f.sources.find(x => x.iso3 === 'ALP' && x.date.startsWith('2026'));
  const row = f.observations.find(x => x.source_id === s.source_id && x.proposition_id === 'ukr_sovereignty');
  const q = 'Invented contradiction: opposition to this policy object.';
  const start = Array.from(s.text).length;
  s.text += q + '\n';
  f.observations.push({
    observation_id: 'synthetic-contradiction', passage_id: 'synthetic-contradiction-p',
    source_id: s.source_id, proposition_id: row.proposition_id, stance:'oppose',
    review_status:'synthetic_label', quote:q, start, end:start + Array.from(q).length
  });
  const r = core.summarize(f, codebook);
  assert.equal(cell(r, 'ALP', 2026, 'ukr_sovereignty').stance, null);
  assert.equal(cell(r, 'ALP', 2026, 'ukr_sovereignty').reason, 'conflicting_or_conditional_evidence');
});
check('pairwise agreement uses common propositions and accountable denominator', () => {
  const r = newReport();
  assert.ok(r.edges.length > 0);
  for (const edge of r.edges) {
    assert.ok(edge.comparable_propositions >= 2);
    assert.equal(edge.agreement_count + edge.disagreement_count, edge.comparable_propositions);
    assert.equal(edge.agreement_share, edge.agreement_count / edge.comparable_propositions);
    assert.ok(edge.possible_propositions >= edge.comparable_propositions);
  }
  assert.ok(r.edges.every(e => e.year === 2025 || e.year === 2026));
});
check('small shared-proposition populations omit unsupported edges', () => {
  const r = core.summarize(newFrame(), codebook, { min_shared_propositions: 6 });
  assert.ok(r.edges.length < newReport().edges.length);
  reject(() => core.summarize(newFrame(), codebook, { min_shared_propositions: 1 }), /minimum shared/);
});
check('report validation refuses rebranding as empirical or fitted', () => {
  const r = newReport();
  assert.equal(core.validateReport(r), true);
  r.model_fitted = true;
  reject(() => core.validateReport(r), /synthetic-only/);
});
check('no model output or confidence interval is fabricated', () => {
  const r = newReport();
  assert.equal(r.model_fitted, false);
  assert.equal(r.publication_eligible, false);
  assert.ok(r.edges.every(e => e.confidence_interval === undefined));
});
process.stdout.write('Tests passed: ' + tests + '; failures: ' + (process.exitCode ? 1 : 0) + '\n');
