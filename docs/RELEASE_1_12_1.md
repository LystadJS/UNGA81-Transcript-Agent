# Browser 1.12.1 — comparison and individual-meeting release

## Delivered

The report builder now supports date-first individual-meeting selection. Choose
**One individual meeting**, enter a date, select **Find meetings**, choose a meeting,
and use the existing analysis/report controls. Only the selected meeting's
transcript is retrieved. Its identity, date, title and coverage are retained in
reports and exports. Pending transcripts remain visible; changed or failed
inventories are not silently replaced by another meeting.

The separate **Compare latent structure** workspace supports exact serialized
saved-run replay, two-run comparison, matched-cohort full-parent versus reviewed-
excerpt analysis, and reusable bounded settings plans. It retains source hashes,
review lineage, coordinates, model settings, assignment coverage, refit counts,
source-linked maps, ARI comparisons and diagnostic/visual exports. Parent-balanced
composition remains a summary, not a reweighted model fit.

[Report builder](https://lystadjs.github.io/un/transcript-agent/)
· [Comparison workspace](https://lystadjs.github.io/un/transcript-agent/latent.html)
· [Meeting guide](INDIVIDUAL_MEETINGS.md)
· [Comparison guide](LATENT_COMPARISON.md)
· [Unsupervised roadmap](NEXT_STEPS.md)

## Acceptance

[Canonical-route acceptance run 37651586467](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37651586467)
passed before source correction commit `f7c8bd91bb8edac61f2c8132fbe64864a517633c`.
It reran the ten existing analytical/source suites, 19 comparison checks, 12
individual-meeting checks, 11 comparison-browser checks and eight meeting-browser
checks. Browser checks used Chrome 154.0.8037.97 on Node 22.23.3, at 1440- and
390-pixel viewport widths. No JavaScript errors or page overflow were recorded.
The comparison browser made no uploads or external requests. These browser tests
use clearly identified synthetic evidence and inventory responses.

The **separate live UN source check** passed at 16:23:14 UTC on 7 October 2026.
For 24 September 2026, it listed 44 inventory meetings and selected
`hrc/63/25`, “25th Meeting - 63rd Session of Human Rights Council.” Only that
meeting was collected: 201 English source segments, 199 retained after the
existing deduplication/filtering path. Source timestamps were flagged by the
existing collector; that warning remains in the coverage record. This is source
collection/descriptive-analysis acceptance, not a substantive interpretation.

The initial live probe exposed an incorrect asset-only meeting-ID restriction.
The correction accepts safe, verified multi-segment UN inventory routes, including
HRC and treaty-body records, while retaining traversal, query and external-URL
rejection. Regression fixtures now exercise these routes. The initial failed live
probe is not relabeled as a successful test.

Acceptance artifact: `canonical-meeting-validation`, GitHub artifact 11497055621.
Deployed-site verification and the final mirror synchronization are separate
release steps and must be confirmed from their respective workflow results.

## Boundaries and unresolved items

The real private twelve-excerpt owner bundle was not rerun in this phase. Its
three-parent baseline remains intentionally withheld by the existing four-usable-
observation minimum; six-parent engineering fixtures validate the supported path.
Existing owner review choices, original transcript text, audio correction status,
D1 adapters and O1–O5 publication gates are unchanged. No formal null test, semantic
encoder, political-stance model or new substantive diplomatic finding is implied.

The roadmap now prioritizes the expanded passage/weighting contract, semantic
representation comparisons, explicit null-reference and held-out-source validation,
and comparable longitudinal actor/theme analysis. Agreement between settings is
not proof of nonrandom diplomatic structure.

Separately, the portfolio repository's broad website regression run 37650672254
recorded 12 passes and two root-navigation URL timeouts in desktop/mobile tests.
Those root portfolio files were not changed by this UN mirror release. The
navigation timeout was not repaired here; the feature-specific UN browser suites
are separate and passed. This report does not claim all portfolio CI is green.
