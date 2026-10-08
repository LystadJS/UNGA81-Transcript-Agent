/* Coordinator source-bound browser integration: research preview, not release. */
(function (root) {
  'use strict';

  const C = root.UNMethodLabContracts;
  const V = root.UNEvidenceViz;
  const REQUIRED = Object.freeze([
    'SHA256.json', 'interchange-v1.json', 'receipt.json',
    'source-linked-edges.json', 'fit-geometry.json'
  ]);
  const SHA = /^[a-f0-9]{64}$/;
  const MAX_FILE_BYTES = 64 * 1024 * 1024;
  const MAX_GRAPH_NODES = 50;
  const check = (ok, why) => { if (!ok) throw Error(why); };
  const byID = id => root.document.getElementById(id);
  const status = (message, bad) => {
    byID('research-status').textContent = message;
    byID('research-status').classList.toggle('research-error', !!bad);
  };
  const metricNumber = n => typeof n === 'number' && Number.isFinite(n);
  const utf8 = bytes => new TextDecoder('utf-8', {fatal:true}).decode(bytes);

  async function digest(data) {
    check(root.crypto && root.crypto.subtle, 'Local SHA-256 requires HTTPS or localhost.');
    const raw = await root.crypto.subtle.digest('SHA-256', data);
    return Array.from(new Uint8Array(raw), b => b.toString(16).padStart(2, '0')).join('');
  }

  async function load(files) {
    check(files && files.length === REQUIRED.length,
      'Select exactly five original W3 JSON files, including SHA256.json.');
    const entries = new Map();
    for (const f of files) {
      check(REQUIRED.includes(f.name) && !entries.has(f.name),
        'Unexpected or duplicate input file: ' + f.name);
      check(f.size > 0 && f.size <= MAX_FILE_BYTES,
        'Invalid or oversized W3 JSON file: ' + f.name);
      entries.set(f.name, f);
    }
    const manifest = JSON.parse(utf8(await entries.get('SHA256.json').arrayBuffer()));
    check(manifest && typeof manifest === 'object' && !Array.isArray(manifest),
      'W3 output checksums missing.');
    const result = {};
    for (const name of REQUIRED.filter(n => n !== 'SHA256.json')) {
      const expected = manifest[name];
      check(SHA.test(expected), 'Missing W3 output SHA-256 for ' + name);
      const raw = await entries.get(name).arrayBuffer();
      check((await digest(raw)) === expected, 'Checksum mismatch: ' + name);
      result[name] = JSON.parse(utf8(raw));
    }
    return result;
  }

  function validate(files) {
    const e = files['interchange-v1.json'];
    const r = files['receipt.json'];
    const edges = files['source-linked-edges.json'];
    const fitted = files['fit-geometry.json'];
    C.validateParallel(e);
    V.validateEnvelope(e);

    // The live public hub intentionally admits invented synthetic W3 only.
    // Privately authorized real development material is NOT a public fixture.
    check(e.contract_version === '1.0.0' && e.producer.workstream_id === 'W3' &&
      e.producer.fixture_kind === 'synthetic' &&
      e.upstream.source_schema === 'synthetic.v1' &&
      e.upstream.source_hash_basis === 'synthetic' &&
      e.cohort.split === 'synthetic' &&
      e.evaluation_role === 'engineering_only' && e.publication_eligible === false,
      'This browser preview accepts only source-bound synthetic W3 v1 output.');
    check(r && r.schema === 'un.graph-methods-receipt.v1' &&
      r.split === 'synthetic' && r.publication_eligible === false &&
      r.heldout_transcripts_opened === 0 && SHA.test(r.code_sha256) &&
      r.code_sha256 === e.producer.code_sha256 &&
      r.fixture_or_source_sha256 === e.upstream.source_sha256 &&
      r.source_hash_basis === e.upstream.source_hash_basis &&
      r.observation_join_sha256 === e.upstream.selection_sha256,
      'W3 graph receipt and interchange source or producer integrity differs.');
    check(r.representation && SHA.test(r.representation.matrix_sha256) &&
      SHA.test(r.representation.training_selection_sha256),
      'Pinned W3 geometry/matrix identity required.');
    check(e.models.length === 2 &&
      e.models.some(m => m.method === 'spectral' && m.method_family === 'graph_partition') &&
      e.models.some(m => m.method === 'diffusion_map' && m.method_family === 'geometry') &&
      e.models.every(m => m.representation_id === r.representation.id &&
        m.representation_version === r.representation.version &&
        m.training_selection_sha256 === r.representation.training_selection_sha256),
      'W3 model graph/diffusion provenance mismatches the fitted representation.');

    const included = e.observations.filter(o =>
      o.source_status === 'available' && o.exclusion_reasons.length === 0);
    const bySource = new Map(included.map(x => [x.id, x]));
    const g = r.graph;
    check(g && g.n_nodes === included.length &&
      Number.isSafeInteger(g.edge_count) && g.edge_count >= 0 &&
      metricNumber(g.bandwidth) && g.bandwidth > 0 &&
      ['euclidean', 'cosine'].includes(g.metric) &&
      g.kernel === 'gaussian' &&
      ['union','mutual'].includes(g.symmetrize) &&
      Number.isSafeInteger(g.n_neighbors) && g.n_neighbors > 0 &&
      g.n_neighbors < included.length &&
      Array.isArray(g.component_sizes) &&
      g.component_sizes.reduce((n,x) => n + x, 0) === included.length &&
      g.connected_components === g.component_sizes.length,
      'Unsupported graph construction, component or source denominator.');
    check(Array.isArray(edges) && edges.length === g.edge_count,
      'Graph edge ledger size differs from declared graph.');
    check(included.every(o => o.source_url === null && !Object.hasOwn(o, 'text')),
      'Synthetic preview may not contain original URLs or source text.');
    const pairKeys = new Set();
    let graphSHA = null;
    for (const edge of edges) {
      const a=bySource.get(edge.from_id), b=bySource.get(edge.to_id);
      check(a && b && a.id !== b.id,
        'Graph edge references missing, excluded, or duplicate source.');
      check(edge.from_text_sha256 === a.text_sha256 &&
        edge.to_text_sha256 === b.text_sha256 &&
        edge.from_parent_id === a.parent_id &&
        edge.to_parent_id === b.parent_id &&
        edge.from_meeting_id === a.meeting_id &&
        edge.to_meeting_id === b.meeting_id &&
        edge.from_source_url === null && edge.to_source_url === null,
        'Graph edge source SHA, meeting or parent identity mismatch.');
      check(metricNumber(edge.weight) && edge.weight > 0 && edge.weight <= 1 &&
        metricNumber(edge.metric_distance) && edge.metric_distance >= 0 &&
        Math.abs(edge.weight -
          Math.exp(-0.5 * Math.pow(edge.metric_distance / g.bandwidth, 2))) <= 1e-10,
        'Graph weights do not reproduce declared Gaussian distance kernel.');
      check(SHA.test(edge.graph_policy_sha256) &&
        (graphSHA === null || graphSHA === edge.graph_policy_sha256),
        'Graph policy fingerprint inconsistent across edges.');
      graphSHA = edge.graph_policy_sha256;
      const key=[a.id,b.id].sort().join('\u001f');
      check(!pairKeys.has(key), 'Duplicate undirected graph edge.');
      pairKeys.add(key);
    }
    // Check the original numerical assignment (never fit a new partition on
    // rendered coordinates) and original eligible observation order.
    for (const method of ['spectral','diffusion']) {
      const view = fitted && fitted[method];
      check(view && Array.isArray(view.source_ordered_ids) &&
        view.source_ordered_ids.length === included.length &&
        view.source_ordered_ids.every((id,i) => id === included[i].id),
        'W3 geometry source order or population changed.');
      if (view.status === 'fitted') {
        check(Array.isArray(view.coordinates) &&
          view.coordinates.length === included.length,
          'W3 fitted coordinate count differs from original source cohort.');
      }
      if (method === 'spectral' && view.status === 'fitted') {
        const model = e.models.find(m => m.method === 'spectral');
        const labels = new Map(e.results.filter(x => x.model_id === model.model_id)
          .map(x => [x.observation_id, x.cluster]));
        check(Array.isArray(view.labels) && view.labels.length === included.length &&
          view.labels.every((label,i) => labels.get(included[i].id) === label),
          'W3 spectral labels disagree with source-bound interchange.');
      }
    }
    return {envelope:e, receipt:r, edges, included,
      excluded:e.coverage.excluded, unavailable:e.coverage.unavailable_sources};
  }

  function panel(data) {
    const e=data.envelope, r=data.receipt, included=data.included;
    const identity={
      source_schema:e.upstream.source_schema,
      source_hash_basis:e.upstream.source_hash_basis,
      source_sha256:e.upstream.source_sha256,
      selection_sha256:e.upstream.selection_sha256,
      unit:e.cohort.unit,weighting:e.cohort.weighting,
      representation_id:r.representation.id,
      representation_version:r.representation.version,
      observation_refs:included.map(x => ({id:x.id,text_sha256:x.text_sha256}))
    };
    const base={
      kind:'network',
      measure:'W3 full-source exact kNN graph, Gaussian-weighted affinity on pinned feature-space distances. Not diplomatic links or policy diffusion.',
      identity,
      warnings:[
        'Synthetic engineering-only, never real UN diplomatic source content.',
        'kNN edges are selected by neighborhood; graph affinity is not cosine similarity or a global threshold.',
        'Per-edge agenda and duplicate sensitivity: not assessed.',
        'No evidence of government stance, alliance, political influence or causality.'
      ],
      reason:null,
      coverage:{frame:e.cohort.total_in_frame, eligible:e.cohort.eligible,
        included:included.length, excluded:data.excluded,missing:data.unavailable}
    };
    if (included.length > MAX_GRAPH_NODES) {
      return {...base,status:'withheld',
        reason:'The W6 network view has a 50-node limit. '+included.length+
          ' source-bound observations remain included in the original W3 result; no sampling performed.',
        coverage:{...base.coverage,included:0}};
    }
    return {...base,status:'ready',
      graph:{
        threshold:0,metric:'gaussian_affinity_on_'+r.graph.metric+'_knn',
        selection_rule:String(r.graph.n_neighbors)+'-nearest-neighbor graph, '+
          r.graph.symmetrize+'-symmetrized; no global affinity threshold; display floor 0'
      },
      nodes:included.map((o,i) => ({
        id:o.id,label:'P'+String(i+1).padStart(2,'0'),
        observation_ids:[o.id],
        affiliation_status:o.country === null ?
          'Unattributed source; no verified national speaker' :
          'Recorded source affiliation only; speaker and stance unverified'
      })),
      edges:data.edges.map(edge => ({
        from:edge.from_id,to:edge.to_id,strength:edge.weight,
        eligible_pairs:1,duplicate_sensitivity:'not_assessed',
        agenda_sensitivity:'not_assessed',
        observation_ids:[edge.from_id,edge.to_id]
      }))
    };
  }

  async function inspect() {
    const button=byID('research-import');
    button.disabled=true;
    byID('research-graph').replaceChildren();
    status('Checking local source identities, checksums, graph geometry and missingness…',false);
    try {
      const files=await load(byID('research-files').files);
      const data=validate(files);
      const graph=panel(data);
      const view=V.mount(byID('research-graph'),data.envelope,[graph]);
      const count=data.included.length;
      const first=data.envelope.models.find(m => m.method === 'spectral');
      const second=data.envelope.models.find(m => m.method === 'diffusion_map');
      check(first && second, 'Original W3 method records unavailable.');
      byID('research-summary').textContent=
        'W5 read-only v1 verification passed. '+count+' eligible observations, '+
        data.excluded+' excluded ('+data.unavailable+' unavailable), '+
        data.edges.length+' source-bound graph edges; '+
        'spectral and diffusion are distinct offline numerical methods.';
      status(graph.status === 'withheld' ?
        'Validated source-complete W3 graph, but display withheld above 50 nodes. No sampling performed.' :
        'Validated W3 source-bound graph. Display is Gaussian kNN affinity, not geopolitical influence.',false);
      return view;
    } catch (error) {
      byID('research-summary').textContent='No verified W3 graph is displayed.';
      byID('research-graph').replaceChildren();
      status('W3 graph refused: '+String(error.message||error),true);
      return null;
    } finally {
      button.disabled=false;
    }
  }

  function begin() {
    if (!C || !V || !byID('research-files') || !byID('research-import'))
      throw Error('Research browser dependencies missing.');
    byID('research-import').addEventListener('click',inspect);
    byID('research-files').addEventListener('change',()=>{
      byID('research-graph').replaceChildren();
      byID('research-summary').textContent='File selection changed; previous source-linked graph cleared.';
      status('Review the original five W3 JSON files, then inspect again.',false);
    });
  }
  root.UNResearchWiring=Object.freeze({VERSION:'research-wiring-0.1.0',
    load,validate,panel,inspect});
  if (root.document.readyState === 'loading')
    root.document.addEventListener('DOMContentLoaded',begin,{once:true});
  else begin();
})(window);
