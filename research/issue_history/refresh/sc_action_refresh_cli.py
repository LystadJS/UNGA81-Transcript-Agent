"""One offline private refresh cycle against already-ingested voting sources."""
import argparse
import json
from .runner import refresh_private_actions


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('collection-file','ddl-database','cache-dir','state-dir','ddl-raw-csv','expected-ddl-source-sha256'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--review-file')
    parser.add_argument('--source-watermark',help='Caller-declared ISO snapshot date; does not establish source freshness.')
    parser.add_argument('--refresh',action='store_true')
    options=vars(parser.parse_args(argv));options['force_refresh']=options.pop('refresh')
    result=refresh_private_actions(**options);checkpoint=result.get('checkpoint') or {}
    summary={key:result.get(key) for key in ('schema','status','cache_status','health_persisted','failure_code')}
    summary.update(checkpoint_generation=checkpoint.get('generation'),cache_key=checkpoint.get('cache_key'),artifact_path=checkpoint.get('artifact_path'),
                   requested_window=checkpoint.get('requested_window'),observed_min=checkpoint.get('observed_min'),observed_max=checkpoint.get('observed_max'),
                   source_watermark=checkpoint.get('source_watermark'),selection_summary=checkpoint.get('selection_summary'))
    print(json.dumps(summary,indent=2))
    if result['status']=='failed':raise SystemExit(1)
    return result


if __name__=='__main__':main()
