# W3 → W5 → W6: coordinator source-bound integration review

**Decision:** accept the synthetic research interchange adapter as a separate
engineering component. W5 and W6 were independently validated and merged;
active browser deployment remains a separate coordinator change.

## Versioned upstream provenance

| Component | Reviewed revision | Status |
| --- | --- | --- |
| W1 source-aware validator | PR #19 merge `87dedd6ee7b30fb7cd1e26e8ef26e30ee8e52329` | Merged; engineering-only |
| W3 spectral/diffusion methods | PR #16 merge `58ad3c25de97beea33325331b4b74fb784ca2e8f` | Merged; engineering-only |
| W5 method lab | PR #21 head `2d78dd8b3bba60b61094179a8dea84f78f1f45ed`; merge `316f3b81cecc0bba0920277f5551bc8d0313764f` | Merged; native and browser QA passed |
| W6 visualization | PR #20 repaired head `b86c90175e8c2f184062b02db996893319b3339c`; merge `16ad599cf88aa6b76e3c8ee45551f6e9c36f7503` | Merged; native/browser QA passed |
| W5/W6 owner/coordinator ownership | PR #27 merge `6f94d7a09314991c0202eadaad3ac894e7553a61`; PR #28 merge `800fa499641ec8c814c079c4833ae162b98079d6` | Scope recorded |

## Source-bound compatibility findings

| Surface | Validated treatment |
| --- | --- |
| W5 import | Native W3 `un.parallel-analysis.v1` remains unchanged, including every excluded, unavailable, failed and unassigned model result; no sampling or reattribution |
| W6 graph view | Derive a separate panel from W3 original source-linked edges and Gaussian-kNN affinity, never mislabel as cosine distance or political alliance |
| Missingness | The previous W6 eligible-only result-row defect is **fixed**: each W3 model now has exactly one result per all inventoried frame rows, including null-cluster excluded records |
| Source identity | Original source/selection hashes, hash basis, observation ID+text SHA, parent/meeting/URL, graph policy and matrix integrity verified through W1 and original W3 receipts |
| Sensitivity | W3 duplicate and meeting concentration is aggregate only; per-edge duplicate/agenda sensitivity remains explicitly `not_assessed` |
| Graph size | W6 has 50-node display cap; 96-node W3 graph is `withheld` with intact 96-source denominator, not sampled |
| Metrics and claims | Gaussian edge strength is a constructed affinity, not cosine similarity, diplomatic coordination, stance, policy transmission or inferred causal influence |
| Privacy | Only invented synthetic source IDs accepted by this coordinator adapter; no authorized private development original-source results are exported into public browser |

## Executed verification and confidence boundaries

- **W5/W6 real browser acceptance:** [CI 37815064508](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37815064508) passed original W5 20/20 and repaired W6 16/16 Node tests, merged W1 relational validation on W6 10+1 frame, W5 Chrome DevTools Worker/PCA/LSA numerical parity, Playwright 1440px/390px keyboard/source inspection, export, no external traffic, empty/failed/withheld states, and actual screenshots.
- [Synthetic browser captures and QA receipts](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37815064508/artifacts/11566917078) are invented source examples, not UN evidence.
- **W3/W5/W6 interchange:** coordinator CI uses native W3 numerical 24, 24+1 and 96 source scenarios, independently pins/loads actual W5/W6 modules, tests raw v1 W5 replay, W6 complete missing frame, graph integrity and over-cap withholding. See latest PR #26 run and test receipt for actual status; no test is claimed without executed CI.
- Reproducibility commands, source snapshots, adapters and measured denominators are documented in `research/integration/w3_w5_w6/README.md`.

## Scientific and operational holds

- **PASS only for synthetic engineering:** provenance matching of supplied derived receipts, numerical graph/assignment consistency, browser accessibility and replay on invented fixtures.
- **NOT RUN:** original-byte revalidation for real UN development transcripts, pinned MiniLM model inference, independent source-group/null-calibrated significance, 37 reserved October 5–6 held-out meetings, representative national source attribution or political interpretation.
- **NOT APPROVED:** public browser deployment, release manifest changes, D1 O1–O5 gate changes, website mirror, or production exposure to private source text. User request is to *prepare* the follow-on active browser wiring PR, not deploy it.
- Existing `tools/build_pages.py` copies only top-level site files, so isolated W5/W6 subdirectories merged under `site/` are not published until a separately reviewed build/release change explicitly includes them.

## Coordinator next stage

Review/merge the isolated coordinator adapter only with latest CI and exact SHA, then prepare a separate draft active browser wiring PR from current `main`. Gate links/scripts on accepted W5/W6 assets and real Chrome/mobile QA; do not change the canonical interchange schema or frozen research files. Keep all analytical outputs engineering-only and all deployment actions pending explicit release approval.
