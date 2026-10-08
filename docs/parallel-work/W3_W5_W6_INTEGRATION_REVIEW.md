# W3 → W5 → W6: coordinator integration and review record

**Decision:** stage a separate synthetic-only read adapter and real cross-branch
consumer tests. Do not merge experimental W5/W6 worker PRs or publish the
browser. Neither original UN transcript content, reserved Oct 5–6 transcripts,
nor any existing source hash/review decision/publication gate is changed.

## Provenance and tested branch pins

| Component | Verified source | Pin for this review | Acceptance |
| --- | --- | --- | --- |
| W1 source group and relational validator | merged main, research/validation_framework/ | PR #19 merge 87dedd6ee7b30fb7cd1e26e8ef26e30ee8e52329 | Engineering only |
| W3 graph/diffusion method results | merged main, research/graph_methods/ | PR #16 merge 58ad3c25de97beea33325331b4b74fb784ca2e8f | Engineering only |
| W5 browser method-lab | PR #21 feat/browser-research-engine | 2d78dd8b3bba60b61094179a8dea84f78f1f45ed | Draft, unmerged |
| W6 visualization module | PR #20 feat/evidence-visualization-suite | 6a404992f34996b4e284a3bdac1f5c3496432478 | Draft, unmerged |
| Coordinator structural/relational v1 | docs/parallel-work/INTERCHANGE_V1.md | Main at PR creation | Existing, unchanged |

Coordinator CI checks out both unmerged worker sources at the exact pinned
commit SHAs into separate scratch directories; this PR does not copy or modify
their code. A changed upstream PR head requires a fresh review and repinning.

## Cross-contract decisions

| Contract | W5 browser | W6 visualization | Coordinator integration |
| --- | --- | --- | --- |
| W3 un.parallel-analysis.v1 | validateParallel/fromParallel source-bound import | Narrower validateEnvelope | Preserve original envelope unchanged for W5 |
| Missing/excluded observations | Requires explicit excluded model rows and fit ledgers | **Blocker:** tests model result count against eligible rows even when excluded frame rows exist | W6 must count full model-by-frame rows; bridge returns blocked_contract until fixed |
| Graph representation | Spectral and diffusion are offline-only | Requires network-specific graph, node, edge, threshold, sensitivity and source references | Derive a W6 panel from W3's audited source-linked edge ledger only |
| Link metric | Retains source model description | Draws a strength between 0 and 1 above a display threshold | W3 kernel weight is Gaussian affinity on kNN, **not cosine similarity**; display minimum 0 is not graph construction cutoff |
| Duplicate/agenda sensitivity | W3 aggregate duplicate/source concentration | Requires per-edge stable/sensitive/not_assessed | All edges marked not_assessed; no fabricated stability |
| Source provenance | Original ID, text SHA, hash basis, meeting, parent, source URL | identity.observation_refs and evidence-linked nodes/edges | Exact joined source hashes, parent/meeting/URL and matrix/representation identity |
| Graph size | Up to 600 source observations | Maximum 50 nodes | Withhold >50, never silently subsample |
| Failed/unassigned fits | Explicit status/counts per W3 model | Requires coherent coverage | No missing/error/noise-to-zero conversions |
| Validation | W5 Node tests, browser/worker and replay acceptance pending | W6 Node tests and Chromium QA pending | Run authentic pinned Node consumer suites; current integration is offline-only |
| Real source content | W1/W3 original source digest still needs private verification | Public W6 synthetic-only | Refuse any development/private inputs in this bridge |

### Required W6 fix (do not silently apply in a worker-owned branch)

In W6 evidence-viz.js validateEnvelope, replace the eligible-only result
count with a complete, unique model × all observed frame row contract.
For each model:

1. Require result rows equal to the total number of frame observations.
2. Check exactly one row for every eligible and excluded observation ID,
   with excluded-source result status excluded, cluster null and explicit
   exclusion reason.
3. Verify model coverage assigned + unassigned + not_fitted equals eligible,
   and the separately counted excluded results equal c.excluded.
4. Preserve unavailable original text_sha256=null, missing reason, and
   nonzero frame/excluded/missing counts. Never remove a record to make a
   chart render.
5. Update the W6 synthetic fixture to include excluded model result rows,
   consistent c.excluded counters, and both positive and adversarial tests.
   Run native Node and real desktop/mobile Chromium QA after any repair.

This coordinator staging PR does not edit W6 source or change v1 schema.
The fix requires the W6 worker/coordinator's separate ownership and release
acceptance.

## Acceptance gate accounting

PASS when demonstrated by current CI: native W3 source-linked generated output;
SHA256 manifest verification; merged W1 relational validation; original W5
fromParallel and SHA256 replay; original W6 small graph rendering; explicit
W6 missing-source refusal; W6 >50 withheld state; Gaussian affinity and graph
pair integrity checks; original W5 and W6 standalone Node regression suites.

WITHHELD: rendering excluded/missing-source W3 envelope through unmodified W6.
NOT RUN: authorized real development-source graph, pinned real MiniLM, original
byte/UN-transcript revalidation, independent null/held-out inference,
production browser/desktop/mobile/screenshots, D1 release or website mirror.
Never call an unexecuted acceptance test a PASS.

## Scientific limitations

W3's kNN graph and kernel weighting are *constructed geometry* sensitive to
vector representation, scale, duplicates, procedural language, source-group
composition and meeting dependence. Edge strength is not diplomatic alliance,
government stance, agreement, influence, policy transmission or causality.
Diffusion maps describe a geometric Markov process, not geopolitical diffusion.
No country attribution, inferential p-value or null calibration arises from
the synthetic fixtures.

## Integration and later release sequence

1. Validate source/identity contracts on exact pinned W5/W6 snapshot commits.
2. Keep this separate coordinator PR additive and unmerged unless it has
   passing checks and independent coordinator acceptance.
3. Review W5 PR #21 and W6 PR #20 independently; resolve W6's ownership
   and model-by-frame defect before accepting its full graph viewer.
4. After approval, adapt the modules into a coordinator-owned **experimental**
   browser entry point, with explicit synthetic/private safeguards.
5. Run actual browser keyboard/mobile/worker replay/exports, source lineage,
   privacy, resource and memory bounds before considering release assets.
6. Public deployment, D1 adapter promotion and portfolio mirroring are
   separate decisions; preserve frozen 37 reserved meetings throughout.

Reproduction commands: research/integration/w3_w5_w6/README.md. Read the
CI test result and recorded SHAs rather than interpreting this planned
acceptance table as a completed validation record.
