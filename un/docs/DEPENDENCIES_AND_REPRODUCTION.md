# D1-I4 clustering addition

M07 and M09 both require the `cluster` package in addition to Matrix/stats. M07 uses `cluster::silhouette`; M09 uses `cluster::pam` plus `cluster::silhouette`. Both were executed with cluster 2.1-8.2 under R 4.6.1 in the checkpoint environment. The two adapters share the frozen M02 representation; neither adds Python or a new external service dependency.

# I2 addition

M02/M05/M06 require Matrix (R recommended package); all three were actually executed with Matrix 1.7-5. Dense PCA/PCoA use stats, and the two new PNGs use base graphics. No Python runtime is required. Feature/projection references bind their implementation, R/Matrix/PCRE/locale and policy; mismatches stop rather than refit. Actual installed production versions must be frozen by setup on the user's machine. See D1_I2_IMPLEMENTATION.md for exact scope.

The following preserves earlier dependency guidance:

# Dependencies and reproduction

## D1-I1 foundation scope

The new foundation uses base R and existing adapters; `targets`, DuckDB, Arrow and advanced modeling dependencies remain design candidates, not installed or implemented backends. A runtime dependency ledger distinguishes candidate packages from actual M01 requirements. The original three figures are now audit-only.

## Two explicitly different runtime profiles

**Normal production profile:** R >=4.3 plus `jsonlite`, `httr2`, `xml2`, `digest`, `base64enc`, `renv` and their package dependencies. R 4.6.1 is the execution reference. `chromote` is optional for browser QA. R's supplied graphics packages draw the three static PNGs. PowerShell integrates Windows credentials and scheduling. There is no Python dependency.

**Minimal offline profile:** R 4.6.1, bundled R packages, explicit `--minimal=true`. This uses tested pure-R JSON/Base64 adapters and `tools::sha256sum`, which allows archived replay and normalized local JSON/extractive execution without downloading packages. Live retrieval and fresh model calls are forbidden in this profile. It does not validate the production package backends by implication.

The separate adapters exist because CRAN/Posit downloads were inaccessible in the build container. They are not undisclosed replacements for the requested package-based production implementation.

## First installation and lock creation

`setup.R` installs packages into a private library under `library/R-MAJOR.MINOR/PLATFORM`. It sets `.libPaths` for the workflow and freezes the actual successfully installed set with `renv::snapshot(type="all")`. It records package versions, the R environment and the runtime path. No daily script installs or upgrades packages.

**No installed production lock is bundled in this release.** The build environment could not retrieve third-party packages, so an exact tested production package set could not be generated honestly. After your first successful installation and acceptance tests, retain the produced `renv.lock` with the release. This is the remaining deployment reproducibility step, not a claim that fresh CRAN installations are identical forever.

Restore that actual lock rather than selecting current package versions again:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Setup-Windows.ps1 -Restore
```

A failed restore remains a failure; the script disables substitution of newer packages through renv's retry option. R itself is not installed or downgraded by renv. Preserve the R version separately. Windows normally uses CRAN binary packages; where compatible binaries are unavailable, source installation may require a matching Rtools toolchain. Do not silently switch toolchains or platforms and claim byte identity.

To add `chromote` after freezing, create a separate reviewed copy of the deployment, install the optional dependency and generate a new dependency lock there; preserve the old release/lock. Initial setup supports `-WithBrowserChecks` to avoid that extra change.

## Provenance retained per run

- Original source bytes and SHA-256 manifest.
- Normalized complete text, sentence IDs, original pointers/timestamps when supplied, text hashes, and country/region registry basis.
- Exact prompt/schema/codebook/model configuration, outgoing request bodies without authorization headers, returned response bodies, returned model IDs, token usage when available.
- Structured summary/issue decisions, source-evidence quotes, review decisions and caveats.
- Country/issue/region/edge data behind every figure.
- `checkpoint.rds`, `config_used.json`, `code_manifest.csv`, `R_sessionInfo.txt` on fresh runs, artifact checksums and validation.

Original source files and externally supplied material remain untrusted inputs. Archive checksum validation is an integrity test against the saved manifest, not an externally authenticated signature. Only open/rebuild archives from a source you trust; never deserialize an arbitrary untrusted RDS file.

## Three levels of reproducibility

1. **Evidence reproducibility:** exact archived bytes, text, source identifiers and decisions can be inspected without the live service.
2. **Analytical/output reproducibility:** the saved checkpoint and unchanged release rebuild the CSVs/charts/email without a model call. EML/HTML/text and all three PNGs were byte-identical in the tested same-environment rebuild.
3. **Fresh API reproducibility:** not guaranteed. A new source retrieval can change, an API model alias can change, and a new model response can differ even with the same prompt. Prefer an available model snapshot, preserve responses, and distinguish rerunning inference from rebuilding an archived result.

OS, fonts, locale, graphics device, R/package versions, MIME timestamps and code all affect exact bytes. Default fresh runs intentionally have a new preparation timestamp. Use a fixed `--prepared-at` only for controlled reproduction, never to disguise when a live product was generated.

## Rebuild the included completed example

```powershell
$rt = Get-Content .\config\runtime.local.json -Raw | ConvertFrom-Json
& $rt.rscript --vanilla .\rebuild.R `
  --input=output/2026-09-23/d1_i1_reference --run-id=local_archived_rebuild
```

Without package setup, use R 4.6.1's actual executable and append `--minimal=true`. The script verifies the original run's saved checksums and current generation-code/asset hashes before using its checkpoint. It creates a new output directory, never overwrites the original, and writes `reproduction_check.json` with the EML byte comparison. It makes no network request.

A separately archived future completed run uses the same command with its real input path and original workflow release. `rebuild.R` rejects a code/asset mismatch; restore that release rather than editing the manifest to suppress the warning. A byte mismatch after a legitimate platform change is reported and requires inspection; semantic agreement alone does not establish byte identity.

## Deployment boundary

The release is standalone. It reads the official documented UN endpoint structure and does not require GitHub credentials or a clone of another repository. It has not been pushed to GitHub. Browser QA can use the optional native-R `chromote` script. Independent Python tooling was used during development to inspect MIME/rendering; no Python file, dependency or invocation is part of the shipped daily workflow.
