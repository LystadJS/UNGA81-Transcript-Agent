"""Check audit attachment on a COPY of a completed daily run using explicit fixture labels."""
from pathlib import Path
import argparse, json, shutil
import pilot_review as pilot
import reviewed_loader as loader

def check(run,output):
    run=Path(run).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    copied=output/'run';shutil.copytree(run,copied)
    rows=json.loads((copied/'audit/speeches.json').read_text(encoding='utf-8'))
    s=rows[0];fixture=output/'fixture-source.json'
    fixture.write_text(json.dumps([dict(iso3=s['iso3'],date=s['date'],text=s['text'])]),encoding='utf-8')
    bundle=output/'fixture-review';meta=pilot.prepare(bundle,fixture)
    policy=json.loads((bundle/'bundle.json').read_text());policy['engineering_fixture']=True;(bundle/'bundle.json').write_text(json.dumps(policy),encoding='utf-8')
    pilot.complete(bundle,{'token':meta['csrf'],'confirmed':True,'reviewer':'SYNTHETIC-INTEGRATION-FIXTURE-NOT-HUMAN','rows':[dict(passage_id=i,label='insufficient',rationale='Synthetic integration assertion only; no human review or relevance claim') for i in meta['selected_ids']]})
    result=loader.attach(bundle,copied)
    receipt=json.loads((Path(result['audit_directory'])/'receipt.json').read_text())
    labels=json.loads((Path(result['audit_directory'])/'labels.json').read_text())
    assert receipt['status']=='engineering_fixture_only' and not labels['human_review_complete']
    result.update(engineering_fixture=True,real_human_review_completed=False,base_files_verified=len(receipt['base_run_file_sha256']),source_run_modified=False)
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('output',type=Path);a=p.parse_args();print(json.dumps(check(a.run,a.output),indent=2))
