"""Synthetic-only temporal inference diagnostics. No empirical fitting entry point."""
from dataclasses import dataclass
import math
import numpy as np

@dataclass(frozen=True)
class Design:
    years: int
    rho: float
    nugget: float
    audit_probability: float
    response_slope: float = 0.0

def validate(d):
    if d.years < 8 or not (-0.95 < d.rho < 0.95) or d.nugget < 0:
        raise ValueError("invalid temporal design")
    if not (0 <= d.audit_probability <= 1):
        raise ValueError("invalid audit probability")

def covariance(t, rho, nugget, scale=1.0):
    if t < 2 or not (-0.95 < rho < 0.95) or nugget < 0 or scale <= 0:
        raise ValueError("invalid covariance")
    lag = np.abs(np.subtract.outer(np.arange(t), np.arange(t)))
    return scale * (rho ** lag + nugget * np.eye(t))

def generate(d, seed, meetings=8, speeches=12):
    validate(d)
    rng = np.random.default_rng(seed)
    shocks = rng.multivariate_normal(np.zeros(d.years), covariance(d.years, d.rho, d.nugget))
    rows = []
    for year in range(d.years):
        for meeting in range(meetings):
            included = bool(rng.random() < 0.5)
            meeting_effect = rng.normal(scale=0.35)
            for speech in range(speeches):
                outcome = float(shocks[year] + meeting_effect + rng.normal())
                response_p = float(1 / (1 + np.exp(-np.clip(-0.4 + d.response_slope * outcome, -30, 30))))
                responded = included and bool(rng.random() < response_p)
                audited = included and not responded and bool(rng.random() < d.audit_probability)
                rows.append(dict(year=year, meeting=meeting, speech=speech,
                    inclusion_probability=0.5, included=included, responded=responded,
                    audited=audited, outcome=outcome if responded or audited else None,
                    truth=outcome))
    return rows

def identifiable(rows):
    if not rows or any(r["inclusion_probability"] <= 0 for r in rows):
        return False, "missing first-stage positivity"
    missing = [r for r in rows if r["included"] and not r["responded"]]
    if missing and not any(r["audited"] for r in missing):
        return False, "outcome-dependent response not identifiable without independent audit"
    return True, "synthetic audit present; verification design still required"

def estimate_year_covariance(annual, ridge=0.1):
    """Constrained moment candidate; explicitly refuses short/weakly identified panels."""
    x = np.asarray(annual, dtype=float)
    if x.ndim != 1 or len(x) < 24 or not np.all(np.isfinite(x)):
        raise ValueError("insufficient independent calendar years for covariance recovery")
    z = x - x.mean()
    variance = float(np.mean(z*z))
    if variance < 1e-10:
        raise ValueError("degenerate year variation")
    lag1 = float(np.mean(z[1:]*z[:-1]))
    lag2 = float(np.mean(z[2:]*z[:-2]))
    if lag1 <= 0 or lag2 <= 0:
        raise ValueError("AR1 and nugget not separately identified by moments")
    rho = float(np.clip(lag2 / lag1, 0.01, 0.9))
    ar_scale = lag1 / rho
    nugget = max(0.0, variance / max(ar_scale, 1e-10) - 1)
    return dict(rho=(1-ridge)*rho, nugget=nugget, scale=ar_scale)

def metadata_compatible(a, b):
    required = ("schema_version", "source_design_id", "population_hash",
                "representation_fingerprint", "year_definition", "sampling_frame_hash")
    if not all(isinstance(a.get(k), str) and a[k] for k in required):
        raise ValueError("incomplete source-comparability metadata")
    if not all(isinstance(b.get(k), str) and b[k] for k in required):
        raise ValueError("incomplete source-comparability metadata")
    if any(a[k] != b[k] for k in required):
        raise ValueError("incompatible source cohorts; pooling refused")
    return True

def real_fit(*args, **kwargs):
    raise PermissionError("Real 2008-2023 inference prohibited; independent protocol and gates required")
