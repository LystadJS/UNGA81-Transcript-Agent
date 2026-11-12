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
    PILOT_PREFIX,PILOT_REVISION,REVIEWER_PREFIX,REVIEWER_REVISION)
from tools.build_private_reviewer import render


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

    def fixture(self):
        draft={'rows':[{'pair_id':str(i),'split':'train','owner_confirmed':False,'text':'Synthetic private passage'} for i in range(180)]}
        data={PILOT_PREFIX+'train-draft.json':json.dumps(draft).encode(),PILOT_PREFIX+'review/train-review.csv':b'pair_id,speaker,source_url\n'}
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

    def test_reviewer_tampering_fails_before_encrypted_output(self):
        storage,data=self.fixture()
        data[REVIEWER_PREFIX+'training-review.html']+=b'changed'
        with self.assertRaisesRegex(ValueError,'checksum'):training_zip(storage)
