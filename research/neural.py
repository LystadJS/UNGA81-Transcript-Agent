"""CPU-only synthetic engineering paths. Never imported by the daily pipeline."""
from pathlib import Path
from contextlib import contextmanager
import argparse
import hashlib
import json
from importlib.metadata import version
import math
import os
import random
import time

os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
import numpy as np
import torch
from torch import nn
from safetensors.torch import save_file, load_file

NEURAL_IDS = ('M16', 'M38')
SEED = 30092026


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read_json(path, with_digest=False):
    path = Path(path)
    require(path.stat().st_size <= 10_000_000, 'JSON resource limit exceeded')
    def unique(pairs):
        result = {}
        for k, v in pairs:
            require(k not in result, 'Duplicate JSON key')
            result[k] = v
        return result
    payload = path.read_bytes()
    require(len(payload) <= 10_000_000, 'JSON resource limit exceeded')
    parsed = json.loads(payload.decode('utf-8'), object_pairs_hook=unique,
                        parse_constant=lambda s: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    return (parsed, hashlib.sha256(payload).hexdigest()) if with_digest else parsed


@contextmanager
def deterministic():
    py, npstate, ts = random.getstate(), np.random.get_state(), torch.get_rng_state()
    threads, flag = torch.get_num_threads(), torch.are_deterministic_algorithms_enabled()
    warn = torch.is_deterministic_algorithms_warn_only_enabled()
    try:
        random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
        torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
        yield
    finally:
        random.setstate(py); np.random.set_state(npstate); torch.set_rng_state(ts)
        torch.set_num_threads(threads); torch.use_deterministic_algorithms(flag, warn_only=warn)


def validate(d, method):
    require(method in NEURAL_IDS, 'Unknown neural method')
    require(d.get('dataset_kind') == 'synthetic_engineering', 'Real/unreviewed neural input is not enabled')
    require(isinstance(d.get('target'), str) and d['target'].strip(), 'Named binary target required')
    parts = [d[k] for k in ('train', 'calibration', 'test')]
    for rows in parts:
        require(isinstance(rows, list) and 24 <= len(rows) <= 512, 'Each partition needs 24..512 observations')
        require({r['y'] for r in rows} == {0, 1}, 'Both binary outcomes required; missing is not negative')
        for key in ('id', 'country', 'text_hash'):
            require(all(isinstance(r[key], str) and r[key].strip() for r in rows), 'Missing grouping identity')
        require(len({r['id'] for r in rows}) == len(rows), 'Duplicate observation ID')
        require(all(isinstance(r['time'], (int, float)) and math.isfinite(r['time']) for r in rows), 'Finite outcome time required')
    for i in range(3):
        for j in range(i+1, 3):
            for key in ('id', 'country', 'text_hash'):
                require(not ({r[key] for r in parts[i]} & {r[key] for r in parts[j]}), 'Country/content/ID leakage across partitions')
            require(max(r['time'] for r in parts[i]) < min(r['time'] for r in parts[j]), 'Forward-time partitions required')
    if method == 'M16':
        for rows in parts:
            for r in rows:
                require(isinstance(r['text'], str) and 1 <= len(r['text']) <= 4000, 'Text length limit')
                require(hashlib.sha256(r['text'].encode()).hexdigest() == r['text_hash'], 'Text hash mismatch')
    else:
        require(d.get('horizon') == 'next_comparable_observation', 'Explicit next-observation horizon required')
        require(isinstance(d.get('representation_id'), str) and d['representation_id'], 'Pinned representation required')
        features = d.get('features')
        require(isinstance(features, list) and 1 <= len(features) <= 32 and all(isinstance(s, str) and s for s in features) and len(set(features)) == len(features), 'Unique ordered feature names required')
        for rows in parts:
            for r in rows:
                x = np.asarray(r['x'], dtype=np.float32)
                require(x.ndim == 2 and 2 <= len(x) <= 32 and x.shape[1] == len(features) and np.isfinite(x).all(), 'Bounded complete sequence matrix required')
                t, a = np.asarray(r['observed_times'], dtype=float), np.asarray(r['available_at'], dtype=float)
                require(t.shape == (len(x),) and a.shape == t.shape and np.isfinite(t).all() and np.isfinite(a).all(), 'Observation and availability times required')
                require(np.all(np.diff(t) > 0) and np.all(a >= t) and np.all(a < r['time']) and t[-1] < r['time'], 'Future/unavailable sequence information')
                require(r.get('comparable') is True, 'Comparability must be declared; gaps are not daily zeros')
                # Hash the complete feature window, not an arbitrary caller identifier.
                require(window_hash(r['x']) == r['text_hash'], 'Sequence content hash mismatch')
        # Evaluation history must also begin after every earlier partition outcome.
        for i in range(2):
            require(max(r['time'] for r in parts[i]) < min(min(r['observed_times']) for r in parts[i+1]), 'Overlapping history across temporal partitions')
    return parts


def window_hash(x):
    return hashlib.sha256(json.dumps(x, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def checkpoint(path, expected):
    path = Path(path).resolve()
    require(sha(path) == expected, 'Checkpoint manifest hash mismatch')
    m = read_json(path)
    require(m.get('purpose') == 'synthetic_engineering', 'Only synthetic checkpoint experiments enabled')
    assets = m['assets']; root = path.parent
    required = {'config.json', 'model.safetensors', 'tokenizer.json', 'tokenizer_config.json'}
    require(required <= set(assets) and len(assets) <= 12, 'Incomplete checkpoint/tokenizer bundle')
    require({p.name for p in root.iterdir()} == set(assets) | {path.name}, 'Untracked checkpoint asset')
    total = 0
    for name, digest in assets.items():
        require(Path(name).name == name and '/' not in name and '\\' not in name and name not in ('.', '..'), 'Invalid checkpoint member path')
        p = root / name
        require(p.is_file() and not p.is_symlink() and p.suffix in ('.json', '.txt', '.safetensors'), 'Unsupported checkpoint asset')
        total += p.stat().st_size
        require(total <= 128_000_000, 'Checkpoint resource limit')
        require(sha(p) == digest, 'Checkpoint asset hash mismatch')
    config = read_json(root / 'config.json')
    validate_config(config)
    return root, m


def validate_config(config):
    require(config.get('model_type') == 'bert' and not config.get('auto_map'), 'Only built-in BERT is supported')
    for key, lo, hi in [('hidden_size', 8, 128), ('num_hidden_layers', 1, 4), ('intermediate_size', 8, 512), ('vocab_size', 8, 32000), ('max_position_embeddings', 16, 512), ('num_attention_heads', 1, 8)]:
        require(isinstance(config.get(key), int) and lo <= config[key] <= hi, 'Bounded BERT configuration required: ' + key)
    require(not config.get('is_decoder', False) and config['hidden_size'] % config['num_attention_heads'] == 0, 'Encoder attention configuration required')


class TemporalGRU(nn.Module):
    def __init__(self, features):
        super().__init__()
        self.gru = nn.GRU(features, 16, batch_first=True)
        self.head = nn.Linear(16, 1)

    def forward(self, x, lengths):
        packed = nn.utils.rnn.pack_padded_sequence(x, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, h = self.gru(packed)
        return self.head(h[-1]).squeeze(-1)


def sequence_tensor(rows, mean, scale):
    arrays = [torch.tensor((np.asarray(r['x'])-mean)/scale, dtype=torch.float32) for r in rows]
    return nn.utils.rnn.pad_sequence(arrays, batch_first=True), torch.tensor([len(x) for x in arrays])


def train(model, batches, y, steps, lr):
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=.01)
    losses = []
    model.train()
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        logits = batches(model)
        loss = nn.functional.binary_cross_entropy_with_logits(logits, y)
        require(torch.isfinite(loss).item(), 'Nonfinite training loss')
        loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1)
        optimizer.step(); losses.append(float(loss.detach()))
    model.eval()
    return losses


def metrics(logits, rows, temperature):
    y = np.array([r['y'] for r in rows], dtype=float)
    raw = np.asarray(logits, dtype=float)
    require(raw.shape == y.shape and np.isfinite(raw).all() and math.isfinite(temperature) and .25 <= temperature <= 4, 'Invalid prediction or calibration values')
    z = raw/temperature
    p = 1/(1+np.exp(-np.clip(z, -40, 40)))
    return {'scores': p.tolist(), 'logloss': float(np.mean(np.logaddexp(0, z)-y*z)),
            'brier': float(np.mean((p-y)**2)), 'coverage': float(np.mean((p <= .3) | (p >= .7))),
            'predicted': ['negative' if v <= .3 else 'positive' if v >= .7 else 'abstain' for v in p]}


def evaluate(cal, test, parts):
    # Fixed temperature grid; only calibration outcomes enter selection.
    candidates = np.geomspace(.25, 4, 41)
    temperature = float(min(candidates, key=lambda t: metrics(cal, parts[1], t)['logloss']))
    result = metrics(test, parts[2], temperature)
    base = np.mean([r['y'] for r in parts[0]])
    result['prevalence_logloss'] = float(np.mean([-r['y']*math.log(base)-(1-r['y'])*math.log(1-base) for r in parts[2]]))
    result['temperature'] = temperature
    return result


def fit(d, method):
    require(torch.__version__.split('+')[0] == '2.10.0', 'Untested torch version; expected 2.10.0')
    parts = validate(d, method)
    started = time.perf_counter()
    with deterministic():
        y = torch.tensor([r['y'] for r in parts[0]], dtype=torch.float32)
        if method == 'M16':
            import transformers
            require(transformers.__version__ == '4.57.6', 'Untested transformers version')
            from transformers import BertTokenizerFast, BertForSequenceClassification
            root, manifest = checkpoint(d['checkpoint_manifest'], d['checkpoint_manifest_sha256'])
            tokenizer = BertTokenizerFast.from_pretrained(str(root), local_files_only=True)
            model, info = BertForSequenceClassification.from_pretrained(str(root), local_files_only=True, use_safetensors=True, num_labels=2, output_loading_info=True, attn_implementation='eager')
            require(not any(k.startswith(('bert.encoder.', 'bert.embeddings.')) for k in info['missing_keys']), 'Checkpoint lacks encoder weights')
            require(len(tokenizer) == model.config.vocab_size and sum(p.numel() for p in model.parameters()) <= 10_000_000, 'Tokenizer/model mismatch or oversized model')
            limit = min(64, model.config.max_position_embeddings)
            tokenized = []
            for rows in parts:
                texts = [r['text'] for r in rows]
                require(all(len(t) <= limit for t in tokenizer(texts, truncation=False)['input_ids']), 'Text exceeds token budget; explicit passage segmentation required')
                tokenized.append(tokenizer(texts, padding=True, truncation=False, return_tensors='pt'))
            def logit(m, i):
                z = m(**tokenized[i]).logits
                return z[:, 1]-z[:, 0]
            before = model.bert.embeddings.word_embeddings.weight.detach().clone()
            losses = train(model, lambda m: logit(m, 0), y, 60, .002)
            with torch.no_grad():
                cal, test = logit(model, 1).numpy(), logit(model, 2).numpy()
            extra = {'encoder_weight_change': float((before-model.bert.embeddings.word_embeddings.weight).norm().detach()),
                     'loading_info': info, 'checkpoint_manifest_sha256': d['checkpoint_manifest_sha256'],
                     'tokenizer_limit': limit, 'config': model.config.to_dict(), 'steps': 60, 'learning_rate': .002,
                     'checkpoint_purpose': manifest['purpose']}
        else:
            x = np.concatenate([r['x'] for r in parts[0]], axis=0)
            mean, scale = x.mean(axis=0), x.std(axis=0)
            require(np.all(scale > 1e-8), 'Constant training feature')
            inputs = [sequence_tensor(rows, mean, scale) for rows in parts]
            model = TemporalGRU(len(d['features']))
            losses = train(model, lambda m: m(*inputs[0]), y, 120, .01)
            with torch.no_grad():
                cal, test = [model(*v).numpy() for v in inputs[1:]]
            # Matched partition baseline using only the most recent observation.
            baseline = nn.Linear(len(d['features']), 1)
            last = [torch.tensor(np.asarray([(np.asarray(r['x'][-1])-mean)/scale for r in rows]), dtype=torch.float32) for rows in parts]
            train(baseline, lambda m: m(last[0]).squeeze(-1), y, 120, .01)
            with torch.no_grad():
                baseline_result = evaluate(baseline(last[1]).squeeze(-1).numpy(), baseline(last[2]).squeeze(-1).numpy(), parts)
            tokenizer = None
            extra = {'features': d['features'], 'representation_id': d['representation_id'], 'mean': mean.tolist(), 'scale': scale.tolist(),
                     'horizon': d['horizon'], 'architecture': 'one-layer unidirectional GRU, 16 hidden units',
                     'steps': 120, 'learning_rate': .01, 'last_observation_baseline': baseline_result}
        result = {'schema': 'un.i8.neural.v1', 'method_id': method, 'dataset_kind': d['dataset_kind'],
                  'publication_eligible': False, 'daily_adapter_integrated': False, 'seed': SEED,
                  'target': d['target'], 'evaluation': evaluate(cal, test, parts), 'details': extra,
                  'training_loss': losses, 'parameters': sum(p.numel() for p in model.parameters()),
                  'elapsed_seconds': time.perf_counter()-started, 'torch': torch.__version__, 'numpy': np.__version__,
                  'packages': {p: version(p) for p in ('torch', 'transformers', 'tokenizers', 'safetensors', 'numpy')},
                  'scope': 'synthetic training mechanics only; no real-text accuracy or deployment acceptance'}
        return result, model, tokenizer


def run(method, input_path, output):
    output = Path(output)
    require(not output.exists(), 'Output directory already exists; use a new immutable name')
    data, input_digest = read_json(input_path, with_digest=True)
    result, model, tokenizer = fit(data, method)
    output.mkdir(parents=True, exist_ok=False)
    result['input_sha256'] = input_digest
    result['engine_sha256'] = sha(__file__)
    if method == 'M16':
        model.save_pretrained(output, safe_serialization=True)
        tokenizer.save_pretrained(output)
    else:
        save_file({k: v.detach().cpu().contiguous() for k, v in model.state_dict().items()}, str(output/'model.safetensors'))
    (output/'result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    hashes = {p.name: sha(p) for p in output.iterdir() if p.is_file()}
    (output/'SHA256.json').write_text(json.dumps(hashes, indent=2)+'\n', encoding='utf-8')
    return result


def predict_saved(output, d):
    """Reload an intact saved run and score its declared synthetic test partition."""
    output = Path(output).resolve()
    hashes = read_json(output/'SHA256.json')
    require({'result.json', 'model.safetensors'} <= set(hashes), 'Incomplete saved run')
    require({p.name for p in output.iterdir()} == set(hashes) | {'SHA256.json'}, 'Untracked saved-run member')
    total = 0
    for name, expected in hashes.items():
        require(Path(name).name == name and '/' not in name and '\\' not in name, 'Invalid saved-run member')
        path = output/name
        require(path.is_file() and not path.is_symlink(), 'Invalid saved-run file')
        total += path.stat().st_size
        require(total <= 128_000_000 and sha(path) == expected, 'Saved-run size/hash mismatch')
    result = read_json(output/'result.json')
    require(result['schema'] == 'un.i8.neural.v1' and result['publication_eligible'] is False and result['daily_adapter_integrated'] is False, 'Invalid research envelope')
    method, details = result['method_id'], result['details']
    parts = validate(d, method)
    require(result['target'] == d['target'], 'Saved target mismatch')
    with deterministic(), torch.no_grad():
        if method == 'M16':
            from transformers import BertTokenizerFast, BertForSequenceClassification
            validate_config(read_json(output/'config.json'))
            tokenizer = BertTokenizerFast.from_pretrained(str(output), local_files_only=True)
            model = BertForSequenceClassification.from_pretrained(str(output), local_files_only=True, use_safetensors=True, attn_implementation='eager')
            texts = [r['text'] for r in parts[2]]
            require(all(len(t) <= details['tokenizer_limit'] for t in tokenizer(texts, truncation=False)['input_ids']), 'Text exceeds saved token budget')
            model.eval(); values = model(**tokenizer(texts, padding=True, return_tensors='pt')).logits
            logits = (values[:, 1]-values[:, 0]).numpy()
        else:
            require(details['features'] == d['features'] and details['representation_id'] == d['representation_id'], 'Saved representation/feature mismatch')
            model = TemporalGRU(len(details['features'])); model.load_state_dict(load_file(str(output/'model.safetensors'))); model.eval()
            logits = model(*sequence_tensor(parts[2], np.array(details['mean']), np.array(details['scale']))).numpy()
        return metrics(logits, parts[2], result['evaluation']['temperature'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('method', choices=NEURAL_IDS); parser.add_argument('input'); parser.add_argument('output')
    a = parser.parse_args(); run(a.method, a.input, a.output)
    print('Saved synthetic neural engineering result; publication remains disabled.')
