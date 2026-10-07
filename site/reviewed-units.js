/* Local analysis bundles retain exact input bytes as UTF-8 strings. Re-derive,
 * do not trust an imported claim that a passage was reviewed or is unchanged. */
(function(root){
  'use strict';
  const C=typeof module!=='undefined'&&module.exports?require('./passage-pilot-core.js'):root.UNSpeechPilot;
  const encoder=new TextEncoder(),validated=new WeakSet();
  const assert=(ok,message)=>{if(!ok)throw Error(message);};
  const parse=text=>JSON.parse(text.replace(/^\uFEFF/,''));
  const stable=value=>JSON.stringify(order(value));
  function order(value){
    if(Array.isArray(value))return value.map(order);
    if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,order(value[k])]));
    return value;
  }
  const count=records=>({passages:records.length,parent_speeches:new Set(records.map(r=>r.parent_id)).size,meetings:new Set(records.map(r=>r.source_group)).size});
  async function audioAudit(ctx,review){
    C.review(ctx,review);
    const choices=new Map(review.choices.filter(c=>c.kind==='audio').map(c=>[c.id,c]));
    assert(ctx.data.audio.every(a=>choices.has(a.id)),'Complete the audio decisions first.');
    const records=ctx.data.audio.map(a=>{
      const c=choices.get(a.id),parent=ctx.parents.get(a.parent_id);
      return {id:a.id,parent_id:a.parent_id,parent_text_sha256:a.parent_text_sha256,
        parent_raw_sha256:parent.raw_sha256,original_start:a.start,original_end:a.end,
        offset_unit:ctx.data.offset_unit||'Unicode code points; zero-based; end exclusive',original_excerpt:a.original_excerpt,
        source_url:a.source_url,video_url:a.video_url,clip_sha256:a.clip_sha256,
        clip_start_seconds:a.clip_start_seconds,clip_end_seconds:a.clip_end_seconds,
        decision:c.decision,listened:c.listened===true,reviewer:c.reviewer,reviewed_at:c.reviewed_at,
        reviewer_note:c.note,correction_status:c.decision==='mismatch'?'recorded discrepancy; wording not applied':c.decision==='unclear'?'unresolved':'supported by owner check',
        replacement_text:null,originals_changed:false};
    });
    return {schema:'un.audio-review-ledger.v1',packet_sha256:ctx.packet_sha256,corpus_sha256:ctx.data.corpus_sha256,
      review_content_sha256:await C.digest(stable(review)),records,
      note_policy:'Notes are retained verbatim. They may describe a discrepancy or cover only part of the span; they are not automatic replacement text.',
      correction_policy:'Applying wording requires an explicit replacement span and text, a new source version and alignment to original offsets.',originals_changed:false};
  }
  async function load(bytes,validateCorpus,progress=async()=>{}){
    assert(bytes.byteLength<=30000000,'Choose a reviewed analysis bundle under 30 MB.');
    const bundle=parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
    assert(bundle.schema==='un.reviewed-speech-analysis.v1'&&typeof bundle.source_json==='string'&&typeof bundle.packet_json==='string'&&typeof bundle.review_json==='string','Use a reviewed speech analysis bundle (un.reviewed-speech-analysis.v1).');
    assert(encoder.encode(bundle.source_json).length<=20000000&&encoder.encode(bundle.packet_json).length<=12000000&&encoder.encode(bundle.review_json).length<=2000000,'Bundle input exceeds its size limit.');
    const original=validateCorpus(parse(bundle.source_json));
    assert(!original.reviewed_units&&!original.records.some(r=>r.parent_id),'Use the original parent collection, not another derived collection.');
    const corpusHash=await C.digest(bundle.source_json),ctx=await C.load(encoder.encode(bundle.packet_json));
    assert(ctx.data.corpus_sha256===corpusHash,'Review packet does not match the exact original collection bytes.');
    await progress('Checking original source text…');
    for(let i=0;i<original.records.length;i++){
      const r=original.records[i];assert(await C.digest(r.text)===r.text_sha256,'Original text hash mismatch: '+r.id);
      if(i%50===0)await progress('Checking original source text…');
    }
    const byId=new Map(original.records.map(r=>[r.id,r]));
    for(const p of ctx.data.parents){
      const r=byId.get(p.id);assert(r,'Review parent is missing from the original collection.');
      assert(/^[a-f0-9]{64}$/.test(r.raw_sha256||''),'Original parent needs a raw-source hash.');
      for(const field of ['text','text_sha256','raw_sha256','date','country','region','language','scope','meeting','source_url'])
        assert(r[field]===p[field],'Review parent differs from the original collection: '+field);
    }
    for(const a of ctx.data.audio){
      const p=byId.get(a.parent_id);
      assert(a.source_url===p.source_url&&a.source_snapshot_sha256===p.raw_sha256,'Audio concern differs from the original source record.');
      assert(typeof a.audio_base64==='string'&&a.audio_base64.length>0,'Audio evidence is missing from the review packet.');
    }
    const review=parse(bundle.review_json),units=await C.derive(ctx,review);
    assert(stable(units)===stable(bundle.units),'Reviewed units differ from the saved choices or exact source slices.');
    const ledger=await audioAudit(ctx,review);
    ledger.review_sha256=await C.digest(bundle.review_json);
    const records=units.records.map(u=>{
      const p=byId.get(u.parent_id);
      return {...u,review_scope:u.scope,scope:p.scope,language:p.language,meeting:p.meeting,
        raw_sha256:p.raw_sha256,parent_json_pointer:p.json_pointer};
    });
    const covered=[...new Set(records.map(r=>r.parent_id))].map(id=>{
      const p=byId.get(id),children=records.filter(r=>r.parent_id===id),total=Array.from(p.text).length,selected=children.reduce((s,r)=>s+r.end-r.start,0);
      return {parent_id:id,country:p.country,passages:children.length,selected_code_points:selected,parent_code_points:total,coverage_percent:100*selected/total};
    });
    const audioCounts=Object.fromEntries(['supported','mismatch','unclear'].map(k=>[k,ledger.records.filter(r=>r.decision===k).length]));
    const metadata={schema:'un.reviewed-unit-import.v1',bundle_sha256:await C.hash(bytes),corpus_sha256:corpusHash,
      packet_sha256:ctx.packet_sha256,review_sha256:await C.digest(bundle.review_json),units_sha256:await C.digest(stable(units)),
      ledger_sha256:await C.digest(stable(ledger)),selection:units.selection,input:count(records),coverage:covered,
      withheld:units.withheld,audio_decisions:audioCounts,originals_changed:false,
      interpretation:'Purposive boundary and inclusion pilot. Not a full speech partition, representative sample, relevance label or complete audio verification.',
      weighting:'Each included unique passage has equal weight; parents contributing more retained passages contribute more observations.',
      resampling:'Meeting or affiliation groups inherited from original parents keep all children of a parent together. Repeated excerpts are not independent speeches.'};
    const corpus={schema:'un.browser.corpus.v1',origin:'Reviewed speech excerpts from '+(original.origin||'imported collection'),
      collection:original.collection,coverage:original.coverage,records,reviewed_units:metadata};
    validateCorpus(corpus);
    // Freeze the validated result so later edits cannot retain validation status.
    function freeze(v){if(v&&typeof v==='object'&&!Object.isFrozen(v)){Object.values(v).forEach(freeze);Object.freeze(v);}return v;}
    freeze(corpus);validated.add(corpus);
    return {corpus,units,ledger};
  }
  async function create(source_json,packet_json,review_json,validateCorpus){
    const ctx=await C.load(encoder.encode(packet_json)),units=await C.derive(ctx,parse(review_json));
    const bundle={schema:'un.reviewed-speech-analysis.v1',source_json,packet_json,review_json,units};
    const bytes=encoder.encode(JSON.stringify(bundle));
    return {bytes,...await load(bytes,validateCorpus)};
  }
  const api={load,create,audioAudit,count,stable,isValidated:corpus=>validated.has(corpus)};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNReviewedUnits=api;
})(globalThis);
