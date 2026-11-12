"""Derive an offline reviewer from a pinned, verified private pilot; never resample."""
import csv
import io
import json
import os
import re
from pathlib import Path
from un_transcript.snapshots import HFStorage, sha, encode, file_sha


def render(draft, display, identity):
    if not draft.get('rows') or any(r.get('split') != 'train' for r in draft['rows']):
        raise ValueError('This reviewer accepts training examples only')
    ids=[r['pair_id'] for r in draft['rows']]
    if len(set(ids)) != len(ids): raise ValueError('Duplicate example identity')
    payload=json.dumps({'draft':draft,'display':display,'identity':identity},ensure_ascii=True)
    payload=payload.replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return Path('tools/pilot-reviewer.html').read_text().replace('__PILOT_PACKET_JSON__',payload)


def main():
    storage=HFStorage(os.environ['HF_DATASET_REPO'])
    revision=os.environ['PILOT_REVISION']; prefix=os.environ['PILOT_PREFIX']
    if not re.fullmatch(r'[0-9a-f]{40}',revision) or not re.fullmatch(r'pilots/[0-9]+-[0-9]+/',prefix):
        raise ValueError('Invalid immutable pilot location')
    storage.info()
    raw_manifest=storage.read(prefix+'packet-manifest.json',revision,16*1024*1024)
    manifest=json.loads(raw_manifest)
    entries={e['path']:e for e in manifest['files']}
    def verified(name):
        path=prefix+name; item=entries[path]
        data=storage.read(path,revision,item['bytes'])
        if len(data)!=item['bytes'] or sha(data)!=item['sha256']: raise ValueError('Pilot checksum mismatch')
        return data
    draft=json.loads(verified('train-draft.json'))
    display={r['pair_id']:{k:r[k] for k in ('speaker','source_url')} for r in csv.DictReader(io.StringIO(verified('review/train-review.csv').decode('utf-8-sig')))}
    identity={'dataset_revision':revision,'packet_prefix':prefix,'manifest_sha256':sha(raw_manifest),'split':'train'}
    out=Path(os.environ['RUNNER_TEMP'])/'private-reviewer';out.mkdir()
    html=out/'training-review.html';html.write_text(render(draft,display,identity),encoding='utf-8')
    destination='reviewers/'+os.environ['GITHUB_RUN_ID']+'-'+os.environ['GITHUB_RUN_ATTEMPT']+'/'
    receipt={**identity,'schema':'un.private-reviewer.v1','examples':len(draft['rows']),'html_sha256':file_sha(html)}
    file=out/'manifest.json';file.write_bytes(encode(receipt))
    files={destination+'training-review.html':html,destination+'manifest.json':file}
    info,used=storage.info()
    if used+sum(p.stat().st_size for p in files.values())+1_000_000>storage.budget_bytes:raise ValueError('Storage budget exceeded')
    storage._immutable_prefix(destination,info.sha)
    commit=storage._commit(files,info.sha,'Add private offline owner reviewer')
    storage._verify_remote(files,commit)
    print(json.dumps({'status':'verified_private_reviewer','path':destination+'training-review.html','revision':commit,'examples':len(draft['rows'])}))

if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'status':'failed','error_type':type(error).__name__}))
        raise SystemExit(1)
