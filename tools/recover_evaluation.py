"""Recover unlabelled later-date candidates from the existing UN ASR archive."""
import argparse, hashlib, json
from collections import Counter
from pathlib import Path
from reviewed_loader import load_bundle, safe

def recover(archive, pilot, output):
    archive, output = Path(archive), Path(output)
    reviewed = load_bundle(pilot)
    cutoff = max(r['event_date'] for r in reviewed['records'])
    countries = {r['iso3'] for r in reviewed['records']}
    read = lambda name: json.loads(safe(archive, name).read_text(encoding='utf-8'))
    inventory, hashes = read('inventory.json'), read('SHA256.json')
    records, segments = read('records.json'), read('segments.json')
    meetings = [m for m in inventory['meetings'] if m['date'][:10] > cutoff and 'general debate' in m['title'].lower()]
    raw_docs, provenance = {}, []
    for m in meetings:
        name = 'raw/' + m['archive_id'] + '.json'
        raw = safe(archive, name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != hashes.get(name): raise ValueError('Archive hash mismatch: ' + name)
        doc = json.loads(raw)
        if doc['video']['date'][:10] != m['date'][:10] or doc['video']['slug'] != m['slug']: raise ValueError('Source identity mismatch')
        if doc['transcript']['language'] != 'en': raise ValueError('Non-English transcript')
        raw_docs[name] = doc
        provenance.append(dict(date=m['date'][:10], url=doc['url'], sha256=digest))
    candidates, excluded, seen = [], Counter(), set()
    for r in records:
        if r['scope'] != 'general_debate' or r['speech_date'] <= cutoff: continue
        if not r['country_id']: excluded['unmapped_affiliation'] += 1; continue
        parts = [s for s in segments if s['record_id'] == r['statement_id']]
        if not parts: raise ValueError('Missing source segments')
        for s in parts:
            doc = raw_docs[s['raw_file']]
            original = doc['transcript']['data'][int(s['json_pointer'].split('/')[-1])]
            text = ' '.join(v['text'] for p in original.get('paragraphs', []) for v in p.get('sentences', []))
            if text != s['text'] or r['text'][s['start_char_0']:s['end_char_0']] != text: raise ValueError('Source text mismatch')
        if '\n\n'.join(s['text'] for s in parts) != r['text']: raise ValueError('Incomplete grouped source')
        digest = hashlib.sha256(r['text'].encode()).hexdigest()
        if digest in seen: excluded['exact_duplicate'] += 1; continue
        seen.add(digest)
        candidates.append(dict(r, text_sha256=digest, source_segments=parts,
                               overlaps_pilot_country=r['country_id'] in countries,
                               human_review_complete=False, evaluation_ready=False))
    output.mkdir(parents=True, exist_ok=False)
    (output/'candidates.json').write_text(json.dumps(candidates, ensure_ascii=False), encoding='utf-8')
    summary = dict(source='archived UN automatic transcripts', sources=provenance,
                   candidates=len(candidates), by_date=dict(Counter(r['speech_date'] for r in candidates)),
                   overlapping_country_candidates=sum(r['overlaps_pilot_country'] for r in candidates),
                   exclusions=dict(excluded), all_text_bound_to_raw=True, human_review_complete=False,
                   evaluation_ready=False, available_at_basis='archive collection time, not event time',
                   archive_collected_at=inventory['collected_at'],
                   caveat='Country-grouped ASR records may include multiple interventions, not one verified national address. No model evaluation or labels assigned.')
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    return summary

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('archive'); p.add_argument('pilot'); p.add_argument('output')
    a=p.parse_args(); print(json.dumps(recover(a.archive,a.pilot,a.output),indent=2))
