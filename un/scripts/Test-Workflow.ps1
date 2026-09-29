[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$rt=Get-Content (Join-Path $root 'config\runtime.local.json') -Raw | ConvertFrom-Json
# Build a fresh local reference first: the shipped Linux reference is not a
# promise of cross-platform bitwise identity or matching tokenizer environment.
& $rt.rscript --vanilla (Join-Path $root 'run_daily.R') --source=replay --date=2026-09-23
if($LASTEXITCODE -ne 0){throw 'Local replay failed; do not enable scheduling.'}
& $rt.rscript --vanilla (Join-Path $root 'tests\run_tests.R')
if($LASTEXITCODE -ne 0){throw 'R regression tests failed; do not enable scheduling.'}
& $rt.rscript --vanilla (Join-Path $root 'tests\run_d1_tests.R')
if($LASTEXITCODE -ne 0){throw 'D1 foundation tests failed; do not enable scheduling.'}
& $rt.rscript --vanilla (Join-Path $root 'tests\run_i2_tests.R')
if($LASTEXITCODE -ne 0){throw 'TF-IDF/projection tests failed; do not enable scheduling.'}
& $rt.rscript --vanilla (Join-Path $root 'tests\run_hierarchical_tests.R')
if($LASTEXITCODE -ne 0){throw 'Hierarchical-only tests failed; do not enable scheduling.'}
& $rt.rscript --vanilla (Join-Path $root 'tests\run_pam_tests.R')
if($LASTEXITCODE -ne 0){throw 'PAM tests failed; do not enable scheduling.'}
Write-Host 'Fresh local replay and all five R suites passed. Descriptive geometry gates are not a model-accuracy certificate. Run one nonempty live day and inspect Outlook before installing a daily task.'
