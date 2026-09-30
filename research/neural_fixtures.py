"""Fictional engineering fixtures, never a source of reviewed UN labels."""
from pathlib import Path
import hashlib
import json
import numpy as np
import torch
import neural as n
from transformers import BertConfig, BertForMaskedLM, BertTokenizerFast

def text_data():
    d = {'dataset_kind': 'synthetic_engineering', 'target': 'fictional binary marker'}
    for name, off in [('train', 0), ('calibration', 1000), ('test', 2000)]:
        d[name] = []
        for i in range(64):
            text = ('alpha' if i % 2 else 'beta') + ' report statement ' + name + str(i)
            d[name].append({'id': name+str(i), 'country': name+str(i), 'time': off+i,
                            'text': text, 'text_hash': hashlib.sha256(text.encode()).hexdigest(), 'y': i % 2})
    return d


def sequence_data():
    rng = np.random.default_rng(912)
    d = {'dataset_kind': 'synthetic_engineering', 'target': 'fictional next observation',
         'horizon': 'next_comparable_observation', 'features': ['level', 'noise'], 'representation_id': 'synthetic-v1'}
    for name, off in [('train', 100), ('calibration', 1000), ('test', 2000)]:
        d[name] = []
        for i in range(96):
            x = rng.normal(size=(6+i % 3, 2)); y = int(x[:, 0].mean() > 0)
            rows = x.tolist(); times = list(range(off+i*10, off+i*10+len(x)))
            # Large offsets between whole partitions, including complete history windows.
            d[name].append({'id': name+str(i), 'country': name+str(i), 'time': times[-1]+1,
                            'x': rows, 'text_hash': n.window_hash(rows), 'observed_times': times,
                            'available_at': times, 'comparable': True, 'y': y})
    # Ensure non-overlap with each preceding 960-time-unit observation panel.
    for r in d['calibration']:
        r['time'] += 1000; r['observed_times'] = [t+1000 for t in r['observed_times']]; r['available_at'] = r['observed_times'][:]
    for r in d['test']:
        r['time'] += 2000; r['observed_times'] = [t+2000 for t in r['observed_times']]; r['available_at'] = r['observed_times'][:]
    return d


def make_checkpoint(root):
    root.mkdir()
    vocab = ['[PAD]', '[UNK]', '[CLS]', '[SEP]', '[MASK]', 'alpha', 'beta', 'report', 'statement', 'train', 'test']
    (root/'vocab.txt').write_text('\n'.join(vocab)+'\n', encoding='utf-8')
    tok = BertTokenizerFast(vocab_file=str(root/'vocab.txt'), do_lower_case=True)
    with n.deterministic():
        cfg = BertConfig(vocab_size=len(vocab), hidden_size=16, num_hidden_layers=1, num_attention_heads=2,
                         intermediate_size=32, max_position_embeddings=64, hidden_dropout_prob=0, attention_probs_dropout_prob=0)
        mlm = BertForMaskedLM(cfg)
        batch = tok(['alpha report statement', 'beta report statement']*12, return_tensors='pt', padding=True)
        labels = batch['input_ids'].clone(); labels[:, [0, 1, 3, 4]] = -100
        batch['input_ids'][:, 2] = tok.mask_token_id
        opt = torch.optim.AdamW(mlm.parameters(), lr=.005)
        for _ in range(15):
            opt.zero_grad(); loss = mlm(**batch, labels=labels).loss; loss.backward(); opt.step()
        mlm.save_pretrained(root, safe_serialization=True); tok.save_pretrained(root)
    manifest = {'purpose': 'synthetic_engineering', 'pretraining': '15 masked-token updates on fictional strings; no natural-language capability claim',
                'assets': {p.name: n.sha(p) for p in root.iterdir()}}
    path = root/'manifest.json'; path.write_text(json.dumps(manifest), encoding='utf-8')
    return path
