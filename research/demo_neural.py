"""Build an explicitly fictional offline demonstration in a new directory."""
import argparse
import json
from pathlib import Path
from neural import run, sha, predict_saved
from neural_fixtures import text_data, sequence_data, make_checkpoint


def demo(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    checkpoint = make_checkpoint(root/'checkpoint')
    text = text_data()
    text.update(checkpoint_manifest=str(checkpoint), checkpoint_manifest_sha256=sha(checkpoint))
    summary = {'dataset_kind': 'synthetic_engineering', 'publication_eligible': False, 'results': {}}
    for method, data in [('M16', text), ('M38', sequence_data())]:
        inp = root/(method+'.json'); inp.write_text(json.dumps(data, indent=2), encoding='utf-8')
        result = run(method, inp, root/method)
        restored = predict_saved(root/method, data)
        assert restored['scores'] == result['evaluation']['scores']
        summary['results'][method] = {'logloss': result['evaluation']['logloss'],
            'prevalence_logloss': result['evaluation']['prevalence_logloss'],
            'parameters': result['parameters'], 'elapsed_seconds': result['elapsed_seconds'], 'saved_predictions_match': True}
        if method == 'M38':
            summary['results'][method]['last_observation_logloss'] = result['details']['last_observation_baseline']['logloss']
    (root/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('output'); a = p.parse_args()
    print(json.dumps(demo(a.output), indent=2))
