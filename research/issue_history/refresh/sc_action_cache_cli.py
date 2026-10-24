"""Maintainer CLI for an offline private selected-action cache; no publication."""
import argparse
import json
from .sc_action_cache import cached_crosswalk


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('collection-file','ddl-database','cache-dir','ddl-raw-csv','expected-ddl-source-sha256'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--review-file')
    parser.add_argument('--refresh',action='store_true',help='Rebuild a fresh cache generation while preserving previous generations.')
    options=vars(parser.parse_args(argv));options['force_refresh']=options.pop('refresh')
    result=cached_crosswalk(**options)
    print(json.dumps({'cache_status':result['cache_status'],'cache_key':result['cache_key'],'artifact_path':str(result['artifact_path']),
                      'crosswalk_summary':result['report']['summary'],'selection_summary':result['report']['event_selection']['summary']},indent=2))
    return result


if __name__=='__main__':main()
