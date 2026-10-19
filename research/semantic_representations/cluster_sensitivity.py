"""Deterministic synthetic-only partition sensitivity; descriptive, not inference."""
import math
import random


def distance(a, b):
    if len(a) != len(b) or not a or any(not math.isfinite(x) for x in a + b):
        raise ValueError('invalid vector geometry')
    return sum((x-y)**2 for x,y in zip(a,b))


def partition(rows, k, seed):
    if not 1 < k < len(rows):
        raise ValueError('k must be between 2 and n-1')
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate observation IDs')
    vectors = [list(map(float, r['vector'])) for r in rows]
    if len({len(v) for v in vectors}) != 1:
        raise ValueError('incompatible dimensions')
    for v in vectors:
        distance(v,v)
    medoids = random.Random(seed).sample(range(len(rows)), k)
    for _ in range(40):
        assignments = [min(range(k), key=lambda j:(distance(v, vectors[medoids[j]]),j)) for v in vectors]
        if len(set(assignments)) < k:
            return {'status':'failed', 'reason':'empty_group', 'assignments':None}
        new = [min((i for i,a in enumerate(assignments) if a == j),
                   key=lambda i:(sum(distance(vectors[i], vectors[h]) for h,a in enumerate(assignments) if a == j), ids[i]))
               for j in range(k)]
        if new == medoids:
            return {'status':'success', 'reason':None, 'assignments':dict(zip(ids, assignments))}
        medoids = new
    return {'status':'failed', 'reason':'iteration_limit', 'assignments':None}


def adjusted_rand(a, b):
    if set(a) != set(b) or len(a) < 2:
        raise ValueError('population mismatch')
    ids = sorted(a)
    pairs = len(ids)*(len(ids)-1)//2
    same_a = sum(a[ids[i]] == a[ids[j]] for i in range(len(ids)) for j in range(i))
    same_b = sum(b[ids[i]] == b[ids[j]] for i in range(len(ids)) for j in range(i))
    both = sum(a[ids[i]] == a[ids[j]] and b[ids[i]] == b[ids[j]] for i in range(len(ids)) for j in range(i))
    expected = same_a*same_b/pairs
    maximum = (same_a+same_b)/2
    return (both-expected)/(maximum-expected) if maximum != expected else (1.0 if same_a == same_b == both else 0.0)


def sensitivity(left, right, k, seeds=(17,23,31,47)):
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('distinct seeds required')
    if [r['id'] for r in left] != [r['id'] for r in right]:
        raise ValueError('observation population/order mismatch')
    ledger = []
    for seed in seeds:
        a,b = partition(left,k,seed),partition(right,k,seed)
        ledger.append({'seed':seed, 'lexical_status':a['status'], 'semantic_status':b['status'],
                       'lexical_reason':a['reason'], 'semantic_reason':b['reason'],
                       'ari':adjusted_rand(a['assignments'],b['assignments']) if a['status']==b['status']=='success' else None})
    ok = [r['ari'] for r in ledger if r['ari'] is not None]
    return {'evaluation_role':'engineering_only', 'publication_eligible':False,
            'attempted_pairs':len(seeds), 'assessable_pairs':len(ok), 'failed_or_unpaired_pairs':len(seeds)-len(ok),
            'ari_mean':sum(ok)/len(ok) if ok else None, 'ari_min':min(ok) if ok else None,
            'ari_max':max(ok) if ok else None,'ledger':ledger,
            'interpretation':'Seed sensitivity of a synthetic geometry, not diplomatic agreement or significance'}
