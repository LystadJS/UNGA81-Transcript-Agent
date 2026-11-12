"""Invented fixtures only: validate contracts, not diplomatic model accuracy."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from un_transcript.models.contracts import LABELS, STATUSES, check_labels, check_registration, digest
from un_transcript.models.contracts import verify_artifacts
from un_transcript.attribution import infer_capacity
from un_transcript.models.runtime import analyze_segments, predict_pair, source_windows
from un_transcript.models.evaluation import evaluate
from un_transcript.models.__main__ import prepare_pilot

ROOT=Path(__file__).resolve().parents[1]


def fixtures():
    catalog={'version':'fixture','issues':[{'id':'ceasefire','label':'Ceasefire',
              'proposition':'Support a ceasefire','patterns':['ceasefire'],'policy_area':'Security','classification_enabled':True}]}
    sources=[]
    for i in range(7):
        text='Fictional source statement number '+str(i)
        sources.append({'source_id':'source'+str(i),'source_hash':digest(('raw'+str(i)).encode()),
                        'meeting_id':'meeting'+str(i),'segment_id':'segment'+str(i),'text_sha256':digest(text.encode()),
                        'date':'2026-11-0'+str(min(i+1,3)),
                        'split':'train' if i==0 else 'calibration' if i==1 else 'test'})
    registration={'schema':'un.stance-registration.v1','registered_at':'2026-11-04T00:00:00Z',
                  'sources':sources,'required_bodies':['GA'],'catalog_sha256':digest(catalog)}
    rows=[]
    for i,pin in enumerate(sources[2:]):
        text='Fictional source statement number '+str(i+2)
        rows.append({**pin,'pair_id':'pair'+str(i),'text':text,'start':0,'end':len(text),
                     'issue_id':'ceasefire','proposition':'Support a ceasefire','body':'GA','policy_area':'Security',
                     'label':LABELS[i],'status':'clear','owner_confirmed':True,'national_attribution_valid':True})
    labels={'owner_confirmed':True,'reviewer_id':'synthetic-test-only','reviewed_at':'2026-11-05T00:00:00Z',
            'sample_role':'complete_source_acceptance_benchmark',
            'registration_sha256':digest(registration),'rows':rows,
            'complete_source_review':{'owner_confirmed':True,'meeting_ids':[r['meeting_id'] for r in rows],
                                      'all_issues_and_missing_candidates_reviewed':True}}
    manifest={'model_id':'synthetic-only','calibration_status':'calibrated_on_registered_source_disjoint_sample',
              'registration_sha256':digest(registration)}
    predictions={'model_manifest_sha256':digest(manifest),'labels_sha256':digest(labels),
                 'catalog_sha256':digest(catalog),
                 'predictions':[{'pair_id':r['pair_id'],'label':r['label'],'confidence':1.} for r in rows]}
    predictions['baseline_predictions']=[{'pair_id':r['pair_id'],'label':None} for r in rows]
    policy=json.loads((ROOT/'config/model-policy.json').read_text())
    policy['minimums']={k:1 for k in policy['minimums']}
    registration['policy_sha256']=digest(policy)
    registration['propositions']={'ceasefire':'Support a ceasefire'}
    attribution=infer_capacity({'text':''})
    for k in ('attribution_method_version','attribution_registry_sha256'):
        registration[k]=attribution[k];manifest[k]=attribution[k];predictions[k]=attribution[k]
    labels['registration_sha256']=digest(registration)
    manifest['registration_sha256']=digest(registration);manifest['policy_sha256']=digest(policy)
    predictions['model_manifest_sha256']=digest(manifest);predictions['labels_sha256']=digest(labels)
    return catalog,registration,labels,manifest,predictions,policy


class ModelsTests(unittest.TestCase):
    def test_no_model_never_invents_stance(self):
        catalog=fixtures()[0]
        result=analyze_segments([{'segment_id':'s','revision_id':'v','text':'We support a ceasefire.',
                                 'capacity':'national','country':'USA'}],catalog)
        self.assertEqual(result['predictions'],[])
        self.assertFalse(result['model_status']['accepted'])
        self.assertEqual(result['issue_candidates'][0]['status'],'retrieval_candidate_not_stance')

    def test_missing_model_artifact_fails_closed(self):
        result=analyze_segments([],fixtures()[0],'/nonexistent-model-fixture')
        self.assertEqual(result['model_status']['status'],'withheld_invalid_model')

    def test_catalog_exports_128_compilable_retrieval_definitions(self):
        catalog=json.loads((ROOT/'config/issues.json').read_text())
        self.assertEqual(len(catalog['issues']),128)
        analyze_segments([],catalog)

    def test_source_revision_is_part_of_candidate_identity(self):
        s={'segment_id':'same','revision_id':'v1','text':'ceasefire'}
        a=analyze_segments([s],fixtures()[0])['issue_candidates'][0]['candidate_id']
        b=analyze_segments([{**s,'revision_id':'v2'}],fixtures()[0])['issue_candidates'][0]['candidate_id']
        self.assertNotEqual(a,b)

    def test_source_windows_overlap_and_preserve_offsets(self):
        text='  '+ ' '.join('token'+str(i) for i in range(1000))
        windows=list(source_windows(text,100,20))
        self.assertGreater(len(windows),1)
        for w in windows:self.assertEqual(w['text'],text[w['start']:w['end']])
        for a,b in zip(windows,windows[1:]):self.assertLess(b['start'],a['end'])
        self.assertEqual(windows[-1]['end'],len(text))

    def test_injected_predictor_yields_label_without_download(self):
        result=predict_pair('Support a ceasefire','A fictional short sentence.',
                    lambda *a:{'probabilities':[0,0,0,1,0],'status_probabilities':[1,0,0,0,0,0,0]})
        self.assertEqual(result['label'],'support')

    def test_status_uncertainty_is_not_neutral(self):
        result=predict_pair('A proposition','Fictional text',
                    lambda *a:{'probabilities':[0,0,1,0,0],'status_probabilities':[0,0,1,0,0,0,0]})
        self.assertIsNone(result['label']);self.assertEqual(result['status'],'no_expressed_position')

    def test_conflicting_windows_abstain(self):
        answers=iter([0,4,0,4,0,4])
        def predict(*a):
            p=[0]*5;p[next(answers)]=1
            return {'probabilities':p,'status_probabilities':[1,0,0,0,0,0,0]}
        result=predict_pair('A proposition',' '.join(['fictional']*800),predict)
        self.assertIsNone(result['label']);self.assertEqual(result['status'],'mixed')

    def test_invalid_probabilities_rejected(self):
        with self.assertRaises(ValueError):
            predict_pair('A proposition','text',lambda *a:{'probabilities':[float('nan')]*5,'status_probabilities':[1]*7})

    def test_gold_requires_owner_confirmation(self):
        _,reg,gold,_,_,_=fixtures();gold['owner_confirmed']=False
        with self.assertRaises(ValueError):check_labels(gold,reg,'test')

    def test_registration_precedes_labels_and_pins_text(self):
        _,reg,gold,_,_,_=fixtures();gold['rows'][0]['text']='modified'
        gold['rows'][0]['text_sha256']=digest(b'modified')
        with self.assertRaises(ValueError):check_labels(gold,reg,'test')

    def test_source_leakage_rejected(self):
        _,reg,*_=fixtures();reg['sources'][2]['meeting_id']=reg['sources'][0]['meeting_id']
        with self.assertRaises(ValueError):check_registration(reg)

    def test_reserved_source_rejected(self):
        _,reg,*_=fixtures();reg['sources'][0]['date']='2026-10-05'
        with self.assertRaises(ValueError):check_registration(reg)

    def test_empty_labels_are_not_zero_error(self):
        _,reg,gold,_,_,_=fixtures();gold['rows']=[]
        with self.assertRaises(ValueError):check_labels(gold,reg,'test')

    def test_all_abstain_fails_recall_and_coverage(self):
        cat,reg,gold,manifest,pred,policy=fixtures()
        pred['predictions']=[]
        result=evaluate(gold,reg,pred,policy,manifest,cat)
        self.assertEqual(result['status'],'fail')
        self.assertIn('emission_coverage',result['reasons']);self.assertIn('end_to_end_recall',result['reasons'])

    def test_test_receipt_metrics_and_nonpromotion(self):
        cat,reg,gold,manifest,pred,policy=fixtures()
        result=evaluate(gold,reg,pred,policy,manifest,cat)
        self.assertEqual(result['status'],'pass');self.assertFalse(result['production_accepted'])
        self.assertEqual(result['metrics']['overall_precision'],1)
        self.assertEqual(result['uncertainty']['overall_precision'],[1,1])

    def test_duplicate_baseline_cannot_distort_comparison(self):
        cat,reg,gold,manifest,pred,policy=fixtures()
        pred['baseline_predictions'].append(dict(pred['baseline_predictions'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate baseline'):
            evaluate(gold,reg,pred,policy,manifest,cat)

    def test_unknown_baseline_pairs_and_labels_fail_closed(self):
        for change in ({'pair_id':'unregistered'}, {'label':'invented_label'}):
            with self.subTest(change=change):
                cat,reg,gold,manifest,pred,policy=fixtures()
                pred['baseline_predictions'][0].update(change)
                with self.assertRaises(ValueError):
                    evaluate(gold,reg,pred,policy,manifest,cat)

    def test_missing_baseline_remains_an_acceptance_failure(self):
        cat,reg,gold,manifest,pred,policy=fixtures()
        pred['baseline_predictions'].pop()
        result=evaluate(gold,reg,pred,policy,manifest,cat)
        self.assertEqual(result['status'],'fail')
        self.assertIn('missing_matched_baseline',result['reasons'])

    def test_boolean_confidence_is_not_a_probability(self):
        cat,reg,gold,manifest,pred,policy=fixtures()
        pred['predictions'][0]['confidence']=True
        with self.assertRaisesRegex(ValueError, 'finite probability'):
            evaluate(gold,reg,pred,policy,manifest,cat)

    def test_missing_complete_source_coverage_blocks_acceptance(self):
        cat,reg,gold,manifest,pred,policy=fixtures();gold['complete_source_review']['owner_confirmed']=False
        pred['labels_sha256']=digest(gold)
        result=evaluate(gold,reg,pred,policy,manifest,cat)
        self.assertIn('missing_complete_source_owner_review',result['reasons'])

    def test_invalid_attribution_fails_even_when_labels_match(self):
        cat,reg,gold,manifest,pred,policy=fixtures();gold['rows'][0]['national_attribution_valid']=False
        pred['labels_sha256']=digest(gold)
        self.assertIn('attribution_error',evaluate(gold,reg,pred,policy,manifest,cat)['reasons'])

    def test_prepare_generates_only_unconfirmed_drafts(self):
        segments=[{'segment_id':'s'+str(i),'revision_id':'v'+str(i),'source_hash':digest(str(i).encode()),
                   'meeting_id':'m'+str(i),'date':'2026-11-0'+str(i+1),'text':'Fictional ceasefire text','body':'GA'} for i in range(3)]
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'pilot';prepare_pilot(segments,fixtures()[0],out,fixtures()[-1])
            draft=json.loads((out/'train-draft.json').read_text())
            self.assertFalse(draft['owner_confirmed']);self.assertIsNone(draft['rows'][0]['label'])
            self.assertFalse(draft['rows'][0]['owner_confirmed'])

    def test_material_qualification_vetoes_clear_window(self):
        calls=iter([0,3,0])
        def predict(*a):
            status=[0]*7;status[next(calls)]=1
            return {'probabilities':[0,0,0,1,0],'status_probabilities':status}
        result=predict_pair('A proposition',' '.join(['fictional']*800),predict)
        self.assertIsNone(result['label']);self.assertEqual(result['status'],'conditional')
        self.assertEqual(len(result['windows']),3)

    def test_runtime_artifact_omission_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'irrelevant').write_text('x')
            with self.assertRaises(ValueError):
                verify_artifacts(tmp,{'schema':'un.stance-model.v1','labels':list(LABELS),'statuses':list(STATUSES),
                                      'artifacts':{'irrelevant':digest(b'x')}})

    def test_post_test_policy_change_is_not_accepted(self):
        cat,reg,gold,manifest,pred,policy=fixtures();policy['thresholds']['macro_f1']=0
        self.assertIn('prospective_policy_binding',evaluate(gold,reg,pred,policy,manifest,cat)['reasons'])

    def test_proposition_substitution_is_rejected(self):
        _,reg,gold,_,_,_=fixtures();gold['rows'][0]['proposition']='An easier invented question'
        with self.assertRaises(ValueError):check_labels(gold,reg,'test')

    def test_invalid_focal_offsets_are_rejected(self):
        _,reg,gold,_,_,_=fixtures();gold['rows'][0]['focal_end']=9999
        with self.assertRaises(ValueError):check_labels(gold,reg,'test')

    def test_issue_denominator_controls_individual_eligibility(self):
        cat,reg,gold,manifest,pred,policy=fixtures();policy['minimums']['assessable_per_issue']=6
        result=evaluate(gold,reg,pred,policy,manifest,cat)
        self.assertEqual(result['eligible_issue_ids'],[])
        self.assertIn('no_individually_eligible_issues',result['reasons'])


if __name__=='__main__':unittest.main()
