"""Restore the canonical private snapshot and audit exports without remote writes."""
import json
import os
from pathlib import Path
from un_transcript.restore_audit import audit_restored_exports
from un_transcript.snapshots import HFStorage


def main():
    root = Path(os.environ['RUNNER_TEMP'])/'restored-export-audit'
    storage = HFStorage(os.environ['HF_DATASET_REPO'])
    pointer = storage.restore(root)
    if pointer is None:
        raise ValueError('No durable snapshot exists')
    result = audit_restored_exports(root/'data', root/'reproduced')
    print(json.dumps({**result, 'durable_revision': pointer['revision']}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__}))
        raise SystemExit(1)
