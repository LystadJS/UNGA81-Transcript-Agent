# Coordinator-only integration proposal — PR #69

**Not applied.** This proposal deliberately lives inside PR #69's exclusive namespace. Applying it would modify coordinator-owned `site/research.html`, `tools/build_pages.py`, and `.github/workflows/coord-c5-evidence-browser-qa.yml`; no worker is authorized to make those edits. Apply only on a separate coordinator branch after independent exact-head acceptance, then independently decide whether to merge/deploy.

## Patch artifact

`coordinator-integration.patch` is a proposed unified diff against merged C5 `main` at `1af11061e3fa65d51b28d42a1b98bef250b6168b`. Rebase and reconcile if `main` advances. The patch is **not** an assertion that private source or scientific publication gates pass.

It adds:

1. One explicitly marked **synthetic-only** navigation link; the original C5 W2 and W4 import controls remain authoritative and unchanged.
2. An exact five-file public Pages allowlist (`index.html`, `style.css`, `renderer.js`, `adapter.js`, `fixture.json`); no recursive copying of README, native tests, unpublished synthetic runs, raw data, screenshots or correction ledgers.
3. A read-only source-contract regression on **original** native C5 synthetic fixture files (previous C5 W1→W2 and W4 generator steps). The new regression calls merged `UNResearchConsensus.validate` and `UNResearchEvidence.loadW4Files`, then tests the v2 adapter against the verified source IDs, hashes, weighted pair numerators/denominators, native `p0/p1` period identities, missingness and original saved actor coordinates. It refuses tampered original hashes/bytes.
4. A *served-page* v2 Chromium QA step in the coordinator workflow, using `$CHROME_BIN` and both responsive viewports, plus extra allowlist/no-test-artifact assertions.

The new C5 native regression is implemented in `native-c5-regression.cjs`. Run only with original generated synthetic fixtures:

```sh
node research/integration/w1_w2/make-synthetic.cjs /tmp/c5-w2
python -m research.integration.w2_w4_w6.run_synthetic --output /tmp/c5-w4
C5_W2_FIXTURES=/tmp/c5-w2 C5_W4_FIXTURES=/tmp/c5-w4 \
  node --test site/experimental/research-validation-v2/native-c5-regression.cjs
python site/experimental/research-validation-v2/browser_smoke.py \
  --browser /usr/bin/google-chrome --output /tmp/rv2-qa
```

**Current local limitation:** the execution container cannot resolve GitHub, so it cannot checkout merged C5 or execute the original producers. The native harness is syntax-checked but NOT RUN here. Prior upstream C5 GitHub Actions #38458650819 passed the original source tests on the accepted merged revision; those are inherited evidence, not new validation of PR #69. Replayed original source-free C5 HTML/CI receipts establish the 25 / 24+1 W2 synthetic frame, 300 total pair records / 276 off-diagonal, and 176 W4 source records with 13 actors and `p0/p1` source periods. They do not replace byte-level native source verification.

## Engineering and release gates

Before integration, independently inspect all twelve worker paths, exact file SHA identities, original W2/W4 fixture contract regression, negative source/privacy tests, actual Chromium served-page results, CI run IDs/jobs/logs and output package contents. Resolve any semantic duplication with merged C5's existing W2/W4 renderers; never replace its weighted W2 statistic or original W4 transforms. Reject private originals, unverified historical W4 observations, held-out transcripts and unsupported scientific conclusions. Leave frozen D1 O1–O5, W1/W2 inference G01–G13, and all release/mirroring gates unchanged.

**No source PR merge, workflow modification, Pages deployment, release metadata change, or portfolio mirroring is authorized by this proposal.**
