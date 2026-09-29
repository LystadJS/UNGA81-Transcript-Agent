# Reproduce and validate this checkout

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
