"""Read-only compatibility with proposed un.historical-source-audit.v1.

It accepts only source metadata and NEVER supplies empirical outcomes to a fit.
An audit receipt without independently verified original bytes is not authentication.
Distinct meeting designs, years, modalities or populations cannot be pooled.
"""
from __future__ import annotations
from collections import Counter,defaultdict
import re

FRAME_KEYS=('id','year','meeting_design','genre','language','translation_modality',
            'roster_definition','selection_design')
RECEIPT_KEYS=('document_id','meeting_id','year','available','transcript_available',
              'sha256','text_sha256')
OBS_KEYS=('id','frame_id','document_id','meeting_id','speech_id','country','year',
          'attribution','outcome_available','inclusion_probability','speech_length','text_sha256')
SHA=re.compile(r'^[0-9a-f]{64}$')


class IncompatibleCohort(ValueError):
    pass


def _string_fields(item,required,kind):
    if not isinstance(item,dict) or any(key not in item for key in required):
        raise IncompatibleCohort(f'incomplete {kind} manifest; missing field')
    for key in required:
        if key in ('year','available','transcript_available','outcome_available',
                   'inclusion_probability','speech_length'):
            continue
        if not isinstance(item[key],str) or not item[key].strip():
            raise IncompatibleCohort(f'empty/invalid {kind} identity: {key}')


def audit_manifest(m):
    if not isinstance(m,dict) or m.get('schema')!='un.historical-source-audit.v1':
        raise IncompatibleCohort('unsupported or missing proposed source audit contract')
    frames=m.get('frames');receipts=m.get('receipts');observations=m.get('observations')
    if not all(isinstance(v,list) for v in (frames,receipts,observations)) or not frames:
        raise IncompatibleCohort('source populations and receipt/observation arrays required')
    by_frame={}
    for f in frames:
        _string_fields(f,FRAME_KEYS,'frame')
        if not isinstance(f['year'],int) or not 2008<=f['year']<=2023 or f['id'] in by_frame:
            raise IncompatibleCohort('bad/duplicate frame or year')
        by_frame[f['id']]=f
    by_document={}
    for r in receipts:
        _string_fields(r,RECEIPT_KEYS,'receipt')
        if not isinstance(r['year'],int) or type(r['available'])!=bool or type(r['transcript_available'])!=bool:
            raise IncompatibleCohort('invalid receipt source/year availability')
        if not (SHA.fullmatch(r['sha256']) and SHA.fullmatch(r['text_sha256'])):
            raise IncompatibleCohort('source original/text SHA-256 identities not declared')
        if r['document_id'] in by_document:
            raise IncompatibleCohort('duplicate original document receipt')
        by_document[r['document_id']]=r
    totals=defaultdict(Counter);seen=set()
    for o in observations:
        _string_fields(o,OBS_KEYS,'observation')
        if o['id'] in seen:raise IncompatibleCohort('duplicate observation identity')
        seen.add(o['id'])
        f=by_frame.get(o['frame_id']);r=by_document.get(o['document_id'])
        if not f or not r or o['year']!=f['year'] or o['year']!=r['year'] or o['meeting_id']!=r['meeting_id']:
            raise IncompatibleCohort('invalid meeting-to-speech-to-frame/year lineage')
        p=o['inclusion_probability']
        if not isinstance(p,(int,float)) or isinstance(p,bool) or not 0<p<=1:
            raise IncompatibleCohort('unknown or nonpositive meeting selection probability')
        if not isinstance(o['speech_length'],int) or o['speech_length']<0 or type(o['outcome_available'])!=bool:
            raise IncompatibleCohort('invalid speech length/missingness status')
        if not SHA.fullmatch(o['text_sha256']):
            raise IncompatibleCohort('invalid text source identity')
        c=totals[f['id']];c['opportunities']+=1
        if not r['available']:c['document_unavailable']+=1
        elif not r['transcript_available']:c['transcript_unavailable']+=1
        elif not o['outcome_available']:c['outcome_missing']+=1
        elif r['text_sha256']!=o['text_sha256']:c['source_text_mismatch']+=1
        else:c['metadata_eligible']+=1
    # Entire populations are distinct by default: no implicit cross-era pooling.
    result=[]
    for f in frames:
        c=totals[f['id']]
        result.append({'frame_id':f['id'],'year':f['year'],'meeting_design':f['meeting_design'],
                       'population_definition':f['roster_definition'],
                       'genre':f['genre'],'language':f['language'],
                       'translation_modality':f['translation_modality'],
                       'selection_design':f['selection_design'],
                       **{key:int(c[key]) for key in ('opportunities','document_unavailable',
                         'transcript_unavailable','outcome_missing','source_text_mismatch','metadata_eligible')},
                       'original_source_bytes_independently_authenticated':False,
                       'statistical_fit_eligible':False})
    return {'schema':'un.temporal_calibration_v2.source_preflight.v1',
            'input_schema':m['schema'],'frames':result,'observations_attempted':len(observations),
            'original_source_bytes_inspected':0,'independent_second_phase_audit_verified':False,
            'pooling_authorized':False,'real_fit_authorized':False,'publication_eligible':False}


def assert_compatible_cohorts(a,b):
    """Use ONLY on separately authenticated population receipts, not generic frames."""
    keys=('schema_version','source_design_id','population_hash','representation_fingerprint',
          'year_definition','sampling_frame_hash','translation_policy','roster_definition')
    if not isinstance(a,dict) or not isinstance(b,dict) or any(
         not isinstance(x.get(k),str) or not x[k] for x in (a,b) for k in keys):
        raise IncompatibleCohort('separately authenticated comparable source population receipts required')
    if any(a[k]!=b[k] for k in keys):
        raise IncompatibleCohort('incompatible source designs, populations or representations')
    if a.get('independently_verified_original_bytes') is not True or b.get('independently_verified_original_bytes') is not True:
        raise IncompatibleCohort('original bytes not independently authenticated')
    if a.get('independent_nonresponse_outcome_audit') is not True or b.get('independent_nonresponse_outcome_audit') is not True:
        raise IncompatibleCohort('unidentified nonrandom transcript selection')
    # Even matching metadata is not permission to fit; separate authorisation needed.
    return {'source_metadata_comparable':True,'real_fit_authorized':False,
            'requires_separate_statistical_protocol':True}
