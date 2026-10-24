"""Private literal context proposals; structural linkage never accepts semantics."""
import hashlib
import json
from pathlib import Path
import re
from ..store.repository import canonical_bytes
from .transcript_review_v3 import build_review_overlay
from .transcripts_un_batch import get_current_batch

VERSION = 'transcript-context-overlay-1'
FIELDS = {'candidate_id','review_state','state','object_evidence','context_evidence','relation','reason'}
REASONS = {'no_literal_context','ambiguous_reference','insufficient_local_evidence'}

def _digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()

def _methods():
    names = ('transcript_context.py','transcript_review_v3.py','transcript_review_v2.py','transcript_review.py','transcripts_un_audit.py','transcripts_un_batch.py','sc_drafts.py')
    return {name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in names}

def build_context_overlay(store,raw,receipt,frame_entry,reviews,context_reviews):
    """Check exact literal locality, not the truth of proposed context or attribution."""
    methods = _methods()
    overlay = build_review_overlay(store,raw,receipt,frame_entry,reviews)
    source = json.loads(raw)
    original = {r['statement_number']:r for r in reviews}
    candidates = {}
    for row in overlay['reviews']:
        for index,match in enumerate(row['policy_matches']):
            cid = match['candidate_id']
            if cid in candidates: raise ValueError('Duplicate original policy candidate')
            candidates[cid] = (row,match,original[row['statement_number']]['policy_matches'][index])
    if not isinstance(context_reviews,list) or len(context_reviews)!=len(candidates):
        raise ValueError('Every policy candidate requires exactly one context proposal')
    output=[];seen=set()
    def proof(items,row):
        if not isinstance(items,list) or not items or len(items)>30: raise ValueError('Bounded nonempty evidence required')
        result=[];parsed=[];unique=set()
        pattern=re.escape(row['json_pointer'])+r'/paragraphs/(0|[1-9]\d*)/sentences/(0|[1-9]\d*)/text'
        for item in items:
            if not isinstance(item,dict) or set(item)!={'pointer','quote'}: raise ValueError('Exact pointer and quote fields required')
            pointer=item['pointer'];quote=item['quote']
            m=re.fullmatch(pattern,pointer) if isinstance(pointer,str) else None
            if not m or not isinstance(quote,str) or not quote.strip() or len(quote)>1000: raise ValueError('Invalid local sentence evidence')
            try:
                value=source
                for token in pointer.strip('/').split('/'): value=value[int(token)] if isinstance(value,list) else value[token]
            except (KeyError,IndexError,TypeError,ValueError): raise ValueError('Unresolvable evidence pointer')
            if not isinstance(value,str) or quote not in value: raise ValueError('Evidence must be an exact source substring')
            key=(pointer,quote)
            if key in unique: raise ValueError('Duplicate evidence')
            unique.add(key);parsed.append((int(m[1]),int(m[2]),pointer,quote))
            result.append({'pointer':pointer,'quote_sha256':hashlib.sha256(quote.encode('utf-8')).hexdigest()})
        return result,parsed
    for item in context_reviews:
        if not isinstance(item,dict) or set(item)!=FIELDS: raise ValueError('Unsupported context proposal fields')
        cid=item['candidate_id']
        if not isinstance(cid,str) or cid not in candidates or cid in seen: raise ValueError('Unknown or duplicate context candidate')
        seen.add(cid);row,match,original_match=candidates[cid]
        if item['review_state']!='assistant_provisional': raise ValueError('Only assistant provisional proposals are allowed')
        state=item['state'];relation=item['relation'];reason=item['reason']
        if state=='unresolved':
            if item['object_evidence']!=[] or item['context_evidence']!=[] or relation is not None or reason not in REASONS: raise ValueError('Unresolved context needs empty evidence and explicit reason')
            objects=contexts=[]
        elif state=='anchored':
            if reason is not None or relation not in ('same_sentence','adjacent_sentence_review'): raise ValueError('Anchored context requires local relation and null reason')
            objects,op=proof(item['object_evidence'],row);contexts,cp=proof(item['context_evidence'],row)
            for para,sent,pointer,quote in op:
                if not any(e['pointer']==pointer and quote in e['quote'] for e in original_match['evidence']): raise ValueError('Object must be inside existing policy-match evidence')
            distance=0 if relation=='same_sentence' else 1
            if any(not any(p==p2 and abs(s-s2)==distance for p2,s2,_,_ in op) for p,s,_,_ in cp): raise ValueError('Context evidence violates local sentence relation')
            if any(not any(p==p2 and abs(s-s2)==distance for p2,s2,_,_ in cp) for p,s,_,_ in op): raise ValueError('Object evidence lacks linked context')
        else: raise ValueError('Unknown context state')
        output.append({k:row[k] for k in ('statement_number','locator_id','text_sha256','capacity_proposal','country_entity','group_entity')} | {'candidate_id':cid,'policy_id':match['policy_id'],'proposed_stance':match['proposed_stance'],'discourse_labels':match['discourse_labels'],'state':state,'object_evidence':objects,'context_evidence':contexts,'relation':relation,'reason':reason,'review_state':'assistant_provisional','context_accepted':False,'comparisons_eligible':False})
    output.sort(key=lambda r:r['candidate_id'])
    batch=get_current_batch(store,overlay['meeting_id'],receipt['source_url'])
    if not batch or _digest(batch)!=overlay['input_fingerprints']['batch_sha256']: raise ValueError('Current batch changed during context validation')
    if _methods()!=methods: raise ValueError('Context methods changed during validation')
    anchored=[r for r in output if r['state']=='anchored']
    return {'schema':'un.transcript-context-overlay.v1','version':VERSION,'meeting_id':overlay['meeting_id'],'source_sha256':overlay['source_sha256'],'source_modality':overlay['source_modality'],'contexts':output,
        'summary':{'candidates':len(output),'anchored':len(anchored),'unresolved':len(output)-len(anchored),'anchored_country_candidates':len({r['country_entity'] for r in anchored if r['country_entity'] is not None}),'anchored_collective_entities':len({r['group_entity'] or r['locator_id'] for r in anchored if r['capacity_proposal']=='collective'}),'accepted_contexts':0,'comparison_eligible':0},
        'private_only':True,'owner_confirmed':False,'accepted_contexts':False,'accepted_positions':False,'comparisons_eligible':False,'production_intake_accepted':False,
        'structural_validation_scope':'exact_literal_linkage_not_semantic_context_or_causal_truth','canonical_context_status':'unresolved',
        'input_fingerprints':{'raw_sha256':overlay['source_sha256'],'batch_sha256':overlay['input_fingerprints']['batch_sha256'],'review_overlay_sha256':_digest(overlay),'reviews_sha256':_digest(reviews),'context_reviews_sha256':_digest(context_reviews),'registry_sha256':overlay['input_fingerprints']['registry_sha256'],'method_sha256':methods},
        'limitations':['Literal same or adjacent sentence anchors do not establish semantic or causal relations.','Context and capacity remain assistant-provisional; no canonical context or accepted country position is created.','Source ASR is not an official UN record; no accepted U.S. comparison is produced by this validator.']}
