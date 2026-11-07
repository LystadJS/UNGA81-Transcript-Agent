"""Independent PR82 review probes; pinned synthetic candidate, no source collection.

Use the candidate's fixture constructor, but new adversarial input designs and
explicit mathematical expectations. No candidate implementation is patched.
"""
import copy
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(os.environ['PR82_CANDIDATE_ROOT']).resolve()
sys.path.insert(0, str(ROOT))
from research.integration.w2_w4_w6.waggoner.make_schema import write_contract
write_contract()
from research.integration.w2_w4_w6.waggoner import us_reference as u
from research.integration.w2_w4_w6.waggoner.test_us_reference import fixture, receipt, r_tables
PKG = ROOT / 'research/integration/w2_w4_w6/waggoner'


def build(p):
    return u.build_us_reference(p, receipt(p))


def r_output(p):
    with tempfile.TemporaryDirectory(prefix='pr82-review-synthetic-') as temp:
        path = Path(temp)
        r_tables(p, path)
        run = subprocess.run(['Rscript', '--vanilla', str(PKG / 'arithmetic.R'), str(path)],
                             capture_output=True, text=True, timeout=30)
        if run.returncode:
            raise AssertionError('Native R execution failed: ' + run.stderr)
        result = {}
        for name in ('profiles', 'weights', 'comparisons', 'transitions'):
            with (path / ('r_' + name + '.tsv')).open() as f:
                result[name] = list(csv.DictReader(f, delimiter='\t'))
        return result


def meeting_collision_panel():
    p = fixture()
    # ALL meeting IDs are numeric-looking, as permitted by the source contract.
    for i, row in enumerate(p['observations']):
        row['meeting_id'] = str(1000 + i)
    row = next(r for r in p['observations'] if r['country_iso3'] == 'CAN' and r['period'] == 'p0')
    row.update(meeting_id='01', vector=[0, 0, 0])
    second = copy.deepcopy(row)
    second.update(id=row['id']+'-second', parent_id=row['parent_id']+'-second',
                  parent_text_sha256=u.digest('second-parent'), text_sha256=u.digest('second-text'),
                  source_pointer=row['source_pointer']+'-second', vector=[2, 0, 0])
    third = copy.deepcopy(row)
    third.update(id=row['id']+'-third', meeting_id='1', source_sha256=u.digest('third-source'),
                 parent_id=row['parent_id']+'-third', parent_text_sha256=u.digest('third-parent'),
                 text_sha256=u.digest('third-text'), source_pointer=row['source_pointer']+'-third',
                 vector=[5, 0, 0])
    p['observations'].extend([second, third])
    return p


class IndependentPR82Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('Rscript') or not shutil.which('node'):
            raise AssertionError('R and Node are required, not optional/skippable')
        for name, expected in {
            'us_reference.py':'e33b4b40fbe18ab98365501cad45d9529b104d33',
            'arithmetic.R':'0fe4748d88d8ea95a4c6f9422d47239e823f933c',
            'read_model.cjs':'2416e015a86e41edaac4e6115b84a5eca137a32b',
            'schema_contract.py':'41b425822b2846a182c24ca83a8428de390938cb',
            'make_schema.py':'fbdaabf88655d42f491f129770bb2b6bfe705161',
        }.items():
            raw = (PKG/name).read_bytes()
            actual = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if actual != expected:
                raise AssertionError('Candidate changed; repin and independently review: '+name)

    def test_distinct_numeric_meetings_retain_r_weights_and_distance(self):
        p = meeting_collision_panel()
        model = build(p)
        profile = next(r for r in model['profiles'] if r['id']=='CAN/p0')
        self.assertEqual(profile['vector'], [3.0, 0.0, 0.0])
        self.assertEqual(sorted(r['weight'] for r in profile['contributions']), [.25, .25, .5])
        actual = r_output(p)
        weights = sorted(float(r['weight']) for r in actual['weights'] if r['profile_id']=='CAN/p0')
        for a, b in zip(weights, [.25, .25, .5]):
            self.assertAlmostEqual(a, b, places=12, msg='R collapsed distinct original meetings 01 and 1')
        gap = next(float(r['distance']) for r in actual['comparisons'] if r['id']=='CAN/p0')
        self.assertAlmostEqual(gap, 3.0, places=12)

    def test_r_preserves_leading_zero_period_identity(self):
        p = fixture()
        change = {'p0':'001', 'p1':'002'}
        for period in p['periods']:
            period['id'] = change[period['id']]
        for row in p['observations']:
            row['period'] = change[row['period']]
        model = build(p)
        actual = r_output(p)
        self.assertEqual([r['id'] for r in actual['profiles']], [r['id'] for r in model['profiles']])

    def test_maximum_accepted_period_identifier_has_valid_result(self):
        p = fixture()
        long_id = 'p' + 'x'*159
        p['periods'][0]['id'] = long_id
        for row in p['observations']:
            if row['period']=='p0':
                row['period'] = long_id
        u.validate_source(p, receipt(p))  # This source is explicitly admissible.
        model = build(p)
        self.assertTrue(u.validate_result(model, p, receipt(p)))

    def test_missing_middle_us_never_creates_bridge_or_self_zero(self):
        p = fixture(periods=3)
        for row in p['observations']:
            if row['country_iso3']=='USA' and row['period']=='p1':
                row.update(source_status='unavailable', vector=None, date=None, missing_reason='syn-missing')
        model = build(p)
        self.assertTrue(all(r['distance'] is None for r in model['comparisons'] if r['period']=='p1'))
        self.assertTrue(all(t['metrics'] is None for t in model['transitions']))
        self.assertEqual({(t['before'],t['after']) for t in model['transitions']}, {('p0','p1'),('p1','p2')})

    def test_fresh_randomized_gap_algebra(self):
        rng = random.Random(8258103)
        for _ in range(120):
            c0,c1,u0,u1 = [[rng.uniform(-3,3) for _ in range(3)] for _ in range(4)]
            result = u.transition_metrics(c0,c1,u0,u1)
            expected = math.dist(c1,u1)-math.dist(c0,u0)
            self.assertAlmostEqual(result['gap_change'], expected, places=12)
            self.assertAlmostEqual(result['gap_country_contribution']+result['gap_us_contribution'], expected, places=12)

    def test_display_highlight_does_not_refit_us(self):
        p = fixture()
        model = build(p)
        baseline = copy.deepcopy(model['baseline'])
        selection = u.select_comparisons(model, ['CAN'])
        selection[0]['distance'] = 123
        self.assertEqual(model['baseline'], baseline)
        self.assertNotEqual(model['comparisons'][2]['distance'], 123)

    def test_forged_permissions_refused_by_node_and_python(self):
        p = fixture()
        model = build(p)
        model['permissions']['publication_eligible'] = True
        model['sha256'] = u.digest({k:v for k,v in model.items() if k!='sha256'})
        with self.assertRaises(u.ContractError):
            u.validate_result(model,p,receipt(p))
        run = subprocess.run(['node',str(PKG/'read_model.cjs')],
            input=json.dumps({'model':model,'source':p,'receipt':receipt(p)}),text=True,
            capture_output=True,timeout=30)
        self.assertNotEqual(run.returncode,0)


if __name__=='__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentPR82Review))
    record = {'kind':'independent_pr82_synthetic_review','candidate_head':'81110db49786a05f9c8f8ce4d5103c92fe255586',
        'review_base':'5f0a872cff0899819b21326e6c18b7af794556c5','mode':os.environ.get('PR82_REVIEW_MODE'),
        'tests_run':result.testsRun,'failures':[str(t) for t,_ in result.failures],
        'errors':[str(t) for t,_ in result.errors],'skipped':[str(t) for t,_ in result.skipped],
        'result':'pass' if result.wasSuccessful() and not result.skipped else 'fail',
        'publication_eligible':False,'holdout_transcripts_opened':0}
    Path(os.environ['PR82_REVIEW_RECEIPT']).write_text(json.dumps(record,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
