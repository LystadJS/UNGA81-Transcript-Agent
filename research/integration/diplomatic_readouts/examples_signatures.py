"""Generate deterministic, invented no-authority Ed25519 preflight receipts.

All test signing keys are publicly reconstructible; NEVER use operationally.
Outputs contain no keys, attestation signatures, original text or source rows.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'tests'))
from test_synthetic_signatures import fixture, resign_custody, resign_revocation
from synthetic_signatures import (
    REVOCATION_SCHEMA, assert_zero_authority, content_digest, receipt_sha256,
    verify_synthetic_signatures,
)
from test_registry_preflight import WHEN


def scenarios():
    yield 'valid_no_authority', fixture()
    f = fixture()
    f['custody']['payload']['audit_tip_sha256'] = 'b' * 64
    yield 'tampered_signature', f
    f = fixture()
    f['revocation']['payload']['revoked_key_ids'] = [f['key_ids']['custody']]
    resign_revocation(f)
    yield 'revoked_custodian', f
    f = fixture()
    f['trust'] = replace(f['trust'], minimum_checkpoint_sequence=3)
    yield 'revocation_highwater_rollback', f
    f = fixture()
    f['trust'] = replace(f['trust'], expected_checkpoint_sha256='b'*64)
    yield 'revocation_checkpoint_replaced', f
    f = fixture()
    f['custody']['payload']['audience'] = 'synthetic:another-audience'
    resign_custody(f)
    yield 'cross_audience_replay', f
    f = fixture()
    f['custody']['payload']['expires_at'] = '2026-10-14T00:00:00Z'
    resign_custody(f)
    yield 'expired_attestation', f
    f = fixture()
    f['snapshot']['fixture_kind'] = 'private_development'
    yield 'real_source_disallowed', f
    f = fixture()
    f['custody']['key_id'] = f['key_ids']['rotation']
    resign_custody(f)
    f['revocation']['payload']['revoked_key_ids'] = [f['key_ids']['custody']]
    resign_revocation(f)
    yield 'rotation_unrevoked_key_no_authority', f
    f = fixture()
    f['policy']['permissions']['read_source_bytes'] = True
    yield 'access_scope_escalation', f


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    target=args.output
    if target.is_symlink() or (target.exists() and (not target.is_dir() or any(target.iterdir()))):
        parser.error('output must be a new or empty nonsymlink directory')
    target.mkdir(parents=True,exist_ok=True,mode=0o700)
    cases={}
    for name,f in scenarios():
        r=verify_synthetic_signatures(f['snapshot'],f['policy'],f['events'],f['proposal'],
            f['custody'],f['revocation'],checked_at=WHEN,trust=f['trust'])
        assert_zero_authority(r)
        assert (r['status']=='synthetic_signatures_verified_no_authority') == (
            name in ('valid_no_authority','rotation_unrevoked_key_no_authority')), name
        data=(json.dumps(r,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        (target/(name+'.json')).write_bytes(data)
        cases[name]={'status':r['status'],'reason_codes':r['reason_codes'],
                     'receipt_sha256':receipt_sha256(r),
                     'file_sha256':sha256(data).hexdigest()}
        print(name,r['status'])
    m={'schema':'un.synthetic-ed25519-example-manifest.v0','synthetic_only':True,
       'authority':'none','authorized':False,'publication_eligible':False,
       'delivery_eligible':False,'transcripts_opened':0,'cases':cases}
    raw=(json.dumps(m,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    (target/'manifest.json').write_bytes(raw)
    print('manifest_sha256',sha256(raw).hexdigest())
    return 0

if __name__=='__main__':
    raise SystemExit(main())
