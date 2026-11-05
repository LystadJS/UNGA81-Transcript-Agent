# Daily collection and reproducible source records

Browser release 1.37.0 opens on today's calendar date in `America/New_York`, regardless of the device timezone. **Today**, **Yesterday**, the date pickers and **Last 7 days** choose dates without changing the meeting scope. Changing scope preserves the chosen dates. The General Debate shortcut remains an explicitly historical September 22–28, 2026 preset.

The default daily scope includes all meetings returned by the date-specific UN transcript inventory, across bodies and committees. It does not establish complete coverage of UN proceedings. Only usable English transcript passages enter the briefing. Single-meeting mode has its own date and meeting selector; range shortcuts are disabled while that mode is selected.

## Availability and partial briefings

The report shows the collection check timestamp in UTC and four source-availability counts:

- **Available:** a transcript response contains segment data, including non-English or empty responses. Collection results separately distinguish collected, non-English and empty material.
- **Pending:** the inventory explicitly says pending/processing/queued/preparing, or advertises a transcript whose response does not yet contain segment data.
- **Unavailable:** no transcript is listed and no explicit pending cue is supplied. This does not imply that publication will occur later.
- **Failed:** a requested transcript could not be retrieved or validated. Inventory failures are shown separately by date because their missing meeting count is unknown.

Successfully collected passages remain analyzable when another source fails. A partial report preserves missing-source warnings and never treats missing material as evidence that a topic was absent. Cancellation retains completed source batches for saving and subsequent analysis; it does not release an unfinished report.

**Retry collection gaps** verifies inventory and revisits gaps within the original meeting selection. **Check for newly published transcripts** also admits newly listed meetings within the original dates and scope and rechecks empty transcript responses. Both preserve successfully collected responses without fetching them again. They do not update already collected transcripts to later revisions; generate a fresh collection when that is required. Entries missing from a subsequent inventory remain visible rather than silently disappearing.

## Saved evidence and versions

Save transcripts to retain original collected passages, inventory snapshots, collection coverage, report filters and `un.browser.source-provenance.v1` source records. Live response records retain the source URL/identifier, retrieval time, SHA-256, a content-addressed `sha256:…` version, raw UTF-8 JSON and exposed HTTP ETag/Last-Modified metadata. A content hash is not a source-issued publication revision. Browser CORS rules may prevent access to the HTTP metadata.

UTF-8 decoding rejects malformed bytes and preserves a leading BOM for hashing. Saved passage records retain the source version, original segment pointer, text hash and raw-response hash. On import, the browser verifies saved raw-source hashes, passage text hashes and passage membership in the saved raw transcript. Reopening the saved collection does not fetch current UN sources. Hashes establish integrity, not source authenticity or independent verification of imported country metadata. Legacy collections without this manifest retain their earlier text-hash checks and do not gain retroactive raw-source verification.

The collector bounds its UTF-8 serialized source/record working payload at 24 MB, leaving room for collection metadata within the existing 30 MB import limit. Oversized additions produce an explicit source failure while preserving completed source batches. Existing limits on dates, meetings, passages and per-response size still apply. Save HTML to preserve the rendered report and analysis JSON to retain calculations and the engine version; rerunning saved inputs with a later engine can produce different interpretations.

## Engineering validation

The New York date tests cover midnight, DST transitions, leap days and year boundaries. Synthetic collection checks cover incremental retry, explicit refresh, inventory outages, disappeared entries, cancellation, pre-request tamper rejection, UTF-8 BOM hashing and malformed UTF-8 rejection. Browser acceptance covers date controls, source states, partial output, refresh/retry, visible timestamps, offline replay and altered source/passage rejection. Existing saved-filter and recovery-browser tests also run. These checks do not establish live UN availability, source completeness or political measurement accuracy. No reserved transcripts or external AI services are used.
