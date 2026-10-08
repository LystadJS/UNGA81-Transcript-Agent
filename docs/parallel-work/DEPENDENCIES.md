# Dependency map and collision rules

```text
Frozen source schemas + development lineage + immutable evaluation lock
                             |
                    COORDINATOR C0
                   Interchange v1
                             |
        +----------+---------+---------+
        |          |                   |
       W1         W2                  W3                 W4
 source/nulls  consensus       spectral/diffusion   longitudinal
        |          |                   |                 |
        +--- statistical review / comparability evidence ---+
                             |
              accepted, source-verified adapters
                             |
                         W5 browser
                          /       \
              W6 visualizations    W7 diplomatic UX
                          \       /
                    coordinator entry points
                             |
                  CI + privacy + provenance
                             |
                source site build / release
                             |
               website mirror and live check
```

W2 and W3 may prototype in parallel with W1 **without claiming significance**. W4 may build a synthetic panel without W2 or W3. W5/W6/W7 may prototype directly against **synthetic v1 envelopes**, independent of production-method acceptance. Final promotion requires verified upstream input identity, model version and eligibility; one worker's completion does not implicitly validate another.

## Specific shared-interface dependencies

| Producer | Consumer | Interface / hazard | Resolution |
| --- | --- | --- | --- |
| `research/corpus/contract.cjs` | W1–W4 | Passage IDs, raw hashes, meeting/parent lineage, development-only eligibility; unreviewed segments are not full speeches | Read-only adapter; require exact source/selection digests |
| `site/analysis-core.js` + `site/latent-core.js` | W2–W7 | Browser `id`, `text_sha256`, `source_url`, optional `parent_id`, saved-run input and selection hashes | Map by stable `id + hash`, never array index or display coordinate |
| `site/cluster-core.js`, `site/gmm-core.js`, `site/nmf-core.js` | W2/W3/W6 | Hard cluster zero = unassigned; GMM responsibilities ≠ NMF shares ≠ calibrated probabilities | Export typed memberships and their fitting basis; keep null/ambiguous separate |
| W1 source/dependence audit | W2 and W3 statistical interpretation | Null exchangeability, source grouping, method-family multiplicity | Descriptor may be computed first, but inferential label withheld until valid test |
| W2/W3 fitted groups | W4 correspondence | Cluster-label permutation, eigenspace rotation, splits/merges and absent units | Stable observation IDs, explicit correspondence/anchor ledger; no automatic one-to-one matching |
| W1–W4 | W5/W6/W7 | Contract compatibility vs numerical comparability | Fail closed on unsupported schema or unknown source/model versions; no silent refit |
| W5 | W6/W7 | Browser app state, import and exports | Separate isolated components; shared entry-point wiring by coordinator only |
| Coordinator source repo | Portfolio mirror | CDN/cached deploy may differ from source branch; private data leakage | Only post-merge mirror, compare expected assets and hashes on live site |

## Integration incompatibility examples

Reject or request correction when a PR changes upstream source hashes; supplies only display-UMAP distances as cluster evidence; merges unreviewed source segments into verified speech/country identities; drops model failures from a consensus denominator; uses holdout text, changes holdout selection, changes O1–O5; renormalizes missing country weights over known countries; treats entropy or membership as stance; compares embeddings with different representation bases without an alignment experiment; defines missing as a zero issue mention; or modifies another worker's namespace.

**Version policy:** `un.parallel-analysis.v1` 1.0.0 is the first additive adapter. Optional additive fields may be introduced under 1.x only if old readers still succeed; required-field or semantic changes require a new schema/version and migration tests. No workers revise the contract; propose changes for coordinator review.
