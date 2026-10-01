"""Prepare new random development and fresh country-disjoint test packets."""
import argparse,json
from pathlib import Path
from test_packet import prepare

def run(work):
    work=Path(work);candidates=work/'ai-evaluation-recovered/candidates.json'
    old=[work/'ai-pilot-r2',work/'ai-later-review',work/'ai-test-sep28']
    dev=work/'ai-random-dev-v2';test=work/'ai-fresh-test-v2'
    if dev.exists() or test.exists():raise FileExistsError('Use a new workspace; existing packets are immutable')
    a=prepare(candidates,old,dev,dates=('2026-09-24','2026-09-25','2026-09-26'),seed=2102026,packet_kind='later_date_development')
    b=prepare(candidates,old,test,seed=3102026,extra_references=[dev])
    return {'development':a,'fresh_test':b}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('workspace');a=p.parse_args();print(json.dumps(run(a.workspace),indent=2))
