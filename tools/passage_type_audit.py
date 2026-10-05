"""Provisional source-type screening; originals are read only, decisions are separate.

Long-text candidates are structural screening, not full factual/audio verification.
An imported human decision requires an explicit per-passage choice and provenance.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

TYPES = {
    'substantive_speech': 'Substantive address segment',
    'mixed_speech_procedure': 'Substantive remarks mixed with procedure',
    'right_of_reply': 'Right of reply',
    'procedure': 'Chair, introduction or other procedure',
    'speech_fragment': 'Fragment of a substantive address',
    'suspected_transcription_issue': 'Possible extraneous transcription',
    'uncertain': 'Uncertain or insufficient text',
}
SCHEMA = 'un.passage-type-mask.v1'
STRICT = ['substantive_speech']
INCLUSIVE = STRICT + ['mixed_speech_procedure', 'speech_fragment']
PROCEDURE = re.compile(r'(on behalf of (?:the )?(?:general )?assembly|(?:the )?assembly will|request (?:the )?protocol|i (?:now )?(?:call|give)|i (?:would )?(?:wish|like) to thank|i thank (?:the|his|her)|we thank|take your seats?|exercise of the right of reply has been requested|meeting is (?:now )?(?:adjourned|end)|called to order|have the floor|last speaker|final statement)', re.I)
REPLY = re.compile(r'(right (?:of|to) reply|second intervention in response)', re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_corpus(path):
    raw = Path(path).read_bytes()
    corpus = json.loads(raw.decode('utf-8-sig'))
    if corpus.get('schema') != 'un.browser.corpus.v1' or not isinstance(corpus.get('records'), list):
        raise ValueError('Expected a saved browser corpus')
    ids = set()
    for row in corpus['records']:
        if row['id'] in ids:
            raise ValueError('Duplicate source ID')
        ids.add(row['id'])
        if digest(row['text'].encode('utf-8')) != row['text_sha256']:
            raise ValueError('Original text hash mismatch: ' + row['id'])
        if not row['source_url'].startswith('https://'):
            raise ValueError('Invalid source URL')
    return corpus, digest(raw)


def propose(records):
    result = []
    reply_context = {}
    for row in records:
        text = row['text']; words = len(text.split()); asset = row['id'].split('#')[0]
        chair = row['country'] == 'GA'
        # Chair context and content are both required; the affiliation alone is insufficient.
        if chair and re.search(r'(called to order|continue (?:its consideration|the general debate))', text, re.I):
            reply_context.pop(asset, None)
        if chair and re.search(r'(exercise of the right of reply|exercise of reply)', text, re.I):
            reply_context[asset] = row['id']
        if re.search(r'(play all songs|play from the khan)', text, re.I):
            kind, reason = 'suspected_transcription_issue', 'Unrelated song/show playback wording; audio has not been verified. Preserve the source.'
        elif words > 500 and (chair or re.search(r'(on behalf of the assembly|assembly will (?:now )?(?:hear|listen|turn)|request (?:the )?protocol)', text[:350], re.I)):
            kind, reason = 'mixed_speech_procedure', 'Substantive address content shares a source segment with chair/protocol wording. Do not trim automatically.'
        elif not chair and (REPLY.search(text[:450]) or asset in reply_context):
            kind, reason = 'right_of_reply', 'Reply wording and/or preceding chair announcement establishes the intervention context.'
        elif words < 250 and PROCEDURE.search(text):
            kind, reason = 'procedure', 'Short source segment contains floor management, introduction, thanks or meeting procedure.'
        elif words >= 500:
            kind, reason = 'substantive_speech', 'Long address candidate outside reply context; structural text inspection is required, not just a length threshold.'
        else:
            kind, reason = 'uncertain', 'Insufficient structural evidence for an automatic source-type candidate.'
        result.append({**{key: row[key] for key in ['id', 'text_sha256', 'source_url', 'date', 'country', 'region']},
                       'words': words, 'proposed_type': kind, 'reason': reason,
                       'inspection': 'rule_screen', 'context_id': reply_context.get(asset),
                       'confirmed_type': None, 'reviewer': None, 'reviewed_at': None})
    return result


def apply_inspections(rows, inspections):
    by_id = {r['id']: r for r in rows}
    seen = set()
    for checked in inspections:
        if checked['id'] in seen or checked['id'] not in by_id:
            raise ValueError('Duplicate or unknown inspection ID')
        seen.add(checked['id']); row = by_id[checked['id']]
        if checked['text_sha256'] != row['text_sha256']:
            raise ValueError('Inspection text hash mismatch')
        if checked['type'] not in TYPES or checked['scope'] not in ['full_short_text', 'structural_windows', 'boundary_context']:
            raise ValueError('Invalid inspection')
        row.update(proposed_type=checked['type'], reason=checked['reason'], inspection=checked['scope'])


def validate_mask(corpus, corpus_sha, mask):
    if mask.get('schema') != SCHEMA or mask.get('corpus_sha256') != corpus_sha:
        raise ValueError('Mask does not match original corpus bytes')
    original = {r['id']: r for r in corpus['records']}
    rows = mask.get('rows', [])
    if len(rows) != len(original) or {r['id'] for r in rows} != set(original):
        raise ValueError('Mask must contain each original ID exactly once')
    for row in rows:
        source = original[row['id']]
        if row['text_sha256'] != source['text_sha256']:
            raise ValueError('Mask text hash mismatch')
        if row['proposed_type'] not in TYPES:
            raise ValueError('Invalid proposed type')
        if row.get('confirmed_type') is not None:
            if row['confirmed_type'] not in TYPES or not isinstance(row.get('reviewer'), str) or not row['reviewer'].strip():
                raise ValueError('Invalid reviewer decision')
            stamp = dt.datetime.fromisoformat(row.get('reviewed_at', '').replace('Z', '+00:00'))
            if stamp.tzinfo is None or stamp > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5):
                raise ValueError('Invalid review timestamp')
    return rows


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepare(corpus_path, output, inspections=None, analysis=None, subset_analysis=None):
    corpus, corpus_sha = load_corpus(corpus_path)
    rows = propose(corpus['records'])
    if inspections:
        annotations = json.loads(Path(inspections).read_text(encoding='utf-8'))
        if annotations['corpus_sha256'] != corpus_sha:
            raise ValueError('Inspection corpus hash mismatch')
        apply_inspections(rows, annotations['rows'])
    mask = {'schema': SCHEMA, 'corpus_sha256': corpus_sha, 'status': 'provisional',
            'provenance': 'Assistant-assisted source-type screening; no human confirmation or audio verification.',
            'types': TYPES, 'strict_types': STRICT, 'inclusive_types': INCLUSIVE, 'rows': rows}
    validate_mask(corpus, corpus_sha, mask)
    out = Path(output)
    if Path(corpus_path).resolve() in [(out/name).resolve() for name in ['mask.json', 'review.html']]:
        raise ValueError('Output would overwrite the original corpus')
    noise = {}
    for prefix, filename in [('', analysis), ('substantive_', subset_analysis)]:
        if not filename:
            continue
        fit = json.loads(Path(filename).read_text(encoding='utf-8'))['methods']['clusters']
        originals = {r['id']: r for r in corpus['records']}
        for f in [fit, fit['comparison']['alternative']]:
            if f.get('algorithm') != 'hdbscan':
                raise ValueError('Unassigned review priority requires HDBSCAN results')
            for point in f['points']:
                if point['id'] not in originals or point['text_sha256'] != originals[point['id']]['text_sha256']:
                    raise ValueError('Analysis source does not match original text')
                noise.setdefault(point['id'], {})[prefix + f['representation']] = point['cluster']
    payload = {'mask': mask, 'records': corpus['records'], 'assignments': noise}
    template = Path(__file__).with_name('passage_type_review.html').read_text(encoding='utf-8')
    packed = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    out.mkdir(parents=True, exist_ok=True)
    write(out/'mask.json', mask)
    (out/'review.html').write_text(template.replace('__PACKET_JSON__', packed), encoding='utf-8')
    return {'records': len(rows), 'types': dict(collections.Counter(r['proposed_type'] for r in rows)),
            'human_confirmed': 0, 'strict_count': sum(r['proposed_type'] in STRICT for r in rows),
            'inclusive_count': sum(r['proposed_type'] in INCLUSIVE for r in rows), 'original_sha256': corpus_sha}


def import_review(corpus_path, mask_path, review_path, output):
    if Path(output).resolve() in [Path(p).resolve() for p in [corpus_path, mask_path, review_path]]:
        raise ValueError('Write an imported mask to a separate file; preserve input evidence')
    corpus, sha = load_corpus(corpus_path); mask = json.loads(Path(mask_path).read_text(encoding='utf-8'))
    validate_mask(corpus, sha, mask)
    incoming = json.loads(Path(review_path).read_text(encoding='utf-8-sig'))
    if incoming.get('schema') != 'un.passage-type-review.v1' or incoming.get('corpus_sha256') != sha:
        raise ValueError('Review does not match the corpus')
    rows = {r['id']: r for r in mask['rows']}; seen = set()
    for choice in incoming.get('choices', []):
        key = choice['id']
        if key not in rows or key in seen or choice['text_sha256'] != rows[key]['text_sha256']:
            raise ValueError('Duplicate, changed or unknown review choice')
        seen.add(key)
        if choice.get('confirmed') is not True or choice.get('type') not in TYPES:
            raise ValueError('Explicit decision missing')
        rows[key].update(confirmed_type=choice['type'], reviewer=choice.get('reviewer'), reviewed_at=choice.get('reviewed_at'), review_note=choice.get('note', '')[:1200])
    validate_mask(corpus, sha, mask)
    mask['status'] = 'human_confirmed' if all(r['confirmed_type'] is not None for r in rows.values()) else 'partially_confirmed'
    mask.setdefault('proposal_provenance', mask['provenance'])
    mask['provenance'] = 'Initial assistant-assisted suggestions with explicit reviewer-declared decisions recorded separately; no audio verification is inferred.'
    mask['review_file_sha256'] = digest(Path(review_path).read_bytes())
    mask['identity_note'] = 'Reviewer-declared identity; not authenticated. No training or daily publication is triggered.'
    write(output, mask)
    return {'status': mask['status'], 'confirmed': sum(r['confirmed_type'] is not None for r in rows.values())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('corpus'); p.add_argument('output'); p.add_argument('--inspections'); p.add_argument('--analysis'); p.add_argument('--subset-analysis')
    p = sub.add_parser('import'); p.add_argument('corpus'); p.add_argument('mask'); p.add_argument('review'); p.add_argument('output')
    args = parser.parse_args()
    print(json.dumps(prepare(args.corpus, args.output, args.inspections, args.analysis, args.subset_analysis) if args.command == 'prepare' else import_review(args.corpus, args.mask, args.review, args.output), indent=2))
