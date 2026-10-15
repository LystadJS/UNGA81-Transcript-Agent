"""Independent DEVELOPMENT-only critical-value calibration. No holdout generator import.

The 90th percentile of pooled identifiable synthetic standardized errors at
each horizon is learned ONLY from the fixed development namespace and then
serialized as an immutable preregistered holdout input. Never tune on holdout.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.stats import t as student_t
from joint_model import fit_observed,FitFailure,NotIdentified
from synthetic_dev import generate

YEARS=(16,24,32)
MASKS=('near_census','stratified_2_of_3')
IDENTIFIABLE=('iid_MAR','AR1_MAR','AR1_MNAR_audited')
R=120

def learn():
    results={}
    attempts=[]
    for T in YEARS:
        scores=[]
        for mask in MASKS:
            for world in IDENTIFIABLE:
                fail=0
                for repetition in range(R):
                    frame,truth=generate(T,mask,world,repetition)
                    try:
                        fit=fit_observed(frame)
                        score=abs(fit["beta"]-truth["beta"])/fit["se"]
                        if not np.isfinite(score):
                            raise FitFailure("Nonfinite development studentized error")
                        scores.append(float(score))
                    except (FitFailure,NotIdentified,np.linalg.LinAlgError) as error:
                        fail+=1
                attempts.append({'years':T,'source_mask':mask,'world':world,
                                 'attempted':R,'failed':fail})
        cutoff_from_development=float(np.quantile(scores,.90,method="higher"))
        default_t=float(student_t.ppf(.95,T-3))
        results[str(T)]={'threshold_from_development':cutoff_from_development,
                         'locked_cutoff':max(default_t,cutoff_from_development),
                         'reference_t_cutoff':default_t,
                         'usable_development_panels':len(scores),
                         'expected_development_panels':R*len(MASKS)*len(IDENTIFIABLE)}
    return {'schema':'un.w4.joint_source_selection.development_cutoffs.v1',
            'phase':'development_not_independent_test',
            'master_seed_namespace':'UNGA81-JOINT-DEV-20261013',
            'holdout_seed_namespace_reserved':'UNGA81-JOINT-HOLDOUT-20261014',
            'R':R,'locked_threshold_rule':'max(t_(T-3,0.95), pooled_identifiable_development_abs_studentized_error_90th_percentile_higher)',
            'results':results,'attempts':attempts,'holdout_inspected':False,
            'all_real_data_inference_withheld':True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Frozen development cutoff must not overwrite existing data")
    obj=learn()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'development_cutoff_frozen_not_tested',
        'cutoffs':obj['results'],'failed_total':sum(x['failed'] for x in obj['attempts'])},indent=2))

if __name__=='__main__':main()
