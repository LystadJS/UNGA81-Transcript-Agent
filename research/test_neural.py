"""Synthetic neural acceptance. Creates no real labels or downloaded models."""
import copy
import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import neural as n
import numpy as np
import torch
from safetensors.torch import save_file, load_file
from transformers import BertConfig, BertForMaskedLM, BertTokenizerFast, BertForSequenceClassification


from neural_fixtures import text_data, sequence_data, make_checkpoint


class NeuralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='un-i8-')
        cls.root = Path(cls.tmp.name).resolve()
        assert cls.root.is_relative_to(Path(tempfile.gettempdir()).resolve())
        cls.seq = sequence_data(); cls.text = text_data()
        path = make_checkpoint(cls.root/'checkpoint')
        cls.text.update(checkpoint_manifest=str(path), checkpoint_manifest_sha256=n.sha(path))
        # Deny network calls even though no loaded asset requires the network.
        with patch('socket.socket.connect', side_effect=AssertionError('network forbidden')):
            cls.text_result, cls.text_model, cls.tokenizer = n.fit(cls.text, 'M16')
            cls.seq_result, cls.seq_model, _ = n.fit(cls.seq, 'M38')

    @classmethod
    def tearDownClass(cls):
        assert cls.root.is_relative_to(Path(tempfile.gettempdir()).resolve())
        cls.tmp.cleanup()

    def reject(self, d, method):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            n.validate(d, method)

    def test_text_encoder_finetuned(self):
        self.assertGreater(self.text_result['details']['encoder_weight_change'], .001)
        self.assertLess(self.text_result['training_loss'][-1], self.text_result['training_loss'][0])

    def test_text_heldout_learning(self):
        e = self.text_result['evaluation']; self.assertLess(e['logloss'], e['prevalence_logloss'])

    def test_sequence_heldout_learning(self):
        e = self.seq_result['evaluation']; self.assertLess(e['logloss'], e['prevalence_logloss'])

    def test_sequence_baseline_present(self):
        e = self.seq_result['details']['last_observation_baseline']
        self.assertTrue(math_finite(e['logloss'])); self.assertEqual(len(e['scores']), 96)

    def test_publication_blocked(self):
        for r in (self.text_result, self.seq_result):
            self.assertFalse(r['publication_eligible']); self.assertFalse(r['daily_adapter_integrated'])

    def test_real_data_rejected(self):
        for d, m in [(self.text, 'M16'), (self.seq, 'M38')]:
            d = copy.deepcopy(d); d['dataset_kind'] = 'real'; self.reject(d, m)

    def test_country_leakage(self):
        d = copy.deepcopy(self.text); d['test'][0]['country'] = d['train'][0]['country']; self.reject(d, 'M16')

    def test_content_leakage(self):
        d = copy.deepcopy(self.text); d['test'][0].update({k:d['train'][0][k] for k in ('text', 'text_hash')}); self.reject(d, 'M16')

    def test_text_hash_binding(self):
        d = copy.deepcopy(self.text); d['test'][0]['text'] += ' changed'; self.reject(d, 'M16')

    def test_duplicate_ids(self):
        d = copy.deepcopy(self.text); d['train'][0]['id'] = d['train'][1]['id']; self.reject(d, 'M16')

    def test_future_training(self):
        d = copy.deepcopy(self.text); d['train'][0]['time'] = 5000; self.reject(d, 'M16')

    def test_missing_outcome(self):
        d = copy.deepcopy(self.text); d['train'][0]['y'] = None; self.reject(d, 'M16')

    def test_empty_target(self):
        d = copy.deepcopy(self.text); d['target'] = ''; self.reject(d, 'M16')

    def test_partition_cap(self):
        d = copy.deepcopy(self.text); d['train'] *= 9; self.reject(d, 'M16')

    def test_future_sequence(self):
        d = copy.deepcopy(self.seq); d['test'][0]['observed_times'][-1] = d['test'][0]['time']; self.reject(d, 'M38')

    def test_unavailable_sequence(self):
        d = copy.deepcopy(self.seq); d['test'][0]['available_at'][-1] = d['test'][0]['time']; self.reject(d, 'M38')

    def test_unsorted_sequence(self):
        d = copy.deepcopy(self.seq); d['test'][0]['observed_times'].reverse(); self.reject(d, 'M38')

    def test_history_leakage(self):
        d = copy.deepcopy(self.seq); d['test'][0]['observed_times'] = list(range(1, 7)); d['test'][0]['available_at'] = list(range(1, 7)); self.reject(d, 'M38')

    def test_unreviewed_comparability(self):
        d = copy.deepcopy(self.seq); d['train'][0]['comparable'] = False; self.reject(d, 'M38')

    def test_calendar_horizon(self):
        d = copy.deepcopy(self.seq); d['horizon'] = 'tomorrow'; self.reject(d, 'M38')

    def test_sequence_hash_binding(self):
        d = copy.deepcopy(self.seq); d['train'][0]['x'][0][0] += .1; self.reject(d, 'M38')

    def test_sequence_missing_feature(self):
        d = copy.deepcopy(self.seq); d['train'][0]['x'][0][0] = float('nan'); self.reject(d, 'M38')

    def test_sequence_padding_invariance(self):
        info = self.seq_result['details']; x, lengths = n.sequence_tensor(self.seq['test'], np.array(info['mean']), np.array(info['scale']))
        changed = x.clone()
        for i, length in enumerate(lengths): changed[i, length:] = 999
        with torch.no_grad():
            torch.testing.assert_close(self.seq_model(x, lengths), self.seq_model(changed, lengths), rtol=0, atol=0)

    def test_sequence_batch_order(self):
        info = self.seq_result['details']; x, lengths = n.sequence_tensor(self.seq['test'], np.array(info['mean']), np.array(info['scale']))
        with torch.no_grad():
            torch.testing.assert_close(self.seq_model(x, lengths), self.seq_model(x.flip(0), lengths.flip(0)).flip(0), rtol=1e-5, atol=1e-6)

    def test_fitted_model_not_changed_by_evaluation_labels(self):
        d = copy.deepcopy(self.seq)
        for r in d['test']: r['y'] = 1-r['y']
        result, model, _ = n.fit(d, 'M38')
        self.assertEqual(result['evaluation']['scores'], self.seq_result['evaluation']['scores'])
        for k, v in model.state_dict().items(): torch.testing.assert_close(v, self.seq_model.state_dict()[k], rtol=0, atol=0)

    def test_rng_and_thread_restoration(self):
        py = random.getstate(); rng = torch.get_rng_state(); threads = torch.get_num_threads(); flag = torch.are_deterministic_algorithms_enabled()
        with n.deterministic(): random.random(); torch.rand(3)
        self.assertEqual(py, random.getstate()); self.assertTrue(torch.equal(rng, torch.get_rng_state())); self.assertEqual(threads, torch.get_num_threads()); self.assertEqual(flag, torch.are_deterministic_algorithms_enabled())

    def test_manifest_hash_binding(self):
        with self.assertRaisesRegex(ValueError, 'manifest hash'): n.checkpoint(self.text['checkpoint_manifest'], '0'*64)

    def test_checkpoint_asset_tampering(self):
        p = Path(self.text['checkpoint_manifest']).parent/'vocab.txt'; original = p.read_bytes()
        try:
            p.write_bytes(original+b'newword\n')
            with self.assertRaisesRegex(ValueError, 'asset hash'): n.checkpoint(self.text['checkpoint_manifest'], self.text['checkpoint_manifest_sha256'])
        finally: p.write_bytes(original)

    def test_untracked_checkpoint_asset(self):
        p = Path(self.text['checkpoint_manifest']).parent/'extra.py'; p.write_text('raise RuntimeError()')
        try:
            with self.assertRaisesRegex(ValueError, 'Untracked'): n.checkpoint(self.text['checkpoint_manifest'], self.text['checkpoint_manifest_sha256'])
        finally: p.unlink()

    def test_saved_sequence_roundtrip(self):
        p = self.root/'sequence.safetensors'; save_file(self.seq_model.state_dict(), str(p))
        model = n.TemporalGRU(2); model.load_state_dict(load_file(str(p))); model.eval()
        for k, v in model.state_dict().items(): torch.testing.assert_close(v, self.seq_model.state_dict()[k])

    def test_saved_text_roundtrip(self):
        p = self.root/'text-roundtrip'; self.text_model.save_pretrained(p, safe_serialization=True)
        loaded = BertForSequenceClassification.from_pretrained(p, local_files_only=True, use_safetensors=True)
        for k, v in loaded.state_dict().items(): torch.testing.assert_close(v, self.text_model.state_dict()[k])

    def test_runner_hashes_and_immutable_output(self):
        inp = self.root/'input.json'; inp.write_text(json.dumps(self.seq), encoding='utf-8'); out = self.root/'run'
        n.run('M38', inp, out)
        for name, digest in n.read_json(out/'SHA256.json').items(): self.assertEqual(digest, n.sha(out/name))
        self.assertEqual(n.read_json(out/'result.json')['input_sha256'], n.sha(inp))
        with self.assertRaisesRegex(ValueError, 'already exists'): n.run('M38', inp, out)

    def test_sequence_saved_predictions(self):
        inp = self.root/'sequence-input.json'; inp.write_text(json.dumps(self.seq), encoding='utf-8'); out = self.root/'sequence-output'
        result = n.run('M38', inp, out)
        self.assertEqual(result['evaluation']['scores'], n.predict_saved(out, self.seq)['scores'])
        wrong = copy.deepcopy(self.seq); wrong['features'].reverse()
        with self.assertRaisesRegex(ValueError, 'representation/feature'): n.predict_saved(out, wrong)
        (out/'model.safetensors').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'): n.predict_saved(out, self.seq)

    def test_text_saved_predictions(self):
        inp = self.root/'text-input.json'; inp.write_text(json.dumps(self.text), encoding='utf-8'); out = self.root/'text-output'
        with patch('socket.socket.connect', side_effect=AssertionError('network forbidden')):
            result = n.run('M16', inp, out)
            np.testing.assert_allclose(result['evaluation']['scores'], n.predict_saved(out, self.text)['scores'], rtol=0, atol=0)

    def test_config_resource_boundaries(self):
        cfg = json.loads((Path(self.text['checkpoint_manifest']).parent/'config.json').read_text())
        for key, val in [('hidden_size', 1000000), ('num_hidden_layers', 100), ('model_type', 'unknown'), ('auto_map', {'remote': 'code'})]:
            altered = dict(cfg); altered[key] = val
            with self.assertRaises(ValueError): n.validate_config(altered)

    def test_long_text_is_not_silently_truncated(self):
        d = copy.deepcopy(self.text); d['test'][0]['text'] = 'alpha '*100
        d['test'][0]['text_hash'] = hashlib.sha256(d['test'][0]['text'].encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'token budget'): n.fit(d, 'M16')

    def test_text_evaluation_labels_do_not_change_training(self):
        d = copy.deepcopy(self.text)
        for r in d['test']: r['y'] = 1-r['y']
        result, model, _ = n.fit(d, 'M16')
        self.assertEqual(result['evaluation']['scores'], self.text_result['evaluation']['scores'])
        for k, v in model.state_dict().items(): torch.testing.assert_close(v, self.text_model.state_dict()[k], rtol=0, atol=0)

    def test_duplicate_json_keys(self):
        p = self.root/'duplicate.json'; p.write_text('{"x":1,"x":2}')
        with self.assertRaisesRegex(ValueError, 'Duplicate'): n.read_json(p)

    def test_nonfinite_json(self):
        p = self.root/'nonfinite.json'; p.write_text('{"x":NaN}')
        with self.assertRaisesRegex(ValueError, 'Nonfinite'): n.read_json(p)

    def test_input_hash_binds_consumed_bytes(self):
        inp = self.root/'changing-input.json'; inp.write_text(json.dumps(self.seq), encoding='utf-8')
        expected = n.sha(inp)
        def changed_after_read(data, method):
            inp.write_text('{}', encoding='utf-8')
            return copy.deepcopy(self.seq_result), self.seq_model, None
        with patch.object(n, 'fit', side_effect=changed_after_read):
            result = n.run('M38', inp, self.root/'changing-output')
        self.assertEqual(result['input_sha256'], expected)
        self.assertNotEqual(result['input_sha256'], n.sha(inp))

    def test_invalid_predictions_rejected(self):
        with self.assertRaisesRegex(ValueError, 'prediction'): n.metrics([float('nan')]*64, self.text['test'], 1)
        with self.assertRaisesRegex(ValueError, 'prediction'): n.metrics([0]*64, self.text['test'], 0)


def math_finite(x):
    return np.isfinite(x)


if __name__ == '__main__':
    unittest.main(verbosity=2)
