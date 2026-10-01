"""Validate recovered artifacts and local links without claiming human review."""
import argparse,hashlib,json,re
from html.parser import HTMLParser
from pathlib import Path

def check(folder):
    folder=Path(folder);data=json.loads((folder/'recovery.json').read_text(encoding='utf-8'))
    events=data['events'];assert len(events)==41 and len({x['archive_id'] for x in events})==41
    statements=0;texts=0;outcomes=0;organizer_transcripts=0
    for item in events:
        assert item['human_reviewed'] is False and item['official_verbatim_record'] is False
        if item.get('text_file'):
            p=folder/item['text_file'];assert p.resolve().is_relative_to(folder.resolve())
            assert hashlib.sha256(p.read_bytes()).hexdigest()==item['text_sha256']
            assert 'UNREVIEWED' in p.read_text(encoding='utf-8').splitlines()[0]
            assert item['segments']>0;texts+=1
            assert item['source_type'] in ('publisher_caption','local_machine_transcription')
            if item['source_type']=='local_machine_transcription':
                assert item['model_revision'] and len(item['source_sha256'])==64
                assert item['quality_review']['audio_language_verified_by_human'] is False
        for s in item['written_sources']:
            assert s['coverage'] in ('individual_statement_only','outcome_document_not_transcript')
            assert hashlib.sha256((folder/s['file']).read_bytes()).hexdigest()==s['extracted_sha256']
            if s['source_type']=='published_statement':statements+=1
            else:outcomes+=1
        for s in item.get('additional_transcripts',[]):
            assert s['source_type']=='organizer_automatic_transcript' and s['human_reviewed'] is False
            assert hashlib.sha256((folder/s['file']).read_bytes()).hexdigest()==s['extracted_sha256']
            assert hashlib.sha256((folder/s['original_file']).read_bytes()).hexdigest()==s['raw_sha256']
            organizer_transcripts+=1
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for key,value in attrs:
                if key in ('src','href') and value and not value.startswith(('https:','http:','#','data:')):
                    assert (folder/value.split('#')[0]).exists(),value
    for page in ('recovery.html','index.html'):
        Links().feed((folder/page).read_text(encoding='utf-8'))
    assert data['summary']['published_statements']==statements
    assert data['summary']['organizer_outcome_documents']==outcomes
    assert data['summary']['organizer_automatic_transcripts']==organizer_transcripts
    assert data['summary']['cuba_candidate_cues']==len(data['cuba_candidates'])
    assert data['summary']['cuba_written_candidates']==len(data['cuba_written_candidates'])
    assert all(x['human_reviewed'] is False for x in data['cuba_candidates']+data['cuba_written_candidates'])
    result=dict(events_verified=41,transcript_hashes_verified=texts,written_statement_hashes_verified=statements,
                outcome_document_hashes_verified=outcomes,organizer_transcripts_verified=organizer_transcripts,
                local_links_valid=True,source_types_labeled=True,human_review_complete=False)
    (folder/'recovery-check.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args();check(a.folder)
