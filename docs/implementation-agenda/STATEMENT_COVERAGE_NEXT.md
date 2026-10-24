# Statement coverage reconciliation: implementation boundary

The metadata-only reconciliation boundary below is now implemented; see STATEMENT_COVERAGE_ACCEPTANCE.md. Native meeting/speaker identity and real source acquisition remain separate next steps.

A statement archive needs a meeting-level coverage ledger independent of position extraction and vote coverage. The current `ingest.discovery.transcript_inventory` validates one official inventory page for one day. It does not reconcile all pages or all dates. `refresh.runner.refresh` reports completion of supplied input rows; this is not verified meeting or archive completeness.

## Single-agent implementation boundary

Add a pure private reconciliation module and source-free tests accepting pinned inventory-page metadata, explicitly declared requested dates and bodies, and separate retrieval/hash/extraction receipts. Require page/date identity, stable totals, duplicate detection, terminal-page evidence and exact meeting IDs. Missing pages or unqueried days remain unknown, including a day that returns no entries without independently established catalog completeness. Do not fetch or open transcript wording in this step.

Report catalog-advertised meetings, advertised transcript availability, retrieved artifacts, verified content hashes and extraction completion separately. A missing explicit position is not a missing transcript, and a missing transcript is not opposition. Count distinct meetings independently of speaker records, countries and positions. Preserve GA committee distinctions and recorded versus derived body metadata; avoid claiming coverage beyond the declared source/window.

Before production acquisition, preserve native meeting linkage and distinct speaker-record identity. The current transcript sink stores only date/body/family/URL/text hash/country metadata; it does not retain native meeting ID, raw artifact hash or the complete attribution metadata. A caller reusing a meeting-level source ID across different speakers could replace the current source revision instead of representing distinct statement records. A new production adapter must enforce a deterministic, provenance-bound speaker-record identity and preserve its parent meeting relation. Historical sources and dependency pins must be explicitly revalidated before migration; do not silently change accepted ingest/cache dependencies.

No acquisition, public snapshot, owner-confirmed annotation or empirical model acceptance follows from coverage engineering. The 37 reserved meetings remain unopened. Original collections, cursors, votes and statement evidence channels remain separate and unchanged.
