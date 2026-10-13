# Coordinator W2 browser inspection — engineering-only acceptance

**Scope:** Follow-on to merged PR #21 (W5), PR #20 (W6), PR #29 (experimental browser release), PR #17 (W2), and the subsequently merged source-complete W1→W2 coordinator integration. Originally based on main 2a61a76c715bcef1c8603b230f3493b2a2af8298; refreshed by a **non-force merge of main 13120efbc271b5bcd733ad3711f2f2a18ecbce3b** on 13 October 2026. Main now includes the accepted W1→W2 grouped-child-fit engineering work (#50). This coordinator PR authorizes **no substantive results, real-source import, D1 change or scientific publication**; the separate synthetic-only browser merge remains gated on final exact-head acceptance.

## Integration contract

The research page adds an isolated, read-only **W2 native weighted-coassignment inspector**. It imports two original synthetic JSON files from the accepted W1→W2 coordinator producer, whose W2 fit and consensus result are from the unmodified W2 method:

1. w2-consensus.json — complete un.consensus.v1 pair, family weights, fit failures, noise, groups and sensitivity ledger;
2. w2-v1-interchange.json — un.parallel-analysis.v1 original source-identity and model–observation ledger.

The browser script site/research-consensus.js applies the existing W5 and W6 validators and then verifies both files' synthetic-only source/schema/selection identity, stable ID + text SHA and original parent/meeting/offsets. It independently checks the actual W2 threshold SHA-256; complete pair and matrix records; weighted/raw planned, assigned-both and coassigned denominators; null-vs-zero, noise/missing/failed-fit accounting; family planned weight audits; complete-link supported groups; and W2 interchange cluster assignments. No model is refitted. Every inspected pair displays the original W2 weighted association, source IDs/hashes and denominators.

**Numerical-contract discrepancy:** W6's original demonstrative consensus display computes the equal mean of per-family raw rates. W2's substantive *descriptive* statistic uses planned family→method→configuration→resample→seed weights and a conditional weighted numerator/denominator. These need not match under differential fitting/missingness. Reusing W6's illustrative consensus panel would silently change the method. The new W2 inspector therefore displays the **original W2 statistic**, rather than transforming W2 results into W6's pair format.

W2 bounds the eligible population at 256 observations. This inspector validates and retains all 256 source identities and pair records but **withholds** the interactive 35×35 matrix when over 35 source observations. It explicitly reports the retained full count without silently sampling, recalculating or discarding evidence. W5's original 600 observation limit remains unchanged.

## Privacy and reproducibility

Only synthetic engineering output is allowed: W2 producer, synthetic.v1 source schema, synthetic SHA basis and split, publication_eligible false, evaluation_role engineering_only, null original source URLs or reserved HTTPS example.invalid fictional fixture pointers (never navigated), and no transcript text fields. User-selected files are parsed locally; same-origin CSP remains. Cross-file hashes confirm consistency but do not authenticate actual UN originals. **Source-grain resolution:** The original standalone W2 fixture intentionally declares six source meetings supporting twelve observations; that inventory count is not an observation-frame count and must not be overwritten just to satisfy W5/W6. This PR now leaves the original W2 fixture unchanged and exclusively accepts the independently accepted W1→W2 coordinator projection with **25 inventoried observation records, 24 eligible and one unavailable**, in the same v1 frame grain. Any incompatible standalone fixture fails closed. The display never claims government stance, alliance, political influence, null significance or policy diffusion.

Native checks:

~~~sh
node research/integration/w1_w2/make-synthetic.cjs /tmp/w2-generated
node research/integration/test_w2_browser_bridge.cjs
node docs/parallel-work/validate-contract.cjs
~~~

Real-browser check (after a disposable Pages build):

~~~sh
python research/integration/w2_browser_smoke.py --site /tmp/w2-pages-preview --fixtures /tmp/w2-generated --browser /usr/bin/google-chrome --output /tmp/w2-qa
~~~

The new path-filtered coordinator workflow generates W2 files with the accepted source-complete **W1→W2 native coordinator producer**, and also runs the independent W1→W2 interop suite, runs original W2/W5/W6/v1 regressions, builds a disposable preview from the existing Pages asset allowlist, then verifies Chrome 1440×900/390×844. It checks keyboard pair inspection, source-file tamper refusal, file-change invalidation, overflow, browser errors, and zero third-party requests. Screenshots remain ephemeral CI artifacts.

## W4 blocked upstream — fail closed

The newly merged W4 interchange adapter correctly describes previously **imported** cluster labels, not fresh W4 fits. It sets attempted_fits:0, successful_fits:0, failed_fits:0 even if source-bound imported positive-cluster assignments are present. W5's current relational validator refuses assigned observations without a successful fit. W1 accepting W4's source/model bookkeeping is not evidence that W5 can consume it. Do not manufacture successful W4 fits or conflate a display-map fit identity with an actual clustering fit identity.

The historical W4 P2 source frame additionally retains 269 unverified country-year cells with unknown dates/identities. Coordinator interchange v1 does not represent a source_status of unverified or a null date. An existing, separately typed and backward-compatible source-inventory sidecar (docs/parallel-work/source-inventory-v1.cjs) preserves that missingness, but its P2-to-v1 legacy binding is explicitly WITHHELD. W4 properly refuses the incompatible direct export rather than inventing timestamps, absences or vectors. A new approved fit-provenance/imported-label consumer contract, authenticated eligible subset binding, source-dependent calibration and explicit validation are prerequisites. No private W4 positions or source-bearing output are imported by this change. W6's older fictional longitudinal example remains a demonstration only.

## Coordinator source and engineering acceptance — 13 October 2026

The eight reviewed paths on PR #45 are: a new same-origin W2 browser reader; a new dedicated coordinator QA workflow and source/method review ledger; two new synthetic-only Node/browser integration tests; plus narrowly scoped edits to the experimental research page, scoped CSS, and the existing browser smoke test's lazy-iframe assertion. No changes to source files under un/, production method kernels, original source or release manifests, frozen held-out evaluation, model checkpoints, or D1 O1–O5 gates.

| Gate | Status | Evidence |
| --- | --- | --- |
| Latest source and exclusive coordinator ownership | **PASS** | Non-force two-parent main integration, latest main 13120efbc271b5bcd733ad3711f2f2a18ecbce3b; 8 PR-diff files only; no collisions with newly accepted W1→W2 and W1 historical-source linkage or open W2/W4 visualization PR #47 |
| Source, selection, identity, status and model constraints | **PASS (synthetic engineering)** | W5 and W6 original validators, W2 sidecar/threshold SHA/complete pair ledger, independently checked W1→W2 25-frame identity; invalid-source and numerically altered cases rejected |
| Native W1→W2→W5/W6 and W2 adversarial tests | **PASS** | 20/20 new W2 browser validation/refusal cases; 16/16 accepted W1→W2 interoperability checks; original W2/W5/W6/v1 regression suites on [coordinator CI 38444210986](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38444210986) |
| Real browser, keyboard, mobile and privacy | **PASS** | Chromium desktop 1440×900 and mobile 390×844, local input-change invalidation, pair/source detail inspection, corrupted sidecar refusal, no horizontal overflow or external requests; same exact CI |
| Existing W3/W5/W6 research browser regression and disposable Pages build | **PASS** | [CI 38444211088](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38444211088), all steps successful, none failed/skipped |
| Shared structural + relational interchange | **PASS** | [CI 38444211080](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38444211080) |
| Latent numerical and real Chromium acceptance | **PASS** | [CI 38444210980](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38444210980) |
| Newly merged W1 grouped child refit semantics | **SEPARATE / NOT PROMOTED** | Source-group sensitivity remains descriptive; the W2 browser displays the original association and clearly distinguishes grouped spread from confidence intervals. It neither refits child models nor fabricates pair opportunities |
| P2/W4 imported label and nullable historical missing-source binding | **BLOCKED** | Existing un.parallel-source-inventory.v1 preserves verified/unverified sources; original-PV-to-legacy-v1 binding and imported-fit semantics remain withheld. No real actor trajectories or intervals imported |
| Original transcript byte validation, reserved 37 October 5–6 meeting text, real MiniLM or scientific calibration | **NOT RUN / WITHHELD** | This PR touches only synthetic browser artifacts. Held-out text not accessed; no empirical findings or country/stance claims |
| Production and website mirror | **SEPARATE VERIFICATION** | Conditional request to merge after final coordinator acceptance covers source integration of an explicitly synthetic browser feature. Postmerge main CI, Pages assets, and the separately owned portfolio mirror must be independently inspected; no private/public empirical data are publishable |

The above workflow receipts were obtained at the **pre-ledger implementation head 06cf2a7051cedb8e3fbb78bc8dbeadf71c4511ce**. An acceptance-ledger-only commit changes the PR SHA, so the coordinator must obtain a new clean **exact-head** CI set and compare the eight-file diff to the latest main immediately before merging.

**Scientific and release boundary:** W2's pair association is descriptive conditional model-fit agreement. A high value is not a probability of diplomacy, agreement, alliance, policy influence, statistical significance, calibrated uncertainty or independently authenticated country position. Real original source bytes, historical missingness, speaker identities and held-out evidence remain under separate authorization and release protocols. No external text transmission, silent sampling or inferred absent-source zeros are permitted.
