"""Offline synthetic-only null study; never import empirical source data."""
import hashlib, json, math, random
from collections import defaultdict

VERSION = "un.null-calibration.moment-study.v1"
def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def seeded(master, scenario, phase, world, reference=None):
    key=[master,scenario,phase,world]
    if reference is not None: key+=["reference",reference]
    return int.from_bytes(hashlib.sha256(json.dumps(key,separators=(",",":")).encode()).digest()[:8],"big")

def world(seed, years=12, per_year=2, passages=4, signal=0, imbalance=False, misspecified=False, cross_family=False, mnar=False):
    """Nested synthetic meeting/speech passages and AR1 year nuisance (generation only)."""
    rng=random.Random(seed); year_effect=[]; rows=[]
    for y in range(years):
        year_effect.append(.55*(year_effect[-1] if year_effect else 0)+rng.gauss(0,.23))
        for m in range(per_year):
            meeting=f"y{y}m{m}"
            shock=rng.gauss(0,.19*(2 if misspecified and y%3==0 else 1))
            n=passages*(4 if imbalance and y==0 and m==0 else 1)
            for i in range(n):
                length=rng.randint(30,100)
                p=max(.06,min(.94,.31+year_effect[-1]+shock+signal*(1 if (y+m)%2 else -1)))
                count=sum(rng.random()<p for _ in range(length))
                rows.append(dict(id=f"{meeting}p{i}",meeting=meeting,year=y,speech=f"{meeting}s{i//2}",
                  family=f"y{y}shared" if cross_family else meeting,length=length,count=count,
                  selected=not(mnar and p>.47),representation="synthetic-count-v1"))
    return rows

def estimate(rows, min_years=12, min_meetings=24, min_effective=12):
    """Estimate pooled binomial prevalence and between-meeting variance, WITHOUT oracle truth.
    Explicitly does NOT identify year AR1 or lexical-representation covariance.
    """
    ids=[r["id"] for r in rows]
    if len(set(ids))!=len(ids): return dict(ready=False,reason="duplicate_id")
    if not rows or any(r["representation"]!="synthetic-count-v1" for r in rows):
        return dict(ready=False,reason="representation_mismatch")
    if any(not r["selected"] for r in rows):
        return dict(ready=False,reason="unknown_selection_mechanism")
    if any(not isinstance(r["length"],int) or not isinstance(r["count"],int) or
           r["length"]<1 or not 0<=r["count"]<=r["length"] for r in rows):
        return dict(ready=False,reason="invalid_counts")
    meetings=defaultdict(list); years=defaultdict(set); families=defaultdict(set)
    for r in rows:
        meetings[r["meeting"]].append(r);years[r["year"]].add(r["meeting"]);families[r["family"]].add(r["meeting"])
    if any(len(x)>1 for x in families.values()):
        return dict(ready=False,reason="cross_meeting_family")
    if len(years)<min_years or any(len(x)<2 for x in years.values()):
        return dict(ready=False,reason="weak_year_identification")
    if len(meetings)<min_meetings or any(len(x)<2 for x in meetings.values()):
        return dict(ready=False,reason="insufficient_meetings")
    sizes=[len(v) for v in meetings.values()]
    kish=sum(sizes)**2/sum(x*x for x in sizes)
    if kish<min_effective: return dict(ready=False,reason="imbalanced_effective_groups",kish=kish)
    prevalence=sum(r["count"] for r in rows)/sum(r["length"] for r in rows)
    if not .03<prevalence<.97:return dict(ready=False,reason="prevalence_boundary")
    means={m:sum(r["count"] for r in rs)/sum(r["length"] for r in rs) for m,rs in meetings.items()}
    between=sum((p-prevalence)**2 for p in means.values())/len(means)
    binomial_noise=sum(prevalence*(1-prevalence)/r["length"] for r in rows)/len(rows)
    sd=math.sqrt(max(0,between-binomial_noise/max(2,min(sizes))))
    return dict(ready=True,prevalence=prevalence,meeting_sd=sd,kish=kish,
                meetings=len(meetings),years=len(years),rows=len(rows),
                year_rho_identified=False,estimator="pooled_source_moments_v1")

def stat(rows):
    grouped=defaultdict(list)
    for r in rows:grouped[r["meeting"]].append(r)
    p=sum(r["count"] for r in rows)/sum(r["length"] for r in rows)
    return sum((sum(r["count"] for r in g)/sum(r["length"] for r in g)-p)**2 for g in grouped.values())/len(grouped)

def bootstrap(rows, fit, seed):
    rng=random.Random(seed)
    noise={g:rng.gauss(0,fit["meeting_sd"]) for g in sorted({r["meeting"] for r in rows})}
    out=[]
    for r in rows:
        p=max(.001,min(.999,fit["prevalence"]+noise[r["meeting"]]))
        out.append(dict(r,count=sum(rng.random()<p for _ in range(r["length"]))))
    return out

def evaluate(master,scenario,phase,worlds,references,**settings):
    if worlds<1 or references<1:raise ValueError("positive budgets required")
    attempts=[]
    for i in range(worlds):
        seed=seeded(master,scenario,phase,i)
        rows=world(seed,**settings);fit=estimate(rows)
        entry=dict(seed=seed,source_sha256=digest(rows),fit=fit,reference_attempted=0,
                   reference_successful=0,reference_failed=0,rejected=None,reason=None)
        if not fit["ready"]:
            entry["reason"]=fit["reason"];attempts.append(entry);continue
        observed=stat(rows);vals=[]
        for j in range(references):
            entry["reference_attempted"]+=1
            sample=bootstrap(rows,fit,seeded(master,scenario,phase,i,j))
            f=estimate(sample)
            if not f["ready"]:
                entry["reference_failed"]+=1;entry["reason"]="reference_fit_failed";break
            vals.append(stat(sample));entry["reference_successful"]+=1
        if entry["reference_failed"] or len(vals)!=references:
            entry["reason"]=entry["reason"] or "incomplete_references"
        else:
            entry["pvalue"]=(1+sum(v>=observed for v in vals))/(1+references)
            entry["rejected"]=entry["pvalue"]<=.05
        attempts.append(entry)
    return attempts

def wilson(k,n):
    if not n:return None
    z=1.95996398454;p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [max(0,c-h),min(1,c+h)]

def summary(attempts):
    completed=[x for x in attempts if x["rejected"] is not None]
    rejected=sum(x["rejected"] for x in completed)
    return dict(attempted=len(attempts),completed=len(completed),withheld=len(attempts)-len(completed),
                reference_attempted=sum(x["reference_attempted"] for x in attempts),
                reference_successful=sum(x["reference_successful"] for x in attempts),
                reference_failed=sum(x["reference_failed"] for x in attempts),
                rejected=rejected,conditional_rate=rejected/len(completed) if completed else None,
                conditional_wilson95=wilson(rejected,len(completed)),
                unconditional_rate=rejected/len(attempts) if len(completed)==len(attempts) and attempts else None,
                science_ready=False)

def smoke(master=810081,worlds=2,references=9):
    cases={"balanced_null":{},"imbalanced_null":{"imbalance":True},
           "misspecified_null":{"misspecified":True},"known_structure":{"signal":.2},
           "eight_years":{"years":8},"cross_family":{"cross_family":True},"mnar":{"mnar":True}}
    results={}
    for name,settings in cases.items():
        results[name]={}
        for phase in ("development","holdout"):
            attempts=evaluate(master,name,phase,worlds,references,**settings)
            results[name][phase]={"summary":summary(attempts),"attempts":attempts}
    return dict(schema=VERSION,master_seed=master,worlds_per_phase=worlds,
                references_per_world=references,scenarios=results,
                scientific_ready=False,publication_eligible=False,
                limitations=["Not the locked 99-reference confirmatory evaluation",
                "Does not estimate AR1, speech covariance, representation effects, or selection",
                "Not W1/W2 model refitting or independent cross-source replication"])
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--worlds",type=int,default=2)
    p.add_argument("--references",type=int,default=9);p.add_argument("--output",required=True)
    a=p.parse_args();result=smoke(worlds=a.worlds,references=a.references)
    from pathlib import Path
    path=Path(a.output)
    if path.exists():raise SystemExit("Refuse overwrite")
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({case:{p:v[p]["summary"] for p in v} for case,v in result["scenarios"].items()},indent=2))
