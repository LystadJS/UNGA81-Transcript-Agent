#!/usr/bin/env python3
"""Fictional source-free engineering preflight for W4 expanded-year preregistration.

This is NOT the preregistered 36-cell 64D known-truth calibration. No real
historical source texts, PV documents, personal IDs or source-linked records.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import unittest
from dataclasses import dataclass

import numpy as np
from scipy.special import expit

SEED = 20261013
YEARS = np.arange(2008, 2024, dtype=int)
N_ACTORS = 18
N_WORDS = 192
DIM = 6


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class Toy:
    counts: np.ndarray
    years: np.ndarray
    actors: np.ndarray
    meetings: np.ndarray
    language: np.ndarray
    observed: np.ndarray
    selection_model: str


def make_toy(mode: str = "MAR", seed: int = SEED, rho: float = 0.65,
             effect: float = 0.2) -> Toy:
    """Generate fictional year->meeting->affiliation speeches with typed metadata."""
    if mode not in ("complete", "MAR", "MNAR"):
        raise ValueError("Unknown source-selection mechanism")
    if not (-0.95 < rho < 0.95):
        raise ValueError("Invalid annual AR(1)")
    rng = np.random.default_rng(seed)
    actor = np.tile(np.arange(N_ACTORS, dtype=int), len(YEARS))
    years = np.repeat(YEARS, N_ACTORS)
    language = ((actor * 5 + years) % 7 < 3).astype(int)
    meeting_number = (actor // 3 + years) % 6
    meetings = np.char.add(np.char.add("fictional-", years.astype(str)),
                           np.char.add("-meeting-", meeting_number.astype(str)))
    yr_shock = np.empty(len(YEARS))
    yr_shock[0] = rng.normal(scale=0.2)
    for j in range(1, len(YEARS)):
        yr_shock[j] = rho * yr_shock[j - 1] + np.sqrt(1-rho**2)*rng.normal(scale=0.2)
    actor_re = rng.normal(scale=0.4, size=N_ACTORS)
    mtg_re = rng.normal(scale=0.12, size=(len(YEARS), 6))
    z = (actor_re[actor] + yr_shock[years-2008]
         + mtg_re[years-2008, meeting_number]
         + effect*(years>=2016) + rng.normal(scale=0.25,size=len(years)))
    # Fixed synthetic random vocabulary loadings, no real words or paragraphs.
    load = rng.normal(scale=0.15, size=N_WORDS)
    logit = (z[:, None] * load[None, :] + rng.normal(scale=0.02, size=(len(z),1)))
    p = np.exp(logit-logit.max(axis=1,keepdims=True))
    p /= p.sum(axis=1,keepdims=True)
    counts = np.array([rng.multinomial(160, prob) for prob in p], dtype=int)
    base = 1.9 - 0.55*language - 0.22*(years<2016)
    if mode=="MNAR":
        base = base - 0.8 * (z-z.mean())/(z.std() or 1)
    observed = np.ones(len(years),dtype=bool) if mode=="complete" else rng.random(len(years))<expit(base)
    return Toy(counts, years, actor, meetings, language, observed, mode)


def _logistic_fit(X: np.ndarray, outcome: np.ndarray, ridge: float = 1.0) -> np.ndarray:
    """Ridge logistic by deterministic Newton updates; no speech outcomes in X."""
    if np.unique(outcome).size < 2:
        return np.r_[np.log((outcome.sum()+0.5)/(len(outcome)-outcome.sum()+0.5)),0.,0.]
    beta = np.zeros(X.shape[1])
    for _ in range(70):
        p = expit(X@beta)
        w = np.maximum(p*(1-p), 1e-6)
        penalty = np.diag([0.,ridge,ridge])
        g = X.T@(outcome-p) - penalty@beta
        H = X.T@(X*w[:,None]) + penalty
        step = np.linalg.solve(H, g)
        beta += np.clip(step,-2,2)
        if np.linalg.norm(step) < 1e-8:
            break
    return beta


def crossfit_probabilities(toy: Toy) -> np.ndarray:
    X = np.column_stack([np.ones(len(toy.years)),toy.language.astype(float),
                         (toy.years < 2016).astype(float)])
    if toy.selection_model=="complete":
        return np.ones(len(toy.years))
    pred = np.empty(len(toy.years))
    # Four folds of WHOLE YEARS, not shuffled speech rows.
    for fold in range(4):
        held=(toy.years - 2008)%4==fold
        beta=_logistic_fit(X[~held],toy.observed[~held].astype(float))
        pred[held]=expit(X[held]@beta)
    return pred


@dataclass
class LexicalFit:
    idf: np.ndarray
    components: np.ndarray
    train_id_hash: str
    training_years: tuple[int, ...]
    rank: int


def fit_training_reference(toy: Toy, train_rows: np.ndarray,
                           component_count: int = DIM) -> LexicalFit:
    train_rows=np.asarray(train_rows,dtype=int)
    if train_rows.ndim!=1 or len(train_rows)<component_count+2:
        raise ValueError("Insufficient year/source training observations")
    if np.any(toy.years[train_rows]>2015) or np.any(~toy.observed[train_rows]):
        raise ValueError("Reference training leakage from post era or unverified text")
    sub=toy.counts[train_rows].astype(float)
    idf=1+np.log((1+len(sub))/(1+(sub>0).sum(axis=0)))
    tf=np.log1p(sub)*idf
    tf/=np.maximum(np.linalg.norm(tf,axis=1,keepdims=True),1e-10)
    _,singular,vt=np.linalg.svd(tf,full_matrices=False)
    rank=int((singular>singular[0]*1e-9).sum())
    if rank<component_count:
        raise ValueError("Reference fit dimension rank deficient")
    return LexicalFit(idf,vt[:component_count].copy(),
                      sha(json.dumps(train_rows.tolist(),separators=(',',':')).encode()),
                      tuple(sorted(set(map(int,toy.years[train_rows])))),rank)


def transform(toy: Toy, ref:LexicalFit) -> np.ndarray:
    x=np.log1p(toy.counts.astype(float))*ref.idf
    x/=np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-10)
    scores=x@ref.components.T
    scores/=np.maximum(np.linalg.norm(scores,axis=1,keepdims=True),1e-10)
    return scores


def distance(toy:Toy, scores:np.ndarray, probs:np.ndarray,
             min_per_era:int=1) -> dict:
    if np.ndim(scores)!=2 or scores.shape[0]!=len(toy.years) or len(probs)!=len(toy.years):
        raise ValueError("Malformed scores or source inclusion probabilities")
    if np.any((probs<=0)|(probs>1)) or not np.isfinite(scores).all():
        raise ValueError("Invalid propensity or feature matrix")
    raw_weight=np.divide(1,probs)
    weights=np.minimum(10,raw_weight)
    distances=[]
    missing_actor_periods=0
    for actor in range(N_ACTORS):
        pair=[]
        for late in (False,True):
            keep=(toy.actors==actor)&((toy.years>=2016)==late)&toy.observed
            if keep.sum()<min_per_era:
                pair=[];missing_actor_periods+=1;break
            # Inner actor-year has one canonical speech in this fictional fixture.
            pair.append(np.average(scores[keep],axis=0,weights=weights[keep]))
        if len(pair)==2:
            distances.append(float(np.linalg.norm(pair[1]-pair[0])))
    return {"eligible_actors":len(distances),"missing_actor_periods":missing_actor_periods,
            "mean_distance":float(np.mean(distances)) if len(distances)==N_ACTORS else None,
            "denominator_preserved":len(distances)==N_ACTORS,
            "max_inverse_weight":float(raw_weight.max()),
            "weight_clipped_fraction":float(np.mean(raw_weight[toy.observed]>10)) if toy.observed.any() else None}


def summary(mode:str="MAR",seed:int=SEED)->dict:
    t=make_toy(mode,seed)
    q=crossfit_probabilities(t)
    pre=np.where((t.years<=2015)&t.observed)[0]
    ref=fit_training_reference(t,pre)
    d=distance(t,transform(t,ref),q)
    # A second deterministic source/year-refit from training-era whole-year weights.
    rng=np.random.default_rng(seed+9)
    draws=rng.choice(YEARS[:8],size=8,replace=True)
    refit_rows=np.concatenate([np.where((t.years==y)&t.observed)[0] for y in draws])
    rr=fit_training_reference(t,refit_rows)
    d2=distance(t,transform(t,rr),q)
    return {"simulation_kind":"fictional_engineering_only",
            "full_preregistered_MC_executed":False,"seed":seed,"source_selection":mode,
            "actors":N_ACTORS,"years":len(YEARS),"lexical_vocabulary":N_WORDS,
            "lexical_dimension":DIM,"original_source_files_read":0,
            "observed":int(t.observed.sum()),"source_cells":len(t.observed),
            "source_meeting_groups":int(len(set(t.meetings.tolist()))),
            "conditional":d,"refitted":d2,"training_years":list(ref.training_years),
            "refit_training_years":list(rr.training_years),
            "mnar_identified_inference_allowed":False if mode=="MNAR" else None,
            "publication_eligible":False}


class Controls(unittest.TestCase):
    def test_population_and_nested_grouping(self):
        t=make_toy('complete')
        self.assertEqual(len(t.years),18*16)
        self.assertEqual(len(set(t.meetings.tolist())),16*6)
        self.assertEqual(int(t.observed.sum()),18*16)
        self.assertTrue(all(len(set(t.years[t.meetings==x]))==1 for x in set(t.meetings.tolist())))

    def test_missingness_not_zero_and_mnar_abstains(self):
        t=make_toy('MNAR')
        self.assertLess(t.observed.sum(),len(t.observed))
        q=crossfit_probabilities(t)
        self.assertTrue((q>0).all() and (q<1).all())
        self.assertIs(summary('MNAR')['mnar_identified_inference_allowed'],False)

    def test_roster_only_source_loss_withholds_instead_of_shrinking(self):
        t=make_toy('complete',effect=0)
        for actor in range(N_ACTORS):
            idx=np.flatnonzero(t.actors==actor)
            t.counts[idx]=t.counts[idx[0]]
        f=fit_training_reference(t,np.flatnonzero(t.years<=2015))
        z=transform(t,f)
        complete=distance(t,z,np.ones(len(z)))
        self.assertTrue(complete['denominator_preserved'])
        self.assertLess(complete['mean_distance'],1e-10)
        t.observed[(t.actors==0)&(t.years>=2016)]=False
        withheld=distance(t,z,np.ones(len(z)))
        self.assertFalse(withheld['denominator_preserved'])
        self.assertIsNone(withheld['mean_distance'])
        self.assertEqual(withheld['eligible_actors'],N_ACTORS-1)

    def test_training_only_no_comparison_leak(self):
        t=make_toy('complete')
        train=np.flatnonzero(t.years<=2015)
        model=fit_training_reference(t,train)
        t.counts[t.years>=2016]*=11
        newer=fit_training_reference(t,train)
        np.testing.assert_array_equal(newer.components,model.components)
        np.testing.assert_array_equal(newer.idf,model.idf)
        with self.assertRaisesRegex(ValueError,'leakage'):
            fit_training_reference(t,np.flatnonzero(t.years>=2016))

    def test_alignment_not_required_for_within_fit_scalar(self):
        t=make_toy('complete')
        f=fit_training_reference(t,np.flatnonzero(t.years<=2015))
        x=transform(t,f)
        q=np.ones(len(x))
        original=distance(t,x,q)['mean_distance']
        rot=np.linalg.qr(np.random.default_rng(9).normal(size=(DIM,DIM)))[0]
        modified=distance(t,x@rot,q)['mean_distance']
        self.assertAlmostEqual(original,modified,places=12)

    def test_unknown_mode_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'Unknown'):
            make_toy('secret_data')
        with self.assertRaisesRegex(ValueError,'annual'):
            make_toy(rho=1)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--selftest',action='store_true')
    parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args()
    if args.selftest:
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
        if not result.wasSuccessful():
            raise SystemExit(2)
        print(json.dumps({"source_only_controls":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"kind":"fictional_engineering_only"}))
    elif args.smoke:
        print(json.dumps({"status":"PASS_ENGINEERING_PREFLIGHT_ONLY", "models": [summary(mode) for mode in ("complete","MAR","MNAR")],
                          "empirical_inference_eligible":False,"full_36_cell_calibration":"NOT_RUN"},sort_keys=True))
    else:
        parser.error('Select --selftest or --smoke; real historical source input not supported')


if __name__=='__main__':
    main()
