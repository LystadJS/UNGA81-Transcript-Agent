#!/usr/bin/env python3
"""Recheck source-bound development outputs; never invoke a reserved-corpus loader."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from reference import HERE, read, digest, canonical
from holdout_dryrun import verify_frozen_lock


def verify(negative_path:Path,masked_dir:Path,dry_dir:Path)->dict:
    lock=verify_frozen_lock()
    n=read(negative_path);m=read(masked_dir/'manifest.json');s=read(masked_dir/'sensitivity.json')
    if n.get('schema')!='un.nuisance-negative-controls.v1' or n['source_parents']!=523 or n['holdout_opened']!=0:
        raise ValueError('Development nuisance-control receipt invalid')
    if m.get('schema')!='un.masked-comparison-manifest.v1' or m['holdout_transcripts_opened']!=0:
        raise ValueError('Country-masking manifest invalid')
    if set(m['files'])!={'mask-policy.json','mask-audit.json','masked-chunks.json','masked-geometry.npz','sensitivity.json'}:
        raise ValueError('Mask export expected file set changed')
    for name, expected in m['files'].items():
        p=masked_dir/name
        if not p.is_file() or p.is_symlink() or digest(p.read_bytes())!=expected:
            raise ValueError('Mask output tampered: '+name)
    if m['original_model_lock_sha256']!=digest((HERE.parent/'semantic_review/model-lock.json').read_bytes()):
        raise ValueError('Model lock changed')
    if s['provisional_passages']!=1641 or s['source_parents']!=523 or s['heldout_opened']!=0 or s['retraining_or_recalibration']:
        raise ValueError('Mask report misstates population/holdout/model status')
    audit=read(masked_dir/'mask-audit.json')
    if len(audit)!=1641 or len({r['id'] for r in audit})!=len(audit):
        raise ValueError('Mask audit lost or duplicated observations')
    if s['replacements']!=sum(r['matches'] for r in audit) or s['matching_passages']!=sum(bool(r['matches']) for r in audit):
        raise ValueError('Masked counts and original audit disagree')
    for r in audit:
        if r['matches']!=len(r['spans']) or any(not 0<=x['start']<x['end'] or len(x['original_span_sha256'])!=64 for x in r['spans']):
            raise ValueError('Untraceable country-name replacement')
    with np.load(masked_dir/'masked-geometry.npz',allow_pickle=False) as arrays:
        if arrays['ids'].shape!=(1641,) or arrays['semantic_raw'].shape!=(1641,384) or arrays['lexical'].shape!=(1641,64) or arrays['semantic_pca64'].shape!=(1641,64):
            raise ValueError('Mask numerical archive shape mismatch')
        if any(arrays[k].dtype.hasobject for k in arrays.files):raise ValueError('Object arrays prohibited')
        if arrays['ids'].tolist()!=[r['id'] for r in audit] or arrays['original_hashes'].tolist()!=[r['source_sha256'] for r in audit] or arrays['masked_hashes'].tolist()!=[r['masked_sha256'] for r in audit]:
            raise ValueError('Numeric mask arrays detached from source lineage')
    byvariant={}
    for variant in ['nominal','correlated','insufficient','all_unavailable','transform-smoke']:
        path=dry_dir/('dry-'+variant+'.json')
        data=read(path)
        if not data.get('synthetic') or data.get('reserved_transcripts_opened')!=0 or data.get('all_meetings')!=37 or data.get('locked_protocol_sha256')!=lock['sha256'] or data.get('actual_replication_claim'):
            raise ValueError('Dry run appears to include actual held-out evaluation')
        byvariant[variant]=data['decision']
    if byvariant != {'nominal':'SYNTHETIC_GATE_WOULD_NOT_PASS','correlated':'SYNTHETIC_GATE_WOULD_PASS','insufficient':'INCONCLUSIVE_SYNTHETIC','all_unavailable':'INCONCLUSIVE_SYNTHETIC','transform-smoke':'SYNTHETIC_GATE_WOULD_NOT_PASS'}:
        raise ValueError('Synthetic gating branch changed')
    if read(dry_dir/'dry-transform-smoke.json')['synthetic_transform_smoke']['status']!='PASS_SYNTHETIC_TRANSFORM_SMOKE':
        raise ValueError('Saved-transform smoke did not pass')
    return {'status':'PASS','strict_passages':1641,'original_source_parents':523,
            'masked_passages':s['matching_passages'],'mask_replacements':s['replacements'],
            'negative_controls':list(n['result']),'synthetic_gate_branches':byvariant,
            'frozen_lock_sha256':lock['sha256'],'reserved_transcripts_opened':0}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('negative',type=Path);parser.add_argument('masked',type=Path);parser.add_argument('dry',type=Path)
    a=parser.parse_args();print(json.dumps(verify(a.negative,a.masked,a.dry),indent=2))
