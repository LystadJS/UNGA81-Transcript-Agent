# Operational architecture

The production service is a scheduled batch pipeline with a static read-only browser. Public users browse a published snapshot; only maintainers change collection configuration or dispatch jobs. No public client holds a database write credential or starts training.

```text
Reviewed collection configuration + frozen exclusions
                         |
            Official inventory and transcripts
                         |
          Immutable raw responses + SQLite revisions
                         |
          Source-bound retrieval and local inference
                         |
       Consistent private CSVs + dictionary + manifest
                         |
          Verified private durable snapshot commit
                         |
       Allowlisted public metadata / accepted outputs
                         |
          Public manifest + read-only browser
```

## Production boundaries

| Location | Responsibility |
| --- | --- |
| `src/un_transcript/` | Collection, persistence, snapshots, inference interfaces and orchestration |
| `config/` | Versioned collection selection, issue catalog and model acceptance policy |
| `site/` | Public browser application, archive reader and existing exploratory interfaces |
| `tests/` | Source-free operational contracts and browser acceptance |
| `research/` | Experimental methods, historical protocols and evaluation tooling |
| `un/` | Preserved R/Shiny package and original frozen evidence |

Operational code does not remove research-only guards or reinterpret old annotations. The existing browser and saved-run contracts remain separate versioned interfaces. New production module versions do not imply that a model is accepted or a service is deployed.

## Source and data identity

A meeting identifier, a retrieved source revision, and a transcript segment are distinct objects. Original response bytes are content-addressed; normalization retains locators and hashes. Revisions are immutable, and one current pointer identifies the presently selected source. Repeated ingestion is idempotent. Attribution records distinguish recorded affiliation from verified national capacity and collective statements.

Research exports come from one SQLite read snapshot. CSVs use stable keys and include a generated dictionary, foreign-key relationships, row counts and checksums. Source-bearing CSVs remain private. The current model output joins the current source revision explicitly; old outputs stay reproducible as history.

The five substantive stance values are ordinal. Unclear attribution, abstention, conditional positions, conflicts and unmentioned issues are separate states. They cannot be replaced by neutral or included in a comparison denominator silently. Repeated segments are not independent country-position observations.

## Publication protocol and trust boundaries

Only one operational writer runs at a time. Build and validate a full snapshot before updating its latest pointer. Verify remote repository visibility, snapshot contents and checksums. Retain prior valid snapshots after failed work. Model candidate uploads share writer serialization but do not change the accepted-model pointer.

Private and public storage use different dataset repositories. The public export is an explicit schema allowlist, not a recursive copy of the warehouse directory. Public consumers fetch an `un.archive.v1` manifest, verify partition lengths and hashes, and render data as text. No source field becomes executable HTML.

`site/archive-config.json` has schema `un.archive-config.v1` and a nullable `manifest_url`. The Pages build accepts only a credential-free public Hugging Face dataset URL through `ARCHIVE_MANIFEST_URL`. A null URL means no operational archive has been configured; it does not mean that the UN held no meetings.

## Limits and reproducibility

Scheduled free compute provides no freshness guarantee. Each snapshot states when it was generated and what was collected, missed, excluded or deferred. Storage includes retained revisions and provider history; budget exhaustion blocks new ingestion without deleting the current report. Full historical coverage is never inferred from an empty response or a completed bounded job.

Frozen model artifacts include the upstream revision, tokenizer, weights, input construction, thresholds and evaluation identities. Inference runs locally on the job runner; model loading must not execute remote custom code. Training is a separate human-dispatched operation. A new source/model/issue version creates a new reproducible result rather than rewriting past meaning.
