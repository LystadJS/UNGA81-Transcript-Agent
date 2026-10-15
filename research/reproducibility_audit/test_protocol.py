"""Synthetic regression controls. No transcript access, downloads or model fitting."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import protocol
import replay
import security

H='a'*64
B='b'*64
C='c'*64
D='d'*64
E='e'*64


def specimen():
    return {
      'schema':'un.parallel-analysis.v1','contract_version':'1.0.0',
      'producer':{'workstream_id':'W2','adapter_version':'0.1.0','code_sha256':H,'runtime':'python3',
                  'generated_at':'2026-10-08T00:00:00Z','fixture_kind':'synthetic'},
      'upstream':{'source_schema':'synthetic.v1','source_engine':'synthetic-offline',
                  'source_hash_basis':'synthetic','source_sha256':B,'frame_sha256':None,
                  'corpus_sha256':None,'selection_sha256':C,'review_sha256':None,'missing_reason':None},
      'cohort':{'split':'synthetic','population':'synthetic_passages','unit':'synthetic',
                'selection_policy':'all synthetic rows','weighting':'none','source_group_unit':'synthetic',
                'duplicate_policy':'retain_and_audit','total_in_frame':2,'eligible':2},
      'observations':[
          {'id':'syn-1','text_sha256':D,'parent_id':None,'parent_text_sha256':None,
           'meeting_id':'syn-meeting-1','speech_id':None,'source_family_id':'synthetic-s1',
           'date':'2026-10-01','country':None,'source_url':None,'json_pointer':None,
           'start':0,'end':4,'unit':'synthetic','review_status':'not_applicable',
           'exclusion_reasons':[],'source_status':'available','missing_reason':None},
          {'id':'syn-2','text_sha256':E,'parent_id':None,'parent_text_sha256':None,
           'meeting_id':'syn-meeting-2','speech_id':None,'source_family_id':'synthetic-s2',
           'date':'2026-10-02','country':None,'source_url':None,'json_pointer':None,
           'start':None,'end':None,'unit':'synthetic','review_status':'not_applicable',
           'exclusion_reasons':[],'source_status':'available','missing_reason':None}],
      'models':[{'model_id':'syn-model','method_family':'partition','method':'pam',
                 'representation_id':'synthetic-vector-v1','representation_version':'v1',
                 'fit_version':'v1','fit_split':'synthetic','parameters_sha256':H,
                 'training_selection_sha256':C,'diagnostic_basis':'synthetic test'}],
      'results':[{'model_id':'syn-model','observation_id':'syn-1','status':'assigned','cluster':1,
                  'membership_kind':'none','memberships':None,'membership_strength':None,
                  'representation_basis_id':'synthetic-vector-v1','reason':None},
                 {'model_id':'syn-model','observation_id':'syn-2','status':'unassigned','cluster':0,
                  'membership_kind':'none','memberships':None,'membership_strength':None,
                  'representation_basis_id':'synthetic-vector-v1','reason':'synthetic abstention'}],
      'coverage':{'inventory_meetings':2,'observations_total':2,'eligible':2,'excluded':0,
                  'unavailable_sources':0,'models':[{'model_id':'syn-model','eligible':2,'assigned':1,
                  'unassigned':1,'not_fitted':0,'excluded':0,'attempted_fits':1,
                  'successful_fits':1,'failed_fits':0}],'failure_ledger':[]},
      'evidence':[],
      'diagnostics':[{'model_id':'syn-model','name':'synthetic_assignment_coverage',
                      'value':1,'denominator':2,'unit':'observations','status':'descriptive','reason':None}],
      'limitations':[{'code':'synthetic_only','scope':'all','description':'No empirical claims.'}],
      'publication_eligible':False,'evaluation_role':'engineering_only'
    }


def synthetic_schema():
    """Small test-only subset; actual contract checked separately by pinned load_contract."""
    obreq=list(specimen()['observations'][0]);mreq=list(specimen()['models'][0]);
    rr=list(specimen()['results'][0]);cm=list(specimen()['coverage']['models'][0]);
    def struct(fields,items=None):
        return {'type':'object','required':list(fields),'additionalProperties':False,
                'properties':{k: {'type':'array'} if k in ('exclusion_reasons',) else {} for k in fields}}
    props={k:{} for k in specimen()}
    props['schema']={'const':'un.parallel-analysis.v1'}
    props['publication_eligible']={'const':False}
    props['evaluation_role']={'const':'engineering_only'}
    props['observations']={'type':'array','items':struct(obreq)}
    props['models']={'type':'array','items':struct(mreq)}
    props['results']={'type':'array','items':struct(rr)}
    props['coverage']={'type':'object','required':list(specimen()['coverage']),
         'additionalProperties':False,'properties':{
             **{k:{} for k in specimen()['coverage']},
             'models':{'type':'array','items':struct(cm)}}}
    return {'type':'object','required':list(props),'additionalProperties':False,'properties':props}


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.d=specimen()
        self.schema=synthetic_schema()

    def assertRejected(self, cause):
        results=protocol.validate_envelope(self.d,self.schema)
        self.assertTrue(results, cause)

    def test_positive(self):
        self.assertEqual(protocol.validate_envelope(self.d,self.schema),[])

    def test_corrupt_hash_syntax_against_authoritative_rule(self):
        self.schema['properties']['observations']['items']['properties']['text_sha256']={'type':'string','pattern':'^[a-f0-9]{64}$'}
        self.d['observations'][0]['text_sha256']='bad'
        self.assertRejected('corrupt source text SHA')

    def test_missing_identity_field(self):
        del self.d['observations'][0]['id']
        self.assertRejected('missing source ID')

    def test_duplicate_observation(self):
        self.d['observations'][1]['id']='syn-1'
        self.assertRejected('duplicate observation')

    def test_missing_parent_hash(self):
        self.d['observations'][0]['parent_id']='parent'
        self.assertRejected('missing parent hash')

    def test_half_null_span(self):
        self.d['observations'][0]['end']=None
        self.assertRejected('invalid span')

    def test_zero_length_span(self):
        self.d['observations'][0]['end']=0
        self.assertRejected('invalid span')

    def test_duplicate_model_result(self):
        self.d['results'].append(copy.deepcopy(self.d['results'][0]))
        self.assertRejected('duplicate result')

    def test_missing_result(self):
        self.d['results'].pop()
        self.assertRejected('missing eligible result')

    def test_orphan_result(self):
        self.d['results'][0]['observation_id']='unknown'
        self.assertRejected('orphan result')

    def test_incompatible_representation(self):
        self.d['results'][0]['representation_basis_id']='different'
        self.assertRejected('wrong representation')

    def test_bad_cluster_status(self):
        self.d['results'][1]['cluster']=1
        self.assertRejected('noise mislabeled')

    def test_bad_membership_normalization(self):
        x=self.d['results'][0]
        x['membership_kind']='nmf_share';x['memberships']=[.2,.2]
        self.assertRejected('partial component sum')

    def test_wrong_eligible_denominator(self):
        self.d['coverage']['eligible']=1
        self.assertRejected('eligible mismatch')

    def test_wrong_assignment_denominator(self):
        self.d['coverage']['models'][0]['assigned']=2
        self.assertRejected('assigned mismatch')

    def test_fit_denominator(self):
        self.d['coverage']['models'][0]['attempted_fits']=2
        self.assertRejected('attempt failure')

    def test_partial_fit(self):
        r=self.d['results'][1];r['status']='not_fitted';r['cluster']=None;r['reason']='synthetic timeout'
        c=self.d['coverage']['models'][0];c['unassigned']=0;c['not_fitted']=1
        self.assertEqual(protocol.validate_envelope(self.d,self.schema),[])

    def test_failed_fit_requires_failure_ledger(self):
        c=self.d['coverage']['models'][0];c['attempted_fits']=2;c['failed_fits']=1
        self.assertRejected('missing attempted-fit failures')

    def test_skipped_fit_needs_ledger(self):
        self.d['coverage']['models'][0]['skipped_fits']=1
        self.schema['properties']['coverage']['properties']['models']['items']['properties']['skipped_fits']={}
        self.assertRejected('unreported skipped fit')

    def test_unavailable_source_with_reason(self):
        o=self.d['observations'][1]
        o['source_status']='unavailable';o['missing_reason']='synthetic missing document';o['exclusion_reasons']=['unavailable']
        self.d['cohort']['eligible']=1
        c=self.d['coverage'];c['eligible']=1;c['excluded']=1;c['unavailable_sources']=1
        z=self.d['results'][1];z['status']='excluded';z['cluster']=None;z['reason']='synthetic unavailable'
        m=c['models'][0];m['eligible']=1;m['excluded']=1;m['unassigned']=0
        self.assertEqual(protocol.validate_envelope(self.d,self.schema),[])

    def test_missing_reason_unavailable(self):
        self.d['observations'][0]['source_status']='unavailable'
        self.assertRejected('no absent source reason')

    def test_unconfirmed_speech(self):
        self.d['observations'][0]['speech_id']='alleged'
        self.assertRejected('unverified speaker')

    def test_reserved_dates(self):
        self.d['observations'][0]['date']='2026-10-05'
        self.assertRejected('reserved holdout')

    def test_release_gate(self):
        self.d['publication_eligible']=True
        self.assertRejected('unauthorized public release')

    def test_invalid_diagnostic_denominator(self):
        self.d['diagnostics'][0]['status']='validated';self.d['diagnostics'][0]['denominator']=0
        self.assertRejected('zero opportunities')

    def test_unreported_exception(self):
        self.d['diagnostics'][0]['status']='withheld';self.d['diagnostics'][0]['reason']=None
        self.assertRejected('unexplained status')

    def test_no_model_and_no_eligible_is_explicit(self):
        self.d['models']=[];self.d['results']=[];self.d['coverage']['models']=[]
        self.d['diagnostics']=[]
        self.d['observations']=[];self.d['cohort']['eligible']=0
        self.d['coverage']['observations_total']=0;self.d['coverage']['eligible']=0
        self.assertEqual(protocol.validate_envelope(self.d,self.schema),[])

    def test_unknown_schema_keyword_refused(self):
        self.assertTrue(protocol.structural({'oneOf':[{'type':'string'}]},'ok'))

    def test_unknown_field_refused(self):
        self.d['extra_private_transcript']='SYNTHETIC_PRIVATE_TRANSCRIPT_SENTINEL'
        self.assertRejected('forbidden schema extra')

    def test_actual_coordinator_schema(self):
        repo=Path(__file__).resolve().parents[2]
        schema,issues=protocol.load_contract(repo)
        if schema is None:
            if (repo / protocol.CONTRACT_RELATIVE).exists():
                self.fail(str(issues))
            self.skipTest('upstream coordinator schema unavailable outside GitHub checkout')
        self.assertEqual(protocol.validate_envelope(self.d,schema),[])

    def test_schema_pin_refuses_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/protocol.CONTRACT_RELATIVE;p.parent.mkdir(parents=True)
            p.write_text('{"type":"object"}',encoding='utf-8')
            schema,issues=protocol.load_contract(Path(td))
            self.assertIsNone(schema);self.assertTrue(issues)

    def test_schema_missing_refuses_pass(self):
        self.assertTrue(protocol.validate_envelope(self.d,None))


class ComparisonTests(unittest.TestCase):
    def test_matched_identity(self):
        a=specimen();self.assertEqual(protocol.check_populations(a,copy.deepcopy(a)),[])

    def test_same_hash_but_different_population(self):
        a=specimen();b=specimen();b['observations'][0]['id']='renamed'
        self.assertTrue(protocol.check_populations(a,b))

    def test_incompatible_source_hash(self):
        a=specimen();b=specimen();b['upstream']['source_sha256']='f'*64
        self.assertTrue(protocol.check_populations(a,b))

    def test_representation_mismatch(self):
        a=specimen();b=specimen();b['models'][0]['representation_id']='other'
        self.assertTrue(protocol.check_populations(a,b))

    def test_unapproved_alignment(self):
        a=specimen();b=specimen();b['cohort']['population']='changed'
        self.assertTrue(protocol.check_populations(a,b,{'protocol_id':'x','approved':False,'protocol_sha256':H}))

    def test_changed_fit_parameters_rejected(self):
        a=specimen(); b=copy.deepcopy(a)
        b['models'][0]['parameters_sha256']='f'*64
        self.assertIn('model fit policy mismatch', protocol.check_populations(a,b))

    def test_changed_method_and_fit_version_rejected(self):
        for field,value in [('method','different'),('fit_version','v2'),
                            ('training_selection_sha256','f'*64)]:
            a=specimen(); b=copy.deepcopy(a)
            b['models'][0][field]=value
            self.assertIn('model fit policy mismatch', protocol.check_populations(a,b))

    def test_matching_missing_text_hash_rejected(self):
        a=specimen(); b=copy.deepcopy(a)
        for doc in (a,b): doc['observations'][0]['text_sha256']=None
        self.assertIn('missing eligible observation text hash',protocol.check_populations(a,b))

    def test_duplicate_source_identity_rejected_during_comparison(self):
        a=specimen(); b=copy.deepcopy(a)
        for doc in (a,b):doc['observations'].append(copy.deepcopy(doc['observations'][0]))
        self.assertIn('duplicate/missing observation identity',protocol.check_populations(a,b))

    def test_cohort_split_or_denominator_change_rejected(self):
        for field,value in [('split','development'),('eligible',1),('duplicate_policy','deduplicate')]:
            a=specimen();b=copy.deepcopy(a);b['cohort'][field]=value
            self.assertTrue(protocol.check_populations(a,b),field)

    def test_source_group_overlap(self):
        a=[{'id':'one','source_family_id':'family','text_sha256':H}]
        b=[{'id':'two','source_family_id':'family','text_sha256':B}]
        self.assertIn('evaluation leakage: source_family_id',protocol.check_isolation(a,b))

    def test_parent_overlap(self):
        a=[{'id':'one','source_family_id':'source1','text_sha256':H,'parent_id':'parent'}]
        b=[{'id':'two','source_family_id':'source2','text_sha256':B,'parent_id':'parent'}]
        self.assertIn('evaluation leakage: parent_id',protocol.check_isolation(a,b))

    def test_missing_sealed_identity_fail_closed(self):
        self.assertTrue(protocol.check_isolation([],[]))

    def test_frozen_path(self):
        self.assertTrue(protocol.changed_path_violations(['docs/parallel-work/interchange-v1.schema.json']))
        self.assertTrue(protocol.changed_path_violations(['research/reproducibility_audit/../../site/release.json']))
        self.assertEqual(protocol.changed_path_violations(['research/reproducibility_audit/test_protocol.py']),[])

    def test_qa_status_requirement(self):
        self.assertEqual(protocol.qa_summary([protocol.result_record('ci','NOT RUN','unavailable')])['engineering_acceptance'],'WITHHELD')
        with self.assertRaises(ValueError): protocol.result_record('x','PASS','')


class SecurityTests(unittest.TestCase):
    def test_synthetic_controls_all_encodings(self):
        import base64
        marker=security.SENTINELS[0]
        for data in (marker.encode(),marker.encode('utf-16-le'),base64.b64encode(marker.encode())):
            self.assertTrue(security.scan_bytes(data))

    def test_private_key(self):
        self.assertTrue(security.scan_bytes(b'-----BEGIN PRIVATE KEY-----\nSYNTHETIC\n'))

    def test_cached_vectors(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'model.npy').write_bytes(b'fake synthetic data')
            self.assertTrue(security.scan_public(Path(td)))

    def test_private_json_rows(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'data.json').write_text(json.dumps({'records':[{'id':'x','text_sha256':H,'source_url':'https://example.invalid','country':'ZZ'}]}))
            self.assertTrue(security.scan_public(Path(td)))

    def test_dangerous_json_key(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'data.json').write_text(json.dumps({'raw_passage':'synthetic placeholder'}))
            self.assertTrue(security.scan_public(Path(td)))

    def test_clean_aggregate(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'summary.json').write_text(json.dumps({'metric':'synthetic','n':3}))
            self.assertEqual(security.scan_public(Path(td)),[])

    def test_symlink_not_followed(self):
        with tempfile.TemporaryDirectory() as td:
            try:
                (Path(td)/'link').symlink_to(Path(td)/'nonexistent')
            except OSError:
                self.skipTest('symlink creation unavailable')
            self.assertTrue(security.scan_public(Path(td)))


class ReplayTests(unittest.TestCase):
    def fixture(self):
        return {'schema':'un.replay-fixture.v1','fixture_kind':'synthetic',
                'seed':271828,'observations':[1.,2.,3.,4.,5.]}

    def test_process_restart(self):
        got=replay.replay(self.fixture())
        self.assertEqual(got['status'],'PASS',got)
        self.assertEqual(got['processes'],2)
        self.assertEqual(got['restarts'],2)

    def test_corrupt_expected_hash(self):
        self.assertEqual(replay.replay(self.fixture(),expected_sha256='f'*64)['status'],'FAIL')

    def test_seed_effect(self):
        a=replay.replay(self.fixture());f=self.fixture();f['seed']+=1
        b=replay.replay(f)
        self.assertNotEqual(a['output_sha256'],b['output_sha256'])

    def test_private_input_rejected_before_worker(self):
        f=self.fixture();f['raw_transcript']='private'
        with self.assertRaises(ValueError): replay.replay(f)

    def test_wrong_fixture_kind(self):
        f=self.fixture();f['fixture_kind']='private_development'
        with self.assertRaises(ValueError): replay.replay(f)


if __name__=='__main__': unittest.main()
