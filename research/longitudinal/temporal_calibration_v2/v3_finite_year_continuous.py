"""Prospective v3 finite-year DEVELOPMENT diagnostics: no holdout, no empirical fit.

1. Refit conditional year-fixed-effect gamma on circular *whole-year* blocks.
2. Bound a two-era contrast's variance over CONTINUOUS compact AR1/nugget
   nuisance ranges by conservative polynomial term bounds.

Neither procedure is a currently validated UN confidence interval. The variance
bound is mathematical conditional on an externally justified upper scale and
correct Gaussian/unbiased annual observation model; no real calibration exists.
"""
from __future__ import annotations
import math
from statistics import NormalDist
import numpy as np
from .v3_nuisance import IdentificationFailure
from .v3_serial_partial import estimate_serial_response

Z90=NormalDist().inv_cdf(.95)
SOURCE_FIELDS=("value","included","responded","audited","at_risk",
               "inclusion_probability","independent_audit_probability")

def finite_year_block_refit(observed:dict, *, seed:int, repetitions:int=24,
                            block_years:int=4, min_success_fraction:float=.75):
    """Circular moving-*year* block bootstrap with full year-FE response refits.

    Repeated actors across independently redrawn blocks, source-selection
    variance, estimated response-year dependence, and finite T are NOT
    calibrated by this procedure. Percentile/basic bounds are diagnostics only.
    All bootstrap optimizer failures remain in the returned attempt ledger.
    """
    if type(seed) is not int or type(repetitions) is not int or not 12<=repetitions<=80:
        raise IdentificationFailure("bounded development bootstrap required")
    if block_years not in (4,8) or min_success_fraction!=.75:
        raise IdentificationFailure("unapproved block length or failure tolerance")
    if not isinstance(observed,dict) or any(k not in observed for k in SOURCE_FIELDS):
        raise IdentificationFailure("source observation fields missing")
    T=np.asarray(observed["value"]).shape[0]
    if T not in (16,24,32) or T<3*block_years:
        raise IdentificationFailure("insufficient whole-year blocks")
    baseline=estimate_serial_response(observed,"year_fixed_effects",lag=2)
    rng=np.random.default_rng(seed)
    estimated=[];failures=[]
    for i in range(repetitions):
        starts=rng.integers(0,T,size=math.ceil(T/block_years))
        indices=np.concatenate([(s+np.arange(block_years))%T for s in starts])[:T]
        draw={k:(np.asarray(v)[indices].copy() if k in SOURCE_FIELDS else v)
              for k,v in observed.items()}
        try:
            fit=estimate_serial_response(draw,"year_fixed_effects",lag=2)
            gamma=float(fit["gamma_hat"])
            if not np.isfinite(gamma):
                raise IdentificationFailure("nonfinite gamma from whole-year refit")
            estimated.append(gamma)
        except (IdentificationFailure,ValueError,ArithmeticError,np.linalg.LinAlgError) as e:
            failures.append({"attempt":i,"reason":type(e).__name__+":"+str(e)})
    required=math.ceil(repetitions*min_success_fraction)
    if len(estimated)<required:
        return dict(method="circular_year_block_refit",block_years=block_years,
            attempted=repetitions,completed=len(estimated),failed=len(failures),
            failure_ledger=failures,status="REFUSED_INSUFFICIENT_RESAMPLED_YEAR_SUPPORT",
            gamma_hat=baseline["gamma_hat"],gamma_se_diagnostic=None,
            diagnostic_low=None,diagnostic_high=None,
            t16_interval_calibrated=False,real_fit_authorized=False,
            holdout_attempted=0)
    vals=np.array(estimated)
    point=float(baseline["gamma_hat"])
    q05,q95=np.quantile(vals,[.05,.95])
    # Basic bootstrap interval; finite T, shared actor and response design
    # concerns mean this is NOT a calibrated confidence interval.
    return dict(method="circular_year_block_refit",block_years=block_years,
        attempted=repetitions,completed=len(estimated),failed=len(failures),
        failure_ledger=failures,status="DEVELOPMENT_DIAGNOSTIC_ONLY",
        gamma_hat=point,gamma_se_diagnostic=float(np.std(vals,ddof=1)),
        diagnostic_low=float(2*point-q95),
        diagnostic_high=float(2*point-q05),
        t16_interval_calibrated=False,real_fit_authorized=False,
        holdout_attempted=0, actor_dependence_preserved_across_resampled_years=False)


def continuous_covariance_upper(*, years:int, rho_range:tuple,
                                nugget_fraction_range:tuple,
                                external_total_scale_upper:float|None,
                                external_independent_provenance:bool):
    """Guaranteed upper *algebraic* bound for w'C(rho,lambda)w, no gridding.

    C = scale * [(1-lambda) R_AR1(rho) + lambda I]. For fixed 2-era
    contrast weights, w'Rw is a polynomial in rho. Bound each polynomial
    term at its monotone extreme over rho in [lo,hi] subset [0,1).
    Then maximize the resulting affine upper envelope over lambda endpoints.

    A known defensible upper bound on marginal year scale is essential.
    Gaussian coverage requires an unbiased Gaussian year-contrast and the true
    nuisance/scales inside the declared set. This module cannot verify those
    empirical conditions or source-based external provenance.
    """
    if years not in (16,24,32) or not isinstance(rho_range,(list,tuple)) or \
       not isinstance(nugget_fraction_range,(list,tuple)) or \
       len(rho_range)!=2 or len(nugget_fraction_range)!=2:
        raise IdentificationFailure("invalid prospective continuous covariance frame")
    lo,hi=map(float,rho_range)
    a,b=map(float,nugget_fraction_range)
    if not (0<=lo<=hi<.95 and 0<=a<=b<=1):
        raise IdentificationFailure("invalid bounded continuous AR1/nugget region")
    if external_independent_provenance is not True or \
       external_total_scale_upper is None:
        raise IdentificationFailure("independently justified scale upper bound absent")
    if not isinstance(external_total_scale_upper,(int,float)) or not math.isfinite(
            external_total_scale_upper) or external_total_scale_upper<=0:
        raise IdentificationFailure("invalid independently declared variance-scale upper bound")
    w=np.r_[np.full(years//2,-1/(years//2)),
            np.full(years-years//2,1/(years-years//2))]
    squared=float(w@w)
    # The exact polynomial w'R(rho)w=sum(w_i²)+sum_k c_k*rho^k.
    coefficients=np.array([2*float(w[:-k]@w[k:]) for k in range(1,years)])
    terms_upper=np.where(coefficients>=0,hi**np.arange(1,years),
                         lo**np.arange(1,years))
    terms_lower=np.where(coefficients>=0,lo**np.arange(1,years),
                         hi**np.arange(1,years))
    ar_upper=float(squared+np.dot(coefficients,terms_upper))
    ar_lower=float(squared+np.dot(coefficients,terms_lower))
    if ar_upper<=0:
        raise IdentificationFailure("invalid continuous upper variance")
    max_norm=max((1-lam)*ar_upper+lam*squared for lam in (a,b))
    min_norm=min((1-lam)*ar_lower+lam*squared for lam in (a,b))
    return dict(method="continuous_termwise_AR1_nugget_variance_upper",
        years=years,rho_range=[lo,hi],nugget_fraction_range=[a,b],
        assumed_external_total_scale_upper=float(external_total_scale_upper),
        upper_variance=float(external_total_scale_upper*max_norm),
        lower_shape_bound=float(max(0,min_norm)),
        termwise_bound_guaranteed_for_all_continuous_rho=True,
        assumed_scale_upper_externally_certified_by_model=False,
        conditional_gaussian_coverage_if_assumptions_hold=True,
        empirical_coverage_calibrated=False,year_nugget_point_identified=False,
        real_fit_authorized=False,holdout_attempted=0)


def continuous_contrast_sensitivity(annual, *, rho_range=(0,.85),
                                    nugget_fraction_range=(0,.7),
                                    external_total_scale_upper=None,
                                    external_independent_provenance=False):
    """Two-era equal-year contrast ±z90*conservative worst-case variance.

    This is a hypothetical conditional sensitivity band, not an audited
    confidence interval. Never calls a true covariance or hidden response.
    """
    y=np.asarray(annual,float)
    if y.ndim!=1 or len(y) not in (16,24,32) or not np.isfinite(y).all():
        raise IdentificationFailure("invalid annual outcome or unsupported T")
    bound=continuous_covariance_upper(
        years=len(y),rho_range=rho_range,
        nugget_fraction_range=nugget_fraction_range,
        external_total_scale_upper=external_total_scale_upper,
        external_independent_provenance=external_independent_provenance)
    mid=len(y)//2
    beta=float(np.mean(y[mid:])-np.mean(y[:mid]))
    hw=Z90*math.sqrt(bound["upper_variance"])
    bound.update(beta_hat=beta,lower=float(beta-hw),upper=float(beta+hw),
                 width=float(2*hw),
                 unconditional_frequentist_coverage_claim=False,
                 source_selection_bias_included=False,
                 finite_year_gaussian_assumption_explicit=True)
    return bound


def verify_continuous_bound(bound:dict, *, rho:float, lam:float,
                            variance_scale:float):
    """Evaluator ONLY; checks no-gridding bound against independently supplied DGP.

    This never participates in estimation and has no real-data entry point.
    """
    T=bound["years"]
    if not (bound["rho_range"][0]<=rho<=bound["rho_range"][1]) or \
       not (bound["nugget_fraction_range"][0]<=lam<=bound["nugget_fraction_range"][1]):
        return dict(assumptions_hold=False,variance_bounded=None,
                    reason="true nuisance lies outside declared set")
    if variance_scale>bound["assumed_external_total_scale_upper"]:
        return dict(assumptions_hold=False,variance_bounded=None,
                    reason="true scale exceeds externally assumed upper bound")
    w=np.r_[np.full(T//2,-1/(T//2)),np.full(T-T//2,1/(T-T//2))]
    lag=np.abs(np.subtract.outer(np.arange(T),np.arange(T)))
    C=variance_scale*((1-lam)*rho**lag+lam*np.eye(T))
    variance=float(w@C@w)
    return dict(assumptions_hold=True,
                variance_bounded=variance<=bound["upper_variance"]+1e-12,
                oracle_variance_for_development_evaluator_only=variance)
