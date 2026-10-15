# Temporal calibration v2 — engineering research, incomplete

This isolated module provides synthetic meeting/year dependence, distinct first-stage meeting selection and outcome-dependent transcript response, a constrained covariance moment candidate, metadata incompatibility refusals and an unconditional real-fit stop.

**Statistical decision: FAIL / WITHHELD.** It does not yet reproduce PR #62's original scenario engine, estimate the response mechanism, conduct independently frozen development/holdout calibration, or establish interval coverage. The moment estimator is deliberately ineligible for 16-year inference (minimum 24 annual observations, and additional identifiability refusals). Its minimum sample size is a conservative engineering refusal, not a validated sufficiency threshold. No synthetic holdout has been examined and no candidate is approved.

Run: `python -m pip install numpy && python -m unittest discover -s research/longitudinal/temporal_calibration_v2 -p 'test_*.py' -v`

PR #62 reported 0/18 temporal rho recovery passes; its 5,760 holdout attempts included 4,260 usable identifiable fits, 60 support failures, and 1,440 appropriate unaudited MNAR abstentions. Those are **inherited reports, not new results**.

Future independent review must freeze a preregistered scenario matrix and thresholds before a fresh holdout, estimate selection response parameters using independently verified audits, and report all convergence, bias, interval, coverage and false-confidence denominators. No historical data, original PVs or reserved transcripts are read here.
