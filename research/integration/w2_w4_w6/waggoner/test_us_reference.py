"""Source-free acceptance, independent Node/base-R replay and native W4 binding.

All vectors, source identities and review records are freshly fictional. Missing
runtimes or upstream code are explicit skips, never reported as acceptance.
"""
from __future__ import annotations
import copy
import csv
import importlib.util
import json
import math
import random
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from . import us_reference as u

HERE = Path(__file__).resolve().parent
GOLDEN = json.loads((HERE / 'golden_cases.json').read_text())


def receipt(panel):
    return {'kind': 'synthetic_consistency_only', 'hash_basis': u.HASH_BASIS, 'panel_sha256': u.digest(panel)}


def fixture(case=None, *, periods=2, countries=('USA', 'CAN', 'FRA'), genres=('debate',)):
    """Fictional panel, not country observations or a real-source receipt."""
    case = case or GOLDEN['cases'][2]
    metric = {'id': 'syn-frozen-3d', 'version': '1', 'dimension': 3,
              'feature_order': ['syn-axis-1', 'syn-axis-2', 'syn-axis-3'],
              'space_kind': 'full_feature_space', 'preprocessing_id': 'syn-fixed',
              'normalization': 'none', 'fit_selection_sha256': u.digest('synthetic-fit'),
              'training_cutoff': '1999-12-31', 'upstream_fingerprint': u.digest('synthetic-upstream')}
    metric['fingerprint'] = u.digest(metric)
    panel = {'schema': u.INPUT_SCHEMA, 'split': 'synthetic',
             'identity': {'producer_schema': 'un.longitudinal-panel.v1', 'producer_version': '1',
                 'producer_panel_sha256': u.digest('synthetic-panel'), 'selection_sha256': u.digest('synthetic-selection'),
                 'runtime_id': 'synthetic-test'},
             'metric_space': metric,
             'display_space': {'method': 'fixed_orthonormal_linear', 'basis': [[1, 0], [0, 1], [0, 0]],
                 'center': [0, 0, 0], 'metric_fingerprint': metric['fingerprint'], 'fit_id': 'syn-projection'},
             'scope': {'countries': list(countries), 'genres': list(genres), 'language': 'en',
                 'source_type': 'synthetic', 'topic_id': 'syn-topic', 'support_mode': 'common',
                 'weight_policy': u.WEIGHT_POLICY, 'source_unit_policy':'one_vector_per_original_parent', 'baseline_iso3': 'USA', 'baseline_mode': 'contemporaneous'},
             'periods': [{'id': f'p{i}', 'start': f'{2000+i}-01-01', 'end': f'{2000+i}-12-31'} for i in range(periods)],
             'observations': []}
    for country in countries:
        for i, period in enumerate(panel['periods']):
            for genre in genres:
                key = f'syn-{country}-{period["id"]}-{genre}'
                vector = case[('u' if country == 'USA' else 'c') + str(min(i,1))]
                row = dict.fromkeys(u.OBS_KEYS)
                row.update({'id': key, 'period': period['id'], 'date': period['start'],
                    'country_iso3': country, 'actor_id': f'syn-person-{country}-{i}',
                    'speaker_id': f'syn-speaker-{country}-{i}', 'speech_id': f'{key}-speech',
                    'capacity': 'national', 'attribution_status': 'synthetic_verified',
                    'review_receipt': f'{key}-review', 'genre': genre, 'language': 'en',
                    'source_type': 'synthetic', 'topic_id': 'syn-topic', 'source_status': 'available',
                    'meeting_id': f'{key}-meeting', 'source_family_id': f'syn-family-{country}-{genre}',
                    'source_sha256': u.digest(key+'-source'), 'text_sha256': u.digest(key+'-text'),
                    'source_hash_basis': 'synthetic', 'parent_id': key+'-parent',
                    'parent_text_sha256': u.digest(key+'-parent-text'), 'start': 0, 'end': 10,
                    'source_pointer': '/synthetic/'+key, 'representation_fingerprint': metric['fingerprint'],
                    'vector': list(vector)})
                panel['observations'].append(row)
    return panel


def missing(row, status='unavailable', *, unknown_date=True):
    row.update(source_status=status, vector=None, missing_reason='syn-missing')
    if unknown_date:
        row['date'] = None


def build(panel):
    return u.build_us_reference(panel, receipt(panel))


def get(model, country='CAN', period='p1', field='comparisons'):
    return next(r for r in model[field] if r['country_iso3'] == country and r['period'] == period)


def node_model(model, panel, rec=None):
    return subprocess.run(['node', str(HERE/'read_model.cjs')], input=json.dumps({
        'model': model, 'source': panel, 'receipt': rec or receipt(panel)}, allow_nan=False),
        text=True, capture_output=True, timeout=30)


def table(path, records, fields):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter='\t')
        writer.writeheader()
        writer.writerows(records)


def r_tables(panel, path):
    fields = ['id', 'country_iso3', 'period', 'meeting_id', 'source_status', 'capacity',
              'attribution_status', 'genre', 'language', 'source_type', 'topic_id']
    numeric = [f'v{i}' for i in range(panel['metric_space']['dimension'])]
    rows = []
    for r in panel['observations']:
        out = {k: r[k] for k in fields}
        out.update(dict(zip(numeric, r['vector'] or [None]*len(numeric))))
        rows.append(out)
    table(path/'source.tsv', rows, fields+numeric)
    table(path/'periods.tsv', panel['periods'], ['id','start','end'])
    scope = panel['scope']
    conf = {'split':'synthetic','baseline':'USA','support_mode':'common','weight_policy':u.WEIGHT_POLICY,
            'countries':','.join(scope['countries']),'genres':','.join(scope['genres']),
            **{k:scope[k] for k in ('language','source_type','topic_id')}}
    table(path/'scope.tsv', [conf], list(conf))


class USReferenceAcceptance(unittest.TestCase):
    def test_tiny_nonzero_gaps_and_large_valid_input_vectors(self):
        case={'case':'tiny','c0':[1e-180,0,0],'c1':[5e-181,0,0],
              'u0':[0,0,0],'u1':[0,0,0]}
        x=u.transition_metrics(case['c0'],case['c1'],case['u0'],case['u1'])
        self.assertTrue(math.isclose(x['gap_country_contribution'],-5e-181,rel_tol=1e-12,abs_tol=0))
        p=fixture(case);m=build(p)
        self.assertAlmostEqual(get(m)['display']['visible_squared_gap_fraction'],1)
        if shutil.which('node'):
            run=subprocess.run(['node',str(HERE/'read_model.cjs'),'--arithmetic'],
                input=json.dumps({'cases':[case]}),capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            v=json.loads(run.stdout)[0]['transition']['gap_country_contribution']
            self.assertTrue(math.isclose(v,-5e-181,rel_tol=1e-12,abs_tol=0))
        if shutil.which('Rscript'):
            script=f"source({json.dumps(str(HERE/'arithmetic.R'))}); x <- us_transition(c(1e-180,0), c(5e-181,0), c(0,0), c(0,0)); stopifnot(abs(x$gap_country_contribution / -5e-181 - 1) < 1e-12)"
            run=subprocess.run(['Rscript','--vanilla','-e',script],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
        large=fixture({'c0':[1e100,0,0],'c1':[1e100,0,0],'u0':[-1e100,0,0],'u1':[-1e100,0,0]})
        self.assertEqual(get(build(large))['distance'],2e100)

    def test_eight_frozen_golden_cases(self):
        for case in GOLDEN['cases']:
            with self.subTest(case=case['case']):
                model = build(fixture(case))
                a, b = get(model,period='p0'), get(model)
                t = next(x['metrics'] for x in model['transitions'] if x['country_iso3']=='CAN')
                actual = {'relative_t0':a['relative_vector'],'relative_t1':b['relative_vector'],
                          'distance_t0':a['distance'],'distance_t1':b['distance'],
                          'projected_xy_t0':a['display']['relative_xy'],'projected_xy_t1':b['display']['relative_xy'], **t}
                for key, expected in case['expected'].items():
                    if isinstance(expected,list):
                        for x,y in zip(actual[key],expected): self.assertAlmostEqual(x,y,places=10)
                    elif expected is None: self.assertIsNone(actual[key])
                    else: self.assertAlmostEqual(actual[key],expected,places=10)

    def test_250_seeded_algebra_and_basis_invariance_cases(self):
        rng = random.Random(20261015)
        for _ in range(250):
            c0,c1,u0,u1=[[rng.uniform(-10,10) for j in range(3)] for i in range(4)]
            result=u.transition_metrics(c0,c1,u0,u1)
            self.assertAlmostEqual(result['gap_country_contribution']+result['gap_us_contribution'],result['gap_change'],places=10)
            # A shared signed coordinate permutation is an orthogonal basis change.
            rotate=lambda x:[-x[2],x[0],-x[1]]
            altered=u.transition_metrics(*map(rotate,(c0,c1,u0,u1)))
            self.assertAlmostEqual(result['relative_displacement'],altered['relative_displacement'],places=10)
            self.assertAlmostEqual(result['gap_change'],altered['gap_change'],places=10)
            shift=[rng.uniform(-5,5) for j in range(3)]
            shifted=[list(map(sum,zip(v,shift))) for v in (c0,c1,u0,u1)]
            self.assertAlmostEqual(result['gap_change'],u.transition_metrics(*shifted)['gap_change'],places=10)

    def test_structured_baseline_and_capacity_exclusions(self):
        for capacity in ('collective','un_staff','unknown'):
            panel=fixture()
            for r in panel['observations']:
                if r['country_iso3']=='USA': r['capacity']=capacity
            model=build(panel)
            self.assertTrue(all(x['distance'] is None and x['reason']=='baseline_missing' for x in model['comparisons']))
        panel=fixture()
        panel['scope']['baseline_iso3']='us'
        with self.assertRaises(u.ContractError): build(panel)

    def test_source_text_is_never_an_attribution_channel(self):
        for field in ('text','speech_text','country_name','html','publication_eligible'):
            panel=fixture(); panel['observations'][0][field]='The United States supports this'
            with self.subTest(field=field), self.assertRaises(u.ContractError): build(panel)
        panel=fixture();panel['observations'][0]['country_iso3']='us'
        with self.assertRaises(u.ContractError): build(panel)

    def test_unverified_attribution_withholds_usa(self):
        panel=fixture()
        for r in panel['observations']:
            if r['country_iso3']=='USA':r['attribution_status']='unverified'
        model=build(panel)
        self.assertEqual(get(model,'USA','p0','profiles')['reason'],'attribution_unverified')
        self.assertIsNone(get(model)['distance'])

    def test_one_baseline_per_period_and_display_filter_invariance(self):
        panel=fixture();model=build(panel);saved=copy.deepcopy(model)
        rows=u.select_comparisons(model,['CAN']);rows[0]['distance']=999
        self.assertEqual(model,saved)
        for p in panel['periods']:
            self.assertEqual(len({r['us_profile_sha256'] for r in model['comparisons'] if r['period']==p['id']}),1)
        with self.assertRaises(u.ContractError):u.select_comparisons(model,['GBR'])

    def test_pairwise_and_fixed_baseline_require_separate_future_contract(self):
        for key,value in [('support_mode','pairwise'),('baseline_mode','initial_period'),('weight_policy','equal_tokens')]:
            panel=fixture();panel['scope'][key]=value
            with self.subTest(key=key),self.assertRaises(u.ContractError):build(panel)

    def test_missing_baseline_not_carried_or_zero_filled(self):
        panel=fixture(periods=3)
        for r in panel['observations']:
            if r['country_iso3']=='USA' and r['period']=='p1':missing(r)
        model=build(panel)
        self.assertEqual(get(model)['reason'],'baseline_missing')
        self.assertIsNone(get(model,'USA')['distance'])
        self.assertTrue(all(t['metrics'] is None for t in model['transitions']))
        self.assertTrue(any(e['date'] is None for e in model['evidence']))
        self.assertEqual(len(model['periods']),3)
        self.assertEqual([(t['before'],t['after']) for t in model['transitions'][:2]],[('p0','p1'),('p1','p2')])

    def test_country_missing_zero_and_source_states_stay_distinct(self):
        panel=fixture(countries=('USA','CAN','FRA','GBR'))
        panel['observations']=[r for r in panel['observations'] if r['country_iso3']!='GBR']
        missing(next(r for r in panel['observations'] if r['country_iso3']=='CAN' and r['period']=='p1'),'unverified')
        missing(next(r for r in panel['observations'] if r['country_iso3']=='FRA' and r['period']=='p1'),'failed')
        model=build(panel)
        self.assertEqual(get(model,'GBR','p1','profiles')['state'],'empty')
        self.assertEqual(get(model,'CAN','p1','profiles')['reason'],'source_unverified')
        self.assertEqual(get(model,'FRA','p1','profiles')['state'],'failed')
        self.assertEqual(get(model,'USA')['distance'],0)
        self.assertIsNone(get(model,'USA')['display']['visible_squared_gap_fraction'])

    def test_required_common_support_is_not_silently_renormalized(self):
        panel=fixture(genres=('debate','committee'))
        panel['observations']=[r for r in panel['observations'] if not(r['country_iso3']=='CAN' and r['genre']=='committee')]
        model=build(panel)
        self.assertEqual(get(model)['reason'],'scope_incompatible')
        self.assertIsNone(get(model)['distance'])
        self.assertEqual(get(model,'FRA')['state'],'ready')

    def test_equal_meetings_then_genres_and_original_people_preserved(self):
        panel=fixture(genres=('debate','committee'))
        r=next(r for r in panel['observations'] if r['country_iso3']=='CAN' and r['period']=='p0' and r['genre']=='debate')
        r['vector']=[0,0,0]
        other=copy.deepcopy(r);other.update(id=r['id']+'-other',parent_id=r['parent_id']+'-other',
          parent_text_sha256=u.digest('other-parent'),text_sha256=u.digest('other-text'),source_pointer=r['source_pointer']+'-other',vector=[2,0,0],actor_id='syn-other-person')
        panel['observations'].append(other)
        extra=copy.deepcopy(r);extra.update(id=r['id']+'-meeting2',meeting_id=r['meeting_id']+'-2',
          source_sha256=u.digest('meeting2'),parent_id=r['parent_id']+'-2',parent_text_sha256=u.digest('parent2'),
          text_sha256=u.digest('text2'),source_pointer=r['source_pointer']+'-2',vector=[5,0,0])
        panel['observations'].append(extra)
        committee=next(r for r in panel['observations'] if r['country_iso3']=='CAN' and r['period']=='p0' and r['genre']=='committee')
        committee['vector']=[10,0,0]
        result=build(panel);profile=get(result,'CAN','p0','profiles')
        self.assertAlmostEqual(profile['vector'][0],6.5) # ((0+2)/2+5)/2 then equal genre with 10.
        self.assertEqual(sorted(c['weight'] for c in profile['contributions']),[.125,.125,.25,.5])
        self.assertIn('syn-other-person',{e['actor_id'] for e in result['evidence']})

    def test_duplicates_overlaps_and_parent_conflicts_rejected(self):
        for mutation in ('duplicate','overlap','fragment','parent_hash','meeting_hash'):
            panel=fixture();row=copy.deepcopy(panel['observations'][0]);row['id']+='-copy'
            if mutation=='overlap':row.update(start=5,end=15)
            elif mutation=='fragment':row.update(start=10,end=20)
            elif mutation=='parent_hash':row.update(start=10,end=20,parent_text_sha256='f'*64)
            elif mutation=='meeting_hash':row.update(source_sha256='f'*64)
            panel['observations'].append(row)
            with self.subTest(mutation=mutation),self.assertRaises(u.ContractError):build(panel)

    def test_external_receipt_is_required_and_not_an_authentication_claim(self):
        panel=fixture();rec=receipt(panel);panel['observations'][0]['vector'][0]+=1
        with self.assertRaises(u.ContractError):u.build_us_reference(panel,rec)
        rec=receipt(panel);rec['kind']='authenticated'
        with self.assertRaises(u.ContractError):u.build_us_reference(panel,rec)

    def test_missing_dates_allowed_only_for_missing_sources(self):
        panel=fixture();panel['observations'][0]['date']=None
        with self.assertRaises(u.ContractError):build(panel)
        missing(panel['observations'][0]);self.assertIsNone(next(e for e in build(panel)['evidence'] if e['id']==panel['observations'][0]['id'])['date'])

    def test_malformed_periods_and_reserved_dates_rejected(self):
        for mutation in ('reverse','overlap','invalid','duplicate'):
            panel=fixture()
            if mutation=='reverse':panel['periods'].reverse()
            elif mutation=='overlap':panel['periods'][1]['start']='2000-12-31'
            elif mutation=='invalid':panel['periods'][0]['start']='2000-02-30'
            else:panel['periods'][1]['id']='p0'
            with self.subTest(mutation=mutation),self.assertRaises(u.ContractError):build(panel)
        panel=fixture();panel['periods'][0].update(start='2026-10-05',end='2026-10-06')
        panel['periods'][1].update(start='2027-01-01',end='2027-12-31')
        for row in panel['observations']:row['date']='2026-10-05' if row['period']=='p0' else '2027-01-01'
        with self.assertRaises(u.ContractError):build(panel)

    def test_frozen_representation_and_dimension_guards(self):
        for mutation in ('vocabulary','fingerprint','boolean','nan','infinity','dimension'):
            panel=fixture()
            if mutation=='vocabulary':panel['metric_space']['feature_order'].reverse()
            elif mutation=='fingerprint':panel['observations'][0]['representation_fingerprint']='f'*64
            elif mutation=='boolean':panel['observations'][0]['vector'][0]=True
            elif mutation=='nan':panel['observations'][0]['vector'][0]=float('nan')
            elif mutation=='infinity':panel['observations'][0]['vector'][0]=float('inf')
            else:panel['observations'][0]['vector'].pop()
            with self.subTest(mutation=mutation),self.assertRaises(u.ContractError):build(panel)

    def test_display_failure_does_not_erase_full_space_metric(self):
        for change in ('missing','nonlinear','scaled','wrong_basis'):
            panel=fixture();expected=get(build(panel))['distance']
            if change=='missing':panel['display_space']=None
            elif change=='nonlinear':panel['display_space']['method']='UMAP'
            elif change=='scaled':panel['display_space']['basis'][0][0]=2
            else:panel['display_space']['metric_fingerprint']='f'*64
            model=build(panel)
            self.assertEqual(get(model)['distance'],expected)
            self.assertEqual(get(model)['display']['state'],'withheld')
            self.assertIsNone(get(model)['display']['relative_xy'])

    def test_basis_and_display_center_changes_do_not_change_profile_hashes(self):
        panel=fixture();a=build(panel)
        panel['display_space']['basis']=[[0,-1],[1,0],[0,0]];panel['display_space']['center']=[10,-20,7]
        b=build(panel)
        self.assertEqual([p['sha256'] for p in a['profiles']],[p['sha256'] for p in b['profiles']])
        self.assertEqual([c['distance'] for c in a['comparisons']],[c['distance'] for c in b['comparisons']])
        self.assertEqual(a['identity']['comparison_set_id'],b['identity']['comparison_set_id'])
        self.assertEqual(a['identity']['metric_input_sha256'],b['identity']['metric_input_sha256'])

    def test_no_publication_real_data_or_uncertainty_authority(self):
        for split in ('development','holdout','production'):
            panel=fixture();panel['split']=split
            with self.assertRaises(u.ContractError):build(panel)
        model=build(fixture());self.assertEqual(model['permissions'],u.PERMISSIONS)
        self.assertEqual(model['uncertainty'],{'state':'withheld','reason':'uncertainty_unavailable','interval':None})
        self.assertEqual(model['sensitivity']['attempts'],[])

    def test_roundtrip_no_mutation_and_replay_tamper_rejection(self):
        panel=fixture();before=copy.deepcopy(panel);model=build(panel)
        self.assertEqual(panel,before)
        self.assertTrue(u.validate_result(json.loads(json.dumps(model)),panel,receipt(panel)))
        for field in ('distance','profile','authority','evidence'):
            altered=copy.deepcopy(model)
            if field=='distance':altered['comparisons'][2]['distance']=99
            elif field=='profile':altered['profiles'][0]['contributions'][0]['weight']=.5
            elif field=='authority':altered['permissions']['publication_eligible']=True
            else:altered['evidence'][0]['actor_id']='syn-wrong'
            altered['sha256']=u.digest({k:v for k,v in altered.items() if k!='sha256'})
            with self.subTest(field=field),self.assertRaises(u.ContractError):u.validate_result(altered,panel,receipt(panel))

    def test_observation_order_is_not_weight_or_profile_identity(self):
        panel=fixture();a=build(panel);panel['observations'].reverse();b=build(panel)
        self.assertEqual(a['profiles'],b['profiles'])
        self.assertEqual(a['comparisons'],b['comparisons'])


class SchemaAcceptance(unittest.TestCase):
    def test_closed_schema_refuses_raw_text_and_permission_escalation(self):
        from .schema_contract import validate, SchemaError
        p=fixture();model=build(p)
        self.assertTrue(validate(p,source=True));self.assertTrue(validate(model))
        for field in ('text','html','release_receipt'):
            q=copy.deepcopy(p);q['observations'][0][field]='not-permitted'
            with self.assertRaises(SchemaError):validate(q,source=True)
        m=copy.deepcopy(model);m['permissions']['publication_eligible']=True
        with self.assertRaises(SchemaError):validate(m)
        m=copy.deepcopy(model);m['permissions']['publication_eligible']=0
        with self.assertRaises(SchemaError):validate(m)
        m=copy.deepcopy(model);m['comparisons'][0]['state']='withheld'
        with self.assertRaises(SchemaError):validate(m)

    def test_standard_jsonschema_cross_check(self):
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ModuleNotFoundError:self.skipTest('Optional independent JSON Schema implementation unavailable')
        from .schema_contract import contract
        schema=contract();Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema,format_checker=FormatChecker())
        for case in GOLDEN['cases']:validator.validate(build(fixture(case)))
        p=fixture();missing(p['observations'][0]);validator.validate(build(p))


@unittest.skipUnless(shutil.which('node'), 'Native Node runtime unavailable')
class NodeParity(unittest.TestCase):
    def test_node_independently_rejects_invalid_source_lineage(self):
        script="const v=require(process.argv[1]);let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>{const x=JSON.parse(s);try{v.validateSyntheticSource(x.source,x.receipt);process.exitCode=0;}catch{process.exitCode=1;}});"
        cases=[]
        for field in ('actor_id','review_receipt','parent_id','source_pointer','source_sha256'):
            p=fixture();p['observations'][0][field]=None;cases.append(p)
        p=fixture();p['observations'][0]['country_iso3']='GBR';cases.append(p)
        p=fixture();missing(p['observations'][0]);p['observations'][0]['start']=None;cases.append(p)
        p=fixture();p['metric_space']['feature_order'].append('syn-extra')
        p['metric_space']['fingerprint']=u.digest({k:v for k,v in p['metric_space'].items() if k!='fingerprint'})
        for row in p['observations']:row['representation_fingerprint']=p['metric_space']['fingerprint']
        p['display_space']['metric_fingerprint']=p['metric_space']['fingerprint'];cases.append(p)
        for p in cases:
            with self.assertRaises(u.ContractError):build(p)
            run=subprocess.run(['node','-e',script,str(HERE/'read_model.cjs')],
                input=json.dumps({'source':p,'receipt':receipt(p)}),capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,1,run.stderr)

    def test_node_source_offsets_are_exact_not_floating_tolerances(self):
        p=fixture();p['observations'][0]['start']=10**12;p['observations'][0]['end']=10**12+10
        m=build(p)
        row=next(r for r in m['evidence'] if r['id']==p['observations'][0]['id'])
        row['end']+=1
        m['sha256']=u.digest({k:v for k,v in m.items() if k!='sha256'})
        self.assertNotEqual(node_model(m,p).returncode,0)

    def test_golden_and_100_seeded_independent_node_arithmetic(self):
        cases=copy.deepcopy(GOLDEN['cases']);rng=random.Random(314159)
        for i in range(100):cases.append({'case':f'random-{i}',**{k:[rng.uniform(-5,5) for _ in range(3)] for k in ('c0','c1','u0','u1')}})
        run=subprocess.run(['node',str(HERE/'read_model.cjs'),'--arithmetic'],input=json.dumps({'cases':cases}),text=True,capture_output=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr)
        actual=json.loads(run.stdout)
        for case,out in zip(cases,actual):
            expected=u.transition_metrics(*(case[k] for k in ('c0','c1','u0','u1')))
            for k,v in expected.items():
                if isinstance(v,(int,float)):self.assertAlmostEqual(v,out['transition'][k],places=10)
                elif isinstance(v,list):
                    for a,b in zip(v,out['transition'][k]):self.assertAlmostEqual(a,b,places=10)
                else:self.assertEqual(v,out['transition'][k])

    def test_independent_node_complete_source_bound_replay(self):
        for case in GOLDEN['cases']:
            panel=fixture(case);run=node_model(build(panel),panel)
            with self.subTest(case=case['case']):self.assertEqual(run.returncode,0,run.stderr)
        panel=fixture(periods=3,genres=('debate','committee'))
        missing(panel['observations'][2]);panel['observations'][-1]['capacity']='collective'
        run=node_model(build(panel),panel);self.assertEqual(run.returncode,0,run.stderr)

    def test_node_rejects_stale_metrics_authority_and_source_pointers(self):
        panel=fixture();original=build(panel)
        for field in ('metrics','authority','pointer','edges','baseline'):
            altered=copy.deepcopy(original)
            if field=='metrics':altered['comparisons'][-1]['distance']=42
            elif field=='authority':altered['permissions']['real_data_eligible']=True
            elif field=='pointer':altered['evidence'][0]['source_pointer']='javascript:alert(1)'
            elif field=='edges':altered['transitions'][0]['after']='p99'
            else:altered['comparisons'][-1]['us_profile_sha256']='f'*64
            altered['sha256']=u.digest({k:v for k,v in altered.items() if k!='sha256'})
            with self.subTest(field=field):self.assertNotEqual(node_model(altered,panel).returncode,0)

    def test_node_import_failure_clears_model(self):
        script="const v=require(process.argv[1]);const r=v.importReadModel({}, {}, {});if(r.state!=='failed'||r.model!==null)process.exit(1);"
        run=subprocess.run(['node','-e',script,str(HERE/'read_model.cjs')],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)


@unittest.skipUnless(shutil.which('Rscript'), 'Native Rscript unavailable: R parity is NOT accepted')
class RParity(unittest.TestCase):
    def test_native_r_ids_weights_states_edges_and_metrics(self):
        panels=[fixture(c) for c in GOLDEN['cases']]
        panel=fixture(periods=3,genres=('debate','committee'));missing(panel['observations'][2]);panel['observations'][-1]['attribution_status']='unverified';panels.append(panel)
        for panel in panels:
            model=build(panel)
            with tempfile.TemporaryDirectory(prefix='usref-synthetic-') as directory:
                path=Path(directory);r_tables(panel,path)
                run=subprocess.run(['Rscript','--vanilla',str(HERE/'arithmetic.R'),str(path)],capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stderr)
                def read(name):
                    with (path/name).open() as f:return list(csv.DictReader(f,delimiter='\t'))
                rp=read('r_profiles.tsv');self.assertEqual(len(rp),len(model['profiles']))
                for a,b in zip(rp,model['profiles']):
                    for key in ('id','country_iso3','period','state','reason'):self.assertEqual(a[key],b[key] or '')
                expected_weights={(p['id'],c['observation_id']):c['weight'] for p in model['profiles'] for c in p['contributions']}
                weights=read('r_weights.tsv');self.assertEqual(len(weights),len(expected_weights))
                for row in weights:self.assertAlmostEqual(float(row['weight']),expected_weights[(row['profile_id'],row['observation_id'])],places=10)
                for a,b in zip(read('r_comparisons.tsv'),model['comparisons']):
                    for key in ('id','state','reason'):self.assertEqual(a[key],b[key] or '')
                    if b['distance'] is None:self.assertEqual(a['distance'],'')
                    else:self.assertAlmostEqual(float(a['distance']),b['distance'],places=10)
                actual=read('r_transitions.tsv');self.assertEqual(len(actual),len(model['transitions']))
                for a,b in zip(actual,model['transitions']):
                    for key in ('country_iso3','before','after','state','reason'):self.assertEqual(a[key],b[key] or '')
                    if b['metrics'] is not None:
                        for key in ('gap_change','country_displacement','us_displacement','relative_displacement',
                           'squared_gap_country_contribution','squared_gap_us_contribution','gap_country_contribution','gap_us_contribution'):
                            if b['metrics'][key] is None:self.assertEqual(a[key],'')
                            else:self.assertAlmostEqual(float(a[key]),b['metrics'][key],places=10)


class W4NativeBinding(unittest.TestCase):
    def test_real_upstream_validator_and_weighting_on_new_synthetic_panel(self):
        try:
            from research.longitudinal import framework as w4
        except ModuleNotFoundError:
            self.skipTest('Full upstream W4 checkout unavailable; native integration is not accepted')
        p=fixture(genres=('debate','committee'))
        raw={'schema':w4.SCHEMA,'split':'synthetic','periods':copy.deepcopy(p['periods']),
             'feature_space':{'id':p['metric_space']['id'],'version':'1','fingerprint':p['metric_space']['upstream_fingerprint'],
                              'dimension':3,'fit_policy':'transformed_reference'},
             'map_space':{'method':'syn-linear','dimension':2},'observations':[]}
        annotations={}
        ann_keys=['country_iso3','capacity','attribution_status','review_receipt','language','source_type','topic_id','source_pointer']
        for source in p['observations']:
            row=copy.deepcopy(source)
            row.update(actor_kind='synthetic',representation_id=raw['feature_space']['id'],representation_version='1',
              representation_fingerprint=raw['feature_space']['fingerprint'],map=source['vector'][:2],map_fit_id='syn-fixed',cluster=None)
            raw['observations'].append(row)
            annotations[source['id']]={k:source[k] for k in ann_keys}
        plan={k:copy.deepcopy(p[k]) for k in ('identity','metric_space','display_space','scope')}
        plan['identity']['producer_panel_sha256']=w4.digest(raw)
        rec={'kind':'synthetic_consistency_only','panel_sha256':w4.digest(raw),'annotations_sha256':u.digest(annotations),'plan_sha256':u.digest(plan)}
        source,check=u.adapt_w4(raw,annotations,plan,rec)
        result=u.build_us_reference(source,check)
        grouped=[{**r,'actor_id':annotations[r['id']]['country_iso3']} for r in raw['observations']]
        for period in p['periods']:
            native=w4._actor_map(grouped,period['id'])
            for country in p['scope']['countries']:
                self.assertTrue(all(abs(a-b)<1e-10 for a,b in zip(native[country],get(result,country,period['id'],'profiles')['vector'])))
        original=copy.deepcopy(raw);bad=copy.deepcopy(raw);bad['observations'][0]['representation_fingerprint']='f'*64
        with self.assertRaises(ValueError):u.adapt_w4(bad,annotations,plan,rec)
        self.assertEqual(raw,original)


if __name__=='__main__':unittest.main()
