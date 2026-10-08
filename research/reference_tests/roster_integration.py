#!/usr/bin/env python3
"""Replay the roster adapter through unchanged parser/review/frozen inference; fake input only."""
import argparse, contextlib, hashlib, json, subprocess, tempfile
from pathlib import Path
from unittest.mock import patch
from production_synthetic import HERE,validate_artificial_corpus,machine_populations,artificial_model_eval,machine,source_status
from holdout_dryrun import verify_frozen_lock
from encoder import offline

def execute(output,checkpoint=None,semantic=None,model=None):
    if output.exists():raise FileExistsError('Refuse to overwrite validation')
    if any(x is not None for x in (checkpoint,semantic,model)) and not all(x is not None for x in (checkpoint,semantic,model)):
        raise ValueError('All three frozen runtime paths are required; no fallback')
    lock=verify_frozen_lock()
    with tempfile.TemporaryDirectory() as td:
        folder=Path(td)/'fake'
        subprocess.run(['node',str(HERE/'roster_adapter.cjs'),str(folder)],check=True,capture_output=True)
        receipt=json.loads((folder/'receipt.json').read_text())
        corpus=machine.read_verified(folder/'corpus.json');validate_artificial_corpus(corpus)
        rows,annotations=machine_populations(corpus)
        strict=[r for r in rows if r['strict_eligible']]
        report={'schema':'un.roster-integration-acceptance.v1','synthetic':True,'reserved_transcripts_opened':0,
            'reserved_roster_commitment':json.loads((folder/'roster.json').read_text())['reserved_roster_sha256'],
            'frozen_evaluation_lock_sha256':lock['sha256'],'roster_slots':len(receipt['rows']),
            'source_coverage':source_status(corpus),'strict_passages':len(strict),'strict_parents':len({r['parent_id'] for r in strict}),
            'strict_meetings':len({r['meeting_id'] for r in strict}),'human_confirmations':0,
            'adapter_receipt_sha256':receipt['sha256'],'inference':'NOT_RUN_MODEL_NOT_PROVIDED'}
        if model is not None:
            from sklearn.cluster import KMeans
            from sklearn.decomposition import PCA,TruncatedSVD,NMF
            from sklearn.feature_extraction.text import TfidfVectorizer,TfidfTransformer
            with offline() as attempts,contextlib.ExitStack() as stack:
                for cls in [KMeans,PCA,TruncatedSVD,NMF,TfidfVectorizer,TfidfTransformer]:
                    stack.enter_context(patch.object(cls,'fit',side_effect=AssertionError('Model refitting prohibited')))
                    if hasattr(cls,'fit_transform'):stack.enter_context(patch.object(cls,'fit_transform',side_effect=AssertionError('Fit-transform prohibited')))
                report['inference']=artificial_model_eval(corpus,checkpoint,semantic,model,lock)
                report['network_attempts']=len(attempts)
                if attempts:raise ValueError('Network call detected')
            report['refit_methods_guarded']=True
    with output.open('x') as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--checkpoint',type=Path);p.add_argument('--semantic',type=Path);p.add_argument('--model',type=Path)
    a=p.parse_args();print(json.dumps(execute(a.output,a.checkpoint,a.semantic,a.model),indent=2))
