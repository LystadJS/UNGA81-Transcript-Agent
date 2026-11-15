"""V3 development-only grouped gamma diagnostics and external replicate calibration.

No holdout, historical source reads, empirical fit, or statistical approval.
Year-cluster sandwich is a *conditional diagnostic*, not valid calibrated CI.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.special import expit
from .v3_nuisance import IdentificationFailure, response_gamma, replicate_nugget

def grouped_gamma_diagnostic(observed: dict, *, min_years: int = 16):
    """Weighted estimating-equation sandwich grouped by whole calendar year.

    Reuses the audited-response point estimate, retaining both stages' weights.
    Independence of calendar years is NOT established under AR1; this sandwich
    is deliberately descriptive and its interval is withheld.
    """
    fitted = response_gamma(observed)
    y=np.asarray(observed["value"],float)
    r=np.asarray(observed["responded"],bool)
    a=np.asarray(observed["audited"],bool)
    pi=np.asarray(observed["inclusion_probability"],float)
    q=np.asarray(observed["independent_audit_probability"],float)
    if y.shape[0]<min_years:
        raise IdentificationFailure("insufficient distinct calendar-year clusters")
    selected=r|a
    p=expit(fitted["intercept"]+fitted["gamma"]*y[selected])
    x=np.column_stack([np.ones(int(selected.sum())),y[selected]])
    w=1.0/pi[selected]
    labels=r[selected].astype(float)
    w[~r[selected]]/=q[selected][~r[selected]]
    curvature=p*(1-p)*w
    bread=(x.T*curvature)@x
    if np.linalg.eigvalsh(bread)[0]<=1e-10 or np.linalg.cond(bread)>1e9:
        raise IdentificationFailure("singular clustered response bread matrix")
    scores=(x.T*(w*(labels-p))).T
    annual_ids=np.broadcast_to(np.arange(y.shape[0])[:,None,None],y.shape)[selected]
    groups=np.stack([scores[annual_ids==year].sum(axis=0) for year in range(y.shape[0])])
    if np.sum(np.linalg.norm(groups,axis=1)>0)<min_years:
        raise IdentificationFailure("too few supported year score blocks")
    center=groups-groups.mean(axis=0)
    meat=(center.T@center)*y.shape[0]/(y.shape[0]-1)
    inv=np.linalg.inv(bread)
    variance=inv@meat@inv
    variance=(variance+variance.T)/2
    if not np.all(np.isfinite(variance)) or variance[1,1]<=0:
        raise IdentificationFailure("unstable year-score sandwich")
    return dict(gamma=fitted["gamma"],gamma_year_cluster_se=float(np.sqrt(variance[1,1])),
                distinct_calendar_years=int(y.shape[0]),
                independent_years_verified=False,
                interval_calibrated=False, interval_eligible=False,
                serial_year_dependence_accounted_for=False,
                response_model_misspecification_tested=False,
                real_data_fit_authorized=False)

def paired_measurement_experiment(*, seed: int, repetitions: int=24,
                                  years: int=24, error_sd: float=0.20,
                                  shared_sd: float=0.0):
    """Invented development-only calibration with independent evaluator truth.

    Two measurements share latent year signal, and may share correlated errors.
    Shared errors violate the replicate-independence assumption and must be
    treated as a *misidentification stress*, not accepted external nugget.
    """
    if not isinstance(seed,int) or not (8<=repetitions<=128) or not (8<=years<=48):
        raise ValueError("development-only bounded replicate experiment required")
    if not (0<error_sd<=1) or not (0<=shared_sd<=1):
        raise ValueError("invalid measurement stress settings")
    rng=np.random.default_rng(seed)
    estimates=[]; failures=0
    for i in range(repetitions):
        latent=rng.normal(size=years)
        shared=rng.normal(scale=shared_sd,size=years)
        a=latent+shared+rng.normal(scale=error_sd,size=years)
        b=latent+shared+rng.normal(scale=error_sd,size=years)
        receipt=dict(independent_replicate_provenance=shared_sd==0,
                     same_latent_year_quantity=True,years=list(range(years)),
                     first=a.tolist(),second=b.tolist())
        try:
            estimates.append(replicate_nugget(receipt)["measurement_noise_variance"])
        except IdentificationFailure:
            failures+=1
    target=error_sd**2
    return dict(status="DEVELOPMENT_ONLY_NOT_CONFIRMATORY",
                attempted=repetitions,completed=len(estimates),refused=failures,
                measurement_noise_truth_known_to_evaluator_only=target,
                estimate_bias=float(np.mean(estimates)-target) if estimates else None,
                estimate_rmse=float(np.sqrt(np.mean((np.asarray(estimates)-target)**2))) if estimates else None,
                independent_replicate_assumption=shared_sd==0,
                calendar_year_nugget_recovered=False,
                accepted_nuisance_models=[],holdout_attempted=0,
                real_fit_authorized=False,statistical_acceptance=False)
