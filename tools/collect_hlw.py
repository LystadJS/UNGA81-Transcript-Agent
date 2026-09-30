"""Archive the public UN English transcript inventory, without altering the program."""
import argparse, datetime as dt, hashlib, json, time, urllib.request
from pathlib import Path
from urllib.parse import urljoin,urlparse

BASE='https://transcripts.un.org'
def fetch(url,path):
    if urlparse(url).hostname!='transcripts.un.org':raise ValueError('Unexpected source host')
    if path.exists():return json.loads(path.read_bytes())
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UNBrief public-source research'}),timeout=60) as response:
                raw=response.read(25_000_001)
            if len(raw)>25_000_000:raise ValueError('Oversized response')
            data=json.loads(raw);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            time.sleep(.5);return data
        except Exception:
            if attempt==2:raise
            time.sleep(2*(attempt+1))

def collect(root,start,end,index_only=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True);items=[];days=[];errors=[]
    day=dt.date.fromisoformat(start)
    while day<=dt.date.fromisoformat(end):
        date=str(day);found=[];expected=None
        try:
            for page in range(1,51):
                url=f'{BASE}/en/meetings.json?date={date}&xlang=1&page={page}'
                doc=fetch(url,root/'index'/f'{date}-{page}.json')
                if doc['page']!=page:raise ValueError('Page mismatch')
                if expected is None:expected=doc['total']
                if expected!=doc['total'] or doc['total']!=doc['totalIncludingOther']:raise ValueError('Inventory changed or language coverage differs')
                found.extend(doc['meetings'])
                if not doc['hasMore']:break
            else:raise ValueError('Pagination limit')
            if len(found)!=expected or len({x['slug'] for x in found})!=expected:raise ValueError('Count or duplicate mismatch')
            if any(x['date'][:10]!=date for x in found):raise ValueError('Date mismatch')
            days.append({'date':date,'meetings':len(found),'inventory_complete':True});items.extend(found)
            print(date,len(found),'meetings',flush=True)
        except Exception as e:errors.append({'date':date,'stage':'inventory','error':str(e)})
        day+=dt.timedelta(days=1)
    for i,item in enumerate(items,1):
        item['archive_id']=hashlib.sha256(item['slug'].encode()).hexdigest()[:12]
        if index_only:continue
        if not item['hasTranscript']:item['collection_status']='unavailable';continue
        try:
            doc=fetch(urljoin(BASE,item['jsonUrl']),root/'raw'/(item['archive_id']+'.json'))
            if doc['video']['slug']!=item['slug']:raise ValueError('Detail identity mismatch')
            item['collection_status']='downloaded'
            print(i,len(items),item['title'],flush=True)
        except Exception as e:
            item['collection_status']='failed';errors.append({'slug':item['slug'],'stage':'detail','error':str(e)})
    result={'start':start,'end':end,'collected_at':dt.datetime.now(dt.timezone.utc).isoformat(),'source':BASE,'locale':'en','days':days,'meetings':items,'errors':errors,'index_only':index_only}
    (root/'inventory.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    manifest={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*.json')) if p.name!='SHA256.json'}
    (root/'SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');p.add_argument('--start',default='2026-09-21');p.add_argument('--end',default='2026-09-28');p.add_argument('--index-only',action='store_true');a=p.parse_args()
    r=collect(a.output,a.start,a.end,a.index_only);print(json.dumps({'meetings':len(r['meetings']),'errors':r['errors']}))
