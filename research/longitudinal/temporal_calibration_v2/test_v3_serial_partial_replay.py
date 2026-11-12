"""Exact scenario/method/replicate failure replay; no confirmatory holdout."""
from __future__ import annotations
from collections import defaultdict
import json
from pathlib import Path
import unittest
from .v3_serial_partial_study import development_study

ROOT=Path(__file__).resolve().parent

class FrozenNegativeDevelopmentReceiptTests(unittest.TestCase):
    def test_all_failed_attempt_identities_preserved(self):
        receipt=json.loads((ROOT/'v3_serial_partial_failure_index.json').read_text())
        out,ledger=development_study(30)
        self.assertEqual(receipt['status'],'SYNTHETIC_DEV_ONLY')
        self.assertEqual(receipt['v3_holdout_attempted'],0)
        self.assertEqual(out['v3_holdout_attempted'],0)
        self.assertEqual(receipt['failed_attempts'],len(ledger))
        self.assertEqual(out['failure_ledger_count'],len(ledger))
        self.assertEqual(out['response_attempted'],receipt['attempted']['response'])
        self.assertEqual(out['covariance_attempted'],receipt['attempted']['covariance'])
        self.assertEqual(out['response_completed']+out['response_failed'],out['response_attempted'])
        self.assertEqual(out['covariance_completed']+out['covariance_failed'],out['covariance_attempted'])
        self.assertFalse(out['statistical_acceptance'])
        reverse={value:key for key,value in receipt['reason_codes'].items()}
        actual=defaultdict(int)
        for x in ledger:
            self.assertIn(x['reason'],reverse)
            key=(x['study'],x['scenario'],reverse[x['reason']])
            self.assertTrue(0<=x['replicate']<30)
            actual[key]|=(1<<x['replicate'])
        expected={(x['study'],x['scenario'],x['reason']):int(x['hex_mask'],16)
                  for x in receipt['failure_masks']}
        self.assertEqual(dict(actual),expected)
        for entry in receipt['failure_masks']:
            how_many=int(entry['hex_mask'],16).bit_count()
            methods=receipt['methods_per_response_scenario'] if entry['study']=='response' else receipt['methods_per_covariance_scenario']
            reported=sum(z['failed'] for z in (out['gamma'] if entry['study']=='response' else out['covariance'])
                         if z['scenario']==entry['scenario'])
            self.assertGreaterEqual(reported,how_many*len(methods))
        self.assertFalse(receipt['statistical_acceptance'])

if __name__=='__main__':unittest.main()
