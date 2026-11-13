"""Synthetic private training transfer; plaintext must never become a public artifact."""
import hashlib
import io
import json
import unittest
import zipfile
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from tools.export_owner_training import (encrypt_bundle,decrypt_bundle,public_key,training_zip,
    registration_option,PILOT_PREFIX,PILOT_REVISION,REVIEWER_PREFIX,REVIEWER_REVISION)
from tools.build_private_reviewer import render
from un_transcript.models.contracts import digest


class OwnerTransfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key=rsa.generate_private_key(public_exponent=65537,key_size=4096)
        cls.private=cls.key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
        cls.public=cls.key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo)

    def test_authenticated_roundtrip_and_tampering(self):
        source=b'SYNTHETIC PRIVATE TRAINING DATA'
        encrypted=encrypt_bundle(source,self.public)
        self.assertNotIn(source,encrypted)
        self.assertEqual(decrypt_bundle(encrypted,self.private),source)
        corrupt=encrypted[:-1]+bytes([encrypted[-1]^1])
        with self.assertRaises(InvalidTag):decrypt_bundle(corrupt,self.private)

    def test_wrong_recipient_and_private_key_input_are_rejected(self):
        key=rsa.generate_private_key(public_exponent=65537,key_size=4096)
        private=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
        with self.assertRaisesRegex(ValueError,'Wrong recipient'):
            decrypt_bundle(encrypt_bundle(b'synthetic',self.public),private)
        with self.assertRaises(ValueError):public_key(self.private)
        with self.assertRaises(ValueError):public_key(b'not a key')

    def fixture(self, change_registration=None, wrong_binding=False):
        registration={'schema':'un.stance-registration.v1','registered_at':'2026-11-04T00:00:00Z',
            'required_bodies':['synthetic'],'catalog_sha256':'a'*64,'policy_sha256':'b'*64,
            'attribution_method_version':'synthetic-v1','attribution_registry_sha256':'c'*64,
            'propositions':{'synthetic':'Adopt a fictional policy.'},'sampling':'Synthetic fixture',
            'sources':[{'source_id':f'source-{i}','source_hash':str(i)*64,'meeting_id':f'meeting-{i}',
                        'date':f'2026-11-0{i}','split':split,'segment_id':f'segment-{i}','text_sha256':'d'*64}
                       for i,split in enumerate(('train','calibration','test'),1)]}
        if change_registration:change_registration(registration)
        draft={'registration_sha256':'0'*64 if wrong_binding else digest(registration),
            'rows':[{'pair_id':str(i),'split':'train','owner_confirmed':False,'text':'Synthetic private passage'} for i in range(180)]}
        data={PILOT_PREFIX+'train-draft.json':json.dumps(draft).encode(),PILOT_PREFIX+'review/train-review.csv':b'pair_id,speaker,source_url\n',
              PILOT_PREFIX+'registration.json':json.dumps(registration).encode()}
        sha=lambda raw:hashlib.sha256(raw).hexdigest()
        manifest={'files':[{'path':path,'bytes':len(raw),'sha256':sha(raw)} for path,raw in data.items()]+[
            {'path':PILOT_PREFIX+'sealed/test-draft.json','bytes':10,'sha256':'0'*64}]}
        raw=json.dumps(manifest).encode();data[PILOT_PREFIX+'packet-manifest.json']=raw
        identity={'dataset_revision':PILOT_REVISION,'packet_prefix':PILOT_PREFIX,'manifest_sha256':sha(raw),'split':'train'}
        html=render(draft,{},identity).encode();data[REVIEWER_PREFIX+'training-review.html']=html
        data[REVIEWER_PREFIX+'manifest.json']=json.dumps({**identity,'schema':'un.private-reviewer.v1','examples':180,'html_sha256':sha(html)}).encode()
        class Storage:
            calls=[]
            def info(self):pass
            def read(self,path,revision,maximum):
                self.calls.append(path)
                assert revision==(REVIEWER_REVISION if path.startswith(REVIEWER_PREFIX) else PILOT_REVISION)
                assert len(data[path])<=maximum
                return data[path]
        return Storage(),data

    def test_exact_training_allowlist_and_hash_bound_html(self):
        storage,_=self.fixture()
        bundle=training_zip(storage)
        with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
            self.assertEqual(len(archive.namelist()),6)
            self.assertIn('01_training/training-review.html',archive.namelist())
            self.assertTrue(all('sealed/' not in name and 'calibration' not in name for name in archive.namelist()))
        self.assertFalse(any('sealed/' in path or 'calibration' in path for path in storage.calls))
        self.assertNotIn(PILOT_PREFIX+'registration.json',storage.calls)

    def test_opt_in_registration_is_hash_bound_metadata_only(self):
        storage,data=self.fixture()
        with zipfile.ZipFile(io.BytesIO(training_zip(storage,True))) as archive:
            self.assertEqual(len(archive.namelist()),7)
            path='01_training/provenance/registration.json'
            self.assertEqual(archive.read(path),data[PILOT_PREFIX+'registration.json'])
            receipt=json.loads(archive.read('01_training/provenance/download-manifest.json'))
            for entry in receipt['files']:
                self.assertEqual(entry['sha256'],hashlib.sha256(archive.read(entry['path'])).hexdigest())
                self.assertEqual(entry['bytes'],len(archive.read(entry['path'])))
        self.assertEqual(storage.calls.count(PILOT_PREFIX+'registration.json'),1)
        self.assertFalse(any('sealed/' in path or 'calibration' in path for path in storage.calls))

    def test_registration_rejects_text_labels_and_nested_payloads(self):
        changes=[lambda r:r.update(text='private passage'),
                 lambda r:r.update(notes='private annotation'),
                 lambda r:r['sources'][0].update(text='private passage'),
                 lambda r:r['sources'][1].update(label='support'),
                 lambda r:r['propositions'].update(synthetic={'text':'nested passage'}),
                 lambda r:r['sources'][0].update(text_sha256='invalid')]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                storage,_=self.fixture(change)
                with self.assertRaises(ValueError):training_zip(storage,True)

    def test_registration_prospective_boundaries_remain_enforced(self):
        changes=[lambda r:r['sources'][1].update(meeting_id='meeting-1'),
                 lambda r:r['sources'][2].update(date='2026-10-06'),
                 lambda r:r['sources'][2].update(date='2026-11-01'),
                 lambda r:r['sources'].pop()]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                storage,_=self.fixture(change)
                with self.assertRaises(ValueError):training_zip(storage,True)

    def test_registration_checksum_and_original_draft_binding(self):
        storage,data=self.fixture()
        path=PILOT_PREFIX+'registration.json'
        data[path]=data[path].replace(b'synthetic-v1',b'synthetic-v2')
        with self.assertRaisesRegex(ValueError,'checksum'):training_zip(storage,True)
        storage,_=self.fixture(wrong_binding=True)
        with self.assertRaisesRegex(ValueError,'draft registration mismatch'):training_zip(storage,True)

    def test_registration_is_explicit_opt_in_before_any_read(self):
        self.assertTrue(registration_option('true'))
        self.assertFalse(registration_option('false'))
        for value in ('', 'True', '1', True, 1, None):
            with self.assertRaises(ValueError):registration_option(value)
        storage,_=self.fixture()
        for value in ('false',1,None):
            with self.assertRaises(ValueError):training_zip(storage,value)
        self.assertEqual(storage.calls,[])

    def test_reviewer_tampering_fails_before_encrypted_output(self):
        storage,data=self.fixture()
        data[REVIEWER_PREFIX+'training-review.html']+=b'changed'
        with self.assertRaisesRegex(ValueError,'checksum'):training_zip(storage)
