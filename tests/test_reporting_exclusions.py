import json
from pathlib import Path
import unittest
from un_transcript.collection import RESERVED_DATES, RESERVED_MEETINGS

class ReportingExclusions(unittest.TestCase):
    def test_browser_reporting_keeps_the_exact_production_holdout(self):
        path = Path(__file__).resolve().parents[1] / 'site/reporting-exclusions.json'
        data = json.loads(path.read_text())
        self.assertEqual(data['schema'], 'un.reporting-exclusions.v1')
        self.assertEqual(data['dates'], sorted(RESERVED_DATES))
        self.assertEqual(data['meetings'], sorted(RESERVED_MEETINGS))
        self.assertEqual(len(data['meetings']), 37)
