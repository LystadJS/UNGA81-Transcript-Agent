'use strict';

/*
 * Coordinator-only W3 -> W5/W6 experimental read adapter.
 * Synthetic outputs only. No transcript ingestion, refits, or source/network IO.
 * W5 and W6 remain independent draft PRs: this module never imports their code
 * in production or mutates their versioned contracts.
 */

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {validateRelational} = require('../../validation_framework/interchange.cjs');

const MAX_NODES = 600;
const W6_MAX_NODES = 50;
const MAX_FILE = 64 * 1024 * 1024;
const SHA = /^[a-f0-9]{64}$/;
const REQUIRED = Object.freeze([
  'interchange-v1.json',
  'receipt.json',
  'source-linked-edges.json',
  'fit-geometry.json'
]);

function check(ok, message) {
  if (!ok) throw new Error(message);
}

function hash(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function fromDirectory(directory) {
  const root = path.resolve(directory);
  check(fs.statSync(root).isDirectory() && !fs.lstatSync(root).isSymbolicLink(),
    'W3 artifact directory must be real, not a symbolic link.');
  const listing = fs.readdirSync(root);
  check(listing.includes('SHA256.json'), 'W3 output checksum manifest missing.');
  const manifestPath = path.join(root, 'SHA256.json');
  check(fs.statSync(manifestPath).size < 128 * 1024, 'W3 checksum manifest unbounded.');
  const checksums = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const files = {};
  for (const name of REQUIRED) {
    check(Object.hasOwn(checksums, name) && SHA.test(checksums[name]),
      'W3 artifact checksum missing/invalid for ' + name);
    check(listing.includes(name) && !fs.lstatSync(path.join(root, name)).isSymbolicLink(),
      'W3 artifact file missing or symlinked: ' + name);
    const stat = fs.statSync(path.join(root, name));
    check(stat.isFile() && stat.size <= MAX_FILE, 'W3 artifact file exceeds size limit: ' + name);
    const bytes = fs.readFileSync(path.join(root, name));
    check(hash(bytes) === checksums[name], 'W3 artifact checksum mismatch: ' + name);
    files[name] = JSON.parse(bytes.toString('utf8'));
  }
  return validate({
    envelope: files['interchange-v1.json'],
    receipt: files['receipt.json'],
    edges: files['source-linked-edges.json'],
    fitted: files['fit-geometry.json'],
    input_sha256: Object.fromEntries(REQUIRED.map(name => [name, checksums[name]]))
  });
}

function validate(bundle) {
  check(bundle && typeof bundle === 'object' && !Array.isArray(bundle), 'Missing W3 bundle.');
  const {envelope: e, receipt: r, edges, fitted} = bundle;
  check(e && e.schema === 'un.parallel-analysis.v1' && e.contract_version === '1.0.0',
    'Expected W3 interchange v1.0.0.');
  check(e.producer?.workstream_id === 'W3' &&
    e.producer.fixture_kind === 'synthetic' && e.cohort.split === 'synthetic' &&
    e.publication_eligible === false && e.evaluation_role === 'engineering_only',
    'Only text-free W3 synthetic engineering artifacts may enter this bridge.');
  check(validateRelational(e) === true, 'Merged W1 relational validation rejected W3.');
  check(r && r.schema === 'un.graph-methods-receipt.v1' &&
    r.split === 'synthetic' && r.publication_eligible === false &&
    r.heldout_transcripts_opened === 0,
    'W3 synthetic graph receipt absent or unsupported.');
  check(SHA.test(r.code_sha256) && r.code_sha256 === e.producer.code_sha256,
    'W3 envelope and receipt producer code identity differ.');
  check(r.fixture_or_source_sha256 === e.upstream.source_sha256 &&
    r.source_hash_basis === e.upstream.source_hash_basis &&
    r.observation_join_sha256 === e.upstream.selection_sha256,
    'W3 receipt/source/selection lineage mismatch.');
  check(r.representation && r.representation.id && r.representation.version &&
    SHA.test(r.representation.matrix_sha256) &&
    SHA.test(r.representation.training_selection_sha256),
    'W3 pinned fitted representation metadata missing.');
  check(e.models.length === 2 &&
    e.models.some(m => m.method === 'spectral' && m.method_family === 'graph_partition') &&
    e.models.some(m => m.method === 'diffusion_map' && m.method_family === 'geometry'),
    'W3 expected spectral and diffusion model records.');
  check(e.models.every(m => m.representation_id === r.representation.id &&
    m.representation_version === r.representation.version &&
    m.training_selection_sha256 === r.representation.training_selection_sha256),
    'W3 model identities disagree with graph representation.');
  const included = e.observations.filter(x => x.source_status === 'available' &&
    x.exclusion_reasons.length === 0);
  const excluded = e.observations.filter(x => x.source_status !== 'available' ||
    x.exclusion_reasons.length > 0);
  const id = new Map(included.map(x => [x.id, x]));
  const g = r.graph;
  check(g && Number.isInteger(g.n_nodes) && g.n_nodes === included.length &&
    g.n_nodes > 0 && g.n_nodes <= MAX_NODES &&
    Number.isInteger(g.edge_count) && g.edge_count >= 0 &&
    Number.isInteger(g.connected_components) && g.connected_components >= 1 &&
    ['euclidean','cosine'].includes(g.metric) &&
    ['gaussian','local_gaussian'].includes(g.kernel) &&
    ['union','mutual'].includes(g.symmetrize) &&
    Number.isInteger(g.n_neighbors) && g.n_neighbors >= 1 && g.n_neighbors < g.n_nodes &&
    typeof g.bandwidth === 'number' && Number.isFinite(g.bandwidth) && g.bandwidth > 0,
    'Invalid W3 graph construction contract.');
  check(Array.isArray(g.component_sizes) &&
    g.component_sizes.every(n => Number.isInteger(n) && n > 0) &&
    g.component_sizes.reduce((a,b) => a+b,0) === included.length &&
    g.component_sizes.length === g.connected_components,
    'W3 connected component ledger does not reconcile.');
  check(Array.isArray(edges) && edges.length === g.edge_count,
    'W3 graph edge count and source-bound edge ledger differ.');
  const seen = new Set();
  let policySHA = null;
  for (const edge of edges) {
    const a = id.get(edge.from_id), b = id.get(edge.to_id);
    check(a && b && a.id !== b.id, 'W3 edge references unavailable, unknown, or self observation.');
    check(a.text_sha256 === edge.from_text_sha256 &&
      b.text_sha256 === edge.to_text_sha256 &&
      a.meeting_id === edge.from_meeting_id &&
      b.meeting_id === edge.to_meeting_id &&
      a.parent_id === edge.from_parent_id &&
      b.parent_id === edge.to_parent_id &&
      a.source_url === edge.from_source_url &&
      b.source_url === edge.to_source_url,
      'W3 edge source hash, parent, meeting or original URL differs from interchange.');
    check(typeof edge.weight === 'number' && Number.isFinite(edge.weight) &&
      edge.weight > 0 && edge.weight <= 1 &&
      typeof edge.metric_distance === 'number' &&
      Number.isFinite(edge.metric_distance) && edge.metric_distance >= 0,
      'W3 edge distance/affinity invalid.');
    if (g.kernel === 'gaussian') {
      const expected = Math.exp(-.5 * (edge.metric_distance / g.bandwidth) ** 2);
      check(Math.abs(expected - edge.weight) <= 1e-10,
        'W3 edge does not match declared Gaussian kernel and distance.');
    }
    const pair = [a.id,b.id].sort().join('\u001f');
    check(!seen.has(pair), 'W3 graph contains duplicate undirected edge.');
    seen.add(pair);
    check(SHA.test(edge.graph_policy_sha256), 'W3 graph construction fingerprint missing.');
    if (policySHA === null) policySHA = edge.graph_policy_sha256;
    check(policySHA === edge.graph_policy_sha256, 'Inconsistent graph policy across edges.');
  }
  for (const method of ['spectral','diffusion']) {
    const view = fitted?.[method];
    check(view && Array.isArray(view.source_ordered_ids) &&
      view.source_ordered_ids.length === included.length &&
      view.source_ordered_ids.every((x,i) => x === included[i].id),
      'W3 fitted source order differs from complete graph observations.');
    const model = e.models.find(m => m.method === (method === 'spectral'?'spectral':'diffusion_map'));
    const modelRows = e.results.filter(x => x.model_id === model.model_id);
    if (method === 'spectral' && view.status === 'fitted') {
      check(Array.isArray(view.labels) && view.labels.length === included.length,
        'W3 spectral fit missing source-ordered assignments.');
      const result = new Map(modelRows.map(x => [x.observation_id,x]));
      for (let i=0;i<included.length;i++) {
        check(result.get(included[i].id)?.cluster === view.labels[i],
          'W3 spectral interchange label does not match saved numerical result.');
      }
    }
    if (view.status === 'fitted') {
      check(Array.isArray(view.coordinates) && view.coordinates.length === included.length,
        'W3 fitted coordinate/source identity count mismatch.');
    }
  }
  // This cross-contract adapter never reserializes an incomplete frame as a
  // purported complete v1 result. W5 receives the untouched source envelope.
  return Object.freeze({envelope:e,receipt:r,edges,fitted,
    input_sha256:bundle.input_sha256 || null,
    population:{eligible:included.length,excluded:excluded.length,
      unavailable:e.coverage.unavailable_sources,inventory:e.cohort.total_in_frame},
    graph_policy_sha256:policySHA});
}

function forW5(bundle) {
  const x = validate(bundle);
  return Object.freeze({
    status:'read_only_unreleased',
    envelope:x.envelope,
    model_methods:x.envelope.models.map(m => m.method),
    reason:'Original authoritative W3 v1 envelope; W5 must validate without altering any missing/excluded rows.'
  });
}

function panelIdentity(e, ref) {
  return {
    source_schema:e.upstream.source_schema,
    source_hash_basis:e.upstream.source_hash_basis,
    source_sha256:e.upstream.source_sha256,
    selection_sha256:e.upstream.selection_sha256,
    unit:e.cohort.unit,
    weighting:e.cohort.weighting,
    representation_id:ref.id,
    representation_version:ref.version,
    observation_refs:e.observations.filter(x => x.source_status === 'available' &&
      x.exclusion_reasons.length === 0).map(x => ({id:x.id,text_sha256:x.text_sha256}))
  };
}

function forW6Network(bundle) {
  const x = validate(bundle);
  const e = x.envelope, r=x.receipt, rows=e.observations.filter(o =>
    o.source_status === 'available' && o.exclusion_reasons.length === 0);
  // W6 draft validateEnvelope incorrectly requires per-model results only for
  // eligible rows, contrary to the complete W3/W1 v1 model×frame contract.
  // Do not strip excluded rows or mark a missing source as observed to bypass.
  if (x.population.excluded > 0) return {
    status:'blocked_contract',panel:null,
    reason:'W6 draft result-row validator excludes required excluded/model rows; full v1 W3 missing-source frame must remain intact.',
    coverage:x.population
  };
  const identity=panelIdentity(e,r.representation);
  const common={
    kind:'network',measure:'Observed W3 exact kNN graph edges weighted by declared Gaussian affinity in full fitted feature geometry; NOT policy ties, cosine similarity, or display-UMAP distances.',
    identity,
    coverage:{frame:e.cohort.total_in_frame,eligible:e.cohort.eligible,
      included:rows.length,excluded:e.coverage.excluded,missing:e.coverage.unavailable_sources},
    warnings:[
      'Engineering-only source-linked research display, not a scientific or diplomatic inference.',
      'Graph is kNN-selected; edge weight is Gaussian affinity, not cosine similarity; display minimum 0 is not a graph-construction threshold.',
      'Duplicate and agenda sensitivity have NOT been assessed per edge; no alliance, influence, agreement or policy transmission.',
      'No source text or 37 reserved October 5–6 transcript is included.'
    ],
    reason:null
  };
  if (rows.length > W6_MAX_NODES) return {
    status:'withheld',panel:{...common,status:'withheld',
      reason:'W6 network renderer caps nodes at 50; full W3 graph has '+rows.length+
        ' nodes. No silent truncation/sampling is permitted.',
      coverage:{...common.coverage,included:0}},
    coverage:x.population
  };
  // No threshold-based selection has been performed: graph construction is
  // kNN neighborhood inclusion, with weights solely for selected connections.
  const nodes=rows.map((row,i)=>({
    id:row.id,label:'P'+String(i+1).padStart(2,'0'),
    observation_ids:[row.id],
    affiliation_status:row.country === null ?
      'Unattributed source; no verified national speaker' :
      'Recorded '+row.country+' affiliation only; speaker and stance unverified'
  }));
  const edges=x.edges.map(edge=>({
    from:edge.from_id,to:edge.to_id,strength:edge.weight,
    eligible_pairs:1,
    duplicate_sensitivity:'not_assessed',
    agenda_sensitivity:'not_assessed',
    observation_ids:[edge.from_id,edge.to_id]
  }));
  return {status:'ready',panel:{
    ...common,status:'ready',
    graph:{
      threshold:0,
      metric:r.graph.kernel+'_affinity_on_'+r.graph.metric+'_knn',
      selection_rule:r.graph.n_neighbors+'-nearest neighbors, '+
        r.graph.symmetrize+'-symmetrized; no global edge-weight threshold; 0 is a display floor'
    },
    nodes,edges
  },coverage:x.population};
}

module.exports=Object.freeze({
  VERSION:'coord-w3-w5-w6-v0.1.0',
  W6_MAX_NODES,
  fromDirectory,validate,forW5,forW6Network
});
