"""Independent design/prototype safety checks; never run a holdout."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
import numpy as np
from . import v3_prototype as v3

DESIGN = Path(__file__).resolve().parent / "v3_design_proposal.json"


class ProspectiveV3Tests(unittest.TestCase):
    def config(self):
        return json.loads(DESIGN.read_text())

    def test_design_valid_and_not_frozen(self):
        cfg = self.config()
        v3.verify_design(cfg)
        self.assertFalse(cfg["gates_frozen"])
        self.assertEqual(cfg["v3_holdout"], "NOT_CREATED")

    def test_cannot_supply_holdout_seed_or_authorization(self):
        for key,value in [("holdout_seed",12345), ("holdout_authorized",True),
                          ("real_fit_authorized",True), ("development_approved",True),
                          ("external_nugget_provenance","ORACLE")]:
            cfg = self.config()
            cfg[key] = value
            with self.assertRaises(ValueError,msg=key):
                v3.verify_design(cfg)

    def test_reproducible_dev_seed(self):
        self.assertEqual(v3.safe_seed("panel-1"), v3.safe_seed("panel-1"))
        self.assertNotEqual(v3.safe_seed("panel-1"), v3.safe_seed("panel-2"))

    def test_no_truth_leakage_and_structural_risk(self):
        o,truth = v3.simulate(16,"two_of_three","audited_mnar",.65,.15,7)
        self.assertNotIn("truth",o)
        self.assertTrue(np.isnan(o["value"][~(o["responded"]|o["audited"])]).all())
        self.assertEqual(truth["true_beta"],.2)
        self.assertFalse(o["at_risk"][:2,:,0].any())
        self.assertTrue(o["at_risk"][2:,:,0].all())
        self.assertFalse(o["included"][:2,:,0].any())

    def test_meeting_first_stage_is_stratified(self):
        o,_ = v3.simulate(16,"two_of_three","mar",0.,0.,8)
        for year in range(16):
            selected=np.flatnonzero(o["included"][year].any(axis=1))
            self.assertEqual(len(selected),8)
            for stratum in range(4):
                self.assertEqual(np.sum((selected>=3*stratum)&(selected<3*stratum+3)),2)

    def test_no_audit_mnar_must_refuse(self):
        o,_ = v3.simulate(16,"two_of_three","unaudited_mnar",.65,.15,7)
        with self.assertRaisesRegex(v3.NonIdentified,"independently audited"):
            v3.audited_year_means(o)

    def test_positive_audit_yields_feasible_estimation_or_support_refusal(self):
        o,_ = v3.simulate(16,"census","audited_mnar",.65,.15,11)
        try:
            annual=v3.audited_year_means(o)
        except v3.NonIdentified as e:
            self.assertIn("support",str(e))
        else:
            fits=v3.feasible_temporal_candidates(annual)
            self.assertTrue(fits["ar1_ridge"]["estimated_nuisance"])
            self.assertNotIn("rho_true",fits["ar1_ridge"])
            self.assertEqual(fits["external_nugget"]["status"],
                             "WITHHELD_EXTERNAL_MEASUREMENT_REQUIRED")
            with self.assertRaises(v3.NonIdentified):
                v3.feasible_temporal_candidates(annual, external_nugget=0.15)

    def test_source_response_state_corruption_refused(self):
        o,_ = v3.simulate(16,"census","audited_mnar",.65,.15,11)
        o["audited"][0,0,1] = True
        o["responded"][0,0,1] = True
        with self.assertRaises(v3.NonIdentified):
            v3.audited_year_means(o)

    def test_smoke_is_explicitly_not_calibration(self):
        result=v3.develop_smoke(self.config(),1)
        self.assertEqual(result["attempts"],3)
        self.assertEqual(result["holdout_attempted"],0)
        self.assertFalse(result["statistical_acceptance"])
        self.assertEqual(result["completed"]+result["refused"],3)

    def test_holdout_real_and_full_development_command_refused(self):
        for phase in ("holdout","real","development"):
            result=subprocess.run([sys.executable,str(Path(v3.__file__)),
                "--phase",phase,"--design",str(DESIGN)],
                capture_output=True,text=True,timeout=20)
            self.assertNotEqual(result.returncode,0,phase)
        result=subprocess.run([sys.executable,str(Path(v3.__file__)),
            "--phase","validate","--design",str(DESIGN)],
            capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)

if __name__ == "__main__":
    unittest.main()
