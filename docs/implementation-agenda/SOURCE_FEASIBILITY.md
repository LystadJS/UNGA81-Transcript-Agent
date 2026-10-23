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
