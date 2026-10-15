# UNGA81 research browser validation v2

**Release:** engineering-only; synthetic fixtures only; draft PR #69; no merge or deployment authorized.
This standalone subtree contains no original UN transcript text, embeddings, speech excerpts, private annotations or claims about actual countries. It does not refit PCA/LSA/NMF, consensus, alignments, or statistical models. Nothing is sent over a network beyond the browser's own same-origin load of the checked-in synthetic fixture when the standalone demo is served.

## Scope and accepted semantics

- **W2 weighted consensus:** complete unordered pair frame, externally supplied conditional weighted association, original coassigned / assigned-both / planned numerator and denominators, source-family audit, unassigned, noise and failed fit counts, zero opportunity, missing pairs and instability. The renderer verifies the original ratio for corruption **without defining another formula**, and never substitutes the prototype W6 mean of eligible family-specific rates. Missing/zero/assessed zero are visibly different.
- **Country by latent component:** weighted numerator and denominator, observation population and weight basis, distinct observed zero, withheld and unavailable cells; unknown affiliations never receive inferred speaker/country positions or stance.
- **Longitudinal:** already aligned coordinates, descriptive radii, source counts and composition labels; draw movement only across sequential passed rank/selection/comparability checks. Failed periods remain in the coverage and alignment table but are not mapped to shared coordinates.
- **Methods:** attempted, successful, failed, skipped, not-fitted, unassigned, excluded and unavailable comparable stability. Stability is never null-calibrated significance.
- **Source/provenance:** full source ledger with synthetic SHA-256 claims, source hash basis, selection SHA, representation identity/version, source IDs, review status, JSON pointer, missingness, source affiliation and period. Missing and failed sources are subsets of exclusions, not disjoint extra inventory populations. Synthetic original hashes are *not* authenticated publisher hashes.
- **Abstentions:** fail closed for non-synthetic, malformed, incompatible, corrupted or incomplete results; withheld panel displays only abstention and required coverage without leaking results. No script in exported static HTML, and exports round-trip numerical data unchanged.

## Contract adapters (read-only)

`adapter.js` provides `fromW2(env,sidecar,{validateW2})`, `fromW4(originalFiles,{validateW4})`, and `fromW6Themes(env,panel,{validateEnvelope,validatePanel})`. The caller must inject the **accepted upstream validators**, not a Boolean trust flag: `UNResearchConsensus.validate` for W2; accepted C5 `UNResearchEvidence.loadW4Files` for the complete five-file original synthetic W4 bundle (byte/checksum verification required); and accepted `UNEvidenceViz.validateEnvelope/validatePanel` for W6. The adapter consumes their validated outputs, preserves original model/source identities and never reparses private source text or estimates numerical results. It **cannot** independently authenticate original source bytes; W4 five-file SHA256 input verification remains the accepted C5 loader's responsibility. Historical real-data W4 P2 / nullable date inventory cannot be silently forced into `un.parallel-analysis.v1`.

The standalone `fixture.json` uses `un.research-validation-v2.synthetic`; this is **not a replacement** for upstream `un.parallel-analysis.v1`, W2's `un.consensus.v1`, or the accepted W6 panel contract. Its full inventory deliberately has five invented sources (3 eligible; 2 unavailable/failed and excluded), 3 complete eligible off-diagonal pair opportunities, 6 affiliation×component cells, two method rows, a failing 2025→2026 alignment, and one source-absent affiliation. All sources and labels are invented.

## QA (Node 22 / Python 3.13 / Chromium)

From repository root:

```sh
node --test site/experimental/research-validation-v2/tests.cjs
python site/experimental/research-validation-v2/browser_smoke.py --output /tmp/unga81-rv2-browser
```

Serve with `python -m http.server 8000`, then open `/site/experimental/research-validation-v2/` for interactive replay. The browser test normally navigates to a transient localhost HTTP server; if Chromium administrator policy blocks all navigation, it detects `ERR_BLOCKED_BY_ADMINISTRATOR` and runs the **same checked-in page logic and CSS** inside an actual Chromium `set_content` document using the local synthetic fixture. That fallback covers rendering, layout, keyboard, exports, JSON replay, invalidation, and XML parsing but **does not count as served-page navigation validation**. It writes PNG screenshots under the specified temporary output directory (not tracked). No external requests, cache, or remote model calls.

Current local follow-up on this workstream (2026-10-15): **62/62 Node cases PASS**; actual Chromium **1440×900 and 390×844 DOM/browser behavior PASS** via the navigation-blocked fallback. Direct Chromium HTTP navigation remains BLOCKED by `ERR_BLOCKED_BY_ADMINISTRATOR`; the actual local HTTP server returns exact original asset bytes (4/4 PASS), but that is not equivalent to served-browser navigation. GitHub Actions/other upstream repository regressions must be evaluated separately on the exact PR head; earlier generic latent acceptance cannot be treated as renderer acceptance. Synthetic fixtures have no random seeds.

## Exact coordinator-only integration proposal

Do **not** change production files in this worker PR. After PR #69 exact-head review and independent validator acceptance, coordinator may:

1. Add a link (not a production importer) to this isolated demo from `site/research.html` on a coordinator-owned branch. Do not enable any empirical source input, public source URLs or silent automatic rendering.
2. If integrating accepted outputs, pass only separately accepted source-validated W2/W4/W6 objects through these adapters. Import accepted W2 `research-consensus.js` and accepted C5 W4 loader only after merged C5 PR #56's source-bound engineering acceptance. Preserve C5's original W2 weighted ratio and W4 five-file byte manifest, save-run stale-input clear/invalidation, 35-ID chart cap and protected asset allowlist.
3. Run the accepted W1/W2 source/numerical/contract regressions, W4 saved-alignment/source checks, W5 replay, W6 desktop/mobile tests, and this subtree's Node/Chromium suite on **the same integration head**. Inspect generated Pages assets for unexpected source-bearing text or recursive directory copies.
4. Update release manifests, Pages build allowlist, portfolio mirror and website live hashes **only after** explicit coordinator/owner release authorization; never automatically deploy this PR.

PR #56 was merged into `main` as synthetic engineering-only integration (`ecfc201ccfcd442c9f29e92777c1d9241beab4d9`); do not confuse this with downstream empirical inference/public release eligibility. W1/W2 G01–G13, D1 O1–O5, frozen source and original hash records, source embargo, 37 unopened October 5–6 transcripts, national-position attribution and longitudinal statistical identification remain untouched.

## Known limitations

This worker's synthetic pass proves display and defensive guards, not independent authenticity of original UN bytes, real-data eligibility, inferential calibration, national positions or accurate diplomatic relationships. W4 original-file ingestion must be performed by the accepted C5 loader. The injected-validator adapter tests use a clearly labeled mock and are **not** independent upstream acceptance. The browser fallback mode tests actual Chromium DOM/replay/export behavior and exact local HTTP bytes, but NOT navigation through the served URL. The coordinator must verify exact head, source schema compatibility, CI and public build/release authorization before any merge.


## Independent C5 compatibility follow-up (15 October 2026)

Source of truth: merged C5 original SHA review, base `main` `1af11061e3fa65d51b28d42a1b98bef250b6168b`, GitHub Actions source QA run `38458650819` (inherited source tests). The original source-free C5 CI artifact was replayed locally: W2 **25 inventoried / 24 eligible / 1 unavailable**, four balanced method families, **300 pair records / 276 off-diagonal**, unchanged original W2 weighted ratios, and original W4 **176 source records**, 13 actors, native `p0/p1` periods. The exported static W2 matrix's 276 pair labels were independently checked against the weighted numerator/assigned-both denominator (numeric rounding), full symmetry and the original source-safe receipt. **This artifact check does not rerun the original producer.**

Two actual integration bugs were identified and repaired in the new v2 projection: native W4 `p0/p1` period identifiers were previously overwritten with `date.slice(0,4)` years, and the arbitrary 100-source display cap excluded C5's 176-row synthetic W4 frame. W4 period association now uses only the original validator-returned `source.observations[].period` joined by source ID, and the original C5 bounded **600-row** frame can be retained without truncating the source ledger. The adapter now **requires the original five-file `loadW4Files` SHA loader**, rejecting use of the weaker pre-parsed `validateW4` method as a file-import substitute. Unknown nested payload keys, including raw-text-bearing fields hidden in a syntactically valid replay, are rejected before rendering or JSON export.

### Executable tests / precise limitations

```sh
# Executed on working copy: 62/62 tests passed, Node v22.16.0
node --test site/experimental/research-validation-v2/tests.cjs
# Executed: actual Chromium DOM/keyboard/exports/replay at 1440x900 and 390x844;
# HTTP file-byte parity passed; navigation blocked by container policy
python site/experimental/research-validation-v2/browser_smoke.py \
  --browser /usr/bin/chromium --output /tmp/rv2-c5-browser-v4
# Syntax-checked, NOT RUN here: requires full merged C5 checkout and generated native outputs
C5_W2_FIXTURES=/tmp/c5-w2 C5_W4_FIXTURES=/tmp/c5-w4 \
  node --test site/experimental/research-validation-v2/native-c5-regression.cjs
```

**Coordinator-only patch:** `COORDINATOR_PATCH.md` and `coordinator-integration.patch` provide exact proposed changes to browser navigation, Pages allowlist and C5 source-verified CI. The patch is **not applied**; its old-side contexts were checked against the `main` files and a synthetic-context `git apply --check` succeeded, not a true clean repository application. If integrated, require complete original source model/rank/comparability/fit/denominator gates; no release/website deployment follows automatically.
