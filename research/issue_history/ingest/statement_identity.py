"""Private development statement identities; not accepted production intake."""
import hashlib
import re
from ..store.repository import canonical_bytes,stable_id
from .statement_coverage import MEETING_FIELDS,RECEIPT_FIELDS,_sha,_date

VERSION='statement-identity-1'
IDENTITY_SCHEME='artifact-local-native-statement-1'
VERIFICATION_SCOPE='normalized_text_hash_and_declared_parent_receipt_not_independent_source_authentication'
FIELDS={'schema','parent_meeting','inventory_metadata_sha256','artifact_receipt','native_statement_id','identity_scheme_version','language','text','text_sha256','speaker','source_role'}


def _digest(value): return hashlib.sha256(canonical_bytes(value)).hexdigest()


def normalize_statement(row):
    """Recompute normalized text hash, structurally bind declared parent receipts."""
    if not isinstance(row,dict) or not FIELDS<=set(row) or set(row)-FIELDS-{'source_id'} or row.get('schema')!='un.normalized-statement.v1' or row.get('source_role')!='product_development': raise ValueError('Unsupported statement development contract')
    m=row.get('parent_meeting');r=row.get('artifact_receipt');speaker=row.get('speaker')
    if not isinstance(m,dict) or set(m)!=MEETING_FIELDS or not isinstance(r,dict) or set(r)!=RECEIPT_FIELDS or r.get('schema')!='un.statement-artifact-receipt.v1': raise ValueError('Exact parent meeting and extraction receipt required')
    mid=m.get('meeting_id');date=m.get('date')
    if not isinstance(mid,str) or len(mid)>500 or not re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+){1,5}',mid) or not _date(date) or date in ('2026-10-05','2026-10-06'): raise ValueError('Invalid or reserved parent meeting')
    body='SC' if mid.startswith('sc/') else 'GA_C'+mid.split('/')[1][1:] if re.match(r'ga/c[1-6]/',mid) else 'GA' if mid.startswith('ga/') else 'other'
    if body=='other' or m.get('body')!=body or type(m.get('transcript_advertised')) is not bool or any(m[k] is not None and (not isinstance(m[k],str) or len(m[k])>300) for k in ('recorded_body','category')): raise ValueError('Parent body metadata mismatch')
    for key,suffix in (('pageUrl',''),('jsonUrl','.json'),('textUrl','.txt')):
        if m[key] is not None and m[key]!='https://transcripts.un.org/en/'+mid+suffix: raise ValueError('Parent artifact URL mismatch')
    if not _sha(row.get('inventory_metadata_sha256')) or any(r.get(k)!=v for k,v in (('meeting_id',mid),('date',date),('body',body),('inventory_metadata_sha256',row['inventory_metadata_sha256']))): raise ValueError('Parent receipt inventory identity mismatch')
    if r.get('source_url') is None or r['source_url'] not in (m['jsonUrl'],m['textUrl']) or any(r.get(k) is not True for k in ('retrieved','hash_verified','extraction_complete')) or not _sha(r.get('source_sha256')) or r.get('expected_sha256')!=r['source_sha256'] or not _sha(r.get('normalized_sha256')) or not isinstance(r.get('extraction_method_version'),str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',r['extraction_method_version']): raise ValueError('Complete declared artifact/extraction chain required')
    native=row.get('native_statement_id');language=row.get('language')
    if row.get('identity_scheme_version')!=IDENTITY_SCHEME or not isinstance(native,str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,200}',native) or not isinstance(language,str) or not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*',language) or len(language)>35: raise ValueError('Stable native statement identity and language required')
    text=row.get('text')
    if not isinstance(text,str) or not text.strip() or len(text.encode('utf-8'))>2_000_000 or not _sha(row.get('text_sha256')) or hashlib.sha256(text.encode('utf-8')).hexdigest()!=row['text_sha256']: raise ValueError('Normalized statement text hash mismatch')
    if not isinstance(speaker,dict) or set(speaker)!={'name','capacity','recorded_affiliation','country','group'} or speaker.get('capacity') not in ('national','collective','unknown'): raise ValueError('Explicit speaker capacity metadata required')
    if any(v is not None and (not isinstance(v,str) or not v.strip() or len(v)>500) for k,v in speaker.items() if k!='capacity'): raise ValueError('Invalid recorded speaker metadata')
    from .sc_drafts import registry
    country_registry=registry();countries=set(country_registry[0].values())
    capacity=speaker['capacity']
    if capacity=='national':
        if speaker['country'] not in countries or speaker['group'] is not None: raise ValueError('National capacity requires explicit canonical country only')
    elif speaker['country'] is not None or (capacity=='collective' and not speaker['group']) or (capacity=='unknown' and speaker['group'] is not None): raise ValueError('Collective or unknown capacity cannot become national attribution')
    source_id=stable_id('un-native-statement',mid,native,IDENTITY_SCHEME,language,r['source_url'])
    if 'source_id' in row and row['source_id']!=source_id: raise ValueError('Caller supplied statement source identity is forged')
    parent_id=stable_id('un-statement-parent-artifact',mid,r['source_url'])
    parent={'id':parent_id,'published_date':date,'body':body,'family':'un_statement_artifact','url':r['source_url'],
            'content_hash':r['source_sha256'],'access':'private','countries':[],
            'meeting_id':mid,'inventory_metadata_sha256':row['inventory_metadata_sha256'],
            'normalized_artifact_sha256':r['normalized_sha256'],'extraction_method_version':r['extraction_method_version'],
            'artifact_revision':_digest(r),'verification_scope':VERIFICATION_SCOPE,'source_role':'product_development'}
    parent_revision=_digest(parent)
    source={'id':source_id,'published_date':date,'body':body,'family':'un_statement','url':r['source_url'],
            'content_hash':row['text_sha256'],'access':'private','countries':[speaker['country']] if capacity=='national' else [],
            'meeting_id':mid,'parent_source_id':parent_id,'parent_source_revision':parent_revision,
            'native_statement_id':native,'identity_scheme_version':IDENTITY_SCHEME,'language':language,
            'artifact_identity_scope':'native_statement_key_local_to_stable_artifact_url',
            'artifact_sha256':r['source_sha256'],'artifact_revision':_digest(r),'normalized_artifact_sha256':r['normalized_sha256'],
            'text_sha256':row['text_sha256'],'speaker':dict(speaker),'parent_meeting':dict(m),
            'inventory_metadata_sha256':row['inventory_metadata_sha256'],'adapter_version':VERSION,
            'country_registry_sha256':country_registry[2],
            'verification_scope':VERIFICATION_SCOPE,'source_role':'product_development','comparisons_eligible':False}
    return {'schema':'un.statement-identity.v1','version':VERSION,'source_id':source_id,'source_revision':_digest(source),
            'parent_source_id':parent_id,'parent_source_revision':parent_revision,'source':source,'parent_source':parent,
            'verification_scope':VERIFICATION_SCOPE,'private_only':True,'production_intake_accepted':False}


def persist_statement(store,row):
    """Atomic private metadata sources and provenance only; creates no opinions."""
    normalized=normalize_statement(row)
    with store.transaction():
        # Hash identities provide no chronology for never-seen artifacts. They
        # can nevertheless reject a known historical revision becoming current
        # again without an explicit replay-review workflow.
        for sid,revision in ((normalized['parent_source_id'],normalized['parent_source_revision']),
                             (normalized['source_id'],normalized['source_revision'])):
            current=store.db.execute('SELECT revision FROM sources WHERE id=?',(sid,)).fetchone()
            historical=store.db.execute('SELECT 1 FROM source_revisions WHERE id=? AND revision=?',(sid,revision)).fetchone()
            if current and current[0]!=revision and historical: raise ValueError('Known historical statement or parent revision requires explicit replay review')
        parent_revision=store.upsert_source(normalized['parent_source'])
        revision=store.upsert_source(normalized['source'])
        if revision!=normalized['source_revision'] or parent_revision!=normalized['parent_source_revision']: raise ValueError('Canonical store revision contract mismatch')
        provenance={'schema':'un.statement-provenance.v1','version':VERSION,
                    'source_id':normalized['source_id'],'source_revision':revision,
                    'parent_source_id':normalized['parent_source_id'],'parent_source_revision':parent_revision,
                    'meeting_id':normalized['source']['meeting_id'],'native_statement_id':row['native_statement_id'],
                    'identity_scheme_version':IDENTITY_SCHEME,'language':row['language'],
                    'artifact_sha256':row['artifact_receipt']['source_sha256'],'normalized_artifact_sha256':row['artifact_receipt']['normalized_sha256'],
                    'text_sha256':row['text_sha256'],'publication':'private_only','comparisons_eligible':False,
                    'verification_scope':VERIFICATION_SCOPE,'production_intake_accepted':False}
        artifact_id=store.put_artifact('statement_provenance',provenance,[normalized['source_id'],normalized['parent_source_id']])
        if not store.artifact_valid(artifact_id): raise ValueError('Previously invalidated statement provenance cannot be replayed as current')
    return {'schema':'un.statement-persistence.v1','version':VERSION,'source_id':normalized['source_id'],'source_revision':revision,
            'parent_source_id':normalized['parent_source_id'],'parent_source_revision':parent_revision,'provenance_artifact_id':artifact_id,
            'verification_scope':VERIFICATION_SCOPE,'private_only':True,'production_intake_accepted':False,'observations_created':0}
