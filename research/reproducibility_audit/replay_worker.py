"""Local deterministic arithmetic worker, no network or external package imports."""
import hashlib
import json
import math
import random
import sys


def calculate(data):
    if data.get('fixture_kind') != 'synthetic' or data.get('schema') != 'un.replay-fixture.v1':
        raise ValueError('Only registered synthetic numerical fixtures are allowed')
    if sorted(data) != ['fixture_kind', 'observations', 'schema', 'seed']:
        raise ValueError('Unexpected synthetic fixture fields')
    if type(data['seed']) is not int or not 0 <= data['seed'] < 2**32:
        raise ValueError('Invalid deterministic seed')
    xs=data['observations']
    if not isinstance(xs,list) or not 2 <= len(xs) <= 4096 or any(type(x) not in (float,int) or not math.isfinite(x) or abs(x)>1e6 for x in xs):
        raise ValueError('Invalid synthetic observations')
    rng=random.Random(data['seed'])
    boot=[]
    for _ in range(128):
        sample=[xs[rng.randrange(len(xs))] for _ in xs]
        boot.append(math.fsum(sample)/len(sample))
    return {'schema':'un.replay-result.v1','seed':data['seed'],
            'count':len(xs),'mean':round(math.fsum(xs)/len(xs),12),
            'bootstrap_mean':round(math.fsum(boot)/len(boot),12)}


if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('expected synthetic fixture path')
    with open(sys.argv[1], 'rb') as f: raw=f.read(150_000)
    if len(raw)>=150_000: raise SystemExit('oversize synthetic fixture')
    data=json.loads(raw)
    output=calculate(data)
    sys.stdout.write(json.dumps(output,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n')
