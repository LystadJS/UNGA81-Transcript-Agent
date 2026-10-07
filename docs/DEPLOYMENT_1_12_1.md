# Browser 1.12.1 — deployment verified

Both requested workflows are implemented and deployed: saved-run/parent-excerpt/
reusable-settings comparison, and date-first individual-meeting analysis.
The unsupervised-learning roadmap has been updated in `NEXT_STEPS.md`.

Application source release: `f7f1fa623ba3d588d51eec0ac0a8febb2decc288`.
Public website release: `e4d6e476961aafd8ce021542786f900004d883c4`.
Browser engine: `browser-descriptive-1.12.1`.
Comparison engine: `latent-comparison-1.0.0`.

## Verified completion

| Check | Recorded result |
|---|---|
| Primary numerical/source regression, comparison and meeting suites | Passed |
| Primary desktop/mobile browser acceptance | Passed |
| Primary GitHub Pages deployment | Passed, run 37652096438 |
| Existing public-only mirror synchronization and all 134 manifest hashes | Passed; repeated synchronization made no changes, run 37652186858 |
| Deployed website asset verification | All 13 selected application/navigation asset hashes matched |
| Deployed comparison browser workflow | Passed |
| Deployed individual-meeting browser workflow | Passed; synthetic inventory clearly distinguished from live sources |
| Separate real UN inventory and selected-meeting collection | Passed as a required release step |

The final deployed-website checks above are recorded in
[release run 37652343847](https://github.com/LystadJS/LystadJS.github.io/actions/runs/37652343847).
Primary source deployment and its prerequisite suites are recorded in
[Pages run 37652096438](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/37652096438).
The full numerical/browser and live-source scope is described in
[the release acceptance record](RELEASE_1_12_1.md).

## Use

Open the [existing report builder](https://lystadjs.github.io/un/transcript-agent/).
Choose **One individual meeting**, enter a date, select **Find meetings**, select
one listed meeting, then generate the analysis/report. Leave Topic blank to retain
all eligible English passages in that meeting. Pending availability, coverage and
source failures remain visible; no other meeting is substituted.

Use **Compare latent structure** in the main navigation for
[the comparison workspace](https://lystadjs.github.io/un/transcript-agent/latent.html).
It supports local source/review imports, saved-run replay, parent/excerpt analysis,
reusable settings plans, source-linked visualizations, JSON and CSV diagnostics,
and standalone visual HTML exports.

## Remaining boundaries

The real private twelve-excerpt owner bundle was not rerun; synthetic tests verify
its data contract and the intended three-parent withholding behavior. D1 adapters,
publication gates, original text and owner review choices remain unchanged.
One meeting does not supply independent meeting-level replication. Sensitivity
and cross-setting agreement are not formal evidence of nonrandom policy alignment.

The separate portfolio root-navigation suite recorded two URL timeouts (12 other
checks passed) in run 37650672254. Those root files were outside this change and
were not repaired. This limitation does not describe the UN feature-specific
browser checks, which passed locally in CI and on the deployed website.
