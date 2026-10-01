"""Package the recovery supplement with short paths and sanitized source records."""
import argparse,hashlib,json,tempfile,zipfile
from pathlib import Path
from check_hlw_recovery import check

def encode(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def digest(raw):return hashlib.sha256(raw).hexdigest()

def package(root,report,output):
    root=Path(root);report=Path(report);output=Path(output)
    check(report)
    ledger=json.loads((report/'recovery.json').read_text(encoding='utf-8'))
    assert all(x.get('text_file') for x in ledger['events']), 'Finish all selected recordings before final packaging'
    files={};source_records=[]
    for p in report.iterdir():
        if p.is_file() and p.name not in ('delivery.json','recovery-delivery.json'):
            files['rec/report/'+p.name]=p.read_bytes()
    for event in ledger['events']:
        aid=event['archive_id'];folder=root/aid
        if event['source_type']=='publisher_caption':
            name='rec/source/'+aid+'.srt';raw=(folder/'caption.srt').read_bytes()
            assert digest(raw)==event['source_sha256'];files[name]=raw
        else:
            original=(folder/'asr.json').read_bytes();assert digest(original)==event['asr_sha256']
            data=json.loads(original);data.pop('audio_url',None)
            with (folder/'audio.flac').open('rb') as audio:
                assert hashlib.file_digest(audio,'sha256').hexdigest()==data['audio_sha256']
            data['source_video_url']=event['video_url']
            data['original_record_sha256']=digest(original)
            data['packaging_note']='Temporary media URL omitted; audio hash and canonical video URL retained.'
            name='rec/source/'+aid+'.json';files[name]=encode(data)
        source_records.append(dict(archive_id=aid,file=name,sha256=digest(files[name]),source_url=event['video_url']))
    for item in json.loads((root/'written/manifest.json').read_text(encoding='utf-8')):
        if item['status']!='downloaded':continue
        p=root/'written'/item['file']
        assert digest(p.read_bytes())==item['sha256']
        files['rec/written/'+p.name]=p.read_bytes()
    files['rec/written/manifest.json']=(root/'written/manifest.json').read_bytes()
    files['rec/source/index.json']=encode(source_records)
    files['rec/START.txt']=b'Open report/recovery.html. Published individual statements and outcome documents are distinct from unreviewed captions and local machine transcription. Original Cuba-brief counts are unchanged. source/ contains captions and sanitized ASR records; written/ preserves downloaded public pages and the communique. Audio, model weights, signed media URLs, and original corpus raw records are excluded. See report/RECOVERY.md.\n'
    hashes={name:digest(raw) for name,raw in files.items()}
    files['rec/MANIFEST.json']=encode(hashes)
    assert max(map(len,files))<100
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,raw in sorted(files.items()):z.writestr(name,raw)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        with tempfile.TemporaryDirectory(prefix='hr-') as tmp:
            target=Path(tmp)
            assert all((target/name).resolve().is_relative_to(target.resolve()) for name in z.namelist())
            z.extractall(target)
            assert all(digest((target/name).read_bytes())==sha for name,sha in hashes.items())
            check(target/'rec/report')
            max_extracted=max(len(str(target/name)) for name in files)
    result=dict(file=output.name,bytes=output.stat().st_size,sha256=digest(output.read_bytes()),
        files=len(files),max_internal_path_chars=max(map(len,files)),max_test_extraction_path_chars=max_extracted,
        zip_integrity=True,extracted_hashes_verified=True,extracted_recovery_links_valid=True,
        local_audio_hashes_verified=True,
        events=len(ledger['events']),human_review_complete=False)
    output.with_suffix('.zip.json').write_bytes(encode(result));print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('report');p.add_argument('output');a=p.parse_args()
    package(a.root,a.report,a.output)
