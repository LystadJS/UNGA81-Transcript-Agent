import copy, hashlib, json, tempfile, unittest
from pathlib import Path
import review_data as rd
import reviewed_loader as loader
import pilot_review as pilot

class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='un-i9-fixture-');self.base=Path(self.tmp.name).resolve()
        assert self.base.is_relative_to(Path(tempfile.gettempdir()).resolve())
        src=self.base/'speeches.json';src.write_text(json.dumps([dict(iso3='AAA',date='2020-01-01',text='Artificial intelligence can improve fictional public services. A fictional policy example.')]),encoding='utf-8')
        self.root=self.base/'pilot';pilot.prepare(self.root,src)
    def tearDown(self):self.tmp.cleanup()
    def finalize(self,label='relevant'):
        meta=json.loads((self.root/'pilot.json').read_text());payload={'token':meta['csrf'],'confirmed':True,'reviewer':'SYNTHETIC-TEST-REVIEWER','rows':[dict(passage_id=i,label=label,rationale='Fictional software fixture, not human annotation') for i in meta['selected_ids']]}
        pilot.complete(self.root,payload)
    def run_fixture(self):
        run=self.base/'daily';(run/'audit/analytics').mkdir(parents=True)
        (run/'checkpoint.json').write_text(json.dumps(dict(stage='complete',no_email_sent=True)))
        (run/'validation.json').write_text(json.dumps(dict(passed=True,five_output_packet_contract='passed')))
        (run/'brief.json').write_text('{}')
        for name in ('daily_briefing.eml','daily_briefing.html','daily_briefing.txt'): (run/name).write_text('Fictional unchanged O1-O5 product')
        for name in ('method_ledger.csv','gate_ledger.csv'):(run/'audit/analytics'/name).write_text('fixture\n')
        s=rd.rows(self.root/'sources.csv')[1][0];text=(self.root/s['text_path']).read_text(encoding='utf-8')
        (run/'audit/speeches.json').write_text(json.dumps([{'iso3':s['iso3'],'text':text}]))
        return run
    def test_unreviewed_rejected(self):
        with self.assertRaisesRegex(ValueError,'incomplete'):loader.load_bundle(self.root)
    def test_single_review_is_explicit(self):
        self.finalize();r=loader.load_bundle(self.root)
        self.assertEqual(r['review_mode'],'single_reviewer_pilot');self.assertFalse(r['independent_review_established']);self.assertFalse(r['publication_eligible']);self.assertFalse(r['model_fit_authorized']);self.assertFalse(r['training_split_validated'])
    def test_insufficient_not_negative(self):
        self.finalize('insufficient');self.assertIsNone(loader.load_bundle(self.root)['records'][0]['binary_label'])
    def test_evidence_bound(self):
        self.finalize();r=loader.load_bundle(self.root);record=r['records'][0]
        self.assertEqual(hashlib.sha256((self.root/'texts/s0001.txt').read_bytes()).hexdigest(),record['text_sha256'])
        self.assertEqual(record['binary_label'],1)
    def test_source_tampering_rejected(self):
        self.finalize();(self.root/'texts/s0001.txt').write_text('changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):loader.load_bundle(self.root)
    def test_empty_target_rejected(self):
        self.finalize();rd.write_csv(self.root/'propositions.csv',rd.SCHEMAS['propositions'].split(),[])
        with self.assertRaisesRegex(ValueError,'named versioned'):loader.load_bundle(self.root)
    def test_pilot_not_training_split(self):
        self.finalize()
        with self.assertRaisesRegex(ValueError,'split|sets must be'):loader.load_bundle(self.root,'labels')
    def test_fake_independent_mode_rejected(self):
        self.finalize();p=json.loads((self.root/'bundle.json').read_text());p['review_mode']='independent';(self.root/'bundle.json').write_text(json.dumps(p))
        with self.assertRaisesRegex(ValueError,'independent reviews'):loader.load_bundle(self.root)
    def test_unknown_mode_rejected(self):
        self.finalize();p=json.loads((self.root/'bundle.json').read_text());p['review_mode']='fast_unreviewed';(self.root/'bundle.json').write_text(json.dumps(p))
        with self.assertRaisesRegex(ValueError,'Unknown review mode'):loader.load_bundle(self.root)
    def test_export_immutable(self):
        self.finalize();out=self.base/'import.json';loader.export(self.root,out)
        with self.assertRaises(FileExistsError):loader.export(self.root,out)
    def test_attach_leaves_every_existing_file_unchanged(self):
        self.finalize();run=self.run_fixture();before={p.relative_to(run):loader.sha(p) for p in run.rglob('*') if p.is_file()};r=loader.attach(self.root,run)
        self.assertEqual(r['matched_passages'],1)
        self.assertEqual(before,{p:loader.sha(run/p) for p in before})
        receipt=json.loads((Path(r['audit_directory'])/'receipt.json').read_text());self.assertFalse(receipt['method_gates_changed'])
    def test_attach_rejects_failed_daily_run(self):
        self.finalize();run=self.run_fixture();(run/'validation.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'five-output'):loader.attach(self.root,run)
    def test_attach_rejects_unrelated_corpus(self):
        self.finalize();run=self.run_fixture();(run/'audit/speeches.json').write_text('[{"iso3":"BBB","text":"other"}]')
        with self.assertRaisesRegex(ValueError,'resolves'):loader.attach(self.root,run)
    def test_attach_rejects_duplicate(self):
        self.finalize();run=self.run_fixture();loader.attach(self.root,run)
        with self.assertRaises(FileExistsError):loader.attach(self.root,run)
    def test_path_escape(self):
        with self.assertRaisesRegex(ValueError,'Unsafe'):loader.safe(self.root,'../escape.txt')
    def test_no_preassigned_labels(self):
        self.assertEqual(rd.rows(self.root/'annotations.csv')[1],[]);self.assertFalse(json.loads((self.root/'bundle.json').read_text())['human_review_complete'])
    def test_completion_needs_confirmation(self):
        with self.assertRaisesRegex(ValueError,'confirmation'):pilot.complete(self.root,{'confirmed':False})
    def test_completion_requires_all_passages(self):
        p=json.loads((self.root/'pilot.json').read_text())
        with self.assertRaisesRegex(ValueError,'Every selected'):pilot.complete(self.root,{'token':p['csrf'],'confirmed':True,'reviewer':'fixture','rows':[]})
    def test_no_second_finalization(self):
        self.finalize()
        with self.assertRaisesRegex(ValueError,'already finalized'):self.finalize()
    def test_save_workflow_attaches_review(self):
        self.finalize();run=self.run_fixture();result=pilot.finish_workflow(self.root,run)
        self.assertEqual(result['matched_passages'],1);self.assertTrue((self.root/'workflow.json').exists())
    def test_engineering_fixture_cannot_claim_human_completion(self):
        self.finalize();policy=json.loads((self.root/'bundle.json').read_text());policy['engineering_fixture']=True;(self.root/'bundle.json').write_text(json.dumps(policy))
        result=loader.load_bundle(self.root);self.assertFalse(result['human_review_complete']);self.assertTrue(result['engineering_fixture'])
    def test_review_cannot_predate_evidence(self):
        self.finalize();rows=rd.rows(self.root/'annotations.csv')[1];rows[0]['reviewed_at']='2019-01-01T00:00:00Z';rd.write_csv(self.root/'annotations.csv',rd.SCHEMAS['annotations'].split(),rows)
        with self.assertRaisesRegex(ValueError,'predates available'):loader.load_bundle(self.root)
    def test_snapshot_identity_changes_with_labels(self):
        self.finalize();before=loader.load_bundle(self.root)['bundle_sha256'];rows=rd.rows(self.root/'adjudications.csv')[1];rows[0]['final_label']='insufficient';rd.write_csv(self.root/'adjudications.csv',rd.SCHEMAS['adjudications'].split(),rows)
        self.assertNotEqual(before,loader.load_bundle(self.root)['bundle_sha256'])

if __name__=='__main__':unittest.main(verbosity=2)
