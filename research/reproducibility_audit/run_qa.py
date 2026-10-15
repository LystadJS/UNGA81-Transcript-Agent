"""Standalone, synthetic-default audit report. No private file discovery or uploads."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from protocol import (load_contract, validate_envelope, changed_path_violations, qa_summary,
                      result_record, canonical_json, check_isolation)
from inventory import build
from replay import replay
from security import scan_public, scan_bytes

GOLDEN_REPLAY_OUTPUT_SHA256 = "1639ed5e207c3704860cf5190f3233198882bc190cead010905fbd6f4a290130"
GOLDEN_FIXTURE_SHA256 = "88ba2f60c77b87e71c30e4022d1c2ad90905f44454ee76ad7783cce1f5a260e0"

def build_summary(repo_root: Path, *, public_root: Path | None = None,
                  changed_paths: list[str] | None = None, envelope: dict | None = None) -> dict:
    """Only synthetic input is accepted; caller explicitly identifies public root."""
    checks=[]
    schema, schema_issues=load_contract(repo_root)
    checks.append(result_record('authoritative_contract', 'PASS' if schema else
        ('NOT RUN' if schema_issues and 'NOT RUN' in schema_issues[0] else 'FAIL'),
        'Pinned coordinator Git blob matched' if schema else '; '.join(schema_issues)))
    if envelope is not None:
        if envelope.get('producer', {}).get('fixture_kind') != 'synthetic' or envelope.get('cohort', {}).get('split') != 'synthetic':
            checks.append(result_record('interchange', 'FAIL','public QA accepts only synthetic fixture envelopes'))
        elif schema is None:
            checks.append(result_record('interchange','NOT RUN','authoritative schema unavailable'))
        else:
            failures=validate_envelope(envelope,schema)
            checks.append(result_record('interchange','FAIL' if failures else 'PASS',
                    '; '.join(failures) if failures else 'structural and relational constraints checked'))
    else:
        checks.append(result_record('interchange','NOT RUN','no explicit synthetic envelope supplied'))
    try:
        registry=build(repo_root)
        checks.append(result_record('method_inventory','PASS',
                                    f"{registry['count_registered']} registered; {registry['count_declared_kernels']} declared synthetic kernels; no executable claim"))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        registry=None
        checks.append(result_record('method_inventory','NOT RUN' if isinstance(exc,OSError) else 'FAIL',
                 f'catalog unavailable or incompatible: {exc.__class__.__name__}'))
    if changed_paths is None:
        checks.append(result_record('owned_path_and_frozen_gate_diff','NOT RUN','exact Git diff not supplied'))
    else:
        violations=changed_path_violations(changed_paths)
        checks.append(result_record('owned_path_and_frozen_gate_diff','FAIL' if violations else 'PASS',
               f'Unauthorized paths: {len(violations)}' if violations else f'{len(changed_paths)} paths under exclusive namespace'))
    replay_result=replay({'schema':'un.replay-fixture.v1','fixture_kind':'synthetic',
                            'seed':271828,'observations':[1,2,3,4,5]},
                          expected_sha256=GOLDEN_REPLAY_OUTPUT_SHA256)
    if replay_result['status']=='PASS' and replay_result.get('fixture_sha256')!=GOLDEN_FIXTURE_SHA256:
        replay_result={'status':'FAIL','reason':'pinned fixture bytes changed'}
    checks.append(result_record('two-process_synthetic_numerical_replay',replay_result['status'],
                  replay_result.get('output_sha256',replay_result.get('reason','no replay result'))))
    # Positive controls must fail the privacy scanner; a clean scanner here is a failure.
    sentinel_hits=scan_bytes(b'SYNTHETIC_PRIVATE_TRANSCRIPT_SENTINEL\n-----BEGIN PRIVATE KEY-----')
    checks.append(result_record('privacy_negative_control','PASS' if len(sentinel_hits)>=2 else 'FAIL',
                    f'{len(sentinel_hits)} expected classes detected' if len(sentinel_hits)>=2 else 'negative control missed'))
    synthetic_train=[{'id':'syn-train','source_family_id':'synthetic-shared','text_sha256':'a'*64}]
    synthetic_test=[{'id':'syn-eval','source_family_id':'synthetic-shared','text_sha256':'b'*64}]
    isolation_hits=check_isolation(synthetic_train, synthetic_test)
    checks.append(result_record('evaluation_leakage_negative_control',
         'PASS' if 'evaluation leakage: source_family_id' in isolation_hits else 'FAIL',
         'shared synthetic source-family identity rejected' if isolation_hits else 'source-family leakage missed'))
    if public_root is None:
        checks.append(result_record('actual_public_build_privacy_scan','NOT RUN','public staging directory not supplied'))
    else:
        findings=scan_public(public_root)
        checks.append(result_record('actual_public_build_privacy_scan','FAIL' if findings else 'PASS',
                  f'{len(findings)} possible exposures or uninspectable assets' if findings else 'no recognized signatures in staged directory'))
    checks.extend([
      result_record('authenticated_original_source_hashes','NOT RUN','private/remote source authentication not conducted'),
      result_record('sealed_evaluation_population','NOT RUN','private sealed evaluation identities deliberately inaccessible'),
      result_record('current_head_ci','NOT RUN','requires current SHA workflow run IDs/jobs from GitHub')
    ])
    summary=qa_summary(checks)
    summary['schema_source_git_blob']=schema and '3786a08eb6c4a7de7db2845138ffe4ae51f4b2c3'
    summary['replay_receipt']=replay_result
    summary['method_inventory']=registry
    summary['release_readiness']={
        'engineering_acceptance':{'status':'NOT RUN','reason':'exact-head applicable CI and coordinator review incomplete'},
        'statistical_calibration':{'status':'NOT RUN','reason':'independent nuisance-preserving null calibration not assessed'},
        'source_eligibility':{'status':'NOT RUN','reason':'authorized original-document source verification not performed'},
        'human_review':{'status':'NOT RUN','reason':'no owner-reviewed publication evidence'},
        'publication_authorization':{'status':'FAIL','reason':'publication explicitly withheld; no change to D1 gates'}
    }
    return summary


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--public-root',type=Path,help='Explicit public staging directory, never private source root')
    p.add_argument('--changed-path-list',type=Path,help='UTF-8 file containing exact PR changed paths')
    p.add_argument('--synthetic-envelope',type=Path,help='Synthetic v1 envelope JSON only')
    p.add_argument('--output',type=Path,help='JSON report path; default stdout')
    args=p.parse_args(argv)
    try:
        paths=args.changed_path_list.read_text(encoding='utf-8').splitlines() if args.changed_path_list else None
        fixture=json.loads(args.synthetic_envelope.read_text(encoding='utf-8')) if args.synthetic_envelope else None
        report=build_summary(args.repo_root,public_root=args.public_root,changed_paths=paths,envelope=fixture)
        raw=canonical_json(report)
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_bytes(raw)
        else:
            sys.stdout.buffer.write(raw)
        return 1 if any(c['status']=='FAIL' for c in report['checks']) else 0
    except (OSError,ValueError,TypeError) as e:
        print('FAIL: safe audit input could not be processed: '+e.__class__.__name__,file=sys.stderr)
        return 2


if __name__=='__main__': raise SystemExit(main())
