"""Build-level source/packaging checks; no empirical inputs."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from .build import build, catalogue, canonical, HERE
from .. import us_reference as u


class BuildAcceptance(unittest.TestCase):
    def test_all_fictional_models_pass_exact_source_replay(self):
        cat, proofs = catalogue()
        self.assertEqual(len(proofs), 8)
        for s, v in zip(cat['scenes'], proofs):
            self.assertTrue(u.validate_result(s['model'], v['source'], v['receipt']))
            self.assertEqual(s['model']['permissions'], u.PERMISSIONS)

    def test_deterministic_self_contained_html_and_manifest(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ma, mb = build(a), build(b)
            self.assertEqual(ma, mb)
            html=(Path(a)/'index.html').read_text()
            self.assertNotIn('@@',html)
            self.assertIn("connect-src 'none'",html)
            self.assertIn("script-src 'sha256-",html)
            self.assertNotIn('<script src=',html)
            self.assertNotIn('https://',html)
            for name, sha in ma['files'].items():
                self.assertEqual(hashlib.sha256((Path(a)/name).read_bytes()).hexdigest(),sha)
            cat=json.loads((Path(a)/'catalogue.json').read_text())
            self.assertEqual(cat['sha256'],u.digest({k:v for k,v in cat.items() if k!='sha256'}))

    def test_output_cannot_target_repository_or_public_assets(self):
        with self.assertRaises(ValueError):build(HERE/'generated')
        with self.assertRaises(ValueError):build(HERE.parents[4]/'site')

    def test_no_real_source_loader_and_no_dropped_frame(self):
        cat,_=catalogue()
        for scene in cat['scenes']:
            m=scene['model'];self.assertEqual(len(m['comparisons']),30)
            self.assertEqual(len(m['transitions']),24)
            self.assertTrue(all(e['source_pointer'].startswith('/synthetic/') for e in m['evidence']))
        empty=next(s['model'] for s in cat['scenes'] if s['id']=='empty')
        self.assertEqual(empty['evidence'],[])
        self.assertTrue(all(c['distance'] is None for c in empty['comparisons']))


if __name__=='__main__':unittest.main()
