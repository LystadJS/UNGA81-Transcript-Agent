/* Shared descriptive text units. Originals and source hashes are never modified. */
(function(root){
  'use strict';
  const tokens = text => String(text || '').normalize('NFKC').toLowerCase().match(/[\p{L}\p{N}]+/gu) || [];
  const wordCount = text => tokens(text).length;
  function sentences(text){
    // Protect common speaker honorifics so 'Thank you, Mr. Chair.' is one unit.
    return String(text || '').replace(/\s+/g,' ').trim()
      .replace(/\b(Mr|Mrs|Ms|Dr|Prof)\./g,'$1\uE000')
      .split(/(?<=[.!?])\s+(?=[\p{Lu}\d"“])/u)
      .map(line=>line.replace(/\uE000/g,'.')).filter(Boolean);
  }
  function proceduralSentence(sentence){
    const text=sentence.trim().replace(/^and\s+/i,'');
    if (wordCount(text)>65) return false;
    // Do not remove policy-bearing courtesy clauses or mixed action sentences.
    if (/\b(?:support|oppose|reject|condemn|urge|call for|endorse|welcome|express|believe|recognize|must|should|because|but|however)\b/i.test(text)) return false;
    const transitions=text.split(/,?\s+and\s+(?=(?:i|we)\s)/i);
    if(transitions.length>1 && transitions.every(proceduralSentence))return true;
    return /^(?:thank you(?:,?\s+(?:(?:Mr|Madam|Ms|Mrs)\.?\s+)?(?:Chair(?:person)?|President|Secretary(?:-General)?|Ambassador|Minister))?(?:,? for giving (?:me|us) the floor)?[.!]?|good (?:morning|afternoon|evening)(?:,?\s+(?:colleagues|everyone|excellencies))?[.!]?)$/i.test(text) ||
      /^i thank (?:the |all |our )?(?:previous speaker|speakers?|representatives?|delegates?|delegations?|president|chair(?:person)?|secretary-general|ambassador|minister)(?: of [\p{L}’'’-]+(?: [\p{L}’'’-]+){0,5})? for (?:his |her |their |the |that |this |your )?(?:informative |comprehensive |detailed |helpful )?(?:statement|remarks|briefing|presentation|participation|contribution|attention)[.!]?$/iu.test(text) ||
      /^i thank (?:Mr|Mrs|Ms|Dr|Prof)\.? [\p{L}’'’-]+(?: [\p{L}’'’-]+){0,5} for (?:his |her |their |the |that |this |your )?(?:informative |comprehensive |detailed |helpful )?(?:statement|remarks|briefing|presentation|participation|contribution|attention)[.!]?$/iu.test(text) ||
      /^(?:(?:i|we) (?:now |shall now |will now )?(?:give|yield) the floor|i now invite\b[^.!?]*\bto take the floor|the floor is (?:now )?(?:given to|yours)|(?:the )?next speaker is)\b[^;!?]*[.!]?$/i.test(text) ||
      /^(?:the )?(?:[\d,]+(?:st|nd|rd|th)? )?(?:meeting|session)(?: of the (?:security council|general assembly|committee|council|assembly))? is (?:now )?(?:called to order|opened|adjourned|suspended|resumed)[.!]?$/i.test(text) ||
      /^(?:the )?(?:security council|general assembly|committee|council|assembly) (?:will|shall) now (?:begin|resume|continue|take up) (?:its |the )?(?:consideration|discussion|meeting|agenda item)\b[^;!?]*[.!]?$/i.test(text);
  }
  function reduceProceduralNoise(text){
    const lines=sentences(text), retained=lines.filter(line=>!proceduralSentence(line));
    return {text:retained.join(' '),removed_sentence_count:lines.length-retained.length};
  }
  const api={tokens,wordCount,sentences,proceduralSentence,reduceProceduralNoise};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNTextUnits=api;
})(typeof globalThis!=='undefined'?globalThis:this);
