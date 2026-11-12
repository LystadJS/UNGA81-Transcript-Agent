# Operational implementation and activation verification — 12 November 2026 (UTC)

This record distinguishes new execution from inherited evidence. Code and source-site deployment are complete for the operational implementation milestone. Seven actual private archive publications succeeded, including restoration and continued collection on fresh runners and a combined private/public publication. Empirical model acceptance and sustained operational acceptance remain open. Activation dates, workflow timestamps and snapshot identifiers in this record use UTC.

## Executed locally

- Production unit/integration tests cover collection selection and exclusions, revision preservation, exact evidence, source/model provenance, consistent CSVs, public field allowlists, storage quotas, two-phase publication, atomic restoration, and pipeline replay. Exact final counts are recorded in the PR validation.
- Public archive: 15 synthetic Chromium checks passed, including hash/byte validation, unavailable/stale/partial state, model withholding, unsafe text/URLs, filtering, CSV safety, keyboard navigation, and mobile overflow.
- A real authorized development meeting (`ga/81/16`, 1 October 2026) completed the new local collection–warehouse–analysis–export–checkpoint pipeline: 69 retained segments; transcript SHA-256 `7e2cfa5b8a5bf587ed7f679b56cf2a7397896a2091d84dd5a225e7e05815cb55`; 1,255,192 bytes including inventory. No accepted model was supplied, zero stances were released, and raw files remain outside the code repository.
- Optional ML dependencies were exercised with a tiny, randomly initialized **synthetic-only** DistilBERT: 30 fictional training pairs, 25 separate calibration pairs, 10 test pairs, TF-IDF baseline, safetensors serialization, and ONNX inference. Dynamic ONNX/PyTorch parity at two sequence lengths differed by at most `2.384185791015625e-07`. The insufficient benchmark correctly failed acceptance. This is software validation, not a trained UN model.
- The public build succeeds without copying private runtime data.

## GitHub and first actual archive publication

- [Source PR #187](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/187) merged as `17232d06a71f7ca187062ae66f51522bb3c4bf73`. All six checks passed, including actual live collection. This supersedes the earlier local-browser certificate limitation for the verified GitHub run; no TLS bypass was required.
- [Source Pages deployment 43154122421](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43154122421) succeeded.
- [First actual Hugging Face archive run 43154577386](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43154577386) succeeded against the owner-controlled private dataset `LystadJS/UN-Transcript-Agent-Private`. The initial connection check reported private visibility, retained storage usage of zero and no existing pointer. Those values describe the empty repository before publication.
- The run published private snapshot `20261112T042431Z-98493e2e5511`, reporting 87 meetings and 76,284,090 downloaded bytes. Coverage was **partial**. Public storage was **not configured**, and model status was **`not_evaluated_missing_labels`**. No accepted stance model or public transcript archive is implied by this success.

The first run establishes actual collection and private write/publication behavior. Because there was no previous pointer, it does not establish restoration of an existing remote archive.

## Second-run recovery verification

[Actual run 43155142584](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43155142584) **succeeded**, with all steps completed. Preflight confirmed an existing snapshot pointer, private repository visibility, an immutable repository revision and 40,446,080 retained bytes against the configured 80,000,000,000-byte budget. This storage reading preceded the second run and does not measure account-wide remaining capacity.

The fresh Actions runner restored `20261112T042431Z-98493e2e5511` before opening the warehouse, continued bounded collection from its persisted state, and published `20261112T043029Z-314632fa4d79`. The second receipt reports 78 downloaded meetings, 75,470,172 bytes and **partial** coverage. Private publication succeeded; public storage remained unconfigured and model status remained `not_evaluated_missing_labels`.

This verifies actual remote restoration and continued publication. The two per-run meeting counts must not be summed as unique coverage because refreshes can overlap. Partial collection still does not establish complete historical acquisition, source completeness or model acceptance.

## Portfolio mirror and remaining acceptance

The portfolio [mirror update in PR #151](https://github.com/LystadJS/LystadJS.github.io/pull/151) is now merged and deployed. Its initial regression run 43153975951 had 27 inherited failures; targeted repairs retained the current design and assertion tolerances while restoring report reading-size behavior. Final CI 43190505975 passed 94 tests with 44 existing viewport-specific skips, and [live run 43191396732](https://github.com/LystadJS/LystadJS.github.io/actions/runs/43191396732) passed exact assets plus real desktop/mobile research/comparison/meeting checks. PR #152 synchronized the separate monitor's stale release pin; live monitor 43192489347 passed 32 asset hashes without transcript requests. The preferred portfolio URL has the operational application; public dataset configuration and scientific acceptance remain separate.

Actual owner labels, trained model acceptance, broader real-source coverage, diplomat usability sessions, and fourteen days of scheduled operation have not been completed. The 37 reserved meetings remain unopened.

The fourteen-day record must measure actual scheduled starts/completions, pending work, storage use and failures. The successful second manual run establishes remote restore/continuation, but it does not replace that observation period, capacity acceptance, continued failure-mode recovery checks, or representative usability evaluation. Source-bearing runtime reports and private recovery records stay outside this code repository.

## Isolated real-provider interruption drill

[Run 43184679678](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43184679678) passed on 12 November 2026. Synthetic snapshots under `drills/43184679678-1/store/` exercised interruption after staging verification but before pointer activation, recovery of the previous snapshot, and successful retry. Both restores reproduced all manifest-bound CSV and artifact hashes. The production `latest.json` remained byte-identical. This supersedes the pending isolated interruption drill; it did not cause a production outage or terminate an operating production writer.

Measured canonical snapshot size was 269,860,459 bytes, largest artifact 50,728,960 bytes, and provider-reported retained storage grew from 152,339,418 to 152,781,786 bytes across the synthetic drill. These are actual repository measurements against an 80,000,000,000-byte configured budget, not account-wide capacity acceptance or a long-term storage forecast. The verified receipt remains private at `drills/43184679678-1/receipt.json`, revision `d7c0b0435be1a2e5fdb215aa98370abbe83673dd`.

## Real research-export replay — 12 November 2026

[Run 43192650005](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43192650005) restored the fifth snapshot, `20261112T092603Z-1fd9c19974c2`, from immutable HF revision `c8cd31ca798a37d8fdcd5cfb352501d22291a462`. It opened the restored SQLite database read-only, passed full integrity and foreign-key checks, regenerated 23 private/public export files, and matched every byte. Those files include 17 CSVs; private-table receipts total 78,444 rows across distinct relational grains. No remote writes or sealed pilot reads occurred. The canonical snapshot and all historical sources remain unchanged.

This complements the isolated real-provider interrupted-publication drill. It establishes coherent export reproduction under the tested exporter version, not complete collection coverage, account-wide free-tier capacity, owner labels, model accuracy or completion of the fourteen-day observation period. Implementation: PR #197; final CI 43192483593 and post-merge CI 43192650428 passed with 108 production tests plus archive/reviewer browser checks.

## Public metadata activation and real browser checks

[Provisioning run 43198037327](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43198037327) created `LystadJS/UN-Transcript-Agent-Public` with existing permissions, validated the metadata-only allowlist before creation, published snapshot `20261112T092603Z-1fd9c19974c2`, and verified anonymous access. No repository visibility was changed and no raw transcripts or annotations were published. The versioned target configuration and both browser endpoints are active through source PR #201 and mirror PR #153.

[Anonymous live browser run 43200525651](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43200525651) passed on source and portfolio sites at widths 1440 and 390. All four cases loaded the same actual 683-meeting snapshot, matched its identity/freshness, exercised filters and keyboard focus, checked mobile overflow, downloaded a byte/hash-verified CSV and confirmed that unaccepted stances remain withheld. No UN source or authenticated requests occurred. Receipt contains only aggregate engineering evidence; human usability acceptance remains false.

Combined warehouse run 43199258075 failed without a private success receipt. The valid prior public snapshot remained accessible during verification. Operation-level diagnostics in PR #203 preserve provider privacy and the existing two-phase activation safeguards. Sustained private/public publication and the observation period remain open until verified operational evidence is recorded.

## Combined publication and monitoring implementation

[Run 43200795553](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43200795553) published snapshot `20261112T103158Z-197cd641468a` privately and publicly. It stores 454 distinct meetings out of 843 known, with 31,548 segments; 37 reserved meetings remain excluded. Automatically triggered [browser check 43202107662](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43202107662) passed desktop/mobile checks on both sites against that new snapshot. The original prior failure's provider cause remains unknown.

The monitoring receipt, scheduled-date ledger and run inspector are implemented through PRs #209–212. They report actual workflow outcomes separately from snapshot freshness and mark missing evidence explicitly. Read-only observation at 11:20 UTC found no scheduled run yet for today's 11:17 UTC slot; this remains awaiting start within the documented reporting grace period. Manual successes do not fill that date. The new read-only restore/re-export audit (43208166363) passed after metadata batching: immutable HF revision `9fe3ff41c7df925e7f8e5d7cfc0ab4538ba6ce23`, 23 files, 17 CSVs and 94,734 rows across private tables reproduced byte for byte; SQLite integrity and foreign keys passed. The row sum is not a meeting count. First new monitoring-artifact acceptance is pending. No elapsed fourteen-day or model acceptance follows from these engineering changes.

## First structured monitoring artifact verification

Manual backfill [43208790947](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43208790947) succeeded with both private/public snapshot `20261112T112521Z-b9eaf946bc36` and aggregate coverage of 541 stored / 1,017 known meetings, 37,544 segments and 63 inventory dates. [Automatic browser check 43209512701](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43209512701) passed all four source/portfolio desktop/mobile cases against that new snapshot.

Monitoring artifact `13940048173` (`operational-receipt-1`, 730 ZIP bytes) was retrieved with the GitHub connector after the managed shell's redirect download returned Forbidden. Its SHA-256 matched GitHub's `6c386272d3a304288f702a697dc6912cc30238e03aa972a98cc37695a323d690`; strict ZIP/allowlist/run/attempt validation passed. The receipt records private provider-reported retained bytes before/after as 1,324,166,706 / 1,701,819,500. Public `usedStorage=0` is a provider report, not proof of no stored metadata. Account-wide quota acceptance remains open. No private sources or annotations were in the artifact.

This establishes actual structured receipt creation and validated retrieval through the connector. The direct-shell download limitation remains environment-specific. No scheduled run or elapsed fourteen-day acceptance is implied.
