/* Coordinator-only, no-network W5/W6 browser integration. Synthetic evidence only. */
(function(root) {
  'use strict';
  const node = typeof module !== 'undefined' && module.exports;
  const W5 = node ? require('./parallel/w05-browser/experimental/method-lab/contracts.js') : root.UNMethodLabContracts;
  const W6 = node ? require('./experimental/evidence-viz/evidence-viz.js') : root.UNEvidenceViz;
  const Fixture = node ? require('./experimental/evidence-viz/fixture.js') : root.UNEvidenceFixture;
  const MAX_BYTES = 1024 * 1024;
  const BANNED_KEYS = new Set(['text','transcript','quote','raw_base64','source_json','audio','raw_text','review_packet','review_ledger','text_path']);
  const check = (condition, why) => { if (!condition) throw Error(why); };

  function checkMetadataOnly(value, depth=0) {
    check(depth <= 35, 'Nested research data exceed the safe input depth.');
    if (Array.isArray(value)) {
      value.forEach(item => checkMetadataOnly(item, depth+1));
    } else if (value !== null && typeof value === 'object') {
      for (const [key, item] of Object.entries(value)) {
        check(!BANNED_KEYS.has(key.toLowerCase()), 'Source-text or private-review field is not permitted: ' + key);
        checkMetadataOnly(item,depth+1);
      }
    }
  }

  function inspect(bundle) {
    check(bundle && typeof bundle === 'object' && !Array.isArray(bundle), 'Expected a bundle of envelope and panels.');
    check(Object.keys(bundle).length === 2 && Object.hasOwn(bundle,'envelope') && Object.hasOwn(bundle,'panels'),
      'Bundle must contain only envelope and panels.');
    checkMetadataOnly(bundle);
    const e = bundle.envelope;
    check(e?.schema === 'un.parallel-analysis.v1' && e.contract_version === '1.0.0',
      'Only the accepted interchange 1.0.0 is supported.');
    check(e.producer?.fixture_kind === 'synthetic' && e.cohort?.split === 'synthetic' &&
      e.upstream?.source_schema === 'synthetic.v1' && e.upstream?.source_hash_basis === 'synthetic',
      'This shared research preview refuses private development and held-out source data.');
    check(Array.isArray(e.observations) && e.observations.every(o => o.source_url === null) &&
      Array.isArray(e.evidence) && e.evidence.every(o => o.source_url === null),
      'Original source URLs are not permitted in the shared synthetic preview.');
    const view = W5.fromParallel(e);
    W6.validateEnvelope(e);
    check(Array.isArray(bundle.panels) && bundle.panels.length === W6.TYPES.length &&
      new Set(bundle.panels.map(p => p.kind)).size === W6.TYPES.length &&
      W6.TYPES.every(kind => bundle.panels.some(p => p.kind === kind)),
      'Provide one source-linked panel for each of the four visualization methods.');
    const panels = bundle.panels.map(p => W6.renderPanel(e,p));
    return {envelope:e,view,panels,bundle};
  }

  function summaryData(checked) {
    const c = checked.envelope.coverage;
    return {
      frame:c.observations_total, eligible:c.eligible, excluded:c.excluded,
      unavailable:c.unavailable_sources, models:checked.view.models.map(m => ({
        id:m.id, name:m.method, representation:m.representation,
        assigned:m.coverage.assigned, unassigned:m.coverage.unassigned,
        not_fitted:m.coverage.not_fitted, excluded:m.coverage.excluded
      })),
      schema:checked.envelope.schema,
      selection:checked.envelope.upstream.selection_sha256,
      source:checked.envelope.upstream.source_sha256
    };
  }

  function connect(doc) {
    const get = id => doc.getElementById(id);
    const result = get('research-panels'), summary = get('research-summary');
    const input = get('research-file'), status = get('research-status');
    let generation=0, active=null;
    const el = (tag,value) => {
      const x=doc.createElement(tag);
      if(value !== undefined)x.textContent=String(value);
      return x;
    };
    function reset() {
      ++generation;
      active=null;
      result.replaceChildren();
      summary.replaceChildren();
      summary.hidden=true;
      status.classList.remove('research-error');
    }
    function setStatus(message,failed=false) {
      status.textContent=message;
      status.classList.toggle('research-error',failed);
    }
    function renderSummary(info) {
      const v=summaryData(info);
      summary.append(el('h3','Independent W5 source and model validation'));
      const meta=el('div');meta.className='research-meta';
      for(const [key,value] of [['Frame',v.frame],['Eligible',v.eligible],['Excluded',v.excluded],
        ['Unavailable',v.unavailable],['Models',v.models.length]]) {
        meta.append(el('span',key+': '+value));
      }
      summary.append(meta);
      const wrap=el('div');wrap.className='research-table-wrap';
      const table=el('table');table.className='research-table';
      const head=el('tr');
      ['Method','Representation','Assigned','Unassigned','Not fitted','Excluded'].forEach(x=>head.append(el('th',x)));
      table.append(head);
      for(const m of v.models) {
        const tr=el('tr');
        [m.name+' / '+m.id,m.representation,m.assigned,m.unassigned,m.not_fitted,m.excluded]
          .forEach(x=>tr.append(el('td',x)));
        table.append(tr);
      }
      wrap.append(table);summary.append(wrap);
      const p=el('p','Verified metadata digest identities (not proof of source authenticity): source '+
        v.source+'; selection '+v.selection+'.');
      p.className='research-hint';summary.append(p);
      summary.hidden=false;
    }
    function download(name, text, mime) {
      const url=URL.createObjectURL(new Blob([text],{type:mime}));
      const a=doc.createElement('a');a.href=url;a.download=name;doc.body.append(a);
      a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }
    function display(bundle) {
      reset();
      try {
        const checked=inspect(bundle);
        // W5 and W6 validate separately; only the accepted W6 mounts evidence.
        const views=W6.mount(result,checked.envelope,bundle.panels);
        check(views.length===4, 'The evidence viewer did not retain all four panels.');
        views.forEach(view=>{
          const section=result.querySelector('[data-ev-kind="'+view.kind+'"]');
          if(!section)throw Error('Missing rendered evidence panel: '+view.kind);
          const controls=el('div');controls.className='research-exports';
          for(const kind of ['svg','html']){
            const button=el('button','Export '+kind.toUpperCase());
            button.className='research-export';button.type='button';
            button.addEventListener('click',()=>download('synthetic-'+view.kind+'.'+kind,
              kind==='svg'?view.svg:W6.htmlDocument(view),
              kind==='svg'?'image/svg+xml;charset=utf-8':'text/html;charset=utf-8'));
            controls.append(button);
          }
          section.append(controls);
        });
        renderSummary(checked);
        active=checked;
        setStatus('Accepted W5 and W6 source contracts passed. Four invented evidence views rendered; no model was fitted.');
        return checked;
      } catch(error) {
        reset();
        setStatus('Evidence rejected: '+error.message,true);
        return null;
      }
    }

    get('research-example').addEventListener('click',()=>{ input.value='';display(Fixture.fixture());});
    get('research-clear').addEventListener('click',()=>{
      reset();input.value='';setStatus('Cleared. No files or analysis were retained.');
    });
    input.addEventListener('change',()=>{reset();setStatus('A local file is selected but not yet inspected.');});
    get('research-open').addEventListener('click',async()=>{
      const selected=input.files?.[0],ticket=++generation;
      reset();
      // reset() advances the generation; retain its new value for async safety.
      const current=generation;
      if(!selected){setStatus('Choose a local synthetic bundle first.',true);return;}
      if(selected.size>MAX_BYTES){setStatus('Bundle exceeds 1 MiB; no partial input was processed.',true);return;}
      try {
        const raw=await selected.text();
        if(current!==generation)return;
        const imported=JSON.parse(raw.replace(/^\uFEFF/,''));
        if(current!==generation)return;
        display(imported);
      }catch(error){if(current===generation){reset();setStatus('Evidence rejected: '+error.message,true);}}
    });
    display(Fixture.fixture());
    return {display,clear:reset,get active(){return active;}};
  }

  const api=Object.freeze({inspect,summaryData,checkMetadataOnly,connect,MAX_BYTES});
  if(node)module.exports=api;
  else {
    root.UNResearchBrowser=api;
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>connect(document),{once:true});
    else connect(document);
  }
})(globalThis);
