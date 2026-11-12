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
    args=parser.parse_args()
    result=inspect_run(args.run_id,args.attempt)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'run_id':result['run_id'],'attempt':result['attempt'],
                      'status':result['status'],'conclusion':result['conclusion'],
                      'receipt_state':result['receipt_state'],'job_timing_available':result['job_timing_available']}))


if __name__=='__main__':
    main()
