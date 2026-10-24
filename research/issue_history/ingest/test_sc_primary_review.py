"""Synthetic primary-fact receipts; no actual review records are public."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from .test_sc_crosswalk import fixture
from .sc_primary_review import VERSION,load_review,_apply_review
from .sc_crosswalk import build_crosswalk

PINS={'collection_sha256':'a'*64,'ddl_database_sha256':'b'*64,'ddl_original_source_sha256':'c'*64}

def review(root,target='dppa',field='draft',before='S/2024/9999',after='S/2024/9998'):
    facts={'schema':'un.sc-primary-facts.v1','source_url':'https://docs.un.org/en/S/PV.9999','hash_scope':'tool_extracted_primary_metadata','facts':{'resolution':'S/RES/9999(2024)','date':'2024-01-01',field:after},'anchor':'Invented fixture only; no original source bytes'}
    evidence=root/'facts.json';evidence.write_text(json.dumps(facts),encoding='utf-8')
    source={'url':facts['source_url'],'hash_scope':facts['hash_scope'],'sha256':hashlib.sha256(evidence.read_bytes()).hexdigest(),'anchor':facts['anchor'],'evidence_file':'facts.json'}
    correction={'target':target,'event':{'resolution':'S/RES/9999(2024)','date':'2024-01-01','dppa_event_id':'1'},'field':field,'before':before,'after':after,'source':source,'review_state':'assistant_provisional'}
    envelope={'schema':'un.sc-primary-review.v1','version':VERSION,'input_pins':dict(PINS),'corrections':[correction]}
    path=root/'reviews.json';path.write_text(json.dumps(envelope),encoding='utf-8');return path,envelope

class PrimaryReviewTests(unittest.TestCase):
    def test_exact_correction_view_preserves_inputs_ballots_and_proof(self):
        c,rows=fixture();original=copy.deepcopy((c,rows))
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path,_=review(Path(folder));r,hashes=load_review(path,PINS);view,ddl,summary=_apply_review(c,rows,r)
            self.assertEqual('S/2024/9998',view['events'][0]['draft']);self.assertEqual(original,(c,rows));self.assertEqual(rows,ddl)
            self.assertEqual(c['events'][0]['votes'],view['events'][0]['votes']);self.assertEqual(2,len(hashes));self.assertFalse(summary['original_records_modified'])
            note=view['events'][0]['primary_review_notes'][0];self.assertEqual('S/2024/9999',note['original']);self.assertEqual(r['corrections'][0]['source'],note['source'])

    def test_date_view_recovers_identity_without_changing_source(self):
        c,rows=fixture();c['events'][0]['date']='2024-01-02';self.assertFalse(build_crosswalk(c,rows)['links'])
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path,r=review(Path(folder),field='date',before='2024-01-02',after='2024-01-01');r['corrections'][0]['event']['date']='2024-01-02'
            view,ddl,_=_apply_review(c,rows,r);self.assertEqual(1,len(build_crosswalk(view,ddl)['links']));self.assertEqual('2024-01-02',c['events'][0]['date'])

    def test_before_mismatch_and_duplicate_corrections_fail_closed(self):
        c,rows=fixture()
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            _,r=review(Path(folder),before='S/2024/7777')
            with self.assertRaises(ValueError):_apply_review(c,rows,r)
            r['corrections'][0]['before']='S/2024/9999';r['corrections'].append(copy.deepcopy(r['corrections'][0]))
            with self.assertRaises(ValueError):_apply_review(c,rows,r)

    def test_source_pins_and_fact_receipts_are_required(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            root=Path(folder);path,_=review(root)
            with self.assertRaises(ValueError):load_review(path,{**PINS,'ddl_database_sha256':'d'*64})
            (root/'facts.json').write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError):load_review(path,PINS)

    def test_unsupported_fact_cannot_authorize_a_correction(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            root=Path(folder);path,r=review(root);r['corrections'][0]['after']='S/2024/8888';path.write_text(json.dumps(r),encoding='utf-8')
            with self.assertRaises(ValueError):load_review(path,PINS)

    def test_no_vote_changes_owner_labels_or_cross_year_date_repair(self):
        c,rows=fixture()
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            _,r=review(Path(folder));r['corrections'][0].update(field='vote',after='yes')
            with self.assertRaises(ValueError):_apply_review(c,rows,r)
            _,r=review(Path(folder));r['corrections'][0]['review_state']='owner_confirmed'
            with self.assertRaises(ValueError):_apply_review(c,rows,r)
            _,r=review(Path(folder),field='date',before='2024-01-01',after='2025-01-01')
            with self.assertRaises(ValueError):_apply_review(c,rows,r)

    def test_ddl_correction_applies_to_complete_group_copies_only(self):
        c,rows=fixture()
        for row in rows:row['draft']='S/2024/9999'
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            _,r=review(Path(folder),target='ddl');view,ddl,_=_apply_review(c,rows,r)
            self.assertEqual(c,view);self.assertTrue(all(x['draft']=='S/2024/9998' for x in ddl));self.assertTrue(all(x['draft']=='S/2024/9999' for x in rows))
            with self.assertRaises(ValueError):_apply_review(c,rows[:-1],r)

    def test_missing_or_wrong_primary_event_date_is_not_supported(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            root=Path(folder);path,r=review(root);evidence=root/'facts.json';facts=json.loads(evidence.read_text(encoding='utf-8'))
            for date in (None,'2024-01-02'):
                facts['facts']['date']=date;evidence.write_text(json.dumps(facts),encoding='utf-8')
                r['corrections'][0]['source']['sha256']=hashlib.sha256(evidence.read_bytes()).hexdigest();path.write_text(json.dumps(r),encoding='utf-8')
                with self.assertRaises(ValueError):load_review(path,PINS)

    def test_evidence_cannot_escape_review_directory(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            root=Path(folder);path,r=review(root);r['corrections'][0]['source']['evidence_file']='../outside.json';path.write_text(json.dumps(r),encoding='utf-8')
            with self.assertRaises(ValueError):load_review(path,PINS)

if __name__=='__main__':unittest.main()
