"""Build a provenance-preserving recovery supplement without changing baseline counts."""
import argparse,collections,datetime as dt,hashlib,html,json,re
from pathlib import Path

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
CUBA=re.compile(r'\bcuba(?:n|ns)?\b|\bhavana\b|\bhelms[ \u2013\u2014-]burton\b',re.I)
def grams(text,n=7):
    words=re.findall('[a-z0-9]+',text.lower())
    return {tuple(words[i:i+n]) for i in range(len(words)-n+1)}
def srt(path):
    rows=[]
    for block in Path(path).read_text(encoding='utf-8-sig').strip().split('\n\n'):
        lines=block.splitlines();timing=next((x for x in lines if '-->' in x),None)
        if not timing:continue
        def seconds(t):
            h,m,s=t.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(s)
        start,end=timing.split(' --> ')
        text=' '.join(lines[lines.index(timing)+1:])
        rows.append(dict(start=seconds(start),end=seconds(end.split()[0]),text=text))
    return rows

WRITTEN={
 'pga':('c29148720b48','Respected Professor Mohammed Yunus','Thank you.','As delivered; individual PGA speech'),
 'unops':('a173d086de17','Excellencies, colleagues, friends','Thank you.','Check against delivery; individual UNOPS remarks'),
 'unctad':('a173d086de17','Excellencies, colleagues,','I thank you.','UNCTAD-published individual statement; browser-rendered text capture'),
 'russia':('634fef94fa16','Excellency, Deputy Prime Minister','Thank you.','Delegation-published individual statement'),
 'icrc':('4ee531a98087','I am joined today by my esteemed colleagues','Together, we must uphold humanity in war.','Organizer-published joint statement; not the entire media stakeout'),
 'unwomen-original':('43630b2b4ca7','I am very happy to be here','Thank you.','As delivered; individual UN Women opening remarks')}
PUBLISHERS={'pga':'General Assembly President','unops':'UNOPS','unctad':'UNCTAD','russia':'Russian delegation','icrc':'ICRC','unwomen-original':'UN Women'}

P1={'6cd8afafddea','2f99e04801b9','6613621f4cda','4ee531a98087','b71afc55df26','634fef94fa16','43630b2b4ca7','aa1a27e5a12f'}
def build(original,recovery,out):
    original=Path(original);recovery=Path(recovery);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    baseline={x['archive_id']:x for x in read(original/'coverage.json')}
    caps=read(recovery/'captions.json');assert len(caps)==41
    records=[];published=[];candidates=[];written_candidates=[];additional=[]
    source_manifest={x['id']:x for x in read(recovery/'written/manifest.json')}
    for name,(aid,start,end,status) in WRITTEN.items():
        path=recovery/'written'/(name+'.txt')
        if not path.exists():continue
        page=path.read_text(encoding='utf-8');a=page.index(start);b=page.index(end,a)+len(end);body=page[a:b]
        source=read(recovery/'written'/(name+'.json')) if name=='unwomen-original' else source_manifest[name]
        assert sha(recovery/'written'/source['file'])==source['sha256']
        filename='w_'+name+'.txt';(out/filename).write_text(status+'\n'+source['url']+'\n\n'+body+'\n',encoding='utf-8',newline='\n')
        published.append(dict(archive_id=aid,file=filename,url=source['url'],source_type='published_statement',publisher=PUBLISHERS[name],
             coverage='individual_statement_only',publication_status=status,raw_sha256=source['sha256'],retrieved_at=source.get('retrieved_at'),
             extracted_sha256=sha(out/filename),extraction_offsets=[a,b],capture_method=source.get('capture_method','Downloaded source bytes; HTML text extraction'),human_reviewed=False))
        for match in CUBA.finditer(body):
            written_candidates.append(dict(archive_id=aid,source_type='published_statement',file=filename,
                source_url=source['url'],body_offset=match.start(),
                context=body[max(0,match.start()-300):match.end()+300],human_reviewed=False))
    if (recovery/'written/gln.pdf').exists():
        source=read(recovery/'written/gln.json');assert sha(recovery/'written/gln.pdf')==source['sha256']
        (out/'w_gln.pdf').write_bytes((recovery/'written/gln.pdf').read_bytes())
        published.append(dict(archive_id='6613621f4cda',file='w_gln.pdf',url=source['url'],source_type='organizer_outcome_document',
             coverage='outcome_document_not_transcript',publication_status='Organizer-issued event communique, 22 September 2026',
             raw_sha256=source['sha256'],extracted_sha256=sha(out/'w_gln.pdf'),retrieved_at=source.get('retrieved_at'),human_reviewed=False))
    if (recovery/'written/ilo.docx').exists():
        source=read(recovery/'written/ilo.json');assert sha(recovery/'written/ilo.docx')==source['sha256']
        (out/'w_ilo.docx').write_bytes((recovery/'written/ilo.docx').read_bytes())
        body=(recovery/'written/ilo.txt').read_text(encoding='utf-8')
        body='\n'.join(line.rstrip() for line in body.splitlines())+'\n'
        (out/'w_ilo.txt').write_text('UNREVIEWED ORGANIZER-PROVIDED AUTOMATIC TRANSCRIPT (WIPO Speech-to-Text).\n'+source['url']+'\n'+body,encoding='utf-8',newline='\n')
        additional.append(dict(archive_id='cc5c5a4aef9f',file='w_ilo.txt',original_file='w_ilo.docx',url=source['url'],
            source_page='https://live.ilo.org/en/event/workplace-new-frontier-promoting-financial-health-2026-09-24',
            source_type='organizer_automatic_transcript',raw_sha256=source['sha256'],extracted_sha256=sha(out/'w_ilo.txt'),retrieved_at=source.get('retrieved_at'),
            human_reviewed=False,coverage='Retrieved organizer transcript; complete event coverage not independently verified'))
        for match in CUBA.finditer(body):
            written_candidates.append(dict(archive_id='cc5c5a4aef9f',source_type='organizer_automatic_transcript',file='w_ilo.txt',
                source_url=source['url'],body_offset=match.start(),context=body[max(0,match.start()-300):match.end()+300],human_reviewed=False))
    parents=collections.defaultdict(list);parent_titles={}
    for x in read(original/'segments.json'):
        if 'SDG Media Zone' in x['title']:
            parents[x['meeting_id']].append(x['text']);parent_titles[x['meeting_id']]=x['title']
    parent_grams={k:grams(' '.join(v)) for k,v in parents.items()}
    for item in caps:
        aid=item['archive_id'];base=baseline[aid];folder=recovery/aid;rows=[]
        record={k:item[k] for k in ('archive_id','title','date','video_url','status','checked_at')}
        record.update(priority=1 if aid in P1 else 2 if any(t in item['title'].lower() for t in ('health','food','migration','africa','leadership','technology')) else 3,
            priority_basis='Editorial triage by regional/policy adjacency and source availability; not an inferred Cuba mention',
            search_topic='2026 '+item['title'],written_sources=[x for x in published if x['archive_id']==aid],
            additional_transcripts=[x for x in additional if x['archive_id']==aid],
            human_reviewed=False,official_verbatim_record=False,baseline_download_status='unavailable',
            inventory_duration=base['duration'],video_duration_seconds=item.get('duration_seconds'))
        if item['status']=='caption_recovered':
            assert sha(recovery/item['caption_file'])==item['caption_sha256']
            rows=srt(recovery/item['caption_file']);record.update(source_type='publisher_caption',source_sha256=item['caption_sha256'])
            if not rows:raise ValueError('Empty or invalid caption file: '+aid)
            record['transcription_method']='Publisher-provided auto-generated captions' if 'Auto-generated' in (recovery/item['caption_file']).read_text(encoding='utf-8-sig') else 'Publisher-provided captions; production method not verified'
            label='UNREVIEWED PUBLISHER CAPTIONS. '+record['transcription_method']+'.'
        elif (folder/'asr.json').exists():
            a=read(folder/'asr.json');rows=a['segments'];record.update(status='local_asr_draft',source_type='local_machine_transcription',
                 model=a['model'],model_revision=a['model_revision'],source_sha256=a['audio_sha256'],
                 asr_duration_seconds=a['duration_seconds'],audio_track=a['audio_track'],asr_sha256=sha(folder/'asr.json'))
            flagged=[s for s in rows if s.get('avg_logprob',0)<-1 or s.get('compression_ratio',0)>2.4]
            record['quality_review']=dict(flagged_segments=len(flagged),
                criterion='avg_logprob < -1 or compression_ratio > 2.4; triage heuristic, not calibrated accuracy',
                flagged_starts=[s['start'] for s in flagged],audio_language_verified_by_human=False)
            label=a['disclaimer']
            if flagged:label+=' QUALITY REVIEW REQUIRED: '+str(len(flagged))+' cues have low-confidence or repetitive-text indicators.'
        else:record['status']='partial_written_only' if record['written_sources'] else 'video_transcription_pending'
        if rows:
            assert all(x['text'].strip() and 0<=x['start']<=x['end'] for x in rows)
            assert all(rows[i]['start']<=rows[i+1]['start'] for i in range(len(rows)-1))
            duration=record.get('asr_duration_seconds') or record.get('video_duration_seconds')
            if duration:assert max(x['end'] for x in rows)<=duration+10
            g=grams(' '.join(x['text'] for x in rows));score,parent=max((len(g&pg)/max(1,len(g)),k) for k,pg in parent_grams.items())
            record['parent_overlap']=dict(seven_word_shingle_fraction=round(score,4),candidate_parent=parent,
                candidate_title=parent_titles[parent],probable_overlap=score>=.65,
                meaning='Text overlap screening only; not complete event coverage or a verified timestamp alignment')
            filename='r_'+aid+'.txt';record.update(text_file=filename,segments=len(rows),first_cue=rows[0]['start'],last_cue=rows[-1]['end'])
            (out/filename).write_text(label+'\n'+item['video_url']+'\n\n'+'\n'.join(f"[{x['start']:.2f}-{x['end']:.2f}] {x['text']}" for x in rows)+'\n',encoding='utf-8',newline='\n')
            record['text_sha256']=sha(out/filename)
            h,m,s=map(int,base['duration'].split(':'));record['inventory_duration_seconds']=h*3600+m*60+s
            record['video_inventory_duration_difference_seconds']=round((duration or 0)-record['inventory_duration_seconds'],2)
            for i,x in enumerate(rows):
                if CUBA.search(x['text']):
                    candidates.append(dict(archive_id=aid,source_type=record['source_type'],start=x['start'],end=x['end'],
                       quote=x['text'],context=' '.join(y['text'] for y in rows[max(0,i-2):i+3]),
                       source_url=item['video_url'],probable_existing_overlap=score>=.65,human_reviewed=False))
        records.append(record)
    summary=dict(checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),events=len(records),
       statuses=dict(collections.Counter(x['status'] for x in records)),published_statements=sum(x['source_type']=='published_statement' for x in published),
       organizer_outcome_documents=sum(x['source_type']=='organizer_outcome_document' for x in published),
       organizer_automatic_transcripts=len(additional),
       events_with_written_sources=len({x['archive_id'] for x in published}),
       probable_parent_overlaps=sum(x.get('parent_overlap',{}).get('probable_overlap',False) for x in records),
       cuba_candidate_cues=len(candidates),cuba_written_candidates=len(written_candidates),baseline_counts_unchanged=True,human_review_complete=False)
    payload=dict(summary=summary,events=sorted(records,key=lambda x:(x['priority'],x['date'],x['title'])),cuba_candidates=candidates,cuba_written_candidates=written_candidates)
    (out/'recovery.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    h=html.escape
    candidate_cards=[];titles={x['archive_id']:x['title'] for x in records}
    for candidate in candidates:
        seconds=int(candidate['start']);timestamp=f'{seconds//3600}:{seconds%3600//60:02d}:{seconds%60:02d}'
        candidate_cards.append(f'<article><small>UNREVIEWED · {h(candidate["source_type"].replace("_"," "))} · {timestamp}</small><h3>{h(titles[candidate["archive_id"]])}</h3><blockquote>{h(candidate["quote"])}</blockquote><details><summary>Surrounding context</summary><p>{h(candidate["context"])}</p></details><p><a href="{h(candidate["source_url"])}">Open recording · seek to {timestamp}</a></p></article>')
    candidate_section='<section><h2>Background: general Cuba candidate passages</h2><p>These recovered references concern hurricane logistics and regional investment. Neither establishes an embargo connection. They are background, not primary embargo evidence; all remain unreviewed.</p>'+(''.join(candidate_cards) if candidate_cards else '<p>No literal candidate cues in the currently recovered caption/ASR text. This does not demonstrate that Cuba was never discussed.</p>')+'</section>'
    entries=[]
    for x in payload['events']:
        sources=[f'<a href="{h(w["file"])}">'+('Outcome document' if w['source_type']=='organizer_outcome_document' else h(w['publisher'])+' statement')+'</a>' for w in x['written_sources']]
        sources.extend(f'<a href="{h(w["file"])}">Organizer automatic transcript</a>' for w in x['additional_transcripts'])
        if x.get('text_file'):sources.append(f'<a href="{h(x["text_file"])}">Draft text</a>')
        sources.append(f'<a href="{h(x["video_url"])}">Video</a>');links=' · '.join(sources)
        overlap=x.get('parent_overlap',{});note=''
        if overlap.get('probable_overlap'):note=f'<p>Probable overlap with <a href="https://transcripts.un.org/en/{h(overlap["candidate_parent"])}">{h(overlap["candidate_title"])}</a>. Kept out of additive counts.</p>'
        if abs(x.get('video_inventory_duration_difference_seconds',0))>60:
            note+='<p>Recording duration differs from the transcript inventory. This text covers the retrieved recording; complete coverage of the originally listed event is unverified.</p>'
        if x.get('quality_review',{}).get('flagged_segments'):
            note+='<p>Audio review required: '+str(x['quality_review']['flagged_segments'])+' cues have low-confidence or repetitive-text indicators. The English track label does not independently verify the spoken language.</p>'
        status_label={'local_asr_draft':'machine transcription — unreviewed','caption_recovered':'publisher captions — unreviewed'}.get(x['status'],x['status'].replace('_',' '))
        entries.append(f'<article><small>Priority {x["priority"]} · {x["date"]} · {h(status_label)}</small><h2>{h(x["title"])}</h2><p>{links}</p>{note}</article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HLW source recovery</title><link rel="stylesheet" href="usun-theme.css"><style>body{margin:0;font:16px Arial;color:#202b38}header{background:#062135;color:white;border-bottom:4px solid #d01319;padding:30px}main{max-width:1080px;margin:auto;padding:28px}h1,h2{font-family:Georgia}h2{font-size:22px;color:#002d74}article{padding:22px 0;border-bottom:1px solid #d6dee7}small{color:#667085}a{color:#002d74}p{line-height:1.6}.note{background:#e7f1f8;padding:20px}input{padding:12px;width:100%;box-sizing:border-box;border:1px solid #667085}</style><header><h1>High-Level Week · Source recovery</h1><p>Working supplement / unreviewed / 21–28 September 2026</p></header><main><a href="index.html">← Cuba visual brief</a><h2>Primary analytical focus: the Cuba embargo</h2><p class="note">COUNTS</p><p>Published statements cover individual speakers. Publisher captions and local machine transcriptions are separate, unreviewed source types. Priority is editorial triage, not evidence of a Cuba position. Some missing clip pages overlap full-day transcripts already collected. The original brief's counts remain a frozen baseline.</p><p><a href="recovery.json">Download full provenance and candidate Cuba matches</a> · <a href="RECOVERY.md">Methods and review instructions</a></p><label for="q">Find an event, priority, or status</label><p><input id="q" type="search" placeholder="Search events"></p><div id="events">ENTRIES</div><p>Next: prioritize Cuba-linked embargo and blockade language, sanctions, terrorism-list designation, financial and extraterritorial restrictions, and stated humanitarian or trade effects. General Cuba mentions are background. Verify each Cuba connection and reconcile overlaps before adding recovered evidence.</p></main><script>document.querySelector('#q').oninput=e=>document.querySelectorAll('article').forEach(a=>a.hidden=!a.textContent.toLowerCase().includes(e.target.value.toLowerCase()))</script></html>'''
    counts=f'{summary["events"]} events checked · {summary["published_statements"]} written statements · {summary["organizer_outcome_documents"]} outcome document · {summary["organizer_automatic_transcripts"]} organizer automatic transcript · {summary["statuses"].get("caption_recovered",0)} caption files · {summary["statuses"].get("local_asr_draft",0)} machine-transcription drafts · {summary["probable_parent_overlaps"]} probable overlaps with existing full-day recordings.'
    page=page.replace('<label for="q">',candidate_section+'<label for="q">')
    (out/'recovery.html').write_text(page.replace('COUNTS',h(counts)).replace('ENTRIES',''.join(entries)).replace("document.querySelectorAll('article')","document.querySelectorAll('#events article')"),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('original');p.add_argument('recovery');p.add_argument('out');a=p.parse_args();build(a.original,a.recovery,a.out)
