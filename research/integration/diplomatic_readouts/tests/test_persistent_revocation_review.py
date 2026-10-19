"""Synthetic-only independent revocation persistence and dual-signer compromise tests."""
from __future__ import annotations

from dataclasses import replace
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from persistent_revocation_review import (
    ExternalObserverPin, SyntheticRestartWithheld, assert_no_authority,
    guarded_restart_verify, make_verified_state, proposed_pin_from_state,
    read_checked_state, state_digest, write_state_rehearsal,
)
from test_synthetic_signatures import fixture, resign_custody, resign_revocation
from test_registry_preflight import WHEN


class RestartCompromiseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'checkpoint.synthetic.json'
        self.original = fixture()
        self.original_state = self._candidate(self.original)
        self.pin1 = write_state_rehearsal(self.path, self.original_state)

    def _candidate(self, f, previous=None):
        return make_verified_state(
            f['snapshot'], f['policy'], f['events'], f['proposal'],
            f['custody'], f['revocation'], checked_at=WHEN,
            trust=f['trust'], previous=previous,
        )

    def _evaluate(self, f=None, pin=None, when=WHEN):
        f = self.original if f is None else f
        pin = self.pin1 if pin is None else pin
        r = guarded_restart_verify(
            self.path, pin, f['snapshot'], f['policy'], f['events'],
            f['proposal'], f['custody'], f['revocation'],
            checked_at=when, trust=f['trust'],
        )
        assert_no_authority(r)
        return r

    def _advanced(self):
        f = fixture()
        # Existing old custody signing key was revoked in a later checkpoint.
        f['custody']['key_id'] = f['key_ids']['rotation']
        resign_custody(f)
        f['revocation']['payload']['sequence'] = 3
        f['revocation']['payload']['revoked_key_ids'] = [f['key_ids']['custody']]
        resign_revocation(f)
        f['trust'] = replace(f['trust'], minimum_checkpoint_sequence=3)
        return f

    def test_01_signed_original_restart_accepts_only_zero_authority(self):
        r = self._evaluate()
        self.assertEqual(r['status'], 'synthetic_checkpoint_consistent_no_authority')
        self.assertEqual(set(r['gate_status'].values()), {'NOT_RUN'})
        self.assertFalse(r['authorized'])
        self.assertFalse(r['can_read_source'])
        self.assertFalse(r['publication_eligible'])

    def test_02_subprocess_restart_reads_exact_independent_pin(self):
        script = ("from persistent_revocation_review import ExternalObserverPin, read_checked_state;"
                  "from pathlib import Path;import sys,json;"
                  "pin=ExternalObserverPin(*json.loads(sys.argv[2]));"
                  "print(read_checked_state(Path(sys.argv[1]),pin)['sequence'])")
        pin_args = [self.pin1.registry_id, self.pin1.sequence_floor,
                    self.pin1.state_sha256, self.pin1.registry_sha256,
                    self.pin1.checkpoint_sha256, self.pin1.observer_ref]
        env = dict(os.environ, PYTHONPATH=str(HERE))
        p = subprocess.run([sys.executable, '-c', script, str(self.path),
                            json.dumps(pin_args)], env=env,
                           capture_output=True, text=True, timeout=10)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), '2')

    def test_03_revoked_key_and_new_pin_survive_restart(self):
        f = self._advanced()
        newer = self._candidate(f, previous=self.pin1)
        pin2 = write_state_rehearsal(self.path, newer, previous_pin=self.pin1)
        self.assertEqual(read_checked_state(self.path, pin2)['sequence'], 3)
        self.assertEqual(self._evaluate(f, pin2)['status'],
                         'synthetic_checkpoint_consistent_no_authority')
        self.assertEqual(self._evaluate(self.original, pin2)['status'], 'withheld')

    def test_04_old_checkpoint_file_restore_denied_against_new_external_pin(self):
        old_bytes = self.path.read_bytes()
        f = self._advanced()
        state2 = self._candidate(f, previous=self.pin1)
        pin2 = write_state_rehearsal(self.path, state2, previous_pin=self.pin1)
        self.path.write_bytes(old_bytes)  # simulate restoring old volume snapshot
        result = self._evaluate(self.original, pin2)
        self.assertEqual(result['status'], 'withheld')
        self.assertIn('persisted_checkpoint_rollback_or_fork', result['reason_codes'])

    def test_05_missing_persistence_refuses_even_with_valid_signatures(self):
        self.path.unlink()
        r = self._evaluate()
        self.assertEqual(r['reason_codes'], ['persistence_state_missing'])

    def test_06_corrupt_file_refuses_even_with_valid_signatures(self):
        self.path.write_text('{"permission":"allow"}', encoding='utf-8')
        self.assertEqual(self._evaluate()['status'], 'withheld')

    def test_07_no_independent_pin_refuses_even_with_valid_signatures(self):
        f = self.original
        r = guarded_restart_verify(
            self.path, None, f['snapshot'], f['policy'], f['events'],
            f['proposal'], f['custody'], f['revocation'],
            checked_at=WHEN, trust=f['trust'])
        self.assertEqual(r['reason_codes'], ['independent_observer_pin_missing'])

    def test_08_changed_pin_or_trust_root_is_withheld(self):
        p = replace(self.pin1, state_sha256='a'*64)
        self.assertEqual(self._evaluate(pin=p)['status'], 'withheld')
        f = fixture()  # fresh synthetic key objects cannot be deep-copied
        f['trust'] = replace(f['trust'], expected_registry_sha256='e'*64)
        self.assertEqual(self._evaluate(f)['status'], 'withheld')

    def test_09_second_persistent_update_must_advance_monotonically(self):
        with self.assertRaisesRegex(SyntheticRestartWithheld,
                                     'persistence_nonmonotonic_or_unlinked'):
            write_state_rehearsal(self.path, self.original_state,
                                  previous_pin=self.pin1)

    def test_10_simultaneous_fork_with_same_sequence_denied(self):
        new = deepcopy(self.original_state)
        new['checked_at'] = '2026-10-15T18:22:00Z'
        self.path.write_text(json.dumps(new, sort_keys=True))
        self.assertEqual(self._evaluate()['status'], 'withheld')

    def test_11_symlink_and_missing_parent_fail_closed(self):
        link = Path(self.temp.name) / 'link.synthetic.json'
        link.symlink_to(self.path)
        with self.assertRaisesRegex(SyntheticRestartWithheld,
                                     'persistence_symlink_forbidden'):
            read_checked_state(link, self.pin1)
        no_parent = Path(self.temp.name) / 'missing' / 'checkpoint.synthetic.json'
        with self.assertRaisesRegex(SyntheticRestartWithheld,
                                     'persistence_directory_untrusted'):
            read_checked_state(no_parent, self.pin1)

    def test_12_external_pin_blocks_both_compromised_signers(self):
        # Hypothetically both test private signing keys have been stolen.
        # Attacker can re-sign a newly forged checkpoint, but CANNOT update the
        # externally pinned state digest and independently maintained floor.
        f = fixture()
        f['custody']['payload']['issued_at'] = '2026-10-14T01:00:00Z'
        resign_custody(f)
        f['revocation']['payload']['sequence'] = 3
        resign_revocation(f)
        f['trust'] = replace(f['trust'], minimum_checkpoint_sequence=3)
        self.assertEqual(self._evaluate(f)['status'], 'withheld')

    def test_13_if_external_pin_is_also_compromised_forgery_is_undetectable(self):
        # This explicitly demonstrates a residual limit, NOT a security PASS.
        # Attacker impersonates both signers AND the out-of-band observer pin.
        f = fixture()
        f['custody']['payload']['issued_at'] = '2026-10-14T01:00:00Z'
        resign_custody(f)
        f['revocation']['payload']['observed_at'] = '2026-10-14T02:00:00Z'
        resign_revocation(f)  # second compromised authority has also signed
        # Current trust is rebuilt by a wholly compromised pin distributor.
        forged_state = self._candidate(f)
        self.path.unlink()
        compromised_pin = write_state_rehearsal(self.path, forged_state)
        r = self._evaluate(f, compromised_pin)
        self.assertEqual(r['status'], 'synthetic_checkpoint_consistent_no_authority')
        self.assertFalse(r['can_read_source'])
        self.assertFalse(r['publication_eligible'])

    def test_14_store_json_has_no_keys_source_text_or_permissions(self):
        text = self.path.read_text(encoding='utf-8')
        for value in ('original_bytes', 'text_sha256', 'signature_b64',
                      'private_key', 'source_url', 'read_reserved'):
            self.assertNotIn(value, text)
        state = json.loads(text)
        for key in ('authorized', 'can_read_source', 'publication_eligible'):
            self.assertIs(state[key], False)

    def test_15_unsigned_state_tamper_denied(self):
        state = json.loads(self.path.read_text(encoding='utf-8'))
        state['sequence'] = 999
        self.path.write_text(json.dumps(state))
        self.assertEqual(self._evaluate()['status'], 'withheld')

    def test_16_revoked_signer_without_rotation_cannot_advance(self):
        f = fixture()
        f['revocation']['payload']['sequence'] = 3
        f['revocation']['payload']['revoked_key_ids'] = [f['key_ids']['custody']]
        resign_revocation(f)
        f['trust'] = replace(f['trust'], minimum_checkpoint_sequence=3)
        with self.assertRaisesRegex(SyntheticRestartWithheld,
                                     'persistence_requires_verified_synthetic_checkpoint'):
            self._candidate(f, previous=self.pin1)

    def test_17_missing_observer_cannot_issue_approval(self):
        r = self._evaluate(pin=replace(self.pin1, observer_ref='bad'))
        self.assertEqual(r['status'], 'withheld')
        self.assertFalse(r['can_issue_review'])
        self.assertEqual(r['holdout_lock']['transcripts_opened'], 0)


if __name__ == '__main__':
    unittest.main()
