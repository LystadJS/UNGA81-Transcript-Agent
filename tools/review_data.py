"""Local review-workspace templates and strict checks. Never creates gold labels."""
from pathlib import Path
import argparse, csv, datetime as dt, hashlib, json, re

SCHEMAS={
 'sources':'source_id iso3 event_date available_at genre language source_url text_path text_sha256 duplicate_group',
 'passages':'passage_id source_id start end quote',
 'propositions':'proposition_id version target proposition scope',
 'annotations':'annotation_id passage_id task proposition_id label reviewer_id reviewed_at rationale',
 'adjudications':'passage_id task proposition_id final_label adjudicator_id adjudicated_at rationale',
 'splits':'source_id split',
 'history':'source_id issue_id proposition_id representation_id comparable_group observation_index',
 'events':'event_id source_id event_type proposition_id actor receiver action event_time available_at passage_id',
 'risk':'risk_id iso3 proposition_id start stop event_id outcome censor_reason',
 'edges':'edge_id sender receiver layer weight measured_at available_at source_id'
}
LABELS={'issue':{'relevant','not_relevant','insufficient'},'stance':{'support','oppose','conditional','descriptive','insufficient'},'event':{'confirmed','not_confirmed','insufficient'}}

def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);result=[]
        for i,row in enumerate(reader):
            if i>=100000:raise ValueError('Table exceeds 100,000-row review limit')
            if None in row or any(v is None for v in row.values()):raise ValueError(f'Row {i+2} has missing or extra cells')
            result.append(row)
        return reader.fieldnames,result

def write_csv(path,fields,records=()):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(records)

def initialize(root,replay=None):
    root.mkdir(parents=True,exist_ok=False)
    for name,cols in SCHEMAS.items():write_csv(root/(name+'.csv'),cols.split())
    policy={'schema':'un.review.v1','dataset_kind':'unreviewed','validation_scheme':'time_and_country','cutoff':'','human_review_complete':False,
        'note':'Fill after review. Software checks cannot establish reviewer identity, truthful labels, accuracy or authorization.'}
    (root/'bundle.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8')
    if replay:
        speeches=json.loads(replay.read_text(encoding='utf-8'));sources=[];passages=[];(root/'texts').mkdir()
        for i,s in enumerate(speeches,1):
            sid=f's{i:04d}';text=s['text'];raw=text.encode('utf-8');name=f'texts/{sid}.txt';(root/name).write_bytes(raw)
            sources.append(dict(source_id=sid,iso3=s['iso3'],event_date=s['date'],available_at='',genre='general_debate',language='en',source_url=s.get('source_url',s.get('url','')),text_path=name,text_sha256=hashlib.sha256(raw).hexdigest(),duplicate_group=''))
            # Paragraph offsets are Unicode codepoints, zero-based and end-exclusive.
            spans=list(re.finditer(r'[^\n]+(?:\n(?!\n)[^\n]+)*',text))
            j=0
            for m in spans:
                pos=m.start()
                while pos<m.end():
                    while pos<m.end() and text[pos].isspace():pos+=1
                    if pos==m.end():break
                    end=min(pos+1000,m.end())
                    if end<m.end():
                        boundaries=list(re.finditer(r'[.!?]["”’]*\s+',text[pos:end]))
                        cut=boundaries[-1].end() if boundaries else text[pos:end].rfind(' ')
                        if cut>=300:end=pos+cut
                    trimmed=end
                    while trimmed>pos and text[trimmed-1].isspace():trimmed-=1
                    j+=1;passages.append(dict(passage_id=f'{sid}-p{j:03d}',source_id=sid,start=pos,end=trimmed,quote=text[pos:trimmed]));pos=end
        write_csv(root/'sources.csv',SCHEMAS['sources'].split(),sources);write_csv(root/'passages.csv',SCHEMAS['passages'].split(),passages)
    (root/'README.txt').write_text('This is an UNREVIEWED workspace. No labels or availability times are invented.\nOffsets: zero-based Unicode codepoints, end-exclusive, against unchanged UTF-8 text.\nSee docs/DATA_GUIDE.md. Keep this directory out of public Git.\n',encoding='utf-8')

def validate(root,capability='labels'):
    errors=[];warnings=[];tables={};texts={}
    def check(ok,message):
        if not ok:errors.append(message)
        return ok
    def timestamp(value):
        if not value:raise ValueError('Missing timestamp')
        z=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        if z.tzinfo is None:raise ValueError('Timestamp needs timezone')
        return z.astimezone(dt.timezone.utc)
    def instant(value,context):
        try:return timestamp(value)
        except (ValueError,TypeError):check(False,f'{context}: invalid/missing timezone timestamp');return None
    policy=json.loads((root/'bundle.json').read_text(encoding='utf-8'))
    check(policy.get('schema')=='un.review.v1','Unknown schema')
    check(policy.get('dataset_kind')=='real','Only explicitly real data can pass review validation')
    check(policy.get('human_review_complete') is True,'Human review is incomplete')
    single=policy.get('review_mode')=='single_reviewer_pilot'
    if single:warnings.append('Single-reviewer operational pilot: no independent agreement or adjudication is established')
    check(policy.get('review_mode','independent') in ('independent','single_reviewer_pilot'),'Unknown review mode')
    cutoff=instant(policy.get('cutoff'),'bundle cutoff')
    for name,cols in SCHEMAS.items():
        try:
            fields,data=rows(root/(name+'.csv'));valid=check(fields==cols.split(),f'{name}: exact headers/order required');tables[name]=data if valid else []
        except (OSError,ValueError) as e:check(False,f'{name}: {e}');tables[name]=[]
    def index(name,key):
        data=tables[name];ids=[r.get(key,'') for r in data];check(all(ids) and len(ids)==len(set(ids)),f'{name}: missing/duplicate {key}')
        return {r.get(key,''):r for r in data}
    sources=index('sources','source_id');passages=index('passages','passage_id');props=index('propositions','proposition_id')
    check(bool(sources) and bool(passages),'Source and passage tables must be nonempty')
    for sid,s in sources.items():
        check(bool(re.fullmatch('[A-Z]{3}',s.get('iso3',''))),f'{sid}: ISO3 format required')
        try:dt.date.fromisoformat(s['event_date'])
        except (KeyError,ValueError):check(False,f'{sid}: invalid event_date')
        for col in ['genre','language','source_url']:check(bool(s.get(col,'')),f'{sid}: missing {col}')
        avail=instant(s.get('available_at'),sid)
        if avail and cutoff:check(avail<=cutoff,f'{sid}: unavailable at cutoff')
        if avail and s.get('event_date'):check(avail.date().isoformat()>=s['event_date'],f'{sid}: availability precedes event')
        try:
            p=(root/s['text_path']).resolve();p.relative_to(root.resolve());check(not p.is_symlink(),f'{sid}: symlink not allowed')
            raw=p.read_bytes();check(len(raw)<=2_000_000,f'{sid}: text exceeds limit')
            check(hashlib.sha256(raw).hexdigest()==s['text_sha256'],f'{sid}: text hash mismatch');texts[sid]=raw.decode('utf-8')
        except (KeyError,ValueError,OSError,UnicodeError):check(False,f'{sid}: invalid text path/UTF-8')
    for pid,p in passages.items():
        sid=p.get('source_id');check(sid in sources,f'{pid}: missing source')
        try:
            start,end=int(p['start']),int(p['end']);text=texts[sid]
            check(0<=start<end<=len(text) and text[start:end]==p['quote'],f'{pid}: quotation/offset mismatch')
        except (ValueError,KeyError):check(False,f'{pid}: invalid offsets/source')
    for pid,p in props.items():
        for col in ['version','target','proposition','scope']:check(bool(p.get(col)),f'{pid}: missing {col}')
    groups={}
    annotations=index('annotations','annotation_id')
    for aid,a in annotations.items():
        key=(a.get('passage_id'),a.get('task'),a.get('proposition_id'));groups.setdefault(key,[]).append(a)
        check(a.get('passage_id') in passages,f'{aid}: unknown passage');check(a.get('label') in LABELS.get(a.get('task'),set()),f'{aid}: invalid label/task')
        if a.get('task') in ('stance','event'):check(a.get('proposition_id') in props,f'{aid}: named proposition/action definition required')
        check(bool(a.get('reviewer_id')) and bool(a.get('rationale')),f'{aid}: reviewer and rationale required')
        t=instant(a.get('reviewed_at'),aid)
        if t and cutoff:check(t<=cutoff,f'{aid}: review after cutoff')
    final_keys=set()
    for a in tables['adjudications']:
        key=(a.get('passage_id'),a.get('task'),a.get('proposition_id'));check(key not in final_keys,f'{key}: duplicate adjudication');final_keys.add(key)
        reviews=groups.get(key,[]);reviewers=[r.get('reviewer_id') for r in reviews]
        if single:
            check(len(reviewers)==1 and bool(reviewers[0]),f'{key}: exactly one identified pilot reviewer required')
            check(bool(a.get('adjudicator_id')) and a.get('adjudicator_id') in reviewers,f'{key}: pilot finalization must be by the same reviewer')
        else:
            check(len(set(reviewers))>=2 and len(reviewers)==len(set(reviewers)),f'{key}: two independent reviews required; one row per reviewer')
            check(bool(a.get('adjudicator_id')) and a.get('adjudicator_id') not in reviewers,f'{key}: separate adjudicator required')
        check(a.get('final_label') in LABELS.get(a.get('task'),set()),f'{key}: invalid final label')
        check(bool(a.get('rationale')),f'{key}: adjudication rationale required')
        t=instant(a.get('adjudicated_at'),str(key))
        if t and cutoff:check(t<=cutoff,f'{key}: adjudication after cutoff')
        for r in reviews:
            rt=instant(r.get('reviewed_at'),str(key))
            if t and rt:check(t>=rt,f'{key}: adjudication precedes review')
    if capability=='pilot':
        check(bool(final_keys),'No finalized pilot labels')
        check(set(groups)==final_keys,'Every pilot annotation needs finalization')
        check({p['passage_id'] for p in tables['passages']}=={k[0] for k in final_keys},'Every selected pilot passage requires a label')
    if capability in ('labels','stance'):
        check(bool(final_keys),'No adjudicated labels')
        check(set(groups)==final_keys,'Every annotation task needs final adjudication')
        if capability=='stance':check(any(k[1]=='stance' for k in final_keys),'No adjudicated stance tasks')
        split={};by_split={k:[] for k in ('train','calibration','test')};duplicate_splits={}
        for r in tables['splits']:
            sid=r.get('source_id');part=r.get('split');check(sid not in split and sid in sources and part in by_split,f'{sid}: invalid/duplicate split')
            split[sid]=part
            if sid in sources and part in by_split:
                s=sources[sid];by_split[part].append(s)
                for group in [s.get('text_sha256'),s.get('duplicate_group')]:
                    if group:duplicate_splits.setdefault(group,set()).add(part)
        check(all(len(v)==1 for v in duplicate_splits.values()),'Duplicate text/group crosses splits')
        for key in final_keys:
            if key[0] in passages:check(passages[key[0]]['source_id'] in split,f'{key}: reviewed source lacks split')
        check(all(by_split.values()),'Train, calibration and test sets must be nonempty')
        if all(by_split.values()):
            dates={k:[s['event_date'] for s in v] for k,v in by_split.items()}
            check(max(dates['train'])<min(dates['calibration']) and max(dates['calibration'])<min(dates['test']),'Splits must be strictly forward in event time')
            country_sets=[{s['iso3'] for s in by_split[k]} for k in ('train','calibration','test')]
            if policy.get('validation_scheme')=='time_and_country':check(all(not country_sets[i]&country_sets[j] for i in range(3) for j in range(i)),'Countries cross grouped splits')
            elif policy.get('validation_scheme')=='time_only':warnings.append('Time-only evaluation does not establish transfer to unseen countries')
            else:check(False,'Unknown validation scheme')
    if capability=='history':
        check(len(tables['history'])>=2,'At least two historical records required')
        matched={};seen=set()
        for r in tables['history']:
            sid=r.get('source_id');check(sid in sources and sid not in seen,f'{sid}: missing/duplicate history source');seen.add(sid)
            check(bool(r.get('representation_id')) and bool(r.get('comparable_group')),f'{sid}: representation and comparability group required')
            if sid in sources:matched.setdefault(r['comparable_group'],[]).append((r,sources[sid]))
        for group,data in matched.items():
            check(len(data)>=2,f'{group}: no comparison')
            for k in ('iso3','genre','language'):check(len({s[k] for r,s in data})==1,f'{group}: mixed {k}')
            for k in ('issue_id','proposition_id','representation_id'):check(len({r[k] for r,s in data})==1,f'{group}: mixed {k}')
            try:
                ordered=sorted(data,key=lambda z:int(z[0]['observation_index']));ix=[int(r['observation_index']) for r,s in ordered];dates=[s['event_date'] for r,s in ordered]
                check(len(ix)==len(set(ix)) and dates==sorted(dates) and len(set(dates))==len(dates),f'{group}: invalid observation ordering')
            except ValueError:check(False,f'{group}: observation_index must be integer')
    if capability in ('diffusion','events'):
        events=index('events','event_id');check(bool(events),'No reviewed observed events');check(bool(tables['risk']),'No risk set')
        for eid,e in events.items():
            check(e.get('source_id') in sources and e.get('passage_id') in passages,f'{eid}: source/passage evidence required')
            if e.get('passage_id') in passages:check(passages[e['passage_id']]['source_id']==e.get('source_id'),f'{eid}: passage from different source')
            check(e.get('event_type') in ('rhetorical_endorsement','observed_interaction','policy_adoption'),f'{eid}: declare actual event type')
            check(bool(e.get('actor')) and bool(e.get('action')),f'{eid}: actor/action required')
            check(e.get('proposition_id') in props,f'{eid}: named proposition/action definition required')
            reviewed=[a for a in tables['adjudications'] if a.get('passage_id')==e.get('passage_id') and a.get('task')=='event' and a.get('proposition_id')==e.get('proposition_id')]
            check(len(reviewed)==1 and reviewed[0].get('final_label')=='confirmed',f'{eid}: independently reviewed and adjudicated event confirmation required')
            if e.get('event_type')=='observed_interaction':check(bool(e.get('receiver')) and e.get('actor')!=e.get('receiver'),f'{eid}: directed actor/receiver required')
            t=instant(e.get('event_time'),eid);a=instant(e.get('available_at'),eid)
            if t and a:check(a>=t,f'{eid}: availability before event')
            if a and cutoff:check(a<=cutoff,f'{eid}: unavailable at cutoff')
        intervals={}
        for r in tables['risk']:
            rid=r.get('risk_id');a=instant(r.get('start'),str(rid));b=instant(r.get('stop'),str(rid))
            check(r.get('proposition_id') in props,f'{rid}: unknown proposition');check(r.get('outcome') in ('0','1'),f'{rid}: outcome must be 0/1')
            if a and b:check(a<b,f'{rid}: nonpositive interval');intervals.setdefault((r.get('iso3'),r.get('proposition_id')),[]).append((a,b,r))
            if r.get('outcome')=='1':
                e=events.get(r.get('event_id'));check(e is not None,f'{rid}: event outcome lacks evidence')
                if e:
                    t=instant(e.get('event_time'),str(rid));check(e.get('actor')==r.get('iso3'),f'{rid}: event actor mismatch')
                    check(e.get('proposition_id')==r.get('proposition_id'),f'{rid}: event proposition mismatch')
                    if t and a and b:check(a<t<=b,f'{rid}: event outside risk interval')
            else:check(not r.get('event_id'),f'{rid}: non-event interval has event_id');check(bool(r.get('censor_reason')),f'{rid}: observation/censor explanation required')
        for key,group in intervals.items():
            group.sort(key=lambda x:x[0]);check(all(group[i][1]<=group[i+1][0] for i in range(len(group)-1)),f'{key}: overlapping risk intervals')
            hits=[i for i,z in enumerate(group) if z[2]['outcome']=='1'];check(len(hits)<=1 and (not hits or hits[0]==len(group)-1),f'{key}: first-event risk continues after adoption')
        for e in tables['edges']:
            eid=e.get('edge_id');t=instant(e.get('measured_at'),str(eid));a=instant(e.get('available_at'),str(eid))
            check(e.get('source_id') in sources,f'{eid}: edge source evidence required')
            check(bool(e.get('sender')) and bool(e.get('receiver')) and e.get('sender')!=e.get('receiver'),f'{eid}: directed non-self edge required')
            if e.get('source_id') in sources:
                sa=instant(sources[e['source_id']].get('available_at'),str(eid))
                if a and sa:check(a>=sa,f'{eid}: edge predates available source evidence')
            check(e.get('layer') in ('observed_interaction','vote','text_similarity','stance_agreement'),f'{eid}: edge layer required')
            try:check(float(e['weight'])>=0 and float(e['weight'])<float('inf'),f'{eid}: invalid edge weight')
            except (ValueError,KeyError):check(False,f'{eid}: invalid edge weight')
            if t and a:check(t<=a,f'{eid}: availability precedes measurement')
            starts=[z[0] for group in intervals.values() for z in group if z[2].get('iso3')==e.get('receiver')]
            if a and starts:check(a<min(starts),f'{eid}: edge not preexisting at first recipient risk interval')
        if capability=='diffusion':check(bool(tables['edges']),'No preexisting network/exposure evidence')
    return {'schema':'un.review.check.v1','capability':capability,'passed':not errors,'errors':errors,'warnings':warnings,'row_counts':{k:len(v) for k,v in tables.items()},'publication_approved':False,'note':'Structural/provenance checks only. Human truthfulness, semantic quality, model validation and causal identification are not certified.'}

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    i=sub.add_parser('init');i.add_argument('directory',type=Path);i.add_argument('--replay',type=Path)
    v=sub.add_parser('validate');v.add_argument('directory',type=Path);v.add_argument('--capability',choices=['pilot','labels','stance','history','diffusion','events'],default='labels');v.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.command=='init':initialize(a.directory,a.replay);print('Created unreviewed workspace; no labels assigned.');return
    result=validate(a.directory,a.capability);payload=json.dumps(result,indent=2)
    if a.out:
        protected={a.directory/'bundle.json',*(a.directory/(name+'.csv') for name in SCHEMAS)}
        protected|={a.directory/s.get('text_path','') for s in rows(a.directory/'sources.csv')[1]}
        if a.out.resolve() in {p.resolve() for p in protected}:raise ValueError('Report cannot overwrite dataset inputs')
        a.out.write_text(payload+'\n',encoding='utf-8')
    print(payload);raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__':main()
