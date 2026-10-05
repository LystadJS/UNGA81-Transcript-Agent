/* Explicit reviewed inclusion policy; the original collection is never rewritten. */
(function(root){
  'use strict';
  const TYPES=['substantive_speech','mixed_speech_procedure','right_of_reply','procedure','speech_fragment','suspected_transcription_issue','uncertain'];
  function validate(corpus,selection){
    if(!selection)return null;
    const {policy,review,corpus_sha256}=selection;
    if(!['substantive','inclusive'].includes(policy))throw Error('Choose a supported reviewed inclusion policy.');
    if(!review||review.schema!=='un.passage-type-review.v1'||!/^[a-f0-9]{64}$/.test(corpus_sha256||'')||review.corpus_sha256!==corpus_sha256)throw Error('Review does not match the saved collection bytes.');
    const choices=review.choices,original=new Map(corpus.records.map(r=>[r.id,r]));
    if(!Array.isArray(choices)||choices.length!==original.size||new Set(choices.map(c=>c.id)).size!==original.size)throw Error('Review must explicitly confirm every original passage exactly once.');
    for(const c of choices){
      if(original.get(c.id)?.text_sha256!==c.text_sha256||c.confirmed!==true||!TYPES.includes(c.type)||typeof c.reviewer!=='string'||!c.reviewer.trim()||!/(Z|[+-]\d\d:\d\d)$/.test(c.reviewed_at||'')||!Number.isFinite(Date.parse(c.reviewed_at))||Date.parse(c.reviewed_at)>Date.now()+300000)throw Error('Invalid or changed passage review decision.');
    }
    const included=policy==='substantive'?['substantive_speech']:['substantive_speech','mixed_speech_procedure','speech_fragment'];
    const selected=new Set(choices.filter(c=>included.includes(c.type)).map(c=>c.id));
    return {selected,policy,included_types:included,corpus_sha256,review_sha256:selection.review_sha256||null,human_confirmed:choices.length,
      excluded_ids:corpus.records.filter(r=>!selected.has(r.id)).map(r=>r.id)};
  }
  const api={TYPES,validate};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNPassageSelection=api;
})(globalThis);
