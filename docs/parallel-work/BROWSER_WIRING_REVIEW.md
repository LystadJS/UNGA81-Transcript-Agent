# Coordinator W5/W6 browser wiring — engineering preview

**PR state:** Draft integration candidate from `main` at `21c1d5298a1a83b27a98f0e7b50113765bc023d0`. This is **not** authorization to merge, deploy the public browser, or promote research findings. The previously accepted [W5](../../site/parallel/w05-browser/experimental/method-lab/README.md), [W6](../../site/experimental/evidence-viz/README.md), and [W3→W5/W6](W3_W5_W6_INTEGRATION_REVIEW.md) implementation files are imported unchanged.

## What this coordinator branch connects

- `site/index.html` and `site/latent.html` link to a new `site/research.html` research landing route.
- `site/research.html` provides links to the accepted **Method Lab** (W5) and **Evidence Visualization Suite** (W6). These use the same original, source-bound worker code.
- The landing route loads the **actual W5 `UNMethodLabContracts.fromParallel`** and **actual W6 `UNEvidenceViz.mount`** against the *same* invented source-linked `un.parallel-analysis.v1` envelope. The visible model, missing-source and fitted-coverage ledgers are derived from W5. All four charts are rendered by W6; no numerical kernels or raw text are loaded or refitted.
- A local, explicitly synthetic **envelope + four panels** JSON bundle may be inspected in the current tab (maximum 1 MiB). Both imported inputs and built-in demo must pass W5, W6, exact 1.0.0 contract and synthetic-split/schema requirements, with no source URLs or text/review-packet fields. No server transfer, storage API, analytics beacon or third-party model call.
- `tools/build_pages.py` has a tight **13-file** nested-source allowlist. It copies only W5/W6 HTML, CSS, runtime JS and one previously accepted invented JSON fixture. The W6 JavaScript fixture is also invented. It refuses missing/symlinked/oversize files. It deliberately **excludes** README, tests, screenshots, synthetic receipts, private reviews, cached vectors, saved runs, research outputs and non-runtime directories.

## Non-release safeguards

The main browser collector, analysis/review/saved-run kernels, daily D1 O1–O5 gates, frozen 37 Oct 5–6 meetings, corpus hashes, human review decisions, `site/release.json`, `site/numerics-manifest.json`, `AGENTS.md` and `docs/NEXT_STEPS.md` are **not edited**. Only coordinator-owned entry/navigation/build and tests are changed. The site release and portfolio mirror remain separate decisions **after PR acceptance**, not automatic evidence of scientific readiness.

W5 separately permits authorized **local** development corpus/saved-run inspection with its existing consent and worker isolation; W6 public preview and shared research landing route are synthetic-only. Do not load held-out evaluation data in W5. No private transcript content or row-level real evidence belongs in the public Git repository or static build. Browser import validation cannot authenticate synthetic labels against arbitrary secretly mislabeled source text; the public route refuses recognizable source-bearing fields and URLs, and users must not provide private files there.

## Acceptance and exact reproducibility

```sh
node --test tools/test_research_browser_wiring.cjs
node --test site/experimental/evidence-viz/tests.cjs
node site/parallel/w05-browser/experimental/method-lab/test-method-lab.cjs
node docs/parallel-work/validate-contract.cjs
python tools/test_research_browser_build.py
python tools/build_pages.py /tmp/research-site-new
python tools/test_research_browser_ui.py --site /tmp/research-site-new --browser-path /usr/bin/google-chrome --outdir /tmp/research-qa
```

The path-scoped `.github/workflows/coord-research-browser-wiring.yml` executes the same native contract checks, relevant existing browser regressions, fresh static build verification, W5 Worker/numerical browser regression and real 1440×900 and 390×844 Chromium checks. It tests original source-link inspector, local SVG export, private-source refusal, stale-result clearing, absence of external requests, nested route availability and mobile page overflow. A **green current-head run** is required before coordinator integration acceptance; prior W5/W6 evidence alone is not sufficient.

## Withheld after engineering acceptance

- Actual UN development original-byte source provenance revalidation and independent null/source-group inference.
- Country/actor stance or policy-alignment inference, significance, influence, causal diffusion, or longitudinal trend publication.
- Production access to private transcript-bearing analytical outputs and new D1 daily adapters.
- Public Pages deployment, `site/release.json` update, website mirror synchronization and live asset verification before an independently accepted source PR and explicit coordinator release decision.

**Disposition:** draft browser integration PR only. Merge and release require a separate fresh-main review of exact paths, current CI, privacy and public build, and any pending W2/W4/W7 interfaces. Engineering readiness is not publication readiness.
