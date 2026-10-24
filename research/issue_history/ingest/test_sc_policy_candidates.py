"""Invented policy-relevance fixtures; no actual votes, documents or positions."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from .test_sc_crosswalk import fixture
from .test_sc_event_selection import run
from . import sc_policy_candidates as P


class PolicyCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('SC_ACTION_TEST_ROOT'))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.collection, self.rows = fixture()
        for row in self.rows:
            row.update(policy='unbound',resolution_version='as_adopted')
        self.selection = run(self.collection, self.rows)
        self.document = self.root/'resolution.pdf'
        self.document.write_bytes(b'%PDF-1.4\nInvented engineering fixture; no actual policy text.\n%%EOF')
        self.url = 'https://digitallibrary.un.org/record/999999999/files/S_RES_9999_2024-EN.pdf'
        self.receipts = [{'file':'resolution.pdf','url':self.url,'bytes':self.document.stat().st_size,
                          'sha256':hashlib.sha256(self.document.read_bytes()).hexdigest()}]
        self.binding = {'binding_id':'synthetic-binding-access','resolution_id':'S/RES/9999(2024)',
            'resolution_version':'as_adopted','stage':'adopted_resolution','policy_id':'humanitarian_access',
            'context_id':'thematic_armed_conflict','source_url':self.url,
            'source_sha256':self.receipts[0]['sha256'],'source_anchor':'Invented operative paragraph 2',
            'rationale':'Invented explicit access clause; engineering fixture only.',
            'review_state':'assistant_provisional','evidence_kind':'full_resolution_vote_topic_relevance',
            'comparable':True,'ontology_version':'humanitarian-ontology-1'}

    def build(self, selection=None, bindings=None, receipts=None):
        return P.build_candidates(self.selection if selection is None else selection,
            [self.binding] if bindings is None else bindings,
            self.receipts if receipts is None else receipts,self.root)

    def test_exact_adopted_action_is_one_candidate_not_fifteen_ballots(self):
        before = copy.deepcopy((self.selection,self.binding,self.receipts))
        result = self.build()
        self.assertEqual('un.sc-policy-candidates.v1',result['schema'])
        self.assertEqual(1,len(result['candidates']))
        candidate = result['candidates'][0]
        self.assertEqual(self.selection['events'][0]['action_id'],candidate['action_id'])
        self.assertEqual('S/RES/9999(2024)',candidate['resolution'])
        self.assertEqual('assistant_provisional',candidate['review_state'])
        self.assertEqual('full_resolution_vote_topic_relevance',candidate['evidence_kind'])
        self.assertFalse(candidate['comparable']);self.assertFalse(candidate['comparisons_eligible'])
        self.assertEqual(1,result['summary']['distinct_actions'])
        self.assertEqual(1,result['summary']['candidate_rows'])
        self.assertEqual(before,(self.selection,self.binding,self.receipts))
        self.assertEqual(result,self.build())
        self.assertNotIn('representative_ballots',json.dumps(result))

    def test_two_policy_rows_count_one_action(self):
        second={**self.binding,'binding_id':'synthetic-binding-protection','policy_id':'civilian_protection'}
        result=self.build(bindings=[self.binding,second])
        self.assertEqual(2,result['summary']['candidate_rows'])
        self.assertEqual(1,result['summary']['distinct_actions'])
        self.assertEqual({'humanitarian_access','civilian_protection'}, {c['policy_id'] for c in result['candidates']})

    def test_unmatched_resolution_is_explicit_gap(self):
        result=self.build(bindings=[{**self.binding,'resolution_id':'S/RES/9998(2024)'}])
        self.assertFalse(result['candidates']);self.assertEqual(1,len(result['gaps']))
        self.assertEqual(1,result['summary']['unmatched_bindings'])

    def test_dppa_only_and_failed_draft_do_not_inherit_adopted_binding(self):
        dppa_only=run(self.collection,[])
        self.assertFalse(self.build(selection=dppa_only)['candidates'])
        failed=copy.deepcopy(self.collection)
        failed['events'][0].update(resolution='',outcome='Not adopted - veto')
        result=self.build(selection=run(failed,[]))
        self.assertFalse(result['candidates']);self.assertTrue(result['gaps'])
        self.assertFalse(self.build(selection=run({**self.collection,'events':[]},self.rows))['candidates'])

    def test_duplicate_action_ids_rejected(self):
        selection=copy.deepcopy(self.selection);selection['events'].append(copy.deepcopy(selection['events'][0]))
        with self.assertRaises(ValueError):self.build(selection=selection)

    def test_duplicate_binding_ids_rejected(self):
        with self.assertRaises(ValueError):self.build(bindings=[self.binding,copy.deepcopy(self.binding)])

    def test_selection_requires_supported_version_and_unbound_ineligible_actions(self):
        for mutation in ('schema','version','bound','eligible'):
            selection=copy.deepcopy(self.selection)
            if mutation in ('schema','version'):selection[mutation]='unsupported'
            elif mutation=='bound':selection['events'][0]['issue_binding']='humanitarian_access'
            else:selection['events'][0]['comparisons_eligible']=True
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):self.build(selection=selection)

    def test_invalid_policy_context_or_identity_is_rejected(self):
        for field,value in [('policy_id','aid_spending'),('context_id','gaza'),
                            ('resolution_version','draft'),('stage','draft_resolution'),
                            ('resolution_id','S/2024/9999'),('ontology_version','unsupported')]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.build(bindings=[{**self.binding,field:value}])

    def test_anchor_rationale_and_source_pin_required(self):
        for field in ('source_anchor','rationale','source_sha256','source_url','binding_id','resolution_id'):
            with self.subTest(field=field):
                item={**self.binding};item.pop(field)
                with self.assertRaises(ValueError):self.build(bindings=[item])

    def test_only_assistant_provisional_relevance_is_permitted(self):
        for field,value in [('review_state','owner_confirmed'),('review_state','unreviewed'),
                            ('evidence_kind','national_policy_position')]:
            with self.subTest(field=field,value=value):
                with self.assertRaises(ValueError):self.build(bindings=[{**self.binding,field:value}])

    def test_changed_document_bytes_or_receipt_size_rejected(self):
        original=self.document.read_bytes();self.document.write_bytes(original+b'changed')
        with self.assertRaises(ValueError):self.build()
        self.document.write_bytes(original)
        with self.assertRaises(ValueError):self.build(receipts=[{**self.receipts[0],'bytes':1}])

    def test_binding_source_hash_must_match_verified_receipt(self):
        with self.assertRaises(ValueError):self.build(bindings=[{**self.binding,'source_sha256':'0'*64}])

    def test_nonofficial_http_and_credential_urls_rejected(self):
        for url in ('https://example.com/res.pdf','http://digitallibrary.un.org/res.pdf',
                    'https://user:secret@digitallibrary.un.org/res.pdf'):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):self.build(bindings=[{**self.binding,'source_url':url}],receipts=[{**self.receipts[0],'url':url}])

    def test_relative_path_traversal_absolute_and_missing_files_rejected(self):
        for value in ('../resolution.pdf',str(self.document.resolve()),'missing.pdf'):
            with self.subTest(file=value):
                with self.assertRaises(ValueError):self.build(receipts=[{**self.receipts[0],'file':value}])

    def test_unexpected_receipt_duplicate_or_unmatched_url_is_rejected(self):
        with self.assertRaises(ValueError):self.build(receipts=self.receipts*2)
        with self.assertRaises(ValueError):self.build(receipts=[{**self.receipts[0],'url':'https://docs.un.org/en/S/RES/9999(2024)'}])

    def test_action_identity_and_ballot_stage_must_match_adopted_resolution(self):
        for mutation in ('action_id','resolution','ballot_stage','ballot_resolution'):
            selection=copy.deepcopy(self.selection);event=selection['events'][0]
            if mutation=='action_id':event['action_id']='sc:dppa:invented'
            elif mutation=='resolution':event['resolution']='S/RES/9998(2024)'
            elif mutation=='ballot_stage':event['representative_ballots'][0]['stage']='draft_resolution'
            else:event['representative_ballots'][0]['resolution']='S/RES/9998(2024)'
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):self.build(selection=selection)

    def test_document_symlink_alias_is_rejected(self):
        link=self.root/'alias.pdf'
        try:link.symlink_to(self.document)
        except OSError as error:self.skipTest('Symlinks unavailable: '+str(error))
        with self.assertRaises(ValueError):self.build(receipts=[{**self.receipts[0],'file':link.name}])

    def test_document_hardlink_alias_is_rejected(self):
        link=self.root/'hardlink.pdf'
        try:os.link(self.document,link)
        except OSError as error:self.skipTest('Hard links unavailable: '+str(error))
        with self.assertRaises(ValueError):self.build(receipts=[{**self.receipts[0],'file':link.name}])


if __name__=='__main__':unittest.main()
