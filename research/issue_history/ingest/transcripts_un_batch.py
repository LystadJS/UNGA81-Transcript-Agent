"""Atomic private artifact-bound ASR segment batches, never stable speech intake."""
import hashlib
import json
from pathlib import Path
from ..store.repository import canonical_bytes,stable_id
from .transcripts_un_audit import audit_source,VERSION as AUDIT_VERSION

VERSION='transcripts-un-batch-1'
KIND='transcripts_un_batch'


def _digest(value): return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _methods():
    return {name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('transcripts_un_audit.py','transcripts_un_batch.py')}


def _source(store,sid,revision):
    row=store.db.execute('SELECT r.payload FROM sources s JOIN source_revisions r ON r.id=s.id AND r.revision=s.revision WHERE s.id=? AND s.revision=?',(sid,revision)).fetchone()
    if not row: raise ValueError('Batch source revision is no longer current')
    payload=json.loads(row[0]);base=dict(payload);base.pop('revision',None)
    if payload.get('revision')!=revision or _digest(base)!=revision: raise ValueError('Batch source metadata hash mismatch')
    return base


def _artifact(store,aid,kind,payload,dependencies):
    row=store.db.execute('SELECT kind,valid,payload FROM artifacts WHERE id=?',(aid,)).fetchone()
    actual={r[0] for r in store.db.execute('SELECT dependency_id FROM dependencies WHERE artifact_id=?',(aid,))}
    if not row or row[0]!=kind or row[1]!=1 or json.loads(row[2])!=payload or actual!=set(dependencies) or aid!=stable_id(kind,payload,sorted(set(dependencies))): raise ValueError('Batch provenance artifact or dependency mismatch')


def get_current_batch(store,meeting_id,source_url):
    """Revalidate authoritative manifest, complete membership and provenance."""
    parent_id=stable_id('un-transcript-artifact',meeting_id,source_url)
    current=store.db.execute('SELECT revision FROM sources WHERE id=?',(parent_id,)).fetchone()
    if not current: return None
    revision=current[0];parent=_source(store,parent_id,revision)
    if parent.get('family')!='un_transcript_artifact' or parent.get('access')!='private' or parent.get('countries')!=[] or parent.get('meeting_id')!=meeting_id or parent.get('url')!=source_url or parent.get('production_intake_accepted') is not False or parent.get('source_role')!='product_development' or parent.get('method_sha256')!=_methods() or parent.get('audit_version')!=AUDIT_VERSION: raise ValueError('Invalid current parent artifact metadata or method pin')
    candidates=[]
    for row in store.db.execute('SELECT a.id,a.payload FROM artifacts a JOIN dependencies d ON d.artifact_id=a.id WHERE a.kind=? AND a.valid=1 AND d.dependency_id=?',(KIND,parent_id)):
        payload=json.loads(row[1])
        if payload.get('parent_source_revision')==revision: candidates.append((row[0],payload))
    if len(candidates)!=1: raise ValueError('Exactly one valid current batch manifest required')
    aid,payload=candidates[0];members=payload.get('members')
    if payload.get('schema')!='un.transcripts-un-batch.v1' or payload.get('version')!=VERSION or payload.get('parent_source_id')!=parent_id or payload.get('meeting_id')!=meeting_id or payload.get('source_url')!=source_url or payload.get('source_sha256')!=parent['content_hash'] or payload.get('audit_sha256')!=parent.get('audit_sha256') or payload.get('method_sha256')!=parent.get('method_sha256') or payload.get('comparisons_eligible') is not False or payload.get('production_intake_accepted') is not False or not isinstance(members,list) or len(members)>10000 or type(payload.get('member_count')) is not int or payload['member_count']!=len(members) or payload['member_count']!=parent.get('segment_count') or payload.get('member_set_sha256')!=_digest(sorted(members,key=lambda m:m['source_id'])): raise ValueError('Invalid current batch manifest')
    if len({m.get('source_id') for m in members})!=len(members) or len({m.get('statement_number') for m in members})!=len(members) or {m.get('statement_number') for m in members}!=set(range(1,len(members)+1)): raise ValueError('Duplicate or incomplete batch membership')
    parent_proof=payload.get('parent_provenance_artifact_id');parent_provenance={'schema':'un.transcript-parent-provenance.v1','version':VERSION,'source_id':parent_id,'source_revision':revision,'audit_sha256':parent['audit_sha256'],'source_sha256':parent['content_hash'],'method_sha256':parent['method_sha256'],'private_only':True}
    _artifact(store,parent_proof,'transcript_parent_provenance',parent_provenance,[parent_id])
    for index,member in enumerate(members):
        sid=member.get('source_id');child=_source(store,sid,member.get('source_revision'))
        locator='artifact-segment:'+_digest([parent['content_hash'],parent['transcript_id'],member['statement_number']])
        if child.get('json_pointer')!='/transcript/data/'+str(index) or child.get('source_role')!='product_development' or child.get('identity_scope')!='immutable_artifact_bound_segment_not_stable_speech': raise ValueError('Batch segment scope or JSON pointer mismatch')
        if child.get('family')!='un_transcript_segment' or child.get('access')!='private' or child.get('countries')!=[] or child.get('capacity')!='unknown' or child.get('national_capacity') is not False or child.get('stable_identity_verified') is not False or child.get('comparisons_eligible') is not False or child.get('production_intake_accepted') is not False or child.get('parent_source_id')!=parent_id or child.get('parent_source_revision')!=revision or child.get('statement_number')!=member['statement_number'] or child.get('meeting_id')!=meeting_id or child.get('url')!=source_url or child.get('artifact_sha256')!=parent['content_hash'] or child.get('audit_sha256')!=parent['audit_sha256'] or child.get('artifact_bound_locator_id')!=locator or sid!=stable_id('un-transcript-segment',locator): raise ValueError('Batch member linkage mismatch')
        proof={'schema':'un.transcript-segment-provenance.v1','version':VERSION,'source_id':sid,'source_revision':member['source_revision'],'parent_source_id':parent_id,'parent_source_revision':revision,'parent_provenance_artifact_id':parent_proof,'artifact_bound_locator_id':child['artifact_bound_locator_id'],'audit_sha256':parent['audit_sha256'],'private_only':True}
        _artifact(store,member.get('provenance_artifact_id'),'transcript_segment_provenance',proof,[parent_id,sid,parent_proof])
    actual={r[0] for r in store.db.execute("SELECT s.id FROM sources s JOIN source_revisions r ON r.id=s.id AND r.revision=s.revision WHERE json_extract(r.payload,'$.family')='un_transcript_segment' AND json_extract(r.payload,'$.parent_source_id')=? AND json_extract(r.payload,'$.parent_source_revision')=?",(parent_id,revision))}
    if actual!={m['source_id'] for m in members}: raise ValueError('Unlisted or missing current batch members')
    _artifact(store,aid,KIND,payload,[parent_id,parent_proof,*[m['provenance_artifact_id'] for m in members]])
    return {**payload,'schema':'un.transcripts-un-current-batch.v1','batch_artifact_id':aid}


def persist_artifact(store,raw_bytes,receipt,frame_entry):
    """Audit whole supplied bytes before one all-or-nothing metadata write."""
    audit=audit_source(raw_bytes,receipt,frame_entry);audit_hash=_digest(audit);methods=_methods()
    mid=audit['meeting_id'];url=audit['source_url'];parent_id=stable_id('un-transcript-artifact',mid,url)
    body='SC' if mid.startswith('sc/') else 'GA_C'+mid.split('/')[1][1:] if mid.startswith(tuple('ga/c'+str(i)+'/' for i in range(1,7))) else 'GA'
    parent={'id':parent_id,'published_date':audit['date'],'body':body,'family':'un_transcript_artifact','url':url,'content_hash':audit['source_sha256'],'access':'private','countries':[],
            'meeting_id':mid,'audit_sha256':audit_hash,'audit_version':AUDIT_VERSION,'method_sha256':methods,'input_fingerprints':audit['input_fingerprints'],
            'transcript_id':audit['transcript_id'],'segment_count':audit['summary']['segments'],
            'published_transcript_language':audit['published_transcript_language'],'video_id':audit['video_id'],
            'source_modality':audit['source_modality'],'disclaimer_sha256':audit['disclaimer_sha256'],'source_role':'product_development','production_intake_accepted':False}
    parent_revision=_digest(parent);children=[]
    for segment in audit['segments']:
        sid=stable_id('un-transcript-segment',segment['locator_id'])
        child={'id':sid,'published_date':audit['date'],'body':body,'family':'un_transcript_segment','url':url,'content_hash':segment['text_sha256'],'access':'private','countries':[],
               'meeting_id':mid,'parent_source_id':parent_id,'parent_source_revision':parent_revision,'artifact_sha256':audit['source_sha256'],'audit_sha256':audit_hash,
               'artifact_bound_locator_id':segment['locator_id'],'statement_number':segment['statement_number'],'json_pointer':segment['json_pointer'],
               'text_sha256':segment['text_sha256'],'recorded_speaker':segment['recorded_speaker'],'capacity':'unknown','national_capacity':False,
               'stable_identity_verified':False,'comparisons_eligible':False,'production_intake_accepted':False,'source_role':'product_development',
               'identity_scope':'immutable_artifact_bound_segment_not_stable_speech','adapter_version':VERSION}
        children.append((child,_digest(child)))
    if len({c['id'] for c,r in children})!=len(children): raise ValueError('Duplicate derived artifact locators')
    with store.transaction():
        for source,rev in [(parent,parent_revision),*children]:
            current=store.db.execute('SELECT revision FROM sources WHERE id=?',(source['id'],)).fetchone()
            historical=store.db.execute('SELECT 1 FROM source_revisions WHERE id=? AND revision=?',(source['id'],rev)).fetchone()
            if current and current[0]!=rev and historical: raise ValueError('Known historical artifact batch requires explicit replay review')
        if store.upsert_source(parent)!=parent_revision: raise ValueError('Parent revision contract mismatch')
        parent_provenance={'schema':'un.transcript-parent-provenance.v1','version':VERSION,'source_id':parent_id,'source_revision':parent_revision,'audit_sha256':audit_hash,'source_sha256':audit['source_sha256'],'method_sha256':methods,'private_only':True}
        parent_proof=store.put_artifact('transcript_parent_provenance',parent_provenance,[parent_id])
        if not store.artifact_valid(parent_proof): raise ValueError('Invalidated parent provenance cannot be accepted')
        members=[]
        for child,revision in children:
            if store.upsert_source(child)!=revision: raise ValueError('Child revision contract mismatch')
            proof={'schema':'un.transcript-segment-provenance.v1','version':VERSION,'source_id':child['id'],'source_revision':revision,'parent_source_id':parent_id,'parent_source_revision':parent_revision,'parent_provenance_artifact_id':parent_proof,'artifact_bound_locator_id':child['artifact_bound_locator_id'],'audit_sha256':audit_hash,'private_only':True}
            proof_id=store.put_artifact('transcript_segment_provenance',proof,[parent_id,child['id'],parent_proof])
            if not store.artifact_valid(proof_id): raise ValueError('Invalidated segment provenance cannot be accepted')
            members.append({'source_id':child['id'],'source_revision':revision,'provenance_artifact_id':proof_id,'statement_number':child['statement_number']})
        manifest={'schema':'un.transcripts-un-batch.v1','version':VERSION,'meeting_id':mid,'source_url':url,'source_sha256':audit['source_sha256'],
                  'parent_source_id':parent_id,'parent_source_revision':parent_revision,'parent_provenance_artifact_id':parent_proof,
                  'members':members,'member_count':len(members),'member_set_sha256':_digest(sorted(members,key=lambda m:m['source_id'])),'audit_sha256':audit_hash,'method_sha256':methods,
                  'audit_input_fingerprints':audit['input_fingerprints'],'gaps':audit['gaps'],'source_modality':audit['source_modality'],
                  'identity_scope':'immutable_artifact_bound_segments_not_stable_speeches','comparisons_eligible':False,'production_intake_accepted':False,'private_only':True,
                  'completeness_scope':'whole_supplied_artifact_only_not_server_meeting_or_archive_completeness'}
        batch_id=store.put_artifact(KIND,manifest,[parent_id,parent_proof,*[m['provenance_artifact_id'] for m in members]])
        if not store.artifact_valid(batch_id): raise ValueError('Invalidated batch manifest cannot be accepted')
        result=get_current_batch(store,mid,url)
    return result
