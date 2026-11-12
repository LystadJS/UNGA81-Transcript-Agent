# Current capability and acceptance matrix

This is the current operational status guide, updated after verified public metadata activation on 12 November 2026 (UTC). `site/release.json` identifies the released browser version. Historical validation receipts retain their original scope and date; they are not a fresh full-system test.

| Capability | Implementation boundary | Deployment / empirical status |
| --- | --- | --- |
| Existing browser collection and reporting | Browser-selected public UN inventory, source links, summaries, recovery and exports | Source PR #187 merged after all six checks passed, including actual live collection; source Pages deployment succeeded |
| Durable operational collection | Versioned selection, bounded refresh/backfill, immutable source revisions, SQLite warehouse | Seven actual runs published to the owner's private Hugging Face dataset; successive fresh runners restored the archive and continued collection |
| Research CSV snapshots | Consistent keyed exports, dictionary, hashes, source and run history | Seven real private snapshots published; latest corrected coverage records 1,017 known / 541 stored meetings and 37,544 current segments; coverage remains partial; latest real restored-export run 43216908065 reproduced 24 files (17 CSVs, 109,794 relational rows) byte for byte |
| Public archive | Read-only manifest/partition browser with source and coverage metadata | Allowlisted metadata is published to `LystadJS/UN-Transcript-Agent-Public`; actual anonymous source and portfolio desktop/mobile checks passed in run 43200525651 |
| Five-level semantic stance | Candidate training, source-bound inference contract, explicit uncertainty and evaluation policy | **No accepted trained model or owner benchmark is supplied** |
| Issue discovery | Versioned catalog and source-linked candidate discovery | New candidates do not silently become validated policy propositions |
| Exploratory methods | Existing browser TF-IDF, dimensional methods and clustering remain available | Exploratory patterns do not establish alignment, influence or causation |
| Historical issue/vote research | Separate private ingestion and research structures | Public historical archive and fitted empirical models remain unaccepted |
| R/Shiny D1 | Separate preserved local workflow | Twelve executable adapters among 42 registered methods; not 42 operational methods |
| Daily operation | Scheduled workflow, allowlisted per-attempt receipts, read-only observation and run inspection | Combined private/public publication and automatic browser freshness checks passed. The first scheduled run is awaiting GitHub start as of 12 November 12:16 UTC; fourteen-day scheduled observation and account-wide capacity acceptance remain outstanding |

The first [actual archive run](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43154577386) reported 87 meetings and 76,284,090 downloaded bytes, with partial coverage. Its private snapshot ID is `20261112T042431Z-98493e2e5511` (UTC). The [second actual run](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43155142584) successfully restored that archive and published `20261112T043029Z-314632fa4d79`, reporting 78 downloaded meetings and 75,470,172 bytes. These run counts may overlap through refreshes and must not be added as unique meetings. Both runs had partial coverage, successful private publication, no configured public storage, and model status `not_evaluated_missing_labels`. These are operational receipts, not empirical stance acceptance. See [the acceptance record](OPERATIONAL_ACCEPTANCE.md) for the deployment and recovery boundaries.

The source repository's Pages deployment succeeded. The preferred portfolio mirror was deployed through [PR #151](https://github.com/LystadJS/LystadJS.github.io/pull/151), after all 94 active browser regression tests and its manifest audit passed (44 existing viewport-specific skips). [Live verification 43191396732](https://github.com/LystadJS/LystadJS.github.io/actions/runs/43191396732) passed exact asset hashes and actual desktop/mobile research/comparison/meeting browser checks. [PR #152](https://github.com/LystadJS/LystadJS.github.io/pull/152) repaired a stale version pin in the separate quick-reader monitor; [run 43192489347](https://github.com/LystadJS/LystadJS.github.io/actions/runs/43192489347) verified 32 live assets without requesting transcripts. The archive application and permitted public metadata are deployed. [Mirror PR #153](https://github.com/LystadJS/LystadJS.github.io/pull/153) activated the endpoint; regression 43199308891, mirror audit 43200237741, Pages 43200237110 and quick-reader monitor 43200237856 passed. [Public archive verification 43200525651](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43200525651) passed on both sites at desktop and mobile sizes: actual anonymous manifest/partition loading, snapshot identity/freshness, filters, withheld stance display and hash-verified CSV downloads. It made no UN transcript requests. This is engineering verification, not diplomat usability acceptance.

## Acceptance dependencies

1. Complete account-wide capacity acceptance and continued recovery observation. Isolated real-provider interruption recovery passed in runs 43184679678 and 43216326797, including accepted-batch response loss; production data and its pointer were left untouched.
2. Complete the fourteen-day scheduled observation record and verify continuing private/public publication. Separate public metadata storage and browser configuration are now active.
3. Complete the owner-labeled 300-example codebook pilot, then expand benchmark coverage.
4. Train and assess the candidate on source-disjoint calibration and untouched test data; record failed gates as failures.
5. Complete representative diplomat usability sessions and the fourteen-day observation period.

The operational release may collect and expose permitted descriptive metadata while stance remains withheld. Publication of code is not completion of external account setup, human labeling, model accuracy acceptance or an elapsed observation period.

## Prior development summary repair

Release 1.40.0 repaired daily-summary extraction using the owner's three-day development review. The repair replay covers 12 meetings and 439 retained segments. A new owner review of repaired output and untouched acceptance remain outstanding. See [DAY_SUMMARY_EVALUATION_STATUS.md](DAY_SUMMARY_EVALUATION_STATUS.md) for the distinction between the earlier missing-sample receipt and the later repair evidence.

## Licensing and data handling

The codebase includes third-party numerical licenses in `site/NUMERICS_LICENSES.txt` and `site/HDBSCAN_LICENSE.txt`. No new blanket license is applied to inherited code, UN transcript text or annotation records. Resolve redistribution rights before adding source-bearing fields to public exports; preserve package/model license notices. Public availability alone does not establish a redistribution license.

The [PR triage](PR_TRIAGE.md) records the disposition recommended for existing unmerged work. It does not merge, close or promote those branches.

The corrected [fourth archive run](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43188813315) separates 42 inventory dates from 569 known meetings. It stores 314 distinct meetings and 22,548 current segments. PR #195 preserves older immutable snapshots, whose meeting totals could include inventory pseudo-records; use the corrected export grain for subsequent coverage comparisons.

The [fifth archive run](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43191295000) published `20261112T092603Z-1fd9c19974c2`: 683 known / 381 stored meetings, 26,897 current segments, and 49 inventory dates. All 37 reserved meetings are recorded as excluded. Coverage remains partial. Current counts supersede earlier aggregate receipts without rewriting their snapshots.

The real [restore/re-export audit](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43192650005) independently regenerated all 23 export files, including 17 CSVs, from restored read-only SQLite and matched every byte. Integrity and foreign-key checks passed. This establishes archive/export coherence for that snapshot and exporter version, not model or statistical acceptance.

## Current public publication and failure evidence

[Provisioning 43198037327](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43198037327) created the dedicated public dataset with existing authorized credentials, published the fifth snapshot’s allowlisted metadata and verified anonymous access. Raw transcripts, annotations, private CSVs and credentials remain private. Source PRs #199–202 enforce the publication boundary, activate versioned configuration, preserve private progress during public outages and add post-warehouse live verification.

Combined warehouse [run 43199258075](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43199258075) failed during private publication without a success receipt. The prior public snapshot remained readable. Preflight reported 789,171,426 retained private-repository bytes against the configured 80 GB safety budget; this is not account-wide capacity certification. [PR #203](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/203) adds sanitized operation/status diagnostics (125 production tests; CI 43200637460 passed). Diagnostic retry [43200795553](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43200795553) succeeded in both private and public publication. Its automatically triggered browser check 43202107662 passed on both sites. The original transient failure cause remains unestablished; retry success alone does not identify it.

Evaluation-contract hardening in [PR #206](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/206) rejects malformed matched baselines and boolean confidence values; CI 43201402092 passed 130 production tests. This is synthetic engineering validation and does not supply owner labels or validate a model.

The [sixth successful archive run](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43200795553) published `20261112T103158Z-197cd641468a`, generated 12 November at 10:35:05 UTC: 843 known / 454 stored meetings, 31,548 current segments and 56 inventory dates. Statuses reconcile as 351 collected + 271 deferred + 13 excluded language + 37 reserved + 171 unavailable. Both private and public publication passed; coverage remains partial and stances withheld. Preflight retained private repository storage was 1,112,616,073 bytes, including history/staged artifacts; account-wide quota remains unverified.

## Monitoring and provenance implementation — 12 November 2026

PRs #209–212 add source-free per-attempt Actions receipts, before/after retained repository measurements, a scheduled-date observation report and a strict artifact inspector. Actual read-only checks correctly distinguish the eight existing manual runs from scheduled observation and report old monitoring artifacts as missing. Receipt artifacts remain monitoring evidence, not durable archive backups. A new manual-run receipt was downloaded through the GitHub connector, matched its artifact SHA-256 and passed strict attempt/field validation. First scheduled-run evidence remains pending.

PR #211 batches metadata only at immutable revisions while retaining every artifact byte/hash check. Its synthetic 250-file check uses three metadata requests. The fresh real [restore/re-export audit 43208166363](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43208166363) passed after the change: all 23 export files, including 17 CSVs and 94,734 rows across private relational tables, reproduced byte for byte from the sixth snapshot. Integrity and foreign keys passed. This is not a count of unique meetings.

PR #214 preserves upstream license and model-card provenance in new candidates. CI 43207832298 passed 161 production tests plus browser/build checks. Notices-only verification at a pinned DistilBERT revision passed; no weights or owner labels were downloaded and no model was trained or accepted.

The [seventh successful archive run 43208790947](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43208790947) published `20261112T112521Z-b9eaf946bc36`, generated at 11:27:31 UTC: 1,017 known / 541 stored meetings, 37,544 segments and 63 inventory dates. All 37 reserved exclusions remain. Both private/public publication and automatic [browser verification 43209512701](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43209512701) passed. This is a manual run and does not fill the scheduled observation.

The source-free monitoring artifact passed SHA-256 and strict field/attempt verification. Provider-reported private retained storage grew from 1,324,166,706 to 1,701,819,500 bytes. The provider reported public `usedStorage=0` despite published metadata; this must not be interpreted as zero physical footprint or account-wide quota acceptance. A later metadata-only measurement reconciled the project footprint; see below. PR #216 adds legitimate absent/removed inventory statuses; CI 43209383437 passed 162 production tests plus browser/build checks.

An anonymous complete public-tree inventory at 11:32 UTC measured 16 files and 1,889,831 bytes, with no LFS files. This current-tree measure excludes deleted/replaced history and differs from the provider-reported zero; neither alone establishes total retained account usage.

## Project storage accounting

[Capacity run 43214811857](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43214811857) measured retained reachable history without reading source payloads: private conservative basis **2,310,896,814 bytes** and public **1,892,160 bytes**. The private provider meter matched large-file bytes in this sample; Git blobs added 609,077,314 bytes. Production write guards now include both measures and stop if the bounded inventory is incomplete. The 80/10 GB budgets remain unchanged. Other account repositories and unadvertised objects remain outside this measurement; account-wide free-tier acceptance is still outstanding. [Accounting scope and evidence](STORAGE_CAPACITY.md).
