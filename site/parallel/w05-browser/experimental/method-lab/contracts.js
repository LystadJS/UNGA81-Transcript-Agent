/* Experimental W5 read contract. No replacement for the coordinator's v1 schema. */
(function (root) {
  'use strict';

  const SCHEMA = 'un.parallel-analysis.v1';
  const VERSION = '1.0.0';
  const MAX_ROWS = 600;
  const MAX_ARCHIVE_BYTES = 128 * 1024 * 1024;
  const SHA = /^[a-f0-9]{64}$/;
  const STATUSES = new Set(['assigned', 'unassigned', 'not_fitted', 'excluded']);
  const MEMBERSHIPS = new Set(['none', 'gmm_responsibility', 'nmf_share', 'hdbscan_strength', 'consensus_frequency']);
  const SPLITS = new Set(['synthetic', 'development']);
  const UNAVAILABLE = new Set(['unavailable', 'failed', 'excluded_language', 'empty_transcript', 'inventory_failed']);

  function check(ok, message) {
    if (!ok) throw new Error(message);
  }
  function object(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }
  function nonempty(value) {
    return typeof value === 'string' && value.trim().length > 0;
  }
  function uint(value) {
    return Number.isSafeInteger(value) && value >= 0;
  }
  function sha(value, nullable) {
    return (nullable && value === null) || (typeof value === 'string' && SHA.test(value));
  }
  function countBy(rows, status) {
    return rows.filter(row => row.status === status).length;
  }
  function sameArray(left, right) {
    return left.length === right.length && left.every((value, index) => value === right[index]);
  }
  function identity(row) {
    return row.id + '\u0000' + String(row.text_sha256);
  }
  function requireFields(value, fields, label) {
    check(object(value) && fields.every(field => Object.hasOwn(value, field)), label + ' is missing required fields.');
  }
  function version(value) {
    if (value === VERSION) return {supported: true, value};
    if (typeof value === 'string' && /^1\.\d+\.\d+$/.test(value)) {
      throw new Error('Interchange ' + value + ' requires an explicit compatibility review; supported: ' + VERSION + '.');
    }
    throw new Error('Unsupported interchange version: ' + String(value) + '.');
  }

  function validateParallel(doc) {
    requireFields(doc, ['schema', 'contract_version', 'producer', 'upstream', 'cohort', 'observations',
      'models', 'results', 'coverage', 'evidence', 'diagnostics', 'limitations',
      'publication_eligible', 'evaluation_role'], 'Interchange');
    check(doc.schema === SCHEMA, 'Not an un.parallel-analysis.v1 envelope.');
    version(doc.contract_version);
    check(doc.publication_eligible === false && doc.evaluation_role === 'engineering_only',
      'Engineering-only publication/evaluation flags cannot be loosened.');
    const producer = doc.producer, upstream = doc.upstream, cohort = doc.cohort, coverage = doc.coverage;
    requireFields(producer, ['workstream_id', 'adapter_version', 'code_sha256', 'runtime', 'generated_at', 'fixture_kind'], 'Producer');
    requireFields(upstream, ['source_schema', 'source_engine', 'source_hash_basis', 'source_sha256',
      'selection_sha256', 'frame_sha256', 'corpus_sha256', 'review_sha256', 'missing_reason'], 'Upstream');
    requireFields(cohort, ['split', 'population', 'unit', 'selection_policy', 'weighting', 'source_group_unit',
      'duplicate_policy', 'total_in_frame', 'eligible'], 'Cohort');
    requireFields(coverage, ['inventory_meetings', 'observations_total', 'eligible', 'excluded',
      'unavailable_sources', 'models', 'failure_ledger'], 'Coverage');
    check(['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7'].includes(producer.workstream_id) &&
      sha(producer.code_sha256) && nonempty(producer.adapter_version) && nonempty(producer.runtime) &&
      ['synthetic', 'private_development'].includes(producer.fixture_kind), 'Invalid producer identity.');
    check(SPLITS.has(cohort.split) &&
      (cohort.split === 'synthetic') === (producer.fixture_kind === 'synthetic'),
      'Synthetic and private-development provenance cannot be mixed.');
    check(['un.browser.corpus.v1', 'un.latent-comparison.v1', 'un.passage-corpus.v1',
      'un.review.v1', 'synthetic.v1'].includes(upstream.source_schema), 'Unknown source schema.');
    check(['utf8_corpus_export', 'raw_response_bytes', 'utf8_response_text', 'canonical_source_text',
      'source_text_file_bytes', 'synthetic'].includes(upstream.source_hash_basis), 'Unknown source hash basis.');
    check(['source_segment', 'passage', 'reviewed_speech', 'parent', 'country_period', 'synthetic'].includes(cohort.unit),
      'Unsupported observation unit.');
    check(['equal_passage', 'equal_meeting', 'equal_speech', 'equal_country', 'none'].includes(cohort.weighting),
      'Unsupported weighting policy.');
    for (const field of ['source_sha256', 'selection_sha256', 'frame_sha256', 'corpus_sha256', 'review_sha256']) {
      check(sha(upstream[field], true), 'Invalid ' + field + '.');
    }
    check(upstream.source_sha256 !== null || nonempty(upstream.missing_reason),
      'Unknown source hash requires an explicit missing reason.');
    check(cohort.split !== 'synthetic' || upstream.source_schema === 'synthetic.v1',
      'Synthetic example must declare a synthetic source schema.');
    check(Array.isArray(doc.observations) && doc.observations.length <= MAX_ROWS &&
      Array.isArray(doc.models) && doc.models.length <= 24 && Array.isArray(doc.results) &&
      Array.isArray(doc.evidence) && Array.isArray(doc.diagnostics) && Array.isArray(doc.limitations),
      'Malformed or over-limit analytical arrays; no sampling is allowed.');
    check(uint(cohort.eligible) && cohort.eligible <= MAX_ROWS && uint(cohort.total_in_frame) &&
      uint(coverage.observations_total) && uint(coverage.eligible) && uint(coverage.excluded) &&
      uint(coverage.inventory_meetings) && uint(coverage.unavailable_sources),
      'Invalid population denominators.');
    check(cohort.eligible === coverage.eligible && coverage.observations_total === doc.observations.length &&
      coverage.eligible + coverage.excluded === doc.observations.length &&
      cohort.total_in_frame >= coverage.observations_total,
      'Source frame / eligible / excluded counts do not reconcile.');
    check(Array.isArray(coverage.models) && Array.isArray(coverage.failure_ledger),
      'Missing coverage model or failure ledger.');
    const obs = new Map(), excluded = new Set();
    for (const row of doc.observations) {
      requireFields(row, ['id', 'text_sha256', 'parent_id', 'parent_text_sha256', 'meeting_id',
        'speech_id', 'source_family_id', 'date', 'country', 'source_url', 'json_pointer',
        'start', 'end', 'unit', 'review_status', 'exclusion_reasons', 'source_status', 'missing_reason'], 'Observation');
      check(nonempty(row.id) && !obs.has(row.id) && sha(row.text_sha256, true) &&
        row.unit === cohort.unit && /^\d{4}-\d{2}-\d{2}$/.test(row.date), 'Invalid/duplicate observation identity.');
      check(Array.isArray(row.exclusion_reasons) && row.exclusion_reasons.every(nonempty),
        'Invalid exclusion ledger for ' + row.id + '.');
      check(row.source_url === null || (typeof row.source_url === 'string' && /^https:\/\//.test(row.source_url)),
        'Source pointer must use HTTPS.');
      check((row.start === null && row.end === null) ||
        (uint(row.start) && uint(row.end) && row.end > row.start),
      'Invalid Unicode source span for ' + row.id + '.');
      check(['available', ...UNAVAILABLE].includes(row.source_status), 'Invalid source status.');
      check(['confirmed', 'pending', 'provisional', 'unreviewed', 'not_applicable'].includes(row.review_status),
        'Invalid review status.');
      if (UNAVAILABLE.has(row.source_status)) {
        check(nonempty(row.missing_reason) && row.exclusion_reasons.length > 0,
          'Unavailable source must remain missing and excluded.');
      }
      if (row.exclusion_reasons.length) excluded.add(row.id);
      else check(row.source_status === 'available', 'Non-available source counted as eligible.');
      obs.set(row.id, row);
    }
    check(excluded.size === coverage.excluded, 'Excluded source denominator differs from observations.');
    const models = new Map();
    for (const model of doc.models) {
      requireFields(model, ['model_id', 'method_family', 'method', 'representation_id', 'representation_version',
        'fit_version', 'fit_split', 'parameters_sha256', 'training_selection_sha256', 'diagnostic_basis'], 'Model');
      check(nonempty(model.model_id) && !models.has(model.model_id) && nonempty(model.method) &&
        nonempty(model.method_family) && nonempty(model.representation_id) &&
        nonempty(model.representation_version) && nonempty(model.fit_version) &&
        model.fit_split === cohort.split && sha(model.parameters_sha256) &&
        sha(model.training_selection_sha256, true), 'Invalid model version/identity.');
      models.set(model.model_id, model);
    }
    check(new Set(coverage.models.map(row => row.model_id)).size === models.size &&
      coverage.models.length === models.size &&
      coverage.models.every(row => models.has(row.model_id)), 'Coverage must contain exactly one row per model.');
    const byModel = new Map([...models.keys()].map(id => [id, new Map()]));
    for (const row of doc.results) {
      requireFields(row, ['model_id', 'observation_id', 'status', 'cluster', 'membership_kind', 'memberships',
        'membership_strength', 'representation_basis_id', 'reason'], 'Assignment');
      const model = models.get(row.model_id), source = obs.get(row.observation_id);
      check(model && source && STATUSES.has(row.status) && MEMBERSHIPS.has(row.membership_kind),
        'Orphan/invalid analytical result.');
      check(!byModel.get(row.model_id).has(row.observation_id), 'Duplicate model–observation assignment.');
      check(row.representation_basis_id === model.representation_id, 'Representation identity drift.');
      check(excluded.has(row.observation_id) === (row.status === 'excluded'),
        'An excluded observation cannot be silently fitted or vice versa.');
      if (row.status === 'assigned') {
        check(Number.isSafeInteger(row.cluster) && row.cluster >= 1, 'Assigned result needs a positive cluster.');
      } else if (row.status === 'unassigned') {
        check(row.cluster === 0, 'Unassigned result requires explicit cluster 0.');
      } else {
        check(row.cluster === null && nonempty(row.reason), 'Unfitted/excluded result needs a null cluster and reason.');
      }
      if (row.membership_kind === 'none') {
        check(row.memberships === null && row.membership_strength === null, 'Unexpected memberships on hard fit.');
      } else if (['gmm_responsibility', 'nmf_share'].includes(row.membership_kind)) {
        check(row.status === 'assigned' && Array.isArray(row.memberships) &&
          row.memberships.length > 0 && row.memberships.length <= 600 &&
          row.memberships.every(v => Number.isFinite(v) && v >= 0 && v <= 1) &&
          Math.abs(row.memberships.reduce((a, b) => a + b, 0) - 1) < 1e-6 &&
          row.membership_strength === null, 'Invalid probabilistic/mixture vector.');
      } else if (row.membership_kind === 'hdbscan_strength') {
        check(row.memberships === null && row.membership_strength !== null &&
          Number.isFinite(row.membership_strength) && row.membership_strength >= 0 &&
          row.membership_strength <= 1, 'Invalid HDBSCAN strength.');
      } else {
        check(row.memberships === null && row.membership_strength === null,
          'Consensus frequency requires separate pair-opportunity diagnostics, not invented point probabilities.');
        check(doc.diagnostics.some(d => d.model_id === row.model_id && /opportunit|denominator|pair/i.test(d.name)),
          'Consensus fit lacks pair-opportunity accounting.');
      }
      byModel.get(row.model_id).set(row.observation_id, row);
    }
    for (const row of coverage.models) {
      const modelRows = byModel.get(row.model_id);
      check(modelRows.size === obs.size && uint(row.eligible) && row.eligible === coverage.eligible &&
        uint(row.assigned) && uint(row.unassigned) && uint(row.not_fitted) && uint(row.excluded) &&
        row.assigned + row.unassigned + row.not_fitted === coverage.eligible &&
        row.excluded === coverage.excluded, 'Model coverage is incomplete.');
      for (const status of STATUSES) {
        check(row[status] === countBy([...modelRows.values()], status),
          'Coverage mismatch for ' + row.model_id + ': ' + status + '.');
      }
      check(uint(row.attempted_fits) && uint(row.successful_fits) && uint(row.failed_fits) &&
        row.attempted_fits >= row.successful_fits + row.failed_fits,
        'Fit attempts/failures do not reconcile.');
      check(!row.assigned || row.successful_fits > 0, 'Assignments exist without a successful fit.');
    }
    for (const failure of coverage.failure_ledger) {
      requireFields(failure, ['model_id', 'attempt', 'status', 'reason'], 'Failure');
      check(models.has(failure.model_id) && uint(failure.attempt) &&
        ['failed', 'skipped', 'timed_out', 'nonconverged'].includes(failure.status) &&
        nonempty(failure.reason), 'Invalid failure ledger entry.');
    }
    for (const ev of doc.evidence) {
      requireFields(ev, ['observation_id', 'source_url', 'json_pointer', 'start', 'end', 'role', 'proposition_id', 'verification'], 'Evidence');
      const source = obs.get(ev.observation_id);
      check(source && (ev.source_url === null || ev.source_url === source.source_url) &&
        (ev.start === null && ev.end === null ||
          (uint(ev.start) && uint(ev.end) && ev.end > ev.start)) &&
        ['representative', 'contrary', 'ambiguous', 'context'].includes(ev.role) &&
        ['source_linked', 'provisional', 'human_confirmed', 'unresolved', 'synthetic'].includes(ev.verification),
        'Evidence source, span, or verification is inconsistent.');
    }
    for (const d of doc.diagnostics) {
      requireFields(d, ['model_id', 'name', 'value', 'denominator', 'unit', 'status', 'reason'], 'Diagnostic');
      check((d.model_id === null || models.has(d.model_id)) && nonempty(d.name) &&
        (d.denominator === null || uint(d.denominator)) &&
        (d.value === null || typeof d.value === 'string' || Number.isFinite(d.value)) &&
        ['descriptive', 'validated', 'withheld', 'inconclusive', 'failed', 'not_run'].includes(d.status),
        'Invalid method diagnostic.');
    }
    check(doc.limitations.length > 0 && doc.limitations.every(row =>
      object(row) && nonempty(row.code) && nonempty(row.scope) && nonempty(row.description)),
    'Interpretive limitations cannot be omitted.');
    return doc;
  }

  function fromParallel(doc) {
    validateParallel(doc);
    const items = doc.observations.map(r => ({
      id:r.id, text_sha256:r.text_sha256, parent_id:r.parent_id,
      meeting_id:r.meeting_id, country:r.country, date:r.date,
      source_url:r.source_url, start:r.start, end:r.end, source_status:r.source_status,
      missing_reason:r.missing_reason, exclusion_reasons:r.exclusion_reasons
    }));
    const modelRows = new Map(doc.models.map(m => [m.model_id, []]));
    for (const row of doc.results) modelRows.get(row.model_id).push(row);
    return {
      kind:'parallel', envelope:doc, source:{
        schema:doc.upstream.source_schema, hash:doc.upstream.source_sha256,
        hash_basis:doc.upstream.source_hash_basis, selection_hash:doc.upstream.selection_sha256,
        unit:doc.cohort.unit, split:doc.cohort.split
      },
      observations:items, coverage:doc.coverage, limitations:doc.limitations,
      models:doc.models.map(m => ({
        id:m.model_id, label:m.method + ' / ' + m.model_id, family:m.method_family, method:m.method,
        representation:m.representation_id, representation_version:m.representation_version,
        fit_version:m.fit_version, settings_hash:m.parameters_sha256, execution:'offline_only',
        coverage:doc.coverage.models.find(c => c.model_id === m.model_id),
        diagnostics:doc.diagnostics.filter(d => d.model_id === m.model_id),
        rows:modelRows.get(m.model_id)
      }))
    };
  }

  function population(view) {
    return view.observations.map(identity).sort();
  }
  function compare(left, right, leftModelId, rightModelId) {
    const a = left.models.find(m => m.id === leftModelId);
    const b = right.models.find(m => m.id === rightModelId);
    check(a && b, 'Select valid comparison methods.');
    const identical = left.source.schema === right.source.schema &&
      left.source.hash === right.source.hash && left.source.hash !== null &&
      left.source.hash_basis === right.source.hash_basis &&
      left.source.selection_hash === right.source.selection_hash &&
      left.source.unit === right.source.unit &&
      left.source.split === right.source.split &&
      sameArray(population(left), population(right));
    const sameRepresentation = a.representation === b.representation &&
      a.representation_version === b.representation_version;
    const sameProtocol = sameRepresentation && a.family === b.family &&
      a.method === b.method && a.fit_version === b.fit_version &&
      a.settings_hash === b.settings_hash;
    const paired = identical && sameProtocol;
    return {
      identical_population:identical, same_representation:sameRepresentation, same_fit_protocol:sameProtocol,
      numerical_comparison_permitted:paired,
      paired_count:identical ? left.observations.length : 0,
      assigned_both:paired ? [...new Map(a.rows.map(r => [r.observation_id, r])).keys()].filter(id =>
        a.rows.find(r => r.observation_id === id)?.status === 'assigned' &&
        b.rows.find(r => r.observation_id === id)?.status === 'assigned').length : null,
      reason:!identical ? 'Different source hash/basis, split, observation identity, unit or selection: comparison blocked.' :
        !sameRepresentation ? 'Identical sources but representation geometry differs; display only.' :
        !sameProtocol ? 'Same source and representation, but algorithm or fit settings/version differ; side-by-side only.' :
        'Matching fit protocol; descriptive paired inspection only, not inferential evidence.'
    };
  }

  const api={SCHEMA, VERSION, MAX_ROWS, MAX_ARCHIVE_BYTES, validateParallel, fromParallel, compare, population};
  if (typeof module !== 'undefined' && module.exports) module.exports=api;
  else root.UNMethodLabContracts=api;
})(globalThis);
