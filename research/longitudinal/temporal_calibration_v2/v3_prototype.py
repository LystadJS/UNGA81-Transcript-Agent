"""Prospective v3 synthetic prototype. NO HOLDOUT OR REAL-DATA ENTRYPOINT.

The simulator emits observable data and evaluator truth separately. Small
development-only smoke simulations test plumbing, NOT calibration acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

MODELS = ("iid_control", "ar1_zero_nugget", "ar1_ridge", "external_nugget", "union_sensitivity")
YEARS = (8, 16, 24, 32, 48)
MASKS = ("census", "two_of_three", "era_shift")
RESPONSES = ("mar", "audited_mnar", "unaudited_mnar", "weak_support")
RHO = (0.0, 0.35, 0.65, 0.85)
NUGGET = (0.0, 0.15, 0.4)
DEV_NAMESPACE = "UNGA81-V3-DESIGN-DEV-NOT-CONFIRMATORY"
SCHEMA = "un.w4.temporal-identification-v3.proposal.v1"


class NonIdentified(ValueError):
    pass


def safe_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256((DEV_NAMESPACE + "|" + label).encode()).digest()[:8], "big")


def verify_design(cfg: dict) -> None:
    if cfg.get("schema") != SCHEMA or cfg.get("status") != "PROPOSED_NOT_FROZEN":
        raise ValueError("v3 requires prospective protocol review")
    if cfg.get("holdout_authorized") is not False or cfg.get("real_fit_authorized") is not False:
        raise ValueError("holdout / real fit forbidden")
    if cfg.get("development_approved") is not False:
        raise ValueError("development has not been approved")
    if cfg.get("primary_years") != 16:
        raise ValueError("16-year primary estimand cannot be replaced")
    if cfg.get("horizons") != list(YEARS) or cfg.get("masks") != list(MASKS):
        raise ValueError("design axes changed")
    if cfg.get("responses") != list(RESPONSES) or cfg.get("rho_values") != list(RHO):
        raise ValueError("design axes changed")
    if cfg.get("nugget_sd") != list(NUGGET):
        raise ValueError("year nugget design changed")
    if cfg.get("methods") != list(MODELS):
        raise ValueError("method identities changed")
    if cfg.get("holdout_seed") is not None:
        raise ValueError("holdout cannot be seeded before freeze")
    if cfg.get("external_nugget_provenance") != "INDEPENDENT_MEASUREMENT_REQUIRED":
        raise ValueError("unknown nugget value cannot be oracle-supplied")


def simulate(T: int, mask: str, response: str, rho: float, nugget_sd: float,
             seed: int) -> tuple[dict, dict]:
    if T not in YEARS or mask not in MASKS or response not in RESPONSES:
        raise ValueError("outside prospective factorial grid")
    if rho not in RHO or nugget_sd not in NUGGET or not isinstance(seed, int):
        raise ValueError("outside nuisance design")
    rng = np.random.default_rng(seed)
    n_meet, n_actor = 12, 18
    # Meeting draws nested in year; actor effects shared across years.
    actor = rng.normal(0, 0.40, n_actor)
    years = np.empty(T)
    previous = 0.0
    for t in range(T):
        previous = rho * previous + math.sqrt(1-rho*rho) * rng.normal(0, 0.20)
        years[t] = previous + rng.normal(0, nugget_sd)
    y = np.full((T, n_meet, n_actor), np.nan)
    included = np.zeros_like(y, dtype=bool)
    response_seen = np.zeros_like(y, dtype=bool)
    audited = np.zeros_like(y, dtype=bool)
    at_risk = np.ones_like(y, dtype=bool)
    inclusion_pi = np.zeros_like(y)
    audit_q = np.zeros_like(y)
    truth = np.full_like(y, np.nan)
    for t in range(T):
        selected = np.zeros(n_meet, dtype=bool)
        if mask == "census":
            selected[:] = True
            pi = np.ones(n_meet)
        else:
            # Four strata of three original meetings; two sampled without replacement.
            pi = np.full(n_meet, 2 / 3)
            if mask == "era_shift" and t >= T // 2:
                # Deliberately different frame in later era; never silently pooled.
                pi[9:12] = 1.0
            for stratum in range(4):
                idx = np.arange(3 * stratum, 3 * stratum + 3)
                k = 3 if mask == "era_shift" and t >= T // 2 and stratum == 3 else 2
                selected[rng.choice(idx, k, replace=False)] = True
        for m in range(n_meet):
            meeting = rng.normal(0, 0.12)
            for a in range(n_actor):
                # Explicit structural ineligibility for a declared actor before year 2.
                at_risk[t,m,a] = not (a == 0 and t < 2)
                if not at_risk[t,m,a]:
                    continue
                value = 0.2 * (t >= T // 2) + years[t] + actor[a] + meeting + rng.normal(0, 0.25)
                truth[t,m,a] = value
                inclusion_pi[t,m,a] = pi[m]
                if not selected[m]:
                    continue
                included[t,m,a] = True
                slope = -1.25 if response != "mar" else 0.0
                logit = float(np.clip(0.4 + slope * value, -20, 20))
                responded = bool(rng.random() < 1 / (1 + math.exp(-logit)))
                response_seen[t,m,a] = responded
                if responded:
                    y[t,m,a] = value
                else:
                    q = 0.0 if response == "unaudited_mnar" else (0.025 if response == "weak_support" else 0.40)
                    audit_q[t,m,a] = q
                    audit = bool(rng.random() < q)
                    audited[t,m,a] = audit
                    if audit:
                        y[t,m,a] = value
    observable = dict(value=y, included=included, responded=response_seen,
                      audited=audited, at_risk=at_risk, inclusion_probability=inclusion_pi,
                      independent_audit_probability=audit_q,
                      independent_audit_provenance=response != "unaudited_mnar",
                      design_id=mask, years=T)
    evaluator = dict(true_beta=0.20, rho=rho, nugget_sd=nugget_sd, truth=truth)
    return observable, evaluator


def audited_year_means(obs: dict) -> np.ndarray:
    if not obs.get("independent_audit_provenance"):
        raise NonIdentified("nonresponse outcomes not independently audited")
    Y, S, R, A = [obs[k] for k in ("value", "included", "responded", "audited")]
    P, Q, eligible = [obs[k] for k in ("inclusion_probability",
                                      "independent_audit_probability", "at_risk")]
    if Y.shape != S.shape or S.shape != R.shape or S.shape != A.shape:
        raise NonIdentified("broken observation lineage")
    if np.any((R | A) & ~S) or np.any(R & A):
        raise NonIdentified("invalid response/audit assignment")
    if np.any(S & ((P <= 0) | (P > 1))) or np.any(S & ~eligible):
        raise NonIdentified("meeting inclusion positivity or structural risk failure")
    if np.any(~np.isfinite(Y[R | A])) or np.any(np.isfinite(Y[~(R | A)])):
        raise NonIdentified("unobserved outcome leakage")
    means = []
    for t in range(Y.shape[0]):
        sampled = S[t] & eligible[t]
        respondents = sampled & R[t]
        missing = sampled & ~R[t]
        recovered = sampled & A[t]
        if not np.any(missing) or not np.any(recovered):
            raise NonIdentified("independent outcome-recovery support unavailable")
        if np.any(Q[t][missing] <= 0):
            raise NonIdentified("audit positivity absent")
        if np.sum(respondents) < 5 or np.sum(recovered) < 3:
            raise NonIdentified("insufficient respondent/recovered strata")
        # Two-stage Hájek by response stratum: meeting weights, phase-II recovery weights.
        wR = 1 / P[t][respondents]
        wM = 1 / P[t][missing]
        wA = 1 / (P[t][recovered] * Q[t][recovered])
        pR = np.sum(wR) / (np.sum(wR) + np.sum(wM))
        meanR = np.average(Y[t][respondents], weights=wR)
        meanM = np.average(Y[t][recovered], weights=wA)
        means.append(float(pR * meanR + (1-pR) * meanM))
    return np.asarray(means)


def feasible_temporal_candidates(annual: np.ndarray, external_nugget: float | None = None) -> dict:
    """Development-only grid fitting; oracle covariance prohibited in caller."""
    x = np.asarray(annual, float)
    T = len(x)
    if T not in YEARS or not np.all(np.isfinite(x)):
        raise NonIdentified("unsupported annual inference frame")
    X = np.column_stack((np.ones(T), np.arange(T) >= T // 2))
    lag = np.abs(np.subtract.outer(np.arange(T), np.arange(T)))
    options = {"iid_control": [], "ar1_zero_nugget": [], "ar1_ridge": []}
    for rho in (-0.2,0,0.15,0.35,0.55,0.7,0.85,0.92):
        for nugget in (0.0,0.2,0.4,0.6,0.8):
            C = (1-nugget)*rho**lag + nugget*np.eye(T)
            W = np.linalg.solve(C, X)
            V = np.linalg.inv(X.T @ W)
            bhat = V @ (W.T @ x)
            err = x-X@bhat
            scale = max(float(err @ np.linalg.solve(C,err))/(T-2), 1e-10)
            objective = float(np.linalg.slogdet(C)[1]+np.linalg.slogdet(X.T@W)[1]+(T-2)*np.log(scale))
            value = dict(beta=float(bhat[1]), se=float(np.sqrt(scale*V[1,1])),
                         rho=float(rho), nugget_fraction=float(nugget),
                         estimated_nuisance=True, objective=objective)
            if rho == 0 and nugget == 0:
                options["iid_control"].append((objective,value))
            if nugget == 0:
                options["ar1_zero_nugget"].append((objective,value))
            options["ar1_ridge"].append((objective+nugget*nugget+0.3*(rho/.92)**2,value))
    result = {key:min(candidates,key=lambda item:item[0])[1] for key,candidates in options.items()}
    if external_nugget is not None:
        # Scalar must come from a separately authenticated measurement study.
        raise NonIdentified("external nugget cannot be supplied from simulator or oracle")
    result["external_nugget"] = dict(status="WITHHELD_EXTERNAL_MEASUREMENT_REQUIRED")
    result["union_sensitivity"] = dict(status="DESIGN_ONLY_NOT_CALIBRATED")
    return result


def develop_smoke(config: dict, repetitions: int) -> dict:
    verify_design(config)
    if not 1 <= repetitions <= 5:
        raise ValueError("only bounded dev plumbing smoke is permitted before v3 freeze")
    attempted = completed = refusals = 0
    for r in range(repetitions):
        for response in ("mar", "audited_mnar", "unaudited_mnar"):
            attempted += 1
            observed, _evaluation_only = simulate(16,"two_of_three",response,.65,.15,
                        safe_seed(f"smoke|{r}|{response}"))
            try:
                annual = audited_year_means(observed)
                fits = feasible_temporal_candidates(annual)
                if not all(np.isfinite(fits[m]["se"]) and fits[m]["estimated_nuisance"]
                           for m in ("iid_control","ar1_zero_nugget","ar1_ridge")):
                    raise ValueError("invalid feasible numeric fit")
                completed += 1
            except NonIdentified:
                refusals += 1
    return dict(status="DEVELOPMENT_PLUMBING_ONLY_NOT_CALIBRATION", attempts=attempted,
                completed=completed, refused=refusals, holdout_attempted=0,
                empirical_models_fit=0, accepted_methods=[], statistical_acceptance=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True,
                        choices=("validate", "smoke", "development", "holdout", "real"))
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--smoke-repetitions", type=int, default=1)
    args = parser.parse_args()
    if args.phase in ("holdout", "real"):
        parser.error("prohibited: no holdout/real execution exists in v3 prototype")
    config = json.loads(args.design.read_text())
    verify_design(config)
    if args.phase == "development":
        parser.error("full development requires separately approved, frozen v3 design")
    print(json.dumps({"status":"PROPOSED_NO_HOLDOUT"} if args.phase=="validate" else
                     develop_smoke(config,args.smoke_repetitions),sort_keys=True))


if __name__ == "__main__":
    main()
