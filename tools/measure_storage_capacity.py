"""Read project storage metadata only; no source/annotation downloads or writes."""
import json
import os
from pathlib import Path
from un_transcript.capacity import measure_capacity
from un_transcript.publication import load_publication_config
from un_transcript.snapshots import HFStorage, StorageRequestError


def main():
    private=os.environ['HF_DATASET_REPO']
    public=load_publication_config('config/publication.json',private,os.environ.get('HF_PUBLIC_DATASET_REPO',''))['public_repo']
    results=[]
    for repo,is_private in ((private,True),(public,False)):
        results.append(measure_capacity(HFStorage(repo,private=is_private)))
    report={'schema':'un.project-capacity.v1','status':'measured','repositories':results,
            'account_capacity_accepted':False,'source_contents_read':False}
    target=Path(os.environ['RUNNER_TEMP'])/'storage-capacity.json'
    target.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,sort_keys=True))


if __name__=='__main__':
    try:main()
    except Exception as error:
        result={'status':'failed','error_type':type(error).__name__}
        if isinstance(error,StorageRequestError):
            result.update(storage_operation=error.operation,http_status=error.status_code)
        print(json.dumps(result))
        raise SystemExit(1)
