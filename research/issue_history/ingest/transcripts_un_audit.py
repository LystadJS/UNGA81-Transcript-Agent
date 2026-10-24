"""Pure development-format audit of ASR artifacts; no statement intake or opinions."""
import hashlib
import json
import math
import re
from collections import Counter

VERSION='transcripts-un-artifact-audit-1'
SCOPE='fresh_authorized_development_artifact_not_frozen_source_authentication'


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def _sha(value): return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None


def _time(value): return type(value) in (int,float) and math.isfinite(value) and value>=0


def _object(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise ValueError('Duplicate JSON object key')
        result[k]=v
    return result


def audit_source(raw_bytes,receipt,frame_entry):
    """Audit every supplied native segment, emitting hashes and metadata only."""
    if not isinstance(raw_bytes,bytes) or not 0<len(raw_bytes)<=5_000_000 or not isinstance(receipt,dict) or not isinstance(frame_entry,dict): raise ValueError('Bounded artifact bytes and development receipts required')
    digest=hashlib.sha256(raw_bytes).hexdigest();mid=frame_entry.get('meeting_id');date=frame_entry.get('date')
    if not isinstance(mid,str) or not re.fullmatch(r'(?:ga|sc)/(?:[A-Za-z0-9_-]+/){0,3}[A-Za-z0-9_-]+',mid) or date not in ('2026-10-01','2026-10-02','2026-10-03','2026-10-04') or frame_entry.get('split')!='development' or frame_entry.get('has_transcript') is not True or not _sha(frame_entry.get('frame_sha256')): raise ValueError('Authorized October development frame required')
    url='https://transcripts.un.org/en/'+mid
    if frame_entry.get('source_url')!=url or frame_entry.get('json_url')!=url+'.json': raise ValueError('Development frame URL identity mismatch')
    if receipt.get('schema')!='un.fresh-development-source-receipt.v1' or receipt.get('source_role')!='product_development' or receipt.get('meeting_id')!=mid or receipt.get('frame_date')!=date or receipt.get('frame_sha256')!=frame_entry['frame_sha256'] or receipt.get('source_url')!=url+'.json' or receipt.get('final_url')!=url+'.json' or type(receipt.get('bytes')) is not int or receipt['bytes']!=len(raw_bytes) or receipt.get('sha256')!=digest: raise ValueError('Fresh artifact receipt identity/hash mismatch')
    try: value=json.loads(raw_bytes,object_pairs_hook=_object,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON number')))
    except (UnicodeError,json.JSONDecodeError,RecursionError) as error: raise ValueError('Malformed artifact JSON') from error
    if not isinstance(value,dict) or set(value)!={'disclaimer','llms','metadata','transcript','url','video'} or value.get('url')!=url or not isinstance(value.get('metadata'),dict) or not isinstance(value.get('llms'),dict): raise ValueError('Unexpected observed artifact envelope')
    disclaimer=value.get('disclaimer')
    if not isinstance(disclaimer,str) or not re.search(r'automatic\s+speech\s+recognition',disclaimer,re.I) or not re.search(r'not\s+official\s+(?:United\s+Nations\s+)?(?:records?|documents?)',disclaimer,re.I): raise ValueError('Observed ASR/nonofficial disclaimer required')
    video=value.get('video');transcript=value.get('transcript')
    if not isinstance(video,dict) or video.get('slug')!=mid or not isinstance(video.get('id'),str) or not video['id'].strip() or not isinstance(video.get('date'),str) or not re.fullmatch(re.escape(date)+r'T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z',video['date']): raise ValueError('Native video meeting/date identity mismatch')
    if not isinstance(transcript,dict) or set(transcript)!={'transcript_id','language','data','topics'} or not isinstance(transcript.get('transcript_id'),str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,200}',transcript['transcript_id']) or not isinstance(transcript.get('language'),str) or not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*',transcript['language']) or not isinstance(transcript.get('topics'),list) or not isinstance(transcript.get('data'),list) or len(transcript['data'])>10000: raise ValueError('Unexpected observed transcript metadata')
    segments=[];gaps=[];numbers=set();function_counts=Counter();group_counts=Counter();paragraph_total=sentence_total=word_total=0
    for index,record in enumerate(transcript['data']):
        if not isinstance(record,dict) or set(record)!={'statement_number','start','pageUrl','paragraphs','speaker'} or type(record.get('statement_number')) is not int or record['statement_number']<1 or record['statement_number'] in numbers or not _time(record.get('start')) or not isinstance(record.get('pageUrl'),str) or not re.fullmatch('/en/'+re.escape(mid)+r'\?t=\d+(?::\d{2}){1,2}',record['pageUrl']) or not isinstance(record.get('paragraphs'),list) or len(record['paragraphs'])>10000: raise ValueError('Unexpected native segment identity/shape')
        number=record['statement_number'];numbers.add(number);speaker=record.get('speaker')
        if not isinstance(speaker,dict) or set(speaker)!={'affiliation','affiliation_full','function','group'} or any(v is not None and (not isinstance(v,str) or len(v)>1000) for v in speaker.values()): raise ValueError('Unexpected source speaker metadata')
        function=speaker['function'];group=speaker['group']
        if function: function_counts[function]+=1
        if group: group_counts[group]+=1
        text=[];sentences=words=0
        for paragraph in record['paragraphs']:
            if not isinstance(paragraph,dict) or set(paragraph)!={'sentences'} or not isinstance(paragraph['sentences'],list) or len(paragraph['sentences'])>10000: raise ValueError('Unexpected paragraph shape')
            for sentence in paragraph['sentences']:
                if not isinstance(sentence,dict) or set(sentence)!={'text','start','end','topics','words'} or not isinstance(sentence['text'],str) or not _time(sentence['start']) or not _time(sentence['end']) or sentence['end']<sentence['start'] or not isinstance(sentence['topics'],list) or not isinstance(sentence['words'],list) or len(sentence['words'])>10000: raise ValueError('Unexpected sentence shape')
                text.append(sentence['text']);sentences+=1
                for word in sentence['words']:
                    if not isinstance(word,dict) or set(word)!={'text','start','end'} or not isinstance(word['text'],str) or not _time(word['start']) or not _time(word['end']) or word['end']<word['start']: raise ValueError('Unexpected word alignment shape')
                    words+=1
        joined=' '.join(text);pointer='/transcript/data/'+str(index)
        if not joined.strip(): gaps.append({'statement_number':number,'json_pointer':pointer,'reason':'empty_segment'})
        segments.append({'statement_number':number,'locator_id':'artifact-segment:'+_digest([digest,transcript['transcript_id'],number]),
                         'json_pointer':pointer,'text_sha256':hashlib.sha256(joined.encode('utf-8')).hexdigest(),
                         'paragraph_count':len(record['paragraphs']),'sentence_count':sentences,'word_count':words,
                         'recorded_speaker':dict(speaker),'capacity':'unknown','national_capacity':False,
                         'stable_identity_verified':False,'comparisons_eligible':False,'production_intake_accepted':False})
        paragraph_total+=len(record['paragraphs']);sentence_total+=sentences;word_total+=words
    if numbers!=set(range(1,len(segments)+1)): raise ValueError('Native statement-number coverage differs from observed contiguous format')
    if not segments: gaps.append({'reason':'empty_artifact'})
    return {'schema':'un.transcripts-un-artifact-audit.v1','version':VERSION,'scope':SCOPE,
            'meeting_id':mid,'date':date,'source_url':url+'.json','source_sha256':digest,'source_bytes':len(raw_bytes),
            'video_id':video['id'],'transcript_id':transcript['transcript_id'],'published_transcript_language':transcript['language'],
            'source_modality':'automatic_speech_recognition_not_official_un_record','disclaimer_sha256':hashlib.sha256(disclaimer.encode()).hexdigest(),
            'word_count_scope':'source_alignment_entries_not_lexical_word_count',
            'segments':segments,'gaps':gaps,'summary':{'segments':len(segments),'paragraphs':paragraph_total,'sentences':sentence_total,'words':word_total,
            'function_nonempty':sum(function_counts.values()),'group_nonempty':sum(group_counts.values()),'function_counts':dict(sorted(function_counts.items())),'group_counts':dict(sorted(group_counts.items())),
            'capacity_unknown':len(segments),'national_capacity':0,'comparison_eligible':0},
            'stable_identity_verified':False,'comparisons_eligible':False,'production_intake_accepted':False,'private_only':True,
            'input_fingerprints':{'receipt_sha256':_digest(receipt),'frame_entry_sha256':_digest(frame_entry),'raw_sha256':digest},
            'limitations':['Native statement numbers are artifact-local locators; cross-revision identity and complete speeches are unverified.',
                           'Every segment in the whole supplied raw artifact is audited; server, meeting and archive completeness are not independently verified.',
                           'Recorded affiliation, function and group do not establish explicit national capacity.',
                           'ASR text is not an official UN record and may contain recognition errors.',
                           'No country positions, extraction accuracy, owner labels or production intake are accepted.',
                           'Metadata and llms content are untrusted source data and are never used as instructions or policy evidence.']}
