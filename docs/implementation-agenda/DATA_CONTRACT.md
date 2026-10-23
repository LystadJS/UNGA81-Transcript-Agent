# Historical store and browser export contract (v1)

Status: executable SQLite prototype and synthetic validation. No hosted database,
historical source ingestion, operational scheduler, or empirical model acceptance
is implied. The maintainer runs this component; readers need only the browser.

## Identity and versions

`research/issue_history/store` uses Python standard-library SQLite. `IssueStore`
applies schema version 1 transactionally and rejects a newer schema. Before a
future migration, `backup(path)` creates a consistent rollback copy; restoring
that copy requires closing the live connection and replacing the database file.
There is no destructive automatic downgrade.

`stable_id(kind, *identity_parts)` hashes canonical UTF-8 JSON. Adapters must use
source-family-native persistent identities, including meeting part or resolution
version where required. Display names and row offsets alone are inadequate IDs.
`upsert_source` returns its canonical metadata revision hash. Source revisions
remain immutable. The content hash is separately supplied and must be SHA-256.
The metadata digest does not authenticate the source's wording or accuracy.

Sources require `id`, `published_date` (ISO date), `body`, `family`, `url`,
`content_hash`, and `access`: `private`, `reference_only`, or `public_approved`.
Metadata changes create a revision and invalidate dependent artifacts. Repeated
identical imports produce no extra revision. Source-bearing content may remain
private in the database; explicit publication approval is required for export.

Observations require `id`, `source_id`, `source_revision`, `country`, `date`,
`policy`, `context`, `stance`, `review_state`, and `attribution`. Stances are
`support`, `oppose`, `qualified`, `conflicting`, or `unknown`. Review states are
`assistant_provisional`, `owner_confirmed`, or `unreviewed`; attribution is
`national`, `collective`, or `unclear`. Storing a collective observation does not
authorize assigning it to the affiliated country in a country opinion statistic.
Canonical country identifiers should be used by production adapters.

Votes require the same identity/date/policy/context fields and `vote`,
`resolution`, `resolution_version`, `stage`, and `eligible` (boolean or null).
Recorded yes/no/abstain/absent require eligibility true; not_eligible requires
false. Stages are adopted_resolution/draft_resolution/amendment/procedural.
Categories are `yes`, `no`, `abstain`, `absent`,
`not_eligible`, and `unknown`. Consensus adoption is never converted to individual
yes votes. Resolution includes its version; stage separates amendment,
procedural, committee and final-adoption decisions. Policy/context binding needs
source verification before a vote can be used as issue evidence.

Membership intervals store country/body/start/end/eligible, with inclusive dates,
open-ended intervals permitted, and overlapping intervals rejected. They are not
inferred from a country's presence in the transcript collection.

`put_artifact(kind, payload, dependencies)` materializes model/panel/report/cache
artifacts. Payload must include the caller's snapshot, ontology, extractor,
method and evaluation versions as applicable. Dependencies reference source,
observation or artifact IDs. Corrections invalidate transitively, preserving
unrelated artifacts. The engine must check artifact validity before reuse.
Prior exported snapshots remain reproducible; mutable evidence rows in the
working store are not a substitute for the frozen report snapshot.

## Read-only browser interface

`export_bundle(directory, snapshot_id, coverage=None)` emits a content-addressed
shard, an immutable snapshot manifest and atomically switches `manifest.json`
only after content is present. Reusing a snapshot ID for changed content fails.

Manifest schema: `un.issue-history.manifest.v1`, `snapshot_id`,
`shards: [{id,url,sha256,bytes}]`, and `counts` for sources/observations/votes.
The default exporter emits one `all` shard for small integration fixtures.
`partition=True` groups policy/year/body, with coverage-only source shards and
separate eligibility shards. `max_rows` (default 1000) and `max_bytes` (default
2 MB) bound each shard; a single oversized evidence unit fails before manifest
publication. Source references may repeat identically across shards; evidence IDs
do not. Manifest entries include policy/year/body for selective client loading.
The refresh runner selects bounded partitioning. Export currently materializes
rows in maintainer memory; streaming export is future large-store scale work.

Shard schema: `un.issue-history.shard.v1`, `snapshot_id`, `sources`,
`observations`, `votes`, `memberships`, `coverage`. Source fields are restricted
to ID/revision/date/body/family/URL/content hash. Observation and vote fields use
the required allowlists above. Source text, audio, private notes and arbitrary
metadata never export. Only current revisions marked `public_approved` and their
current evidence export; evidence tied to superseded revisions is withheld.
Coverage accepts only status/expected/retrieved/verified/unavailable/excluded.
Coverage totals must be established by the ingestion runner, not guessed.

SHA-256 covers the exact shard bytes. Browser clients must reject damaged
shards, inconsistent snapshot IDs, incomplete fetches and incompatible schemas,
and retain their previous valid snapshot. No source approval is granted by the
exporter itself. A synthetic fixture is not a ten-year source archive.

## Executed checks

Optional source `countries` lists preserve explicitly recorded affiliations,
including countries with no detected positions, with source date/body.
Optional observation `unresolved` booleans and `qualification_codes` identifiers
preserve exclusions and qualification categories without quoted wording.

## Maintainer refresh

`research.issue_history.refresh.runner.refresh` consumes one bounded approved
input snapshot through the ingestion adapter and durable checkpoint. It publishes
only after all rows complete without quarantine, preserving the previous manifest
on partial batches, quarantined rows or failures. Health state contains counts,
status, source-side watermark and last published snapshot, never source text or
exception messages. `transcript_sink` maps adapter records to canonical store
revisions and optionally materializes deterministic extracted observations.
Access defaults to private; publishing requires explicit caller approval.

The input snapshot is immutable across resumes. Source-side watermark is supplied
by the approved feed; successful processing alone cannot establish freshness.
A private checkpoint contains diagnostic reasons and must not be published.
The GitHub `Historical issue store checks` workflow runs synthetic engineering
checks only. No remote feed, credentials, production refresh schedule, database
host or ten-year coverage is configured. Production rollout requires a verified
feed/access decision, persistent database volume, serialized refresh scheduling,
private checkpoint storage, health alerts and static-bundle publication. Before
upgrading, back up the database and retain the last valid manifest/content files;
rollback points readers to that exact earlier immutable manifest.

## Combined validation

On 23 October 2026 a single synthetic local run on Windows, Python 3.11.9,
8 logical processors, with 1000 sources and 1000 observations produced 20 shards
(642490 bytes). Cold ingestion took 4.192 s; repeated idempotent ingestion
0.473 s; cold export 0.148 s; repeated export 0.135 s. Run
`python -m research.issue_history.store.benchmark --size 1000` to repeat.
These measure ledger/export work only, not browser latency, network transfer,
real-source extraction, model fitting, report rendering or ten-year scale.
The cross-store partition test invokes the actual browser query module and
checks matching dates/body/policy against the exporter fixture's expected rows.

`python -m unittest research.issue_history.store.test_store -v` exercises
canonical identities, idempotent imports, immutable source revisions, stale
evidence rejection, transitive and targeted invalidation, source/text privacy,
hash verification, frozen snapshot identity, eligibility overlap, vote
categories, and rollback-copy readability. These are engineering checks using
invented metadata, not empirical extraction/model accuracy measurements.
