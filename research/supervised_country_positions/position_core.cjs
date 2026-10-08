'use strict';

/*
 * Source-bound, descriptive country-position aggregation.
 *
 * IMPORTANT: This module never fits M12/M17, authenticates diplomatic actors,
 * assigns political allegiance, or publishes empirical position results.
 * Its only executable input class is synthetic_engineering.
 */
const { createHash } = require('node:crypto');
const SCHEMA = 'un.country-positions.evidence.v1';
const REPORT_SCHEMA = 'un.country-positions.report.v1';
const STANCES = Object.freeze(['support', 'oppose', 'conditional', 'descriptive', 'insufficient']);
const SUBSTANTIVE = new Set(['support', 'oppose']);
const ID = /^[a-z][a-z0-9_-]{2,79}$/;
const SHA = /^[a-f0-9]{64}$/;
const ISO = /^[A-Z]{3}$/;

function requireThat(value, message) {
  if (!value) throw new Error(message);
}
function uniq(values) {
  return [...new Set(values)];
}
function keyOf(...values) {
  return JSON.stringify(values);
}
function validDate(date) {
  return typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date) &&
    !Number.isNaN(Date.parse(date)) && new Date(date + 'T00:00:00Z').toISOString().slice(0, 10) === date;
}
function validUrl(url) {
  if (url === null) return true;
  if (typeof url !== 'string' || !url.startsWith('https://')) return false;
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' && Boolean(parsed.hostname) &&
      !parsed.username && !parsed.password;
  } catch {
    return false;
  }
}
function validateCodebook(codebook) {
  requireThat(codebook && codebook.schema === 'un.country-positions.propositions.v1',
    'Expected proposition codebook v1');
  requireThat(codebook.release_status === 'draft' && codebook.publication_eligible === false,
    'Codebook must remain an unpublished draft');
  requireThat(Array.isArray(codebook.propositions) && codebook.propositions.length >= 2 &&
    codebook.propositions.length <= 100, 'Invalid proposition count');
  const seen = new Set();
  for (const row of codebook.propositions) {
    requireThat(row && ID.test(row.proposition_id) && ID.test(row.issue_id) &&
      typeof row.version === 'string' && /^\d+\.\d+\.\d+$/.test(row.version),
    'Invalid proposition identity/version');
    requireThat(!seen.has(row.proposition_id), 'Duplicate proposition ID');
    seen.add(row.proposition_id);
    for (const field of ['target', 'proposition', 'scope', 'exclusion_rule']) {
      requireThat(typeof row[field] === 'string' && row[field].trim().length >= 8,
        'Proposition missing ' + field);
    }
    requireThat(row.review_status === 'draft', 'Unreviewed propositions must remain draft');
  }
  return new Map(codebook.propositions.map(row => [row.proposition_id, row]));
}

/**
 * The frame intentionally has no real-data escape hatch.
 * All source and observation identifiers must be source-bound; their supplied
 * hashes are checked for shape here. Upstream ingestion verifies actual bytes.
 */
function validateFrame(frame, codebook) {
  const propositions = validateCodebook(codebook);
  requireThat(frame && frame.schema === SCHEMA, 'Unknown position frame schema');
  requireThat(frame.dataset_kind === 'synthetic_engineering' &&
    frame.evaluation_role === 'engineering_only' &&
    frame.publication_eligible === false &&
    frame.daily_adapter_integrated === false,
  'Real/unreviewed/approved/published frames are not eligible for this prototype');
  requireThat(frame.codebook_version === codebook.version, 'Codebook version mismatch');
  requireThat(frame.source_schema === 'un.review.v1' ||
    frame.source_schema === 'un.browser.corpus.v1' ||
    frame.source_schema === 'un.passage-corpus.v1',
  'Unrecognized upstream source contract');
  requireThat(Array.isArray(frame.sources) && frame.sources.length > 0 &&
    frame.sources.length <= 1000, 'Invalid source count');
  requireThat(Array.isArray(frame.observations) &&
    frame.observations.length <= 10000, 'Invalid observation count');
  const sources = new Map();
  const familyOwners = new Map();
  for (const source of frame.sources) {
    requireThat(source && typeof source.source_id === 'string' &&
      source.source_id.length > 0 && !sources.has(source.source_id),
    'Missing or duplicate source ID');
    requireThat(ISO.test(source.iso3) && typeof source.name === 'string' &&
      source.name.trim(), 'Invalid recorded country affiliation');
    requireThat(validDate(source.date), 'Invalid source date');
    requireThat(SHA.test(source.text_sha256), 'Missing/invalid canonical text hash');
    requireThat(typeof source.text === 'string' &&
      createHash('sha256').update(source.text, 'utf8').digest('hex') === source.text_sha256,
      'Full synthetic original text does not match its declared SHA-256');
    requireThat(typeof source.source_family_id === 'string' && source.source_family_id,
      'Source family required to prevent duplicate speech counting');
    requireThat(typeof source.language === 'string' && source.language &&
      typeof source.genre === 'string' && source.genre, 'Missing source language/genre');
    requireThat(['individual', 'collective', 'unresolved'].includes(source.attribution),
      'Unknown individual/collective attribution');
    requireThat(['available', 'unavailable', 'unverified'].includes(source.source_status),
      'Unknown source availability');
    requireThat(validUrl(source.source_url === undefined ? null : source.source_url),
      'Source URL must be HTTPS, with no embedded credentials');
    const owner = keyOf(source.iso3, source.date.slice(0, 4), source.genre);
    const previous = familyOwners.get(source.source_family_id);
    requireThat(previous === undefined || previous === owner,
      'Source family crosses country, year, or genre');
    familyOwners.set(source.source_family_id, owner);
    sources.set(source.source_id, source);
  }
  const observationIds = new Set();
  for (const observation of frame.observations) {
    requireThat(observation && typeof observation.observation_id === 'string' &&
      observation.observation_id && !observationIds.has(observation.observation_id),
    'Missing or duplicate observation ID');
    observationIds.add(observation.observation_id);
    requireThat(sources.has(observation.source_id), 'Observation has unknown source');
    requireThat(propositions.has(observation.proposition_id),
      'Observation refers to unversioned/unknown proposition');
    requireThat(STANCES.includes(observation.stance),
      'Observation has unrecognized stance; absence is not opposition');
    requireThat(observation.review_status === 'synthetic_label',
      'Real, unreviewed or assistant-provisional labels cannot enter prototype');
    requireThat(typeof observation.passage_id === 'string' && observation.passage_id,
      'Source passage ID required');
    requireThat(typeof observation.quote === 'string' &&
      observation.quote.length > 0 && observation.quote.length <= 3000,
      'Synthetic source quotation required for evidence inspection');
    requireThat(Number.isSafeInteger(observation.start) &&
      Number.isSafeInteger(observation.end) &&
      observation.start >= 0 && observation.end > observation.start,
      'Expected Unicode-codepoint source offsets');
    const parent = sources.get(observation.source_id);
    if (typeof parent.text === 'string') {
      const cps = Array.from(parent.text);
      requireThat(observation.end <= cps.length &&
        cps.slice(observation.start, observation.end).join('') === observation.quote,
        'Evidence quote does not match the original source at declared offsets');
    } else {
      requireThat(false, 'Synthetic fixture requires full original text to verify offsets');
    }
  }
  return { propositions, sources };
}

function reduceStances(values) {
  const distinct = uniq(values);
  if (distinct.length === 0) return { stance: null, reason: 'no_observed_statement' };
  const substantive = distinct.filter(value => SUBSTANTIVE.has(value));
  if (substantive.length === 1 &&
    !distinct.includes('conditional')) {
    return { stance: substantive[0], reason: null };
  }
  if (substantive.length > 1 ||
    (substantive.length && distinct.includes('conditional'))) {
    return { stance: null, reason: 'conflicting_or_conditional_evidence' };
  }
  if (distinct.includes('conditional')) return { stance: null, reason: 'conditional_only' };
  if (distinct.includes('descriptive')) return { stance: null, reason: 'descriptive_only' };
  return { stance: null, reason: 'insufficient_evidence' };
}

/*
 * Comparison unit: country x year x proposition, with a speech/source family
 * contributing once regardless of the number of repeated excerpts/translations.
 * Cross-family conflicting positions remain withheld rather than majority-voted.
 */
function summarize(frame, codebook, options = {}) {
  const { propositions, sources } = validateFrame(frame, codebook);
  const minShared = options.min_shared_propositions === undefined ?
    2 : options.min_shared_propositions;
  requireThat(Number.isSafeInteger(minShared) && minShared >= 2 &&
    minShared <= propositions.size, 'Invalid minimum shared propositions');

  const eligible = new Map();
  const excludedObservations = [];
  for (const row of frame.observations) {
    const source = sources.get(row.source_id);
    if (source.source_status !== 'available' || source.attribution !== 'individual') {
      excludedObservations.push({
        observation_id: row.observation_id,
        reason: source.source_status !== 'available' ?
          'source_not_verified_available' : 'not_individual_country_attribution'
      });
      continue;
    }
    const group = keyOf(source.iso3, source.date.slice(0, 4),
      row.proposition_id, source.source_family_id);
    if (!eligible.has(group)) eligible.set(group, []);
    eligible.get(group).push(row);
  }

  const byCell = new Map();
  const evidence = [];
  for (const [groupKey, rows] of eligible) {
    const first = rows[0];
    const source = sources.get(first.source_id);
    const cellKey = keyOf(source.iso3, source.date.slice(0, 4), first.proposition_id);
    const family = JSON.parse(groupKey)[3];
    const outcome = reduceStances(rows.map(row => row.stance));
    if (!byCell.has(cellKey)) byCell.set(cellKey, []);
    byCell.get(cellKey).push({ family, ...outcome, observation_ids: rows.map(row => row.observation_id) });
    for (const row of rows) {
      const record = sources.get(row.source_id);
      evidence.push({
        observation_id: row.observation_id, passage_id: row.passage_id,
        proposition_id: row.proposition_id, iso3: record.iso3,
        year: Number(record.date.slice(0, 4)), stance: row.stance,
        source_id: row.source_id, source_family_id: record.source_family_id,
        text_sha256: record.text_sha256, source_url: record.source_url || null,
        start: row.start, end: row.end, quote: row.quote,
        verification: 'synthetic_only'
      });
    }
  }

  const countries = new Map();
  for (const source of sources.values()) {
    const id = keyOf(source.iso3, source.date.slice(0, 4));
    requireThat(!countries.has(id) || countries.get(id).name === source.name,
      'Conflicting recorded affiliation names within country-year');
    countries.set(id, {
      iso3: source.iso3, name: source.name,
      year: Number(source.date.slice(0, 4))
    });
  }

  const profiles = [];
  for (const actor of countries.values()) {
    for (const proposition of propositions.values()) {
      const cellKey = keyOf(actor.iso3, String(actor.year), proposition.proposition_id);
      const groups = byCell.get(cellKey) || [];
      // A null family stance retains its specific absence/conflict reason;
      // do not silently relabel descriptive-only or insufficient as conditional.
      const positionStances = uniq(groups.map(group => group.stance).filter(Boolean));
      const blockers = uniq(groups.map(group => group.reason).filter(Boolean));
      let stance = null;
      let reason = 'no_observed_statement';
      if (groups.length > 0) {
        if (blockers.includes('conflicting_or_conditional_evidence') ||
            positionStances.length > 1 ||
            (positionStances.length > 0 && blockers.includes('conditional_only'))) {
          reason = 'conflicting_or_conditional_evidence';
        } else if (positionStances.length === 1) {
          stance = positionStances[0];
          reason = null;
        } else if (blockers.includes('conditional_only')) {
          reason = 'conditional_only';
        } else if (blockers.includes('descriptive_only')) {
          reason = 'descriptive_only';
        } else {
          reason = 'insufficient_evidence';
        }
      }
      const observationIds = uniq(groups.flatMap(group => group.observation_ids));
      profiles.push({
        ...actor, proposition_id: proposition.proposition_id,
        issue_id: proposition.issue_id,
        stance, reason,
        source_family_count: groups.length, evidence_ids: observationIds
      });
    }
  }

  const edges = [];
  const byYear = new Map();
  for (const p of profiles) {
    if (!byYear.has(p.year)) byYear.set(p.year, new Map());
    if (!byYear.get(p.year).has(p.iso3)) byYear.get(p.year).set(p.iso3, []);
    byYear.get(p.year).get(p.iso3).push(p);
  }
  for (const [year, actors] of byYear) {
    const ids = [...actors.keys()].sort();
    for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
      const aa = new Map(actors.get(ids[i]).map(p => [p.proposition_id, p]));
      const bb = new Map(actors.get(ids[j]).map(p => [p.proposition_id, p]));
      const common = [...propositions.keys()].filter(prop =>
        aa.get(prop).stance !== null && bb.get(prop).stance !== null);
      if (common.length < minShared) continue;
      const agreements = common.filter(prop => aa.get(prop).stance === bb.get(prop).stance);
      const disagreements = common.filter(prop => aa.get(prop).stance !== bb.get(prop).stance);
      edges.push({
        year, country_a: ids[i], country_b: ids[j],
        agreement_count: agreements.length, disagreement_count: disagreements.length,
        comparable_propositions: common.length, possible_propositions: propositions.size,
        agreement_share: agreements.length / common.length,
        agreement_balance: (agreements.length - disagreements.length) / common.length,
        shared_proposition_ids: common,
        evidence_ids: uniq(common.flatMap(prop => [
          ...aa.get(prop).evidence_ids, ...bb.get(prop).evidence_ids
        ]))
      });
    }
  }
  const report = {
    schema: REPORT_SCHEMA, dataset_kind: 'synthetic_engineering',
    evaluation_role: 'engineering_only', publication_eligible: false,
    daily_adapter_integrated: false, model_fitted: false,
    method_reference: ['M12', 'M17'],
    interpretation: 'Agreement on explicitly matched policy propositions, not influence, alliances, or a measure of overall diplomatic allegiance',
    codebook_version: codebook.version, min_shared_propositions: minShared,
    propositions: codebook.propositions.map(row => ({
      proposition_id: row.proposition_id, issue_id: row.issue_id,
      version: row.version, proposition: row.proposition
    })),
    countries: [...countries.values()].sort((a, b) =>
      a.year - b.year || a.iso3.localeCompare(b.iso3)),
    profiles, edges, evidence,
    coverage: {
      total_sources: frame.sources.length, total_observations: frame.observations.length,
      retained_observations: evidence.length,
      excluded_observations: excludedObservations.length,
      excluded_ledger: excludedObservations,
      source_families_retained: uniq(evidence.map(e => e.source_family_id)).length,
      evaluated_country_year_proposition_cells: profiles.length,
      comparable_pairs: edges.length
    },
    limitations: [
      'Entirely fictional synthetic engineering fixture; no real country positions inferred.',
      'No fitted supervised model, human gold annotations, calibration, or independent evaluation.',
      'Agreement edges are descriptive and have no confidence interval or causal meaning.',
      'Missing sources and unmentioned propositions are not opposition, neutrality, or zero.',
      'Only individually attributed statements can enter aggregation; group statements are withheld.',
      'Repeated excerpts and translated duplicates share one source-family counting opportunity.'
    ]
  };
  return report;
}
function validateReport(report) {
  requireThat(report && report.schema === REPORT_SCHEMA &&
    report.dataset_kind === 'synthetic_engineering' &&
    report.evaluation_role === 'engineering_only' &&
    report.publication_eligible === false &&
    report.daily_adapter_integrated === false &&
    report.model_fitted === false, 'Visualization accepts synthetic-only, unpublished, unfitted reports');
  for (const key of ['propositions', 'countries', 'profiles', 'edges', 'evidence']) {
    requireThat(Array.isArray(report[key]), 'Missing report array: ' + key);
  }
  for (const e of report.edges) {
    requireThat(e.comparable_propositions >= 2 &&
      e.comparable_propositions === e.agreement_count + e.disagreement_count &&
      e.agreement_share >= 0 && e.agreement_share <= 1 &&
      Math.abs((e.agreement_count / e.comparable_propositions) - e.agreement_share) < 1e-10,
    'Malformed synthetic edge accounting');
  }
  return true;
}
module.exports = {
  SCHEMA, REPORT_SCHEMA, STANCES, validateCodebook, validateFrame,
  summarize, validateReport, reduceStances
};
