# Independent reproducibility and public research security audit

**Status: engineering draft; no empirical, human-review or publication authorization.**
Read the [evidence-backed coordinator handoff](AUDIT_REPORT.md) before relying on any QA status.

## Inputs and commands

This namespace owns only synthetic tests and read-only public metadata. It never retrieves source text, sealed evaluation transcripts, private reviews or vectors. Python 3 stdlib is the only dependency for the standalone audit. The repository's upstream R/Node/Chromium suites remain separate, read-only acceptance checks.

From the repository root (full authenticated checkout with upstream contract):

```sh
python3 -m unittest discover -s research/reproducibility_audit -p 'test_*.py' -v
python3 research/reproducibility_audit/run_qa.py --repo-root . --output /tmp/unga-reproducibility-QA.json
node docs/parallel-work/validate-contract.cjs
```

For explicit, **synthetic-only** envelope and local public staging input:

```sh
python3 research/reproducibility_audit/run_qa.py \
  --repo-root . \
  --synthetic-envelope /path/to/approved-synthetic-v1.json \
  --public-root /path/to/approved-public-staging \
  --changed-path-list /path/to/exact-pr-paths.txt \
  --output /tmp/unga-reproducibility-QA.json
```

The CLI exit status is **0 only when every required check is PASS/NOT APPLICABLE**, **1 if any check FAILS**, **3 if checks are NOT RUN / engineering acceptance WITHHELD**, and **2 for malformed/unreadable audit inputs**. JSON always marks `publication_authorized:false`. An absent upstream schema, missing identity population or unaudited public build is never a successful result.

## Audit implementation

| Module | Purpose | Evidence boundary |
| --- | --- | --- |
| `method_inventory.json` | Machine-readable snapshot of 30 backlog methods, upstream gates, runners and executable test entries | Existing `research/catalog.json` metadata, not proof of execution |
| `inventory.py` | Regenerate and compare catalog values and exact upstream Git blob | Rejects catalog drift; dependencies and claimed synthetic execution remain inherited |
| `protocol.py` | Structural schema validation, normative relational checks, source lineage/population compatibility, isolation and frozen path protections | Requires pinned upstream `interchange-v1.schema.json`; no original-source authentication |
| `replay.py` / `replay_worker.py` | Two fresh-process deterministic bootstrap replay, independent reference, seed and fixture/output hashes | Synthetic numerical arithmetic only, not empirical W1/W4 model replay |
| `security.py` | Synthetic privacy sentinel, secret-shaped content, source-record and vector artifact checks | Explicit public staging directory; negative patterns are not comprehensive privacy certification |
| `run_qa.py` | Standalone JSON PASS/FAIL/NOT RUN/NOT APPLICABLE summary and five-gate release matrix | Does not alter any gate or authorize deployment |
| `test_protocol.py` / `test_harness.py` | Positive and deliberately corrupted synthetic regression fixtures | No private inputs, no historical-fit claims |
| `audit.py` / `test_audit.py` | Inherited first-stage conservative subset retained for backward compatibility | Not authoritative v1 structural/relational validation |

The coordinator-owned schema is pinned to exact Git blob `3786a08eb6c4a7de7db2845138ffe4ae51f4b2c3`. The inventory is pinned to catalog Git blob `6aca560d961369fda7637869853e92366df86bde`. A future upstream schema or catalog change must trigger a separately reviewed audit update; never silently accept semantic drift.

## Required external acceptance

Run the actual **PR-head** synthetic suites, upstream contract, source-aware numerical regression and applicable CI. Record workflow run IDs, failures, skipped jobs, dependency versions and exact SHA. Independently authenticate only authorized original-source metadata; preserve the 37 reserved October 5–6 transcript lock, original source checksums, human decisions and D1 O1–O5. Public staging checks require an actual approved build and independent coordinator review.

The existing GitHub workflows do not automatically run the Python audit suite on the worker namespace. The integration coordinator must add a **separate coordinator-owned, path-limited workflow**; this worker must not edit `.github/workflows/**`.

A successfully executed synthetic suite is **engineering evidence only**. Statistical calibration, historical source eligibility, owner interpretation and publication authorization are separate decisions. The PR must remain draft and unmerged pending the coordinator's exact-head acceptance.
