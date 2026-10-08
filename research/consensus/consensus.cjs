'use strict';
/*
 * Source-bound consensus of hard partition labels. Engineering-only W2 adapter.
 * Original text, browser kernels, and frozen evaluation sources are never loaded.
 */
const {createHash} = require('node:crypto');
const INTERCHANGE = require('../../docs/parallel-work/interchange-v1.schema.json');
const VERSION = '0.1.0';
const SHA = /^[0-9a-f]{64}$/;
const TYPES = new Set(['baseline', 'leave_group_out', 'group_bootstrap']);
const fail = message => { throw new Error('consensus: ' + message); };
const check = (ok, message) => { if (!ok) fail(message); };
const stable = x => Array.isArray(x) ? '[' + x.map(stable).join(',') + ']' :
  x && typeof x === 'object' ? '{' + Object.keys(x).sort().map(k => JSON.stringify(k) + ':' + stable(x[k])).join(',') + '}' : JSON.stringify(x);
const digest = x => createHash('sha256').update(typeof x === 'string' ? x : stable(x)).digest('hex');
const round = n => Number.isFinite(n) ? Math.round(n * 1e12) / 1e12 : null;
const unique = xs => [...new Set(xs)];
const groupBy = (xs, key) => {
  const groups = new Map();
  for (const x of xs) { const k = key(x); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(x); }
  return groups;
};
function schemaCheck(spec, value, at = '$') {
  if (Object.hasOwn(spec, 'const')) check(stable(spec.const) === stable(value), at + ': wrong constant');
  if (spec.enum) check(spec.enum.includes(value), at + ': invalid enumeration');
  if (spec.type) {
    const types = Array.isArray(spec.type) ? spec.type : [spec.type];
    const matches = type => type === 'null' ? value === null : type === 'object' ?
      value !== null && typeof value === 'object' && !Array.isArray(value) :
      type === 'array' ? Array.isArray(value) : type === 'integer' ?
      Number.isSafeInteger(value) : type === 'number' ?
      typeof value === 'number' && Number.isFinite(value) : typeof value === type;
    check(types.some(matches), at + ': invalid type');
  }
  if (typeof value === 'string') {
    if (spec.minLength !== undefined) check(value.length >= spec.minLength, at + ': too short');
    if (spec.pattern) check(new RegExp(spec.pattern).test(value), at + ': bad format');
    if (spec.format === 'date-time') check(!Number.isNaN(Date.parse(value)) && /(Z|[+-]\d\d:\d\d)$/.test(value), at + ': bad timestamp');
  }
  if (typeof value === 'number') {
    if (spec.minimum !== undefined) check(value >= spec.minimum, at + ': below minimum');
    if (spec.maximum !== undefined) check(value <= spec.maximum, at + ': above maximum');
  }
  if (Array.isArray(value)) {
    if (spec.minItems !== undefined) check(value.length >= spec.minItems, at + ': too few items');
    if (spec.items) value.forEach((v, i) => schemaCheck(spec.items, v, at + '[' + i + ']'));
  }
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    (spec.required || []).forEach(k => check(Object.hasOwn(value, k), at + ': missing ' + k));
    for (const [k, v] of Object.entries(value)) {
      if (spec.properties && Object.hasOwn(spec.properties, k)) schemaCheck(spec.properties[k], v, at + '.' + k);
      else if (spec.additionalProperties === false) fail(at + ': unknown property ' + k);
    }
  }
}
function sourceGroup(row, mode) {
  const key = {meeting: 'meeting_id', speech: 'speech_id', parent: 'parent_id',
    country: 'country', source_family: 'source_family_id'}[mode];
  if (mode === 'synthetic') return row.meeting_id || row.source_family_id || null;
  return key ? row[key] : null;
}
function validateEnvelope(x) {
  schemaCheck(INTERCHANGE, x);
  check(x.schema === 'un.parallel-analysis.v1', 'interchange v1 required');
  check(/^1\./.test(x.contract_version) && x.producer.workstream_id !== 'W2' || /^1\./.test(x.contract_version),
    'unsupported contract version');
  check(x.publication_eligible === false && x.evaluation_role === 'engineering_only', 'non-engineering input forbidden');
  check(x.cohort.split === x.producer.fixture_kind.replace('private_', '') || x.cohort.split === 'development' && x.producer.fixture_kind === 'private_development',
    'fixture/split mismatch');
  check(SHA.test(x.upstream.source_sha256 || '') && SHA.test(x.upstream.selection_sha256 || ''), 'source and selection hashes required');
  check(x.cohort.eligible > 0 && x.cohort.eligible <= 256, 'eligible count outside [1,256]');
  check(x.observations.length === x.coverage.observations_total, 'observation inventory mismatch');
  check(x.coverage.eligible === x.cohort.eligible, 'eligible coverage mismatch');
  const observed = new Map(), eligible = new Map();
  for (const row of x.observations) {
    check(!observed.has(row.id), 'duplicate observation ID ' + row.id);
    observed.set(row.id, row);
    check(row.start === null && row.end === null || Number.isInteger(row.start) && Number.isInteger(row.end) && row.end > row.start, 'invalid offset');
    check(row.parent_id === null || !!row.parent_text_sha256, 'parent missing hash');
    check(row.source_status === 'available' || !!row.missing_reason, 'unavailable source missing reason');
    check(row.review_status === 'confirmed' || row.speech_id === null, 'unverified speech identity');
    if (x.cohort.split === 'development') check(!['2026-10-05', '2026-10-06'].includes(row.date), 'reserved transcript date');
    if (row.source_status === 'available' && !row.exclusion_reasons.length) {
      check(SHA.test(row.text_sha256 || ''), 'eligible observation lacks text hash');
      eligible.set(row.id, row);
    }
  }
  check(eligible.size === x.cohort.eligible && observed.size - eligible.size === x.coverage.excluded, 'eligible/excluded lineage mismatch');
  check(x.models.length === x.coverage.models.length, 'missing model coverage rows');
  const models = new Map(), ledgers = new Map();
  for (const c of x.coverage.models) { check(!ledgers.has(c.model_id), 'repeated model coverage'); ledgers.set(c.model_id, c); }
  const results = groupBy(x.results, r => r.model_id);
  for (const m of x.models) {
    check(!models.has(m.model_id), 'duplicate model ID');
    models.set(m.model_id, m);
    check(m.fit_split === x.cohort.split, 'model split mismatch');
    check(m.training_selection_sha256 === x.upstream.selection_sha256, 'model training selection mismatch');
    const c = ledgers.get(m.model_id), rows = results.get(m.model_id) || [];
    check(c && c.eligible === eligible.size && c.assigned + c.unassigned + c.not_fitted === c.eligible,
      'model coverage incompatible: ' + m.model_id);
    check(c.attempted_fits === c.successful_fits + c.failed_fits, 'fit attempt ledger inconsistent');
    const byId = new Map();
    for (const r of rows) {
      check(!byId.has(r.observation_id) && observed.has(r.observation_id), 'duplicate/unknown fit observation');
      byId.set(r.observation_id, r);
      check(r.representation_basis_id === m.representation_id, 'wrong representation basis');
      if (r.status === 'assigned') check(Number.isSafeInteger(r.cluster) && r.cluster > 0, 'invalid assigned cluster');
      if (r.status === 'unassigned') check(r.cluster === 0, 'noise is cluster zero');
      if (r.status === 'not_fitted' || r.status === 'excluded') check(r.cluster === null && !!r.reason, 'missing fit needs null and reason');
      if (r.membership_kind === 'gmm_responsibility' || r.membership_kind === 'nmf_share')
        check(Array.isArray(r.memberships) && r.memberships.length > 0 &&
          r.memberships.every(v => Number.isFinite(v) && v >= 0 && v <= 1) &&
          Math.abs(r.memberships.reduce((a, b) => a + b, 0) - 1) <= 1e-6, 'invalid soft membership');
      else check(r.memberships === null, 'unexpected membership array');
      if (r.membership_kind === 'hdbscan_strength') check(r.membership_strength !== null, 'missing density strength');
    }
    check([...eligible.keys()].every(id => byId.has(id) && byId.get(id).status !== 'excluded'), 'missing eligible results');
    for (const status of ['assigned', 'unassigned', 'not_fitted', 'excluded'])
      check(rows.filter(r => r.status === status).length === c[status], 'coverage status mismatch ' + status);
    check(c.successful_fits > 0 || [...eligible.keys()].every(id => byId.get(id).status === 'not_fitted'),
      'failed fit used as successful assignments');
    for (const id of eligible.keys()) check(sourceGroup(eligible.get(id), x.cohort.source_group_unit) !== null,
      'missing declared source group for ' + id);
  }
  check(models.size === ledgers.size && [...results.keys()].every(k => models.has(k)), 'unknown model in results');
  for (const f of x.coverage.failure_ledger) check(models.has(f.model_id), 'failure references unknown model');
  for (const e of x.evidence) check(observed.has(e.observation_id) &&
    (e.start === null && e.end === null || e.start !== null && e.end !== null && e.start < e.end),
    'unlinked evidence pointer');
  return {observed, eligible, models, results, ledgers};
}
function extract(envelopes, opts = {}) {
  check(Array.isArray(envelopes) && envelopes.length > 0, 'provide one or more interchange v1 envelopes');
  const base = envelopes[0], baseline = validateEnvelope(base);
  const identity = x => stable({
    upstream: x.upstream, cohort: x.cohort, observations: x.observations.map(o => o).sort((a, b) => a.id.localeCompare(b.id))
  });
  const baseIdentity = identity(base);
  const fits = [], ids = [...baseline.eligible.keys()].sort();
  const sourceGroups = unique(ids.map(id => sourceGroup(baseline.eligible.get(id), base.cohort.source_group_unit))).sort();
  const seen = new Set();
  for (const x of envelopes) {
    const v = x === base ? baseline : validateEnvelope(x);
    check(identity(x) === baseIdentity, 'incompatible source population, lineage, hash basis or selection');
    for (const m of x.models) {
      check(!seen.has(m.model_id), 'model IDs must be globally unique');
      seen.add(m.model_id);
      const meta = (opts.fit_plan || {})[m.model_id] || {};
      const type = meta.resample_type || 'baseline';
      check(TYPES.has(type), 'invalid resample design');
      const resampleId = meta.resample_id || 'baseline';
      check(typeof resampleId === 'string' && !!resampleId, 'invalid resample ID');
      check((type === 'baseline') === (resampleId === 'baseline'), 'baseline resample ID mismatch');
      const sampled = type === 'baseline' ? sourceGroups : meta.sampled_groups;
      check(Array.isArray(sampled) && sampled.length && sampled.every(g => sourceGroups.includes(g)),
        'resample must declare existing whole source groups');
      const included = new Set(sampled);
      if (type === 'leave_group_out') check(sampled.length === sourceGroups.length - 1 && included.size === sampled.length,
        'leave-group-out must omit exactly one whole group');
      if (type === 'group_bootstrap') check(sampled.length === sourceGroups.length && sourceGroups.length >= 3,
        'group bootstrap must sample source groups with replacement');
      const rows = new Map((v.results.get(m.model_id) || []).map(r => [r.observation_id, r]));
      for (const id of ids) if (!included.has(sourceGroup(baseline.eligible.get(id), base.cohort.source_group_unit)))
        check(rows.get(id).status === 'not_fitted', 'omitted source group cannot have a fitted/noise label');
      fits.push({
        id: m.model_id, family: m.method_family, method: m.method,
        config: meta.configuration_id || [m.method, m.representation_id, m.representation_version, m.parameters_sha256].join('|'),
        resample_id: resampleId, resample_type: type, sampled_groups: sampled.slice(),
        seed: meta.seed === undefined ? null : meta.seed,
        model: m, coverage: v.ledgers.get(m.model_id), rows
      });
    }
  }
  check(Object.keys(opts.fit_plan || {}).every(k => seen.has(k)), 'metadata references unknown model');
  const bases = unique(fits.map(f => f.model.representation_id + '@' + f.model.representation_version));
  if (bases.length > 1) check(opts.cross_basis_protocol === 'identity_join_hard_partition_v1',
    'cross-representation models require named identity-join descriptive protocol');
  const plans = new Map();
  for (const f of fits) {
    const k = f.resample_type + ':' + f.resample_id;
    if (plans.has(k)) check(stable(plans.get(k)) === stable(f.sampled_groups), 'resample ID disagrees on sampled groups');
    else plans.set(k, f.sampled_groups);
  }
  // A retry with the same seed/configuration/resample is not an independent vote.
  const repetitions = new Set();
  for (const f of fits) {
    const key = stable([f.family, f.method, f.config, f.resample_type, f.resample_id, f.seed]);
    if (f.seed !== null) check(!repetitions.has(key), 'duplicate declared seed/configuration vote');
    repetitions.add(key);
  }
  return {base, baseline, ids, sourceGroups, fits, bases};
}
function weightsFor(fits) {
  const weights = new Map();
  const families = groupBy(fits, f => f.family);
  for (const familyFits of families.values()) {
    const methods = groupBy(familyFits, f => f.method);
    for (const methodFits of methods.values()) {
      const configs = groupBy(methodFits, f => f.config);
      for (const configFits of configs.values()) {
        const resamples = groupBy(configFits, f => f.resample_type + ':' + f.resample_id);
        for (const replicaFits of resamples.values()) {
          const w = 1 / families.size / methods.size / configs.size / resamples.size / replicaFits.length;
          for (const f of replicaFits) weights.set(f.id, w);
        }
      }
    }
  }
  check(Math.abs([...weights.values()].reduce((a, b) => a + b, 0) - 1) < 1e-9, 'family weights do not sum to one');
  return weights;
}
function pairFor(a, b, fits, weights) {
  let co = 0, both = 0, opportunity = 0, coN = 0, bothN = 0, opportunityN = 0;
  let missingN = 0, noiseN = 0, differentN = 0, failedN = 0;
  const families = new Set();
  for (const f of fits) {
    const w = weights.get(f.id), x = f.rows.get(a), y = f.rows.get(b);
    opportunity += w; opportunityN++;
    if (f.coverage.successful_fits === 0) failedN++;
    if (!x || !y || ['not_fitted', 'excluded'].includes(x.status) || ['not_fitted', 'excluded'].includes(y.status)) { missingN++; continue; }
    if (x.status !== 'assigned' || y.status !== 'assigned') { noiseN++; continue; }
    both += w; bothN++; families.add(f.family);
    if (x.cluster === y.cluster) { co += w; coN++; }
    else differentN++;
  }
  return {observation_a:a, observation_b:b, coassigned_count:coN, assigned_both_count:bothN,
    planned_count:opportunityN, missing_pair_count:missingN, noise_pair_count:noiseN,
    different_cluster_count:differentN, failed_fit_count:failedN,
    coassigned_weight:round(co), assigned_both_weight:round(both), planned_weight:round(opportunity),
    association:both > 1e-15 ? round(co / both) : null,
    assignment_coverage:opportunity > 1e-15 ? round(both / opportunity) : null,
    contributing_families:[...families].sort()};
}
function matrix(ids, pairs, key) {
  const byPair = new Map(pairs.map(p => [stable([p.observation_a, p.observation_b]), p]));
  return ids.map((a, i) => ids.map((b, j) =>
    byPair.get(stable(i <= j ? [a, b] : [b, a]))[key]));
}
function quantile(xs, p) {
  const v = xs.slice().sort((a, b) => a - b);
  if (!v.length) return null;
  const at = (v.length - 1) * p, lo = Math.floor(at);
  return round(v[lo] + (v[Math.ceil(at)] - v[lo]) * (at - lo));
}
function uncertainty(a, b, fits) {
  const designs = {};
  for (const type of ['leave_group_out', 'group_bootstrap']) {
    const resamples = groupBy(fits.filter(f => f.resample_type === type), f => f.resample_id);
    const values = [], eligibleN = [], familyCounts = [];
    for (const rows of resamples.values()) {
      const p = pairFor(a, b, rows, weightsFor(rows));
      if (p.association !== null) values.push(p.association);
      eligibleN.push(p.assigned_both_count);
      familyCounts.push(p.contributing_families.length);
    }
    const target = type === 'group_bootstrap' ? 5 : 3;
    designs[type] = {status: resamples.size >= target && values.length >= target ? 'descriptive' : 'withheld',
      total_resamples:resamples.size, assessable_resamples:values.length, 
      p05:values.length >= target ? quantile(values, 0.05) : null,
      p95:values.length >= target ? quantile(values, 0.95) : null,
      minimum_assigned_fits:eligibleN.length ? Math.min(...eligibleN) : null,
      minimum_method_families:familyCounts.length ? Math.min(...familyCounts) : null,
      reason:resamples.size >= target && values.length >= target ? null : 'Insufficient source-group refits with this pair assigned in both rows; not a confidence interval.'};
  }
  return designs;
}
function ari(a, b) {
  if (a.length !== b.length || a.length < 4) return null;
  const choose2 = n => n * (n - 1) / 2, ca = new Map(), cb = new Map(), ct = new Map();
  for (let i = 0; i < a.length; i++) {
    ca.set(a[i], (ca.get(a[i]) || 0) + 1);
    cb.set(b[i], (cb.get(b[i]) || 0) + 1);
    const k = a[i] + '|' + b[i]; ct.set(k, (ct.get(k) || 0) + 1);
  }
  if (ca.size < 2 || cb.size < 2) return null;
  const x = [...ca.values()].reduce((s, n) => s + choose2(n), 0);
  const y = [...cb.values()].reduce((s, n) => s + choose2(n), 0);
  const z = [...ct.values()].reduce((s, n) => s + choose2(n), 0);
  const exp = x * y / choose2(a.length), den = (x + y) / 2 - exp;
  return den > 1e-12 ? round((z - exp) / den) : null;
}
function buildGroups(ids, byKey, observed, options) {
  const threshold = options.min_association ?? 0.8;
  const minCoverage = options.min_coverage ?? 0.4;
  const minFamilies = options.min_families ?? 2;
  const minGroups = options.min_source_groups ?? 2;
  for (const [v, name] of [[threshold, 'min_association'], [minCoverage, 'min_coverage']])
    check(typeof v === 'number' && v >= 0 && v <= 1, 'bad ' + name);
  check(Number.isSafeInteger(minFamilies) && minFamilies >= 1 && Number.isSafeInteger(minGroups) && minGroups >= 1,
    'invalid minimum group/family support');
  const get = (a, b) => byKey.get(stable([a, b].sort()));
  const supported = p => p && p.association !== null && p.association >= threshold &&
    p.assignment_coverage >= minCoverage && p.contributing_families.length >= minFamilies;
  // Deterministic complete-link: a bridge cannot join a group unless all its cross-pairs qualify.
  const groups = ids.map(id => [id]);
  while (true) {
    let best = null;
    for (let i = 0; i < groups.length; i++) for (let j = i + 1; j < groups.length; j++) {
      const cross = groups[i].flatMap(a => groups[j].map(b => get(a, b)));
      if (!cross.every(supported)) continue;
      const minimum = Math.min(...cross.map(p => p.association));
      const key = stable([...groups[i], ...groups[j]].sort());
      if (!best || minimum > best.minimum + 1e-12 || Math.abs(minimum - best.minimum) <= 1e-12 && key < best.key)
        best = {i, j, minimum, key};
    }
    if (!best) break;
    const combined = [...groups[best.i], ...groups[best.j]].sort();
    groups.splice(best.j, 1); groups.splice(best.i, 1); groups.push(combined);
    groups.sort((a, b) => a[0].localeCompare(b[0]));
  }
  const usable = [], sourceRestricted = [];
  for (const members of groups.filter(g => g.length >= 2)) {
    const groupsFound = groupBy(members, id => observed.get(id).__source_group);
    const largest = Math.max(...[...groupsFound.values()].map(g => g.length));
    const rec = {members, source_group_count:groupsFound.size, max_source_group_share:round(largest / members.length),
      minimum_pair_association:round(Math.min(...members.flatMap((a, i) => members.slice(i + 1).map(b => get(a, b).association))))};
    if (groupsFound.size >= minGroups) usable.push(rec);
    else sourceRestricted.push({...rec, reason:'source_concentration'});
  }
  const result = usable.map((g, i) => ({group_id:'G' + String(i + 1).padStart(3, '0'),
    status:'descriptive_reproducible', ...g}));
  const membership = new Map(result.flatMap(g => g.members.map(id => [id, g.group_id])));
  const ambiguous = [];
  for (const id of ids) {
    const strong = ids.filter(other => other !== id && supported(get(id, other)));
    const externalGroups = unique(strong.map(other => membership.get(other)).filter(g => g !== undefined && g !== membership.get(id)));
    const unreproduced = !membership.has(id);
    if (externalGroups.length || unreproduced && strong.length)
      ambiguous.push({observation_id:id, assigned_group:membership.get(id) || null,
        reason:externalGroups.length ? 'cross_group_links' : 'no_complete_link_supported_group',
        cross_group_links:externalGroups, supported_neighbor_count:strong.length});
  }
  const unsupported = [];
  for (const p of byKey.values()) {
    if (p.observation_a === p.observation_b) continue;
    let reason = null;
    if (p.association === null) reason = 'no_assigned_pair';
    else if (p.assignment_coverage < minCoverage) reason = 'insufficient_pair_coverage';
    else if (p.contributing_families.length < minFamilies) reason = 'insufficient_method_families';
    else if (p.association < threshold) reason = 'below_association_threshold';
    else if (!membership.get(p.observation_a) || membership.get(p.observation_a) !== membership.get(p.observation_b))
      reason = 'supported_pair_not_in_reproducible_group';
    if (reason) unsupported.push({observation_a:p.observation_a, observation_b:p.observation_b,
      reason, association:p.association, assigned_both_count:p.assigned_both_count, planned_count:p.planned_count});
  }
  return {groups:result, source_restricted_groups:sourceRestricted, ambiguous, membership, unsupported,
    thresholds:{min_association:threshold,min_coverage:minCoverage,min_families:minFamilies,min_source_groups:minGroups}};
}
function runConsensus(envelopes, options = {}) {
  const x = extract(envelopes, options), {ids, fits, baseline, base} = x, weights = weightsFor(fits);
  const pairs = [];
  for (let i = 0; i < ids.length; i++) for (let j = i; j < ids.length; j++)
    pairs.push(pairFor(ids[i], ids[j], fits, weights));
  const byKey = new Map(pairs.map(p => [stable([p.observation_a, p.observation_b]), p]));
  const source = new Map(ids.map(id => [id, {...baseline.eligible.get(id),
    __source_group:sourceGroup(baseline.eligible.get(id), base.cohort.source_group_unit)}]));
  const groups = buildGroups(ids, byKey, source, options);
  const families = groupBy(fits, f => f.family);
  const familyWeightAudit = [...families].map(([name, fs]) => ({
    method_family:name, total_weight:round(fs.reduce((s, f) => s + weights.get(f.id), 0)),
    methods:unique(fs.map(f => f.method)).sort(), configurations:unique(fs.map(f => f.config)).length,
    models:fs.length, successful_fit_records:fs.filter(f => f.coverage.successful_fits > 0).length,
    completely_failed_fit_records:fs.filter(f => f.coverage.successful_fits === 0).length,
    internal_attempts:fs.reduce((s, f) => s + f.coverage.attempted_fits, 0),
    internal_failures:fs.reduce((s, f) => s + f.coverage.failed_fits, 0),
    records:fs.map(f => ({model_id:f.id, method:f.method, configuration_id:f.config,
      resample_type:f.resample_type, resample_id:f.resample_id, seed:f.seed, planned_weight:round(weights.get(f.id)),
      fitted_observations:[...f.rows.values()].filter(r => r.status === 'assigned').length,
      source_group_sample:f.sampled_groups.slice(), fitting_success:f.coverage.successful_fits > 0}))
  })).sort((a, b) => a.method_family.localeCompare(b.method_family));
  const comparisons = fits.map(f => {
    const both = ids.filter(id => f.rows.get(id).status === 'assigned' && groups.membership.has(id));
    return {model_id:f.id, method_family:f.family, method:f.method, assigned_n:ids.filter(id => f.rows.get(id).status === 'assigned').length,
      compared_to_consensus_n:both.length, ari_conditional_on_both_assigned:
        ari(both.map(id => f.rows.get(id).cluster), both.map(id => groups.membership.get(id))),
      note:'ARI is conditional on shared hard assignments; missing/noise units are not coerced to a cluster.'};
  });
  const sensitivity = [];
  for (const family of families.keys()) {
    const remaining = fits.filter(f => f.family !== family);
    if (!remaining.length) continue;
    const w = weightsFor(remaining);
    let available = 0, changed = 0, maxDelta = 0, withheld = 0;
    for (const p of pairs.filter(p => p.observation_a !== p.observation_b)) {
      const alternative = pairFor(p.observation_a, p.observation_b, remaining, w);
      if (p.association === null || alternative.association === null) {withheld++; continue;}
      available++;
      maxDelta = Math.max(maxDelta, Math.abs(p.association - alternative.association));
      if ((p.association >= groups.thresholds.min_association) !== (alternative.association >= groups.thresholds.min_association)) changed++;
    }
    sensitivity.push({design:'leave_one_method_family_out', removed_family:family, assessed_pairs:available,
      withheld_pairs:withheld, threshold_crossings:changed, maximum_absolute_association_change:round(maxDelta),
      interpretive_status:'descriptive_not_inferential'});
  }
  const baselineFits = fits.filter(f => f.resample_type === 'baseline');
  if (baselineFits.length && baselineFits.length < fits.length) {
    const w = weightsFor(baselineFits); let assessed = 0, delta = 0;
    for (const p of pairs.filter(p => p.observation_a !== p.observation_b)) {
      const v = pairFor(p.observation_a, p.observation_b, baselineFits, w);
      if (v.association !== null && p.association !== null) {assessed++; delta = Math.max(delta, Math.abs(v.association - p.association));}
    }
    sensitivity.push({design:'baseline_only_vs_all_refits', assessed_pairs:assessed,
      maximum_absolute_association_change:round(delta), interpretive_status:'descriptive_not_inferential'});
  }
  const sourceResamples = fits.some(f => f.resample_type !== 'baseline');
  const uncertaintyRows = sourceResamples ? pairs.filter(p => p.observation_a !== p.observation_b)
    .map(p => ({observation_a:p.observation_a,observation_b:p.observation_b,...uncertainty(p.observation_a,p.observation_b,fits)})) : [];
  const unassigned = ids.filter(id => !groups.membership.has(id));
  return {
    schema:'un.consensus.v1', version:VERSION, contract_schema:'un.parallel-analysis.v1',
    evaluation_role:'engineering_only', publication_eligible:false,
    source:{...base.upstream, cohort:base.cohort, observation_keys:ids.map(id => ({id,
      text_sha256:baseline.eligible.get(id).text_sha256,
      parent_id:baseline.eligible.get(id).parent_id,
      meeting_id:baseline.eligible.get(id).meeting_id,
      source_url:baseline.eligible.get(id).source_url,
      json_pointer:baseline.eligible.get(id).json_pointer,
      start:baseline.eligible.get(id).start,end:baseline.eligible.get(id).end})),
      representation_versions:x.bases, cross_basis_protocol:options.cross_basis_protocol || null},
    observation_ids:ids,
    matrix:{association:matrix(ids,pairs,'association'),
      coassigned_count:matrix(ids,pairs,'coassigned_count'),assigned_both_count:matrix(ids,pairs,'assigned_both_count'),
      planned_count:matrix(ids,pairs,'planned_count'),coassigned_weight:matrix(ids,pairs,'coassigned_weight'),
      assigned_both_weight:matrix(ids,pairs,'assigned_both_weight'),planned_weight:matrix(ids,pairs,'planned_weight'),
      assignment_coverage:matrix(ids,pairs,'assignment_coverage')},
    pairs, family_weight_audit:familyWeightAudit,
    uncertainty:{unit:base.cohort.source_group_unit, source_groups:x.sourceGroups.length,
      design:sourceResamples ? 'grouped_refits_descriptive_spread' : 'not_estimated',
      pairwise:uncertaintyRows},
    reproducible_groups:groups.groups, source_restricted_groups:groups.source_restricted_groups,
    ambiguous_members:groups.ambiguous, ungrouped_observations:unassigned,
    unsupported_pair_ledger:groups.unsupported, thresholds:groups.thresholds,
    sensitivity_report:sensitivity, individual_method_comparisons:comparisons,
    limitations:[
      'Co-assignment frequencies are conditional descriptive fit agreement, not calibrated probabilities of diplomacy, country positions, alliances, or coalitions.',
      'Noise/unassigned and failed/missing pairs do not enter assigned-both denominators; planned weight and omitted counts remain visible.',
      'Grouped refit percentiles measure resampling sensitivity, not confidence or independent external replication.',
      'Stable nuisance-driven partitions may persist; no null significance or universal best-model claim is made.',
      'Selection, source-genre, representation, and configuration-search effects remain potential confounders.'
    ]};
}
function toInterchangeV1(input, consensus, options = {}) {
  validateEnvelope(input);
  check(consensus.schema === 'un.consensus.v1' && consensus.publication_eligible === false, 'invalid consensus output');
  check(stable(consensus.source.observation_keys.map(r => [r.id, r.text_sha256])) ===
    stable(input.observations.filter(o => o.source_status === 'available' && !o.exclusion_reasons.length)
      .sort((a, b) => a.id.localeCompare(b.id)).map(r => [r.id, r.text_sha256])), 'consensus source-key mismatch');
  const modelId = options.model_id || 'w2-consensus-0.1.0';
  const groups = new Map(consensus.reproducible_groups.flatMap((g, i) => g.members.map(id => [id, i + 1])));
  const observations = input.observations.map(o => structuredClone(o)), eligible = observations.filter(o => o.source_status === 'available' && !o.exclusion_reasons.length);
  const rows = observations.map(o => {
    const eligibleRow = o.source_status === 'available' && !o.exclusion_reasons.length;
    const cluster = eligibleRow ? groups.get(o.id) || 0 : null;
    return {model_id:modelId,observation_id:o.id,status:eligibleRow ? cluster ? 'assigned' : 'unassigned' : 'excluded',
      cluster,membership_kind:'none',memberships:null,membership_strength:null,
      representation_basis_id:'w2-hard-assignment-identity-join-v1',
      reason:eligibleRow ? cluster ? null : 'No sufficiently supported descriptive group' : o.exclusion_reasons.join('; ') || o.missing_reason || 'Source unavailable'};
  });
  const assigned = rows.filter(r => r.status === 'assigned').length;
  const limits = consensus.limitations.map((description, i) => ({code:'w2_limit_' + (i + 1), scope:'consensus',description}));
  const output = {schema:'un.parallel-analysis.v1', contract_version:'1.0.0',
    producer:{workstream_id:'W2', adapter_version:VERSION,code_sha256:options.code_sha256 || digest(VERSION),
      runtime:options.runtime || 'node-22',generated_at:options.generated_at || new Date().toISOString(),
      fixture_kind:input.producer.fixture_kind},
    upstream:structuredClone(input.upstream),cohort:structuredClone(input.cohort),observations,
    models:[{model_id:modelId,method_family:'ensemble',method:'descriptive_complete_link_consensus',
      representation_id:'w2-hard-assignment-identity-join-v1', representation_version:VERSION, fit_version:VERSION,
      fit_split:input.cohort.split,parameters_sha256:digest(consensus.thresholds),
      training_selection_sha256:input.upstream.selection_sha256,diagnostic_basis:'descriptive conditional hard co-assignment'}],
    results:rows,
    coverage:{inventory_meetings:input.coverage.inventory_meetings,observations_total:observations.length,
      eligible:eligible.length,excluded:observations.length - eligible.length,unavailable_sources:input.coverage.unavailable_sources,
      models:[{model_id:modelId,eligible:eligible.length,assigned,unassigned:eligible.length-assigned,
        not_fitted:0,excluded:observations.length-eligible.length,attempted_fits:1,successful_fits:1,failed_fits:0}],
      failure_ledger:[]},
    evidence:[],diagnostics:[{model_id:modelId,name:'pairwise_opportunities',
      value:consensus.pairs.filter(p => p.observation_a !== p.observation_b).length,
      denominator:null,unit:'observation_pairs',status:'descriptive',reason:null},
      {model_id:modelId,name:'confirmed_inferential_evidence',value:null,denominator:null,
        unit:'hypothesis_test',status:'withheld',reason:'No exchangeability-valid, null-calibrated test.'}],
    limitations:limits,publication_eligible:false,evaluation_role:'engineering_only'};
  validateEnvelope(output);
  return output;
}
module.exports = {VERSION, validateEnvelope, extract, weightsFor, pairFor, ari, runConsensus, toInterchangeV1};
