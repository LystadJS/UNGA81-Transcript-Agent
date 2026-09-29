# Historical store — source versions and knowledge cutoffs

## Layout

```text
history/
  SCHEMA.json
  objects/<hash-prefix>/<sha256>.rds     statement + metadata + passages
  labels/<hash-prefix>/<sha256>.rds      separately versioned issue labels
  blobs/<hash-prefix>/<sha256>.bin       archived original source bytes
  snapshots/<hash-prefix>/<sha256>.rds   immutable selected observation index
  commits/000000000001_<hash>/
    commit.rds
    COMMITTED
  .write-lock/owner.json                 present only while a writer owns it
```

This is an append-only local RDS/CSV store, **not an ACID database**. Content hashes, a single-writer lock, commit hash chain and same-directory staging/rename enforce logical commit visibility. No fsync or power-loss durability guarantee is claimed. Keep backups on a reliable local filesystem and avoid concurrent cloud synchronization while writing. Incomplete hidden staging directories are not accepted commits. Unreferenced content after an interrupted write is harmless orphaned storage, not an accepted observation; no automatic deletion is performed.

## Grain and identity

A stored observation is a statement, not just a country/date aggregate. Meeting, statement number, agenda item, genre and its provenance, language/translation, speaker, source/text hashes and exact source sentences are retained when supplied. Missing fields remain unspecified. Identity uses an explicit observation key first, otherwise meeting plus statement number, otherwise source-file/date identity, otherwise a content-addressed fallback that explicitly cannot link changed text as a revision. An unverified identity is never guessed from a speaker name.

Each statement version has stable source-linked passage IDs. Character offsets are checked against the exact original text; unavailable offsets remain NA. Exact UTF-8 duplicate hashes and normalized-text hashes are separate. Near-duplicate clustering is **not implemented** and is labeled unassessed. Original statement records survive aggregation into one regional country readout.

## Two clocks, no retroactive knowledge

The event date/time is separate from local acquisition and store-commit time. Date-only sources do not receive invented seconds. `reported_available_at` from input is retained as provenance, but it cannot backdate trusted acquisition. First-seen means first observed by this store, **not the first time the source was ever public**.

An as-of query requires both a UTC knowledge cutoff and an event-date cutoff. Only committed acquisitions available by the knowledge cutoff and events on/before the event cutoff are selected. Corrected transcripts retain old versions. Reacquiring unchanged bytes preserves their first-seen time; an explicit subsequent reversion to older bytes is represented as a later observation of that version. Late backfills are excluded from what an earlier report could have known.

```sh
Rscript history_tool.R --command=verify --store=history
Rscript history_tool.R --command=query --store=history --as-of=2026-09-26T00:00:00Z --event-date=2026-09-23 --out=output/my_as_of.csv
Rscript history_tool.R --command=labels --store=history --as-of=2026-09-26T00:00:00Z --event-date=2026-09-23 --out=output/label_vintages.json
```

Append `--minimal=true` only for the explicit no-extra-package offline reference profile. Existing export paths are not overwritten. The R API `history_index(..., latest=FALSE)` returns all unique visible versions. The label API returns distinct available label vintages; it is not a gold training-set selector.

## Labels, fixtures and training

Human-adjudicated, model-generated, rule-generated and inherited origins are not merged. This release stores automatic labels only: `is_gold=FALSE`, `training_eligible=FALSE`. Every label binds to the contributing source statement versions and its exact codebook version. Mixed replay labels remain marked; no semantic historical recoding was performed.

Observations are tagged `replay_fixture`, `engineering_fixture` or `observed_input`. Replay/engineering fixtures cannot supply prior-real-observation readiness. Even an `observed_input` record is only a candidate, not an accepted comparable sequence or validated source. Genre/issue/encoder/time compatibility must be established by later adapters.

## Frozen reports versus whole-store backups

A completed run contains its current full statements, raw source archive, as-of index, packets, method artifacts and checksums. That is enough to reproduce its existing email without a live store. The global store retains other historical objects referenced by the index; back up the **whole store** to preserve all historical source exploration. Frozen-report rendering and full historical-store restoration are different operations.

The sample store is under `examples/href`, not `history/`. It contains only the explicitly qualified replay vintage. Running a new daily job creates a separate active store. Rebuilding an archived report does not ingest anything.

## Locks and limits

Inspect the history writer before recovery:

```sh
Rscript history_tool.R --command=inspect-lock --store=history
```

Verify locally that the recorded process on that machine is stopped. Only then use `--command=release-lock --owner-token=THE_EXACT_TOKEN --confirm-owner-stopped=true`. The owner record is moved into a preserved recovery directory; no process is signaled. The separate output run-lock follows the existing documented recovery procedure. The workflow never assumes a saved PID still identifies a live owner on a different machine.

Queries are bounded by `max_store_objects_per_query` (default 100000 visible acquisition entries); raw blobs are bounded by `max_raw_blob_bytes` (250000000). These are operational caps, not measured RAM guarantees. Queries currently scan the commit chain and revalidate selected object hashes. Large histories need an indexed backend and explicit migration rather than silently disabling integrity checks. DuckDB/Parquet are not installed in I1.
