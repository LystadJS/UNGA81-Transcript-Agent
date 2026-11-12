"""Authenticated manual setup; credentials and restored private data stay on runner."""
import json
import os
from pathlib import Path
from urllib.request import urlopen
from un_transcript.publication import provision_public, validate_target
from un_transcript.snapshots import HFStorage


def main():
    private_repo = os.environ['HF_DATASET_REPO']
    public_repo = os.environ['PUBLIC_METADATA_REPO']
    validate_target(private_repo, public_repo)
    private = HFStorage(private_repo)
    root = Path(os.environ['RUNNER_TEMP'])/'public-provision'
    if private.restore(root) is None:
        raise ValueError('No private snapshot is available for public projection')
    result = provision_public(private_repo, public_repo, root/'data/public', api=private.api)
    # Deliberately anonymous: no token/header is supplied to this public read.
    with urlopen(result['manifest_url']+'?verify='+result['snapshot_id'], timeout=30) as response:
        if response.status != 200:
            raise ValueError('Anonymous public read failed')
        live = json.loads(response.read(16*1024*1024))
    if live.get('snapshot_id') != result['snapshot_id'] or live.get('schema') != 'un.archive.v1':
        raise ValueError('Anonymous public manifest mismatch')
    print(json.dumps({**result, 'anonymous_read_verified': True}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = getattr(getattr(error, 'response', None), 'status_code', None)
        print(json.dumps({'status': 'blocked' if code in (401,403) else 'failed',
                          'error_type': type(error).__name__, 'http_status': code}))
        raise SystemExit(1)
