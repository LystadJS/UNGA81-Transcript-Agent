"""Invented judgments only; exercise private transport and publication failures."""
import base64
import copy
from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zlib

from test_review_intake import packet
from tools import receive_owner_review as R
from un_transcript.snapshots import RemoteEntryMissing, encode

NOW = datetime(2026, 11, 13, tzinfo=timezone.utc)


class Storage:
    private = True
    budget_bytes = 80_000_000_000
    def __init__(self):
        self.head = '0'*40
        self.versions = {self.head:{'latest.json':b'warehouse pointer must not change'}}
        self.commits = []; self.reads = []; self.used = 0; self.fail_verify = False
        self.fail_activate = False; self.lost_activate_response = False
    def info(self):
        return SimpleNamespace(sha=self.head, private=self.private), self.used
    def budget_info(self):
        return self.info()
    def read(self, path, revision, limit):
        self.reads.append(path)
        if path not in self.versions[revision]:
            raise RemoteEntryMissing(path)
        raw = self.versions[revision][path]
        if len(raw) > limit:
            raise ValueError('Fixture size bound')
        return raw
    def _immutable_prefix(self, prefix, revision):
        if any(p.startswith(prefix) for p in self.versions[revision]):
            raise FileExistsError('Immutable prefix')
    def _commit(self, files, parent, message):
        if parent != self.head:
            raise ValueError('Concurrent writer')
        if self.fail_activate and R.LATEST in files:
            raise RuntimeError('Injected activation failure')
        self.head = f'{len(self.versions):040x}'
        self.versions[self.head] = {**self.versions[parent], **files}
        self.commits.append(copy.deepcopy(files))
        if self.lost_activate_response and R.LATEST in files:
            raise RuntimeError('Injected accepted activation response loss')
        return self.head
    def _verify_remote(self, files, revision):
        if self.fail_verify:
            raise ValueError('Injected remote verification failure')
        for path, raw in files.items():
            if self.read(path, revision, len(raw)) != raw:
                raise ValueError('Remote mismatch')


class EncryptedIntake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared_storage = Storage()
        cls.recipient = R.prepare_recipient(cls.prepared_storage, NOW)

    def setUp(self):
        self.storage = copy.deepcopy(self.prepared_storage)
        self.recipient = copy.deepcopy(type(self).recipient)
        self.draft, self.registration, self.returned, self.identity = packet()
        self.originals = (self.draft, self.registration, self.identity)
        self.reader = patch.object(R, 'original_inputs', return_value=self.originals)
        self.reader.start(); self.addCleanup(self.reader.stop)

    def send(self, returned=None):
        raw = json.dumps(returned or self.returned, indent=2).encode()+b'\n'
        dispatches = R.make_dispatches(raw, self.recipient, NOW)
        for d in dispatches[:-1]:
            i = d['inputs']
            R.receive_part(self.storage, i['key_id'], i['key_revision'], i['cipher_sha256'],
                           int(i['part_count']), int(i['part_number']), i['ciphertext_part'], NOW)
        i = dispatches[-1]['inputs']
        args = (i['key_id'], i['key_revision'], i['cipher_sha256'], int(i['part_count']))
        return raw, args, dispatches

    def finish(self, args, run='10-1'):
        return R.finalize(self.storage, *args, run, 'a'*40, NOW)

    def test_exact_bytes_private_keys_and_public_receipt_boundary(self):
        raw, args, dispatches = self.send()
        receipt = self.finish(args)
        pointer = json.loads(self.storage.versions[self.storage.head][R.LATEST])
        stored = self.storage.versions[pointer['revision']]
        self.assertEqual(stored[pointer['prefix']+'owner-return.json'], raw)
        self.assertEqual(json.loads(stored[pointer['prefix']+'validated-training.json'])['rows'],
                         self.returned['rows'])
        self.assertFalse(receipt['model_accepted']); self.assertFalse(receipt['training_started'])
        self.assertEqual(receipt['confirmed_examples'], 1)
        self.assertEqual(set(receipt), {'schema','status','key_id','private_revision','confirmed_examples',
                         'total_examples','clarification_count','original_bytes_preserved','remote_files_verified','training_started','model_accepted'})
        exposed = encode([receipt, self.recipient, dispatches])
        for secret in (b'PRIVATE KEY', b'Fictional source statement', b'synthetic-owner'):
            self.assertNotIn(secret, exposed)
        self.assertEqual(self.storage.versions[self.storage.head]['latest.json'], b'warehouse pointer must not change')
        self.assertFalse(any('sealed/' in p or 'calibration' in p or p.startswith('raw/') for p in self.storage.reads))

    def test_replay_is_verified_without_new_commit(self):
        _, args, _ = self.send(); first = self.finish(args); count = len(self.storage.commits)
        again = self.finish(args, '11-1')
        self.assertEqual(len(self.storage.commits), count)
        self.assertEqual(again['private_revision'], first['private_revision'])
        self.assertEqual(again['status'], 'verified_duplicate_intake')

    def test_duplicate_and_conflicting_parts(self):
        _, _, dispatches = self.send(); i = dispatches[0]['inputs']; count = len(self.storage.commits)
        args = (i['key_id'],i['key_revision'],i['cipher_sha256'],int(i['part_count']),1)
        R.receive_part(self.storage,*args,i['ciphertext_part'],NOW)
        self.assertEqual(len(self.storage.commits),count)
        wrong = ('A' if i['ciphertext_part'][0] != 'A' else 'B')+i['ciphertext_part'][1:]
        with self.assertRaisesRegex(ValueError,'conflict'):
            R.receive_part(self.storage,*args,wrong,NOW)

    def test_tampering_and_missing_parts_never_activate(self):
        _, args, _ = self.send()
        path = 'owner-intake/transfers/'+args[0]+'/'+args[2]+'/1.b64'
        old = self.storage.versions[self.storage.head][path]
        self.storage.versions[self.storage.head][path] = b'A'+old[1:]
        with self.assertRaises(ValueError):self.finish(args)
        self.assertNotIn(R.LATEST,self.storage.versions[self.storage.head])
        del self.storage.versions[self.storage.head][path]
        with self.assertRaises(RemoteEntryMissing):self.finish(args)

    def test_invalid_review_preserves_previous_pointer(self):
        _, args, _ = self.send(); self.finish(args); old = self.storage.versions[self.storage.head][R.LATEST]
        self.recipient = R.prepare_recipient(self.storage,NOW)
        changed = copy.deepcopy(self.returned); changed['rows'][0]['label'] = 'oppose'
        _, args, _ = self.send(changed)
        with self.assertRaisesRegex(ValueError,'Conflicting'):self.finish(args,'12-1')
        self.assertEqual(self.storage.versions[self.storage.head][R.LATEST],old)

    def test_later_partial_review_accumulates_without_relabeling(self):
        _, args, _ = self.send(); self.finish(args)
        self.recipient = R.prepare_recipient(self.storage,NOW)
        later = copy.deepcopy(self.returned)
        later['rows'][0] = {**later['rows'][0], 'pair_id':self.draft['rows'][1]['pair_id']}
        _, args, _ = self.send(later)
        self.assertEqual(self.finish(args,'12-1')['confirmed_examples'],2)

    def test_crash_verification_and_activation_failure_preserve_previous_archive(self):
        for mode in ('verify','activate','lost_response'):
            with self.subTest(mode=mode):
                self.storage = copy.deepcopy(self.prepared_storage)
                _, args, _ = self.send()
                if mode == 'verify':self.storage.fail_verify = True
                if mode == 'activate':self.storage.fail_activate = True
                if mode == 'lost_response':self.storage.lost_activate_response = True
                with self.assertRaises((ValueError,RuntimeError)):self.finish(args)
                if mode != 'lost_response':
                    self.assertNotIn(R.LATEST,self.storage.versions[self.storage.head])
                self.assertEqual(self.storage.versions[self.storage.head]['latest.json'],b'warehouse pointer must not change')
                self.storage.fail_verify = self.storage.fail_activate = self.storage.lost_activate_response = False
                receipt = self.finish(args,'13-1')
                self.assertTrue(receipt['remote_files_verified'])
                self.assertEqual(receipt['status'],'verified_duplicate_intake' if mode=='lost_response' else 'verified_private_owner_intake')

    def test_budget_visibility_expiry_and_bad_identifiers_fail_closed(self):
        self.storage.private = False
        with self.assertRaises(ValueError):R.prepare_recipient(self.storage,NOW)
        self.storage.private = True; self.storage.budget_bytes = 1
        with self.assertRaisesRegex(ValueError,'budget'):R.prepare_recipient(self.storage,NOW)
        self.storage.budget_bytes = 80_000_000_000
        with self.assertRaisesRegex(ValueError,'expired'):
            R.make_dispatches(encode(self.returned),self.recipient,NOW+timedelta(days=2))
        with self.assertRaises(ValueError):
            R.receive_part(self.storage,'../private','a'*40,'b'*64,1,1,'AAAA',NOW)
        for count in (True,0,9):
            with self.assertRaises(ValueError):R.transfer_identity('a'*32,'b'*40,'c'*64,count)

    def test_decompression_bombs_duplicate_json_and_nonfinite_values_rejected(self):
        for raw in (b'A'*(R.MAX_RETURN+1), b'', b'two streams'):
            compressed = zlib.compress(raw)
            if raw == b'two streams':compressed += zlib.compress(raw)
            with self.assertRaises(ValueError):R.expand_return(compressed)
        for raw in (b'{"label":1,"label":2}',b'{"label":NaN}',b'{"label":Infinity}'):
            with self.assertRaises(ValueError):R.make_dispatches(raw,self.recipient,NOW)

    def test_multipart_reassembly_and_size_bounds(self):
        import random
        random_bytes = random.Random(87).randbytes(100000)
        value = {'synthetic':base64.b64encode(random_bytes).decode()}
        dispatches = R.make_dispatches(encode(value),self.recipient,NOW)
        self.assertGreater(len(dispatches),2)
        self.assertLessEqual(len(dispatches),R.MAX_PARTS+1)
        self.assertTrue(all(len(encode(d))<65535 for d in dispatches))
        for d in dispatches[:-1]:
            i=d['inputs']
            R.receive_part(self.storage,i['key_id'],i['key_revision'],i['cipher_sha256'],
                           int(i['part_count']),int(i['part_number']),i['ciphertext_part'],NOW)
        i=dispatches[-1]['inputs']
        with self.assertRaisesRegex(ValueError,'label schema'):
            self.finish((i['key_id'],i['key_revision'],i['cipher_sha256'],int(i['part_count'])))
        self.assertNotIn(R.LATEST,self.storage.versions[self.storage.head])

    def test_lookup_errors_are_not_missing_and_stored_files_are_reverified(self):
        with patch.object(self.storage,'read',side_effect=RuntimeError('outage')):
            with self.assertRaises(RuntimeError):R.optional(self.storage,R.LATEST,self.storage.head)
        _,args,_=self.send();self.finish(args)
        pointer=json.loads(self.storage.versions[self.storage.head][R.LATEST])
        self.storage.versions[pointer['revision']][pointer['prefix']+'owner-return.json']=b'corrupt'
        with self.assertRaises(ValueError):self.finish(args,'14-1')

    def test_final_budget_and_concurrent_writer_block_activation(self):
        _,args,_=self.send()
        before=len(self.storage.commits)
        self.storage.budget_bytes=1
        with self.assertRaisesRegex(ValueError,'budget'):self.finish(args)
        self.assertEqual(len(self.storage.commits),before)
        self.storage.budget_bytes=80_000_000_000
        with patch.object(self.storage,'budget_info',return_value=(SimpleNamespace(sha='f'*40),0)):
            with self.assertRaisesRegex(ValueError,'changed'):self.finish(args)
        self.assertNotIn(R.LATEST,self.storage.versions[self.storage.head])
        self.assertEqual(len(self.storage.commits),before)

    def test_consumed_recipient_cannot_accept_different_ciphertext(self):
        _,args,_=self.send();self.finish(args)
        before=len(self.storage.commits)
        with self.assertRaisesRegex(ValueError,'reused'):
            self.finish((args[0],args[1],'f'*64,args[3]))
        i=R.make_dispatches(encode(self.returned),self.recipient,NOW)[0]['inputs']
        with self.assertRaisesRegex(ValueError,'consumed'):
            R.receive_part(self.storage,i['key_id'],i['key_revision'],i['cipher_sha256'],
                           int(i['part_count']),int(i['part_number']),i['ciphertext_part'],NOW)
        self.assertEqual(len(self.storage.commits),before)

    def test_collective_flag_is_provisional_and_preserves_owner_choices(self):
        for row in self.draft['rows']:
            row['capacity']='collective'
        self.returned['rows'][0].update(capacity='collective',national_attribution_valid=True)
        raw,args,_=self.send()
        receipt=self.finish(args)
        self.assertEqual(receipt['clarification_count'],1)
        pointer=json.loads(self.storage.versions[self.storage.head][R.LATEST])
        stored=self.storage.versions[pointer['revision']]
        self.assertEqual(stored[pointer['prefix']+'owner-return.json'],raw)
        choices=json.loads(stored[pointer['prefix']+'validated-training.json'])
        self.assertIs(choices['rows'][0]['national_attribution_valid'],True)
        flags=json.loads(stored[pointer['prefix']+'clarifications.json'])
        self.assertEqual(flags['role'],'assistant_provisional_qa')
        self.assertFalse(flags['owner_choices_changed'])
