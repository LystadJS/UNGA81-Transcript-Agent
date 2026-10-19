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
    if (/\b(?:support\w*|oppos\w*|reject\w*|condemn\w*|urg\w*|call for|endors\w*|welcome|express\w*|believ\w*|recogniz\w*|must|should|because|but|however)\b/i.test(text)) return false;
    const handoff=text.replace(/^(?:and )?now /i,'').replace(/^(?:i|we) (?:will|shall) (?:first |now )?/i,'I ');
    if (/^(?:(?:i|we) (?:now )?(?:give|yield) (?:the |our panelists the )floor\b[^;!?]*|(?:i|we) now call on\b[^;!?]*|(?:now )?you have the floor)[.!]?$/i.test(handoff)) return true;
    if (/^i thank (?:(?:the )?(?:distinguished |permanent |deputy )*(?:representative|delegate|ambassador|director)\b)[^;!?]*[.!]?$/i.test(text) &&
        !/\b(?:that|which|who|while|because|on sanctions|on weapons|for (?!arms control|disarmament affairs|(?:his |her |their |the )?(?:statement|remarks|briefing|presentation|participation|contribution|attention)\b))\b/i.test(text)) return true;
    const transitions=text.split(/,?\s+and\s+(?=(?:i|we)\s)/i);
    if(transitions.length>1 && transitions.every(proceduralSentence))return true;
    // Institutional names can be long; the action must still end the sentence.
    if (/^(?:the )?[\d,]+(?:st|nd|rd|th)? meeting of the [\p{L}\p{N},’'() -]{1,180} is (?:now )?(?:called to order|opened|adjourned|suspended|resumed)[.!]?$/iu.test(text)) return true;
    if (/^(?:(?:distinguished|dear) (?:delegates|colleagues|representatives|members)|excellencies)(?:,? (?:distinguished |dear )?(?:delegates|colleagues|representatives|members|excellencies))*[,.!]?$/i.test(text)) return true;
    if (/^(?:the )?full (?:version|text) of (?:this|my|our|the) statement (?:will be|is|has been) (?:submitted|made available|available)(?: to the secretariat| on eStatements)?[.!]?$/i.test(text)) return true;
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
  function summaryEvidenceSentence(line){
    // Meeting logistics may name a policy subject without discussing that subject.
    if(proceduralSentence(line) || /^(?:i|we) thank\b/i.test(line.trim()))return false;
    return !/^(?:in accordance with the (?:program|programme) of work|following the exchanges|this will be followed by|(?:distinguished delegates,? )?the next meeting|it is now my pleasure to extend a warm welcome|with this,? i now invite)\b/i.test(line.trim());
  }
  const api={tokens,wordCount,sentences,proceduralSentence,reduceProceduralNoise,summaryEvidenceSentence};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.UNTextUnits=api;
})(typeof globalThis!=='undefined'?globalThis:this);
