"""Reproducible source-free AR1 parameter recovery and percentile interval audit."""
import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from study import world, seeded
from temporal_ar1 import estimate_ar1, resample_ar1

TRUTH_RHO = .55  # Benchmark-only truth; never passed to estimator.

def interval(ordered, probability):
    if not ordered:return None
    a=sorted(ordered)
    index=probability*(len(a)-1)
    lo=math.floor(index);hi=math.ceil(index)
    return a[lo]*(hi-index)+a[hi]*(index-lo) if lo!=hi else a[lo]

def benchmark(master=810081, worlds=100, replicates=40, years=24, per_year=4, misspecified=False):
    if worlds<2 or replicates<2:raise ValueError('budgets too small')
    failures=Counter();rho_est=[];covered=0;intervals=0;bootstrap_attempts=0;bootstrap_success=0
    for j in range(worlds):
        seed=seeded(master,'ar1_independent_recovery_misspecified' if misspecified else 'ar1_independent_recovery','development',j)
        data=world(seed,years=years,per_year=per_year,misspecified=misspecified)
        fit=estimate_ar1(data)
        if not fit['ready']:
            failures[fit['reason']]+=1
            continue
        rho_est.append(fit['rho'])
        estimates=[]
        for k in range(replicates):
            bootstrap_attempts+=1
            new=resample_ar1(data,fit,seeded(master,'ar1_independent_recovery','reference',j,k))
            f=estimate_ar1(new)
            if f['ready']:
                bootstrap_success+=1;estimates.append(f['rho'])
            else:failures['bootstrap_'+f['reason']]+=1
        if len(estimates)==replicates:
            intervals+=1
            left,right=interval(estimates,.025),interval(estimates,.975)
            covered+=left<=TRUTH_RHO<=right
        else:
            failures['interval_withheld_incomplete_bootstrap']+=1
    n=len(rho_est)
    return dict(schema='un.null-calibration.ar1-recovery.v1',master_seed=master,worlds_attempted=worlds,
                years=years,meetings_per_year=per_year,bootstrap_per_fitted_world=replicates,
                misspecified=misspecified,worlds_fit=n,worlds_failed=worlds-n,
                failures=dict(sorted(failures.items())),bootstrap_attempted=bootstrap_attempts,
                bootstrap_successful=bootstrap_success,intervals_attempted=n,
                intervals_complete=intervals,intervals_covering_truth=covered,
                conditional_interval_coverage=covered/intervals if intervals else None,
                unconditional_interval_coverage=covered/worlds if intervals==worlds else None,
                true_rho=TRUTH_RHO,mean_rho=statistics.mean(rho_est) if n else None,
                rho_bias=statistics.mean(rho_est)-TRUTH_RHO if n else None,
                rho_rmse=math.sqrt(sum((x-TRUTH_RHO)**2 for x in rho_est)/n) if n else None,
                boundary_frequency=sum(abs(x)>.8 for x in rho_est)/n if n else None,
                scientific_ready=False,publication_eligible=False,
                caveats=['Truth used only by benchmark scorer','Percentile coverage conditional on complete bootstrap and fitted worlds',
                         'Not validated W1/W2 method or frozen PR57 holdout','Selection/representation effects not identified'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worlds',type=int,default=100)
    p.add_argument('--replicates',type=int,default=40);p.add_argument('--years',type=int,default=24)
    p.add_argument('--meetings',type=int,default=4);p.add_argument('--misspecified',action='store_true')
    a=p.parse_args()
    report=benchmark(worlds=a.worlds,replicates=a.replicates,years=a.years,per_year=a.meetings,misspecified=a.misspecified)
    output=json.dumps(report,sort_keys=True,indent=2)
    print(output)
    print('receipt_sha256',hashlib.sha256(output.encode()).hexdigest())
