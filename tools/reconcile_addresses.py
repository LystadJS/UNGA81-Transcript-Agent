"""Reconcile user DOCX variants against hash-pinned General Debate ASR sources.

Private output stays outside Git. No edited upload is promoted to verbatim truth.
Standard library only; run from repository root. See --help.
"""
import argparse
import collections
import csv
import datetime as dt
import difflib
import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
ALIASES = {
    'eu': 'EU', 'holy see': 'VAT', 'state of palestine': 'PSE',
    'secretary general': 'UN', 'republic of congo': 'COG', 'brunei': 'BRN',
    "cote d'ivoire": 'CIV', 'micronesia': 'FSM', 'russia': 'RUS',
    'st. kitts and nevis': 'KNA', 'st. lucia': 'LCA',
    'st. vincent and the grenadines': 'VCT', 'turkey': 'TUR',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tokens(text):
    return re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold())


def grams(words):
    return set(zip(*(words[i:] for i in range(5))))


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(archive, source_dir, output, repo):
    output.mkdir(parents=True, exist_ok=True)
    for folder in ['variants', 'canonical', 'diffs']:
        (output / folder).mkdir(exist_ok=True)
    registry = list(csv.DictReader((repo / 'un/config/countries.csv').open(encoding='utf-8-sig')))
    aliases = {v.casefold(): r['iso3'] for r in registry
               for v in (r['aliases'] + '|' + r['country']).split('|')}
    aliases.update(ALIASES)
    by_iso = {r['iso3']: r for r in registry}
    coverage = list(csv.DictReader((repo / 'reports/hlw-cuba/coverage.csv').open(encoding='utf-8-sig')))
    hashes = json.loads((repo / 'reports/hlw-cuba/source-hashes.json').read_text())
    sources, segments = [], []
    for row in coverage:
        if row['scope'] != 'general_debate':
            continue
        aid = sha(row['slug'].encode())[:12]
        data = (source_dir / (aid + '.json')).read_bytes()
        assert sha(data) == hashes['raw/' + aid + '.json'], 'Historical source hash mismatch'
        doc = json.loads(data)
        assert doc['video']['slug'] == row['slug']
        sources.append(dict(archive_id=aid, sha256=sha(data), slug=row['slug'],
                            url='https://transcripts.un.org' + row['pageUrl'], date=row['date'][:10]))
        for i, s in enumerate(doc['transcript']['data']):
            text = ' '.join(v['text'] for p in s.get('paragraphs', []) for v in p.get('sentences', []))
            segments.append(dict(id=f'{aid}:{i}', source_id=aid, date=row['date'][:10],
                affiliation=(s.get('speaker') or {}).get('affiliation'), speaker=s.get('speaker'),
                text=text, source_url='https://transcripts.un.org' + s['pageUrl'],
                json_pointer=f'/transcript/data/{i}', words=tokens(text)))
    by_id = {s['id']: s for s in segments}
    inverted = collections.defaultdict(set)
    for i, s in enumerate(segments):
        s['grams'] = grams(s['words'])
        for gram in s['grams']:
            inverted[gram].add(i)
    rows, uploads, diffs = [], [], []
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None, 'Archive CRC failure'
        for name in sorted(z.namelist()):
            if not name.lower().endswith('.docx'):
                continue
            raw = z.read(name)
            with zipfile.ZipFile(io.BytesIO(raw)) as docx:
                doc = ET.fromstring(docx.read('word/document.xml'))
                assert not doc.findall('.//w:del', NS), 'Tracked deletions require review'
            ps = [''.join(t.text or '' for t in p.findall('.//w:t', NS))
                  for p in doc.findall('.//w:body//w:p', NS)]
            markers = [i for i, p in enumerate(ps) if p.strip() == 'Full Speech Text']
            assert len(markers) == 1, f'Missing/ambiguous speech boundary: {name}'
            idx = markers[0]
            body = '\n\n'.join(p for p in ps[idx+1:]
                                if 'Access all of our data products' not in p).strip()
            assert body, f'Empty speech: {name}'
            meta = {}
            for p in ps[:idx]:
                for key in ['Date', 'Speaker', 'Region']:
                    if p.startswith(key + ':'):
                        meta[key] = p.split(':', 1)[1].strip()
            date = dt.datetime.strptime(meta['Date'], '%B %d, %Y').date().isoformat()
            label = Path(name).name.split('-UNGA')[0]
            expected = aliases.get(label.casefold())
            assert expected, f'Unresolved country alias: {label}'
            words = tokens(body)
            gs = grams(words)
            hits = collections.Counter(i for g in gs for i in inverted[g])
            assert hits, f'No source text match: {name}'
            candidates = hits.most_common(2)
            best, count = candidates[0]
            s = segments[best]
            assert s['affiliation'] == expected, f'Country mismatch: {name}'
            assert s['date'] == date, f'Date mismatch: {name}'
            assert count / len(gs) > .5, f'Low-overlap match: {name}'
            assert len(candidates) == 1 or count > candidates[1][1] * 2, 'Ambiguous source match'
            variant_id = expected + '-' + sha(raw)[:10]
            (output/'variants'/(variant_id+'.txt')).write_text(body, encoding='utf-8')
            matcher = difflib.SequenceMatcher(None, s['words'], words, autojunk=False)
            changes = []
            for tag, i, j, k, l in matcher.get_opcodes():
                if tag != 'equal':
                    changes.append(dict(operation=tag, source_token_start=i, source_token_end=j,
                        variant_token_start=k, variant_token_end=l,
                        source_tokens=s['words'][i:j], variant_tokens=words[k:l]))
            write_json(output/'diffs'/(variant_id+'.json'), changes)
            row = dict(filename=name, entity_id=expected, entity=label,
                entity_type='member_state' if expected not in ['VAT','PSE','EU','UN'] else
                    {'VAT':'observer_state','PSE':'observer_state','EU':'regional_organization','UN':'secretary_general'}[expected],
                date=date, speaker=meta['Speaker'], source_segment=s['id'],
                upload_sha256=sha(raw), extracted_text_sha256=sha(body.encode()),
                source_word_count=len(s['words']), upload_word_count=len(words),
                exact_text_equal=body==s['text'], normalized_token_equal=words==s['words'],
                token_similarity=round(matcher.ratio(),6),
                upload_fivegram_overlap=round(count/len(gs),6),
                source_fivegram_overlap=round(count/len(s['grams']),6),
                changed_token_blocks=len(changes),
                source_url=s['source_url'], variant_file='variants/'+variant_id+'.txt',
                diff_file='diffs/'+variant_id+'.json',
                decision='retain_source_and_archive_variant')
            rows.append(row)
            uploads.append(dict(variant_id=variant_id, filename=name, metadata=meta,
                editorial_material='\n\n'.join(ps[:idx]), text=body, source_segment=s['id']))
    matched = {r['source_segment'] for r in rows}
    canonical, others = [], []
    for sid in sorted(matched):
        s = by_id[sid]
        variants = [r for r in rows if r['source_segment']==sid]
        parts = [s]
        # Egypt's adjacent same-speaker continuation is part of the address.
        aid, index = sid.split(':')
        next_segment = by_id.get(f'{aid}:{int(index)+1}')
        if next_segment and next_segment['affiliation']==s['affiliation'] and next_segment['speaker']==s['speaker']:
            assert next_segment['id'] not in matched, 'Continuation also matched separately'
            parts.append(next_segment)
        text = '\n\n'.join(p['text'] for p in parts)
        identifier = 'gd-' + s['date'] + '-' + s['affiliation']
        (output/'canonical'/(identifier+'.txt')).write_text(text,encoding='utf-8')
        reg = by_iso.get(s['affiliation'], {})
        canonical.append(dict(statement_id=identifier, country=reg.get('country',variants[0]['entity']),
            country_id=s['affiliation'],region=reg.get('region','Unmapped'),
            speaker=variants[0]['speaker'],speech_date=s['date'],language='en',text=text,
            source_url=s['source_url'],declared_status='available',
            entity_type=variants[0]['entity_type'], source_segments=[p['id'] for p in parts],
            source_text_sha256=sha(text.encode()), upload_variants=[r['filename'] for r in variants],
            provenance='Existing hash-verified automatic transcript; not an official verbatim record',
            speaker_name_provenance='User document metadata; not independently verified'))
    consumed={sid for r in canonical for sid in r['source_segments']}
    for s in segments:
        if s['id'] in consumed:
            continue
        kind='procedural' if s['affiliation']=='GA' else 'unattributed' if not s['affiliation'] else 'other_intervention'
        if s['id']=='223b59cb43db:7': kind='video_introduction'
        elif s['id']=='ba152bf94143:9':kind='language_switch_fragment'
        elif s['affiliation'] and s['affiliation']!='GA':kind='reply'
        others.append(dict(source_segment=s['id'],affiliation=s['affiliation'],date=s['date'],
            classification=kind,words=len(s['words']),source_url=s['source_url'],text=s['text']))
    # Keep the Shiny contract distinct from extended provenance fields.
    fields=['statement_id','country','country_id','region','speaker','speech_date','language','text','source_url','declared_status']
    write_csv(output/'shiny.csv',[{k:r[k] for k in fields} for r in canonical])
    write_csv(output/'national.csv',[{k:r[k] for k in fields} for r in canonical
                                      if r['entity_type']=='member_state'])
    write_csv(output/'comparison.csv',rows)
    write_csv(output/'other-segments.csv',[{k:v for k,v in r.items() if k!='text'} for r in others])
    write_json(output/'other-segments.json',others)
    write_json(output/'canonical.json',canonical)
    write_json(output/'variants.json',uploads)
    write_json(output/'sources.json',sources)
    summary=dict(upload_files=len(rows),unique_addresses=len(canonical),
        entity_types=dict(collections.Counter(r['entity_type'] for r in canonical)),
        new_addresses=0,duplicate_address_variants=len(rows)-len(canonical),
        exact_text_matches=sum(r['exact_text_equal'] for r in rows),
        normalized_token_matches=sum(r['normalized_token_equal'] for r in rows),
        changed_token_variants=sum(not r['normalized_token_equal'] for r in rows),
        low_fivegram_overlap_under_80_percent=sum(r['upload_fivegram_overlap']<.8 for r in rows),
        source_meetings=len(sources),source_segments=len(segments),
        canonical_source_segments=len(consumed),other_source_segments=len(others),
        other_classifications=dict(collections.Counter(r['classification'] for r in others)),
        all_country_and_date_matches=True,all_source_hashes_match=True,
        archive_sha256=sha(archive.read_bytes()))
    assert len(canonical)==len({r['statement_id'] for r in canonical})
    assert len(consumed)+len(others)==len(segments)
    assert all(r['text'].strip() for r in canonical)
    assert len(rows)==len(uploads)
    write_json(output/'validation.json',summary)
    write_json(output/'SHA256.json',{p.relative_to(output).as_posix():sha(p.read_bytes())
        for p in sorted(output.rglob('*')) if p.is_file() and p.name!='SHA256.json'})
    print(json.dumps(summary,indent=2))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('source_dir',type=Path,help='Directory containing original hashed raw JSON files')
    parser.add_argument('output',type=Path)
    parser.add_argument('--repo',type=Path,default=Path('.'))
    args=parser.parse_args()
    run(args.archive,args.source_dir,args.output,args.repo)
