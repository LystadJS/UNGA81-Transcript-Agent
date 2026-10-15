"""Coordinator-only prospective gate. GET-only freshness; no branch/ref writes.

Trees/commit envelopes are unreachable local Git objects. Only allowlisted code
is materialized, never a corpus. Receipts describe execution, not authorization.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parent
PREFIX = 'research/integration/w2_w4_w6/usref_integration/'
STAGE = PREFIX + 'stage.json'
HEX = re.compile(r'^[0-9a-f]{40}$')
MODES = ('head', 'effective-tree', 'combined')
HOLD = {'merge_authorized': False, 'publication_authorized': False,
        'real_source_access_authorized': False, 'protection_enforcement': 'UNVERIFIED'}


class Rejected(ValueError):
    pass


def need(ok, reason):
    if not ok:
        raise Rejected(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def load(path):
    p = Path(path)
    need(p.is_file() and not p.is_symlink() and 0 < p.stat().st_size <= 32*1024*1024,
         'Missing, empty, symlinked or oversized JSON receipt')
    def unique(pairs):
        d = {}
        for k, v in pairs:
            need(k not in d, 'Duplicate JSON keys')
            d[k] = v
        return d
    return json.loads(p.read_text(encoding='utf-8'), object_pairs_hook=unique)


def git(repo, *args, data=None, extra=None):
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_AUTHOR_NAME': 'Synthetic tree envelope', 'GIT_AUTHOR_EMAIL': 'synthetic@example.invalid',
           'GIT_COMMITTER_NAME': 'Synthetic tree envelope', 'GIT_COMMITTER_EMAIL': 'synthetic@example.invalid',
           'GIT_AUTHOR_DATE': '2000-01-01T00:00:00Z', 'GIT_COMMITTER_DATE': '2000-01-01T00:00:00Z', **(extra or {})}
    r = subprocess.run(['git', '-C', str(repo), *args], input=data, capture_output=True,
                       env=env, timeout=120)
    need(r.returncode == 0, 'Git operation failed: ' + ' '.join(args[:2]) + '\n' + r.stderr.decode(errors='replace')[:1500])
    return r.stdout


def oid(repo, value):
    need(type(value) is str and HEX.fullmatch(value) and value != '0'*40, 'Invalid Git identity')
    return git(repo, 'rev-parse', '--verify', value+'^{commit}').decode().strip()


def tree(repo, ref):
    return git(repo, 'rev-parse', '--verify', ref+'^{tree}').decode().strip()


def listing(repo, ref):
    out = {}
    for entry in git(repo, 'ls-tree', '-rz', ref).split(b'\0'):
        if not entry:
            continue
        header, name = entry.split(b'\t', 1)
        mode, kind, blob = header.decode().split()
        name = name.decode('utf-8')
        need(not name.startswith('/') and '..' not in PurePosixPath(name).parts, 'Unsafe tree path')
        out[name] = [mode, kind, blob]
    return out


def event_identity(event, name, status_sha, run_id, attempt):
    need(event.get('repository', {}).get('full_name') == 'LystadJS/UNGA81-Transcript-Agent', 'Wrong repository')
    if name == 'pull_request':
        p = event['pull_request']
        need(p['head']['repo']['full_name'] == event['repository']['full_name'], 'Fork gate changes require independent review')
        head, base = p['head']['sha'], p['base']['sha']
        current = {'pr': p['number'], 'base_ref': 'refs/heads/'+p['base']['ref']}
    elif name == 'push':
        need(event.get('ref') == 'refs/heads/main' and not event.get('deleted'), 'Only nondeleted main pushes')
        head, base = event['after'], event['before']
        need(status_sha == head, 'Push status mismatch')
        current = {'head_ref': event['ref']}
    elif name == 'merge_group':
        g = event['merge_group']
        head, base = g['head_sha'], g['base_sha']
        need(status_sha == head, 'Merge queue status mismatch')
        current = {'head_ref': g['head_ref'], 'base_ref': g['base_ref']}
    else:
        raise Rejected('Unsupported event, including manual-dispatch acceptance')
    for x in (head, base, status_sha):
        need(type(x) is str and HEX.fullmatch(x) and x != '0'*40, 'Malformed event SHA')
    need(str(run_id).isdigit() and str(attempt).isdigit(), 'Invalid run identity')
    return {'event': name, 'status_sha': status_sha, 'head': head, 'base': base,
            'run_id': str(run_id), 'attempt': str(attempt), 'freshness': current}


def check_fresh(repo, identity):
    """GET-only, run before and after execution. Never retrieves PR body/source."""
    f = identity['freshness']
    if 'pr' in f:
        req = urllib.request.Request('https://api.github.com/repos/LystadJS/UNGA81-Transcript-Agent/pulls/'+str(f['pr']),
                                     headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'usref-synthetic-gate'})
        token = os.environ.get('GH_READ_TOKEN')
        if token:
            req.add_header('Authorization', 'Bearer '+token)
        with urllib.request.urlopen(req, timeout=25) as stream:
            p = json.load(stream)
        need(p['head']['sha'] == identity['head'] and 'refs/heads/'+p['base']['ref'] == f['base_ref'],
             'Stale head or retargeted base')
    for key, expected in [('head_ref', identity['head']), ('base_ref', identity['base'])]:
        if key in f:
            ref = f[key]
            need(ref.startswith('refs/') and not any(c in ref for c in '\r\n\0 '), 'Invalid ref')
            raw = git(repo, 'ls-remote', '--exit-code', 'origin', ref).decode().splitlines()
            need(len(raw) == 1 and raw[0].split()[0] == expected, 'Stale or missing '+key)
    return True


def merged(repo, left, right):
    raw = git(repo, 'merge-tree', '--write-tree', left, right).decode().strip()
    need(HEX.fullmatch(raw), 'Conflict or ambiguous merge-tree output')
    # No ref is created, moved or merged by commit-tree.
    envelope = git(repo, 'commit-tree', raw, '-p', left, '-p', right,
                   data=b'Unreferenced synthetic integration tree; no merge authorization\n').decode().strip()
    return envelope


def set_stage(repo, ref, stage):
    body = (json.dumps({'schema': 'un.usref-adoption-stage.v1', 'stage': stage}, indent=2)+'\n').encode()
    blob = git(repo, 'hash-object', '-w', '--stdin', data=body).decode().strip()
    with tempfile.TemporaryDirectory(prefix='usref-index-') as tmp:
        env = {'GIT_INDEX_FILE': str(Path(tmp)/'index')}
        git(repo, 'read-tree', ref, extra=env)
        git(repo, 'update-index', '--add', '--cacheinfo', '100644,'+blob+','+STAGE, extra=env)
        return git(repo, 'write-tree', extra=env).decode().strip()


def stage_in(repo, ref, policy, allow_pre_adoption=False):
    entries = listing(repo, ref)
    all_paths = {p for x in policy['payloads'] for p in x['integration_paths']}
    # The bridge is pre-existing; bootstrap permits only its exact base version.
    bridge = 'research/integration/w2_w4_w6/test_w4_bridge.py'
    historical = listing(repo, policy['historical_main'])
    if STAGE not in entries:
        need(allow_pre_adoption, 'Required stage declaration was removed')
        stage = 'bootstrap'
    else:
        need(entries[STAGE][:2] == ['100644', 'blob'], 'Unsafe stage declaration')
        s = json.loads(git(repo, 'show', ref+':'+STAGE))
        need(set(s) == {'schema', 'stage'} and s['schema'] == 'un.usref-adoption-stage.v1', 'Invalid stage declaration')
        stage = s['stage']
    need(stage in policy['stage_order'], 'Unknown declared adoption stage')
    level = policy['stage_order'].index(stage)
    required = set()
    for p in policy['payloads'][:level]:
        pinned = listing(repo, p['head_sha'])
        for name in p['integration_paths']:
            need(entries.get(name) == pinned.get(name) and entries.get(name, [])[:2] == ['100644', 'blob'],
                 'Missing, mutated or wrong-mode frozen payload: '+name)
            required.add(name)
    for name in all_paths-required:
        need(entries.get(name) == historical.get(name), 'Payload contradicts declared stage: '+name)
    for name in entries:
        if name.startswith(('research/integration/w2_w4_w6/waggoner/', 'research/integration/w2_w4_w6/pr92_review/')):
            need(name in required, 'Undeclared product/reviewer path: '+name)
    if not allow_pre_adoption or STAGE in entries:
        for name in policy['gate_paths']:
            need(entries.get(name, [])[:2] == ['100644', 'blob'], 'Required gate file missing or wrong-mode: '+name)
    return stage


def safe_output(path, repos):
    p = Path(path).resolve()
    for repo in repos:
        r = Path(repo).resolve()
        need(p != r and r not in p.parents and p not in r.parents, 'Output overlaps a repository')
    need(not p.exists(), 'Output must be new; stale evidence cannot be reused')
    p.mkdir(parents=True)
    return p


def materialize(repo, ref, dest, policy):
    """Write only test/code allowlist; no git checkout or transcript/corpus loader."""
    dest.mkdir(parents=True, exist_ok=False)
    selected = {}
    explicit = set(policy['gate_paths']) | {p for x in policy['payloads'] for p in x['integration_paths']}
    for name, entry in listing(repo, ref).items():
        if name in explicit or (any(name.startswith(x) for x in policy['materialize_prefixes'])
                and Path(name).suffix in policy['materialize_suffixes']):
            need(entry[:2] == ['100644', 'blob'], 'Symlink, submodule or executable mode rejected: '+name)
            selected[name] = entry
    for name, entry in selected.items():
        p = dest/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(git(repo, 'cat-file', 'blob', entry[2]))
    return selected


def prepare(repo, control, out, mode, identity, policy):
    need(mode in MODES, 'Unknown mode')
    head, base = oid(repo, identity['head']), oid(repo, identity['base'])
    before_refs = git(repo, 'show-ref')
    original_index = git(repo, 'write-tree').decode().strip()
    gate_paths = policy['gate_paths']
    candidate_stage = stage_in(repo, head, policy)
    base_stage = stage_in(repo, base, policy, allow_pre_adoption=True)
    need(policy['stage_order'].index(candidate_stage) >= policy['stage_order'].index(base_stage), 'Adoption stage cannot downgrade')
    ref = head if mode == 'head' else merged(repo, head, base)
    stages = []
    if mode == 'combined':
        initial = listing(repo, ref)
        for payload in policy['payloads']:
            ref = merged(repo, ref, oid(repo, payload['head_sha']))
            stages.append({'pr': payload['number'], 'head': payload['head_sha'], 'tree': tree(repo, ref)})
        tested = set_stage(repo, ref, 'integrated')
        after = listing(repo, tested)
        allowed = {STAGE} | {p for x in policy['payloads'] for p in x['integration_paths']}
        changed = {p for p in set(initial)|set(after) if initial.get(p) != after.get(p)}
        need(changed <= allowed, 'Combined tree changed an unrelated path')
        need(set(initial) <= set(after), 'Combined tree deleted an existing path')
    else:
        tested = tree(repo, ref)
    stage = stage_in(repo, tested, policy)
    gate_inventory = {p: listing(repo, tested)[p] for p in gate_paths}
    # The separately executing controller must equal gate code in the tested tree.
    for p, entry in gate_inventory.items():
        raw = (Path(control)/p).read_bytes()
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == entry[2]
             or (mode == 'combined' and p == STAGE), 'Controller differs from tested gate: '+p)
    code = materialize(repo, tested, out/'candidate', policy)
    hist = out/'historical'
    hist.mkdir()
    for label, revision, name in [('pr87', policy['pr87']['head_sha'], policy['pr87']['source_path']),
            ('pr93', policy['payloads'][2]['head_sha'], 'research/integration/w2_w4_w6/pr92_review/test_review.py')]:
        (hist/(label+'.py')).write_bytes(git(repo, 'show', revision+':'+name))
    need(git(repo, 'show-ref') == before_refs and git(repo, 'write-tree').decode().strip() == original_index,
         'Reference or controller index mutation')
    result = {**identity, 'schema': 'un.usref-gate-identity.v1', 'mode': mode, 'stage': stage,
              'control_commit': head, 'tested_tree': tested, 'head_tree': tree(repo, head), 'base_tree': tree(repo, base),
              'candidate_stage': candidate_stage, 'assembly': stages,
              'gate_inventory': gate_inventory, 'policy_sha256': sha((Path(control)/PREFIX/'policy.json').read_bytes()),
              'materialized_paths': sorted(code), 'refs_unchanged': True, 'controller_index_unchanged': True,
              'coverage': 'gate_bootstrap_only' if stage == 'bootstrap' else 'offline_synthetic_product', **HOLD}
    dump(out/'identity.json', result)
    return result


def validate_final(event, results, needs):
    need(set(needs) == {'checks'} and needs['checks'].get('result') == 'success', 'Mandatory job did not succeed')
    need(type(results) is dict and set(results) == set(MODES), 'Missing or extra mode receipts')
    for mode, bundle in results.items():
        i, r = bundle['identity'], bundle['receipt']
        for k in ('event', 'status_sha', 'head', 'base', 'run_id', 'attempt', 'freshness'):
            need(i.get(k) == event.get(k), 'Stale or wrong event identity: '+k)
        need(i.get('mode') == mode and r.get('mode') == mode, 'Wrong mode')
        need(r.get('identity_sha256') == bundle['identity_sha256'], 'Receipt identity binding failed')
        need(r.get('result') == 'pass' and r.get('errors') == [] and r.get('skipped') == [], 'Failed or incomplete execution')
        need(r.get('stage') == i.get('stage') and r.get('coverage') == i.get('coverage'), 'Stage/coverage mismatch')
        need(i.get('refs_unchanged') is True and i.get('controller_index_unchanged') is True, 'Mutation detected')
        need(r.get('holds') == HOLD, 'Receipt attempted to grant authority')
        expected = required_suites(i['stage'])
        need(set(r.get('suites', {})) == set(expected), 'Missing or unexpected suite inventory')
        for suite, minimum in expected.items():
            s = r['suites'][suite]
            need(s.get('result') == 'pass' and type(s.get('tests')) is int and s['tests'] >= minimum
                 and s.get('skipped') == 0 and s.get('errors') == 0 and s.get('failures') == 0,
                 'Incomplete mandatory suite: '+suite)
        need(bundle.get('evidence_verified') is True, 'Missing/corrupt evidence')
    need(results['combined']['identity']['stage'] == 'integrated', 'Combined coverage not integrated')
    need(results['head']['identity']['stage'] == results['effective-tree']['identity']['stage'], 'Ambiguous actual stage')
    return {'schema':'un.usref-required-check.v1', 'result':'pass', 'event_identity':event,
            'actual_stage': results['head']['identity']['stage'],
            'combined_tree': results['combined']['identity']['tested_tree'],
            'combined_coverage': 'offline_synthetic_dry_run', **HOLD}


def required_suites(stage):
    need(stage in ('bootstrap', 'phase1', 'phase2', 'integrated'), 'Unknown stage')
    s = {'gate-controls': 30, 'w4': 25, 'interchange': 14, 'guards': 11}
    if stage != 'bootstrap':
        s.update(phase1=40, bridge=49, pr87=7)
    if stage in ('phase2', 'integrated'):
        s.update({'phase2-build':4, 'phase2-node':12, 'source-replay':8, 'browser':17, 'pr93':7})
    return s


def read_bundle(folder):
    folder = Path(folder)
    i, r = load(folder/'identity.json'), load(folder/'receipt.json')
    files = r.get('files')
    need(type(files) is dict and files, 'No retained evidence')
    for name, expected in files.items():
        p = folder/name
        need(not Path(name).is_absolute() and '..' not in Path(name).parts and p.is_file()
             and not p.is_symlink() and sha(p.read_bytes()) == expected, 'Missing/corrupt artifact member')
    return {'identity':i, 'receipt':r, 'identity_sha256':sha((folder/'identity.json').read_bytes()), 'evidence_verified':True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['prepare','finalize'])
    p.add_argument('--repo', type=Path, required=True); p.add_argument('--control', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True); p.add_argument('--mode', choices=MODES)
    p.add_argument('--artifacts', type=Path)
    a = p.parse_args()
    event = event_identity(load(os.environ['GITHUB_EVENT_PATH']), os.environ['GITHUB_EVENT_NAME'],
                           os.environ['GITHUB_SHA'], os.environ['GITHUB_RUN_ID'], os.environ['GITHUB_RUN_ATTEMPT'])
    check_fresh(a.repo, event)
    if a.command == 'prepare':
        out = safe_output(a.out, [a.repo, a.control])
        policy = load(a.control/PREFIX/'policy.json')
        prepare(a.repo, a.control, out, a.mode, event, policy)
    else:
        need(a.artifacts is not None, 'Artifact directory required')
        results = {m:read_bundle(a.artifacts/('usref-gate-'+m)) for m in MODES}
        policy = load(a.control/PREFIX/'policy.json')
        from run_suites import audit_bundle
        with tempfile.TemporaryDirectory(prefix='usref-final-identity-') as tmp:
            for mode in MODES:
                expected = prepare(a.repo, a.control, Path(tmp)/mode, mode, event, policy)
                need(results[mode]['identity'] == expected, 'Identity differs from independently reconstructed tree')
                audit_bundle(a.artifacts/('usref-gate-'+mode), results[mode], policy)
        result = validate_final(event, results, json.loads(os.environ['GATE_NEEDS']))
        check_fresh(a.repo, event)
        dump(a.out, result)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
