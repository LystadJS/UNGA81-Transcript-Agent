"""Synthetic Ed25519 + revocation verification microbenchmark, never release gate.

Compare the existing metadata-only preflight against the additional cryptographic
verifier on the same fictional fixture. Latencies are environment-dependent;
no latency threshold determines correctness or diplomatic readiness. Output
contains timings and safe receipt digests only, no keys or signatures.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
import statistics
import sys
from time import perf_counter_ns

from cryptography import __version__ as cryptography_version
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'tests'))
from test_synthetic_signatures import fixture
from test_registry_preflight import WHEN
from registry_preflight import preflight, assert_no_authority
from synthetic_signatures import verify_synthetic_signatures, assert_zero_authority, receipt_sha256


def _stats(times):
    ordered=sorted(times)
    return {'median_ms':round(statistics.median(ordered)/1e6,6),
            'p95_ms':round(ordered[math.ceil(.95*len(ordered))-1]/1e6,6),
            'mean_ms':round(statistics.mean(ordered)/1e6,6),
            'min_ms':round(ordered[0]/1e6,6),
            'max_ms':round(ordered[-1]/1e6,6)}


def benchmark(iterations=1000,warmup=50):
    if type(iterations) is not int or iterations<20 or iterations>100000 or type(warmup) is not int or warmup<0 or warmup>10000:
        raise ValueError('invalid synthetic benchmark bounds')
    f=fixture()
    def metadata():
        r=preflight(f['snapshot'],f['policy'],f['events'],checked_at=WHEN,proposal=f['proposal'])
        assert_no_authority(r)
        if r['metadata_status']!='metadata_consistent':raise AssertionError('synthetic control failed')
        return r
    def signed():
        r=verify_synthetic_signatures(f['snapshot'],f['policy'],f['events'],f['proposal'],
            f['custody'],f['revocation'],checked_at=WHEN,trust=f['trust'])
        assert_zero_authority(r)
        if r['status']!='synthetic_signatures_verified_no_authority':raise AssertionError('synthetic signature failed')
        return r
    for _ in range(warmup): metadata();signed()
    meta_ns=[];signed_ns=[]
    for i in range(iterations):
        # Alternate ordering to avoid bias from machine warmup/CPU drift.
        routines=((metadata,meta_ns),(signed,signed_ns)) if i%2==0 else ((signed,signed_ns),(metadata,meta_ns))
        for fn,sample in routines:
            t=perf_counter_ns();fn();sample.append(perf_counter_ns()-t)
    positive=signed()
    med=statistics.median(signed_ns)/statistics.median(meta_ns)
    return {
        'schema':'un.synthetic-signature-benchmark.v0',
        'synthetic_only':True,'authority':'none','authorized':False,
        'publication_eligible':False,'delivery_eligible':False,
        'iterations_per_mode':iterations,'warmup_per_mode':warmup,
        'python':platform.python_version(),'platform_system':platform.system(),
        'cryptography':cryptography_version,
        'metadata_preflight':_stats(meta_ns),
        'ed25519_revocation_preflight':_stats(signed_ns),
        'median_overhead_ratio':round(med,4),
        'receipt_sha256':receipt_sha256(positive),
        'note':'Synthetic-only timings are not a production SLA or gate decision.',
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iterations',type=int,default=1000)
    p.add_argument('--warmup',type=int,default=50)
    p.add_argument('--output',type=Path)
    args=p.parse_args(argv)
    value=benchmark(args.iterations,args.warmup)
    text=json.dumps(value,sort_keys=True,indent=2)+'\n'
    if args.output:
        if args.output.is_symlink() or args.output.exists(): p.error('output must be a new, nonsymlinked file')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x',encoding='utf-8') as f:f.write(text)
    print(text,end='')
    return 0

if __name__=='__main__':raise SystemExit(main())
