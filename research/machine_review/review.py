#!/usr/bin/env python3
"""Provisional machine review, never a human approval. Offline; stdlib only."""
from __future__ import annotations
import argparse, collections, csv, hashlib, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = 'machine-boundary-1.0.0'
SCHEMA = 'un.corpus-machine-review.v1'
PRESIDING = {'chair', 'vice-chair', 'vice-president', 'president', 'pga',
             'minister of justice; president', 'chairperson of committee ii',
             'chair of the credentials committee', 'chair of committee i', 'moderator'}
PROCESS = re.compile(r'(?i)\b(?:give|giving|gives|hand|handing|pass|passing|yield|yielding)\b.{0,45}\b(?:floor|microphone)\b|\byou have the floor\b|\b(?:meeting|session) (?:is |stands |will be )?(?:adjourned|suspended|called to order)\b|\blist of speakers\b|\bit is so decided\b|\bi see no objection\b|\b(?:take|taking) (?:it|that) that\b|\brules? of procedure\b|\b(?:draft|adopt(?:ion|ed)?) (?:report|programme of work)\b')
REPLY = re.compile(r'(?i)\b(?:i |we |my delegation ).{0,85}\b(?:right of reply|in reply|in response to (?:the |certain |some )?(?:statement|delegation))\b|\b(?:exercise|exercising) (?:my|our|its|the) right of reply\b')
ASR = re.compile(r'(?i)\[(?:inaudible|unintelligible|unrecognized|audio missing)[^\]]*\]|\b(?:audio is not available|interpretation (?:is )?not available)\b')
FORMAL_OPEN = re.compile(r'(?i)^(?:thank you|i thank|mr\.?|madam|madame|mister|excellenc|distinguished|dear|good (?:morning|afternoon)|on behalf|president|chair|vice.president|shukran|merci|gracias)')
TYPES = {'procedure', 'mixed_speech_procedure', 'right_of_reply', 'substantive_speech',
         'speech_fragment', 'uncertain', 'press_question', 'suspected_transcription_issue'}

def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def dump(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def read_verified(path: Path) -> dict:
    """Use the project's unchanged validator: rederive all text from cached bytes."""
    contract = Path(__file__).resolve().parents[1] / 'corpus' / 'contract.cjs'
    script = "const fs=require('node:fs'),C=require(process.argv[1]); const c=C.load(JSON.parse(fs.readFileSync(process.argv[2],'utf8'))); console.log(c.sha256);"
    expected = subprocess.check_output(['node', '-e', script, str(contract), str(path.resolve())], text=True).strip()
    corpus = json.loads(path.read_text(encoding='utf-8'))
    if corpus['sha256'] != expected:
        raise ValueError('Source re-derivation mismatch')
    if any(r['split'] != 'development' for r in corpus['parents']):
        raise ValueError('Only frozen development sources may be reviewed')
    if any(c.get('confirmed') for c in (corpus.get('boundary_review') or {}).get('choices', [])):
        raise ValueError('Preserve existing human choices; this runner requires the untouched development baseline')
    return corpus

def role(r: dict) -> str:
    fn = (r['speaker_metadata'].get('function') or '').lower()
    if fn == 'journalist':
        return 'journalist'
    if fn in PRESIDING:
        return 'presiding_or_moderating'
    if r['genre'] == 'Press Conferences':
        return 'official_press_response' if fn or r.get('affiliation_raw') else 'unresolved_press_role'
    if fn in {'rapporteur', 'secretary', 'secretariat'}:
        return 'recorded_official_role'
    if r.get('country'):
        return 'country_delegation'
    if r.get('affiliation_raw'):
        return 'other_recorded_affiliation'
    if fn:
        return 'recorded_official_role'
    return 'unresolved_affiliation'

def classify(r: dict, previous: dict | None, following: dict | None) -> dict:
    text = r['text']; words = len(text.split()); actor = role(r)
    process = list(PROCESS.finditer(text)); reply = REPLY.search(text); asr = ASR.search(text)
    fn = (r['speaker_metadata'].get('function') or '').lower()
    flags = []
    if not r.get('country'):
        flags.append('country_not_mapped_to_recorded_affiliation' if r.get('affiliation_raw') or fn else 'affiliation_unresolved')
    if actor == 'presiding_or_moderating' and r.get('country'):
        flags.append('country_metadata_not_national_policy_voice')
    if r.get('timestamps_flagged'):
        flags.append('source_timestamps_flagged')
    if words and not FORMAL_OPEN.search(text.strip()):
        flags.append('opening_not_established')
    if text.strip() and text.rstrip()[-1] not in '.!?。！？”’"\'':
        flags.append('possible_truncated_ending')
    if words >= 4 and text.strip().endswith((' I.', ' the.', ' and.', ' to.')):
        flags.append('possible_truncated_ending')
    if previous and previous['speaker_metadata'] == r['speaker_metadata'] and (r.get('affiliation_raw') or fn):
        flags.append('adjacent_same_metadata_not_automatically_same_speech')
    if following and following['speaker_metadata'] == r['speaker_metadata'] and (r.get('affiliation_raw') or fn):
        flags.append('adjacent_same_metadata_not_automatically_same_speech')
    if actor == 'journalist':
        kind, reason = 'press_question', 'Recorded journalist role; do not attribute the question to a state or responding official.'
    elif asr:
        kind, reason = 'suspected_transcription_issue', 'Explicit missing/unclear audio marker; no attempted wording repair.'
    elif actor == 'presiding_or_moderating' and process and words < 12:
        kind, reason = 'procedure', 'Short recorded presiding turn with an explicit floor-management cue.'
    elif words < 12:
        kind, reason = 'uncertain', 'Very short source turn; insufficient standalone context for a speech boundary.'
    elif actor == 'presiding_or_moderating':
        if words <= 180:
            kind, reason = 'procedure', 'Recorded presiding/moderating role and short turn; provisional procedural classification.'
        else:
            kind, reason = 'mixed_speech_procedure', 'Long presiding/moderating turn may combine thematic remarks and meeting administration.'
    elif re.search(r'(?i)\b(?:raise|raising|raised) (?:a |the )?point of order\b', text):
        kind, reason = 'mixed_speech_procedure', 'Explicit point of order may combine procedural objection with substantive position.'
    elif reply:
        kind, reason = 'right_of_reply', 'Explicit first-person reply language; proposed type, not a finding about the dispute.'
    elif len(process) >= 2 or (process and words <= 180):
        kind, reason = 'mixed_speech_procedure', 'Floor-management or procedural language inside a non-presiding source; possible mixed attribution.'
    elif words >= 80:
        kind, reason = 'substantive_speech', 'Extended non-presiding source turn; substantive candidate only, not a verified complete speech.'
    elif words >= 12:
        kind, reason = 'speech_fragment', 'Short non-presiding turn; retain for inclusive sensitivity, with extent unresolved.'
    else:
        kind, reason = 'uncertain', 'Insufficient source evidence.'
    if actor in {'official_press_response', 'unresolved_press_role', 'journalist'}:
        flags.append('press_genre_separate_from_formal_statements')
    if process:
        flags.append('procedural_language_present')
    if asr:
        flags.append('explicit_audio_issue_marker')
    evidence = []
    for cue, match in [('procedural_cue', process[0] if process else None), ('reply_cue', reply), ('audio_cue', asr)]:
        if match:
            evidence.append({'cue': cue, 'start': match.start(), 'end': match.end(), 'quote': text[match.start():match.end()]})
    return {'id': r['id'], 'text_sha256': r['text_sha256'], 'raw_sha256': r['raw_sha256'],
            'meeting_id': r['meeting_id'], 'source_url': r['source_url'], 'json_pointer': r['json_pointer'],
            'actor_kind': 'machine', 'annotation_method': 'deterministic_full_text_rules',
            'status': 'provisional', 'human_confirmed': False, 'suggested_type': kind,
            'actor_role': actor, 'extent': 'unknown', 'speech_id': None,
            'reason': reason, 'flags': sorted(set(flags)), 'evidence': evidence,
            'word_count': words, 'rule_confidence': 'uncalibrated_not_probability',
            'previous_id': previous['id'] if previous else None, 'next_id': following['id'] if following else None}

def validate_ledger(corpus: dict, ledger: dict) -> None:
    if any(r.get('split') != 'development' for r in corpus['parents']):
        raise ValueError('Held-out or undeclared source split is prohibited')
    if ledger.get('schema') != SCHEMA or ledger.get('source_bundle_sha256') != corpus['source_bundle']['sha256'] or ledger.get('corpus_sha256') != corpus['sha256']:
        raise ValueError('Machine review schema/source binding mismatch')
    source = {r['id']: r for r in corpus['parents']}
    rows = ledger.get('annotations', [])
    if len(rows) != len(source) or len({r['id'] for r in rows}) != len(source):
        raise ValueError('Account for every source exactly once')
    for a in rows:
        r = source.get(a['id'])
        if not r or any(a[k] != r[k] for k in ['text_sha256','raw_sha256','meeting_id','source_url','json_pointer']):
            raise ValueError('Annotation source identity mismatch')
        if a['actor_kind'] != 'machine' or a['status'] != 'provisional' or a['human_confirmed'] is not False or a['speech_id'] is not None or a['extent'] != 'unknown':
            raise ValueError('Machine annotations cannot create human approval or complete-speech denominators')
        if a['suggested_type'] not in TYPES:
            raise ValueError('Unknown annotation type')
        for e in a['evidence']:
            if not 0 <= e['start'] < e['end'] <= len(r['text']) or r['text'][e['start']:e['end']] != e['quote']:
                raise ValueError('Evidence quote does not match exact original text')
        for key in ['previous_id', 'next_id']:
            if a[key] and (a[key] not in source or source[a[key]]['meeting_id'] != r['meeting_id']):
                raise ValueError('Context must not cross meetings')

def selections(corpus: dict, ledger: dict) -> list[dict]:
    validate_ledger(corpus, ledger)
    ann = {a['id']: a for a in ledger['annotations']}
    rows = []
    for p in corpus['passages']:
        a = ann[p['parent_id']]; excluded = list(p['exclusions'])
        strict = excluded + ([] if a['suggested_type'] in {'substantive_speech', 'right_of_reply'} else ['machine_type_' + a['suggested_type']])
        if a['actor_role'] in {'presiding_or_moderating', 'journalist', 'official_press_response', 'unresolved_press_role'}:
            strict.append('role_not_formal_substantive_turn')
        if 'possible_truncated_ending' in a['flags']:
            strict.append('possible_truncated_source')
        broad = excluded + (['machine_type_' + a['suggested_type']] if a['suggested_type'] in {'procedure', 'uncertain', 'suspected_transcription_issue', 'press_question'} else [])
        rows.append({**p, 'machine_type': a['suggested_type'], 'machine_actor_role': a['actor_role'],
                     'machine_flags': a['flags'], 'human_confirmed': False, 'machine_status': 'provisional',
                     'strict_exclusions': strict, 'inclusive_exclusions': broad,
                     'strict_eligible': not strict, 'inclusive_eligible': not broad,
                     'baseline_eligible': not excluded})
    return rows

def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open('x', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for row in rows:
            vals = {}
            for key in fields:
                v = row.get(key)
                if isinstance(v, (list, dict)):
                    v = json.dumps(v, ensure_ascii=False)
                if isinstance(v, str) and v[:1] in '=+-@':
                    v = "'" + v  # Spreadsheet-formula injection protection.
                vals[key] = v
            w.writerow(vals)

def execute(corpus_path: Path, out: Path, overrides_path: Path | None = None) -> dict:
    corpus = read_verified(corpus_path)
    if out.exists():
        raise FileExistsError('Output exists; use a new directory to preserve prior results')
    groups = collections.defaultdict(list)
    for r in corpus['parents']:
        groups[r['meeting_id']].append(r)
    annotations = []
    for rs in groups.values():
        for i, r in enumerate(rs):
            annotations.append(classify(r, rs[i-1] if i else None, rs[i+1] if i+1 < len(rs) else None))
    lookup = {a['id']: a for a in annotations}
    overrides = json.loads(overrides_path.read_text()) if overrides_path else {'overrides': []}
    if len({o['id'] for o in overrides['overrides']}) != len(overrides['overrides']):
        raise ValueError('Duplicate contextual override')
    for o in overrides['overrides']:
        a = lookup[o['id']]
        if a['text_sha256'] != o['text_sha256'] or o['suggested_type'] not in TYPES or not o['reason']:
            raise ValueError('Invalid source-bound contextual override')
        a.update(suggested_type=o['suggested_type'], reason=o['reason'], annotation_method='assistant_contextual_override', baseline_rule_type=a['suggested_type'])
        a['flags'] = sorted(set(a['flags'] + ['contextual_machine_check']))
    ledger = {'schema': SCHEMA, 'engine': VERSION, 'created_at': datetime.now(timezone.utc).isoformat(),
              'actor_kind': 'machine', 'authorization': 'Owner requested automated batch review on 2026-10-07; human adjudication deferred.',
              'corpus_sha256': corpus['sha256'], 'source_bundle_sha256': corpus['source_bundle']['sha256'],
              'frame_sha256': corpus['frame']['sha256'], 'source_file_sha256': digest(corpus_path.read_bytes()),
              'implementation_sha256': digest(Path(__file__).read_bytes()),
              'override_file_sha256': digest(overrides_path.read_bytes()) if overrides_path else None,
              'holdout_access': 'none', 'human_confirmations': 0, 'annotations': annotations}
    rows = selections(corpus, ledger)
    out.mkdir(parents=True)
    dump(out/'machine-review.json', ledger)
    dump(out/'provisional-corpus.json', {'schema': 'un.provisional-passage-corpus.v1', 'source_corpus_sha256': corpus['sha256'],
          'machine_review_sha256': digest((out/'machine-review.json').read_bytes()), 'population_status': 'machine_only_not_human_reviewed',
          'frame_sha256': corpus['frame']['sha256'], 'holdout_transcripts_opened': 0, 'human_confirmations': 0,
          'meetings': [m for m in corpus['frame']['meetings'] if m['split']=='development'], 'records': rows})
    write_csv(out/'machine-review.csv', annotations, ['id','meeting_id','suggested_type','actor_role','annotation_method','word_count','extent','human_confirmed','reason','flags','evidence','source_url','json_pointer','text_sha256'])
    write_csv(out/'passage-selection.csv', rows, ['id','parent_id','meeting_id','country','machine_actor_role','machine_type','strict_eligible','inclusive_eligible','baseline_eligible','strict_exclusions','inclusive_exclusions','parent_start','parent_end','text_sha256','source_url'])
    # Every source is retained for later adjudication; priority is not a sampling filter.
    queue = sorted(annotations, key=lambda a: (0 if a['suggested_type'] in {'uncertain','mixed_speech_procedure','suspected_transcription_issue'} or 'possible_truncated_ending' in a['flags'] else 1, a['meeting_id'], int(a['id'].rsplit('#',1)[1])))
    write_csv(out/'adjudication-queue.csv', queue, ['id','suggested_type','actor_role','reason','flags','source_url','text_sha256'])
    receipt = {'schema':'un.machine-review-validation.v1','engine':VERSION,'status':'PASS','sources':len(annotations),'passages':len(rows),
               'types':dict(collections.Counter(a['suggested_type'] for a in annotations)), 'roles':dict(collections.Counter(a['actor_role'] for a in annotations)),
               'strict_passages':sum(p['strict_eligible'] for p in rows),'inclusive_passages':sum(p['inclusive_eligible'] for p in rows),
               'baseline_passages':sum(p['baseline_eligible'] for p in rows),'contextual_overrides':len(overrides['overrides']),
               'holdout_transcripts_opened':0,'human_confirmations':0,'reviewed_speech_eligible':corpus['counts']['reviewed_speech_eligible'],
               'source_corpus_sha256':corpus['sha256'],'all_sources_accounted':True,'all_original_partitions_retained':True,
               'no_new_source_requests':True,'limitations':['Rule-assisted triage, not independent human validation','No audio checking or automatic transcription repair','Speech extent remains unknown','Country metadata is not a national policy voice when a chair is speaking']}
    dump(out/'review-validation.json', receipt)
    return receipt

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('corpus',type=Path);p.add_argument('output',type=Path);p.add_argument('--overrides',type=Path)
    args=p.parse_args()
    try:
        print(json.dumps(execute(args.corpus,args.output,args.overrides),indent=2))
    except (ValueError,KeyError,FileExistsError,subprocess.CalledProcessError) as e:
        p.exit(1,str(e)+'\n')
