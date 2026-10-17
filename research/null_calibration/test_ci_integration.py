import tempfile
import unittest
from pathlib import Path
from ci_integration import validate, call, FROZEN

class StrictIntegrationTests(unittest.TestCase):
    def test_no_checkout(self):
        with tempfile.TemporaryDirectory() as d:
            x=validate(d,'a'*40,'b'*40)
            self.assertFalse(x['ready'])
            self.assertEqual(x['blocker'],'no_git_checkout')
    def test_wrong_head(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'.git').mkdir()
            self.assertEqual(validate(d,'a'*40,'b'*40)['blocker'],'wrong_head_or_main')
    def test_nonzero_is_failure(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(call(d,['python3','-c','raise SystemExit(7)'],10)['status'],'FAIL')
    def test_frozen_pins(self):
        self.assertEqual(len(FROZEN),2)
        self.assertTrue(all(len(v)==40 for v in FROZEN.values()))

if __name__ == '__main__':unittest.main()
