"""Invented, metadata-only v1 interface fixture; no source transcripts."""
from dataclasses import replace
from hashlib import sha256
import json

from bridge import UpstreamValidation, digest


def h(x: bytes) -> str:
    return sha256(x).hexdigest()


def source_text(id: str) -> str:
    return f"Fictional {id} metadata source: no UN content; café 🌐 synthetic lexical pattern."


def original(text: str) -> bytes:
    return json.dumps({'records':[{'text':text}]}, ensure_ascii=False, sort_keys=True).encode('utf-8')


def make_fixture(readout):
    ids = ('synthetic-A','synthetic-B')
    sources={}
    obs=[]
    evidence=[]
    for id in ids:
        text=source_text(id)
        proof=readout.SourceReceipt(source_id=id, original_bytes=original(text), text=text,
            representation_id='synthetic-rep-v1', parent_id='parent-'+id,
            accepted=True, public=True, source_url='https://example.invalid/'+id,
            json_pointer='/records/0/text', collective=False, meeting_id='fictional-meeting',
            speech_id=None,source_family_id='fictional-family-'+id)
        sources[id]=proof
        obs.append({'id':id,'text_sha256':h(text.encode('utf-8')),
          'parent_id':proof.parent_id,'parent_text_sha256':h(text.encode('utf-8')),
          'meeting_id':proof.meeting_id,'speech_id':None,'source_family_id':proof.source_family_id,
          'date':'2026-10-01' if id==ids[0] else '2026-10-02',
          'country':None,'source_url':proof.source_url,'json_pointer':proof.json_pointer,
          'start':0,'end':len(text),'unit':'synthetic','review_status':'not_applicable',
          'exclusion_reasons':[],'source_status':'available','missing_reason':None})
        evidence.append({'observation_id':id,'source_url':proof.source_url,
          'json_pointer':proof.json_pointer,'start':0,'end':6 if id==ids[0] else 8,
          'role':'representative' if id==ids[0] else 'contrary',
          'proposition_id':None,'verification':'synthetic'})
    obs.append({'id':'synthetic-C','text_sha256':h(b'excluded'), 'parent_id':None,
      'parent_text_sha256':None,'meeting_id':'fictional-meeting','speech_id':None,
      'source_family_id':None,'date':'2026-10-02','country':None,'source_url':None,
      'json_pointer':None,'start':None,'end':None,'unit':'synthetic','review_status':'unreviewed',
      'exclusion_reasons':['procedural'],'source_status':'available','missing_reason':None})
    obs.append({'id':'synthetic-D','text_sha256':None,'parent_id':None,
      'parent_text_sha256':None,'meeting_id':None,'speech_id':None,'source_family_id':None,
      'date':'2026-10-02','country':None,'source_url':None,'json_pointer':None,
      'start':None,'end':None,'unit':'synthetic','review_status':'unreviewed',
      'exclusion_reasons':[],'source_status':'unavailable','missing_reason':'synthetic_unavailable'})
    modelid='synthetic-model-1'
    envelope={
      'schema':'un.parallel-analysis.v1','contract_version':'1.0.0',
      'producer':{'workstream_id':'W1','adapter_version':'synthetic-bridge-1',
        'code_sha256':'a'*64,'runtime':'python-3.13','generated_at':'2026-10-15T00:00:00Z',
        'fixture_kind':'synthetic'},
      'upstream':{'source_schema':'synthetic.v1','source_engine':'synthetic-fixture',
        'source_hash_basis':'synthetic','source_sha256':h(b'synthetic-original-collection'),
        'frame_sha256':None,'corpus_sha256':None,
        'selection_sha256':h(b'selected-fixed-invented-frame'),
        'review_sha256':None,'missing_reason':None},
      'cohort':{'split':'synthetic','population':'Five invented source identities',
        'unit':'synthetic','selection_policy':'static synthetic population',
        'weighting':'equal_passage','source_group_unit':'synthetic',
        'duplicate_policy':'retain_and_audit','total_in_frame':5,'eligible':2},
      'observations':obs,
      'models':[{'model_id':modelid,'method_family':'partition','method':'pam',
        'representation_id':'synthetic-rep-v1','representation_version':'1',
        'fit_version':'1','fit_split':'synthetic','parameters_sha256':'b'*64,
        'training_selection_sha256':h(b'selected-fixed-invented-frame'),
        'diagnostic_basis':'invented synthetic fit'}],
      'results':[
        {'model_id':modelid,'observation_id':oid,'status':status,'cluster':cluster,
        'membership_kind':'none','memberships':None,'membership_strength':None,
        'representation_basis_id':'synthetic-rep-v1','reason':reason}
        for oid,status,cluster,reason in [
          ('synthetic-A','assigned',1,None),('synthetic-B','unassigned',0,'synthetic noise'),
          ('synthetic-C','excluded',None,'synthetic selection exclusion'),
          ('synthetic-D','excluded',None,'synthetic unavailable')]],
      'coverage':{'inventory_meetings':1,'observations_total':4,'eligible':2,
        'excluded':2,'unavailable_sources':1,
        'models':[{'model_id':modelid,'eligible':2,'assigned':1,'unassigned':1,
          'not_fitted':0,'excluded':2,'attempted_fits':1,'successful_fits':1,
          'failed_fits':0}], 'failure_ledger':[]},
      'evidence':evidence,
      'diagnostics':[{'model_id':modelid,'name':'synthetic_coverage','value':1,
        'denominator':2,'unit':'observation','status':'descriptive','reason':None}],
      'limitations':[{'code':'synthetic_only','scope':'all',
        'description':'Synthetic example only; no real-source policy inference.'}],
      'publication_eligible':False,'evaluation_role':'engineering_only'
    }
    approval=UpstreamValidation(envelope_sha256=digest(envelope),
      source_schema=envelope['upstream']['source_schema'],
      source_hash_basis=envelope['upstream']['source_hash_basis'],
      source_sha256=envelope['upstream']['source_sha256'],
      selection_sha256=envelope['upstream']['selection_sha256'])
    intent={
      'title':'FICTIONAL source-bound readout',
      'template':'emerging_themes', 'model_id':modelid,
      'uncertainty':'No independent statistical calibration has been performed',
      'sensitivity':'Not tested on another source population',
      'alternative_explanations':'Shared fictional source formatting and duplicated vocabulary',
      'reviewer_note':'Fictional methodological caution, not an empirical position',
      'findings':[{'id':'fictional-f1','category':'descriptive',
        'label':'Invented source-language comparison',
        'observation':'One invented source contains an identified synthetic phrase',
        'pattern':None,'reviewer_interpretation':None,
        'supporting':['synthetic-A'],'contrary':['synthetic-B'],
        'contrary_search':'identified',
        'uncertainty':'No extrapolation to real UN speech is authorized',
        'sensitivity':'Different invented text would produce different evidence',
        'alternative_explanations':'The document generator determines source vocabulary',
        'country_attribution':None,'stance':None}]}
    return envelope,intent,sources,approval


def reaffirm(envelope, old):
    """Synthetic-only consistency receipt after a deliberate test mutation."""
    return replace(old,envelope_sha256=digest(envelope),
      source_sha256=envelope['upstream']['source_sha256'],
      selection_sha256=envelope['upstream']['selection_sha256'])
