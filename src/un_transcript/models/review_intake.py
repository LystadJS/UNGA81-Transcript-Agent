"""Reconcile actual owner exports against a frozen training pilot, without training."""
import argparse
import copy
from datetime import datetime
import hashlib
import json
import re
from pathlib import Path
from .contracts import check_labels, digest, read_json, write_json

EDITABLE={'status','label','national_attribution_valid','owner_confirmed','notes'}
IDENTITY=('dataset_revision','packet_prefix','manifest_sha256','split')


def reconcile(draft, registration, returned, expected_packet, previous=None):
    if draft.get('schema')!='un.stance-labels.v1':raise ValueError('Unsupported original label schema')
    if expected_packet.get('split')!='train':raise ValueError('Training review only; sealed evaluation stays separate')
    if draft.get('registration_sha256')!=digest(registration):raise ValueError('Original draft registration mismatch')
    originals={r['pair_id']:r for r in draft['rows']}
    if len(originals)!=len(draft['rows']):raise ValueError('Duplicate original pair')
    merged={}; receipts=[]; reviewers=set(); dates=[]
    for bundle,kind in ([(previous,'reconciled_training')] if previous is not None else [])+[(returned,'reviewed_subset')]:
        if bundle.get('schema')!='un.stance-labels.v1':raise ValueError('Unsupported returned label schema')
        meta=bundle.get('review_export',{})
        if meta.get('schema')!='un.owner-browser-review.v1' or meta.get('kind')!=kind or meta.get('packet')!=expected_packet:
            raise ValueError('Mismatched packet or unfinished progress export')
        if (type(meta.get('total_examples')) is not int or meta['total_examples']!=len(originals)
            or type(meta.get('confirmed_examples')) is not int or meta['confirmed_examples']!=len(bundle.get('rows',[]))):
            raise ValueError('Review export counts do not reconcile with the frozen pilot')
        if kind=='reconciled_training':
            hashes=meta.get('input_exports')
            if (not isinstance(hashes,list) or not hashes
                or any(not isinstance(h,str) or not re.fullmatch('[a-f0-9]{64}',h) for h in hashes)
                or len(hashes)!=len(set(hashes))):
                raise ValueError('Invalid prior review export provenance')
        if not isinstance(bundle.get('reviewer_id'),str) or not bundle['reviewer_id'].strip():
            raise ValueError('A nonempty reviewer identity is required')
        check_labels(bundle,registration,'train')
        reviewers.add(bundle['reviewer_id']); dates.append(bundle['reviewed_at'])
        for row in bundle['rows']:
            base=originals.get(row['pair_id'])
            if base is None:raise ValueError('Unknown pilot example')
            if any(row.get(k)!=v for k,v in base.items() if k not in EDITABLE):
                raise ValueError('Frozen passage, proposition or source field changed')
            if set(row)-set(base)-EDITABLE:raise ValueError('Unexpected row fields')
            if row.get('national_attribution_valid') is not None and type(row['national_attribution_valid']) is not bool:
                raise ValueError('National attribution must be true, false or null')
            if not isinstance(row.get('notes',''),str):raise ValueError('Notes must be text')
            clean={**copy.deepcopy(base),**{k:copy.deepcopy(row.get(k)) for k in EDITABLE if k in row}}
            old=merged.get(row['pair_id'])
            if old is not None and old!=clean:raise ValueError('Conflicting returned judgments require explicit resolution: '+row['pair_id'])
            merged[row['pair_id']]=clean
        receipts.extend(meta.get('input_exports',[]) if meta.get('kind')=='reconciled_training' else [digest(bundle)])
    if len(reviewers)!=1:raise ValueError('Different reviewer identities require explicit resolution')
    result={**copy.deepcopy(draft),'owner_confirmed':True,'reviewer_id':next(iter(reviewers)),
            'reviewed_at':max(dates,key=lambda d:datetime.fromisoformat(d.replace('Z','+00:00'))),
            'rows':[merged[r['pair_id']] for r in draft['rows'] if r['pair_id'] in merged],
            'review_export':{'schema':'un.owner-browser-review.v1','kind':'reconciled_training',
                            'packet':expected_packet,'input_exports':sorted(set(receipts)),
                            'total_examples':len(originals),'confirmed_examples':len(merged)}}
    check_labels(result,registration,'train')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('draft','registration','packet-manifest','reviewer-manifest','returned','output'):
        p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--previous',type=Path);args=p.parse_args()
    reviewer=read_json(args.reviewer_manifest);identity={k:reviewer[k] for k in IDENTITY}
    raw=args.packet_manifest.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=identity['manifest_sha256']:raise ValueError('Packet manifest checksum mismatch')
    entries={r['path']:r for r in json.loads(raw)['files']}
    for file,name in ((args.draft,'train-draft.json'),(args.registration,'registration.json')):
        item=entries[identity['packet_prefix']+name]; data=file.read_bytes()
        if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise ValueError('Original pilot input checksum mismatch')
    result=reconcile(read_json(args.draft),read_json(args.registration),read_json(args.returned),identity,
                     read_json(args.previous) if args.previous else None)
    write_json(args.output,result)
    print(json.dumps({'status':'validated_owner_training_subset','confirmed_examples':len(result['rows']),
                      'total_examples':len(read_json(args.draft)['rows']),'training_started':False,'model_accepted':False}))

if __name__=='__main__':main()
