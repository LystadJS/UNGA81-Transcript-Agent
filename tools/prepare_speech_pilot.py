"""Build an offline review packet; originals and previous decisions are read-only."""
import argparse,base64,hashlib,json,math
from pathlib import Path
from passage_type_audit import load_corpus,validate_mask

PARENTS=['asset/k1b/k1b5jwwa58#23','asset/k18/k18iyhzwip#42','asset/k1k/k1kfcwu5kc#37']
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()

def sentences_for(row,metadata):
    slug,index=row['id'].split('#');raw=(Path(metadata)/(slug.rsplit('/',1)[1]+'.json')).read_bytes()
    if sha(raw)!=row['raw_sha256']:raise ValueError('Raw source snapshot changed')
    doc=json.loads(raw)
    if doc['video']['slug']!=slug:raise ValueError('Wrong source slug')
    sentences=[s for p in doc['transcript']['data'][int(index)]['paragraphs'] for s in p['sentences']]
    if ' '.join(s['text'] for s in sentences)!=row['text']:raise ValueError('Source sentences do not reconstruct the original')
    offsets=[];pos=0
    for s in sentences:offsets.append((pos,pos+len(s['text'])));pos+=len(s['text'])+1
    return sentences,offsets

def chunks(row,metadata):
    sentences,offsets=sentences_for(row,metadata);result=[];first=0;words=0
    for i,s in enumerate(sentences):
        count=len(s['text'].split())
        if words and words+count>250:
            result.append((first,i));first=i;words=0
        words+=count
        if words>=180:result.append((first,i+1));first=i+1;words=0
    if first<len(sentences):result.append((first,len(sentences)))
    return [dict(start=offsets[a][0],end=offsets[b-1][1],sentence_start=a,sentence_end=b,
                 source_start_seconds=sentences[a]['start'],source_end_seconds=sentences[b-1]['end']) for a,b in result]

def prepare(corpus_path,mask_path,metadata,audio_path,output):
    corpus,corpus_sha=load_corpus(corpus_path);records={r['id']:r for r in corpus['records']}
    mask=read(mask_path);types={r['id']:r['confirmed_type'] for r in validate_mask(corpus,corpus_sha,mask)}
    if any(t is None for t in types.values()):raise ValueError('Owner passage-type review is incomplete')
    audio_path=Path(audio_path);audio=read(audio_path)
    if audio['corpus_sha256']!=corpus_sha:raise ValueError('Wrong audio-check collection')
    selected=[];coverage=[]
    for parent_id in PARENTS:
        row=records[parent_id]
        if types[parent_id]!='substantive_speech':raise ValueError('Pilot parent is not a reviewed substantive address')
        proposals=chunks(row,metadata);indices=sorted({math.floor(j*(len(proposals)-1)/3+.5) for j in range(4)})
        for i in indices:
            p=proposals[i];text=row['text'][p['start']:p['end']]
            selected.append(dict(id='P'+str(len(selected)+1).zfill(2),parent_id=parent_id,**p,text_sha256=sha(text.encode()),words=len(text.split()),
                reason=f'Proposal {i+1} of {len(proposals)} sentence-aligned chunks; selected at four evenly spaced positions in this parent.'))
        coverage.append({'parent_id':parent_id,'country':row['country'],'total_words':len(row['text'].split()),'candidate_chunks':len(proposals),
            'selected_chunks':len(indices),'selected_words':sum(len(row['text'][proposals[i]['start']:proposals[i]['end']].split()) for i in indices)})
    audio_rows=[]
    for row in audio['rows']:
        parent=records[row['parent_id']]
        if parent['text'][row['start']:row['end']]!=row['original_excerpt'] or parent['text_sha256']!=row['parent_text_sha256']:raise ValueError('Audio excerpt provenance mismatch')
        result={k:v for k,v in row.items() if k!='clip_file'}
        if row.get('clip_file'):
            clip=(audio_path.parent/row['clip_file']).read_bytes()
            if sha(clip)!=row['clip_sha256']:raise ValueError('Clip changed')
            result['audio_base64']=base64.b64encode(clip).decode('ascii')
        audio_rows.append(result)
    ids=list(dict.fromkeys(PARENTS+[r['parent_id'] for r in audio_rows]));parents=[{**records[id],'reviewed_type':types[id]} for id in ids]
    data={'schema':'un.speech-pilot-packet.v1','corpus_sha256':corpus_sha,'reviewed_mask_sha256':sha(Path(mask_path).read_bytes()),
        'selection':'Twelve purposive boundary proposals from Palau, Fiji and Vanuatu, selected from the leading substantive membership-change cases. Four evenly spaced chunks per speech; not a representative sample or a complete partition.',
        'offset_unit':'Unicode code points; zero-based; end exclusive','audio':audio_rows,'parents':parents,'passages':selected,'coverage':coverage}
    output=Path(output);output.mkdir(parents=True,exist_ok=False);raw=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8');(output/'speech-pilot.json').write_bytes(raw)
    site=Path(__file__).resolve().parents[1]/'site';html=(site/'passage-pilot.html').read_text(encoding='utf-8')
    css=(site/'analysis.css').read_text(encoding='utf-8')+'\n'+(site/'passage-pilot.css').read_text(encoding='utf-8')
    seal=base64.b64encode((site.parent/'reports/hlw-cuba/seal.png').read_bytes()).decode('ascii');css=css.replace('reports/hlw-cuba/seal.png','data:image/png;base64,'+seal)
    html=html.replace('<link rel="stylesheet" href="analysis.css"><link rel="stylesheet" href="passage-pilot.css">','<style>'+css+'</style>')
    for name in ['passage-pilot-core.js','passage-pilot.js']:
        script=(site/name).read_text(encoding='utf-8');html=html.replace(f'<script defer src="{name}"></script>','');html=html.replace('</body>','<script>'+script+'</script></body>')
    html=html.replace('id="embedded-packet">null','id="embedded-packet">'+json.dumps({'base64':base64.b64encode(raw).decode('ascii')}))
    (output/'review.html').write_text(html,encoding='utf-8')
    summary={'schema':'un.speech-pilot-summary.v1','corpus_sha256':corpus_sha,'packet_sha256':sha(raw),'parents_with_passages':len(PARENTS),'passage_proposals':len(selected),'audio_concerns':len(audio_rows),'human_decisions':0,'originals_changed':False,'coverage':coverage,'raw_text_and_clips_published':False}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('corpus');p.add_argument('mask');p.add_argument('metadata');p.add_argument('audio');p.add_argument('output');a=p.parse_args()
    prepare(a.corpus,a.mask,a.metadata,a.audio,a.output)
