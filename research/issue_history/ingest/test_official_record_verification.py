"""Invented metadata only; no source bodies, network or private database reads."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from . import official_record_verification as V
from .test_historical_register_bridge import fixture as bridge_fixture


def fixture():
    kw = bridge_fixture()
    source = kw['register_kwargs']['entries'][0]
    primary = {'symbol': 'A/81/PV.9999', 'body': 'GA', 'meeting_date': source['date'],
               'official_url': 'https://docs.un.org/en/A/81/PV.9999'}
    metadata = {'url': 'https://digitallibrary.un.org/record/99999999',
                'retrieved_on': '2026-10-24', 'content_sha256': 'b'*64,
                'hash_scope': 'retrieved_primary_metadata_bytes', 'retrieval_mode': 'direct_primary'}
    crosswalk = {'source_native_id': source['native_id'], 'source_url': source['source_url'],
                 'official_symbol': primary['symbol'], 'explicit_link': True,
                 'metadata': {**metadata, 'url': 'https://transcripts.un.org/en/catalog', 'content_sha256': 'c'*64}}
    receipts = [{'source_id': source['source_id'], 'primary_record': primary,
                 'primary_metadata': metadata, 'crosswalk': crosswalk, 'permissions': []}]
    return {'bridge_kwargs': kw, 'evidence_receipts': receipts,
            'expected_evidence_sha256': V._digest(receipts)}


def repin(kw):
    kw['expected_evidence_sha256'] = V._digest(kw['evidence_receipts'])


class OfficialRecordVerificationTests(unittest.TestCase):
    def setUp(self):
        self.kw = fixture()
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('SC_ACTION_TEST_ROOT'))
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'verification.json'

    def build(self):
        return V.build_verification(**self.kw)

    def test_explicit_metadata_link_never_authenticates_or_grants(self):
        before = copy.deepcopy(self.kw)
        out = self.build(); row = out['entries'][0]
        self.assertEqual('consistent_supplied_metadata_link', row['identity_status'])
        self.assertEqual(before, self.kw)
        self.assertFalse(row['production_intake_accepted'])
        self.assertTrue(all(not p['approved'] for p in row['permissions'].values()))
        self.assertEqual(out, self.build())

    def test_missing_and_unlinked_evidence_remains_visible(self):
        self.kw['evidence_receipts'] = []; repin(self.kw)
        self.assertEqual('unverified_no_primary_metadata', self.build()['entries'][0]['identity_status'])
        self.kw = fixture(); self.kw['evidence_receipts'][0]['crosswalk'] = None; repin(self.kw)
        self.assertEqual('unlinked_primary_metadata', self.build()['entries'][0]['identity_status'])

    def test_body_date_native_and_crosswalk_conflicts(self):
        for field in ('date', 'body', 'native', 'crosswalk'):
            self.kw = fixture(); receipt = self.kw['evidence_receipts'][0]
            if field == 'date': receipt['primary_record']['meeting_date'] = '2026-10-02'
            elif field == 'body': receipt['primary_record'].update(symbol='S/PV.9999', body='SC', official_url='https://docs.un.org/en/S/PV.9999'); receipt['crosswalk']['official_symbol']='S/PV.9999'
            elif field == 'native':
                source=self.kw['bridge_kwargs']['register_kwargs']['entries'][0]; source['native_id']='A/81/PV.8'; source['source_kind']='official_un_meeting_record'
            else: receipt['crosswalk']['source_native_id']='ga/81/8'
            repin(self.kw)
            with self.subTest(field=field): self.assertEqual('conflicting_metadata', self.build()['entries'][0]['identity_status'])

    def test_symbol_body_url_and_metadata_validation(self):
        for field, value in [('symbol','A/81/PV.0'), ('body','SC'), ('official_url','https://docs.un.org.evil/en/A/81/PV.9999'), ('official_url','https://docs.un.org/en/A/81/PV.8'), ('official_url','https://documents.un.org/doc?s=A%2F81%2FPV.9999&symbol=A%2F81%2FPV.9999')]:
            self.kw=fixture();self.kw['evidence_receipts'][0]['primary_record'][field]=value;repin(self.kw)
            with self.subTest(field=field,value=value), self.assertRaises(ValueError):self.build()

    def test_explicit_mapping_independent_artifact_and_dates_required(self):
        for field in ('explicit', 'samehash', 'future', 'badsha'):
            self.kw=fixture();receipt=self.kw['evidence_receipts'][0]
            if field=='explicit':receipt['crosswalk']['explicit_link']=False
            elif field=='samehash':receipt['crosswalk']['metadata']['content_sha256']='b'*64
            elif field=='future':receipt['primary_metadata']['retrieved_on']='2026-10-25'
            else:receipt['primary_metadata']['content_sha256']='bad'
            repin(self.kw)
            with self.subTest(field=field),self.assertRaises(ValueError):self.build()

    def test_conditional_rights_and_endpoint_approval_do_not_clear_permissions(self):
        receipt=self.kw['evidence_receipts'][0]
        receipt['permissions']=[{'scope':'private_analysis','status':'conditional','evidence':copy.deepcopy(receipt['primary_metadata'])}, {'scope':'automated_retrieval','status':'approval_required','evidence':copy.deepcopy(receipt['primary_metadata'])}]
        repin(self.kw);permissions=self.build()['entries'][0]['permissions']
        self.assertEqual('approval_required',permissions['automated_retrieval']['status'])
        self.assertTrue(all(not p['approved'] for p in permissions.values()))
        self.assertEqual('unknown',permissions['public_redistribution']['status'])

    def test_permission_grants_duplicates_unbacked_claims_rejected(self):
        for mode in ('grant','duplicate','unbacked'):
            self.kw=fixture();r=self.kw['evidence_receipts'][0]
            p={'scope':'private_analysis','status':'unknown','evidence':None}
            r['permissions']=[p]
            if mode=='grant':p['status']='confirmed_allow'
            elif mode=='duplicate':r['permissions'].append(copy.deepcopy(p))
            else:p['status']='conditional'
            repin(self.kw)
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.build()

    def test_restricted_and_reserved_sources_cannot_gain_authorization(self):
        for role in ('evaluation','source_quality_audit','restricted_research'):
            self.kw=fixture();self.kw['bridge_kwargs']['register_kwargs']['entries'][0]['declared_role']=role
            row=self.build()['entries'][0]
            with self.subTest(role=role):self.assertTrue(row['role_blocked']);self.assertFalse(row['production_intake_accepted'])

    def test_frame_holdout_and_exact_historical_audit_restrictions_survive(self):
        self.kw=fixture()
        frame=self.kw['bridge_kwargs']['register_kwargs']['frame']
        frame['meetings'][0]['split']='holdout'
        frame['sha256']=V._digest({k:v for k,v in frame.items() if k!='sha256'})
        self.kw['bridge_kwargs']['register_kwargs']['expected_frame_sha256']=frame['sha256']
        row=self.build()['entries'][0]
        self.assertTrue(row['role_blocked']);self.assertEqual('evaluation',row['effective_role'])
        self.assertFalse(row['metadata_candidate_only'])
        self.kw=fixture()
        source=self.kw['bridge_kwargs']['register_kwargs']['entries'][0]
        source.update(native_id='A/71/PV.88',source_kind='official_un_meeting_record',
                      source_url='https://docs.un.org/en/A/71/PV.88')
        r=self.kw['evidence_receipts'][0]
        r['primary_record'].update(symbol='A/71/PV.88',official_url=source['source_url'])
        r['crosswalk'].update(source_native_id=source['native_id'],source_url=source['source_url'],official_symbol='A/71/PV.88')
        repin(self.kw);row=self.build()['entries'][0]
        self.assertEqual('consistent_supplied_metadata_link',row['identity_status'])
        self.assertEqual('source_quality_audit',row['effective_role'])
        self.assertTrue(row['role_blocked']);self.assertFalse(row['metadata_candidate_only'])
        self.assertFalse(row['production_intake_accepted'])

    def test_family_never_converted_to_statement(self):
        source=self.kw['bridge_kwargs']['register_kwargs']['entries'][0]
        source.update(family='vote',source_kind='official_un_vote')
        self.assertIn('source_family',self.build()['entries'][0]['metadata_conflicts'])

    def test_unknown_duplicate_and_extra_receipt_fields_rejected(self):
        for mode in ('unknown','duplicate','extra'):
            self.kw=fixture();r=self.kw['evidence_receipts'][0]
            if mode=='unknown':r['source_id']='reserved:not-registered'
            elif mode=='duplicate':self.kw['evidence_receipts'].append(copy.deepcopy(r))
            else:r['source_text']='forbidden'
            repin(self.kw)
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.build()

    def test_external_evidence_pin_required(self):
        self.kw['evidence_receipts'][0]['crosswalk']=None
        with self.assertRaises(ValueError):self.build()

    def test_save_reopen_idempotent_and_canonical(self):
        out=self.build();V.save_verification(self.path,out,**self.kw);raw=self.path.read_bytes()
        self.assertEqual(out,V.load_verification(self.path,**self.kw))
        V.save_verification(self.path,out,**self.kw);self.assertEqual(raw,self.path.read_bytes())

    def test_tamper_resealed_and_changed_inputs_rejected_without_overwrite(self):
        out=self.build();V.save_verification(self.path,out,**self.kw);raw=self.path.read_bytes()
        tamper=copy.deepcopy(out);tamper['entries'][0]['production_intake_accepted']=True
        tamper['content_sha256']=V._digest({k:v for k,v in tamper.items() if k!='content_sha256'})
        with self.assertRaises(ValueError):V.save_verification(self.path,tamper,**self.kw)
        self.assertEqual(raw,self.path.read_bytes())
        self.kw['evidence_receipts'][0]['crosswalk']=None;repin(self.kw)
        with self.assertRaises(ValueError):V.load_verification(self.path,**self.kw)

    def test_wrong_window_method_and_corrupt_noncanonical_rejected(self):
        out=self.build();V.save_verification(self.path,out,**self.kw)
        methods=V._methods();methods['official_record_verification.py']='f'*64
        with patch.object(V,'_methods',return_value=methods),self.assertRaises(ValueError):V.load_verification(self.path,**self.kw)
        self.path.write_bytes(b'{broken')
        with self.assertRaises(ValueError):V.load_verification(self.path,**self.kw)

    def test_path_query_conflicts_and_review_note_identity_rejected(self):
        for mode in ('path', 'review_note', 'search_index'):
            self.kw=fixture();r=self.kw['evidence_receipts'][0]
            if mode=='path':r['primary_record']['official_url']='https://docs.un.org/en/S/PV.9?s=A%2F81%2FPV.9999'
            elif mode=='review_note':r['primary_metadata'].update(hash_scope='review_note',retrieval_mode='review_note')
            else:r['primary_metadata']['retrieval_mode']='search_index'
            repin(self.kw)
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.build()

    def test_case_variants_cannot_hide_document_conflicts(self):
        for url in ('https://docs.un.org/en/a/80/pv.1?s=A%2F81%2FPV.9999',
                    'https://docs.un.org/en/A/81/PV.9999?SYMBOL=S%2FPV.8',
                    'https://docs.un.org/en/A/81/PV.9999?S=A%2F81%2FPV.9999'):
            self.kw=fixture();self.kw['evidence_receipts'][0]['primary_record']['official_url']=url;repin(self.kw)
            with self.subTest(url=url),self.assertRaises(ValueError):self.build()

    def test_separate_windows_invalidate_snapshot_and_preserve_bytes(self):
        V.save_verification(self.path,self.build(),**self.kw);raw=self.path.read_bytes()
        self.kw['bridge_kwargs']['register_kwargs']['as_of']='2026-10-23'
        self.kw['bridge_kwargs']['exclusion_kwargs']['as_of']='2026-10-23'
        with self.assertRaises(ValueError):V.load_verification(self.path,**self.kw)
        self.assertEqual(raw,self.path.read_bytes())

    def test_incomplete_primary_and_crosswalk_combinations_rejected(self):
        for key in ('primary_record','primary_metadata'):
            self.kw=fixture();self.kw['evidence_receipts'][0][key]=None;repin(self.kw)
            with self.subTest(key=key),self.assertRaises(ValueError):self.build()

    def test_sc_and_committee_symbols_are_separate_strict_records(self):
        for symbol,body in [('S/PV.9999','SC'),('A/C.3/81/SR.99','GA_C3')]:
            self.kw=fixture();r=self.kw['evidence_receipts'][0]
            r['primary_record'].update(symbol=symbol,body=body,official_url='https://docs.un.org/en/'+symbol)
            r['crosswalk']['official_symbol']=symbol
            self.kw['bridge_kwargs']['register_kwargs']['entries'][0]['body']=body
            repin(self.kw)
            with self.subTest(symbol=symbol):self.assertEqual('consistent_supplied_metadata_link',self.build()['entries'][0]['identity_status'])


if __name__=='__main__':unittest.main()
