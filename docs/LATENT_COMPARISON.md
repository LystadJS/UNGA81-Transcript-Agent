# Saved runs and latent-structure comparison

Open **Compare latent structure** from the transcript workspace, or open
[`latent.html`](https://lystadjs.github.io/un/transcript-agent/latent.html).
The orchestration engine is `latent-comparison-1.1.0`. Existing browser
numerical engines, frozen R references, daily adapters and publication gates
are unchanged. The workspace is an audit tool, not an automatic topic/stance or
policy-alignment classifier.

## Start a comparison

1. Select a saved `un.browser.corpus.v1` collection, or the existing private
   `un.reviewed-speech-analysis.v1` bundle. For a reviewed substantive/inclusive
   subset of a full collection, also select its completed passage-type review.
2. Choose dates, meeting scope and speaker region. Leave Topic blank to explore
   all eligible passages. A topic deliberately narrows the discovery population;
   an absence of matching text is not evidence of issue absence.
3. Add explicit settings, or select the paired PCA/LSA baseline. Comma-separated
   lists form a grid; the interface refuses more than twelve settings rather
   than silently sampling or truncating the grid. Inspect the rows before running.
4. Optionally select whole-meeting or recorded-affiliation refits. All settings
   receive the same requested group schedule. Actual schedules and successful/
   assessable denominators are retained and compared.
5. Generate the comparison, inspect coverage, fit status, source examples,
   assignment coverage and sensitivity, then save the replayable run or export
   JSON, diagnostic/coverage/weighting CSVs and self-contained visual HTML.
6. Open saved run A, then saved run B. Each keeps its own coverage, weights and
   settings. Coverage changes are reported only for identical original parent
   text; absent parents remain outside the corresponding retained cohort.

The comparison page performs no new transcript collection. It reads imported
files locally and executes numerical work in a cancellable Web Worker. Its
network policy allows same-origin assets only. No source text, review choices,
audio, API key, or packet upload is sent to an external service. Runtime source
hashes are recorded from the same-origin module files. Missing runtime assets
stop a new run rather than yielding an untracked result.

## Three distinct operations

| Operation | Preserved | What can change |
|---|---|---|
| Reopen saved run A | Exact input strings, output JSON and stored coordinates | Current rendering code; no numerical refit occurs |
| Compare A with B | Each archived run and its own settings/runtime | Cross-run comparisons are calculated only where identities/populations permit |
| Refit a settings plan | Source input and explicit selection plan | Each selected representation/model is independently fitted; its numerical diagnostics are retained |

A settings file contains no source text. A replayable run **does** contain the
original collection and, for reviewed inputs, its original review/audio bundle.
Store it in approved local storage. Downloading a report or diagnostic JSON is
not equivalent to saving a replay archive.

## Saved-run contract

`un.latent-saved-run.v1` contains `input_json` and `result_json` as exact strings,
with their SHA-256 hashes. `input_json` stores the original source string, input
kind and optional complete passage-review string/policy. `result_json` contains
`un.latent-comparison.v1`, normalized settings, source/selection hashes, numerical
outputs, coordinates, counts and runtime/module identities. The serialized JSON
contract omits JavaScript-only undefined properties and serializes negative zero
as zero; finite coordinate values and archived strings round-trip unchanged.

Reopening checks both hashes, revalidates source and review lineage through the
existing loaders, reconstructs the complete excerpt and full-parent populations,
and verifies the planned fit inventory, normalized settings, counts, original
metadata, offsets, coverage and cached composition summaries. Omitting records
from an archived fit is rejected even if its outer hash is recalculated. It does not
refit PCA, clustering, NMF or UMAP. Hashes establish consistency, not authenticity
of a reviewer or proof of numerical correctness. They do not protect against a
person deliberately forging both content and hashes. The exact numerical runtime
is recorded; a seed alone is not claimed to reproduce another environment.

Version 1.0 archives remain readable and byte-preserved. Their original outputs
are not rewritten to add new fields. The current renderer can derive overlapping
component summaries from their stored weights. A failed second-run import clears
the previous comparison and exports, preventing a stale report from appearing
to describe the rejected file.

Raw historical `analysis.json` exports are not silently promoted into replayable
runs: they may lack the original input bytes and review lineage. Open a source
collection or reviewed bundle and save a new run under the complete contract.

## Full-parent versus reviewed-excerpt contract

Enable the parent comparison only for a validated reviewed bundle. The excerpt
selection follows the normal date/scope/region/language, deduplication and optional
topic filters. The parent cohort then consists **only of the original parents of
those retained excerpts**. It is not the entire original 460-record collection.
The parent baseline has no topic filter: it represents those full speeches,
including material outside the selected windows. The other eligibility restrictions
and original exact-text deduplication remain in force.

Reports show retained passages, actual analyzed parents, and original collection
coverage separately. Per-parent coverage is the union of included original
Unicode-code-point spans divided by the original parent's code-point length;
it is not audio coverage or verified sentence accuracy. Original offset and text
hash lineage remain in the nested source records and full JSON output. Duplicate
exclusions and withheld fits remain inspectable.

Every existing fit continues to give each eligible unique observation equal
weight. More excerpts therefore give a parent more influence in an excerpt-level
fit. The additional **parent-balanced cluster composition** first calculates
cluster shares within each represented parent and then averages parents equally.
That is a descriptive summary of the existing partition, **not** a reweighted PCA,
TF-IDF or clustering fit. Country-balanced fitting is not implemented in this phase.

The same two summaries now retain NMF's normalized component shares and Gaussian
mixture responsibilities. No hard assignment is substituted for overlapping
weights. Undefined NMF shares are excluded, with explicit defined-passage and
defined-parent denominators; a parent with no defined shares is absent from that
conditional summary, not a zero-weight theme. Source-record analysis labels its
balanced summary accordingly: an original transcript segment is not automatically
a complete speech.

Coverage bars share a 0–100% original-text scale. Paired composition bars show
passage-weighted and equal-parent summaries on the same scale. Expandable component
profiles retain source links and values, show up to 30 parents in source order,
and retain all rows in JSON. Components remain local to their fitted model and
have no automatic substantive names. The dedicated CSVs retain denominator
counts, original parent hashes where available, and the balancing unit.

Full speeches and excerpts are different observations in different fitted feature
spaces. No cross-unit ARI, coordinate displacement, cluster-number matching or
“better model” score is reported. Compare coverage, source examples and model
behavior; do not compare cluster 1 in the parent fit with cluster 1 in the excerpt
fit as if they were the same theme.

**The actual pilot has only three parents.** The current clustering and NMF
engines require at least four usable observations. Its full-parent models must
therefore be visibly withheld, even though its twelve approved excerpts can be
analyzed. The synthetic six-parent test validates the supported parent-fitting
path. Neither that fixture nor the three-parent pilot establishes representative
method performance.

## Reusable settings

`un.latent-plan.v1` separates a shared source selection and group schedule from
1–12 explicit model rows. With parent comparison, each row yields an excerpt fit
and a parent fit, up to 24 full fits. Limits remain 600 selected passages, 31 days,
40 MB source import, 4 MB optional passage review, and 128 MB saved-run archive.
Existing model-specific bounds and refusal rules still apply. These are bounded
resource policies, not a claim that every largest permitted grid is fast or fits
every browser's memory. Cancellation releases no partial report.

The controls support PCA/LSA, retained dimensions, k-means/PAM/Ward/average counts,
HDBSCAN size/density/selection, Gaussian covariance and regularization, NMF ranks,
and UMAP neighbors/seeds. Metric MDS is an optional fixed-score display. A saved
plan can explicitly specify additional existing numerical options such as starts,
iteration ceilings and tolerances; validation uses the original method contracts.
A common group-refit policy overrides per-row refit settings to make the intended
pairing explicit. No new algorithm or model-selection policy is introduced.

## Interpret the diagnostics separately

- **Cross-setting ARI:** compares only identically selected source populations
  and usable vectors. For all methods, it requires at least two represented
  assigned groups in each fit. HDBSCAN noise is excluded from ARI but retained in
  assignment-status transitions and the shared-assigned denominator. Matching
  numeric cluster labels are never taken as evidence of agreement.
- **Coverage and imbalance:** assigned/usable and largest-group/usable fractions
  accompany silhouettes and stability. A high agreement score on a tiny assigned
  subset or a nearly universal group is not a good-policy-model score.
- **Soft models:** equal-count Gaussian mixtures retain aligned responsibility
  comparisons; NMF uses full-vocabulary component cosine and shared-passage mixture
  L1 after equal-rank alignment. These are not the same quantity as ARI. Different
  NMF ranks and hard-versus-soft-component families are not forcibly matched.
- **Representation and display:** full diagnostics remain in each result. The
  comparison separately checks identical score coordinates, identical labels and
  identical UMAP coordinates. Display-only changes should preserve model fitting;
  neither UMAP nor MDS plot separation validates a substantive grouping.
- **Group refits:** the actual schedules, successful fits, assessable ARIs and
  distinct omission sets remain separate. Repeating the same source omissions
  does not produce independent meetings or confidence intervals.

The heatmap is a display of cross-setting ARI, **not** a new consensus partition
or a probability of policy agreement. There is no combined best-method score,
no automatic theme naming, no formal null test, and no new release gate. The
[roadmap](NEXT_STEPS.md) separates robustness checks from later null-calibrated,
held-out-source evidence for nonrandom structure.

## Reproduce and validate

From a checkout with Node 22:

```sh
node tools/test_latent.cjs
node tools/latent_fixture.cjs synthetic-latent-input
python3 tools/build_pages.py new-public-build
```

For actual browser execution in an isolated developer environment:

```sh
npm install --prefix /tmp/latent-qa --ignore-scripts --no-audit --no-fund playwright@1.55.0
/tmp/latent-qa/node_modules/.bin/playwright install --with-deps chromium
NODE_PATH=/tmp/latent-qa/node_modules node tools/test_latent_ui.cjs new-public-build new-browser-validation
```

The UI test also accepts a deployed workspace base URL instead of a local build
path. It creates clearly identified synthetic evidence, never fetches the owner's
private review bundle, and checks actual worker execution, exports, exact archived
replay, two-run comparison, corruption rejection, cancellation, stale results,
small-parent refusal and desktop/mobile overflow. Logs and screenshots are saved
as GitHub Actions artifacts. A successful CI-built-site run is distinct from a
successful test against a deployed public URL.

Version 1.1 also runs the owner's real private twelve-excerpt bundle through
PCA/k-means, LSA/k-means and NMF, archive replay, A/B comparison and browser exports.
The three-parent models remain withheld. Four included excerpts per parent make
the pilot's passage-weighted and equal-parent component summaries coincide;
separate unequal-size fixtures test the case where those weights differ.

Run the private acceptance tool locally with an explicitly selected bundle:

```sh
node tools/check_latent_pilot.cjs BUILT_SITE_OR_URL REVIEWED_BUNDLE NEW_OUTPUT
```

The tool writes private archives, reports, CSVs and screenshots only to that new
local output directory. It does not include private inputs in CI or publish them.
See [executed validation](comparison-refinement-validation.json) for newly run
checks, runtimes and deployment evidence. This is workflow acceptance, not a new
representative corpus or evidence of nonrandom diplomatic structure. All existing
source review remains complete; correction notes are not silently applied to text.
