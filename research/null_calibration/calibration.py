"""Offline descriptive consensus and fail-closed synthetic scalar calibration.

Does NOT implement the frozen W1/W2 null hypothesis or qualify empirical data.
Python 3.10+, standard library only.
"""
from collections import defaultdict
import hashlib
import json
import math
import random

PROTOCOL = "un.null-calibration.synthetic.v2"


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def generate(seed, groups=12, per_group=8, signal=0., imbalance=False, misspecified=False):
    if groups < 2 or per_group < 2 or not math.isfinite(signal):
        raise ValueError("invalid synthetic design")
    rng = random.Random(seed)
    rows = []
    for g in range(groups):
        effect = rng.gauss(0, 1.5) * (1 + g % 3 if misspecified else 1)
        for i in range(per_group * (4 if imbalance and g == 0 else 1)):
            length = rng.randint(20, 120)
            topic = (1 if g % 2 else -1) if signal else 0
            prevalence = (.20 + .07 * effect + signal * topic * .12,
                          .35 - .04 * effect - signal * topic * .12,
                          .10 + .03 * effect)
            counts = [sum(rng.random() < max(.01, min(.99, p)) for _ in range(length)) for p in prevalence]
            rows.append(dict(id=f"g{g}-s{i}", group=f"g{g}", speech=f"g{g}-s{i//2}",
                             length=length, tokens=counts, representation="synthetic-counts-v1"))
    return rows


def consensus(fits, ids, family_weights=None):
    """Nested balancing: family > method > configuration > attempted replica.

    A failed or unassigned fit retains its planned denominator. Pairwise association
    is CONDITIONAL ON BOTH ASSIGNED; report unconditional assignment coverage too.
    Neither fraction is an inferential probability.
    """
    if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
        raise ValueError("duplicate or empty observation IDs")
    if not isinstance(fits, list) or not fits:
        return dict(ready=False, reason="no_attempts", pairs=[], ledger=[])
    ledger = []
    families = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    signatures = {}
    for index, fit in enumerate(fits):
        family = fit.get("family")
        if not isinstance(family, str) or not family:
            raise ValueError("missing method family")
        method = fit.get("method", "unspecified")
        config = fit.get("configuration_id", "undeclared_setting")
        seed = fit.get("seed", None)
        if not all(isinstance(v, str) and v for v in (method, config)):
            raise ValueError("invalid method/configuration ID")
        status = fit.get("status", "failed")
        if status not in ("converged", "failed", "nonconverged", "skipped"):
            raise ValueError("invalid attempted fit status")
        labels = fit.get("labels", {})
        if status == "converged":
            if not isinstance(labels, dict) or set(labels) != set(ids) or any(
                v is not None and (not isinstance(v, int) or isinstance(v, bool) or v < 0) for v in labels.values()
            ):
                status = "failed"
                labels = {}
        key = (family, method, config, seed)
        # Exact same declared seed/configuration is not another independent vote.
        if seed is not None and key in signatures:
            if signatures[key] != (status, labels):
                raise ValueError("duplicate fit identity with conflicting results")
            ledger.append(dict(index=index, family=family, method=method, configuration_id=config,
                               status="duplicate_excluded", assigned=0, unassigned=0,
                               reason="same family/method/configuration/seed"))
            continue
        if seed is not None:
            signatures[key] = (status, labels)
        assigned = sum(v is not None and v != 0 for v in labels.values()) if status == "converged" else 0
        ledger.append(dict(index=index, family=family, method=method, configuration_id=config,
                           status=status, assigned=assigned,
                           unassigned=(len(ids) - assigned) if status == "converged" else 0,
                           not_fitted=len(ids) if status != "converged" else 0))
        families[family][method][config].append((status, labels))
    planned = sum(len(settings) for methods in families.values() for configs in methods.values() for settings in configs.values())
    weights = {f: 1. for f in families} if family_weights is None else family_weights
    if set(weights) != set(families) or any(not isinstance(w, (int, float)) or w <= 0 or not math.isfinite(w) for w in weights.values()):
        raise ValueError("invalid or missing family weights")
    slots = []
    for family, methods in families.items():
        for method, configs in methods.items():
            for config, settings in configs.items():
                vote = (weights[family] / sum(weights.values())) / len(methods) / len(configs) / len(settings)
                slots.extend((family, vote, status, labels) for status, labels in settings)
    pairs = []
    for ai, a in enumerate(ids):
        for b in ids[ai+1:]:
            co = eligible = planned_weight = 0.
            assigned_fits = 0
            contributing = set()
            for family, w, status, labels in slots:
                planned_weight += w
                if status != "converged":
                    continue
                u, v = labels[a], labels[b]
                if u in (None, 0) or v in (None, 0):
                    continue
                eligible += w
                assigned_fits += 1
                contributing.add(family)
                if u == v:
                    co += w
            pairs.append(dict(a=a, b=b, coassignment=co / eligible if eligible else None,
                              eligible_fit_pairs=assigned_fits, eligible_weight=eligible,
                              planned_fit_pairs=planned, planned_weight=planned_weight,
                              assignment_coverage=eligible / planned_weight if planned_weight else None,
                              contributing_families=sorted(contributing)))
    return dict(pairs=pairs, ledger=ledger, attempted_fits=len(fits),
                unique_planned_fits=planned,
                converged_fits=sum(r["status"] == "converged" for r in ledger),
                failed_or_unfitted=sum(r["status"] in ("failed", "nonconverged", "skipped") for r in ledger),
                duplicates_excluded=sum(r["status"] == "duplicate_excluded" for r in ledger),
                ready=False, reason="descriptive_only_not_null_calibrated")


def calibrate(development, holdout, alpha=.05, minimum_groups=8, minimum_holdout=100):
    """Finite-sample development quantile, then untouched synthetic holdout.

    Failures remain in attempted denominators. No source-grounded or publication
    claim, and not a substitute for PR57's untouched fixed critical values.
    """
    if not isinstance(alpha, (float, int)) or not 0 < alpha < 1:
        raise ValueError("invalid alpha")
    reasons = []
    if not isinstance(development, list) or not isinstance(holdout, list):
        raise ValueError("development/holdout must be lists")
    if not development:
        reasons.append("no_development")
    if len(holdout) < minimum_holdout:
        reasons.append("insufficient_holdout_simulations")
    seeds = [r.get("seed") for r in development + holdout]
    if any(s is None for s in seeds) or len(set(seeds)) != len(seeds):
        reasons.append("duplicate_or_missing_seed")
    hashes = {key: {r.get(key) for r in development + holdout} for key in ("generator_hash", "estimator_hash")}
    if any(len(values) != 1 or None in values or "" in values for values in hashes.values()):
        reasons.append("missing_or_mismatched_code_identity")
    for r in development + holdout:
        if r.get("groups", 0) < minimum_groups:
            reasons.append("small_effective_group_count")
        if r.get("nuisance_converged") is not True:
            reasons.append("nuisance_estimation_failure")
        if r.get("identifiable") is not True:
            reasons.append("weak_identification")
        value = r.get("statistic")
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            reasons.append("nonfinite_or_missing_statistic")
    base = dict(attempted_development=len(development), attempted_holdout=len(holdout),
                publication_eligible=False, evaluation_role="engineering_only")
    if reasons:
        return dict(base, ready=False, reasons=sorted(set(reasons)), threshold=None, false_positive_rate=None)
    ordered = sorted(r["statistic"] for r in development)
    rank = math.ceil((len(ordered) + 1) * (1-alpha))
    if rank > len(ordered):
        return dict(base, ready=False, reasons=["insufficient_development_resolution"], threshold=None)
    threshold = ordered[rank-1]
    exceed = sum(r["statistic"] > threshold for r in holdout)
    rate = exceed / len(holdout)
    se = math.sqrt(rate * (1-rate) / len(holdout))
    return dict(base, ready=True, reasons=[], alpha=alpha, threshold=threshold,
                exceedances=exceed, false_positive_rate=rate,
                approximate_95pct_interval=[max(0, rate-1.96*se), min(1, rate+1.96*se)],
                strict_exceedance=True, scientific_inference_eligible=False)
