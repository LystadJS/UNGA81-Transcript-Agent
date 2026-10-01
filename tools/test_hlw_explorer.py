"""Independent numeric and provenance checks for the actual report explorer."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from analyze_hlw_explorer import analyze

REPORT = Path(__file__).resolve().parents[1]/'reports/hlw-cuba'


class ExplorerChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = analyze(REPORT/'evidence.csv')
        with (REPORT/'evidence.csv').open(encoding='utf-8-sig') as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_membership_and_no_topic_hit_duplication(self):
        x = self.result
        by_offset = {(r['statement_id'], r['start_char'], r['end_char']): r for r in self.rows}
        ids = set()
        for p in x['points']:
            identity = (p['statement_id'], p['start_char'], p['end_char'])
            self.assertNotIn(identity, ids)
            ids.add(identity)
            r = by_offset[identity]
            self.assertEqual(p['quote'], r['quote'])
            self.assertEqual(p['raw_sha256'], r['raw_sha256'])
            self.assertNotEqual(p['scope'], 'other_week_proceedings')
        self.assertEqual((x['counts']['topic_rows'],len(ids)), (71,65))
        self.assertEqual(x['source']['sha256'],hashlib.sha256((REPORT/'evidence.csv').read_bytes()).hexdigest())

    def test_independent_overlap_recount(self):
        x = self.result
        for i,a in enumerate(x['topics']):
            for j,b in enumerate(x['topics']):
                both=either=0
                for identity in {(p['raw_file'],p['json_pointer']) for p in x['points']}:
                    hits={r['topic'] for r in self.rows if (r['raw_file'],r['json_pointer'])==identity}
                    both+=int(a in hits and b in hits)
                    either+=int(a in hits or b in hits)
                cell=x['overlap'][i][j]
                self.assertEqual((cell['intersection'],cell['union']),(both,either))
                self.assertAlmostEqual(cell['jaccard'],both/either)

    def test_independent_silhouette_and_projection_variance(self):
        x=self.result
        a=TfidfVectorizer(stop_words='english',sublinear_tf=True).fit_transform([p['quote'] for p in x['points']]).toarray()
        distances=np.clip(1-a@a.T,0,2)
        np.fill_diagonal(distances,0)
        for partition in x['partitions']:
            labels=np.array(partition['labels']);scores=[]
            self.assertEqual(sum(c['n'] for c in partition['clusters']),len(a))
            for i,g in enumerate(labels):
                own=np.flatnonzero(labels==g)
                if len(own)==1:
                    scores.append(0);continue
                within=distances[i,own].sum()/(len(own)-1)
                between=min(distances[i,labels==h].mean() for h in set(labels) if h!=g)
                scores.append((between-within)/max(within,between))
            self.assertAlmostEqual(float(np.mean(scores)),partition['silhouette'],places=10)
        centered=a-a.mean(axis=0)
        eig=np.linalg.eigvalsh(centered@centered.T)[::-1]
        np.testing.assert_allclose(x['variance_ratio'],eig[:2]/eig.sum(),atol=1e-12)

    def test_deterministic_and_serializable(self):
        self.assertEqual(self.result,analyze(REPORT/'evidence.csv'))
        self.assertEqual(self.result,json.loads((REPORT/'explorer.json').read_text(encoding='utf-8')))
        json.dumps(self.result,allow_nan=False)
        self.assertTrue(self.result['audit_only'])
        self.assertFalse(self.result['human_review_complete'])

    def test_empty_input_fails_without_sampling(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'empty.csv';p.write_text('scope,raw_file,json_pointer,topic\n')
            with self.assertRaisesRegex(ValueError,'6–500'):
                analyze(p)


if __name__=='__main__':
    unittest.main()
