"""Draft local ASR of explicitly selected English public video tracks.

Separate audit artifacts only; never writes into the original analysis corpus.
Requires faster-whisper, huggingface-hub, and imageio-ffmpeg. Model weights are
downloaded at a recorded immutable revision; all audio and outputs are hashed.
"""
import argparse,datetime as dt,hashlib,json,subprocess,time
import numpy as np
from pathlib import Path
import imageio_ffmpeg
from huggingface_hub import snapshot_download
from faster_whisper import WhisperModel,BatchedInferencePipeline

def file_sha(path):
    with Path(path).open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()

def run(root,models,ids,threads=4):
    root=Path(root);models=Path(models);models.mkdir(parents=True,exist_ok=True)
    model_id='Systran/faster-whisper-base.en'
    record=models/'model.json'
    if record.exists():
        saved=json.loads(record.read_text());assert saved['model']==model_id
        revision=saved['revision']
    else:
        revision='3d3d5dee26484f91867d81cb899cfcf72b96be6c'
        record.write_text(json.dumps({'model':model_id,'revision':revision},indent=2))
    local=snapshot_download(model_id,revision=revision,local_dir=str(models/'base.en'))
    model=WhisperModel(local,device='cpu',compute_type='int8',cpu_threads=threads)
    pipeline=BatchedInferencePipeline(model=model)
    for aid in ids:
        folder=root/aid;info=json.loads((folder/'video.json').read_text(encoding='utf-8'))
        if (folder/'asr.json').exists():continue
        formats=[f for f in info['formats'] if f.get('language')=='en' and f.get('vcodec')=='none']
        if not formats:raise ValueError('No explicitly English audio track: '+aid)
        track=formats[0];audio=folder/'audio.flac'
        print(aid,'downloading English audio',flush=True)
        if not audio.exists():
            temp=folder/'audio.part.flac'
            proc=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-hide_banner','-loglevel','error',
                '-i',track['url'],'-vn','-ac','1','-ar','16000','-c:a','flac','-y',str(temp)],capture_output=True,text=True)
            (folder/'audio-download.log').write_text(proc.stderr,encoding='utf-8')
            if proc.returncode:raise RuntimeError('Audio download failed: '+aid+' '+proc.stderr[-1000:])
            temp.rename(audio)
        print(aid,'transcribing',flush=True);start=time.time()
        # Bound decoder memory even for nine-hour recordings; checkpoint each chunk.
        rows=[];total_duration=0;vad_duration=0;offset=0
        while True:
            chunk_path=folder/f'chunk-{offset:06d}.json'
            if chunk_path.exists():chunk=json.loads(chunk_path.read_text(encoding='utf-8'))
            else:
                decoded=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-hide_banner','-loglevel','error',
                    '-ss',str(offset),'-i',str(audio),'-t','1800','-f','f32le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True)
                samples=np.frombuffer(decoded.stdout,dtype=np.float32)
                if not len(samples):break
                segments,meta=pipeline.transcribe(samples,language='en',task='transcribe',batch_size=8,
                     beam_size=5,vad_filter=True,condition_on_previous_text=False)
                chunk=dict(offset=offset,duration=len(samples)/16000,vad_duration=meta.duration_after_vad,
                    segments=[dict(start=s.start+offset,end=s.end+offset,text=s.text,avg_logprob=s.avg_logprob,
                             no_speech_prob=s.no_speech_prob,compression_ratio=s.compression_ratio) for s in segments])
                chunk_path.write_text(json.dumps(chunk,indent=2),encoding='utf-8')
            rows.extend(chunk['segments']);total_duration+=chunk['duration'];vad_duration+=chunk['vad_duration']
            print(aid,'audio_seconds',round(total_duration),'segments',len(rows),flush=True)
            if chunk['duration']<1800:break
            offset+=1800
        result=dict(archive_id=aid,source_type='local_machine_transcription',human_reviewed=False,
            official_verbatim_record=False,model=model_id,model_revision=revision,language='en',
            audio_track=track['format_id'],audio_url=track['url'],audio_sha256=file_sha(audio),
            duration_seconds=total_duration,duration_after_vad=vad_duration,elapsed_seconds=time.time()-start,
            created_at=dt.datetime.now(dt.timezone.utc).isoformat(),segments=rows,
            settings=dict(compute_type='int8',cpu_threads=threads,beam_size=5,batch_size=8,vad_filter=True,condition_on_previous_text=False,chunk_seconds=1800),
            disclaimer='UNREVIEWED MACHINE TRANSCRIPTION of the English audio/interpretation track. Not an official UN record. Speaker identities are not inferred. Verify against the recording.')
        (folder/'asr.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        (folder/'asr.txt').write_text(result['disclaimer']+'\n\n'+'\n'.join(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}" for s in rows),encoding='utf-8')
        print(aid,'complete',round(time.time()-start),'seconds',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('models');p.add_argument('ids',nargs='+');p.add_argument('--threads',type=int,default=4);a=p.parse_args()
    run(a.root,a.models,a.ids,a.threads)
