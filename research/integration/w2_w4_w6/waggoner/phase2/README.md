# Offline synthetic US-relative trajectory views — Phase 2

A research-side implementation of specification V05–V08, stacked on PR82's
accepted repaired head `81110db49786a05f9c8f8ce4d5103c92fe255586`.
This directory owns no production loader, public asset, empirical source intake,
scientific gate or release permission. No merge or publication is authorized.
Other Waggoner figure families (biplots, dimension diagnostics, sensitivity grids)
are not claimed implemented by this trajectory-specific delivery.

## Components and behavior

`views.js` exposes reusable `series`, `radius`, `elapsedPositions`, `csv`,
`replay`, `validateReplay` and `mount` functions. The mounted interface contains
paired absolute/US-centered SVG paths, a high-dimensional gap time series,
algebraic gap contributions, a complete country-period matrix, and both sides'
source/weight inspector. SVG positions come from the Phase1 producer. The views
never refit, calculate new profiles or change the US reference when highlighting
another country. All countries in the fictional frame are selectable.

The paired plots use one scene-wide fixed range and equal x/y units. Dates use
actual elapsed time at declared period ends. Only valid adjacent transitions are
connected. Display rejection preserves valid high-dimensional metrics; missing
US profiles never become carried-forward coordinates or a structural zero.
Zero-gap ratios stay undefined, and the visible squared-gap fraction exposes
omitted-dimension movement. Uncertainty/sensitivity remain withheld.

Eight new fictional scenarios cover moving references, missing US periods,
missing required comparator genres, third-dimension-only movement, zero gaps,
invalid display transforms, an empty inventory and failed comparator sources.
Every source, person, review record and measurement in these fixtures is invented;
the country codes are navigation labels, not empirical diplomatic observations.

## Source and replay boundary

The builder accepts no analytical data path or URL. It manufactures the explicit
fictional panels, calls unchanged Phase1 `build_us_reference`/`validate_result`,
and assembles a deterministic catalogue. The coordinator suite then replays all
eight full source/model/receipt bundles through the unchanged independent Node
validator and verifies six exact Phase1 code blobs. Source/profile hashes are
consistency checks, never real-source authentication or release authority.

A SHA256 literal in the CSP-hashed application script binds the exact catalogue
bytes. Native WebCrypto must verify them before any chart or export is enabled.
The result is frozen in memory. This is bundle integrity, not a signed publisher
identity; someone replacing the entire HTML and its code can replace that trust
root. An insecure context or missing WebCrypto fails closed.

Browser file input accepts only a bounded, closed `un.us-relative-view-replay.v1`
selection record that exactly matches a bundled model and catalogue. It does NOT
accept arbitrary source panels, raw transcripts, model JSON or self-issued
receipts. Empirical importing requires a separately authorized integration.
Rejected or cancelled imports clear charts, source details and exports. An epoch
counter prevents delayed imports/PNG renders from restoring stale selections.
There is no storage, analytics, external script/font, source fetch or model fetch.

## Local output

```sh
python -m research.integration.w2_w4_w6.waggoner.phase2.build --out /tmp/usref-phase2
node research/integration/w2_w4_w6/waggoner/phase2/verify_catalogue.cjs /tmp/usref-phase2
```

Open `/tmp/usref-phase2/index.html` locally, or serve only that generated directory
on loopback. The builder refuses an output directory inside the repository,
including `site/`. Nothing is added to the Pages build or portfolio mirror.
The output is a single self-contained HTML file plus a manifest and fictional
verification inputs. Export buttons produce local SVG, PNG, CSV, replay JSON and
standalone HTML preserving the current selection. CSV retains all 30 cells,
blank numerical values for missing comparisons, state/reason fields and source
hashes. SVG/PNG contain both coordinate systems and high-dimensional diagnostics;
SVG metadata retains the replay identity. All output remains synthetic-only.

## Acceptance

```sh
python -m research.integration.w2_w4_w6.waggoner.run_tests --require-complete
python -m unittest research.integration.w2_w4_w6.waggoner.phase2.test_build -v
PHASE2_BUILD_DIR=/tmp/usref-phase2 node --test research/integration/w2_w4_w6/waggoner/phase2/test_views.cjs
python -m research.integration.w2_w4_w6.waggoner.phase2.test_browser \
  --build-dir /tmp/usref-phase2 --artifact-dir /tmp/usref-phase2-evidence \
  --require-axe --axe /path/to/axe-core/axe.min.js
```

The coordinator-only `coord-us-relative-phase2.yml` proposal runs exact-head and
disposable integration-tree variants with native R, Python, Node and Chromium.
Browser acceptance uses Playwright1.57.0 and axe-core4.10.3, a loopback server
allowlisting generated HTML only, blocked nonlocal requests, mandatory local-file
HTML replay, keyboard inspection, cancellation/race checks, integrity corruption,
all export formats, 320/390-pixel layouts and reduced-motion checks. Automated
WCAG2.1 A/AA scans cover eight desktop scenarios and the default mobile view;
incomplete automated rules are retained rather than suppressed. This is not a
claim of full WCAG conformance or a manual assistive-technology audit.

Missing runtimes, failed imports, test failures and skips cannot be reported as
acceptance. The build is not acceptance; exact-head execution receipts and any
remaining failures belong in the PR. Phase1's original R1/R2 reproductions and
scientific/publication holds remain intact. No real transcripts are opened.
