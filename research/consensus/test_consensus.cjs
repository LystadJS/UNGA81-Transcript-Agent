'use strict';
/* Independent deterministic numerical/relational tests; synthetic records only. */
const assert = require('node:assert/strict');
const C = require('./consensus.cjs');
const F = require('./fixtures.cjs');
let count = 0;
function test(name, fn) {
  fn(); count++;
  process.stdout.write('PASS ' + name + '\n');
}
const clone = x => structuredClone(x);
const known = F.fixtureKnown(false);
const opts = {fit_plan:known.fit_plan};
const base = C.runConsensus(known.envelopes, opts);
const find = (out, a, b) => out.pairs.find(p =>
  p.observation_a === a && p.observation_b === b || p.observation_a === b && p.observation_b === a);
const a1 = 'fictional-unit-1-a', b1 = 'fictional-unit-1-b', a2 = 'fictional-unit-2-a';
function reject(name, change, expected, use = known) {
  test(name, () => {
    const fixture = clone(use);
    change(fixture);
    assert.throws(() => C.runConsensus(fixture.envelopes,{fit_plan:fixture.fit_plan}), expected);
  });
}
test('all synthetic interchange v1 envelopes pass strict upstream validation', () => {
  known.envelopes.forEach(C.validateEnvelope);
  assert.equal(base.schema, 'un.consensus.v1');
  assert.equal(base.publication_eligible, false);
  assert.equal(base.evaluation_role, 'engineering_only');
});
test('pair counts preserve numerator and three different missingness mechanisms', () => {
  const s = find(base, a1, a2), n = find(base, a1, b1);
  assert.equal(s.coassigned_count, 8);
  assert.equal(s.assigned_both_count, 8);
  assert.equal(s.planned_count, 9);
  assert.equal(s.missing_pair_count, 1);
  assert.equal(s.noise_pair_count, 0);
  assert.equal(s.association, 1);
  assert.equal(n.coassigned_count, 0);
  assert.equal(n.assigned_both_count, 8);
  assert.equal(n.missing_pair_count, 1);
  assert.equal(n.association, 0);
});
test('noise excluded from assigned denominator, not silently cluster zero', () => {
  const pair = find(base, a1, 'fictional-unit-6-a');
  assert.equal(pair.planned_count, 9);
  assert.equal(pair.missing_pair_count, 1);
  assert.equal(pair.noise_pair_count, 1);
  assert.equal(pair.assigned_both_count, 7);
  assert.equal(pair.coassigned_count, 7);
  assert.equal(pair.association, 1);
});
test('equal total family weights, equal method shares and seed downweighting', () => {
  assert.equal(base.family_weight_audit.length, 4);
  for (const family of base.family_weight_audit) assert.equal(family.total_weight, 0.25);
  const part = base.family_weight_audit.find(r => r.method_family === 'partition');
  assert.equal(part.records.find(r => r.model_id === 'pam-1').planned_weight, 0.125);
  assert.equal(part.records.find(r => r.model_id === 'kmeans-1').planned_weight, 0.025);
  assert.equal(part.records.find(r => r.model_id === 'failed-1').planned_weight, 0.025);
  assert.equal(part.completely_failed_fit_records, 1);
});
test('added kmeans seeds cannot give partition family extra vote', () => {
  const scenario = clone(known), more = clone(known.envelopes[0]);
  more.models[0].model_id = 'kmeans-5';
  more.results.forEach(r => r.model_id = 'kmeans-5');
  more.coverage.models[0].model_id = 'kmeans-5';
  scenario.envelopes.push(more);
  scenario.fit_plan['kmeans-5'] = {configuration_id:'kmeans_k2',seed:5};
  const out = C.runConsensus(scenario.envelopes,{fit_plan:scenario.fit_plan});
  assert.equal(out.family_weight_audit.find(f => f.method_family === 'partition').total_weight, 0.25);
  assert.equal(find(out, a1, a2).association, 1);
  assert.equal(find(out, a1, b1).association, 0);
});
test('label switching does not change consensus co-assignment', () => {
  const scenario = clone(known);
  for (const row of scenario.envelopes[0].results)
    if (row.status === 'assigned') row.cluster = row.cluster === 1 ? 2 : 1;
  const out = C.runConsensus(scenario.envelopes,{fit_plan:scenario.fit_plan});
  assert.deepEqual(out.matrix.association, base.matrix.association);
});
test('known-structure fixture recovers two across-meeting complete-link groups', () => {
  assert.deepEqual(base.reproducible_groups.map(g => g.members.length), [6,6]);
  assert.equal(base.source_restricted_groups.length, 0);
  assert.equal(base.ungrouped_observations.length, 0);
  assert.equal(new Set(base.reproducible_groups.flatMap(g => g.members)).size, 12);
  assert(base.reproducible_groups.every(g => g.source_group_count === 6));
});
test('observed pair matrix is symmetric with exact explicit denominators', () => {
  const {matrix:m,observation_ids:ids} = base;
  for (const key of ['association','assigned_both_count','planned_count','coassigned_count',
    'assigned_both_weight','planned_weight','coassigned_weight','assignment_coverage']) {
    assert.equal(m[key].length, ids.length);
    for (let i = 0; i < ids.length; i++) for (let j = 0; j < ids.length; j++)
      assert.equal(m[key][i][j], m[key][j][i], key + ': nonsymmetric pair');
  }
  assert.equal(base.pairs.length, ids.length * (ids.length + 1) / 2);
  assert.equal(base.unsupported_pair_ledger.length, 36);
});
test('all failed fits: null associations, zero assigned-both denominator, no groups', () => {
  const failOnly = clone(known.envelopes.find(e => e.models[0].model_id === 'failed-1'));
  const out = C.runConsensus([failOnly], {min_families:1});
  assert.equal(find(out,a1,a2).association, null);
  assert.equal(find(out,a1,a2).assigned_both_count, 0);
  assert.equal(find(out,a1,a2).planned_count, 1);
  assert.equal(out.reproducible_groups.length,0);
  assert(out.unsupported_pair_ledger.every(x => x.reason === 'no_assigned_pair'));
});
test('nuisance-only meeting group partitions are not treated as replicated cross-source groups', () => {
  const fixture = F.fixtureNuisance(), out = C.runConsensus(fixture.envelopes,{fit_plan:fixture.fit_plan});
  assert.equal(out.reproducible_groups.length, 0);
  assert.equal(out.source_restricted_groups.length, 6);
  assert(out.source_restricted_groups.every(g => g.source_group_count === 1));
  assert(out.unsupported_pair_ledger.some(x => x.reason === 'supported_pair_not_in_reproducible_group'));
});
test('grouped leave-one-meeting-out and bootstrap quantify descriptive spread only', () => {
  const fixture = F.fixtureKnown(true);
  const out = C.runConsensus(fixture.envelopes,{fit_plan:fixture.fit_plan,min_coverage:0.2});
  const row = out.uncertainty.pairwise.find(p =>
    p.observation_a === a1 && p.observation_b === a2);
  assert.equal(out.uncertainty.source_groups, 6);
  assert.equal(out.uncertainty.design, 'grouped_refits_descriptive_spread');
  assert(row.leave_group_out.total_resamples === 6);
  assert.equal(row.leave_group_out.assessable_resamples, 4);
  assert.equal(row.leave_group_out.status,'descriptive');
  assert.equal(row.leave_group_out.p05,1);
  assert.equal(row.leave_group_out.p95,1);
  assert(row.group_bootstrap.total_resamples === 7);
  assert.equal(row.group_bootstrap.assessable_resamples, 5);
  assert.equal(row.group_bootstrap.status, 'descriptive');
  assert.equal(row.group_bootstrap.p05,1);
  assert.equal(row.group_bootstrap.p95,1);
  assert(out.sensitivity_report.some(r => r.design === 'baseline_only_vs_all_refits'));
  assert(out.sensitivity_report.some(r => r.design === 'leave_one_method_family_out'));
  assert(out.reproducible_groups.length === 2);
  assert(!Object.keys(row.group_bootstrap).some(k => /confidence|p_value/.test(k)));
});
test('source links, hashes, parent identity and unknown speaker remain unchanged in v1 adapter', () => {
  const adapted = C.toInterchangeV1(known.envelopes[0],base,{generated_at:'2026-10-08T00:00:00Z'});
  C.validateEnvelope(adapted);
  assert.equal(adapted.producer.workstream_id,'W2');
  assert.equal(adapted.results.length,12);
  assert.equal(adapted.coverage.models[0].assigned,12);
  assert.equal(adapted.upstream.source_sha256,known.envelopes[0].upstream.source_sha256);
  assert.deepEqual(adapted.observations, known.envelopes[0].observations);
  assert(adapted.observations.every(o => o.country === null && o.speech_id === null));
  assert(adapted.diagnostics.some(d => d.status === 'withheld'));
  assert(!JSON.stringify(adapted).includes('transcript_text'));
});
test('ARI is label-permutation invariant and explicitly conditional', () => {
  assert.equal(C.ari([1,1,2,2,3,3],[3,3,1,1,2,2]),1);
  assert.equal(C.ari([1,1,1,1],[1,1,1,1]),null);
  assert.equal(C.ari([1,2],[1,2]),null);
  assert.equal(C.ari([1,1,2,2],[1,2,1,2]),-0.5);
  assert(base.individual_method_comparisons.every(m => 'ari_conditional_on_both_assigned' in m));
});
test('no resamples means no uncertainty confidence claims', () => {
  assert.equal(base.uncertainty.design,'not_estimated');
  assert.deepEqual(base.uncertainty.pairwise,[]);
  assert(base.limitations.some(t => t.includes('not confidence')));
});
reject('reject mixed source hashes', fixture => {fixture.envelopes[1].upstream.source_sha256=F.sha('wrong source');}, /incompatible source population/);
reject('reject mismatched selection identity', fixture => {fixture.envelopes[1].upstream.selection_sha256=F.sha('wrong selection');fixture.envelopes[1].models[0].training_selection_sha256=F.sha('wrong selection');}, /incompatible source population/);
reject('reject altered source URLs', fixture => {fixture.envelopes[1].observations[0].source_url='https://example.invalid/different';}, /incompatible source population/);
reject('reject mismatched observation text hashes', fixture => {fixture.envelopes[1].observations[0].text_sha256=F.sha('modified synthetic id');}, /incompatible source population/);
reject('reject duplicate observed identities', fixture => {fixture.envelopes[0].observations[1].id=fixture.envelopes[0].observations[0].id;}, /duplicate observation ID/);
reject('reject undocumented missing pair result', fixture => {fixture.envelopes[0].results.pop();}, /missing eligible results/);
reject('reject non-null cluster for failed fit', fixture => {fixture.envelopes.at(-1).results[0].cluster=2;}, /missing fit needs null and reason/);
reject('reject unassigned/noise assigned a positive cluster', fixture => {fixture.envelopes.find(e => e.models[0].method === 'hdbscan').results.at(-2).cluster=99;}, /noise is cluster zero/);
reject('reject changed representation basis within model', fixture => {fixture.envelopes[0].results[0].representation_basis_id='wrong-basis';}, /wrong representation basis/);
reject('reject mismatched failure accounting', fixture => {fixture.envelopes.at(-1).coverage.models[0].failed_fits=0;}, /fit attempt ledger inconsistent/);
reject('reject unverifiable country-speaker promotion', fixture => {fixture.envelopes[0].observations[0].speech_id='invented-id';}, /unverified speech identity/);
reject('reject inclusion of reserved-date development records', fixture => {const e=fixture.envelopes[0];e.cohort.split='development';e.producer.fixture_kind='private_development';e.models[0].fit_split='development';e.observations[0].date='2026-10-05';}, /reserved transcript date/);
reject('reject cross-basis comparison without declared protocol', fixture => {
  fixture.envelopes[1].models[0].representation_id='synthetic-minilm-lock';
  fixture.envelopes[1].results.forEach(r => r.representation_basis_id='synthetic-minilm-lock');
}, /cross-representation models require/);
test('named cross-basis protocol permits identity-matched descriptive partition comparisons', () => {
  const fixture = clone(known);
  fixture.envelopes[1].models[0].representation_id='synthetic-minilm-lock';
  fixture.envelopes[1].results.forEach(r => r.representation_basis_id='synthetic-minilm-lock');
  const out = C.runConsensus(fixture.envelopes,{fit_plan:fixture.fit_plan,
    cross_basis_protocol:'identity_join_hard_partition_v1'});
  assert.equal(out.source.representation_versions.length,2);
  assert.equal(out.source.cross_basis_protocol,'identity_join_hard_partition_v1');
});
test('unknown model metadata is rejected before assigning weights', () => {
  assert.throws(() => C.runConsensus(known.envelopes,{fit_plan:{...known.fit_plan,nonexistent:{}}}),/metadata references unknown model/);
});
test('duplicate seed/configuration/resample cannot amplify a model vote', () => {
  const fixture=clone(known), duplicate=clone(known.envelopes[0]);
  duplicate.models[0].model_id='kmeans-copy';
  duplicate.results.forEach(r => r.model_id='kmeans-copy');
  duplicate.coverage.models[0].model_id='kmeans-copy';
  fixture.envelopes.push(duplicate);
  fixture.fit_plan['kmeans-copy'] = {configuration_id:'kmeans_k2',seed:1};
  assert.throws(() => C.runConsensus(fixture.envelopes,{fit_plan:fixture.fit_plan}), /duplicate declared seed/);
});
test('omitted source group cannot retain a fitted or noise assignment', () => {
  const fixture=F.fixtureKnown(true);
  const index=fixture.envelopes.findIndex(e => e.models[0].model_id==='ward-loo-1');
  const row=fixture.envelopes[index].results.find(r => r.observation_id === a1);
  row.status='assigned'; row.cluster=1; row.reason=null;
  const counts=fixture.envelopes[index].coverage.models[0];
  counts.assigned++;counts.not_fitted--;
  assert.throws(() => C.runConsensus(fixture.envelopes,{fit_plan:fixture.fit_plan}),/omitted source group cannot/);
});
test('family sensitivity is a list of comparisons, never a universal ranking metric', () => {
  assert(base.sensitivity_report.every(r => r.design === 'leave_one_method_family_out'));
  assert(!Object.hasOwn(base,'best_model'));
  assert(!Object.hasOwn(base,'significance'));
  assert(!Object.hasOwn(base,'p_value'));
});
test('saved consensus sidecar passes structural schema and independent relational invariants', () => {
  assert.equal(C.validateConsensus(base),true);
  const bad = clone(base);
  bad.matrix.association[0][1] = 0.25;
  assert.throws(() => C.validateConsensus(bad), /matrix\/pair ledger mismatch/);
});
test('corrupted pair count or weighted numerator is rejected', () => {
  const bad = clone(base);
  bad.pairs[1].assigned_both_count = bad.pairs[1].planned_count + 1;
  assert.throws(() => C.validateConsensus(bad), /raw pair-opportunity accounting/);
  const second = clone(base);
  second.pairs[1].coassigned_weight = second.pairs[1].assigned_both_weight + 0.1;
  assert.throws(() => C.validateConsensus(second), /weighted opportunity accounting/);
});
test('corrupt sidecar source hashes, IDs and group membership are rejected', () => {
  const bad = clone(base);
  bad.source.observation_keys[0].text_sha256 = 'not-a-hash';
  assert.throws(() => C.validateConsensus(bad), /source links\/hashes/);
  const groupBad = clone(base);
  groupBad.reproducible_groups[1].members.push(groupBad.reproducible_groups[0].members[0]);
  assert.throws(() => C.validateConsensus(groupBad), /observation belongs to multiple groups|complete-link group contains unsupported pair/);
});
test('invalid parent offsets and mismatched parent hashes fail closed', () => {
  const scenario = clone(known);
  scenario.envelopes[0].observations[0].parent_id='synthetic-parent';
  assert.throws(() => C.runConsensus(scenario.envelopes,{fit_plan:scenario.fit_plan}), /parent missing hash/);
  scenario.envelopes[0].observations[0].parent_text_sha256=F.sha('synthetic parent');
  scenario.envelopes[0].observations[0].start=10;
  scenario.envelopes[0].observations[0].end=5;
  assert.throws(() => C.runConsensus(scenario.envelopes,{fit_plan:scenario.fit_plan}), /invalid offset/);
});
process.stdout.write(JSON.stringify({suite:'consensus-synthetic',tests:count,status:'pass',
  input_models:known.envelopes.length,known_structure_groups:base.reproducible_groups.length,
  reserved_transcripts_opened:0,network_access:false}) + '\n');
