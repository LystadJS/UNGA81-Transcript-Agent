"""Convert archived meetings to existing upload contract; retain every source segment."""
import csv,hashlib,json,re
from pathlib import Path
from urllib.parse import urljoin
import argparse

def prepare(root,registry_path):
    root=Path(root);inv=json.loads((root/'inventory.json').read_text());registry={}
    for r in csv.DictReader(Path(registry_path).open(encoding='utf-8-sig')):
        for alias in (r['aliases']+'|'+r['iso3']+'|'+r['country']).split('|'):registry[alias.casefold()]=r
    segments=[];records=[];coverage=[]
    for item in inv['meetings']:
        title=item['title'];slug=item['slug'];scope='general_debate' if 'general debate' in title.lower() else 'broader_hlw'
        if slug.startswith(('hrc/','ced/','crc/','briefing/geneva/')) or re.search(r'OHCHR Special Procedures|HRC - Press|UNCTAD Press conference|UN Crime Congress|Patriotic Pact Organization',title,re.I):scope='other_week_proceedings'
        item['scope']=scope;coverage.append(item)
        if item.get('collection_status')!='downloaded':continue
        path=root/'raw'/(item['archive_id']+'.json');raw=path.read_bytes();raw_hash=hashlib.sha256(raw).hexdigest();doc=json.loads(raw);tr=doc['transcript']
        item['transcript_language']=tr['language']
        if doc['video']['date'][:10]!=item['date'][:10]:raise ValueError('Date mismatch')
        # Group a meeting's segments by explicitly recorded affiliation. This avoids
        # input row limits without dropping procedural, brief or unidentified speech.
        groups={}
        for index,s in enumerate(tr['data']):
            sp=s.get('speaker') or {};aff=sp.get('affiliation') or sp.get('affiliation_full') or ''
            country=registry.get(aff.casefold());key=country['iso3'] if country else 'unresolved:'+aff
            sentences=[v for p in s.get('paragraphs',[]) for v in p.get('sentences',[])]
            text=' '.join(v['text'] for v in sentences)
            if not text.strip():continue
            group=groups.setdefault(key,{'country':country,'parts':[],'affiliation':aff})
            group['parts'].append((s,text,index,sp))
        for gi,(key,g) in enumerate(groups.items(),1):
            sid=f"{item['archive_id']}-{gi:03d}";c=g['country'];text='';parts=[]
            for s,body,index,sp in g['parts']:
                if text:text+='\n\n'
                start=len(text);text+=body
                segment={'record_id':sid,'meeting_id':slug,'title':title,'scope':scope,'date':item['date'][:10],'country':c['country'] if c else '', 'iso3':c['iso3'] if c else '', 'speaker_metadata':sp,'statement_number':s['statement_number'],'start_char_0':start,'end_char_0':len(text),'text':body,'source_url':urljoin('https://transcripts.un.org',s.get('pageUrl') or item['pageUrl']),'raw_file':path.relative_to(root).as_posix(),'raw_sha256':raw_hash,'json_pointer':f'/transcript/data/{index}'}
                segments.append(segment)
            records.append({'statement_id':sid,'country':c['country'] if c else '', 'country_id':c['iso3'] if c else '', 'region':c['region'] if c else 'Unmapped','speaker':title+' | '+(g['affiliation'] or 'Unidentified affiliation'),'speech_date':item['date'][:10],'language':tr['language'],'text':text,'source_url':urljoin('https://transcripts.un.org',item['pageUrl']),'declared_status':'available','scope':scope})
    root.joinpath('input').mkdir(exist_ok=True)
    fields=['statement_id','country','country_id','region','speaker','speech_date','language','text','source_url','declared_status']
    # Separate out-of-scope background material, but search it as a contextual run.
    batches={}
    for name,selected in [('hlw',[r for r in records if r['scope']!='other_week_proceedings']),('background',[r for r in records if r['scope']=='other_week_proceedings'])]:
        for batch in range(0,len(selected),2000):
            with (root/'input'/f'{name}-{batch//2000+1}.csv').open('w',encoding='utf-8',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(selected[batch:batch+2000])
            batches[f'{name}-{batch//2000+1}.csv']=len(selected[batch:batch+2000])
    (root/'input-batches.json').write_text(json.dumps(batches,indent=2),encoding='utf-8')
    (root/'segments.json').write_text(json.dumps(segments,ensure_ascii=False),encoding='utf-8')
    (root/'records.json').write_text(json.dumps(records,ensure_ascii=False),encoding='utf-8')
    (root/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'meetings':len(coverage),'source_segments':len(segments),'analysis_records':len(records),'hlw_records':sum(r['scope']!='other_week_proceedings' for r in records)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--registry',default='un/config/countries.csv');a=p.parse_args();prepare(a.root,a.registry)
