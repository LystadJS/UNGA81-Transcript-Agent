"""Synthetic mathematical and source-contract regression tests; offline only."""
import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from fixtures import make_panel, sha
from framework import (AlignmentError, ContractError, actor_distances, cluster_correspondence,
                       compare, digest, grouped_bootstrap, procrustes, to_interchange_v1,
                       validate_panel, write_exports)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ANCHORS = [f'A{i}' for i in range(6)]


class SyntheticLongitudinalTests(unittest.TestCase):
    def panel(self, **kw):
        p = make_panel(**kw)
        self.assertEqual(validate_panel(p)['available'], len([x for x in p['observations'] if x['vector'] is not None]))
        return p

    def test_roster_only_changes_population_not_matched_actor(self):
        p = self.panel()
        z = compare(p, 'p0', 'p1', anchor_ids=ANCHORS, bootstrap_reps=100)
        d = z['high_dimensional']
        self.assertGreater(d['all_actor_centroid_distance'], 2)
        self.assertLess(d['mean_within_actor_distance'], 1e-12)
        self.assertLess(d['common_actor_centroid_distance'], 1e-12)
        self.assertCountEqual(d['arrived_actors'], ['N0', 'N1'])
        self.assertCountEqual(d['departed_actors'], ['D0', 'D1'])
        self.assertLess(z['alignment']['anchor_relative_rmse'], 1e-12)
        self.assertLess(z['display']['common_actor_centroid_distance'], 1e-12)
        self.assertEqual(z['uncertainty']['attempted'], 100)
        self.assertEqual(z['uncertainty']['failed'], 0)
        self.assertAlmostEqual(z['uncertainty']['percentile_interval'][1], 0, places=12)
        self.assertFalse(z['publication_eligible'])

    def test_true_target_motion_recovered_and_roster_explicit(self):
        p = self.panel(motion=True)
        z = compare(p, 'p0', 'p1', anchor_ids=ANCHORS, bootstrap_reps=100)
        actor = next(a for a in z['high_dimensional']['rows'] if a['actor_id'] == 'T0')
        self.assertAlmostEqual(actor['euclidean'], math.hypot(.8, .2), places=10)
        self.assertAlmostEqual(actor['chord'], math.sqrt(2 * actor['cosine']), places=12)
        self.assertIn(9, z['cluster_correspondence']['after_clusters'])
        mapped = next(a for a in z['display']['actor_distances'] if a['actor_id'] == 'T0')
        self.assertAlmostEqual(mapped['euclidean'], math.hypot(.8, .2), places=10)
        self.assertEqual(z['alignment']['mode'], 'rigid_full_refit')
        self.assertEqual(z['uncertainty']['status'], 'sensitivity_only')

    def test_no_roster_no_change_reference_transform(self):
        p = self.panel(roster=False, fit_policy='transformed_reference')
        z = compare(p, 'p0', 'p1', bootstrap_reps=50)
        self.assertEqual(z['alignment']['mode'], 'identity_pinned_transform')
        self.assertAlmostEqual(z['high_dimensional']['all_actor_centroid_distance'], 0)
        self.assertAlmostEqual(z['high_dimensional']['mean_within_actor_distance'], 0)

    def test_missing_meeting_recorded_not_imputed_zero(self):
        p = self.panel(roster=False, unavailable_family=('p1', 3))
        z = compare(p, 'p0', 'p1', anchor_ids=ANCHORS, bootstrap_reps=50)
        self.assertGreater(z['coverage']['unavailable_by_period']['p1'], 0)
        self.assertEqual(z['high_dimensional']['mean_within_actor_distance'], 0)
        self.assertLess(z['common_source']['mean_distance'], 1e-12)
        self.assertEqual(z['uncertainty']['status'], 'withheld')
        env = to_interchange_v1(p, z)
        self.assertEqual(env['coverage']['excluded'], 9)
        self.assertEqual(env['coverage']['models'][0]['excluded'], 9)

    def test_splits_merges_permutation_and_abstention(self):
        p = self.panel(motion=True)
        z = cluster_correspondence(p['observations'], 'p0', 'p1', min_overlap=2)
        self.assertIn(1, z['splits'])
        self.assertEqual(z['arrived_actors'], ['N0', 'N1'])
        self.assertFalse(any(m['before'] == m['after'] for m in z['max_overlap_matching']))
        for r in p['observations']:
            if r['period'] == 'p1' and r['actor_id'] == 'A0':
                r['cluster'] = 0
        z = cluster_correspondence(p['observations'], 'p0', 'p1')
        self.assertGreaterEqual(z['unassigned_after'], 1)
        self.assertGreater(z['eligible_shared_assigned'], 0)

    def test_changes_in_embedding_vocabulary_or_map_fit_rejected(self):
        for mutation in ('fingerprint', 'version', 'map'):
            p = self.panel()
            if mutation == 'fingerprint':
                p['observations'][-1]['representation_fingerprint'] = sha('different-embeddings')
            elif mutation == 'version':
                p['observations'][-1]['representation_version'] = 'unpinned-2'
            else:
                p['observations'][-1]['map_fit_id'] = 'unexpected-second-fit'
            with self.subTest(mutation=mutation), self.assertRaises(ContractError):
                validate_panel(p)

    def test_source_hash_duplicate_offset_actor_evidence_reserve(self):
        def mutate(kind, p):
            r = p['observations'][0]
            if kind == 'duplicate': p['observations'][1]['id'] = r['id']
            if kind == 'hash': r['text_sha256'] = 'invalid-hash'
            if kind == 'offset': r['start'] = 10; r['end'] = None
            if kind == 'speaker': r['actor_kind'] = 'verified_speaker'
            if kind == 'period': r['date'] = '2026-02-10'
            if kind == 'source': r['source_status'] = 'unavailable'
            if kind == 'genre': r['genre'] = ''
        for label in ['duplicate', 'hash', 'offset', 'speaker', 'period', 'source', 'genre']:
            p = self.panel()
            mutate(label, p)
            with self.subTest(case=label), self.assertRaises(ContractError):
                validate_panel(p)
        p = self.panel()
        p['split'] = 'development'
        for r in p['observations']:
            r['source_hash_basis'] = 'raw_response_bytes'
        p['periods'][1]['end'] = '2026-10-06'
        p['observations'][-1]['date'] = '2026-10-05'
        with self.assertRaisesRegex(ContractError, 'Reserved holdout'):
            validate_panel(p)

    def test_anchor_degenerate_incomplete_and_unstable(self):
        p = self.panel()
        with self.assertRaises(AlignmentError):
            compare(p, 'p0', 'p1', anchor_ids=['A0', 'A1'], bootstrap_reps=50)
        for r in p['observations']:
            if r['period'] == 'p1' and r['actor_id'] == 'A0':
                r['map'][0] += 100
        with self.assertRaises(AlignmentError):
            compare(p, 'p0', 'p1', anchor_ids=ANCHORS, bootstrap_reps=50)
        with self.assertRaises(AlignmentError):
            procrustes([[0, 0], [1, 0], [2, 0], [3, 0]], [[0, 0], [1, 0], [2, 0], [3, 0]])

    def test_nonindependent_or_insufficient_groups_withheld(self):
        p = self.panel()
        kept = [r for r in p['observations'] if r['source_family_id'] in
                {'fictional-series-0', 'fictional-series-1'}]
        z = grouped_bootstrap(kept, 'p0', 'p1', repetitions=50)
        self.assertEqual(z['status'], 'withheld')
        self.assertEqual(z['attempted'], 0)

    def test_export_interchange_schema_and_relational_counts(self):
        p = self.panel(motion=True)
        z = compare(p, 'p0', 'p1', anchor_ids=ANCHORS, bootstrap_reps=50)
        env = to_interchange_v1(p, z)
        self.assertEqual(env['schema'], 'un.parallel-analysis.v1')
        self.assertFalse(env['publication_eligible'])
        self.assertEqual(env['coverage']['eligible'], len(p['observations']))
        self.assertEqual(env['coverage']['models'][0]['attempted_fits'], 0)
        for m in env['coverage']['models']:
            self.assertEqual(m['assigned'] + m['unassigned'] + m['not_fitted'], m['eligible'])
        schema_file = ROOT / 'docs/parallel-work/interchange-v1.schema.json'
        if schema_file.exists():
            import jsonschema
            schema = json.loads(schema_file.read_text())
            jsonschema.Draft202012Validator(schema).validate(env)
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'new'
            paths = write_exports(target, z, env)
            self.assertEqual(len(paths), 4)
            self.assertTrue((target / 'aligned-coordinates.csv').exists())
            with self.assertRaises(FileExistsError):
                write_exports(target, z, env)
            self.assertNotIn('fictional_intervention', (target/'aligned-coordinates.csv').read_text())
        p['observations'][0]['text_sha256'] = sha('tampered')
        with self.assertRaises(ContractError):
            to_interchange_v1(p, z)

    def test_development_export_requires_explicit_source_ledger(self):
        p = self.panel(roster=False)
        p['split'] = 'development'
        for r in p['observations']:
            r['source_hash_basis'] = 'raw_response_bytes'
        z = compare(p, 'p0', 'p1', anchor_ids=ANCHORS, bootstrap_reps=50)
        with self.assertRaises(ContractError):
            to_interchange_v1(p, z)
        env = to_interchange_v1(p, z, upstream={'source_schema': 'un.passage-corpus.v1',
            'source_engine': 'read_only_upstream', 'source_hash_basis': 'raw_response_bytes',
            'source_sha256': sha('original-byte-hash'), 'selection_sha256': sha('original-selection'),
            'frame_sha256': None, 'corpus_sha256': None, 'review_sha256': None,
            'missing_reason': None})
        self.assertEqual(env['upstream']['source_sha256'], sha('original-byte-hash'))
        self.assertEqual(env['producer']['fixture_kind'], 'private_development')

    def test_repeatability_read_only_and_cli(self):
        p = self.panel(motion=True)
        original = copy.deepcopy(p)
        one = compare(p, 'p0', 'p1', anchor_ids=ANCHORS, bootstrap_reps=50, bootstrap_seed=321)
        two = compare(p, 'p0', 'p1', anchor_ids=ANCHORS, bootstrap_reps=50, bootstrap_seed=321)
        self.assertEqual(digest(one), digest(two))
        self.assertEqual(original, p)
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / 'demo'
            proc = subprocess.run([sys.executable, str(HERE/'run_demo.py'), '--output', str(output)],
                                  capture_output=True, text=True, timeout=40)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(len(list(output.iterdir())), 4)


if __name__ == '__main__':
    unittest.main(verbosity=2)
