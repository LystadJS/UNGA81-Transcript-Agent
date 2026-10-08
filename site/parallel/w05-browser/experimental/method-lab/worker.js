/* Classic Web Worker: read, restore, run or export; never fetch transcript URLs. */
'use strict';
importScripts('contracts.js', 'adapters.js');
const lab = self.UNMethodLabContracts;
const adapters = self.UNMethodLabAdapters;
const MODULES = [
  'numerics.js', 'meeting-scopes.js', 'mds-core.js', 'gmm-core.js',
  'cluster-options.js', 'nmf-options.js', 'passage-selection.js',
  'passage-pilot-core.js', 'reviewed-units.js', 'meeting-quick-reader.js',
  'analysis-core.js', 'lsa-core.js', 'representation-metrics.js',
  'cluster-algorithms.js', 'hdbscan-core.js', 'cluster-core.js',
  'cluster-stability.js', 'nmf-core.js', 'latent-core.js'
];
let engineLoaded = false;
const clock = () => performance.now();
const inputBytes = text => new TextEncoder().encode(text).length;

function memory() {
  const bytes = performance.memory?.usedJSHeapSize;
  return Number.isSafeInteger(bytes) ? {used_heap_bytes:bytes, basis:'browser_exposed_heap'} :
    {used_heap_bytes:null, basis:'not_available_in_this_browser'};
}
function send(id, type, details={}) {
  postMessage({id, type, ...details, resource:memory()});
}
async function loadEngine(id) {
  if (engineLoaded) return;
  send(id, 'progress', {phase:'engine', message:'Loading existing same-origin numerical modules.'});
  importScripts(...MODULES.map(name => '../../../' + name + '?v=w5-experimental-1'));
  engineLoaded = true;
}
async function moduleHashes() {
  const entries = [];
  for (const name of MODULES) {
    const response=await fetch('../../../' + name + '?v=w5-experimental-1', {cache:'no-store'});
    if (!response.ok || new URL(response.url).origin !== location.origin) {
      throw new Error('Same-origin numerical source unavailable: ' + name);
    }
    const bytes=await response.arrayBuffer();
    const digest=await crypto.subtle.digest('SHA-256', bytes);
    const hex=Array.from(new Uint8Array(digest), x=>x.toString(16).padStart(2,'0')).join('');
    entries.push([name, hex]);
  }
  return Object.fromEntries(entries);
}
function parse(text) {
  if (typeof text !== 'string' || inputBytes(text) > lab.MAX_ARCHIVE_BYTES) {
    throw new Error('Import is not UTF-8 text or exceeds the existing 128 MB archive limit.');
  }
  return JSON.parse(text.replace(/^\uFEFF/, ''));
}
self.onmessage = async event => {
  const data = event.data || {};
  const id = data.id;
  const started = clock();
  try {
    if (!Number.isSafeInteger(id) || id <= 0) throw new Error('Missing task identity.');
    if (!['open', 'run_local', 'save_parallel'].includes(data.action)) throw new Error('Unknown lab operation.');
    send(id, 'progress', {phase:'validation', message:'Validating input and provenance.'});
    if (data.action === 'open') {
      const doc=parse(data.text);
      if (doc.schema === lab.SCHEMA) {
        const view=lab.fromParallel(doc);
        send(id, 'result', {kind:'parallel', views:[view], elapsed_ms:clock()-started,
          retained_observations:view.observations.length, supplied_bytes:inputBytes(data.text)});
      } else if (doc.schema === adapters.ARCHIVE) {
        const items=await adapters.restoreParallel(data.text);
        const views=items.map(lab.fromParallel);
        send(id, 'result', {kind:'parallel', views, elapsed_ms:clock()-started,
          retained_observations:views.reduce((sum,v)=>sum+v.observations.length,0),
          supplied_bytes:inputBytes(data.text)});
      } else if (doc.schema === 'un.latent-saved-run.v1') {
        if (data.authorization !== 'development') throw new Error('Confirm that the archive contains only authorized development/synthetic records.');
        await loadEngine(id);
        const restored=await self.UNLatent.restore(data.text, message=>
          send(id, 'progress', {phase:'replay', message}));
        const view=adapters.fromLegacy(restored);
        send(id, 'result', {kind:'legacy', views:[view], archive_text:data.text,
          runtime_warning:restored.result.engine === self.UNLatent.VERSION ? null :
            'An older numerical engine produced this archive. Source-bound restored snapshot only; no refit or inference.',
          elapsed_ms:clock()-started,
          retained_observations:view.observations.length, supplied_bytes:inputBytes(data.text)});
      } else {
        throw new Error('Unsupported saved-run schema: ' + String(doc.schema));
      }
    } else if (data.action === 'run_local') {
      if (data.authorization !== 'development') throw new Error('Development/synthetic source authorization is required.');
      if (!data.payload || !['corpus','reviewed'].includes(data.payload.kind) ||
        typeof data.payload.text !== 'string' || inputBytes(data.payload.text) > 40*1024*1024) {
        throw new Error('Select a supported local corpus/reviewed input within the 40 MB limit.');
      }
      await loadEngine(id);
      const plan=self.UNLatent.validatePlan(data.plan);
      const hashes=await moduleHashes();
      const runtime={
        engine:self.UNLatent.VERSION, execution:'isolated browser Web Worker',
        method_lab:'0.1.0', user_agent:navigator.userAgent, module_sha256:hashes
      };
      const result=await self.UNLatent.run(data.payload,plan,runtime,message=>
        send(id, 'progress', {phase:'fit', message}));
      const archive_text=await self.UNLatent.pack(data.payload,result);
      const view=adapters.fromLegacy({result});
      send(id, 'result', {kind:'legacy', views:[view], archive_text,
        elapsed_ms:clock()-started, retained_observations:view.observations.length,
        supplied_bytes:inputBytes(data.payload.text)});
    } else {
      const text=await adapters.packParallel(data.envelopes);
      send(id, 'result', {kind:'export', text, elapsed_ms:clock()-started,
        retained_observations:data.envelopes.reduce((n,e)=>n+e.observations.length,0),
        supplied_bytes:inputBytes(text)});
    }
  } catch(error) {
    send(id, 'error', {phase:'error', message:error?.message || String(error),
      elapsed_ms:clock()-started});
  }
};
