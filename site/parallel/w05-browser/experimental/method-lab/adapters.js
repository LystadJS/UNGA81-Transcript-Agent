/* Source-bound, read-only adapters. Computational kernels remain upstream. */
(function (root) {
  'use strict';
  const C = typeof module !== 'undefined' && module.exports
    ? require('./contracts.js') : root.UNMethodLabContracts;
  const ARCHIVE = 'un.method-lab-saved-run.v1';
  const ARCHIVE_VERSION = '0.1.0';
  const METHODS = Object.freeze([
    {name:'PCA', id:'pca', availability:'browser_existing', detail:'Retained cluster score representation; not an independent political measure.'},
    {name:'LSA', id:'lsa', availability:'browser_existing', detail:'Uncentered TF-IDF SVD used by the existing cluster fitter.'},
    {name:'k-means / PAM / hierarchy / HDBSCAN / GMM', id:'clusters', availability:'browser_existing',
      detail:'Existing, bounded numerical engines; options validated upstream.'},
    {name:'NMF', id:'nmf', availability:'browser_existing', detail:'Nonnegative lexical mixtures; shares are not stance probabilities.'},
    {name:'Spectral clustering', id:'spectral', availability:'offline_only', detail:'Await W3 source/graph validation and coordinator integration.'},
    {name:'Diffusion maps', id:'diffusion', availability:'offline_only', detail:'Await W3 validated graph kernel and geometry.'},
    {name:'Consensus clustering', id:'consensus', availability:'offline_only', detail:'Await W2 family/denominator-aware validation.'},
    {name:'Longitudinal alignment', id:'longitudinal', availability:'offline_only', detail:'Await W4 temporal/source-aware validation.'},
    {name:'Local MiniLM', id:'minilm', availability:'feasibility_only', detail:'No model weights, tokenizer or network fetch in this lab.'}
  ]);
  const assert = (ok, message) => { if (!ok) throw new Error(message); };
  const hashString = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
  function utf8Length(text) {
    if (typeof TextEncoder !== 'undefined') return new TextEncoder().encode(text).byteLength;
    if (typeof Buffer !== 'undefined') return Buffer.byteLength(text, 'utf8');
    return unescape(encodeURIComponent(text)).length;
  }
  function digest() {
    if (root.crypto && root.crypto.subtle) return root.crypto.subtle;
    if (typeof require === 'function') return require('node:crypto').webcrypto.subtle;
    throw new Error('SHA-256 is unavailable; use HTTPS or localhost.');
  }
  async function sha256(text) {
    const bytes = new TextEncoder().encode(text);
    const hash = await digest().digest('SHA-256', bytes);
    return Array.from(new Uint8Array(hash), x => x.toString(16).padStart(2, '0')).join('');
  }
  function fixtureInformation(value) {
    if (value.schema === C.SCHEMA) return 'Validated v1 analytical envelope';
    if (value.schema === ARCHIVE) return 'Versioned method-lab saved run';
    if (value.schema === 'un.latent-saved-run.v1') return 'Legacy latent archive; original engine replay required';
    return 'Unsupported format: ' + String(value.schema);
  }
  function fromLegacy(restored) {
    assert(restored && restored.result && restored.result.schema === 'un.latent-comparison.v1' &&
      hashString(restored.result.source_hash) && hashString(restored.result.selection_hash),
    'Restore the source-checked legacy saved archive with UNLatent.restore first.');
    assert(Array.isArray(restored.result.entries) && restored.result.entries.length <= 24,
      'Invalid legacy fit inventory.');
    const source = {
      schema:'un.latent-comparison.v1', hash:restored.result.source_hash,
      hash_basis:restored.payload?.kind === 'reviewed' ? 'utf8_reviewed_bundle' : 'utf8_corpus_export',
      selection_hash:restored.result.selection_hash,
      unit:'mixed', split:'development_not_verified'
    };
    const byID = new Map(), models = [];
    for (const entry of restored.result.entries) {
      assert(['source', 'parent', 'excerpt'].includes(entry.unit) &&
        ['clusters', 'nmf'].includes(entry.method) &&
        Array.isArray(entry.result?.matched) && entry.result.matched.length <= C.MAX_ROWS,
      'Invalid legacy fit population.');
      const fit = entry.result.methods[entry.method];
      assert(fit, 'Missing saved fit.');
      const matched = new Map();
      for (const r of entry.result.matched) {
        assert(typeof r.id === 'string' && hashString(r.text_sha256) &&
          !matched.has(r.id), 'Missing/duplicate source-linked legacy observation.');
        matched.set(r.id, r);
        const key = entry.unit + '\u0000' + r.id;
        if (byID.has(key)) {
          assert(byID.get(key).text_sha256 === r.text_sha256, 'Conflicting source hash in saved fit.');
        } else byID.set(key, {
          id:key, text_sha256:r.text_sha256, original_id:r.id, unit:entry.unit,
          parent_id:r.parent_id || null, meeting_id:r.meeting_slug || null,
          date:r.date, country:r.country || null, source_url:r.source_url,
          start:r.start ?? null, end:r.end ?? null,
          source_status:'available', missing_reason:null, exclusion_reasons:[]
        });
      }
      const known = new Map((fit.points || []).map(row => [row.id, row]));
      assert(known.size === (fit.points || []).length, 'Duplicate legacy fit assignment.');
      const excluded = new Map((fit.excluded || []).map(row => [row.id, row.reason]));
      const rows = [];
      for (const r of matched.values()) {
        const key = entry.unit + '\u0000' + r.id, point = known.get(r.id);
        if (point) {
          assert(point.text_sha256 === r.text_sha256, 'Legacy point/source hash mismatch.');
          if (entry.method === 'clusters') {
            assert(Number.isSafeInteger(point.cluster) && point.cluster >= 0, 'Invalid hard cluster label.');
            const kind = Array.isArray(point.memberships) ? 'gmm_responsibility' :
              typeof point.membership_strength === 'number' ? 'hdbscan_strength' : 'none';
            rows.push({model_id:entry.id, observation_id:key, status:point.cluster ? 'assigned':'unassigned',
              cluster:point.cluster, membership_kind:kind,
              memberships:kind === 'gmm_responsibility' ? point.memberships : null,
              membership_strength:kind === 'hdbscan_strength' ? point.membership_strength : null,
              reason:null, score_coordinates:point[fit.representation] || null});
          } else {
            assert(point.shares === null || (Array.isArray(point.shares) &&
              point.shares.every(v => Number.isFinite(v) && v >= 0) &&
              Math.abs(point.shares.reduce((a, b) => a + b, 0) - 1) < 1e-6),
            'Invalid legacy NMF shares.');
            rows.push({model_id:entry.id, observation_id:key,
              status:point.shares ? 'mixture':'unassigned',
              cluster:null, membership_kind:point.shares ? 'nmf_share':'none',
              memberships:point.shares, membership_strength:null,
              reason:point.shares ? null:'Undefined mixture weights'});
          }
        } else {
          assert(fit.skipped || excluded.has(r.id), 'Legacy fit silently omitted source ' + r.id + '.');
          rows.push({model_id:entry.id, observation_id:key,
            status:excluded.has(r.id) ? 'excluded_from_fit':'not_fitted',
            cluster:null, membership_kind:'none', memberships:null,
            membership_strength:null, reason:excluded.get(r.id) || fit.skipped});
        }
      }
      models.push({
        id:entry.id, label:entry.label, family:entry.method === 'clusters' ? 'partition':'mixture',
        method:entry.method === 'clusters' ? (fit.algorithm || 'cluster') : 'nmf',
        representation:entry.method === 'clusters' ? fit.representation : 'tfidf-nonnegative',
        representation_version:restored.result.engine,
        fit_version:restored.result.engine,
        settings_hash:null, settings:fit.parameters || null, unit:entry.unit, execution:'browser_existing',
        coverage:{
          eligible:matched.size,
          assigned:rows.filter(r => r.status === 'assigned' || r.status === 'mixture').length,
          unassigned:rows.filter(r => r.status === 'unassigned').length,
          not_fitted:rows.filter(r => r.status === 'not_fitted').length,
          excluded:rows.filter(r => r.status === 'excluded_from_fit').length
        },
        diagnostics:fit.diagnostics || {}, rows
      });
    }
    return {
      kind:'legacy', source, observations:[...byID.values()],
      coverage:restored.result.counts,
      limitations:[{code:'legacy_replay', scope:'all',
        description:'Legacy replay verified source and saved population without numerical refitting. Hashes do not establish correctness or source authenticity.'}],
      models
    };
  }
  function compareLegacyPopulations(left, right, a, b) {
    // The same original source may contain multiple comparison units. Reconstruct from rows,
    // never from a shared country label or an implicitly common parent population.
    const leftRows = a.rows.map(r => [r.observation_id,
      left.observations.find(o => o.id === r.observation_id)?.text_sha256]).sort();
    const rightRows = b.rows.map(r => [r.observation_id,
      right.observations.find(o => o.id === r.observation_id)?.text_sha256]).sort();
    return left.source.hash === right.source.hash &&
      left.source.hash_basis === right.source.hash_basis &&
      left.source.selection_hash === right.source.selection_hash &&
      a.unit === b.unit && JSON.stringify(leftRows) === JSON.stringify(rightRows);
  }
  function compareViews(left, right, leftModelId, rightModelId) {
    const a = left.models.find(m => m.id === leftModelId), b = right.models.find(m => m.id === rightModelId);
    assert(a && b, 'Choose two existing models.');
    let comparison;
    if (left.kind === 'legacy' && right.kind === 'legacy') {
      const identical = compareLegacyPopulations(left, right, a, b);
      const sameGeometry = a.representation === b.representation &&
        a.representation_version === b.representation_version;
      const sameProtocol = sameGeometry && a.family === b.family &&
        a.method === b.method && a.fit_version === b.fit_version &&
        JSON.stringify(a.settings) === JSON.stringify(b.settings);
      comparison = {
        identical_population:identical, same_representation:sameGeometry,
        same_fit_protocol:sameProtocol, numerical_comparison_permitted:identical && sameProtocol,
        paired_count:identical ? a.rows.length : 0,
        assigned_both:null,
        reason:!identical ? 'Legacy source, selection, unit, or observation identities differ.' :
          !sameGeometry ? 'Same observations, different geometry. Separate descriptive views only.' :
          !sameProtocol ? 'Same observations and representation, but different algorithm/settings; no paired numeric metric.' :
          'Matched fit protocol, descriptive preview only; no inferential claim.'
      };
    } else if (left.kind === 'parallel' && right.kind === 'parallel') {
      comparison = C.compare(left, right, a.id, b.id);
    } else comparison = {
      identical_population:false, same_representation:false, numerical_comparison_permitted:false,
      paired_count:0, assigned_both:null,
      reason:'Cross-schema comparisons are withheld until the coordinator approves a source/hash-basis bridge.'
    };
    if (a.family !== 'partition' || b.family !== 'partition') {
      comparison = {...comparison, numerical_comparison_permitted:false, assigned_both:null,
        reason:comparison.reason + ' Mixtures, graph distances and consensus frequencies are not interchangeable partitions.'};
    }
    return comparison;
  }
  function ensureParallelOnly(items) {
    assert(Array.isArray(items) && items.length > 0 && items.length <= 6,
      'Save between one and six validated interchange envelopes.');
    for (const item of items) C.validateParallel(item);
  }
  async function packParallel(items) {
    ensureParallelOnly(items);
    const payload_json=JSON.stringify(items);
    assert(utf8Length(payload_json) <= C.MAX_ARCHIVE_BYTES, 'Lab archive exceeds existing 128 MB cap.');
    return JSON.stringify({
      schema:ARCHIVE, version:ARCHIVE_VERSION, created_at:new Date().toISOString(),
      kind:'parallel_envelopes', payload_json, sha256:await sha256(payload_json)
    });
  }
  async function restoreParallel(text) {
    assert(typeof text === 'string' && utf8Length(text) <= C.MAX_ARCHIVE_BYTES,
      'Saved file exceeds existing 128 MB cap.');
    const archive=JSON.parse(text.replace(/^\uFEFF/, ''));
    assert(archive.schema === ARCHIVE && archive.version === ARCHIVE_VERSION &&
      archive.kind === 'parallel_envelopes' && typeof archive.payload_json === 'string' &&
      hashString(archive.sha256), 'Unsupported lab archive version or incomplete checksum.');
    assert(await sha256(archive.payload_json) === archive.sha256, 'Saved-run content checksum mismatch.');
    const items=JSON.parse(archive.payload_json);
    ensureParallelOnly(items);
    return items;
  }
  const api={METHODS, ARCHIVE, ARCHIVE_VERSION, fromLegacy, compareViews,
    sha256, packParallel, restoreParallel, fixtureInformation};
  if (typeof module !== 'undefined' && module.exports) module.exports=api;
  else root.UNMethodLabAdapters=api;
})(globalThis);
