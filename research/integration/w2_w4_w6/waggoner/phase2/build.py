"""Build a self-contained fictional catalogue. Never read external analytical input."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
from .. import us_reference as u
from ..make_schema import write_contract
from .fixtures import scenarios

HERE = Path(__file__).resolve().parent
PHASE1_HEAD = '81110db49786a05f9c8f8ce4d5103c92fe255586'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False)


def catalogue():
    write_contract()
    scenes, verification = [], []
    for scene in scenarios():
        source = scene['source']
        receipt = dict(kind='synthetic_consistency_only', hash_basis=u.HASH_BASIS, panel_sha256=u.digest(source))
        model = u.build_us_reference(source, receipt)
        u.validate_result(model, source, receipt)
        scenes.append({k: scene[k] for k in ('id', 'title', 'note')} | {'model': model})
        verification.append(dict(id=scene['id'], source=source, receipt=receipt, model=model))
    payload = dict(schema='un.us-relative-synthetic-catalogue.v1', version='0.1.0',
                   phase1_head=PHASE1_HEAD, permissions=u.PERMISSIONS, scenes=scenes)
    payload['sha256'] = u.digest(payload)
    return payload, verification


def build(out):
    out = Path(out).resolve()
    # Do not turn a development convenience into a public asset build command.
    repo = HERE.parents[4]
    if out == repo or repo in out.parents:
        raise ValueError('Choose a temporary output directory outside the repository')
    out.mkdir(parents=True, exist_ok=True)
    cat, verification = catalogue()
    data = canonical(cat).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    js = (HERE/'views.js').read_text().replace('@@CATALOGUE_BYTES_SHA@@', hashlib.sha256(data.encode()).hexdigest())
    css = (HERE/'views.css').read_text()
    script_hash = base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
    csp = "default-src 'none'; script-src 'sha256-" + script_hash + "'; style-src 'unsafe-inline'; img-src data: blob:; connect-src 'none'; base-uri 'none'; form-action 'none'; object-src 'none'"
    page = (HERE/'template.html').read_text()
    # JSON remains data, not executable HTML; the only executable script is hashed.
    data = canonical(cat).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    page = page.replace('@@CSP@@', csp).replace('@@CSS@@', css).replace('@@DATA@@', data).replace('@@JS@@', js)
    (out/'index.html').write_text(page)
    (out/'catalogue.json').write_text(canonical(cat)+'\n')
    # The verifier input is fictional and local to the build directory, not a transcript export.
    (out/'verification.json').write_text(canonical(verification)+'\n')
    manifest = dict(schema='un.us-relative-offline-build.v1', phase1_head=PHASE1_HEAD,
                    catalogue_sha256=cat['sha256'], scenario_count=len(cat['scenes']),
                    publication_eligible=False, real_sources_opened=0,
                    files={name:hashlib.sha256((out/name).read_bytes()).hexdigest()
                           for name in ('index.html', 'catalogue.json', 'verification.json')})
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, help='Temporary directory outside the repository')
    args=parser.parse_args()
    print(json.dumps(build(args.out), indent=2))
