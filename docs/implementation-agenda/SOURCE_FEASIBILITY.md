# Source feasibility and ingestion status

Checked official discovery sources on 23 October 2026. This is a feasibility inventory, not certification of complete downloaded coverage.

| Family | Official reference | Established scope | Unverified work |
| --- | --- | --- | --- |
| GA adopted-resolution recorded votes | [UN Library guide](https://research.un.org/en/docs/unvoting/undl), [dataset catalog record](https://digitallibrary.un.org/record/4060887?ln=en) | Official downloadable dataset and voting records. Catalog description extends through the main part of the 80th session in December 2025. | Retrieve exact licensed/permitted bytes, pin revision/hash, inspect headers and reconcile membership and date coverage. 2026 freshness remains unverified. |
| SC adopted-resolution votes | [UN voting information](https://www.un.org/en/library/page/voting-information), [datasets inventory](https://ask.un.org/faq/432839) | Official adopted-resolution voting records and dataset family. | Fetch and pin actual schema, validate eligibility and changing membership. |
| SC draft-resolution votes | [Security Council draft voting records since 1992](https://main.un.org/securitycouncil/en/content/voting-records-1992) | Separate official draft-resolution voting family from January 1992 onward. | Resolve dataset download contract and distinguish failed drafts from adopted resolutions; do not infer this coverage from adopted-resolution records. |
| GA committee/amendment/procedural votes | [UN finding-votes guide](https://research.un.org/en/docs/find/voting) | Main adopted-resolution collection does not establish complete committee, amendment or procedural coverage. | Separate adapter and coverage discovery required. |
| UN transcript statements | Existing source-bound corpus schema and app collector | Normalized records can preserve dates, speaker affiliations, URLs and source hashes. | No verified ten-year access/format/permission inventory is claimed; normalized fixtures are not proof of remote availability. |

The implemented `research/issue_history/ingest/adapters.py` accepts a deliberately strict normalized transcript JSON format and a normalized vote JSON format. It does not pretend to parse an uninspected remote CSV header or scrape a ten-year archive. Transcript text hashes are verified; metadata changes produce a new revision. Documents are rejected from the UN-statement channel. Vote categories preserve yes, no, abstain, absent, not eligible and unknown; consensus cannot become an individual yes. Stage/version and eligibility must be supplied explicitly.

The bounded runner uses an immutable input snapshot, explicit cursor, batch limit (maximum 500), retry counts, metadata-only quarantine entries and coverage reconciliation. The caller must persist its returned checkpoint and provide an idempotent transactional sink. Network access and scheduling are intentionally outside the runner. No automatic background ingestion, source permission approval, complete historical database, or scheduled service deployment is represented as operational.

Validation uses source-free synthetic fixtures only. The 37 reserved transcripts were not opened. No private source text, review ledger or raw model output is added to this public repository. Official links establish discovery scope, not permission to republish original material. Public bundles still require explicit per-source `public_approved` status from the authoritative store.

Next executable unit: download one permitted official vote dataset into a private staging directory, pin its exact bytes and schema, implement its specific header adapter, reconcile one bounded year/body shard, then feed validated normalized rows through the runner. The same process repeats per source family.

## Bounded catalog discovery check

The official [Ask DAG dataset inventory](https://ask.un.org/faq/432839) was directly read on 23 October 2026. It links GA vote catalog record 4060887 and SC vote catalog record 4055387, describes periodic updates and CSV/metadata availability, and states non-commercial use with attribution. Both linked catalog fetches returned HTTP 403 in this environment. No block was bypassed, no actual CSV header or downloadable bytes were verified, and no remote-specific parsing adapter is claimed.

`ingest/discovery.py` freezes those verified catalog links and can inspect a bounded supplied metadata page for same-host CSV/JSON/XML candidates. Candidates remain unverified pending permissions/schema/hash review. It does not fetch, guess filenames or assert an operational dataset connection. This keeps B3/B9 remote acquisition incomplete while allowing deterministic engineering tests to proceed.

Vote-to-store mapping now verifies exact resolution ID, revision and stage against a separately supplied policy binding. It preserves country, explicit eligibility, abstention and resolution version through SQLite and public-bundle export in a synthetic integration test. D3/D4 trained-classifier and semantic-extractor prerequisites remain unmet: no accepted labeled benchmark, resource-approved production checkpoint, or independent calibration evidence exists. The audit-only tiny checkpoint is not promoted.

## B9 acquisition blocker and permitted alternative

B9 cannot progress from discovery to verified real-year ingestion in this environment because both official Digital Library catalog requests returned HTTP 403 before download links, schema or files could be inspected. This is an access result, not evidence the datasets do not exist. No anti-bot bypass or substitute unofficial dataset is authorized by this implementation. A maintainer can use the normal official catalog interface where access is available, obtain the permitted CSV plus metadata, record the download URL/date/licensing and SHA-256, and place it in private staging. The next agent can then inspect that exact file, implement the actual family header adapter and process one bounded, reconciled year/body shard. No secret or source-bearing staging file should enter the public repository.

## Actual transcript inventory probes

On 23 October 2026, four bounded metadata-only HTTPS requests used the app collector's actual endpoint, `/en/meetings.json?date=YYYY-MM-DD&xlang=1&page=1`. No transcript JSON/text endpoint was opened, and no reserved October 5–6 source was requested. Each response fit within 256 KiB and reported no further page.

| Requested date | Inventory total | Advertised transcript availability | Relevant body metadata |
| --- | ---: | --- | --- |
| 2016-09-22 | 0 | No entries returned; historical absence is not verified | None returned |
| 2020-09-22 | 0 | No entries returned; historical absence is not verified | None returned |
| 2025-09-23 | 41 | 5 true, 36 false across all inventory entries | GA plenary 1 with advertised transcript; SC 2 both without advertised transcript |
| 2026-10-01 | 13 | 13 true across all entries | GA plenary 1; Third Committee 2; Fourth Committee 1; Second Committee 1 |

Response SHA-256 values: 2016 and 2020 `2c8debb987d7d4ecbcebea18e41f984e6abbd1a7879e00b0ccc17d1dde013217`; 2025 `e22715c4190ca6464eb4f97fd0c85001cf935498b6d2a43b9e7dc8367c648298`; 2026 `2cdf6c734ede94a4bd5178a0c9d8c3482d8500d7435875ee3f917a3f2c55c4f6`.

These probes establish recent inventory access and its actual field format, not continuous ten-year transcript availability. Zero entries on two historical dates cannot establish that no UN meetings occurred. Advertised transcript flags do not verify transcript bytes, language, speaker metadata or permission to redistribute. The sampled 2025 SC meetings are a concrete source-availability gap even though meeting metadata exists.

`ingest/discovery.py:transcript_inventory` now implements this inspected inventory format with byte/page/count bounds, date and duplicate checks, exact source-link identities, canonical body mapping and separate advertised-versus-verified availability. It returns metadata only and performs no fetch. Additional archive families, coverage reconciliation, language and actual source verification remain necessary before a ten-year policy database is operational.

## GA actual-file access and adapter acceptance (supersedes GA catalog blocker)

Later on 23 October 2026 the normal browser catalog interface exposed version 6 and its exact CSV/metadata links. The earlier 403 result was specific to that request path and no longer blocks this GA family. The official metadata was downloaded to private staging (SHA-256 `9bc00a25eb56e882f92beff45523b08aab4b675fc7e1bfd7d9a9588149525242`). It describes 954,382 Member-State/resolution entries through resolution 81/1, 17 September 2026, published 15 October 2026. Recorded votes on adopted resolutions are covered; failed drafts and individual paragraphs are explicitly excluded.

The exact [official CSV](https://digitallibrary.un.org/record/4060887/files/2026_10_15_votes_ga.csv) was downloaded privately: 368,130,256 bytes, SHA-256 `8c2e1c6aaf427c685835e7fdf74833375ed711a28d1ee9e393163903e99e11a5`. The initial 250 MiB transfer bound stopped the first request. A documented 400 MiB bound and server-confirmed HTTP 206 byte range completed the same verified file. No third-party mirror or access-control bypass was used. Original CSV, metadata and normalized real vote rows remain outside this repository.

The actual header has 20 fields, including `undl_id` in addition to the metadata dictionary's fields. `ingest/ga_votes.py` freezes this header, verifies official voting-record IDs/links and adopted resolution symbols, and preserves historical country names and three-letter codes. Y maps to yes, N to no and A to abstain. X means non-voting: it maps conservatively to unknown with eligibility null, never absent or not eligible. Blank/unrecognized symbols are rejected. Additional vote notes remain flagged for review. Version `as_adopted` identifies the adopted symbol; dataset version 6 is separate provenance.

One bounded 2025 GA sample of 500 normalized rows was processed privately with zero policy bindings; the source cursor reached CSV record 892,929. The sample is incomplete and is not a representative policy sample. No title/subject keyword created a humanitarian policy binding. `iter_batches` provides a single streaming pass with batches of at most 500 and explicit record ordinals, avoiding a full source scan for each batch. Full-file row-count/year reconciliation and persistent store ingestion are separate maintainer acceptance records. Terms remain United Nations copyright, non-commercial use with attribution to the UN Dag Hammarskjold Library, with source metadata and applicable UN terms retained.

## Canonical country and resolution identity correction

The actual GA CSV records country names in uppercase. Adapter version `ga-v6-csv-3` now joins the explicit `ms_code` to `un/config/countries.csv` by exact ISO3 code. It preserves the original historical `ms_name` separately, plus the mapping status and registry SHA-256. No fuzzy name matching or title-casing establishes identity. USA maps to United States, NGA to Nigeria and PLW to Palau. Unknown codes retain an explicit unmapped identity; even a familiar raw name does not establish a mapped country. This join does not establish historical UN membership or continuity of states.

A complete symbol-only scan within 24 October 2016–23 October 2026 found adopted-resolution subparts with bracketed letters and space-letter suffixes. These exact symbols remain distinct; no bracket or suffix is stripped. It also found 193 rows for `A/DEC/80/506`, an adopted decision. Those rows are retained under the explicitly separate `adopted_decision` stage; they never enter an adopted-resolution comparison baseline. Both normalized vote and policy-binding validators require an exact `A/DEC/` source symbol for that stage, and forbid recoding a decision as an adopted resolution. No issue binding is inferred. Reingestion must rebuild or invalidate the earlier raw-name materialization to avoid parallel duplicate identities. Private source bytes and intermediate normalized rows remain outside the public repository.

## Whole-file GA publisher-total reconciliation

A later read-only streaming pass over the verified compressed source scanned all 954,382 rows, selecting 205,738 rows dated 24 October 2016–23 October 2026. The selected rows form 1,066 exact UN Digital Library ID / literal symbol / date groups. Each group has 193 distinct country codes. Every group's observed Y, N, A and X counts and row total match its repeated publisher fields. The source uses integral decimal strings such as `193.0`; fractional totals are rejected rather than rounded.

Aggregate selected codes: Y 153,737; N 13,037; A 20,370; X 18,594. There were zero duplicate-country groups, blank-total groups, inconsistent/invalid published totals, invalid dates, source-ID identity conflicts or resolution-symbol identity conflicts in the requested window. Source groups were contiguous in this exact file, although the reusable reconciliation function also handles noncontiguous groups. No blank-total/consensus-like source groups were found in-window; this does not turn X into an absence or determine eligibility independently.

| Year portion | Selected rows | Exact source groups |
| --- | ---: | ---: |
| 2016 (from 24 October) | 15,247 | 79 |
| 2017 | 18,142 | 94 |
| 2018 | 20,651 | 107 |
| 2019 | 19,300 | 100 |
| 2020 | 19,300 | 100 |
| 2021 | 16,598 | 86 |
| 2022 | 17,177 | 89 |
| 2023 | 16,984 | 88 |
| 2024 | 18,335 | 95 |
| 2025 | 37,056 | 192 |
| 2026 (through 23 October) | 6,948 | 36 |

This validates internal source-file reconciliation, not independent historical membership, policy binding, database completeness or public release readiness. The partially ingested database's last group must be separately reconciled; its truncation cannot be reported as a source-file defect or a complete group. Only a small aggregate receipt was written outside the public repository. No archive was expanded to disk, new database created, source rows published or source text opened for this check.

### Separate partial-database check

A read-only SQLite query of the private staging database confirmed 98,000 stored GA rows across 508 exact symbol/date groups: 507 complete groups of 193 distinct country codes, plus one partial group with 149 distinct country codes. The partial group is `A/RES/77/208`, 15 December 2022, Digital Library record 3997749; its publisher source total is 193, leaving 44 rows not yet ingested in that group. The source file itself passes full-group reconciliation. This is a resumable ingestion boundary, not a source discrepancy, and the 508th group must not be exported or presented as complete. Overall GA database ingestion remains incomplete against 205,738 in-window source rows; no public data export is approved by this receipt. The database was opened in read-only mode and not modified.
