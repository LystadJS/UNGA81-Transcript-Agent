"""R1/R2 regression coverage. Original golden cases and review probes are retained."""
from copy import deepcopy
import csv
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from . import us_reference as u
from .make_schema import contract
from .schema_contract import validate, SchemaError
from .test_us_reference import fixture, receipt, r_tables, missing, node_model

HERE = Path(__file__).resolve().parent


def build(panel):
    return u.build_us_reference(panel, receipt(panel))


def rename_periods(panel, names):
    mapping = dict(zip([p['id'] for p in panel['periods']], names))
    for p in panel['periods']:
        p['id'] = mapping[p['id']]
    for row in panel['observations']:
        row['period'] = mapping[row['period']]


def meeting_panel(first='01', second='1'):
    p = fixture()
    for i, row in enumerate(p['observations']):
        row['meeting_id'] = str(1000 + i)
    r = next(r for r in p['observations'] if r['country_iso3'] == 'CAN' and r['period'] == 'p0')
    r.update(meeting_id=first, vector=[0, 0, 0])
    b = deepcopy(r)
    b.update(id=r['id']+'-second', parent_id=r['parent_id']+'-second',
             parent_text_sha256=u.digest('second-parent'), text_sha256=u.digest('second-text'),
             source_pointer=r['source_pointer']+'-second', vector=[2, 0, 0])
    c = deepcopy(r)
    c.update(id=r['id']+'-third', meeting_id=second, source_sha256=u.digest('third-source'),
             parent_id=r['parent_id']+'-third', parent_text_sha256=u.digest('third-parent'),
             text_sha256=u.digest('third-text'), source_pointer=r['source_pointer']+'-third',
             vector=[5, 0, 0])
    p['observations'].extend([b, c])
    return p


def run_r(panel, edit=None):
    with tempfile.TemporaryDirectory(prefix='pr82-r1-r2-synthetic-') as temp:
        root = Path(temp)
        r_tables(panel, root)
        if edit:
            edit(root)
        process = subprocess.run(['Rscript', '--vanilla', str(HERE/'arithmetic.R'), str(root)],
                                 text=True, capture_output=True, timeout=30)
        output = {}
        if process.returncode == 0:
            for name in ('profiles', 'weights', 'comparisons', 'transitions'):
                with (root/f'r_{name}.tsv').open() as stream:
                    output[name] = list(csv.DictReader(stream, delimiter='\t'))
        return process, output


@unittest.skipUnless(shutil.which('Rscript'), 'Native R required for R1/R2 regression acceptance')
class RIdentifierRegression(unittest.TestCase):
    def test_original_meeting_collision_and_additional_opaque_ids(self):
        for first, second in [('01','1'), ('1e0','1'), ('9007199254740992','9007199254740993')]:
            with self.subTest(first=first, second=second):
                p = meeting_panel(first, second)
                model = build(p)
                expected = next(x for x in model['profiles'] if x['id'] == 'CAN/p0')
                self.assertEqual(expected['vector'], [3.0, 0.0, 0.0])
                process, output = run_r(p)
                self.assertEqual(process.returncode, 0, process.stderr)
                weights = sorted(float(x['weight']) for x in output['weights'] if x['profile_id']=='CAN/p0')
                self.assertEqual(weights, [.25, .25, .5])
                actual = next(x for x in output['comparisons'] if x['id']=='CAN/p0')
                self.assertEqual(float(actual['distance']), 3.0)

    def test_original_leading_zero_periods_and_other_string_forms(self):
        for ids in [('001','002'), ('01','1'), ('TRUE','FALSE'), ('NA','NaN')]:
            with self.subTest(ids=ids):
                p = fixture()
                rename_periods(p, ids)
                model = build(p)
                process, output = run_r(p)
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertEqual([x['id'] for x in output['profiles']], [x['id'] for x in model['profiles']])
                self.assertEqual([(x['before'],x['after']) for x in output['transitions']],
                                 [(x['before'],x['after']) for x in model['transitions']])

    def test_numeric_feature_conversion_rejects_malformed_values(self):
        for invalid in ('garbage','TRUE','NA','NaN','Inf','1e999','1e101',''):
            with self.subTest(value=invalid):
                def edit(root):
                    path = root/'source.tsv'
                    lines = path.read_text().splitlines()
                    header, row = lines[0].split('\t'), lines[1].split('\t')
                    row[header.index('v0')] = invalid
                    lines[1] = '\t'.join(row)
                    path.write_text('\n'.join(lines)+'\n')
                process, _ = run_r(fixture(), edit)
                self.assertNotEqual(process.returncode, 0)

    def test_empty_features_remain_missing_not_zero(self):
        p = fixture(periods=3)
        for row in p['observations']:
            if row['country_iso3']=='USA' and row['period']=='p1':
                missing(row)
        process, output = run_r(p)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(all(x['distance']=='' for x in output['comparisons'] if x['id'].endswith('/p1')))
        self.assertTrue(all(x['state']=='withheld' and x['gap_change']=='' for x in output['transitions']))


class DerivedIdentityRegression(unittest.TestCase):
    def test_full_accepted_period_range_produces_valid_identities(self):
        for size in (1,156,157,159,160):
            with self.subTest(size=size):
                p = fixture()
                rename_periods(p, ['p'+'x'*(size-1), 'q'+'y'*(size-1)])
                u.validate_source(p, receipt(p))
                model = build(p)
                self.assertTrue(u.validate_result(model,p,receipt(p)))
                self.assertTrue(validate(model))
                for profile in model['profiles']:
                    self.assertEqual(profile['id'], profile['country_iso3']+'/'+profile['period'])
                    self.assertEqual(len(profile['id']), size+4)
                self.assertEqual(set(model['baseline']['profile_hashes']), {x['id'] for x in p['periods']})

    def test_source_limit_and_derived_id_shape_remain_strict(self):
        p = fixture()
        rename_periods(p, ['p'+'x'*160, 'p1'])
        with self.assertRaises(u.ContractError):
            build(p)
        model = build(fixture())
        for name, key in [('profiles','id'), ('comparisons','id'),
                          ('transitions','before_comparison_id'), ('transitions','after_comparison_id')]:
            for bad in ('p0','usa/p0','USA/','USA/'+'p'*161):
                m = deepcopy(model)
                m[name][0][key] = bad
                with self.subTest(name=name,key=key,value=bad), self.assertRaises(SchemaError):
                    validate(m)

    @unittest.skipUnless(shutil.which('node'), 'Native Node required for derived-ID parity')
    def test_node_replays_maximum_identity_and_rejects_invalid_shapes(self):
        p = fixture()
        rename_periods(p, ['p'+'x'*159, 'q'+'y'*159])
        m = build(p)
        run = node_model(m,p)
        self.assertEqual(run.returncode,0,run.stderr)
        for group,key in [('profiles','id'),('comparisons','id'),('transitions','after_comparison_id')]:
            changed = deepcopy(m)
            changed[group][0][key] = 'USA/'+'x'*161
            changed['sha256'] = u.digest({k:v for k,v in changed.items() if k!='sha256'})
            self.assertNotEqual(node_model(changed,p).returncode,0)

    def test_standard_schema_checks_maximum_identity_and_source_limit(self):
        try:
            from jsonschema import Draft202012Validator, FormatChecker, ValidationError
        except ModuleNotFoundError:
            self.skipTest('Independent JSON Schema validator unavailable')
        schema = contract()
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        p = fixture()
        rename_periods(p, ['p'+'x'*159, 'q'+'y'*159])
        model = build(p)
        validator.validate(model)
        source_validator = Draft202012Validator({**schema,'$ref':'#/$defs/source'},format_checker=FormatChecker())
        source_validator.validate(p)
        p['periods'][0]['id'] += 'x'
        with self.assertRaises(ValidationError):
            source_validator.validate(p)
        model['transitions'][0]['before_comparison_id'] += 'x'
        with self.assertRaises(ValidationError):
            validator.validate(model)


if __name__ == '__main__':
    unittest.main()
