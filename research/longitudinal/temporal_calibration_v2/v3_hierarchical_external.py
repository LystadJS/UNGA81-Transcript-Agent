"""Prospective V3 DEVELOPMENT ONLY: empirical-Bayes year propensity and external scale.

DO NOT use for original UN texts or real 2008-2023 inference.
This module reads invented observed arrays and wholly separate independent
synthetic calibration samples; no truth covariance enters feasible fitting.

Hierarchical estimator: two-stage measurement-error-adjusted Gaussian REML
for latent annual response intercepts, followed by penalized annual-logit
refit. Estimated nuisance variance and AR1 rho are *plug-in*, not integrated,
and the gamma Hessian is therefore an uncalibrated sensitivity diagnostic.

External covariance bound: independent normal source-calibration replicate
variance one-sided upper confidence bound plus conservative continuous
AR1/nugget variance bound with Bonferroni alpha allocation.
The 90% statement is conditional on genuine external matching, independent
Gaussian samples, an unbiased Gaussian annual contrast, and true nuisance
parameters inside the externally justified sensitivity rectangle.
No real calibration-source authentication occurs in this module.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import chi2, norm

from .v3_nuisance import IdentificationFailure
from .v3_serial_partial import _design, _fit_years
from .v3_finite_year_continuous import continuous_covariance_upper

RHO_PROFILE_GRID = (0.0, 0.35, 0.7, 0.88)
YEAR_NUGGET_GRID = (0.0, 0.25, 0.50)
YEAR_VARIANCE_GRID = (0.05, 0.2, 0.6, 1.5)
ALPHA_TOTAL = 0.10
ALPHA_CALIBRATION = 0.025
ALPHA_CONTRAST = ALPHA_TOTAL-ALPHA_CALIBRATION
SOURCE_SCHEMA="un.w4.v3.synthetic-external-scale-calibration.v1"


def _centered_precision(C):
    one=np.ones(C.shape[0])
    try:
        invone=np.linalg.solve(C,one)
        denominator=float(one@invone)
        inv=np.linalg.inv(C)
    except np.linalg.LinAlgError as e:
        raise IdentificationFailure("singular annual covariance precision") from e
    if denominator<=0 or not np.isfinite(denominator):
        raise IdentificationFailure("annual mean curvature degeneracy")
    P=inv-np.outer(invone,invone)/denominator
    return .5*(P+P.T),invone/denominator


def estimate_year_effects_covariance(alpha_hat,conditional_alpha_variance):
    """Pseudo-REML for observed FE intercepts, never oracle year covariance."""
    a=np.asarray(alpha_hat,dtype=float)
    v=np.asarray(conditional_alpha_variance,dtype=float)
    T=len(a)
    if T not in (16,24,32) or v.shape!=(T,) or not np.all(np.isfinite(a)) or \
       not np.all(np.isfinite(v)) or np.any(v<=0):
        raise IdentificationFailure("invalid annual-intercept measurement uncertainty")
    lag=np.abs(np.subtract.outer(np.arange(T),np.arange(T)))
    I=np.eye(T)
    options=[]
    for rho in RHO_PROFILE_GRID:
        for nugget in YEAR_NUGGET_GRID:
            R=(1-nugget)*rho**lag+nugget*I
            for var in YEAR_VARIANCE_GRID:
                C=var*R+np.diag(v)
                try:
                    P,mean_coeff=_centered_precision(C)
                    sign,logdet=np.linalg.slogdet(C)
                    mean_info=float(np.ones(T)@np.linalg.solve(C,np.ones(T)))
                    if sign<=0 or mean_info<=0:
                        raise IdentificationFailure("non-positive covariance determinant")
                    objective=float(logdet+math.log(mean_info)+a@P@a)
                    if not np.isfinite(objective):
                        raise IdentificationFailure("nonfinite annual random-effect REML")
                except (IdentificationFailure,np.linalg.LinAlgError,ValueError):
                    continue
                options.append((objective,rho,nugget,var))
    if len(options)<2:
        raise IdentificationFailure("hierarchical annual covariance profile has no support")
    options.sort()
    objective,rho,nugget,var=options[0]
    gap=float(options[1][0]-objective)
    return {"rho_hat":float(rho),"year_nugget_fraction_hat":float(nugget),
        "annual_effect_variance_hat":float(var),"profile_min":float(objective),
        "second_best_gap":gap,"weakly_identified":bool(gap<2),
        "rho_boundary":bool(rho in (RHO_PROFILE_GRID[0],RHO_PROFILE_GRID[-1])),
        "variance_boundary":bool(var in (YEAR_VARIANCE_GRID[0],YEAR_VARIANCE_GRID[-1])),
        "profile_fits_available":len(options),
        "nuisance_estimated_from_observed_year_intercepts":True,
        "nuisance_recovery_certified":False}


def hierarchical_conditional_gamma(observed:dict):
    """Two-step empirical Bayes gamma fitted from audited *observed* outcomes.

    Profile nuisance from annual FE intercepts with approximate independent
    error variance 1/H_aa. Historical source/audit dependencies are not
    certified; gamma diagnostic SE excludes nuisance-estimation uncertainty.
    """
    vals,labels,w,year,T=_design(observed)
    fe=_fit_years(vals,labels,w,year,T)
    a=fe["intercept_by_year"]
    p=expit(a[year]+fe["gamma_hat"]*vals)
    information=np.bincount(year,weights=w*p*(1-p),minlength=T)
    if np.any(information<1e-6):
        raise IdentificationFailure("insufficient annual random-effect measurement support")
    nuisance=estimate_year_effects_covariance(a,1/information)
    lag=np.abs(np.subtract.outer(np.arange(T),np.arange(T)))
    rho=nuisance["rho_hat"]
    lam=nuisance["year_nugget_fraction_hat"]
    C=nuisance["annual_effect_variance_hat"]*((1-lam)*rho**lag+lam*np.eye(T))
    precision,_=_centered_precision(C)

    center=float(np.average(vals,weights=w))
    scale=float(np.sqrt(np.average((vals-center)**2,weights=w)))
    if not np.isfinite(scale) or scale<1e-8:
        raise IdentificationFailure("no within-year slope variation")
    xs=(vals-center)/scale
    theta0=np.r_[a+fe["gamma_hat"]*center,fe["gamma_hat"]*scale]
    def objective(theta):
        linear=theta[year]+theta[-1]*xs
        residual=w*(expit(linear)-labels)
        loss=float(np.sum(w*(np.logaddexp(0,linear)-labels*linear)))
        grad=np.zeros(T+1)
        np.add.at(grad,year,residual)
        grad[-1]=float(np.sum(residual*xs))
        penalty=precision@theta[:T]
        loss+=.5*float(theta[:T]@penalty)
        grad[:T]+=penalty
        return loss,grad
    opt=minimize(objective,theta0,method="L-BFGS-B",jac=True,
                 options={"maxiter":260,"ftol":1e-11,"gtol":1e-6})
    if not opt.success and np.max(np.abs(opt.jac))>1e-3:
        raise IdentificationFailure("hierarchical response refit not converged")
    theta=opt.x
    prob=expit(theta[year]+theta[-1]*xs)
    curv=w*prob*(1-prob)
    h_alpha=np.diag(np.bincount(year,weights=curv,minlength=T))+precision
    h_cross=np.bincount(year,weights=curv*xs,minlength=T)
    h_slope=float(np.sum(curv*xs*xs))
    try:
        projected=h_slope-h_cross@np.linalg.solve(h_alpha,h_cross)
    except np.linalg.LinAlgError as e:
        raise IdentificationFailure("hierarchical slope information singular") from e
    if projected<=1e-8 or not np.isfinite(projected):
        raise IdentificationFailure("hierarchical gamma not identified from audited outcomes")
    return {"gamma_hat":float(theta[-1]/scale),
        "conditional_FE_gamma_hat":float(fe["gamma_hat"]),
        "gamma_hessian_se_diagnostic":float(1/(math.sqrt(projected)*scale)),
        "method":"two_stage_empirical_bayes_AR1_year_intercepts",
        "years":T,"year_rho_hat":nuisance["rho_hat"],
        "year_nugget_fraction_hat":nuisance["year_nugget_fraction_hat"],
        "year_effect_variance_hat":nuisance["annual_effect_variance_hat"],
        "nuisance_profile_gap":nuisance["second_best_gap"],
        "nuisance_weakly_identified":nuisance["weakly_identified"],
        "nuisance_on_boundary":bool(nuisance["rho_boundary"] or nuisance["variance_boundary"]),
        "nuisance_estimated_not_oracle":True,"estimation_is_two_stage":True,
        "all_source_and_audit_outcomes_observed_or_randomly_recovered":True,
        "gamma_interval_calibrated":False,
        "year_serial_dependence_uncertainty_certified":False,
        "historical_source_audit_satisfied":False,
        "real_fit_authorized":False,"holdout_attempted":0}


def external_scale_upper(calibration:dict, *, target_design_id:str):
    """One-sided chi-square upper variance receipt from INDEPENDENT synthetic worlds.

    Requires complete independent Gaussian calibration draws from a matching
    marginal annual-year estimand, not a mere independent textual source.
    This cannot verify genuine empirical independence or historical matching.
    """
    if not isinstance(calibration,dict) or calibration.get("schema")!=SOURCE_SCHEMA or \
       calibration.get("synthetic_development_only") is not True:
        raise IdentificationFailure("independent synthetic external calibration contract absent")
    for key in ("independent_world_samples","same_year_quantity","independent_gaussian",
                "same_scale_population","same_representation","same_year_definition"):
        if calibration.get(key) is not True:
            raise IdentificationFailure("external covariance calibration provenance or comparability absent")
    if calibration.get("design_id")!=target_design_id or \
       not isinstance(target_design_id,str) or not target_design_id:
        raise IdentificationFailure("external calibration population/representation mismatch")
    sample=np.asarray(calibration.get("values",[]),dtype=float)
    if sample.ndim!=1 or not 20<=len(sample)<=1000 or not np.all(np.isfinite(sample)):
        raise IdentificationFailure("independent external calendar-scale replicates insufficient")
    variance=float(np.var(sample,ddof=1))
    if not np.isfinite(variance) or variance<=1e-12:
        raise IdentificationFailure("degenerate external calendar-year variance")
    upper=float((len(sample)-1)*variance/chi2.ppf(ALPHA_CALIBRATION,len(sample)-1))
    if not np.isfinite(upper) or upper<=variance:
        raise IdentificationFailure("invalid one-sided external year-scale confidence bound")
    return {"method":"independent_world_chi_square_upper",
        "variance_estimate":variance,"variance_upper":upper,
        "independent_world_count":len(sample),
        "alpha_calibration":ALPHA_CALIBRATION,
        "alpha_contrast":ALPHA_CONTRAST,
        "provenance":"SYNTHETIC_INDEPENDENT_WORLDS_ONLY",
        "conditional_on_independent_gaussian_calibration":True,
        "externally_authenticated_real_world":False,
        "real_fit_authorized":False}


def bonferroni_continuous_covariance(annual,calibration:dict, *,
                                   rho_range, nugget_fraction_range,
                                   target_design_id:str):
    """95%-scale upper plus 92.5%-contrast -> at least 90% *if assumptions hold*.

    Union bound: P(scale exceeds upper) <= .025 and P(normal contrast outside
    z_0.9625 interval, with genuine covariance inside set) <= .075;
    combined noncoverage <= .10. No real source meets those requirements here.
    """
    y=np.asarray(annual,float)
    if y.ndim!=1 or len(y) not in (16,24,32) or not np.all(np.isfinite(y)):
        raise IdentificationFailure("invalid annual year observations for sensitivity")
    external=external_scale_upper(calibration,target_design_id=target_design_id)
    shape=continuous_covariance_upper(
        years=len(y),rho_range=rho_range,nugget_fraction_range=nugget_fraction_range,
        external_total_scale_upper=external["variance_upper"],
        external_independent_provenance=True)
    midpoint=len(y)//2
    contrast=float(np.mean(y[midpoint:])-np.mean(y[:midpoint]))
    critical=float(norm.ppf(1-ALPHA_CONTRAST/2))
    half=critical*math.sqrt(shape["upper_variance"])
    return {"method":"bonferroni_independent_scale_continuous_AR1",
        "estimate":contrast,"lower":float(contrast-half),"upper":float(contrast+half),
        "width":float(2*half),"critical_value":critical,
        "alpha_total_assumed":ALPHA_TOTAL,
        "alpha_external_scale":ALPHA_CALIBRATION,
        "alpha_gaussian_contrast":ALPHA_CONTRAST,
        "rho_range":shape["rho_range"],
        "nugget_fraction_range":shape["nugget_fraction_range"],
        "scale_upper":external["variance_upper"],
        "external_replicate_count":external["independent_world_count"],
        "conditional_90_bound_if_all_assumptions_hold":True,
        "target_unbiased_gaussian_assumption_verified":False,
        "historical_source_scale_verified":False,
        "full_year_nugget_identified":False,
        "statistical_freeze_accepted":False,
        "real_fit_authorized":False,"holdout_attempted":0}
