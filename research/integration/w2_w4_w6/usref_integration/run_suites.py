"""Execute retained synthetic suites; missing runtimes and skipped tests are fatal.

Historical reviewer output is retained unchanged and wrapped with actual tested
head/base/tree identity. A frozen historical receipt is never used as that identity.
"""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import traceback
from gate import ROOT, HOLD, Rejected, need, dump, load, sha, required_suites


def unittest_result(text, minimum):
    runs = re.findall(r'^Ran (\d+) tests? in ', text, re.M)
    ids = re.findall(r'^(test_\w+) \(([^)]+)\) \.\.\. ', text, re.M)
    need(len(runs) == 1 and re.search(r'^OK\s*$', text, re.M), 'Missing unittest completion')
    outcomes = re.findall(r'^test_\w+ \([^)]+\) \.\.\. (.*)$', text, re.M)
    need(len(outcomes) == len(ids) and all(x == 'ok' for x in outcomes), 'Nonpassing raw unittest outcome')
    n = int(runs[0])
    need(n >= minimum and len(ids) == n and len(set(ids)) == n, 'Missing/duplicated test inventory')
    need(not re.search(r'\.\.\. skipped|^OK \(|^FAILED|^ERROR:|^FAIL:', text, re.M), 'Skipped/failed unittest')
    return {'result':'pass','tests':n,'test_ids':[b+'.'+a for a,b in ids], 'skipped':0,'errors':0,'failures':0}


def tap_result(text, minimum):
    counts = {}
    for key in ('tests','pass','fail','cancelled','skipped','todo'):
        values = re.findall(r'^# '+key+r' (\d+)\s*$', text, re.M)
        need(len(values) == 1, 'Missing or repeated TAP count: '+key)
        counts[key] = int(values[0])
    need(not re.search(r'^not ok|# (?:SKIP|TODO)', text, re.M), 'Nonpassing raw TAP outcome')
    names = re.findall(r'^ok \d+ - (.+)$', text, re.M)
    need(counts['tests'] == counts['pass'] == len(names) and len(set(names)) == len(names)
         and counts['tests'] >= minimum and all(counts[k] == 0 for k in ('fail','cancelled','skipped','todo')),
         'Incomplete/failed/skipped TAP suite')
    return {'result':'pass','tests':counts['tests'],'test_ids':names,'skipped':0,'errors':0,'failures':0}


def check_native_record(path, minimum):
    r = load(path)
    need(r.get('result') == 'pass' and type(r.get('tests_run')) is int and r['tests_run'] >= minimum
         and r.get('failures') in (0, []) and r.get('errors') in (0, []) and r.get('skipped') == [],
         'Native receipt not complete')
    need(r.get('publication_eligible') is False, 'Native receipt grants publication')
    return r


def runtimes(policy):
    for binary in ('Rscript','node'):
        need(shutil.which(binary), 'Mandatory runtime missing: '+binary)
    def version(cmd):
        r = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
        need(r.returncode == 0, 'Runtime could not execute')
        return r.stdout.strip()
    actual = {'python':platform.python_version(), 'R':version(['Rscript','--vanilla','-e','cat(as.character(getRversion()))']),
              'node':version(['node','--version']).lstrip('v')}
    for pkg in ('numpy','scipy','jsonschema','playwright'):
        actual[pkg] = importlib.metadata.version(pkg)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        need(Path(p.chromium.executable_path).is_file(), 'Mandatory Chromium missing')
        browser = p.chromium.launch(headless=True)
        actual['chromium'] = browser.version
        browser.close()
    for key, value in actual.items():
        need(value == policy['runtime_baseline'][key], 'Runtime drift requires reviewed compatibility evidence: '+key)
    return actual


def run(control, out, axe):
    identity = load(out/'identity.json')
    policy = load(control/'policy.json')
    expected = required_suites(identity['stage'])
    evidence = out/'evidence'
    evidence.mkdir(exist_ok=False)
    logs = evidence/'logs'; logs.mkdir()
    report = {'schema':'un.usref-gate-execution.v1','mode':identity['mode'],'stage':identity['stage'],
              'coverage':identity['coverage'],'identity_sha256':sha((out/'identity.json').read_bytes()),
              'result':'fail','errors':[],'skipped':[],'suites':{},'holds':HOLD,'files':{}}
    candidate = out/'candidate'
    env = {**os.environ, 'GITHUB_SHA':identity['head'], 'PYTHONHASHSEED':'0',
           'OPENBLAS_NUM_THREADS':'1', 'MKL_NUM_THREADS':'1','OMP_NUM_THREADS':'1',
           'PR82_CANDIDATE_ROOT':str(candidate), 'PR82_REVIEW_MODE':identity['mode'],
           'PR82_REVIEW_RECEIPT':str(evidence/'pr87-original.json'), 'PHASE2_BUILD_DIR':str(out/'build')}
    # Tests do not receive the freshness-read token or repository write credentials.
    env.pop('GH_READ_TOKEN', None); env.pop('GITHUB_TOKEN', None)
    def command(label, args, kind='unittest', minimum=None, cwd=None):
        target = logs/(label+'.log')
        with target.open('w') as f:
            try:
                p = subprocess.run(args, cwd=cwd or candidate, env=env, stdout=f, stderr=subprocess.STDOUT,
                                   text=True, timeout=600)
            except subprocess.TimeoutExpired as exc:
                raise Rejected('Suite timeout: '+label) from exc
        text = target.read_text()
        print(text, flush=True)
        need(p.returncode == 0, 'Command failed: '+label)
        if kind == 'unittest':
            result = unittest_result(text, minimum or expected[label])
        elif kind == 'tap':
            result = tap_result(text, minimum or expected[label])
        elif kind == 'interchange':
            first = json.JSONDecoder().raw_decode(text.strip())[0]
            need(first['status'] == 'pass' and first['positive'] == 1 and first['negative'] == 13
                 and first['network_access'] is False and first['holdout_access'] is False, 'Interchange receipt mismatch')
            result = {'result':'pass','tests':14,'skipped':0,'failures':0,'errors':0}
        elif kind == 'source-replay':
            r = json.loads(text)
            need(r['result'] == 'pass' and r['scenarios'] == 8 and r['phase1_pins'] == 6
                 and r['publication_eligible'] is False, 'Incomplete source-bound replay')
            result = {'result':'pass','tests':8,'skipped':0,'failures':0,'errors':0}
        else:
            return
        result['log'] = str(target.relative_to(out)); result['log_sha256'] = sha(target.read_bytes())
        report['suites'][label] = result
    try:
        report['runtimes'] = runtimes(policy)
        need(axe.is_file() and not axe.is_symlink(), 'Mandatory axe file missing')
        package = load(axe.parent/'package.json')
        need(package['name'] == 'axe-core' and package['version'] == policy['runtime_baseline']['axe'], 'Wrong axe package')
        report['runtimes']['axe'] = package['version']; report['axe_sha256'] = sha(axe.read_bytes())
        py = sys.executable
        command('gate-controls',[py,str(control/'test_gate.py'),'-v'], minimum=1, cwd=control)
        command('w4',[py,'-m','unittest','discover','-s','research/longitudinal','-p','test_*.py','-v'])
        command('interchange',['node','docs/parallel-work/validate-contract.cjs'], 'interchange')
        command('guards',['node','docs/parallel-work/test-w1-w2-inference-readiness.cjs'], 'tap')
        if identity['stage'] != 'bootstrap':
            command('phase1',[py,'-m','research.integration.w2_w4_w6.waggoner.run_tests',
                             '--require-complete','--receipt',str(evidence/'phase1-original.json')])
            check_native_record(evidence/'phase1-original.json',40)
            command('bridge',[py,'-m','unittest','research.integration.w2_w4_w6.test_w4_bridge','-v'])
            command('pr87',[py,str(out/'historical/pr87.py')])
            check_native_record(evidence/'pr87-original.json',7)
        if identity['stage'] in ('phase2','integrated'):
            mod = 'research.integration.w2_w4_w6.waggoner.phase2.'
            folder = 'research/integration/w2_w4_w6/waggoner/phase2/'
            command('phase2-build',[py,'-m','unittest',mod+'test_build','-v'])
            command('build',[py,'-m',mod+'build','--out',str(out/'build')],kind='build')
            command('source-replay',['node',folder+'verify_catalogue.cjs',str(out/'build')],'source-replay')
            command('phase2-node',['node','--test',folder+'test_views.cjs'],'tap')
            command('browser',[py,'-m',mod+'test_browser','--build-dir',str(out/'build'),
                               '--artifact-dir',str(evidence/'browser'),'--require-axe','--axe',str(axe)])
            check_native_record(evidence/'browser/browser-receipt.json',17)
            reviewer = candidate/'research/integration/w2_w4_w6/pr92_review/test_review.py'
            if identity['stage'] == 'phase2':
                reviewer = out/'historical/pr93.py'
            command('pr93',[py,str(reviewer),'--build',str(out/'build'),'--out',str(evidence/'independent'),
                           '--axe-results',str(evidence/'browser/axe-results.json')])
            check_native_record(evidence/'independent/review-receipt.json',7)
            observations = load(evidence/'independent/observations.json')
            need(observations['historical_targets'] == observations['resolved_historical_targets'] == 444
                 and observations['palette_selections'] == 48 and observations['independent_comparisons'] == 240
                 and observations['independent_transitions'] == 192, 'Incomplete independent review coverage')
            # Keep original axe incompletes and independent resolution as separate files.
            shutil.copytree(out/'build', evidence/'build')
        need(set(report['suites']) == set(expected), 'Suite inventory mismatch')
        report['result'] = 'pass'
    except Exception as exc:
        report['errors'].append(type(exc).__name__+': '+str(exc))
        (evidence/'failure.txt').write_text(traceback.format_exc())
    finally:
        for p in sorted(evidence.rglob('*')):
            if p.is_file():
                need(not p.is_symlink(), 'Symlink in retained evidence')
                report['files'][str(p.relative_to(out))] = sha(p.read_bytes())
        dump(out/'receipt.json',report)
    return report['result'] == 'pass'


def audit_bundle(folder, bundle, policy):
    """Reconcile fixed evidence/ID inventories with logs, native receipts and outcomes.

    The producer manifest is not an authority to choose which evidence is required.
    Original PR87 labels remain historical; returned wrappers bind their new run.
    """
    from evidence_contract import (require_inventory, require_test_ids, bind_native,
                                   validate_build, validate_accessibility)
    folder = Path(folder)
    r = bundle['receipt']; i = bundle['identity']
    need(r.get('runtimes') == policy['runtime_baseline'], 'Runtime receipt mismatch')
    require_inventory(folder, bundle)
    checked_suites = {}
    for name, expected in required_suites(i['stage']).items():
        relative = 'evidence/logs/'+name+'.log'
        path = folder/relative
        text = path.read_text()
        if name in ('guards','phase2-node'):
            checked = tap_result(text,expected)
        elif name in ('interchange','source-replay'):
            checked = {'result':'pass','tests':expected,'skipped':0,'failures':0,'errors':0}
            obj, end = json.JSONDecoder().raw_decode(text.strip())
            tail = text.strip()[end:].strip()
            need(tail in ('', '\\n'), 'Unparsed trailing result content')
            if name == 'interchange':
                need(obj.get('status') == 'pass' and obj.get('positive') == 1 and obj.get('negative') == 13
                     and obj.get('network_access') is False and obj.get('holdout_access') is False, 'Bad interchange evidence')
            else:
                need(obj.get('result') == 'pass' and obj.get('scenarios') == 8 and obj.get('phase1_pins') == 6
                     and obj.get('publication_eligible') is False, 'Bad source replay evidence')
        else:
            checked = unittest_result(text,expected)
        require_test_ids(name, checked, policy)
        for key in checked:
            need(r['suites'][name].get(key) == checked[key], 'Summary differs from raw test evidence')
        need(r['suites'][name].get('log') == relative and
             r['suites'][name].get('log_sha256') == sha(path.read_bytes()), 'Log binding mismatch')
        checked_suites[name] = checked
    native_files = {}
    if i['stage'] != 'bootstrap':
        native_files.update(phase1='evidence/phase1-original.json',pr87='evidence/pr87-original.json')
    if i['stage'] in ('phase2','integrated'):
        native_files.update(browser='evidence/browser/browser-receipt.json',pr93='evidence/independent/review-receipt.json')
    wrappers = []
    for name, relative in native_files.items():
        path = folder/relative
        native = check_native_record(path, checked_suites[name]['tests'])
        wrappers.append(bind_native(name, native, checked_suites[name], i, policy,
                                    sha(path.read_bytes()), r['suites'][name]['log_sha256']))
    bundle['native_execution_bindings'] = wrappers
    if i['stage'] in ('phase2','integrated'):
        counts = validate_build(folder, policy)
        bundle['semantic_evidence'] = validate_accessibility(folder, policy, counts)
    bundle['semantic_evidence_verified'] = True


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True); p.add_argument('--axe',type=Path,required=True)
    a = p.parse_args()
    raise SystemExit(0 if run(ROOT,a.out.resolve(),a.axe.resolve()) else 1)
