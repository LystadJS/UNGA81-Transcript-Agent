"""Retrieve bounded English clips and make a separate machine-transcription check.

Input metadata comes from the official source and yt-dlp. Clips and ASR remain
local. No ASR result is a human decision, correction or verified quotation.
"""
import argparse, datetime as dt, hashlib, json, subprocess, re
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d): Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def run(corpus_path, metadata, plan_path, model_path, output):
    import imageio_ffmpeg
    from faster_whisper import WhisperModel
    corpus=read(corpus_path); records={r['id']:r for r in corpus['records']}
    metadata=Path(metadata); output=Path(output); output.mkdir(parents=True,exist_ok=False)
    model_path=Path(model_path); model=WhisperModel(str(model_path/'base.en'),device='cpu',compute_type='int8',cpu_threads=4)
    model_record=read(model_path/'model.json'); model_record['weights_sha256']=sha((model_path/'base.en/model.bin').read_bytes())
    rows=[]
    for item in read(plan_path)['concerns']:
        parent=records[item['parent_id']]; slug,index=parent['id'].split('#'); stem=slug.rsplit('/',1)[1]
        raw=(metadata/(stem+'.json')).read_bytes(); data=json.loads(raw)
        if sha(raw)!=parent['raw_sha256'] or data['video']['slug']!=slug: raise ValueError('Source snapshot differs from original corpus: '+slug)
        sentences=[s for p in data['transcript']['data'][int(index)]['paragraphs'] for s in p['sentences']]
        if ' '.join(s['text'] for s in sentences)!=parent['text'] or sha(parent['text'].encode())!=parent['text_sha256']: raise ValueError('Parent text mismatch')
        lo,hi=item['sentences']; assert 0<=lo<hi<=len(sentences)
        offset=sum(len(s['text'])+1 for s in sentences[:lo]); text=' '.join(s['text'] for s in sentences[lo:hi]); end=offset+len(text)
        assert parent['text'][offset:end]==text
        start=max(0,sentences[lo]['start']-8); stop=sentences[hi-1]['end']+8
        if stop-start>90: raise ValueError('Clip exceeds 90 seconds')
        info=read(metadata/(stem+'-video.json'))
        if info.get('id')!=data['video']['kaltura_id']: raise ValueError('Video identity mismatch')
        track=next(f for f in info['formats'] if f.get('language')=='en' and f.get('vcodec')=='none')
        row={**item,'source_url':parent['source_url'],'video_url':data['video']['url'],'parent_text_sha256':parent['text_sha256'],
             'source_snapshot_sha256':sha(raw),'offset_unit':'Unicode code points; zero-based; end exclusive','start':offset,'end':end,
             'original_excerpt':text,'clip_start_seconds':start,'clip_end_seconds':stop,'track_language':'en','track_id':track['format_id'],
             'status':'unresolved','human_reviewed':False}
        clip=output/(item['id']+'.mp3')
        try:
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-hide_banner','-loglevel','error','-ss',str(start),'-i',track['url'],
                '-t',str(stop-start),'-vn','-ac','1','-ar','16000','-b:a','64k',str(clip)],check=True,capture_output=True,timeout=120)
            segments,info=model.transcribe(str(clip),language='en',beam_size=5,vad_filter=True,condition_on_previous_text=False)
            row.update(clip_file=clip.name,clip_sha256=sha(clip.read_bytes()),decoded_duration_seconds=info.duration,
                machine_segments=[{'start':s.start,'end':s.end,'text':s.text,'avg_logprob':s.avg_logprob,'no_speech_prob':s.no_speech_prob} for s in segments])
            if abs(info.duration-(stop-start))>2: raise ValueError('Decoded clip duration does not match requested interval')
            row.update(status='machine_comparison_pending_listening',model=model_record,
                       machine_text=' '.join(s['text'].strip() for s in row['machine_segments']))
        except Exception as e:
            row.update(status='unresolved',error=str(e))
        rows.append(row); write(output/'audio-checks.json',{'schema':'un.audio-checks.v1','corpus_sha256':sha(Path(corpus_path).read_bytes()),
            'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'method':'Independent local ASR of a bounded English audio/interpretation clip. Not human listening or authenticated wording.','rows':rows})
        print(item['id'],row['status'],row.get('machine_text',row.get('error','')),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('corpus');p.add_argument('metadata');p.add_argument('plan');p.add_argument('models');p.add_argument('output');a=p.parse_args()
    run(a.corpus,a.metadata,a.plan,a.models,a.output)
