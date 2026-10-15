"""Explicit source-free build/test entry point; no source or result publication.

The JSON Schema is a deterministic build artifact from make_schema.py. It must
exist before either validator is used. No import of the numerical producer
writes files. Direct unittest imports must run make_schema first.
"""
import argparse
import importlib.util
import json
import os
import platform
import shutil
import unittest
from pathlib import Path

from .make_schema import write_contract

MODULE = 'research.integration.w2_w4_w6.waggoner.test_us_reference'


def suite(loader=None):
    write_contract()
    return (loader or unittest.TestLoader()).loadTestsFromName(MODULE)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',type=Path)
    parser.add_argument('--require-complete',action='store_true',help='Fail rather than accept any skipped test')
    args=parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(suite())
    receipt={'kind':'synthetic_engineering_tests','python':platform.python_version(),
        'head_sha':os.environ.get('GITHUB_SHA'),'tests_run':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),
        'skipped':[{'test':str(t),'reason':why} for t,why in result.skipped],
        'result':'pass' if result.wasSuccessful() and not result.skipped else 'incomplete' if result.wasSuccessful() else 'fail',
        'publication_eligible':False,'real_data_eligible':False,'holdout_transcripts_opened':0}
    if args.receipt:
        args.receipt.parent.mkdir(parents=True,exist_ok=True)
        args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    return 0 if result.wasSuccessful() and (not args.require_complete or not result.skipped) else 1


if __name__=='__main__':
    raise SystemExit(main())
