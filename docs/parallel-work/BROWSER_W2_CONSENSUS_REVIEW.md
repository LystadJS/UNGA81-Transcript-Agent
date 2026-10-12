# Coordinator W2 browser inspection — engineering-only acceptance

**Scope:** Follow-on to merged PR #21 (W5), PR #20 (W6), PR #29 (experimental browser release) and newly merged PR #17 (W2). Based on main 2a61a76c715bcef1c8603b230f3493b2a2af8298, which also contains W4 PR #18. **No substantive results or new public-site release are authorized by this draft.**

## Integration contract

The research page adds an isolated, read-only **W2 native weighted-coassignment inspector**. It imports two original synthetic JSON files from the unmodified W2 producer:

1. consensus-v1.json — complete un.consensus.v1 pair, family weights, fit failures, noise, groups and sensitivity ledger;
2. standardized-interchange-v1.json — un.parallel-analysis.v1 original source-identity and model–observation ledger.

The browser script site/research-consensus.js applies the existing W5 and W6 validators and then verifies both files' synthetic-only source/schema/selection identity, stable ID + text SHA and original parent/meeting/offsets. It independently checks the actual W2 threshold SHA-256; complete pair and matrix records; weighted/raw planned, assigned-both and coassigned denominators; null-vs-zero, noise/missing/failed-fit accounting; family planned weight audits; complete-link supported groups; and W2 interchange cluster assignments. No model is refitted. Every inspected pair displays the original W2 weighted association, source IDs/hashes and denominators.

**Numerical-contract discrepancy:** W6's original demonstrative consensus display computes the equal mean of per-family raw rates. W2's substantive *descriptive* statistic uses planned family→method→configuration→resample→seed weights and a conditional weighted numerator/denominator. These need not match under differential fitting/missingness. Reusing W6's illustrative consensus panel would silently change the method. The new W2 inspector therefore displays the **original W2 statistic**, rather than transforming W2 results into W6's pair format.

W2 bounds the eligible population at 256 observations. This inspector validates and retains all 256 source identities and pair records but **withholds** the interactive 35×35 matrix when over 35 source observations. It explicitly reports the retained full count without silently sampling, recalculating or discarding evidence. W5's original 600 observation limit remains unchanged.

## Privacy and reproducibility

Only synthetic engineering output is allowed: W2 producer, synthetic.v1 source schema, synthetic SHA basis and split, publication_eligible false, evaluation_role engineering_only, null original source URLs or reserved HTTPS example.invalid fictional fixture pointers (never navigated), and no transcript text fields. User-selected files are parsed locally; same-origin CSP remains. Cross-file hashes confirm consistency but do not authenticate actual UN originals. W2's synthetic producer originally mislabeled 12 observations as six total frame units; this PR corrects only that fictional fixture denominator while keeping its six distinct meeting groups, model fits and weighting unchanged. The display never claims government stance, alliance, political influence, null significance or policy diffusion.

Native checks:

~~~sh
node research/consensus/run_synthetic.cjs /tmp/w2-generated
node research/integration/test_w2_browser_bridge.cjs
node docs/parallel-work/validate-contract.cjs
~~~

Real-browser check (after a disposable Pages build):

~~~sh
python research/integration/w2_browser_smoke.py --site /tmp/w2-pages-preview --fixtures /tmp/w2-generated --browser /usr/bin/google-chrome --output /tmp/w2-qa
~~~

The new path-filtered coordinator workflow generates W2 files with its **actual native producer**, runs original W2/W5/W6/v1 regressions, builds a disposable preview from the existing Pages asset allowlist, then verifies Chrome 1440×900/390×844. It checks keyboard pair inspection, source-file tamper refusal, file-change invalidation, overflow, browser errors, and zero third-party requests. Screenshots remain ephemeral CI artifacts.

## W4 blocked upstream — fail closed

The newly merged W4 interchange adapter correctly describes previously **imported** cluster labels, not fresh W4 fits. It sets attempted_fits:0, successful_fits:0, failed_fits:0 even if source-bound imported positive-cluster assignments are present. W5's current relational validator refuses assigned observations without a successful fit. W1 accepting W4's source/model bookkeeping is not evidence that W5 can consume it. Do not manufacture successful W4 fits or conflate a display-map fit identity with an actual clustering fit identity.

The historical W4 P2 source frame additionally retains 269 unverified country-year cells with unknown dates/identities. Coordinator interchange v1 does not represent a source_status of unverified or a null date. An existing, separately typed and backward-compatible source-inventory sidecar (docs/parallel-work/source-inventory-v1.cjs) preserves that missingness, but its P2-to-v1 legacy binding is explicitly WITHHELD. W4 properly refuses the incompatible direct export rather than inventing timestamps, absences or vectors. A new approved fit-provenance/imported-label consumer contract, authenticated eligible subset binding, source-dependent calibration and explicit validation are prerequisites. No private W4 positions or source-bearing output are imported by this change. W6's older fictional longitudinal example remains a demonstration only.

## Pending acceptance

| Check | Status at branch authoring |
| --- | --- |
| Fresh source and coordinator ownership review | PASS; final exact-head review pending |
| W2 original producer ↔ browser validator and adversarial Node tests | NOT RUN natively |
| Real Chromium desktop/mobile, keyboard, tamper and privacy | NOT RUN |
| Existing W3/W5/W6 static build and browser regression | NOT RUN |
| W4 imported-fit/source-status compatibility | BLOCKED — new contract necessary |
| Private original UN source authentication and longitudinal significance | WITHHELD |
| Reserved 37 October 5–6 meeting text | NOT ACCESSED |
| New production/main/Pages deployment and website mirror | NOT AUTHORIZED |

**Merge / release boundary:** Coordinator must inspect the exact changed paths and current main, obtain current-head CI PASS, and receive a separate explicit release decision before deployment or website mirroring. Engineering-only draft code is not empirical publication approval.
