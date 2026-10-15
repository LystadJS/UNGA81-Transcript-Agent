# Engineering validation record — 2026-10-15

## Baseline and ownership

- `main` initially inspected at `25ba1a7948c33188f21986af3cffbe73bbcafdba`, then refreshed at `1af11061e3fa65d51b28d42a1b98bef250b6168b`. PR #66 began at `f13b8bce9dc3c90e033043fc8173aa6bb59d2342`; concurrent authorized commits moved its head to `663ee04dd92e932825f992baf2a876bd9b38ea17` during preparation. The continuation revalidated exact heads and intentionally retained the concurrent `controls.py` and `test_controls.py` without rewriting them.
- Authorized path: `research/semantic_representations/**` only. This revision adds/replaces only files in that subtree. No reserved transcripts opened, original source data edited, site/portfolio changed, W1–W7 implementation edited or release gate weakened.
- Direct upstream review: `AGENTS.md`, `docs/NEXT_STEPS.md`, `docs/parallel-work/{OWNERSHIP,PR_ACCEPTANCE,INTERCHANGE_V1,DEPENDENCIES}.md`, `docs/SEMANTIC_COMPARISON.md`, `research/semantic_review/{encoder.py,model-lock.json,requirements.txt,RUN_CONTRACT.md}`, `site/{analysis-core.js,lsa-core.js,representation-metrics.js,latent-core.js}`, and coordinator ledger dated 2026-10-15. Existing 47-model-test/57-machine-test/53-corpus-check and 15-regression results belong to **prior upstream work**, not fresh PR #66 evidence.

## Newly executed synthetic validation

Execution environment: Python 3.13.5, standard library only for the new suite; all fixture vectors and source texts invented, no model download, no external inference. Seeds for the comparison diagnostic: 17, 23, 31, 47 by default; deterministic per-test medoid seeds specified explicitly. No random source sampling.

```sh
cd research/semantic_representations
python3 -m unittest discover -v -p 'test_*.py'
python3 -m compileall -q pipeline.py local_model.py comparison.py interchange.py fixtures.py cli.py controls.py test_pipeline.py test_controls.py
python3 cli.py synthetic --cache /tmp/unga81-semantic-cache --output /tmp/unga81-semantic-fixture.json --k 3
```

**Run result:** 79/79 Python unit tests passed in 1.783 seconds (76 newly implemented fixture/pipeline tests plus 3 retained branch control tests); compileall PASS. CLI synthetic run PASS: 16/16 source-bound fixture observations encoded; no encoder failures; same-observation lexical test-double vs semantic test-double neighborhood overlap `0.3958333333` for k=3 (synthetic only); all four authored paraphrase/opposition diagnostics satisfy the test-double's programmed separation; opposite positions never receive automatic stance labels. Twelve of 16 cross-geometry seed-fit pairs assessable; at least one deliberately unstable/failed synthetic medoid fit remains visible rather than omitted. A separate synthetic input contains 600 tokens in 3 chunks with zero declared truncation. Independent-process cache replay tests verify SHA-bound 16/16 cache hits, zero new inference calls, and output no-overwrite protection. Counts and medoid scores are **synthetic software checks**, not MiniLM checkpoint evaluation.

### Acceptance checklist by gate

| Gate | Status / evidence |
|---|---|
| Exact source-lineage / split / unit / hash-basis preservation on *synthetic* frames | PASS — tests for wrong hash, duplicate IDs, missing parent, Unicode offsets, withheld split, missing/exclusion and source URL |
| Source-bound cache replay, independent restart, corruption and changed code/model/selection refusal | PASS — unit tests + process-level CLI replay; representation includes implementation SHA-256 |
| Deterministic length handling and no silent truncation | PASS — synthetic 254/600 token fixtures; production tokenizer handling is inherited from the pinned existing encoder and its earlier validation |
| Semantic model revision/tokenizer/artifact pin | PASS — verified repository blob identities and ten artifact SHA-256 values in upstream lock; newly executed actual checkpoint inference **NOT RUN** |
| Dependency exact-version checks | PASS — code checks all six pins and Python 3.13; new environment provisioning / wheel-hash reproducibility **NOT RUN** |
| Same-observation lexical reference checks | PASS — archived-transform-only adapter and mismatch-refusal synthetic tests; real fit comparison **NOT RUN** |
| Contrasts: paraphrase, negation, protocol, opposite position, length sensitivity | PASS — authored deterministic fixture coverage; real model negative-control accuracy **NOT RUN** |
| Neighborhood overlap, failed fit/selection denominators, clustering changes | PASS — deterministic synthetic tests and auditable attempted-fits ledger; no inferential threshold |
| Read-only interchange contract | PARTIAL — synthetic v1 structural/relational consumer checks, metadata-only nonpublic development export; full coordinator JSON schema and upstream source receipt validation **NOT RUN** |
| Cross-repository existing regression suites | NOT RUN — unrelated shared kernels/consumers unchanged; coordinator may choose upstream suites for integration |
| GitHub exact-head CI | NOT RUN — no workflow configured for this exclusive new path; check-run and Actions statuses must be refreshed after push |
| Source-bound actual UN development comparison | WITHHELD — no authenticated private local model/source package available; no private inputs accessed |
| Held-out 37 meetings / D1 O1–O5 / public publication | NOT APPLICABLE — explicitly preserved and forbidden in this PR |

## Coordinator integration instructions

1. Confirm exact PR head, new `main` SHA and file list; no other PR namespace overlap. This remains **draft/engineering-only**.
2. Run `python3 -m unittest -v research/semantic_representations/test_pipeline.py` from its directory and the CLI synthetic smoke on a fresh, external cache path; compare fixture behavior and attest no transcript content entered public files.
3. Run official `node docs/parallel-work/validate-contract.cjs ...` on coordinator-authored synthetic source envelopes (not fabricated empirical exports); independently verify relational invariants, source/selection hashes and read-only consumer provenance.
4. If real local checkpoint evaluation is later authorized, supply authentic development-only source receipts, exact pinned local model artifacts, and saved lexical-fit vector hashes; run the private CLI **offline** outside the public repo. Preserve original text, exclusions and missingness. Prior inference in `research/semantic_review` must not be mislabeled as this PR's rerun.
5. Any browser integration, new W8 producer registration, CI workflow and release/mirror changes are coordinator-owned separate PRs. No deployment or merge is authorized by these fixture results.
