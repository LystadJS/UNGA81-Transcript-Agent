"""Real-provider recovery exercise with synthetic data in an isolated namespace."""
import json
import os
from pathlib import Path
import re
from un_transcript.snapshots import HFStorage, encode, seal_snapshot, verify_snapshot, sha
from un_transcript.warehouse import Warehouse
from un_transcript.exports import export_snapshot


class SimulatedInterruption(Exception): pass


class DrillStorage(HFStorage):
    def __init__(self, repo, prefix, **kwargs):
        if not re.fullmatch(r'drills/[0-9]+-[0-9]+/store/',prefix):
            raise ValueError('An isolated drill namespace is required')
        super().__init__(repo, **kwargs)
        self.prefix=prefix; self.interrupt=False
        download=self.downloader
        self.downloader=lambda path, revision: download(self.prefix+path,revision)

    def _entries(self, paths, revision):
        return super()._entries([self.prefix+p for p in paths],revision)

    def _commit(self, files, parent, message):
        if self.interrupt and 'latest.json' in files:
            raise SimulatedInterruption('Injected stop before isolated pointer activation')
        return super()._commit({self.prefix+k:v for k,v in files.items()},parent,'Synthetic recovery drill: '+message)


def fixture(root, name, cursor):
    with Warehouse(root/'fixture'/'warehouse.sqlite3') as db:
        stamp='2026-11-12T00:00:00Z'
        db.start_run(name,{'synthetic_recovery_drill':True},stamp)
        db.ingest({'meeting_id':'ga/81/42','date':'2026-11-10','title':'Synthetic recovery fixture','body':'ga',
                   'source_url':'https://transcripts.un.org/en/ga/81/42','json_url':'https://transcripts.un.org/en/ga/81/42.json'},
                  b'{"synthetic_recovery_fixture":true}',[{'text':'Synthetic recovery fixture only.','language':'en',
                  'speaker':'fictional','country':'','capacity':'unknown','json_pointer':'/synthetic'}],stamp)
        db.finish_run(name,'complete',stamp)
        target=root/name
        export_snapshot(db,target,name,stamp)
        seal_snapshot(db,target,{'synthetic':True,'cursor':cursor},name,stamp)
    return target


def main():
    repo=os.environ['HF_DATASET_REPO']; identity=os.environ['GITHUB_RUN_ID']+'-'+os.environ['GITHUB_RUN_ATTEMPT']
    prefix='drills/'+identity+'/'
    live=HFStorage(repo); info,budget_before=live.budget_info()
    used_before=live.last_capacity_measurement['provider_reported_bytes']
    if budget_before+100_000_000>live.budget_bytes:raise ValueError('Insufficient drill budget reserve')
    canonical_before=live.read('latest.json',info.sha,1024*1024)
    pointer=json.loads(canonical_before)
    manifest_raw=live.read(pointer['manifest_path'],pointer['revision'],16*1024*1024)
    if sha(manifest_raw)!=pointer['manifest_sha256']:raise ValueError('Canonical manifest checksum mismatch')
    manifest=json.loads(manifest_raw)
    store=DrillStorage(repo,prefix+'store/')
    live._immutable_prefix(prefix,info.sha)
    root=Path(os.environ['RUNNER_TEMP'])/'recovery-drill'; root.mkdir()
    baseline=fixture(root,'baseline',1);store.publish(baseline)
    head,_=store.info();old_pointer=store.read('latest.json',head.sha)
    interrupted=fixture(root,'interrupted',2);store.interrupt=True
    try:store.publish(interrupted)
    except SimulatedInterruption:pass
    else:raise AssertionError('Expected simulated interruption')
    store.interrupt=False
    head,_=store.info()
    if store.read('latest.json',head.sha)!=old_pointer:raise AssertionError('Failed write changed the pointer')
    store.restore(root/'restore-after-failure')
    restored=root/'restore-after-failure/data'
    if verify_snapshot(restored)!=verify_snapshot(baseline):raise AssertionError('Restored manifest differs')
    if json.loads((restored/'state.json').read_bytes())['cursor']!=1:raise AssertionError('Cursor advanced on failure')
    retry=fixture(root,'retry',2);store.publish(retry);store.restore(root/'restore-after-retry')
    if verify_snapshot(root/'restore-after-retry/data')!=verify_snapshot(retry):raise AssertionError('Retry restore differs')
    final,used_after=live.info()
    if live.read('latest.json',final.sha)!=canonical_before:raise AssertionError('Production pointer changed during drill; inspect concurrent writers')
    result={'schema':'un.recovery-drill.v1','status':'passed','synthetic_only':True,'canonical_pointer_unchanged':True,
            'interruption':'after verified staging, before isolated pointer activation','old_snapshot_restored':True,
            'retry_snapshot_restored':True,'csv_and_artifact_hashes_reproduced':True,
            'canonical_snapshot':pointer['snapshot_id'],'canonical_snapshot_bytes':sum(f['bytes'] for f in manifest['files']),
            'largest_artifact_bytes':max(f['bytes'] for f in manifest['files']),
            'retained_bytes_before':used_before,'retained_bytes_after':used_after,
            'repository_budget_bytes':live.budget_bytes,'account_capacity_acceptance':False}
    files={prefix+'receipt.json':encode(result)}
    revision=live._commit(files,final.sha,'Record isolated recovery drill receipt')
    live._verify_remote(files,revision)
    print(json.dumps({**result,'receipt_path':prefix+'receipt.json','revision':revision}))

if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'status':'failed','error_type':type(error).__name__}))
        raise SystemExit(1)
