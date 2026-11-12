"""Prepare an immutable private owner packet; print aggregate metadata only."""
import csv
import json
import os
from pathlib import Path
from un_transcript.snapshots import HFStorage, file_sha, encode
from un_transcript.models.__main__ import prepare_pilot
from un_transcript.models.contracts import read_json


def review_files(packet, segments):
    index = {s['segment_id']: s for s in segments['segments']}
    counts = {}
    fields = ['pair_id', 'meeting_id', 'date', 'source_id', 'source_hash', 'segment_id',
              'speaker', 'country', 'capacity', 'source_url', 'issue_id', 'proposition',
              'text', 'status', 'label', 'national_attribution_valid', 'owner_confirmed', 'notes']
    for split, expected in [('train', 180), ('calibration', 60), ('test', 60)]:
        draft = read_json(packet / (split + '-draft.json'))
        counts[split] = len(draft['rows'])
        if counts[split] != expected:
            raise ValueError('Insufficient diverse pilot candidates; no incomplete packet published')
        target = packet / ('sealed' if split == 'test' else 'review')
        target.mkdir(exist_ok=True)
        with (target / (split + '-review.csv')).open('w', newline='', encoding='utf-8-sig') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for row in draft['rows']:
                source = index[row['segment_id']]
                values = {k: row.get(k, source.get(k, '')) for k in fields}
                values.update(status='', label='', national_attribution_valid='', owner_confirmed='', notes='')
                values = {k: ("'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else v) for k, v in values.items()}
                writer.writerow(values)
        if split == 'test':
            (packet / 'test-draft.json').rename(target / 'test-draft.json')
    (packet / 'README.md').write_text(Path('docs/PILOT_REVIEW.md').read_text())
    return counts


def main():
    storage = HFStorage(os.environ['HF_DATASET_REPO'])
    work = Path(os.environ['RUNNER_TEMP']) / 'owner-pilot'
    restored = storage.restore(work)
    if not restored:
        raise ValueError('A verified archive snapshot is required')
    segments = read_json(work / 'data/private/current_segments.json')
    packet = work / 'packet'
    prepare_pilot(segments, read_json('config/issues.json'), packet, read_json('config/model-policy.json'))
    counts = review_files(packet, segments)
    prefix = 'pilots/' + os.environ['GITHUB_RUN_ID'] + '-' + os.environ['GITHUB_RUN_ATTEMPT'] + '/'
    files = {prefix + p.relative_to(packet).as_posix(): p for p in packet.rglob('*') if p.is_file()}
    manifest = {'schema': 'un.owner-pilot.v1', 'source_snapshot': segments['snapshot_id'],
                'counts': counts, 'owner_confirmed': False, 'test_sealed_by_procedure': True,
                'files': [{'path': path, 'sha256': file_sha(p), 'bytes': p.stat().st_size} for path, p in sorted(files.items())]}
    (packet / 'packet-manifest.json').write_bytes(encode(manifest))
    files[prefix + 'packet-manifest.json'] = packet / 'packet-manifest.json'
    info, used = storage.info()
    if used + sum(p.stat().st_size for p in files.values()) + 1_000_000 > storage.budget_bytes:
        raise ValueError('Private storage budget exceeded')
    storage._immutable_prefix(prefix, info.sha)
    revision = storage._commit(files, info.sha, 'Prepare unreviewed owner pilot')
    storage._verify_remote(files, revision)
    print(json.dumps({'status': 'verified_private_pilot', 'path': prefix, 'revision': revision,
                      'source_snapshot': segments['snapshot_id'], 'counts': counts,
                      'owner_confirmed': False}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error_type': type(error).__name__}))
        raise SystemExit(1)
