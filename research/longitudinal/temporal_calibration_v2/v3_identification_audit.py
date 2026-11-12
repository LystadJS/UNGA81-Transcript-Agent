"""Independent, source-free prospective v3 identification audit.

Deterministic mathematical counterexamples only. Does not import a simulator,
execute any holdout, refit source models or mutate frozen v2 protocols.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.special import expit, logit
from .v3_serial_partial import RHO_NARROW, NUGGET_NARROW

SCHEMA = "un.w4.v3.prospective-identification-review.v1"


def conditional_vs_marginal_gamma(*, gamma=-1.25, year_intercepts=(-1.5, 1.5)):
    """Exact two-point year-effect mixture witnesses logistic noncollapsibility."""
    if len(year_intercepts) != 2 or not all(np.isfinite(x) for x in (*year_intercepts, gamma)):
        raise ValueError("finite two-point intercept distribution required")
    if gamma == 0:
        raise ValueError("nonzero conditional slope required to witness noncollapsibility")
    alpha = np.asarray(year_intercepts, dtype=float)
    p_lo = float(np.mean(expit(alpha-gamma)))
    p_hi = float(np.mean(expit(alpha+gamma)))
    marginal_slope = float((logit(p_hi)-logit(p_lo))/2)
    return dict(conditional_gamma=float(gamma), marginal_logit_contrast=marginal_slope,
                absolute_difference=float(abs(marginal_slope-gamma)),
                conditioning="fixed year intercept versus mixture of year intercepts",
                identical_estimand=False, real_fit_authorized=False)


def no_audit_mnar_counterexample(*, observed_response_rate=.5,
                                 positive_given_response=.7,
                                 missing_positive_fractions=(.2,.8)):
    """Two nonresponse populations induce different slopes with identical observed data.

    With binary Y, the odds contrast logit P(R=1|Y=1) minus logit
    P(R=1|Y=0) is a saturated logistic slope. Missing Y distribution
    is not learned from observed response/observed respondent outcomes.
    """
    if not 0<observed_response_rate<1 or not 0<positive_given_response<1:
        raise ValueError("valid observed response table required")
    results=[]
    for m in missing_positive_fractions:
        if not 0<m<1:
            raise ValueError("unobserved outcome composition must be interior")
        positive_responding = observed_response_rate*positive_given_response
        negative_responding = observed_response_rate*(1-positive_given_response)
        positive_missing = (1-observed_response_rate)*m
        negative_missing = (1-observed_response_rate)*(1-m)
        gamma = math.log(positive_responding/positive_missing) - math.log(
            negative_responding/negative_missing)
        results.append(dict(missing_positive_fraction=float(m),
                            observed_response_rate=observed_response_rate,
                            positive_among_respondents=positive_given_response,
                            compatible_gamma=float(gamma)))
    return dict(candidates=results,
                observed_data_indistinguishable=True,
                gamma_point_identified=False,
                independent_randomized_missing_outcome_audit_required=True)


def year_nugget_measurement_alias(*, years=16, rho=.65,
                                  ar1_variance=.04, year_nugget=.025,
                                  measurement_error=.0144,
                                  transfer=.01):
    """Two admissible variance decompositions give exactly the same annual covariance."""
    if type(years) is not int or years<8 or years>64 or not 0<rho<.95:
        raise ValueError("invalid covariance horizon/correlation")
    if min(ar1_variance,year_nugget,measurement_error,transfer)<0 or transfer>year_nugget:
        raise ValueError("nonnegative variance decomposition required")
    lag = np.abs(np.subtract.outer(np.arange(years),np.arange(years)))
    ar = ar1_variance*(rho**lag)
    cov_a = ar+(year_nugget+measurement_error)*np.eye(years)
    cov_b = ar+(year_nugget-transfer+measurement_error+transfer)*np.eye(years)
    max_difference=float(np.max(np.abs(cov_a-cov_b)))
    return dict(years=years,
                first_variance_decomposition=[year_nugget,measurement_error],
                second_variance_decomposition=[year_nugget-transfer,measurement_error+transfer],
                max_absolute_covariance_difference=max_difference,
                intrinsic_nugget_identified_from_annual_covariance=False,
                external_measurement_error_may_break_exact_alias=True,
                finite_year_recovery_certified=False)


def nuisance_grid_truth_witness(*, rho=.65, process_variance=.04,
                               nugget_variance=.025, measurement_variance=.0144):
    """Demonstrates that proposed narrow sensitivity *grid* omits known DGP covariance.

    Only a mathematical development counterexample; simulator generating truth
    is not passed to any feasible estimator.
    """
    total=process_variance+nugget_variance+measurement_variance
    if total<=0 or min(process_variance,nugget_variance,measurement_variance)<0:
        raise ValueError("invalid variance proportions")
    lam=(nugget_variance+measurement_variance)/total
    inside_hull=min(NUGGET_NARROW)<=lam<=max(NUGGET_NARROW) and         min(RHO_NARROW)<=rho<=max(RHO_NARROW)
    exactly_on_grid=(lam in NUGGET_NARROW and rho in RHO_NARROW)
    return dict(evaluator_true_effective_diagonal_fraction=float(lam),
                assumed_narrow_lambda_max=float(max(NUGGET_NARROW)),
                true_nuisance_in_narrow_range=bool(inside_hull),
                true_covariance_is_grid_point=bool(exactly_on_grid),
                observed_beta_sensitivity_hit_does_not_validate_nuisance_set=True,
                finite_discrete_grid_is_not_continuous_identification_region=True)


def independent_freeze_decision(candidate: dict, design: dict):
    """Fail-closed identification acceptance; cannot authorize v3 or v2 fitting."""
    if candidate.get("status")!="UNAPPROVED_DESIGN_CANDIDATE_NOT_FROZEN":
        raise ValueError("unexpected prospective v3 candidate status")
    if design.get("status")!="PROPOSED_NOT_FROZEN" or design.get("primary_years")!=16:
        raise ValueError("unapproved or invalid v3 estimand/design identity")
    if candidate.get("holdout_run") is not False or design.get("holdout_authorized") is not False:
        raise ValueError("holdout execution must remain prohibited")
    if candidate.get("real_fit_authorized") is not False or design.get("real_fit_authorized") is not False:
        raise ValueError("empirical fitting must remain prohibited")
    return dict(
        schema=SCHEMA,
        status="STATISTICAL_FREEZE_NOT_ACCEPTED",
        engineering_source_integrity="REVIEWABLE_NOT_A_SCIENTIFIC_FREEZE",
        year_fixed_effects_estimand="CONDITIONAL_WITHIN_YEAR_LOGIT_GAMMA_ONLY",
        marginal_gamma_identified=False,
        serial_year_gamma_interval_calibrated=False,
        genuine_randomized_real_outcome_audit_verified=False,
        intrinsic_calendar_nugget_identified=False,
        hypothetical_covariance_union_coverage_calibrated=False,
        externally_defended_nuisance_ranges_approved=False,
        independent_holdout_producer_frozen=False,
        source_comparability_approved=False,
        holdout_executed=False,
        v2_frozen_methods_changed=False,
        empirical_fit_authorized=False,
        coordinator_merge_authorized=False,
    )
