"""Create an unfinished-only reviewer from a hash-bound original training packet.

Checks submitted labels against frozen originals; does not train a model or
replace the separate full-registration acceptance gate.
"""
import argparse
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
from tools.build_private_reviewer import render
from un_transcript.models.contracts import LABELS, STATUSES
from un_transcript.models.review_intake import EDITABLE, IDENTITY


def remaining(draft, returned, identity):
    meta=returned.get('review_export',{})
    originals={r['pair_id']:r for r in draft['rows']}
    if (draft.get('schema')!='un.stance-labels.v1' or len(originals)!=len(draft['rows'])
        or any(r.get('split')!='train' for r in draft['rows'])):
        raise ValueError('Invalid original training frame')
    if (returned.get('schema')!='un.stance-labels.v1' or returned.get('owner_confirmed') is not True
        or returned.get('registration_sha256')!=draft['registration_sha256']
        or meta.get('schema')!='un.owner-browser-review.v1' or meta.get('kind')!='reviewed_subset'
        or meta.get('packet')!=identity or identity.get('split')!='train'
        or type(meta.get('total_examples')) is not int or meta['total_examples']!=len(originals)
        or type(meta.get('confirmed_examples')) is not int or meta['confirmed_examples']!=len(returned.get('rows',[]))
        or not isinstance(returned.get('reviewer_id'),str) or not returned['reviewer_id'].strip()):
        raise ValueError('Returned review does not match the frozen frame')
    if datetime.fromisoformat(returned['reviewed_at'].replace('Z','+00:00')).tzinfo is None:
        raise ValueError('Review timestamp requires a timezone')
    seen=set();flags=[]
    for row in returned['rows']:
        mid=row.get('pair_id');base=originals.get(mid)
        if base is None or mid in seen:raise ValueError('Unknown or duplicate reviewed example')
        seen.add(mid)
        # JSON equality is type-sensitive (false must not equal offset zero).
        if any(json.dumps(row.get(k),sort_keys=True)!=json.dumps(v,sort_keys=True)
               for k,v in base.items() if k not in EDITABLE) or set(row)-set(base)-EDITABLE:
            raise ValueError('Frozen source, proposition or identity changed')
        if (row.get('owner_confirmed') is not True or row.get('status') not in STATUSES
            or (row['status']=='clear' and row.get('label') not in LABELS)
            or (row['status']!='clear' and row.get('label') is not None)
            or (row.get('national_attribution_valid') is not None and type(row['national_attribution_valid']) is not bool)
            or not isinstance(row.get('notes',''),str)):
            raise ValueError('Invalid confirmed choices')
        if row.get('capacity')=='collective' and row.get('national_attribution_valid') is True:
            flags.append({'pair_id':mid,'reason':'recorded_collective_but_national_attribution_confirmed',
                          'resolution':'owner_clarification_required','owner_choice_unchanged':True})
    out=copy.deepcopy(draft);out['rows']=[r for r in out['rows'] if r['pair_id'] not in seen]
    return out,flags


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',type=Path,required=True)
    p.add_argument('--returned',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.original;prov=root/'provenance'
    reviewer=json.loads((prov/'reviewer-manifest.json').read_bytes())
    identity={k:reviewer[k] for k in IDENTITY}
    raw=(prov/'packet-manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=identity['manifest_sha256']:raise ValueError('Packet manifest mismatch')
    entries={e['path']:e for e in json.loads(raw)['files']}
    raw_draft=(prov/'original-training-draft.json').read_bytes()
    pin=entries[identity['packet_prefix']+'train-draft.json']
    if len(raw_draft)!=pin['bytes'] or hashlib.sha256(raw_draft).hexdigest()!=pin['sha256']:
        raise ValueError('Original training draft checksum mismatch')
    html=(root/'training-review.html').read_bytes()
    if hashlib.sha256(html).hexdigest()!=reviewer['html_sha256']:raise ValueError('Original reviewer checksum mismatch')
    payload=json.loads(html.decode().split('<script id="packet" type="application/json">',1)[1].split('</script>',1)[0])
    draft=json.loads(raw_draft)
    if payload['draft']!=draft or payload['identity']!=identity:raise ValueError('Reviewer payload mismatch')
    raw_returned=a.returned.read_bytes();returned=json.loads(raw_returned)
    todo,flags=remaining(draft,returned,identity)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'owner-reviewed-original.json').write_bytes(raw_returned)
    if todo['rows']:
        (a.output/'remaining-review.html').write_text(render(todo,
            {r['pair_id']:payload['display'].get(r['pair_id'],{}) for r in todo['rows']},identity,
            total_examples=len(draft['rows'])),encoding='utf-8')
    receipt={'schema':'un.owner-continuation.v1','packet':identity,
        'returned_sha256':hashlib.sha256(raw_returned).hexdigest(),'original_total':len(draft['rows']),
        'completed':len(returned['rows']),'remaining':len(todo['rows']),'clarifications':flags,
        'validation':'hash_bound_original_training_packet','registration_acceptance_gate_run':False,
        'training_started':False,'model_accepted':False}
    (a.output/'validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ('completed','remaining','training_started','model_accepted')}))

if __name__=='__main__':main()
