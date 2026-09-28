# Reproduce this completed run

## What is included

- `emails/`: the five selected EML drafts, self-contained HTML previews, and plaintext.
- `workflow/`: the unchanged generation source, frozen configuration/policies, original engineering fixtures/validation records, six new source-run archives (five selected plus the superseded September 22 version), and the current historical/model/cache snapshot. Old checkpoint-generated reports not used by this task are omitted.
- `execution/selected_runs.json`: authoritative final date-to-run mapping. September 22 selects `uploaded_txt_20260928_regionfix`; the other four use `uploaded_txt_20260928`.
- `execution/adapter/`: R session importer, run wrappers, exact-text checker and rebuild verifier. These are a bounded input extension, not a modification of clustering/projection policies.
- `execution/input_original/` and `provenance/UPLOADED_TRANSCRIPTS_ORIGINAL.zip`: original uploaded source data.
- `execution/normalized/`: national-address objects, all 383 turns, supplemental text, per-turn dispositions and date coverage.
- `execution/normalized_regionfix/`: corrected September 22 administrative region metadata. Original source bytes remain unchanged.
- `execution/aggregate/`: combined method/gate/country/issue tables.
- `execution/validation/`: actual validation from THIS execution. `workflow/validation/` is inherited checkpoint validation, not a new 371-test run.
- `provenance/CHECKPOINT_ORIGINAL_SHA256SUMS.txt`: original checkpoint manifest for provenance only. It is not the delivery manifest, because the working output/state now includes real runs. The top-level SHA256SUMS.txt is authoritative for this delivery.

No interpreter, fonts, API credentials, local dependency-library paths or OS task configuration is distributed.

## Native-R archived rebuild

Use a separate extracted copy. Install R 4.6.1 with its recommended `Matrix` and `cluster` packages (tested versions: Matrix 1.7-5, cluster 2.1-8.2). The explicit minimal offline I/O profile needs no Python, API key or network access.

From this directory:

```sh
Rscript --vanilla reproduce_delivery.R --date=all --run-id=my_verified_rebuild
```

For one date:

```sh
Rscript --vanilla reproduce_delivery.R --date=2026-09-26 --run-id=my_single_day_rebuild
```

The helper invokes the preserved `workflow/rebuild.R`, verifies every input run's manifest and generation-code hashes, then explicitly rerenders the PAM audit figure. The checkpoint's original rebuild entry point omits that last figure call; no original module was patched.

New outputs go to `workflow/output/DATE/NEW_ID/`. Per-file SHA comparisons and logs go to `local_reproductions/NEW_ID/`. Existing run directories cannot be overwritten. A mismatching font/graphics/R environment can change PNG bytes; the helper returns exit 2 rather than claiming exact reproduction. Never edit hashes or policies to bypass a mismatch.

The original five archived rebuilds in this execution reproduced 55 output files byte-for-byte. This is reuse of frozen analyses, not new model fitting or re-adjudication. It leaves historical/model/cache data unchanged.

## Fresh execution versus archived reproduction

The delivered source run used `execution/adapter/run_uploaded.R` and the metadata-corrected September 22 wrapper. They load actual core workflow functions and explicitly select extractive mode with external processing disabled. Their numerical adapters are the unchanged checkpoint R code.

The importer matches source affiliation headings to the country registry, not speaker-name guesses. A source-compatible re-import must verify the uploaded TXT hashes and preserve the turn ledger/exclusions. `normalized` objects store the original import workspace paths; they are archival evidence, not portable fresh-input paths. To make a fresh collection/import on another computer, use a NEW isolated workspace and rerun `prepare_import.R` there before generation. Do not execute the supplied fixed-run-ID driver over completed archives or delete history to make it run.

For model-reviewed narrative summaries, configure the previously documented authorized API or another separately implemented review path locally. That was not performed here. Do not place credentials into chat or shared archives.

## Important acceptance boundary

Drafts are exact-excerpt, review-required products. Automatic source names and allegations are not independently verified. September 28 is missing from the supplied archive, not a day with zero speeches. Native Outlook has not been tested in this environment; browser/MIME checks are not Outlook acceptance. No email has been sent.

The original checkpoint contains a stale internal `2.4.0-d1-hc-only` version label; the actual verified archive is 2.5.0 D1-I4 and contains PAM. Exact source/manifest hashes and method ledgers bind this fact. No version string was silently rewritten.

## Relocated delivery check

The helper above was also executed from this delivery directory for September 26. All 11 compared files were byte-identical, and all 2,488 historical/model/cache files were unchanged. Its archived output is `workflow/output/2026-09-26/relocation_acceptance_20260928`; it is a reproduction, not a sixth source-day result. Logs are in `local_reproductions/relocation_acceptance_20260928/`.
