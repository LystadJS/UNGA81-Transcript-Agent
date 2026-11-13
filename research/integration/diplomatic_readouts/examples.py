"""Standalone synthetic-only replay: no real source files and no side effects beyond output dir."""
from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
from copy import deepcopy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'tests'))
from bridge import prepare, Withheld  # noqa: E402
from fixtures import make_fixture, reaffirm  # noqa: E402
import readout  # noqa: E402


def write_once(path: Path, content: str):
    path.write_bytes(content.encode('utf-8'))
    return sha256(path.read_bytes()).hexdigest()


def execute(root: Path):
    if root.is_symlink() or root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError('output directory must be new or empty and not a symlink')
    root.mkdir(parents=True,exist_ok=True)
    manifest={"schema":"un.coordinator-readout-synthetic-replay.v1", "publication_eligible":False,
              "cases":{}}
    for scenario in ('descriptive','partial_statistical','unreviewed','failed_source','missing_evidence'):
        env,intent,proofs,approval=make_fixture(readout)
        if scenario=='partial_statistical':
            f=intent['findings'][0]
            f['category']='exploratory'; f['pattern']='Fictional grouping requires unissued statistical acceptance'
            f['observation']=None
        if scenario=='failed_source':
            proofs['synthetic-A']=replace(proofs['synthetic-A'],accepted=False)
        if scenario=='missing_evidence':
            env['evidence']=[]
            approval=reaffirm(env,approval)
        output=root/scenario
        output.mkdir(mode=0o700)
        try:
            candidate=prepare(env,intent,proofs,approval,readout_module=readout)
            decision=None
            if scenario in ('descriptive','partial_statistical'):
                # Synthetic example approval only. Core bridge never issues a reviewer decision.
                decision=readout.ReviewDecision(
                    report_sha256=readout.report_digest(candidate.report),
                    source_gate='pass',reviewer_gate='pass',privacy_gate='pass',
                    statistical_gate='not_run',evaluation_role='synthetic_fixture')
            paths={}
            for fmt,ext in (('json','json'),('markdown','md'),('html','html')):
                value=readout.render(candidate.report,fmt,proofs=candidate.proofs,decision=decision)
                paths[ext]=write_once(output/('readout.'+ext),value)
            state=readout.normalize(candidate.report,candidate.proofs,decision)['release_state']
            manifest['cases'][scenario]={"state":state,"hashes":paths,"error":None}
        except Withheld as ex:
            # No authored prose leaves a failed candidate. Renderer is fed an empty dict.
            paths={}
            for fmt,ext in (('json','json'),('markdown','md'),('html','html')):
                paths[ext]=write_once(output/('readout.'+ext),readout.render({},fmt))
            manifest['cases'][scenario]={"state":"withheld","hashes":paths,"error":ex.code}
    assert manifest['cases']['descriptive']['state']=='descriptive_only'
    assert all(manifest['cases'][k]['state']=='withheld' for k in
               ('partial_statistical','unreviewed','failed_source','missing_evidence'))
    manifest_hash=write_once(root/'manifest.json',json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print('synthetic_cases',len(manifest['cases']),'manifest_sha256',manifest_hash)
    return manifest_hash


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    execute(args.output)

if __name__=='__main__':
    main()
