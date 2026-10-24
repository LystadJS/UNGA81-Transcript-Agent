"""Private read-only provisional review overlays, never accepted country positions."""
import hashlib
import json
from pathlib import Path
import re
from ..store.repository import canonical_bytes
from .transcripts_un_audit import audit_source
from .transcripts_un_batch import get_current_batch
from .sc_drafts import registry

VERSION='transcript-review-overlay-1'
ROW_FIELDS={'statement_number','json_pointer','text_sha256','locator_id','review_state','capacity','attribution_evidence','policy_matches','speech_boundary'}
MATCH_FIELDS={'policy_id','proposed_stance','context_id','discourse_labels','evidence','comparison_eligible'}
LABELS={'requested_action','reported_condition','claimed_implementation'}


def _digest(value): return hashlib.sha256(canonical_bytes(value)).hexdigest()


def build_review_overlay(store,raw,receipt,frame_entry,reviews):
    audit=audit_source(raw,receipt,frame_entry)
    batch=get_current_batch(store,audit['meeting_id'],audit['source_url'])
    if not batch or batch.get('source_sha256')!=audit['source_sha256'] or batch.get('audit_sha256')!=_digest(audit) or batch.get('audit_input_fingerprints')!=audit['input_fingerprints']: raise ValueError('Review requires exact current audited artifact batch')
    if not isinstance(reviews,list) or len(reviews)!=len(audit['segments']): raise ValueError('Every current segment must have exactly one review')
    source=json.loads(raw);segments={r['statement_number']:r for r in audit['segments']};codes,aliases,registry_sha=registry()
    seen=set();output=[];countries={};groups={}

    def evidence(items,segment,*,sentence_only=False):
        if not isinstance(items,list) or len(items)>30: raise ValueError('Evidence count exceeds bound')
        result=[];resolved=[];prefix=segment['json_pointer']+'/'
        for e in items:
            if not isinstance(e,dict) or set(e)!={'pointer','quote'}: raise ValueError('Evidence requires exact pointer and quote')
            pointer=e.get('pointer');quote=e.get('quote')
            if not isinstance(pointer,str) or not pointer.startswith(prefix) or not isinstance(quote,str) or not quote.strip() or len(quote)>1000: raise ValueError('Evidence is empty or outside its segment')
            sentence=bool(re.fullmatch(re.escape(segment['json_pointer'])+r'/paragraphs/(?:0|[1-9]\d*)/sentences/(?:0|[1-9]\d*)/text',pointer))
            if sentence_only and not sentence: raise ValueError('Sentence text evidence required')
            value=source
            try:
                for part in pointer.split('/')[1:]:
                    part=part.replace('~1','/').replace('~0','~')
                    if isinstance(value,list):
                        if not re.fullmatch(r'0|[1-9]\d*',part): raise ValueError('Noncanonical array pointer')
                        value=value[int(part)]
                    else:value=value[part]
            except (KeyError,IndexError,TypeError): raise ValueError('Evidence pointer cannot be resolved')
            if not isinstance(value,str) or quote not in value: raise ValueError('Evidence quote is not an exact source substring')
            result.append({'pointer':pointer,'quote_sha256':hashlib.sha256(quote.encode()).hexdigest()});resolved.append((pointer,quote,sentence))
        if len({(e['pointer'],e['quote_sha256']) for e in result})!=len(result): raise ValueError('Duplicate evidence entries')
        return result,resolved

    for row in reviews:
        if not isinstance(row,dict) or set(row)!=ROW_FIELDS: raise ValueError('Unsupported review row fields')
        number=row.get('statement_number')
        if type(number) is not int or number not in segments or number in seen: raise ValueError('Duplicate or unknown reviewed segment')
        seen.add(number);segment=segments[number]
        if any(row.get(k)!=segment[k] for k in ('json_pointer','text_sha256','locator_id')) or row.get('review_state')!='assistant_provisional' or row.get('speech_boundary')!='unverified': raise ValueError('Stale review identity or unsupported accepted label')
        capacity=row.get('capacity')
        if capacity not in ('national_candidate','collective','procedural','unclear'): raise ValueError('Unknown capacity proposal')
        attribution,resolved=evidence(row['attribution_evidence'],segment)
        if capacity!='unclear' and not attribution: raise ValueError('Capacity proposal needs source evidence')
        recorded=segment['recorded_speaker'];country=group=None
        function=re.sub(r'[^a-z]','',(recorded.get('function') or '').casefold())
        chair=function=='pga' or 'vicepresident' in function
        if capacity=='national_candidate':
            if chair or recorded.get('group') or not any(sentence for p,q,sentence in resolved): raise ValueError('National proposal conflicts with chair/group or lacks sentence evidence')
            affiliation=recorded.get('affiliation');full=recorded.get('affiliation_full');choices=set()
            if affiliation in codes:choices.add(affiliation)
            for name in (affiliation,full): choices.update(aliases.get(name,set()))
            if len(choices)!=1: raise ValueError('National proposal needs one explicit canonical source affiliation')
            country=codes[next(iter(choices))]
        elif capacity=='collective':
            group=recorded.get('group') or None
            if not group and not any(sentence and re.search(r'on behalf of|speaking for|represent(?:ing)?\s+(?:the|a)\s+group',q,re.I) for p,q,sentence in resolved): raise ValueError('Collective proposal lacks recorded group or explicit source mandate')
        matches=row.get('policy_matches')
        if not isinstance(matches,list) or len(matches)>30: raise ValueError('Policy proposal count exceeds bound')
        proposed=[]
        for match in matches:
            if not isinstance(match,dict) or set(match)!=MATCH_FIELDS or match.get('policy_id') not in ('humanitarian_access','civilian_protection') or match.get('proposed_stance') not in ('support','oppose','qualified',None) or match.get('context_id') is not None or match.get('comparison_eligible') is not False: raise ValueError('Unsupported policy proposal or resolved comparison')
            labels=match.get('discourse_labels')
            if not isinstance(labels,list) or not labels or any(label not in LABELS for label in labels) or len(set(labels))!=len(labels): raise ValueError('Explicit distinct discourse labels required')
            if match['proposed_stance'] is not None and 'requested_action' not in labels: raise ValueError('Conditions or implementation alone cannot establish normative stance')
            proof,_=evidence(match['evidence'],segment,sentence_only=True)
            if not proof: raise ValueError('Policy proposal needs exact sentence evidence')
            item={'policy_id':match['policy_id'],'proposed_stance':match['proposed_stance'],'context_id':None,'discourse_labels':sorted(labels),'evidence':proof,'comparison_eligible':False}
            item['candidate_id']='provisional-policy:'+_digest([segment['locator_id'],item]);proposed.append(item)
        if len({m['candidate_id'] for m in proposed})!=len(proposed): raise ValueError('Duplicate policy proposal')
        result={'statement_number':number,'locator_id':segment['locator_id'],'json_pointer':segment['json_pointer'],'text_sha256':segment['text_sha256'],
                'capacity_proposal':capacity,'country_entity':country,'group_entity':group,'attribution_evidence':attribution,
                'source_capacity':'unknown','policy_matches':proposed,'speech_boundary':'unverified','review_state':'assistant_provisional','attribution_accepted':False,'comparisons_eligible':False}
        output.append(result)
        target=None
        if country is not None:
            target=countries.setdefault(country,{'country':country,'capacity':'national_candidate','reviewed_segments':[],'requested_actions':[],'reported_conditions':[],'claimed_implementation':[],'accepted_position':False,'comparison_eligible':False})
        elif capacity=='collective':
            key=group if group is not None else segment['locator_id']
            target=groups.setdefault(key,{'group':group,'group_identity_status':'recorded_group' if group else 'unresolved','reviewed_segments':[],'requested_actions':[],'reported_conditions':[],'claimed_implementation':[],'accepted_position':False,'comparison_eligible':False})
        if target is not None:
            target['reviewed_segments'].append(number)
            for item in proposed:
                for label,field in (('requested_action','requested_actions'),('reported_condition','reported_conditions'),('claimed_implementation','claimed_implementation')):
                    if label in item['discourse_labels']:target[field].append({'statement_number':number,**item})
    if seen!=set(segments): raise ValueError('Missing current segment review')
    if get_current_batch(store,audit['meeting_id'],audit['source_url'])!=batch: raise ValueError('Current artifact batch changed during review validation')
    output.sort(key=lambda r:r['statement_number'])
    country_rows=[countries[k] for k in sorted(countries)];group_rows=[groups[k] for k in sorted(groups)]
    for target in country_rows+group_rows:target['reviewed_segments'].sort()
    return {'schema':'un.transcript-review-overlay.v1','version':VERSION,'meeting_id':audit['meeting_id'],'source_sha256':audit['source_sha256'],
            'source_modality':audit['source_modality'],'reviews':output,'countries':country_rows,'groups':group_rows,
            'summary':{'reviewed_segments':len(output),'national_candidate_countries':len(country_rows),'collective_groups':len(group_rows),
                       'requested_action_countries':sum(bool(c['requested_actions']) for c in country_rows),'reported_condition_countries':sum(bool(c['reported_conditions']) for c in country_rows),
                       'claimed_implementation_countries':sum(bool(c['claimed_implementation']) for c in country_rows),
                       'accepted_positions':0,'comparison_eligible':0},
            'accepted_positions':False,'attribution_accepted':False,'comparisons_eligible':False,'production_intake_accepted':False,'private_only':True,'context_resolution':'unresolved',
            'structural_validation_scope':'exact_source_linkage_only_not_semantic_label_or_attribution_truth',
            'input_fingerprints':{'raw_sha256':audit['source_sha256'],'batch_artifact_id':batch['batch_artifact_id'],'batch_sha256':_digest(batch),'reviews_sha256':_digest(reviews),
                                  'registry_sha256':registry_sha,'method_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('transcript_review.py','transcripts_un_audit.py','transcripts_un_batch.py','sc_drafts.py')}},
            'limitations':['All capacity and policy labels are assistant-provisional proposals, not accepted country positions.',
                           'Exact quote linkage does not independently validate semantic labels or national capacity.',
                           'Context remains unresolved; no policy agreement or U.S. comparison is computed.',
                           'Source ASR is not an official UN record, and speech boundaries remain unverified.',
                           'Country summaries count distinct proposed countries, not supporting passages.']}
