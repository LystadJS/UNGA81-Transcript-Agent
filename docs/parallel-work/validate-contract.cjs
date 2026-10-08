'use strict';
/* Synthetic-only contract smoke/regression tests. No transcript fetch, review input or side effects. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = __dirname;
const schema = JSON.parse(fs.readFileSync(path.join(root, 'interchange-v1.schema.json'), 'utf8'));
const doc = fs.readFileSync(path.join(root, 'INTERCHANGE_V1.md'), 'utf8');
const exampleStart = doc.indexOf('```json', doc.indexOf('## 4. Mapping example'));
assert(exampleStart >= 0, 'No synthetic example in INTERCHANGE_V1.md');
const exampleEnd = doc.indexOf('```', exampleStart + 7);
assert(exampleEnd > exampleStart, 'Unclosed synthetic example');
const example = JSON.parse(doc.slice(exampleStart + 7, exampleEnd).trim());
const isObject = x => !!x && typeof x === 'object' && !Array.isArray(x);
function structural(def, val, at='$') {
  if (def.const !== undefined) assert.deepEqual(val, def.const, at + ': wrong const');
  if (def.enum) assert(def.enum.includes(val), at + ': unknown enum');
  if (def.type) {
    const allowed = Array.isArray(def.type) ? def.type : [def.type];
    assert(allowed.some(t => t === 'null' ? val === null : t === 'array' ? Array.isArray(val) :
      t === 'object' ? isObject(val) : t === 'integer' ? Number.isSafeInteger(val) :
      t === 'number' ? typeof val === 'number' && Number.isFinite(val) : typeof val === t), at + ': type');
  }
  if (typeof val === 'string') {
    if (def.minLength !== undefined) assert(val.length >= def.minLength, at + ': length');
    if (def.pattern) assert(new RegExp(def.pattern).test(val), at + ': pattern');
    if (def.format === 'date-time') assert(/(Z|[+-]\\d{2}:\\d{2})$/.test(val) && !Number.isNaN(Date.parse(val)), at + ': timestamp');
  }
  if (typeof val === 'number') {
    if (def.minimum !== undefined) assert(val >= def.minimum, at + ': minimum');
    if (def.maximum !== undefined) assert(val <= def.maximum, at + ': maximum');
  }
  if (Array.isArray(val)) {
    if (def.minItems !== undefined) assert(val.length >= def.minItems, at + ': minItems');
    if (def.items) val.forEach((item, i) => structural(def.items, item, at + '[' + i + ']'));
  }
  if (isObject(val)) {
    (def.required || []).forEach(k => assert(Object.hasOwn(val, k), at + ': missing ' + k));
    for (const [k, item] of Object.entries(val)) {
      if (def.properties && Object.hasOwn(def.properties, k)) structural(def.properties[k], item, at + '.' + k);
      else if (def.additionalProperties === false) assert.fail(at + ': unknown property ' + k);
    }
  }
}
function invariant(x) {
  structural(schema, x);
  assert(x.cohort.split !== 'development' || x.producer.fixture_kind === 'private_development', 'source split/fixture mismatch');
  if (x.cohort.split === 'development') {
    assert(x.observations.every(o => !['2026-10-05', '2026-10-06'].includes(o.date)), 'reserved meeting date in development');
  }
  const ids = x.observations.map(o => o.id), mm = x.models.map(m => m.model_id);
  assert.equal(new Set(ids).size, ids.length, 'duplicate observation identity');
  assert.equal(new Set(mm).size, mm.length, 'duplicate model identity');
  assert.equal(x.coverage.observations_total, ids.length, 'observation total mismatch');
  assert.equal(x.coverage.eligible, x.cohort.eligible, 'eligible mismatch');
  assert.equal(x.coverage.eligible + x.coverage.excluded, ids.length, 'eligible/excluded missing');
  assert(x.cohort.eligible <= x.cohort.total_in_frame || x.cohort.unit !== 'source_segment',
    'source segment count exceeds frame population');
  const byId = new Map(x.observations.map(o => [o.id, o]));
  for (const o of x.observations) {
    if (o.start === null || o.end === null) assert(o.start === null && o.end === null, 'half-null offset');
    else assert(o.start < o.end, 'invalid code-point span');
    if (o.parent_id !== null) assert(o.parent_text_sha256, 'parent missing hash');
    if (o.source_status !== 'available') assert(o.missing_reason, 'source status lacks reason');
    if (o.review_status !== 'confirmed') assert(!o.speech_id, 'unverified speech');
    if (o.date && x.cohort.split === 'development') assert(o.source_status !== 'available' || o.meeting_id, 'development record requires verified meeting');
  }
  assert.equal(x.coverage.models.length, x.models.length, 'model ledger count mismatch');
  const cm = new Map(x.coverage.models.map(m => [m.model_id, m]));
  assert.equal(cm.size, mm.length, 'duplicate model coverage');
  for (const m of x.models) {
    const c = cm.get(m.model_id); assert(c, 'model missing coverage');
    assert.equal(c.eligible, x.cohort.eligible, 'model eligible count');
    assert.equal(c.assigned + c.unassigned + c.not_fitted, c.eligible, 'model population accounting');
    assert.equal(c.attempted_fits, c.successful_fits + c.failed_fits, 'fit attempt accounting');
    const rows = x.results.filter(z => z.model_id === m.model_id);
    assert.equal(new Set(rows.map(z => z.observation_id)).size, rows.length, 'duplicate result ID');
    assert.equal(rows.filter(z => z.status === 'assigned').length, c.assigned, 'assigned count');
    assert.equal(rows.filter(z => z.status === 'unassigned').length, c.unassigned, 'unassigned count');
    assert.equal(rows.filter(z => z.status === 'not_fitted').length, c.not_fitted, 'not fitted count');
    assert.equal(rows.filter(z => z.status === 'excluded').length, c.excluded, 'excluded count');
    const eligible = x.observations.filter(o => o.source_status === 'available' && !o.exclusion_reasons.length);
    assert.equal(eligible.length, c.eligible, 'eligible population derivation');
    assert(eligible.every(o => rows.some(z => z.observation_id === o.id && z.status !== 'excluded')), 'missing result for eligible observation');
    assert(rows.every(z => byId.has(z.observation_id)), 'result references nonexistent observation');
  }
  for (const z of x.results) {
    const m = x.models.find(a => a.model_id === z.model_id); assert(m, 'result references nonexistent model');
    assert.equal(z.representation_basis_id, m.representation_id, 'representation basis mismatch');
    if (z.status === 'assigned') assert(Number.isInteger(z.cluster) && z.cluster > 0, 'assigned label');
    if (z.status === 'unassigned') assert.equal(z.cluster, 0, 'unassigned label');
    if (z.status === 'excluded' || z.status === 'not_fitted') {
      assert.equal(z.cluster, null, 'missing/nonfit cluster');
      assert(z.reason && z.reason.length, 'missing explicit failure reason');
    }
    if (z.membership_kind === 'gmm_responsibility' || z.membership_kind === 'nmf_share') {
      assert(Array.isArray(z.memberships) && z.memberships.length > 0, 'missing soft memberships');
      assert(Math.abs(z.memberships.reduce((a, v) => a + v, 0) - 1) < 1e-6, 'soft membership normalization');
    } else assert(z.memberships === null, 'untyped membership array');
    if (z.membership_kind === 'hdbscan_strength') assert(z.membership_strength !== null, 'missing density strength');
  }
  for (const e of x.evidence) {
    assert(byId.has(e.observation_id), 'evidence missing observation');
    assert(e.start === null && e.end === null || Number.isInteger(e.start) && Number.isInteger(e.end) && e.start < e.end,
      'invalid evidence span');
  }
  for (const d of x.diagnostics) {
    assert(d.model_id === null || mm.includes(d.model_id), 'unknown diagnostics model');
    assert(d.status !== 'validated' || d.denominator !== 0, 'zero-denominator valid result');
    if (d.status === 'withheld' || d.status === 'failed') assert(d.reason, 'withheld/failed diagnostic requires reason');
  }
  for (const f of x.coverage.failure_ledger) assert(mm.includes(f.model_id), 'unknown failed model');
  assert.equal(x.publication_eligible, false);
}
function expectReject(label, change) {
  const x = structuredClone(example); change(x); assert.throws(() => invariant(x), undefined, label);
}
invariant(example);
expectReject('source hash format', x => {x.observations[0].text_sha256='bad';});
expectReject('duplicate identity', x => {x.observations.push(structuredClone(x.observations[0]));x.coverage.observations_total++;});
expectReject('wrong unassigned label', x => {x.results[0].cluster=1;});
expectReject('wrong model basis', x => {x.results[0].representation_basis_id='different';});
expectReject('missing result', x => {x.results=[];});
expectReject('wrong coverage', x => {x.coverage.models[0].assigned=1;});
expectReject('half-null span', x => {x.observations[0].start=0;});
expectReject('unverified speech', x => {x.observations[0].speech_id='claimed speech';});
expectReject('reserved date', x => {x.cohort.split='development';x.producer.fixture_kind='private_development';x.observations[0].date='2026-10-05';});
expectReject('publication bypass', x => {x.publication_eligible=true;});
expectReject('private text field', x => {x.observations[0].text='private text';});
expectReject('failure ledger mismatch', x => {x.coverage.models[0].attempted_fits=2;});
process.stdout.write(JSON.stringify({suite:'parallel-v1-synthetic',positive:1,negative:12,status:'pass',network_access:false,holdout_access:false})+'\\n');
