"""CLI/inventory and cross-grain regression checks; all fixtures synthetic."""
import json
from pathlib import Path
import tempfile
import unittest

import inventory
import protocol
import replay
import run_qa
from test_protocol import specimen, synthetic_schema


class InventoryTests(unittest.TestCase):
    def synthetic_catalog(self):
        return {'schema':'un.i8.catalog.v1','methods':[
            {'id':'M03','method':'Synthetic embedding placeholder','research_kernel':'synthetic_tested',
             'runner':'run.R','required_gates':['source_text'],
             'publication_eligible':False,'daily_adapter_integrated':False},
            {'id':'M26','method':'Unavailable movement model','research_kernel':'not_implemented',
             'runner':None,'required_gates':['supported_regime'],
             'publication_eligible':False,'daily_adapter_integrated':False}]}

    def test_method_registry_includes_unimplemented(self):
        with tempfile.TemporaryDirectory() as td:
            obj=inventory.build(Path(td),catalog=self.synthetic_catalog())
            self.assertEqual(obj['count_registered'],2)
            self.assertEqual(obj['count_declared_kernels'],1)
            self.assertIsNone(obj['methods'][1]['runner'])
            self.assertEqual(obj['methods'][1]['execution_evidence'],'inherited declaration; not independently executed')

    def test_registry_snapshot_detects_source_drift(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'research/reproducibility_audit').mkdir(parents=True)
            source=self.synthetic_catalog()
            raw=(json.dumps(source,sort_keys=True)+'\n').encode()
            (root/'research/catalog.json').write_bytes(raw)
            snapshot={'source_blob_sha':protocol.git_blob_sha(raw),
                      'source_catalog_schema':source['schema'],
                      'methods':[{'method_id':m['id'],'name':m['method'],
                                  'required_gates':m['required_gates'],
                                  'registered_state':m['research_kernel'],
                                  'runner':None if m['runner'] is None else 'research/'+m['runner']}
                                 for m in source['methods']]}
            source['backlog_methods']=2;source['synthetic_kernels']=1
            # Correct the metadata fixture before testing the signed snapshot.
            raw=(json.dumps(source,sort_keys=True)+'\n').encode()
            (root/'research/catalog.json').write_bytes(raw)
            snapshot['source_blob_sha']=protocol.git_blob_sha(raw)
            (root/'research/reproducibility_audit/method_inventory.json').write_text(json.dumps(snapshot))
            self.assertEqual(inventory.verify_snapshot(root),[])
            (root/'research/catalog.json').write_bytes(raw+b' ')
            self.assertIn('method catalog source Git blob mismatch',inventory.verify_snapshot(root))

    def test_duplicate_catalog_id_rejected(self):
        c=self.synthetic_catalog();c['methods'][1]['id']='M03'
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError): inventory.build(Path(td),catalog=c)

    def test_unauthorized_publication_rejected(self):
        c=self.synthetic_catalog();c['methods'][0]['publication_eligible']=True
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError): inventory.build(Path(td),catalog=c)


class QAIntegrationTests(unittest.TestCase):
    def test_no_external_access_yields_not_run_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            report=run_qa.build_summary(Path(td))
            by_name={x['name']:x['status'] for x in report['checks']}
            self.assertEqual(by_name['authoritative_contract'],'NOT RUN')
            self.assertEqual(by_name['actual_public_build_privacy_scan'],'NOT RUN')
            self.assertEqual(by_name['current_head_ci'],'NOT RUN')
            self.assertEqual(by_name['two-process_synthetic_numerical_replay'],'PASS')
            self.assertFalse(report['publication_authorized'])

    def test_bad_public_root_fails_not_passes(self):
        with tempfile.TemporaryDirectory() as td:
            report=run_qa.build_summary(Path(td),public_root=Path(td)/'absent')
            by_name={x['name']:x['status'] for x in report['checks']}
            self.assertEqual(by_name['actual_public_build_privacy_scan'],'FAIL')

    def test_path_protection_passes_only_owned_prefix(self):
        with tempfile.TemporaryDirectory() as td:
            report=run_qa.build_summary(Path(td),changed_paths=['research/reproducibility_audit/test_harness.py'])
            self.assertEqual({c['name']:c['status'] for c in report['checks']}['owned_path_and_frozen_gate_diff'],'PASS')
            report2=run_qa.build_summary(Path(td),changed_paths=['.github/workflows/pages.yml'])
            self.assertEqual({c['name']:c['status'] for c in report2['checks']}['owned_path_and_frozen_gate_diff'],'FAIL')

    def test_corrupt_synthetic_input_does_not_get_pass(self):
        d=specimen();d['producer']['fixture_kind']='private_development'
        with tempfile.TemporaryDirectory() as td:
            report=run_qa.build_summary(Path(td),envelope=d)
            self.assertEqual({c['name']:c['status'] for c in report['checks']}['interchange'],'FAIL')

    def test_per_obs_frame_and_meeting_denominators_distinct(self):
        d=specimen();d['cohort']['total_in_frame']=1
        d['coverage']['inventory_meetings']=1
        self.assertEqual(protocol.validate_envelope(d,synthetic_schema()),[])

    def test_child_output_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'worker.py'
            p.write_text('print("{}")\n')
            d={'schema':'un.replay-fixture.v1','fixture_kind':'synthetic',
               'seed':123,'observations':[1,2,3]}
            self.assertEqual(replay.replay(d,worker=p)['status'],'FAIL')


if __name__=='__main__': unittest.main()
