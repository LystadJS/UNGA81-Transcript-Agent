"""Inspect one warehouse attempt without downloading private archive material."""
import argparse
import json
from pathlib import Path
from un_transcript.run_inspection import inspect_run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',type=int,required=True)
    parser.add_argument('--attempt',type=int)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--receipt-zip',type=Path,help='Connector-downloaded monitoring ZIP; must match the live artifact digest')
    args=parser.parse_args()
    receipt_zip=None
    if args.receipt_zip:
        with args.receipt_zip.open('rb') as stream:receipt_zip=stream.read(262145)
        if len(receipt_zip)>262144:raise ValueError('Monitoring archive exceeds size bound')
    result=inspect_run(args.run_id,args.attempt,receipt_zip=receipt_zip)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'run_id':result['run_id'],'attempt':result['attempt'],
                      'status':result['status'],'conclusion':result['conclusion'],
                      'receipt_state':result['receipt_state'],'job_timing_available':result['job_timing_available']}))
    return 1 if result['receipt_state'] in ('invalid','unavailable') else 0


if __name__=='__main__':
    raise SystemExit(main())
