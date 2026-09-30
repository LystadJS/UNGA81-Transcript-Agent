"""Read-only comparison of a daily TXT ZIP against the archived UN JSON sources."""
import argparse, csv, hashlib, io, json, re, zipfile
from pathlib import Path
from reviewed_loader import safe

def compare(zip_path, archive):
    archive=Path(archive)
    inv=json.loads((archive/'inventory.json').read_text(encoding='utf-8'))
    hashes=json.loads((archive/'SHA256.json').read_text(encoding='utf-8'))
    normalize=lambda text:' '.join(text.split())
    result=[]
    with zipfile.ZipFile(zip_path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)): raise ValueError('Duplicate archive names')
        if any(i.file_size>30_000_000 for i in z.infolist()): raise ValueError('Oversized archive member')
        if z.testzip(): raise ValueError('ZIP integrity failure')
        supplied={name:digest for digest,name in (line.split(None,1) for line in z.read('SHA256SUMS.txt').decode('utf-8-sig').splitlines() if line.strip())}
        index=list(csv.DictReader(io.StringIO(z.read('source_index.csv').decode('utf-8-sig'))))
        for row in index:
            if row['scheduled']!='YES': continue
            name='transcripts/'+row['saved_filename']; raw=z.read(name)
            digest=hashlib.sha256(raw).hexdigest()
            if digest!=row['sha256'] or digest!=supplied.get(name) or len(raw)!=int(row['bytes']): raise ValueError('Upload integrity mismatch')
            text=raw.decode('utf-8-sig'); date=row['calendar_date']
            matches=[m for m in inv['meetings'] if m['date'][:10]==date and 'general debate' in m['title'].lower()]
            if len(matches)!=1: raise ValueError('Expected one archived daily meeting')
            m=matches[0]; rel='raw/'+m['archive_id']+'.json'; archived=safe(archive,rel).read_bytes()
            if hashlib.sha256(archived).hexdigest()!=hashes[rel]: raise ValueError('Archived source hash mismatch')
            doc=json.loads(archived)
            if row['source_url']!=doc['url']+'.txt': raise ValueError('Source URL mismatch')
            headings=list(re.finditer(r'^([^\n]+) \[(\d+:\d+(?::\d+)?)\]:\s*$',text,re.M))
            chunks=[text[h.end():headings[i+1].start() if i+1<len(headings) else len(text)].strip() for i,h in enumerate(headings)]
            turns=doc['transcript']['data']
            bodies=[' '.join(v['text'] for p in s.get('paragraphs',[]) for v in p.get('sentences',[])) for s in turns]
            ordered_equal=len(chunks)==len(bodies) and all(normalize(a)==normalize(b) for a,b in zip(chunks,bodies))
            seconds=lambda t:sum(int(v)*60**i for i,v in enumerate(reversed(t.split(':'))))
            time_equal=len(headings)==len(turns) and all(abs(seconds(h.group(2))-s['start'])<1.01 for h,s in zip(headings,turns))
            result.append(dict(date=date,source_url=doc['url'],upload_sha256=digest,archive_sha256=hashes[rel],upload_turns=len(chunks),archive_turns=len(turns),ordered_text_equal_after_whitespace_normalization=ordered_equal,timestamps_match_to_one_second=time_equal))
    return dict(upload_zip_sha256=hashlib.sha256(Path(zip_path).read_bytes()).hexdigest(),days=result,total_turns=sum(x['upload_turns'] for x in result),all_ordered_text_equal=all(x['ordered_text_equal_after_whitespace_normalization'] for x in result),scope='Six General Debate daily sessions, not all high-level-week events',normalization='Whitespace only; case, punctuation and wording retained',source_files_modified=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('zip');p.add_argument('archive');p.add_argument('report');a=p.parse_args()
    data=compare(a.zip,a.archive)
    with Path(a.report).open('x',encoding='utf-8') as f: json.dump(data,f,indent=2);f.write('\n')
    print(json.dumps(data,indent=2))
