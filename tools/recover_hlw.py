"""Recover public publisher captions for missing HLW events, preserving provenance.

Run after written-source searches. Captions are publisher-provided and unreviewed;
they are never represented as official transcripts or newly generated ASR.
Requires yt-dlp. Original collection and core application remain untouched.
"""
import argparse, concurrent.futures, datetime as dt, hashlib, json, re
import urllib.request
from pathlib import Path
import yt_dlp

def recover(coverage, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    items=[x for x in json.loads(Path(coverage).read_text(encoding='utf-8'))
           if x['collection_status']=='unavailable' and x['scope']=='broader_hlw']
    assert len({x['archive_id'] for x in items})==len(items)
    def one(item):
        folder=output/item['archive_id'];folder.mkdir(exist_ok=True)
        url='https://webtv.un.org/en/'+item['slug']
        result={'archive_id':item['archive_id'],'title':item['title'],'date':item['date'][:10],
                'video_url':url,'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),
                'source_type':'publisher_caption','human_reviewed':False,
                'official_verbatim_record':False,'transcription_method':'Publisher caption; production method unverified'}
        try:
            with yt_dlp.YoutubeDL({'quiet':True,'no_warnings':True,'skip_download':True,
                                  'socket_timeout':20,'retries':1}) as ydl:
                info=ydl.extract_info(url,download=False)
                (folder/'video.json').write_text(json.dumps(ydl.sanitize_info(info),indent=2),encoding='utf-8')
            subtitles=info.get('subtitles') or {}
            result.update(video_id=info['id'],duration_seconds=info.get('duration'),
                          languages=list(subtitles),format_count=len(info.get('formats',[])))
            language=next((x for x in subtitles if x=='en'),None)
            if not language:language=next((x for x in subtitles if x.startswith('en-')),None)
            if language:
                options=subtitles[language];sub=next((x for x in options if x.get('ext')=='srt'),options[0])
                request=urllib.request.Request(sub['url'],headers={'User-Agent':'Mozilla/5.0'})
                with urllib.request.urlopen(request,timeout=30) as response:raw=response.read(20_000_001)
                if len(raw)>20_000_000:raise ValueError('Caption exceeds size limit')
                ext=sub.get('ext','txt');assert re.fullmatch('[a-z0-9]+',ext)
                name='caption.'+ext;(folder/name).write_bytes(raw)
                result.update(status='caption_recovered',language=language,caption_file=item['archive_id']+'/'+name,
                              caption_url=sub['url'],caption_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
            else:result['status']='no_english_publisher_caption'
        except Exception as error:result.update(status='retrieval_error',error=str(error))
        (folder/'provenance.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(item['archive_id'],result['status'],flush=True)
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(one,items))
    (output/'captions.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('coverage');p.add_argument('output');a=p.parse_args()
    recover(a.coverage,a.output)
