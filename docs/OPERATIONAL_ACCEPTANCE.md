# Operational implementation and activation verification — 12 November 2026 (UTC)

This record distinguishes new execution from inherited evidence. Code and source-site deployment are complete for the operational implementation milestone. Two actual private archive publications succeeded, including restoration and continued collection on a fresh runner. Empirical model acceptance and sustained operational acceptance remain open. Activation dates, workflow timestamps and snapshot identifiers in this record use UTC.

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
