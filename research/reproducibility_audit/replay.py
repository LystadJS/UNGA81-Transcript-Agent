"""Independent process restart / expected digest replay for synthetic-only inputs."""
from __future__ import annotations
import json
import os
import math
import random
from pathlib import Path
import subprocess
import sys
import tempfile
from protocol import canonical_json, sha256


def replay(fixture: dict, *, expected_sha256: str | None = None, worker: Path | None = None) -> dict:
    # Second implementation independently computes the reference result rather
    # than importing the child worker whose behavior is being checked.
    if (set(fixture) != {'schema', 'fixture_kind', 'seed', 'observations'} or
        fixture.get('schema') != 'un.replay-fixture.v1' or
        fixture.get('fixture_kind') != 'synthetic' or
        type(fixture.get('seed')) is not int or not 0 <= fixture['seed'] < 2**32):
        raise ValueError('Only registered synthetic numeric fixtures are allowed')
    xs=fixture['observations']
    if (not isinstance(xs,list) or not 2 <= len(xs) <= 4096 or
        any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e6 for x in xs)):
        raise ValueError('Invalid synthetic numeric observations')
    random_source=random.Random(fixture['seed'])
    reference_boot=[]
    for replicate in range(128):
        positions=[random_source.randrange(len(xs)) for position in range(len(xs))]
        reference_boot.append(math.fsum(xs[j] for j in positions)/len(xs))
    expected={'schema':'un.replay-result.v1','seed':fixture['seed'],
              'count':len(xs),'mean':round(math.fsum(xs)/len(xs),12),
              'bootstrap_mean':round(math.fsum(reference_boot)/len(reference_boot),12)}
    if worker is None:
        worker=Path(__file__).resolve().with_name('replay_worker.py')
    worker=Path(worker).resolve()
    if not worker.is_file():
        return {'status':'NOT RUN','reason':'replay worker not present'}
    fixture_bytes=canonical_json(fixture)
    if len(fixture_bytes)>150_000:
        return {'status':'FAIL','reason':'synthetic fixture too large'}
    if expected_sha256 is not None and len(expected_sha256)!=64:
        return {'status':'FAIL','reason':'expected digest format'}
    with tempfile.TemporaryDirectory(prefix='unga-replay-') as td:
        fixture_path=Path(td)/'fixture.json'
        fixture_path.write_bytes(fixture_bytes)
        outputs=[]
        for _ in range(2):
            try:
                process=subprocess.run([sys.executable,'-I','-S',str(worker),str(fixture_path)],
                    cwd=td,env={'PYTHONHASHSEED':'0','PYTHONDONTWRITEBYTECODE':'1','PATH':os.environ.get('PATH','')},
                    text=False,capture_output=True,timeout=10,check=False)
            except (FileNotFoundError, OSError) as e:
                return {'status':'NOT RUN','reason':f'runtime unavailable: {e.__class__.__name__}'}
            except subprocess.TimeoutExpired:
                return {'status':'FAIL','reason':'replay timeout'}
            if process.returncode!=0 or len(process.stdout)>10000:
                return {'status':'FAIL','reason':'replay child failed'}
            try:
                actual=json.loads(process.stdout)
            except ValueError:
                return {'status':'FAIL','reason':'malformed replay stdout'}
            if actual!=expected:
                return {'status':'FAIL','reason':'worker does not match independent reference'}
            outputs.append(process.stdout)
    if outputs[0]!=outputs[1]:
        return {'status':'FAIL','reason':'independent process restart mismatch'}
    digest=sha256(outputs[0])
    if expected_sha256 is not None and expected_sha256!=digest:
        return {'status':'FAIL','reason':'pinned expected digest mismatch','observed_sha256':digest}
    return {'status':'PASS','seed':fixture['seed'],'fixture_sha256':sha256(fixture_bytes),
            'worker_sha256':sha256(worker.read_bytes()),'output_sha256':digest,
            'runtime':sys.version.split()[0], 'dependency_versions':{'python':sys.version.split()[0], 'stdlib':'bundled'},
            'restarts':2,'processes':2}
