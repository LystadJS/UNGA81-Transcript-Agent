/** U1 orchestration only. C0 remains the authority for every view and export. */
import {assess, exportReadModel, digest, canonical, parseStrict, validateQuery, validateShape} from '../../../research/integration/product_contracts/contracts.mjs';
export const C0_COMMIT = '884097997f89b0040e4418480378f077e3b65434';
export const MAX_IMPORT_BYTES = 2097152;
const clone = value => parseStrict(canonical(value));
const ensure = (yes, code) => { if (!yes) throw new Error(code); };
export function readBundle(value) {
  const bundle = typeof value === 'string' ? parseStrict(value) : clone(value);
  ensure(Object.keys(bundle).sort().join(',') === 'capability,product,query,receipts', 'bundle_fields');
  validateQuery(bundle.query); validateShape('capability', bundle.capability);
  validateShape('product', bundle.product);
  ensure(bundle.product.fixture_kind === 'synthetic' && bundle.query.resolved.source_mode === 'synthetic', 'synthetic_only');
  ensure(Array.isArray(bundle.receipts) && bundle.receipts.length <= 512, 'receipts');
  bundle.receipts.forEach(r => validateShape('receipt', r));
  return bundle;
}
function hostContext(value) {
  const ctx = clone(value);
  ensure(Object.keys(ctx).sort().join(',') === 'commitment,keys,now,revision', 'host_context');
  ensure(typeof ctx.revision === 'string' && ctx.revision.length <= 100, 'revision');
  ensure(typeof ctx.now === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(ctx.now), 'clock');
  ensure(Array.isArray(ctx.keys) && ctx.keys.length <= 32, 'keys');
  ctx.keys.forEach(k => validateShape('authority', k));
  ensure(ctx.commitment === null || /^[a-f0-9]{64}$/.test(ctx.commitment), 'commitment');
  return ctx;
}
const trustIdentity = ctx => canonical({keys: ctx.keys, commitment: ctx.commitment, revision: ctx.revision});
const visible = section => ['ready','partial'].includes(section.state);
function exportMatchesView(view, output) {
  if(!view.valid || !output.valid || !output.can_export) return false;
  return output.sections.filter(visible).every(s => {
    const shown=view.sections.find(v=>v.id===s.id && visible(v));
    return shown && canonical([s.evidence,s.findings,s.result,s.display,s.coverage])===canonical([shown.evidence,shown.findings,shown.result,shown.display,shown.coverage]);
  });
}
const fresh = (bundle, now) => bundle.receipts.every(r => r.payload.issued_at <= now && now < r.payload.expires_at);
export async function textDigest(text) {
  const bytes = new TextEncoder().encode(text);
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2,'0')).join('');
}
/** A provider is trusted host code, never a value imported from an uploaded bundle. */
export function createController(provider) {
  let generation = 0, detailGeneration = 0, active = null, saved = [], saveSerial = 0;
  let state = {phase:'idle', query:null, model:null, details:null, highlight:null, notice:null, canExport:false, saved:[]};
  const listeners = new Set();
  const snapshot = () => clone(state);
  const publish = () => { state.saved = saved.map(({id,query}) => ({id,query:clone(query)})); for (const listener of listeners) listener(snapshot()); };
  const clear = (phase='idle',notice=null) => {
    generation++; detailGeneration++; active = null;
    state = {...state, phase, query:null, model:null, details:null, highlight:null, notice, canExport:false}; publish(); return generation;
  };
  const current = ticket => ensure(ticket === generation, 'stale_operation');
  async function evaluated(bundle, destination, ticket) {
    const productId = await digest(bundle.product); current(ticket);
    const ctx = hostContext(await provider.getTrust(productId)); current(ticket);
    const input = { ...bundle, trustedKeys:ctx.keys, trustedReceiptSetSha256:ctx.commitment, destination, now:ctx.now };
    const model = await assess(input); current(ticket);
    // An in-flight response cannot revive a permission changed during verification.
    const after = hostContext(await provider.getTrust(productId)); current(ticket);
    ensure(trustIdentity(ctx) === trustIdentity(after) && fresh(bundle,after.now), 'trust_changed');
    return {model, ctx:after, productId, input:{...input,now:after.now}};
  }
  function stopped(ticket, phase='withheld', notice='permission_changed') {
    if (ticket !== generation) return null;
    clear(phase,notice); return snapshot();
  }
  async function install(candidate, ticket) {
    const bundle = readBundle(candidate);
    const checked = await evaluated(bundle,'local_view',ticket);
    const permission = await evaluated(bundle,'local_export',ticket);
    ensure(trustIdentity(checked.ctx) === trustIdentity(permission.ctx), 'trust_changed');
    current(ticket);
    active = {bundle, productId:checked.productId, trust:trustIdentity(permission.ctx)};
    state = {...state, phase:checked.model.valid ? checked.model.state : 'withheld',query:clone(bundle.query),model:checked.model,details:null,highlight:null,
      notice:checked.model.valid ? null : 'invalid_bundle',canExport:exportMatchesView(checked.model,permission.model)};
    publish(); return snapshot();
  }
  async function create(selection) {
    const ticket = clear('loading');
    try { const candidate = await provider.resolve(clone(selection)); current(ticket); return await install(candidate,ticket); }
    catch (error) { return stopped(ticket,error?.message==='trust_changed'?'withheld':'failed',error?.message==='trust_changed'?'permission_changed':'could_not_create'); }
  }
  async function importBundle(textOrPromise) {
    const ticket = clear('loading');
    try { const text = await textOrPromise; current(ticket); ensure(typeof text === 'string' && new TextEncoder().encode(text).length <= MAX_IMPORT_BYTES,'import_size'); return await install(readBundle(text),ticket); }
    catch { return stopped(ticket,'withheld','invalid_bundle'); }
  }
  async function refreshTrust() {
    if (!active) return true;
    const ticket = generation, entry = active;
    try {
      const ctx = hostContext(await provider.getTrust(entry.productId)); current(ticket);
      ensure(trustIdentity(ctx) === entry.trust && fresh(entry.bundle,ctx.now),'trust_changed');
      return true;
    } catch { stopped(ticket); return false; }
  }
  async function save() {
    if (!active || !['ready','partial','empty'].includes(state.phase)) return false;
    const ticket = generation, entry = active;
    try {
      const checked = await evaluated(entry.bundle,'local_view',ticket);
      ensure(checked.model.valid && trustIdentity(checked.ctx) === entry.trust,'trust_changed'); current(ticket);
      const old = saved.find(x => x.productId === entry.productId);
      if (!old) {
        ensure(saved.length < 20,'save_limit');
        saved.push({id:`briefing-${++saveSerial}`,query:clone(entry.bundle.query),bundle:clone(entry.bundle),productId:entry.productId});
      }
      state.notice = 'saved'; publish(); return true;
    } catch { stopped(ticket); return false; }
  }
  async function openSaved(id) {
    const record = saved.find(x => x.id === id), ticket = clear('loading');
    try { ensure(record,'saved_missing'); return await install(clone(record.bundle),ticket); }
    catch { return stopped(ticket); }
  }
  function removeSaved(id) { saved = saved.filter(x => x.id !== id); publish(); }
  async function exportModel() {
    if (!active) return null;
    const ticket = generation, entry = active;
    try {
      const view = await evaluated(entry.bundle,'local_view',ticket);
      const check = await evaluated(entry.bundle,'local_export',ticket);
      ensure(trustIdentity(view.ctx) === entry.trust && trustIdentity(check.ctx) === entry.trust && exportMatchesView(view.model,check.model),'trust_changed');
      const output = await exportReadModel(check.input); current(ticket);
      const after = hostContext(await provider.getTrust(entry.productId)); current(ticket);
      ensure(trustIdentity(after) === entry.trust && fresh(entry.bundle,after.now) && output.ok,'export_denied');
      // No unfiltered product, saved can_export flag, keyring or ledger enters these bytes.
      return {utf8:output.utf8,mediaType:output.media_type,filename:'synthetic-briefing.json',ticket};
    } catch { stopped(ticket); return null; }
  }
  async function openEvidence(id) {
    if (!active) return null;
    const ticket = generation, detailTicket = ++detailGeneration, entry = active;
    state.details = null; publish();
    try {
      const check = await evaluated(entry.bundle,'local_view',ticket);
      ensure(trustIdentity(check.ctx) === entry.trust,'trust_changed');
      const evidence = check.model.sections.flatMap(s=>s.evidence).find(e=>e.id===id);
      ensure(evidence,'evidence_not_visible');
      const detail = clone(await provider.getEvidence(entry.productId,id)); current(ticket);
      ensure(Object.keys(detail).sort().join(',') === 'fixture_kind,id,meeting_id,source_id,text','evidence_fields');
      ensure(detail.fixture_kind==='synthetic' && detail.id===id && detail.source_id===evidence.source_id && detail.meeting_id===evidence.meeting_id,'evidence_identity');
      ensure(typeof detail.text==='string' && detail.text.length<=16000 && await textDigest(detail.text)===evidence.text_sha256,'evidence_hash');
      const after = hostContext(await provider.getTrust(entry.productId)); current(ticket);
      ensure(trustIdentity(after)===entry.trust && fresh(entry.bundle,after.now),'trust_changed');
      if(detailTicket!==detailGeneration) return null;
      state.details = {id, text:[...detail.text].slice(evidence.start??0,evidence.end??undefined).join(''),country:evidence.country,capacity:evidence.capacity,meeting:detail.meeting_id,source:evidence.source_id};
      publish(); return clone(state.details);
    } catch { if (detailTicket===detailGeneration) stopped(ticket); return null; }
  }
  return Object.freeze({snapshot,create,importBundle,refreshTrust,save,openSaved,removeSaved,exportModel,openEvidence,
    subscribe(fn) { listeners.add(fn); fn(snapshot()); return () => listeners.delete(fn); },
    invalidate(notice='selection_changed') { clear('idle',notice); },
    closeEvidence() { detailGeneration++; state.details=null; publish(); },
    highlight(country) { ensure(country===null || /^[A-Z]{3}$/.test(country),'country'); state.highlight=country; publish(); },
    isCurrent(ticket) { return ticket===generation && active!==null; }
  });
}
