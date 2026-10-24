"""Read-only, source-verified topic relevance candidates, never policy positions."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

VERSION='sc-policy-candidates-1'


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()


def _sha(value):
    return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None


def _official(value):
    if not isinstance(value,str): return False
    try:
        u=urlparse(value)
        return u.scheme=='https' and (u.hostname=='un.org' or (u.hostname or '').endswith('.un.org')) and not u.username and not u.password
    except ValueError: return False


def _unalias(path):
    for p in (path,*path.parents):
        if p.is_symlink() or getattr(p,'is_junction',lambda:False)(): raise ValueError('Document proof aliases are not allowed')


def build_candidates(selection_report,bindings,document_receipts,document_root):
    """Return a separate provisional relevance packet without changing actions."""
    from .sc_crosswalk import normalize_resolution,_date
    from .sc_event_selection import VERSION as selection_version
    s=selection_report
    if not isinstance(s,dict) or s.get('schema')!='un.sc-event-selection.v1' or s.get('version')!=selection_version or not isinstance(s.get('events'),list) or len(s['events'])>10000 or not isinstance(s.get('withheld'),list): raise ValueError('Invalid selected-action report')
    events=s['events'];summary=s.get('summary',{})
    if any(not isinstance(e,dict) or e.get('status') not in ('matched_adopted','ddl_only_adopted','dppa_only_adopted','failed_draft') for e in events): raise ValueError('Invalid selected action shape or status')
    statuses={status:sum(e.get('status')==status for e in events) for status in sorted({e.get('status') for e in events})}
    if summary.get('selected_actions')!=len(events) or summary.get('statuses')!=statuses or summary.get('withheld_groups')!=len(s['withheld']) or summary.get('political_scores_computed') is not False: raise ValueError('Incoherent selected-action summary')
    fingerprints=s.get('input_fingerprints',{})
    if set(fingerprints)!={'collection_sha256','ddl_votes_sha256'} or not all(_sha(v) for v in fingerprints.values()): raise ValueError('Missing selected-action input fingerprints')
    seen=set();by_resolution={}
    for e in events:
        aid=e.get('action_id')
        if not isinstance(aid,str) or not aid or aid in seen or e.get('issue_binding')!='unbound' or e.get('comparisons_eligible') is not False: raise ValueError('Bound, comparable or duplicate selected action')
        seen.add(aid)
        n=normalize_resolution(e.get('resolution'))
        if e.get('status')!='failed_draft' and (not n or n!=e.get('resolution') or aid!='sc:adopted:'+n or not _date(e.get('date')) or e['date'][:4]!=n[-5:-1]): raise ValueError('Incoherent selected adopted identity')
        if e.get('status')=='matched_adopted':
            rows=e.get('representative_ballots')
            if e.get('representative_source')!='ddl' or not isinstance(rows,list) or len(rows)!=15 or len({r.get('country_code') for r in rows})!=15 or any(normalize_resolution(r.get('resolution'))!=n or r.get('date')!=e['date'] or r.get('resolution_version')!='as_adopted' or r.get('stage')!='adopted_resolution' or r.get('policy')!='unbound' for r in rows): raise ValueError('Selected DDL action stage, version or policy mismatch')
        if n: by_resolution.setdefault(n,[]).append(e)
    if not isinstance(bindings,list) or len(bindings)>1000 or not isinstance(document_receipts,list) or len(document_receipts)>100: raise ValueError('Candidate input exceeds bounds')
    root=Path(document_root).absolute();_unalias(root);root=root.resolve()
    proofs={};files={}
    for r in document_receipts:
        if not isinstance(r,dict) or not isinstance(r.get('file'),str) or Path(r['file']).is_absolute() or not _official(r.get('url')) or not _sha(r.get('sha256')) or type(r.get('bytes')) is not int or not 0<r['bytes']<=10_000_000: raise ValueError('Invalid document receipt')
        file=root/r['file'];_unalias(file);file=file.resolve()
        if not file.is_relative_to(root) or not file.is_file() or file.stat().st_nlink!=1 or file.stat().st_size!=r['bytes']: raise ValueError('Document proof path or size mismatch')
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        if digest!=r['sha256']: raise ValueError('Document proof hash mismatch')
        key=(r['url'],digest)
        if key in proofs or str(file) in files: raise ValueError('Duplicate document proof identity')
        proofs[key]=r;files[str(file)]=digest
    candidates=[];gaps=[];binding_ids=set();binding_questions=set()
    for b in bindings:
        if not isinstance(b,dict): raise ValueError('Invalid binding')
        n=b.get('resolution_id');bid=b.get('binding_id');question=(n,b.get('policy_id'),b.get('context_id'))
        if not isinstance(bid,str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}',bid) or bid in binding_ids or question in binding_questions: raise ValueError('Duplicate or invalid binding identity')
        binding_ids.add(bid);binding_questions.add(question)
        if not isinstance(n,str) or not re.fullmatch(r'S/RES/[1-9]\d*\(\d{4}\)',n) or normalize_resolution(n)!=n or b.get('resolution_version')!='as_adopted' or b.get('stage')!='adopted_resolution' or b.get('policy_id') not in ('humanitarian_access','civilian_protection') or b.get('context_id')!='thematic_armed_conflict' or b.get('review_state')!='assistant_provisional' or b.get('evidence_kind')!='full_resolution_vote_topic_relevance' or b.get('ontology_version')!='humanitarian-ontology-1': raise ValueError('Unsupported provisional topic binding')
        if not _official(b.get('source_url')) or not _sha(b.get('source_sha256')) or any(not isinstance(b.get(k),str) or not b[k].strip() or len(b[k])>4000 for k in ('source_anchor','rationale')): raise ValueError('Incomplete binding source proof')
        if (b['source_url'],b['source_sha256']) not in proofs: raise ValueError('Binding is not supported by a verified document receipt')
        qualifications=b.get('source_qualifications',[])
        if not isinstance(qualifications,list) or len(qualifications)>20 or any(not isinstance(q,str) or not q.strip() or len(q)>2000 for q in qualifications): raise ValueError('Invalid source qualifications')
        limitation=b.get('limitation','')
        if not isinstance(limitation,str) or len(limitation)>4000: raise ValueError('Invalid binding limitation')
        matches=by_resolution.get(n,[])
        reason='no_selected_adopted_action' if not matches else 'ambiguous_selected_resolution' if len(matches)!=1 else None
        e=matches[0] if len(matches)==1 else None
        if e and (e.get('status')!='matched_adopted' or e.get('representative_source')!='ddl'): reason='selected_action_not_matched_ddl_adopted'
        if e and reason is None:
            rows=e.get('representative_ballots');link=e.get('comparison_evidence',{})
            if not isinstance(rows,list) or len(rows)!=15 or not _date(e.get('date')) or e['date'][:4]!=n[-5:-1] or e['action_id']!='sc:adopted:'+n: raise ValueError('Invalid selected adopted action identity')
            if len({r.get('country_code') for r in rows})!=15 or any(normalize_resolution(r.get('resolution'))!=n or r.get('date')!=e['date'] or r.get('resolution_version')!='as_adopted' or r.get('stage')!='adopted_resolution' or r.get('policy')!='unbound' for r in rows): raise ValueError('Selected DDL action stage, version or policy mismatch')
            if link.get('deduplication_eligible') is not True or link.get('resolution')!=n or link.get('date')!=e['date'] or any(link.get(k) for k in ('reference_conflicts','roster_gaps','conflicting_countries','participation_conflicts')): raise ValueError('Selected action lacks eligible identity evidence')
        if reason:
            gaps.append({'binding_id':bid,'resolution':n,'policy_id':b['policy_id'],'reason':reason});continue
        candidates.append({'binding_id':bid,'action_id':e['action_id'],'date':e['date'],'resolution':n,
                           'resolution_version':'as_adopted','stage':'adopted_resolution','policy_id':b['policy_id'],'context_id':b['context_id'],
                           'source_url':b['source_url'],'source_sha256':b['source_sha256'],'source_anchor':b['source_anchor'],'rationale':b['rationale'],
                           'review_state':'assistant_provisional','evidence_kind':'full_resolution_vote_topic_relevance',
                           'scope':'topic_relevance_only','comparable':False,'comparisons_eligible':False,'issue_agreement':False,
                           'source_qualifications':list(qualifications),'source_limitation':limitation,
                           'limitation':'A full-resolution vote does not establish an explicit position on an isolated clause or exact issue agreement.'})
    # Detect changes to proof bytes during validation without writing anything.
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha for p,sha in files.items()): raise ValueError('Document proof changed during candidate validation')
    candidates.sort(key=lambda r:(r['date'],r['action_id'],r['policy_id'],r['binding_id']));gaps.sort(key=lambda r:r['binding_id'])
    return {'schema':'un.sc-policy-candidates.v1','version':VERSION,'candidates':candidates,'gaps':gaps,
            'summary':{'candidate_rows':len(candidates),'distinct_actions':len({r['action_id'] for r in candidates}),'unmatched_bindings':len(gaps),'comparisons_eligible':0},
            'input_fingerprints':{'selection_sha256':_digest(s),'bindings_sha256':_digest(bindings),'document_receipts_sha256':_digest(document_receipts),
                                  'verified_documents':dict(sorted((r['file'],r['sha256']) for r in document_receipts)),
                                  'method_dependencies':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('sc_crosswalk.py','sc_event_selection.py')},
                                  'method_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            'limitations':['Separate assistant-provisional topic-relevance candidates only.','Source actions, ballots and original binding artifacts remain unchanged.','Repeated policy candidates do not create additional voting actions.']}
