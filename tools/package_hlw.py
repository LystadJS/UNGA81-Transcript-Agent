"""Create a short-path delivery with raw sources, readable texts and verified runs."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def package(root,report,output):
    root=Path(root);report=Path(report);output=Path(output)
    validation=json.loads((report/'validation.json').read_text(encoding='utf-8'))
    assert validation['all_input_rows_reconciled'] and validation['all_evidence_offsets_verified']
    inventory=json.loads((root/'coverage.json').read_text(encoding='utf-8'))
    files={}
    for folder in ('raw','index','input'):
        for p in (root/folder).glob('*'):files['hlw/'+folder+'/'+p.name]=p.read_bytes()
    for name in ('inventory.json','coverage.json','segments.json','records.json','input-batches.json','SHA256.json'):
        files['hlw/'+name]=(root/name).read_bytes()
    for item in inventory:
        if item.get('collection_status')!='downloaded':continue
        raw=json.loads((root/'raw'/(item['archive_id']+'.json')).read_bytes());text=[item['title'],item['date'],raw.get('url',''),raw.get('disclaimer',''),'']
        for s in raw['transcript']['data']:
            text+=['Statement '+str(s['statement_number']),json.dumps(s.get('speaker'),ensure_ascii=False),' '.join(t['text'] for p in s.get('paragraphs',[]) for t in p.get('sentences',[])),'']
        files['hlw/text/'+item['archive_id']+'.txt']='\n'.join(text).encode('utf-8')
    for p in report.iterdir():
        if p.is_file() and p.name!='delivery.json':files['hlw/report/'+p.name]=p.read_bytes()
    for filename in json.loads((root/'input-batches.json').read_text()):
        name=Path(filename).stem;run=root/('final-'+name)
        for p in run.rglob('*'):
            if p.is_file() and p.name!='progress.rds':files['hlw/runs/'+name+'/'+p.relative_to(run).as_posix()]=p.read_bytes()
    files['hlw/START.txt']=b'Open report/index.html first. Original UN automatic transcript responses are in raw/; readable copies in text/. The coverage file records 56 unavailable meetings. Only verified runs are delivered. EML files are unsent drafts. This is a public-source working collection, not official verbatim UN records. See report/README.md for scope and reproduction.\n'
    hashes={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}
    files['hlw/MANIFEST.json']=json.dumps(hashes,indent=2).encode()
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,raw in sorted(files.items()):z.writestr(name,raw)
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(name)).hexdigest()==digest for name,digest in hashes.items())
    result={'file':output.name,'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'files':len(files),'max_internal_path_chars':max(map(len,files)),'zip_integrity':True,'all_member_hashes_verified':True}
    output.with_suffix('.zip.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('report');p.add_argument('output');a=p.parse_args();package(a.root,a.report,a.output)
