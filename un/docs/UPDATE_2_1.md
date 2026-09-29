# Release 2.1 — fixed topics and regional readouts

## Changes

**Permanent issue order:** Iran, Cuba, Ukraine, AI. These four separate categories are never dropped for having zero mentions. Nine additional broad categories remain, for 13 default categories. All categories are non-exclusive. The broad Middle East and AI & digital categories do not establish the narrower Iran and AI codes.

Fresh narrative runs review every country against every category using the complete source text and a separate review call. The fixed topics are administrative priorities, not political ratings, stance labels, or forced topics in country prose. Model schemas are bound to the active codebook. The codebook/prompt/version changes invalidate old model caches rather than recycling incompatible decisions.

**Region order:** Africa; Asia-Pacific; Europe & Eurasia; Near East; Western Hemisphere. Country names are alphabetized within each. Existing source-region assignments are retained; these are analytical regional groups, not new continent or UN electoral classifications. Unmapped countries appear last. Configure regional sequence in `config/config.json` under `display.region_order`.

The HTML email, plaintext, audit, output country table and regional heatmap follow this same ordering. Regional headers show each group's country count. The permanent four-row watchlist appears near the executive takeaway. The first four chart rows remain fixed; additional chart rows sort by prevalence. All four network nodes remain even when zero or unresolved.

**Uncertainty:** Present, absent and uncertain are different states. Zero observed presence with unresolved countries is never described as established absence. When no country text is available, the watchlist says “No country texts.” Network edges now require complete decisions for the pair across the full corpus; unresolved nodes are retained but their edges withheld. This avoids positive-only scans producing artificial high-overlap links.

## Archived example: do not confuse replay with fresh review

The September 23 example preserves all original source files, 155 inherited summary points and all ten original issue decisions. It adds provisional full-text lexicon scans for Iran, Cuba and AI. No-match is unresolved, not absent. Ukraine retains its original broader v1 decision in this example; fresh runs use the current Ukraine definition. Original and current codebooks, row-level versions and exact supporting matches are preserved separately.

This is a reproducible display/example update, not a new semantic review of all historical speeches. Do not combine its mixed-version topic values with fresh model-coded days as a homogeneous series. For a fully recoded historical day, run local or live narrative mode with the v2.1 codebook and your authorized API setup. No paid model call was made during this update.

## New installation

Follow `START_HERE.md`. No new R dependencies or Python requirement were added. The default still generates unsent drafts only.

## Existing installation

Keep the v2.0 directory and all old run archives intact; old archives require their matching code release for exact reproduction. Extract v2.1 into a separate directory.

Transfer authorized non-secret settings (model choice, sender/recipients, scope and limits) into the new config. Keep the new `display` settings and codebook. Do not copy old `runtime.local.json`, `library_path.txt`, `output/latest.json`, or old release code into the new folder: those can point at the wrong installation. Do not share `.secrets` or API keys in chat.

To restore the same package versions, copy your locally generated `renv.lock` to the new root and run `scripts/Setup-Windows.ps1 -Restore`. Without an existing lock, run normal setup. Setup records paths for this new installation. Configure the key locally using `scripts/Set-ApiKey.ps1`.

Run `scripts/Test-Workflow.ps1`, then a nonempty live-day acceptance test and an Outlook-native visual check. Only after those pass, disable the old scheduled task and install the new task from the new directory. Nothing in this release changes your existing task automatically.

## Reproduce the shipped example

With normal installed dependencies:

```sh
Rscript --vanilla run_daily.R --source=replay --date=2026-09-23
```

With the reference R 4.6.1 and explicit no-extra-package offline adapters:

```sh
Rscript --vanilla tests/run_tests.R --minimal=true
Rscript --vanilla run_daily.R --source=replay --date=2026-09-23 --minimal=true
```

To rebuild the included completed reference without retrieval or model calls:

```sh
Rscript --vanilla rebuild.R --input=output/2026-09-23/r_2_1_validated --run-id=my_rebuild --minimal=true
```

Byte-identical reproduction depends on matching R, graphics/font environment and saved run inputs. Live model outputs are not promised to be byte-identical across new calls.
