"""Untouched-source acceptance; missing evidence never becomes a passing rate."""
from collections import Counter, defaultdict
from .contracts import LABELS, check_labels, digest


def evaluate(labels, registration, predictions, policy, manifest, catalog):
    rows = check_labels(labels, registration, 'test')
    predicted = predictions.get('predictions', []) if isinstance(predictions, dict) else predictions
    by_id = {p['pair_id']: p for p in predicted}
    if len(by_id) != len(predicted):
        raise ValueError('Duplicate predicted pair IDs')
    if not set(by_id).issubset({r['pair_id'] for r in rows}):
        raise ValueError('Predictions contain unregistered test pairs')
    emitted = correct = reversals = attribution_errors = 0
    gold_count = sum(r['status'] == 'clear' for r in rows)
    gold_classes, output_classes, true_positive = Counter(), Counter(), Counter()
    groups = defaultdict(lambda: {'gold': 0, 'emitted': 0, 'correct': 0})
    scores = []
    for row in rows:
        p = by_id.get(row['pair_id'], {})
        label = p.get('label')
        if label is not None and label not in LABELS:
            raise ValueError('Unknown predicted label')
        clear = row['status'] == 'clear'
        if clear:
            gold_classes[row['label']] += 1
        for group in ('body', 'policy_area'):
            groups[(group, row.get(group, 'unknown'))]['gold'] += int(clear)
        if label is None:
            continue
        emitted += 1; output_classes[label] += 1
        right = clear and label == row['label']
        correct += int(right)
        if right:
            true_positive[label] += 1
        if clear and row['label'] != 'neutral' and label != 'neutral':
            reversals += int((LABELS.index(label) < 2) != (LABELS.index(row['label']) < 2))
        attribution_errors += int(row.get('national_attribution_valid') is not True)
        confidence = p.get('confidence')
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError('Emitted prediction needs a finite probability confidence')
        scores.append((confidence, int(right)))
        for group in ('body', 'policy_area'):
            g = groups[(group, row.get(group, 'unknown'))]
            g['emitted'] += 1; g['correct'] += int(right)
    def ratio(a, b):
        return a/b if b else None
    class_metrics = {}
    for label in LABELS:
        precision = ratio(true_positive[label], output_classes[label])
        recall = ratio(true_positive[label], gold_classes[label])
        f1 = 2*true_positive[label]/(output_classes[label]+gold_classes[label]) if output_classes[label]+gold_classes[label] else 0.
        class_metrics[label] = {'precision': precision, 'recall': recall, 'f1': f1,
                                'emitted': output_classes[label], 'gold': gold_classes[label]}
    # Five equal-frequency confidence bins. This is descriptive calibration, not a CI.
    scores.sort()
    ece = 0.
    if scores:
        for i in range(5):
            group = scores[i*len(scores)//5:(i+1)*len(scores)//5]
            if group:
                ece += abs(sum(c for c,_ in group)/len(group)-sum(v for _,v in group)/len(group))*len(group)/len(scores)
    complete = labels.get('complete_source_review', {})
    complete_meetings = set(complete.get('meeting_ids', []))
    test_meetings = {r['meeting_id'] for r in rows}
    if not complete_meetings.issubset(test_meetings):
        raise ValueError('Complete-source review refers to meetings absent from gold')
    metrics = {'overall_precision': ratio(correct, emitted),
               'polarity_reversal': ratio(reversals, emitted),
               'end_to_end_recall': ratio(correct, gold_count),
               'emission_coverage': ratio(sum(r['status']=='clear' and by_id.get(r['pair_id'],{}).get('label') in LABELS for r in rows), gold_count),
               'macro_f1': sum(c['f1'] for c in class_metrics.values())/5,
               'ece': ece if scores else None, 'attribution_error': ratio(attribution_errors, emitted)}
    reasons = []
    if labels.get('sample_role') != 'complete_source_acceptance_benchmark':
        reasons.append('pilot_is_not_acceptance_benchmark')
    if manifest.get('calibration_status') != 'calibrated_on_registered_source_disjoint_sample':
        reasons.append('missing_independent_calibration')
    if registration.get('catalog_sha256') != digest(catalog):
        reasons.append('registration_catalog_binding')
    if manifest.get('registration_sha256') != digest(registration):
        reasons.append('training_registration_binding')
    if registration.get('policy_sha256') != digest(policy) or manifest.get('policy_sha256') != digest(policy):
        reasons.append('prospective_policy_binding')
    for key in ('attribution_method_version','attribution_registry_sha256'):
        if not registration.get(key) or manifest.get(key)!=registration[key] or not isinstance(predictions,dict) or predictions.get(key)!=registration[key]:
            reasons.append('attribution_pipeline_binding:'+key)
    propositions={i['id']:i['proposition'] for i in catalog['issues']}
    if any(propositions.get(r['issue_id'])!=r['proposition'] for r in rows):
        reasons.append('canonical_proposition_binding')
    minimums, thresholds = policy['minimums'], policy['thresholds']
    lower = {'overall_precision':'overall_precision','end_to_end_recall':'end_to_end_recall',
             'emission_coverage':'emission_coverage','macro_f1':'macro_f1'}
    upper = {'polarity_reversal':'max_polarity_reversal','ece':'max_ece','attribution_error':'max_attribution_error'}
    for key, gate in lower.items():
        if metrics[key] is None or metrics[key] < thresholds[gate]: reasons.append(key)
    for key, gate in upper.items():
        if metrics[key] is None or metrics[key] > thresholds[gate]: reasons.append(key)
    for label, result in class_metrics.items():
        if result['emitted'] < minimums['emitted_per_class']: reasons.append('class_denominator:'+label)
        if result['precision'] is None or result['precision'] < thresholds['per_class_precision']: reasons.append('class_precision:'+label)
    if len(test_meetings) < minimums['test_meetings']: reasons.append('meeting_coverage')
    if complete.get('owner_confirmed') is not True or complete.get('all_issues_and_missing_candidates_reviewed') is not True:
        reasons.append('missing_complete_source_owner_review')
    if len(complete_meetings) < minimums['complete_source_meetings']: reasons.append('complete_source_coverage')
    areas = {r.get('policy_area') for r in rows if r['status']=='clear'} - {None, 'unknown'}
    if len(areas) < minimums['policy_areas']: reasons.append('policy_area_coverage')
    issue_metrics=[];eligible_issues=[]
    enabled_issues={i['id'] for i in catalog['issues'] if i.get('classification_enabled') is True}
    for issue in sorted({r['issue_id'] for r in rows}):
        subset=[r for r in rows if r['issue_id']==issue]
        g=sum(r['status']=='clear' for r in subset)
        e=sum(by_id.get(r['pair_id'],{}).get('label') in LABELS for r in subset)
        c=sum(r['status']=='clear' and by_id.get(r['pair_id'],{}).get('label')==r['label'] for r in subset)
        p=ratio(c,e)
        eligible=issue in enabled_issues and g>=minimums['assessable_per_issue'] and p is not None and p>=thresholds['overall_precision'] and c/g>=thresholds['end_to_end_recall']
        issue_metrics.append({'issue_id':issue,'gold':g,'emitted':e,'correct':c,'precision':p,'eligible':eligible})
        if eligible: eligible_issues.append(issue)
    if not eligible_issues: reasons.append('no_individually_eligible_issues')
    declared_bodies = set(registration.get('required_bodies', []))
    if not declared_bodies: reasons.append('missing_prospective_body_frame')
    for body in declared_bodies:
        if groups[('body',body)]['gold'] < minimums['assessable_per_body']: reasons.append('body_coverage:'+body)
    slices = []
    for (kind, name), group in sorted(groups.items()):
        precision = ratio(group['correct'],group['emitted'])
        slices.append({'kind':kind,'name':name,**group,'precision':precision})
        n = minimums['assessable_per_body' if kind=='body' else 'assessable_per_area']
        if kind=='policy_area' and group['gold'] < n: reasons.append('area_denominator:'+name)
        if group['gold'] >= n and (precision is None or precision < thresholds['minimum_slice_precision']):
            reasons.append('slice_precision:'+kind+':'+name)
    # Test receipts must be produced from this candidate; arbitrary unbound arrays cannot approve it.
    if not isinstance(predictions,dict) or predictions.get('model_manifest_sha256') != digest(manifest):
        reasons.append('prediction_model_binding')
    if isinstance(predictions,dict) and predictions.get('labels_sha256') != digest(labels):
        reasons.append('prediction_source_binding')
    if not isinstance(predictions,dict) or predictions.get('catalog_sha256') != digest(catalog):
        reasons.append('prediction_catalog_binding')
    baseline_rows = predictions.get('baseline_predictions',[]) if isinstance(predictions,dict) else []
    baseline_by_id={p['pair_id']:p for p in baseline_rows}
    baseline_metrics=None
    if len(baseline_by_id)!=len(rows) or set(baseline_by_id)!={r['pair_id'] for r in rows}:
        reasons.append('missing_matched_baseline')
    else:
        baseline_emitted=Counter(p['label'] for p in baseline_rows if p.get('label') in LABELS)
        baseline_tp=Counter(r['label'] for r in rows if r['status']=='clear' and baseline_by_id[r['pair_id']].get('label')==r['label'])
        baseline_f1=sum(2*baseline_tp[c]/(baseline_emitted[c]+gold_classes[c]) if baseline_emitted[c]+gold_classes[c] else 0 for c in LABELS)/5
        baseline_metrics={'macro_f1':baseline_f1,'emitted':sum(baseline_emitted.values()),
                          'exact_precision':ratio(sum(baseline_tp.values()),sum(baseline_emitted.values()))}
        if metrics['macro_f1']<baseline_f1: reasons.append('below_matched_baseline_macro_f1')
    # Meeting-cluster bootstrap preserves within-meeting dependence. No population
    # weighting is inferred for purposively sampled/enriched benchmark rows.
    import random
    meeting_rows=defaultdict(list)
    for r in rows: meeting_rows[r['meeting_id']].append(r)
    rng=random.Random(20261111); precision_draws=[]; recall_draws=[]
    keys=sorted(meeting_rows)
    for _ in range(500):
        sample=[r for key in rng.choices(keys,k=len(keys)) for r in meeting_rows[key]]
        drawn_emitted=sum(by_id.get(r['pair_id'],{}).get('label') in LABELS for r in sample)
        drawn_gold=sum(r['status']=='clear' for r in sample)
        drawn_correct=sum(r['status']=='clear' and by_id.get(r['pair_id'],{}).get('label')==r['label'] for r in sample)
        if drawn_emitted: precision_draws.append(drawn_correct/drawn_emitted)
        if drawn_gold: recall_draws.append(drawn_correct/drawn_gold)
    def interval(draws):
        draws=sorted(draws)
        return [draws[int(.025*(len(draws)-1))],draws[int(.975*(len(draws)-1))]] if draws else None
    return {'schema':'un.stance-evaluation.v1','status':'pass' if not reasons else 'fail',
            'production_accepted':False,'reasons':reasons,'metrics':metrics,'class_metrics':class_metrics,
            'baseline':baseline_metrics,
            'issue_metrics':issue_metrics,
            'slices':slices,'denominators':{'gold':gold_count,'emitted':emitted,'test_meetings':len(test_meetings),
                                          'complete_source_meetings':len(complete_meetings)},
            'model_manifest_sha256':digest(manifest),'labels_sha256':digest(labels),
            'registration_sha256':digest(registration),'policy_sha256':digest(policy),
            'catalog_sha256':digest(catalog),'eligible_issue_ids':eligible_issues,
            'uncertainty':{'method':'500 deterministic meeting-cluster bootstrap draws, percentile 95%',
                           'overall_precision':interval(precision_draws),'end_to_end_recall':interval(recall_draws)},
            'limitation':'Benchmark-frame estimates; enriched sampling is not population prevalence.'}
