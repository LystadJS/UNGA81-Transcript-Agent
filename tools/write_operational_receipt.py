"""Project an explicit public allowlist from local, private operational files."""
import json
import os
from pathlib import Path
from un_transcript.monitoring import operational_receipt


def read_optional(path):
    if not path.exists():
        return None
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError('Unsafe operational input')
    return json.loads(path.read_bytes())


def main():
    root = Path(os.environ['RUNNER_TEMP'])
    receipt = operational_receipt(read_optional(root/'un-warehouse/last-run.json'),
        run_id=os.environ['GITHUB_RUN_ID'], attempt=os.environ['GITHUB_RUN_ATTEMPT'],
        event=os.environ['GITHUB_EVENT_NAME'], processing_status=os.environ['PROCESSING_STATUS'],
        before=read_optional(root/'storage-preflight.json'),
        after_private=read_optional(root/'storage-after-private.json'),
        after_public=read_optional(root/'storage-after-public.json'))
    target = root/'operational-receipt.json'
    target.write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    main()
