"""One-shot, restartable batch commands; no daemon or external AI endpoint."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timezone, timedelta
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

from .snapshots import HFStorage, atomic_json, seal_snapshot, verify_snapshot


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


@contextmanager
def writer_lock(workspace):
    workspace = Path(workspace); workspace.mkdir(parents=True, exist_ok=True)
    with (workspace / '.writer.lock').open('a+b') as lock:
        if os.name == 'nt':
            import msvcrt
            lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == 'nt':
                lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def run_pipeline(config_path, workspace, *, as_of=None, transport=None, remote=None, public_remote=None,
                 publish_public=None, catalog_path='config/issues.json', model_dir=None):
    from .collection import Collector, load_config
    from .warehouse import Warehouse
    from .exports import export_snapshot
    from .models import analyze_segments
    workspace = Path(workspace)
    config = load_config(config_path)
    data_directory = workspace / 'data'
    with writer_lock(workspace):
        if remote:
            if public_remote and remote.repo_id == public_remote.repo_id:
                raise ValueError('Private and public datasets must be different repositories')
            # Check privacy and accounted history before downloading sources.
            _, used = remote.info()
            if used + config.get('max_bytes_per_run', 100_000_000) * 3 > remote.budget_bytes:
                raise ValueError('Insufficient private storage budget for a collection run')
            if public_remote:
                public_remote.info()
            if not data_directory.exists():
                remote.restore(workspace)
        state_file = data_directory / 'state.json'
        state = json.loads(state_file.read_bytes()) if state_file.exists() else {}
        stamp = now()
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:12]
        directory = workspace / 'snapshots' / run_id
        with Warehouse(data_directory / 'warehouse.sqlite3') as warehouse:
            warehouse.start_run(run_id, config, stamp)
            finished = False
            try:
                collection = Collector(config, transport=transport).collect(as_of or date.today(), state)
                for receipt in collection['inventory']:
                    warehouse.record_inventory(run_id, receipt)
                for item in collection['items']:
                    warehouse.ingest(item['meeting'], item['raw'], item['segments'], item['retrieved_at'], item.get('headers'))
                for row in collection['coverage']:
                    warehouse.record_coverage(run_id, row['meeting_id'], row['status'], row.get('detail', ''))
                catalog = json.loads(Path(catalog_path).read_bytes())
                for issue in catalog.get('issues', []):
                    warehouse.upsert_issue({'issue_id':issue['id'],'version':catalog['version'],
                                            'label':issue['label'],'definition':issue.get('proposition',issue['label'])})
                segments = warehouse.current_segments()
                for segment in segments:
                    segment.update(source_id=segment['revision_id'], source_hash=segment['raw_sha256'],
                                   attribution_kind={'national':'individual_country'}.get(segment['capacity'],segment['capacity']))
                analysis = analyze_segments(segments, catalog, model_dir=model_dir)
                warehouse.record_analysis(analysis, created_at=now(), run_id=run_id)
                incomplete = {'failed','inventory_failed','deferred','pending','unavailable','empty_transcript'}
                partial = any(r['status'] in incomplete for r in collection['coverage']) or bool(collection['state'].get('pending_dates'))
                status = 'partial' if partial else 'complete'
                end = now()
                warehouse.finish_run(run_id, status, end); finished = True
                manifest = export_snapshot(warehouse, directory, run_id, end)
                seal_snapshot(warehouse, directory, collection['state'], run_id, end)
            except BaseException:
                if not finished:
                    warehouse.finish_run(run_id, 'failed', now())
                raise
        # A remote failure never advances local cursor or published pointer. A
        # rerun remains idempotent even when local SQLite contains durable rows.
        pointer = remote.publish(directory) if remote else {'snapshot_id':run_id,'path':str(directory),'schema':'un.local-snapshot.v1'}
        atomic_json(state_file, collection['state'])
        atomic_json(workspace / 'latest.json', pointer)
        if publish_public:
            dest = Path(publish_public)
            if dest.exists():
                raise FileExistsError('Public output destination must be new')
            shutil.copytree(directory / 'public', dest)
        public_status = 'not_configured'
        if public_remote:
            public_remote.publish_public(directory / 'public')
            public_status = 'published'
        receipt = {'schema':'un.pipeline-run.v1','run_id':run_id,'status':status,'generated_at':end,
                   'snapshot':str(directory),'meetings_downloaded':len(collection['items']),
                   'bytes_downloaded':collection['bytes_downloaded'],'model_status':analysis['model_status'],
                   'coverage':manifest['coverage'],
                   'private_publication':'published' if remote else 'local_only','public_publication':public_status}
        atomic_json(workspace / 'last-run.json', receipt)
        return receipt


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('run','restore','verify','status'):
        s = sub.add_parser(command)
        s.add_argument('--workspace', type=Path, required=True)
        if command in ('run','restore'):
            s.add_argument('--remote', choices=['hf'])
            s.add_argument('--repo', default=os.environ.get('HF_DATASET_REPO'))
            s.add_argument('--storage-budget-bytes',type=int,default=80_000_000_000)
        if command == 'run':
            s.add_argument('--config', default='config/collection.json')
            s.add_argument('--catalog',default='config/issues.json')
            s.add_argument('--as-of',type=date.fromisoformat)
            s.add_argument('--public-repo')
            s.add_argument('--publish-public',type=Path)
            s.add_argument('--model-dir',type=Path)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command in ('run','restore'):
            if args.remote and not args.repo:
                raise ValueError('HF_DATASET_REPO or --repo is required for durable remote storage')
            remote = HFStorage(args.repo, budget_bytes=args.storage_budget_bytes) if args.remote else None
        if args.command == 'run':
            if args.public_repo and not remote:
                raise ValueError('Public publication requires a verified private remote snapshot first')
            public_remote = HFStorage(args.public_repo,private=False,budget_bytes=10_000_000_000) if args.public_repo else None
            result = run_pipeline(args.config,args.workspace,as_of=args.as_of,remote=remote,public_remote=public_remote,
                                  publish_public=args.publish_public,catalog_path=args.catalog,model_dir=args.model_dir)
        elif args.command == 'restore':
            if not remote:
                raise ValueError('restore requires --remote hf')
            with writer_lock(args.workspace):
                result = remote.restore(args.workspace) or {'status':'empty_remote'}
        elif args.command == 'verify':
            result = verify_snapshot(args.workspace)
            result = {'status':'verified','snapshot_id':result['snapshot_id'],'files':len(result['files'])}
        else:
            file = args.workspace / 'last-run.json'
            result = json.loads(file.read_bytes()) if file.exists() else {'status':'not_run'}
            if result.get('generated_at'):
                result['stale'] = datetime.now(timezone.utc) - datetime.fromisoformat(result['generated_at'].replace('Z','+00:00')) > timedelta(hours=36)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as error:
        # Provider error strings may include signed URLs or credentials. Keep
        # details in the operator's private debugger, never CI logs.
        if isinstance(error, (ValueError, FileExistsError)):
            message = str(error)
        else:
            message = 'Operation failed; previous published snapshot remains available'
        print(json.dumps({'status':'failed','error_type':type(error).__name__,'message':message}),file=sys.stderr)
        return 1
