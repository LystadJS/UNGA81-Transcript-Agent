# Reproduce and validate this checkout

## Use the browser application

Open the [report builder](https://lystadjs.github.io/un/transcript-agent/). No installation or coding is required. Select a meeting or date range, generate a report, inspect its evidence and coverage, then save the transcript JSON to reopen the collection. The [browser guide](docs/BROWSER_ANALYSIS.md) explains the controls and limits. The current application release is **1.14.0**; `site/release.json` is the release record.

## Developer verification

These commands are for maintainers, not application users. From the repository root, with Node.js 22 and Python installed:

```sh
node tools/test_browser_analysis.cjs
node tools/test_meeting_quick_reader.cjs
node tools/test_meeting_quick_reader_context.cjs
node tools/test_meeting_picker.cjs
node tools/test_browser_briefing.cjs
node tools/test_text_units.cjs
node tools/test_object_expressions.cjs
node tools/test_collection_recovery.cjs
python tools/build_pages.py _site
```

The Pages workflow also requires synthetic browser acceptance from `meeting-quick-reader.yml` before deployment. These tests mock public UN responses and do not establish live service availability. A separate weekly or manually dispatched `browser-collection-check.yml` monitors actual UN collection using its fixed October 1 development date. External-service failures remain visible in that workflow without blocking the synthetic release gate. Reserved October 5–6 transcripts remain unopened.

## Optional R / Shiny verification

Run commands from `un/`. Set up the pipeline using `START_HERE.md` and the Shiny
interface using `ui/START_HERE.md`. The themed UI starts with `ui/Start.bat`.

With R and the declared dependencies installed, the included checks are:

```powershell
Rscript --vanilla tests/run_tests.R
Rscript --vanilla tests/run_d1_tests.R
Rscript --vanilla tests/run_i2_tests.R
Rscript --vanilla tests/run_hierarchical_tests.R
Rscript --vanilla tests/run_pam_tests.R
Rscript --vanilla tests/run_shiny_adapter_tests.R
Rscript --vanilla tests/run_i5_tests.R
Rscript --vanilla ui/tests/test_shiny.R
Rscript --vanilla ui/tests/run_tests.R ui
```

Tests may write under validation or regenerate practice outputs; run them in a
separate checkout when preserving the delivered checksums. The UI backend check
includes PDF export, which needs a working supported rendering setup.

The frozen reference artifacts retain their full hashes and original bytes.
R/package/platform differences can prevent reuse of a frozen reference; follow
the pipeline's instructions for a fresh local reference rather than bypassing gates.

`un/SHA256SUMS.txt` is the current package inventory. The similarly named ORIGINAL
inventory and inherited test records are historical provenance.

The previous root reproduction document is preserved at
`docs/legacy/reproduce.md`. Its separate five-email execution bundle is not part
of this integrated Shiny package.
