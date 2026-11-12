"""Source-bound retrieval and fail-closed CPU model inference."""
import collections
import math
import re
from pathlib import Path
from .contracts import LABELS, STATUSES, digest, identity, read_json, verify_artifacts


def source_windows(text, max_tokens=350, overlap=64, tokenizer=None):
    """Overlapping windows retain original Python Unicode code-point offsets."""
    if max_tokens < 2 or not 0 <= overlap < max_tokens:
        raise ValueError('Invalid window/overlap budget')
    if tokenizer is None:
        offsets = [(m.start(), m.end()) for m in re.finditer(r'\S+', text)]
    else:
        offsets = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)['offset_mapping']
    for index in range(0, len(offsets), max_tokens - overlap):
        window = offsets[index:index + max_tokens]
        if not window:
            break
        start, end = window[0][0], window[-1][1]
        yield {'text': text[start:end], 'start': start, 'end': end,
               'text_sha256': digest(text[start:end].encode())}
        if index + max_tokens >= len(offsets):
            break


def _softmax(values):
    top = max(values)
    weights = [math.exp(float(v) - float(top)) for v in values]
    return [v / sum(weights) for v in weights]


class OnnxPredictor:
    def __init__(self, directory, manifest):
        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise RuntimeError('Install requirements-model.txt for local semantic inference') from exc
        self.tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True, use_fast=True, trust_remote_code=False)
        self.session = ort.InferenceSession(str(Path(directory) / 'model.onnx'), providers=['CPUExecutionProvider'])
        self.temperature = float(manifest.get('temperature', 1.0))
        if not math.isfinite(self.temperature) or self.temperature <= 0:
            raise ValueError('Invalid calibration temperature')

    def __call__(self, proposition, text):
        encoded = self.tokenizer(proposition, text, return_tensors='np', truncation=False)
        if encoded['input_ids'].shape[-1] > 512:
            raise ValueError('Window exceeds model budget; silent truncation is forbidden')
        feed = {i.name: encoded[i.name] for i in self.session.get_inputs()}
        stance, status = self.session.run(None, feed)
        return {'probabilities': _softmax(stance[0] / self.temperature),
                'status_probabilities': _softmax(status[0])}


def predict_pair(proposition, text, predictor, threshold=0.9, status_threshold=0.9):
    """Injectable predictor keeps unit tests offline; production always verifies artifacts."""
    tokenizer = getattr(predictor, 'tokenizer', None)
    proposition_tokens = len(tokenizer(proposition, add_special_tokens=False)['input_ids']) if tokenizer else len(proposition.split())
    budget = 512 - proposition_tokens - 3
    if budget < 128:
        return {'label': None, 'status': 'unclear', 'reason': 'proposition_exceeds_budget', 'windows': []}
    rows = []
    for window in source_windows(text, min(350, budget), 64, tokenizer):
        answer = predictor(proposition, window['text'])
        probs = answer['probabilities']; statuses = answer['status_probabilities']
        if (len(probs) != 5 or len(statuses) != len(STATUSES) or
                any(not math.isfinite(float(p)) or not 0 <= p <= 1 for p in probs + statuses) or
                abs(sum(probs)-1) > 1e-5 or abs(sum(statuses)-1) > 1e-5):
            raise ValueError('Malformed model probability output')
        status = STATUSES[max(range(len(statuses)), key=lambda i: statuses[i])]
        label = LABELS[max(range(5), key=lambda i: probs[i])]
        emitted = status == 'clear' and max(statuses) >= status_threshold and max(probs) >= threshold
        rows.append({**window, 'label': label if emitted else None, 'status': status,
                     'status_confidence': max(statuses),
                     'probabilities': probs, 'confidence': max(probs), 'emitted': emitted})
    material=[r for r in rows if r['status'] in ('conditional','mixed','unclear','unresolved_attribution') and r['status_confidence']>=status_threshold]
    if material:
        status=material[0]['status'] if len({r['status'] for r in material})==1 else 'unclear'
        return {'label':None,'status':status,'reason':'material_context_qualification','windows':rows}
    accepted = [r for r in rows if r['emitted']]
    labels = {r['label'] for r in accepted}
    if len(labels) > 1:
        return {'label': None, 'status': 'mixed', 'reason': 'window_disagreement', 'windows': rows}
    if not accepted:
        status = rows[0]['status'] if rows and len({r['status'] for r in rows}) == 1 else 'unclear'
        return {'label': None, 'status': status if status != 'clear' else 'unclear',
                'reason': 'abstained', 'windows': rows}
    probabilities = [sum(r['probabilities'][i] for r in accepted)/len(accepted) for i in range(5)]
    return {'label': accepted[0]['label'], 'status': 'clear', 'confidence': max(probabilities),
            'probabilities': probabilities, 'windows': rows}


def load_accepted_model(directory, catalog):
    manifest = read_json(Path(directory) / 'manifest.json')
    verify_artifacts(directory, manifest)
    from ..attribution import infer_capacity
    current=infer_capacity({'text':''})
    if any(manifest.get(k)!=current[k] for k in ('attribution_method_version','attribution_registry_sha256')):
        raise ValueError('Attribution method/registry differs from accepted model pipeline')
    receipt = read_json(Path(directory) / 'acceptance.json')
    if (receipt.get('status') != 'accepted' or receipt.get('owner_release_confirmed') is not True or
            receipt.get('model_manifest_sha256') != digest(manifest) or
            receipt.get('catalog_sha256') != digest(catalog)):
        raise ValueError('No owner-approved, artifact-bound model acceptance')
    return OnnxPredictor(directory, manifest), manifest, receipt


def analyze_segments(segments, catalog, model_dir=None):
    issues = catalog.get('issues', []) if isinstance(catalog, dict) else catalog
    catalog_version = catalog.get('version', 'unversioned') if isinstance(catalog, dict) else 'unversioned'
    matcher = []
    for issue in issues:
        matcher.append((issue, [re.compile(p, re.I) for p in issue.get('patterns', [])]))
    predictor = manifest = receipt = None
    model_status = {'status': 'not_evaluated_missing_labels', 'accepted': False,
                    'reason': 'No approved trained model supplied; issue mentions are not stances'}
    if model_dir:
        try:
            predictor, manifest, receipt = load_accepted_model(model_dir, catalog)
            model_status = {'status': 'accepted', 'accepted': True, 'model_id': manifest['model_id'],
                            'release_approved': True, 'acceptance_sha256': digest(receipt),
                            'attribution_method_version':manifest['attribution_method_version'],
                            'attribution_registry_sha256':manifest['attribution_registry_sha256']}
        except (ValueError, OSError, KeyError, RuntimeError) as exc:
            model_status = {'status': 'withheld_invalid_model', 'accepted': False, 'reason': str(exc)}
    predictions, evidence, candidates = [], [], []
    frequency = collections.Counter()
    for segment in segments:
        from ..attribution import infer_capacity
        segment=infer_capacity(segment)
        text = segment.get('text', '')
        if not text or segment.get('language', 'en') != 'en':
            continue
        sid = segment.get('segment_id') or identity('segment', segment.get('revision_id'), text)
        source_id = segment.get('source_id') or segment.get('revision_id')
        source_hash = segment.get('source_hash') or segment.get('artifact_sha256')
        capacity = segment.get('attribution_kind') or segment.get('capacity', 'unknown')
        ref = {'segment_id': sid, 'source_id': source_id, 'source_hash': source_hash,
               'meeting_id': segment.get('meeting_id'), 'date': segment.get('date'),
               'body': segment.get('body'), 'country': segment.get('country'),
               'capacity': capacity, 'source_url': segment.get('source_url'),
               'json_pointer': segment.get('json_pointer'), 'text_sha256': digest(text.encode())}
        ref.update({k:segment[k] for k in ('canonical_country','attribution_kind','attribution_evidence',
                                          'attribution_method_version','attribution_registry_sha256','attribution_status')})
        matched = False
        for issue, patterns in matcher:
            matches = [m for pattern in patterns for m in pattern.finditer(text)]
            if not matches:
                continue
            matched = True
            candidate_id = identity('candidate', source_id, sid, ref['text_sha256'], issue['id'], catalog_version)
            spans = sorted(set((m.start(), m.end()) for m in matches))
            evidence_id = identity('evidence', candidate_id)
            evidence.append({**ref, 'evidence_id': evidence_id, 'issue_id': issue['id'],
                             'spans': [{'start': a, 'end': b} for a, b in spans],
                             'offset_basis': 'segment_text_unicode_codepoints', 'kind': 'lexical_issue_mention'})
            candidates.append({**ref, 'candidate_id': candidate_id, 'issue_id': issue['id'],
                               'label': issue.get('label', issue['id']), 'catalog_version': catalog_version,
                               'status': 'retrieval_candidate_not_stance', 'evidence_id': evidence_id})
            frequency[issue['id']] += 1
            if not predictor or issue.get('classification_enabled') is not True or issue['id'] not in receipt.get('eligible_issue_ids', []):
                continue
            if not source_id or not source_hash or capacity not in ('national', 'individual_country') or not segment['canonical_country']:
                continue
            answer = predict_pair(issue['proposition'], text, predictor,
                                  manifest.get('decision_threshold', .9), manifest.get('status_threshold', .9))
            predictions.append({**ref, 'revision_id': source_id,
                                'prediction_id': identity('prediction', candidate_id, manifest['model_id']),
                                'issue_id': issue['id'], 'catalog_version': catalog_version,
                                'issue_version': catalog_version, 'model_version': manifest['model_id'],
                                'model_id': manifest['model_id'], 'evidence_id': evidence_id,
                                'label': answer['label'], 'stance': answer['label'],
                                'status': 'validated' if answer['label'] else 'abstained',
                                'interpretability_status': answer['status'],
                                'confidence': answer.get('confidence'),
                                'probabilities': answer.get('probabilities'),
                                'evidence': [{'start':w['start'],'end':w['end'],'quote':text[w['start']:w['end']]}
                                             for w in answer['windows'] if w['emitted']] if answer['label'] else [],
                                'windows': [{k:v for k,v in w.items() if k != 'text'} for w in answer['windows']]})
        if not matched:
            # New lexical candidates are a discovery queue, never automatically promoted policy objects.
            terms = collections.Counter(w.lower() for w in re.findall(r'\b[A-Za-z][A-Za-z-]{4,}\b', text)
                                        if w.lower() not in {'their','there','which','would','should','these','those','united','nations'})
            candidates.append({**ref, 'candidate_id': identity('discovery', source_id, sid, ref['text_sha256']),
                               'issue_id': None, 'status': 'uncatalogued_lexical_discovery',
                               'terms': [w for w, _ in terms.most_common(8)]})
    return {'issues': [{'issue_id':i['id'],'version':catalog_version,'label':i.get('label',i['id']),
                        'definition':i.get('proposition',i.get('label',i['id']))} for i in issues],
            'predictions': predictions, 'evidence': evidence, 'issue_candidates': candidates,
            'analytical_results': [{'method': 'lexical_issue_mention_counts', 'unit': 'segments',
                                    'status': 'descriptive_not_stance', 'counts': dict(sorted(frequency.items()))}],
            'model_status': model_status}
