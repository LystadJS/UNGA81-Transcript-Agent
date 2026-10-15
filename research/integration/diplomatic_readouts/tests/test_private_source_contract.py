"""Synthetic-only proposals: no registry access, authorizations or holdout reads."""
from copy import deepcopy
import json
import unittest

from private_source_contract import (
    AuthorizationWithheld, REQUIRED_GATES, SCHEMA_ID,
    assert_design_only, make_proposal, proposal_digest,
)


class PrivateAuthorizationDesignTests(unittest.TestCase):
    def setUp(self):
        self.envelope = {
            'schema':'un.parallel-analysis.v1',
            'publication_eligible': False, 'evaluation_role':'engineering_only',
            'producer':{'fixture_kind':'synthetic'},
            'cohort':{'split':'synthetic','total_in_frame':5},
            'upstream':{'source_schema':'synthetic.v1',
                        'source_hash_basis':'synthetic',
                        'source_sha256':'a'*64,
                        'selection_sha256':'b'*64},
            'coverage':{'observations_total':4, 'eligible':2,
                        'excluded':2, 'unavailable_sources':1},
        }
        self.digest = 'c'*64

    def proposal(self):
        return make_proposal(self.envelope, self.digest)

    def test_public_proposal_always_withheld(self):
        p = self.proposal()
        assert_design_only(p)
        self.assertEqual(p['schema'], SCHEMA_ID)
        self.assertEqual(set(p['gate_status']), set(REQUIRED_GATES))
        self.assertEqual(set(p['gate_status'].values()), {'NOT_RUN'})
        self.assertFalse(p['authorized'])
        self.assertFalse(p['publication_eligible'])
        self.assertFalse(p['delivery_eligible'])
        self.assertEqual(p['reserved_holdout']['transcripts_opened'], 0)

    def test_unknown_source_private_keys_cannot_be_exported(self):
        self.envelope['source_text'] = 'DO_NOT_COPY_SYNTHETIC_SECRET'
        self.envelope['upstream']['credentials'] = 'SYNTHETIC_CREDENTIAL'
        p = self.proposal()
        text = json.dumps(p)
        self.assertNotIn('DO_NOT_COPY_SYNTHETIC_SECRET',text)
        self.assertNotIn('SYNTHETIC_CREDENTIAL',text)
        self.assertNotIn('source_text',text)
        self.assertNotIn('credentials',text)

    def test_cannot_escalate_private_gate(self):
        p = self.proposal()
        p['gate_status']['original_bytes']='PASS'
        with self.assertRaisesRegex(AuthorizationWithheld,'private_gates_must_remain_not_run'):
            assert_design_only(p)

    def test_cannot_escalate_authorization_or_delivery(self):
        for k in ('authorized','publication_eligible','delivery_eligible'):
            p = self.proposal()
            p[k] = True
            with self.assertRaises(AuthorizationWithheld):
                assert_design_only(p)

    def test_cannot_open_reserved_holdout(self):
        p = self.proposal()
        p['reserved_holdout']['transcripts_opened']=1
        with self.assertRaisesRegex(AuthorizationWithheld,'reserved_holdout_must_remain_sealed'):
            assert_design_only(p)

    def test_private_source_mode_is_not_implemented(self):
        self.envelope['cohort']['split']='development'
        self.envelope['producer']['fixture_kind']='private_development'
        with self.assertRaisesRegex(AuthorizationWithheld,'real_source_authorization_not_implemented'):
            self.proposal()

    def test_population_and_digest_fail_closed(self):
        self.envelope['coverage']['eligible']=3
        with self.assertRaisesRegex(AuthorizationWithheld,'inconsistent_source_population'):
            self.proposal()
        self.envelope['coverage']['eligible']=2
        with self.assertRaisesRegex(AuthorizationWithheld,'invalid_or_unverified_envelope_reference'):
            make_proposal(self.envelope,'not-a-sha')

    def test_payload_is_closed(self):
        p=self.proposal()
        p['private_source_path']='/tmp/restricted'
        with self.assertRaisesRegex(AuthorizationWithheld,'proposal_extra_or_missing_fields'):
            assert_design_only(p)

    def test_canonical_determinism_and_digest(self):
        a, b=self.proposal(), self.proposal()
        self.assertEqual(a,b)
        self.assertEqual(proposal_digest(a),proposal_digest(b))
        self.assertEqual(len(proposal_digest(a)),64)

    def test_schema_alignment_and_reject_escalation(self):
        from pathlib import Path
        import jsonschema
        schema = json.loads((Path(__file__).resolve().parents[1]/'private_source_contract.v0.schema.json').read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        p=self.proposal()
        jsonschema.Draft202012Validator(schema).validate(p)
        mutated=deepcopy(p)
        mutated['gate_status']['source_registry']='PASS'
        self.assertTrue(list(jsonschema.Draft202012Validator(schema).iter_errors(mutated)))


if __name__=='__main__': unittest.main()
