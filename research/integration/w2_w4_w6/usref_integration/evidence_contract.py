"""Stage-defined evidence and cross-record checks, independent of producer manifests.

This contract checks completeness and consistency. It is not a signed authority,
proof of arbitrary log truth, scientific acceptance or publication permission.
Frozen synthetic fixture identities and retained test IDs are reviewed policy.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from gate import need, load, sha, required_suites

SCENES = ('moving', 'missing-us', 'support-gap', 'hidden-dimension', 'zero-gap',
          'display-withheld', 'empty', 'failed-source')
COUNTRIES = ('USA', 'BRA', 'CAN', 'FRA', 'IND', 'GBR')
BROWSER_FILES = ('all-country-gaps.csv', 'axe-results.json', 'browser-receipt.json',
                 'desktop.png', 'mobile.png', 'paired-trajectories.png',
                 'paired-trajectories.svg', 'standalone.html', 'view-replay.json')
BUILD_FILES = ('catalogue.json', 'index.html', 'manifest.json', 'verification.json')
INDEPENDENT_FILES = ('contrast-resolution.json', 'observations.json',
                     'review-export.svg', 'review-receipt.json')


def number(x):
    return type(x) in (float, int) and math.isfinite(x)


def same_number(x, y, name):
    need(number(x) and number(y) and math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12),
         'Inconsistent numerical evidence: '+name)


def required_files(stage):
    """A producer may add diagnostic files, but cannot remove a mandatory member."""
    files = {'evidence/logs/'+name+'.log' for name in required_suites(stage)}
    if stage != 'bootstrap':
        files |= {'evidence/phase1-original.json', 'evidence/pr87-original.json'}
    if stage in ('phase2', 'integrated'):
        files |= {'evidence/logs/build.log'}
        files |= {'evidence/browser/'+n for n in BROWSER_FILES}
        files |= {'evidence/build/'+n for n in BUILD_FILES}
        files |= {'evidence/independent/'+n for n in INDEPENDENT_FILES}
        files |= {'evidence/independent/'+n+'.png' for n in (*SCENES, 'moving-mobile')}
    return files


def require_inventory(folder, bundle):
    wanted = required_files(bundle['identity']['stage'])
    files = bundle['receipt']['files']
    need(wanted <= set(files), 'Mandatory stage evidence absent from manifest: '+
         ', '.join(sorted(wanted-set(files))))
    for name in wanted:
        p = Path(folder)/name
        need(p.is_file() and p.stat().st_size > 0, 'Mandatory stage evidence missing: '+name)
    return wanted


def require_test_ids(suite, checked, policy):
    """Retained IDs are independent of the producer's raw log and summary count."""
    expected = policy['mandatory_test_ids'].get(suite)
    if expected is None:
        need(suite in ('interchange', 'source-replay'), 'Unregistered mandatory test inventory')
        return
    observed = checked.get('test_ids')
    need(type(observed) is list and len(observed) == len(set(observed)), 'Duplicate/missing raw IDs')
    actual = {'count':len(observed), 'sha256':sha(json.dumps(
        sorted(observed), ensure_ascii=True, separators=(',', ':')).encode())}
    need(actual == expected, 'Retained test inventory was removed/replaced: '+suite)
    need(checked['tests'] == len(observed), 'Raw ID count mismatch')



def bind_native(label, native, checked, identity, policy, native_hash, log_hash):
    need(type(native.get('tests_run')) is int and native['tests_run'] == checked['tests'],
         'Native count differs from raw test IDs: '+label)
    need(native.get('result') == 'pass' and native.get('skipped') == []
         and native.get('publication_eligible') is False, 'Incomplete native receipt: '+label)
    for key in ('errors', 'failures'):
        value = native.get(key)
        need((type(value) is int and value == 0) or (type(value) is list and not value),
             'Failed or malformed native result: '+label)
    original_identity = {}
    if label == 'phase1':
        need(native.get('head_sha') == identity['head'], 'Native Phase1 head differs from actual execution')
        need(native.get('kind') == 'synthetic_engineering_tests'
             and native.get('python') == policy['runtime_baseline']['python']
             and native.get('real_data_eligible') is False
             and type(native.get('holdout_transcripts_opened')) is int
             and native['holdout_transcripts_opened'] == 0, 'Invalid Phase1 native context')
        original_identity = {'head_sha': native['head_sha']}
    elif label == 'pr87':
        # These labels are intentionally historical. Do not rewrite them to the new head.
        need(native.get('kind') == 'independent_pr82_synthetic_review'
             and native.get('candidate_head') == policy['payloads'][0]['head_sha']
             and native.get('review_base') == policy['pr87']['receipt_base_sha']
             and native.get('mode') == identity['mode']
             and type(native.get('holdout_transcripts_opened')) is int
             and native['holdout_transcripts_opened'] == 0, 'Invalid historical PR87 receipt context')
        original_identity = {k: native[k] for k in ('candidate_head', 'review_base', 'mode')}
    elif label == 'browser':
        need(native.get('suite') == 'phase2-strict-browser'
             and native.get('source_scope') == 'generated_synthetic_only'
             and native.get('browser') == policy['runtime_baseline']['chromium']
             and native.get('python') == policy['runtime_baseline']['python'], 'Invalid browser native context')
    elif label == 'pr93':
        need(native.get('suite') == 'pr92-independent-contrast-review'
             and native.get('complete_wcag_certification') is False
             and type(native.get('real_sources_opened')) is int
             and native['real_sources_opened'] == 0, 'Invalid independent native context')
    else:
        need(False, 'Unregistered native suite')
    # This wrapper is derived by the finalizer and separately returned to the ledger.
    # It is not written into any original producer/reviewer receipt.
    return {'suite': label, 'actual_execution': {k:identity[k] for k in
            ('head', 'base', 'status_sha', 'run_id', 'attempt', 'mode', 'tested_tree')},
            'native_sha256':native_hash, 'raw_log_sha256':log_hash,
            'tests':checked['tests'], 'original_receipt_identity':original_identity}


def selector_inventory(names):
    need(type(names) is list and all(type(n) is str and n for n in names)
         and len(names) == len(set(names)), 'Missing/duplicate selector inventory')
    return {'count':len(names), 'selectors_sha256':sha(json.dumps(
        sorted(names), ensure_ascii=True, separators=(',', ':')).encode())}


def rgba(value):
    need(type(value) is list and len(value) == 4 and all(number(x) and 0 <= x <= 255 for x in value)
         and value[3] == 255, 'Invalid/unresolved transparent authored color')
    return value[:3]


def luminance(rgb):
    xs = [x/255 for x in rgb]
    ys = [x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in xs]
    return sum(a*b for a,b in zip(ys, (.2126, .7152, .0722)))


def ratio(foreground, background):
    a,b = sorted((luminance(foreground), luminance(background)))
    return (b+.05)/(a+.05)


def check_contrast_record(row):
    need(type(row) is dict and row.get('passed') is True and row.get('threshold') == 4.5,
         'Measured contrast result failed or threshold changed')
    fg = rgba(row.get('foreground'))
    backgrounds = row.get('backgrounds')
    need(type(backgrounds) is list and backgrounds, 'Missing contrast backgrounds')
    bgs = [rgba(b) for b in backgrounds]
    image = row.get('background_image')
    need(type(image) is str, 'Missing background image description')
    if image != 'none':
        need(image.startswith('repeating-linear-gradient('), 'Unreviewed background pattern')
        colors = re.findall(r'rgb\((\d+), (\d+), (\d+)\)', image)
        need(colors and bgs == [[int(c) for c in color] for color in colors],
             'Pattern stops missing from contrast measurement')
    minimum = min(ratio(fg,bg) for bg in bgs)
    need(minimum >= 4.5, 'Independent luminance calculation fails text contrast')
    same_number(row.get('minimum_ratio'), minimum, 'measured contrast')
    return minimum


def validate_build(folder, policy):
    root = Path(folder)/'evidence/build'
    manifest = load(root/'manifest.json')
    pinned = policy['frozen_synthetic_build']
    need(manifest == {k:v for k,v in pinned.items() if k != 'manifest_sha256'},
         'Synthetic build manifest differs from reviewed fixed fixture')
    need(sha((root/'manifest.json').read_bytes()) == pinned['manifest_sha256'], 'Manifest bytes changed')
    for name, expected in pinned['files'].items():
        need(name in ('index.html','catalogue.json','verification.json') and
             sha((root/name).read_bytes()) == expected, 'Frozen synthetic build bytes differ: '+name)
    catalogue, verification = load(root/'catalogue.json'), load(root/'verification.json')
    need(catalogue['sha256'] == manifest['catalogue_sha256'] and
         catalogue['phase1_head'] == manifest['phase1_head'] == policy['payloads'][0]['head_sha'],
         'Build/model identity mismatch')
    need([s['id'] for s in catalogue['scenes']] == list(SCENES)
         and [v['id'] for v in verification] == list(SCENES), 'Missing synthetic scene')
    counts = {'independent_ready_profiles':0,'independent_comparisons':0,'independent_transitions':0}
    for scene, v in zip(catalogue['scenes'],verification):
        model = scene['model']
        need(model == v['model'] and model['split'] == v['source']['split'] == 'synthetic',
             'Catalogue differs from source-bound verification model')
        need(model['scope']['countries'] == list(COUNTRIES) and len(model['periods']) == 5
             and len(model['comparisons']) == 30 and len(model['transitions']) == 24,
             'Incomplete country-period frame')
        need(model['permissions'] == catalogue['permissions']
             and catalogue['permissions']['publication_eligible'] is False
             and catalogue['permissions']['real_data_eligible'] is False
             and catalogue['permissions']['holdout_access'] is False, 'Fixture authority escalation')
        counts['independent_ready_profiles'] += sum(p['state']=='ready' for p in model['profiles'])
        counts['independent_comparisons'] += len(model['comparisons'])
        counts['independent_transitions'] += len(model['transitions'])
    return counts


def validate_accessibility(folder, policy, model_counts):
    root = Path(folder)/'evidence'
    axe = load(root/'browser/axe-results.json')
    resolution = load(root/'independent/contrast-resolution.json')
    observed = load(root/'independent/observations.json')
    required_scenes = list(SCENES)+['moving-mobile']
    need(type(axe) is list and [s.get('scene') for s in axe] == required_scenes, 'Incomplete axe scan frame')
    targets = {}
    for scan in axe:
        need(scan.get('violations') == [] and scan.get('engine') ==
             {'name':'axe-core', 'version':policy['runtime_baseline']['axe']}, 'Axe violation or engine mismatch')
        need(type(scan.get('incomplete')) is list and len(scan['incomplete']) == 1
             and scan['incomplete'][0].get('id') == 'color-contrast', 'Unreviewed axe incomplete rule')
        pairs = scan['incomplete'][0]['targets']
        need(all(type(t) is list and len(t)==1 for t in pairs), 'Invalid axe selector')
        names = [t[0] for t in pairs]
        need(selector_inventory(names) == policy['axe_target_inventory'][scan['scene']],
             'Historical axe target inventory changed')
        targets[scan['scene']] = names
    need(type(resolution) is list and len(resolution) == 57, 'Incomplete contrast group frame')
    seen = set(); total = palette = palette_checks = 0; palette_min = math.inf
    for group in resolution:
        key = (group.get('source'), group.get('scene'), group.get('country'))
        need(key not in seen, 'Duplicate contrast group'); seen.add(key)
        rows = group.get('records')
        need(type(rows) is list and rows, 'Missing contrast records')
        names = [r.get('selector') for r in rows]
        inventory = selector_inventory(names)
        if key[0] == 'historical-axe-targets':
            need(key[1] in targets and key[2] is None and set(names)==set(targets[key[1]]),
                 'Contrast resolutions do not cover exact axe targets')
            total += len(rows)
        else:
            need(key[0] == 'all-country-palette' and key[1] in SCENES and key[2] in COUNTRIES,
                 'Unknown contrast group')
            expected_count = policy['palette_counts'][key[1]][COUNTRIES.index(key[2])]
            need(len(rows) == expected_count and set(names) == {
                '[data-review-target="'+str(j)+'"]' for j in range(expected_count)}, 'Palette target inventory changed')
            palette += 1; palette_checks += len(rows)
        ratios = [check_contrast_record(r) for r in rows]
        if key[0] == 'all-country-palette':
            palette_min = min(palette_min,*ratios)
    expected_keys = {('historical-axe-targets',s,None) for s in required_scenes} | {
                     ('all-country-palette',s,c) for s in SCENES for c in COUNTRIES}
    need(seen == expected_keys and total == 444 and palette == 48 and palette_checks == 3301,
         'Contrast coverage incomplete')
    # Validate required output counts, tied to the verified model frame above.
    expected = {**model_counts,'historical_targets':total,'resolved_historical_targets':total,
                'palette_selections':palette,'export_text_nodes':53}
    need(set(observed) == set(expected)|{'palette_minimum_ratio','minimum_graphic_focus_ratio'},
         'Missing/unknown independent coverage fields')
    for key,value in expected.items():
        need(type(observed.get(key)) is int and observed[key] == value, 'Independent coverage mismatch: '+key)
    same_number(observed['palette_minimum_ratio'],palette_min,'palette minimum')
    need(number(observed['minimum_graphic_focus_ratio']) and observed['minimum_graphic_focus_ratio'] >= 3,
         'Graphic/focus contrast failed')
    same_number(observed['minimum_graphic_focus_ratio'],policy['reviewed_graphic_focus_minimum_ratio'],
                'graphic/focus minimum for unchanged reviewed build')
    # Exported SVG foregrounds are checked independently over their explicit white canvas.
    raw = (root/'independent/review-export.svg').read_bytes()
    need(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'Unsafe exported SVG')
    try:
        svg = ET.fromstring(raw)
    except ET.ParseError:
        need(False, 'Malformed exported SVG')
    need(not any(e.tag.rsplit('}',1)[-1] in ('script','foreignObject') for e in svg.iter()),
         'Unsafe exported SVG content')
    texts = svg.findall('.//{http://www.w3.org/2000/svg}text')
    need(len(texts)==expected['export_text_nodes'], 'Missing exported SVG text nodes')
    for t in texts:
        color = t.get('fill','')
        need(re.fullmatch('#[0-9a-fA-F]{6}',color), 'Unresolved exported text color')
        need(ratio([int(color[i:i+2],16) for i in (1,3,5)],[255,255,255]) >= 4.5,
             'Exported SVG text contrast failed')
    return {'historical_targets':total,'palette_selections':palette,'palette_checks':palette_checks,
            'minimum_palette_ratio':palette_min,'export_text_nodes':len(texts)}
