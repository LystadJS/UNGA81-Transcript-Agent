"""Synthetic-only, fail-closed null calibration. Python 3.10+, standard library."""
import hashlib
import json
import math
import random
from collections import defaultdict

PROTOCOL = "un.null-calibration.synthetic.v1"

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def generate(seed, groups=12, per_group=8, signal=0., imbalance=False, misspecified=False):
    """Group-correlated token counts; nuisance prevalence/length and optional latent signal."""
    if groups < 2 or per_group < 2:
        raise ValueError("Insufficient groups/observations")
    rng = random.Random(seed)
    rows = []
    for g in range(groups):
        group_bias = rng.gauss(0, 1.5)
        n = per_group * (4 if imbalance and g == 0 else 1)
        for i in range(n):
            length = rng.randint(20, 120)
            latent = (1 if g % 2 else -1) if signal else 0
            dependence = group_bias * (1 + (g % 3) if misspecified else 1)
            x = [sum(rng.random() < max(.01, min(.99, p)) for _ in range(length))
                 for p in (.20 + .07 * dependence + signal * latent * .12,
                           .35 - .04 * dependence - signal * latent * .12,
                           .10 + .03 * dependence)]
            rows.append(dict(id=f"g{g}-s{i}", group=f"g{g}", speech=f"g{g}-s{i//2}",
                             length=length, tokens=x, representation="synthetic-counts-v1"))
    return rows

def consensus(fits, ids, family_weights=None):
    """Equal method-family votes; within family each setting has equal weight.
    A fit is {family, labels: {id: integer label or None}, status}.
    Missing/unassigned observations are never silently treated as separate clusters.
    """
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("Duplicate/empty IDs")
    families = defaultdict(list)
    ledger = []
    for k, fit in enumerate(fits):
        status = fit.get("status", "failed")
        labels = fit.get("labels", {})
        if status == "converged" and (not isinstance(labels, dict) or set(labels) != set(ids)):
            status = "failed"
        if status not in ("converged", "failed", "nonconverged", "skipped"):
            raise ValueError("Invalid fit status")
        ledger.append(dict(index=k, family=fit.get("family"), status=status,
                           assigned=sum(v is not None and v != 0 for v in labels.values()) if status == "converged" else 0,
                           unassigned=sum(v is None or v == 0 for v in labels.values()) if status == "converged" else len(ids)))
        if status == "converged":
            families[fit["family"]].append(labels)
    if not families:
        return dict(pairs=[], ledger=ledger, ready=False, reason="no_converged_fits")
    weights = family_weights or {f: 1. for f in families}
    if any(f not in weights or weights[f] <= 0 or not math.isfinite(weights[f]) for f in families):
        raise ValueError("Invalid family weights")
    pairs = []
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            numerator = denominator = 0.
            opportunities = 0
            for family, models in families.items():
                w = weights[family] / len(models)
                for labels in models:
                    u, v = labels[ids[a]], labels[ids[b]]
                    if u in (None, 0) or v in (None, 0):
                        continue
                    opportunities += 1
                    denominator += w
                    numerator += w * (u == v)
            pairs.append(dict(a=ids[a], b=ids[b], coassignment=numerator / denominator if denominator else None,
                              eligible_fit_pairs=opportunities, eligible_weight=denominator))
    return dict(pairs=pairs, ledger=ledger, ready=True, reason=None)

def calibrate(development, holdout, alpha=.05, minimum_groups=8, minimum_holdout=100):
    """Prospective independent simulation threshold, then one-shot holdout evaluation.
    Inputs are records {seed, statistic, groups, nuisance_converged, identifiable,
    generator_hash, estimator_hash}; independent holdout seeds are mandatory.
    """
    if not 0 < alpha < 1:
        raise ValueError("Invalid alpha")
    reasons = []
    if len(holdout) < minimum_holdout:
        reasons.append("insufficient_holdout_simulations")
    if not development:
        reasons.append("no_development")
    dev_seeds = [x["seed"] for x in development]
    test_seeds = [x["seed"] for x in holdout]
    if len(set(dev_seeds)) != len(dev_seeds) or len(set(test_seeds)) != len(test_seeds) or set(dev_seeds) & set(test_seeds):
        reasons.append("seed_overlap_or_duplicate")
    for r in development + holdout:
        if r["groups"] < minimum_groups:
            reasons.append("small_effective_group_count")
        if not r["nuisance_converged"]:
            reasons.append("nuisance_estimation_failure")
        if not r["identifiable"]:
            reasons.append("weak_identification")
        if not math.isfinite(r["statistic"]):
            reasons.append("nonfinite_statistic")
    if len({r["generator_hash"] for r in development + holdout}) != 1:
        reasons.append("generator_mismatch")
    if len({r["estimator_hash"] for r in development + holdout}) != 1:
        reasons.append("estimator_mismatch")
    if reasons:
        return dict(ready=False, reasons=sorted(set(reasons)), attempted_development=len(development),
                    attempted_holdout=len(holdout), threshold=None, false_positive_rate=None)
    sorted_dev = sorted(r["statistic"] for r in development)
    rank = math.ceil((len(sorted_dev) + 1) * (1 - alpha))
    if rank > len(sorted_dev):
        return dict(ready=False, reasons=["insufficient_development_resolution"], threshold=None,
                    attempted_development=len(development), attempted_holdout=len(holdout))
    threshold = sorted_dev[rank - 1]
    exceed = sum(r["statistic"] > threshold for r in holdout)
    p = exceed / len(holdout)
    se = math.sqrt(p * (1 - p) / len(holdout))
    return dict(ready=True, reasons=[], threshold=threshold, alpha=alpha,
                attempted_development=len(development), attempted_holdout=len(holdout),
                exceedances=exceed, false_positive_rate=p,
                approximate_95pct_interval=[max(0, p - 1.96 * se), min(1, p + 1.96 * se)],
                strict_exceedance=True, publication_eligible=False)
