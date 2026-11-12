# Daily transcript warehouse operations

The operational pipeline collects configured meetings, keeps immutable source revisions, and generates consistent research CSV snapshots. The browser application remains usable without configuring this service. This project's first actual private archive publication succeeded on 12 November 2026 (UTC); the account setup below is now verified for that run. Scheduled reliability and recovery acceptance remain separate checks.

## Storage and account setup

Use pre-existing Hugging Face dataset repositories under an account you control:

1. A **private** dataset repository for the SQLite warehouse, raw sources, state, private CSVs and optional model artifacts.
2. A separate **public** dataset repository only if public metadata publication is desired. It must never contain the private warehouse, transcript text or annotations.

Configure these GitHub Actions settings in this source repository:

| Setting | Type | Purpose |
| --- | --- | --- |
| `HF_TOKEN` | Secret | Least-privilege write access to the configured dataset repositories; never a browser credential |
| `HF_DATASET_REPO` | Variable | Private `owner/dataset` repository |
| `HF_PUBLIC_DATASET_REPO` | Optional variable | Different public `owner/dataset` repository for allowlisted exports |
| `ARCHIVE_MANIFEST_URL` | Optional variable | `https://huggingface.co/datasets/OWNER/PUBLIC_DATASET/resolve/main/latest.json` |
| `HF_ACCEPTED_MODEL_PATH` | Optional variable | Directory of an owner-approved model within the private dataset |
| `HF_ACCEPTED_MODEL_REVISION` | Optional variable | Immutable 40-character commit SHA containing that model and its acceptance receipt |

The service does not create accounts, enter billing details, enable paid tiers, or purchase compute. Free-provider quotas and availability can change. Count retained history in storage budgets. Missing credentials, wrong repository visibility, or an exhausted budget must fail before transient-only collection or unsafe publication.

The main portfolio mirror uses the same public manifest URL in its deployment configuration. The repository's Pages build reads `ARCHIVE_MANIFEST_URL`; no token belongs in this URL. Without it the archive screen says it is not configured.

Set both accepted-model variables only after real model acceptance. The workflow verifies pinned artifacts, catalog identity and the owner-confirmed acceptance receipt before collection. With neither variable set, collection continues with stance withheld. Supplying only one or a mismatched artifact fails visibly; no floating model revision is selected automatically.

## First archive run

After the operational workflow is merged into the default branch, open **Actions → Daily transcript warehouse → Run workflow**, choose `main`, and start the run. The manual control may be absent until that merge. Saving the Actions settings alone does not start collection.

The **Verify private archive connection** step checks authenticated access, private visibility, an immutable repository revision, and retained storage usage before collection. Its output contains only operational metadata. It does not prove write access; that is established by successful snapshot publication. An initialized dataset without `latest.json` is a normal first run. If repository metadata has no valid commit SHA, add an initial README or `.gitattributes` through Hugging Face and retry; do not disable the revision check. Missing storage usage remains a blocker.

For this project's archive, `LystadJS/UN-Transcript-Agent-Private` is configured and the [first actual workflow run](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43154577386) succeeded. Its connection check reported private visibility, `usedStorage: 0` and no existing pointer before collection; successful publication then established write access. The initial zero-byte reading is not a measurement of storage after publication. Public-repository and accepted-model settings remain unset.

Success requires the **Restore, collect, validate and publish one snapshot** step to complete and the private dataset to contain `latest.json` pointing to its verified `snapshots/<id>/snapshot.json`. The first successful snapshot is `20261112T042431Z-98493e2e5511` (UTC), reporting 87 meetings, 76,284,090 downloaded bytes and partial collection coverage. Private publication succeeded; public publication was not configured and stance remained withheld as `not_evaluated_missing_labels`.

The [second actual run](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43155142584) **succeeded**. On a fresh Actions runner it verified the existing private pointer and immutable repository revision, restored the prior archive, continued collection, and published `20261112T043029Z-314632fa4d79`. Its receipt reports 78 downloaded meetings, 75,470,172 bytes and partial coverage. Preflight retained storage was 40,446,080 bytes against the configured 80,000,000,000-byte budget; this is a pre-run repository reading, not account-wide capacity acceptance. Public publication remained unconfigured and stance remained withheld. Refreshes may overlap the two runs, so their meeting counts are not a unique-meeting total. The configured daily schedule applies at 11:17 UTC; two manual runs do not establish scheduled reliability.

## Select meetings and run

Edit `config/collection.json` through a reviewed source change. The current-session default begins 8 September 2026, uses English records from available venues, and ends dynamically. Exact meeting selection and body/date subscription are separate configuration modes. Source availability, not requested scope, determines actual coverage.

The collector retains the reserved meeting exclusions from the frozen source frame. It checks exclusions before downloading text. Do not remove them to enlarge a sample.

With Python 3.12 from the repository root:

```sh
python -m pip install huggingface-hub==0.36.0
PYTHONPATH=src python -m un_transcript run --config config/collection.json --workspace /private/un-warehouse --remote hf --repo OWNER/PRIVATE_DATASET --public-repo OWNER/PUBLIC_DATASET --publish-public /private/un-public
```

Supply `HF_TOKEN` through your local secret mechanism. Do not place it in shell history or a checked-in file. Omit `--public-repo` to keep remote outputs private. Use a private workspace outside the source checkout.

`Daily transcript warehouse` runs at **11:17 UTC** and supports manual dispatch. GitHub scheduling can be delayed, skipped, or disabled by provider inactivity rules. The single-writer concurrency group includes training-artifact uploads and does not cancel a writer halfway through publication.

Daily work combines new dates, unresolved downloads, a fourteen-day refresh window, and bounded backfill. Weekly reconciliation revisits the selected frame. The configuration caps dates, meetings, response bytes and total bytes per run; a partially processed frame remains explicit and resumes later. A successful bounded run does not mean the entire requested history has been acquired.

## Publication and recovery

The remote private snapshot is authoritative. Runner files, caches and Actions artifacts are temporary. A publication consists of a complete versioned directory and verified manifest before the current pointer changes. Public publication uses a distinct allowlisted export; source text, annotations and unaccepted predictions are not made public just because their parent meeting is public.

On failure, inspect the Actions status and the last valid manifest's timestamp and coverage. Do not infer freshness from a green Pages deployment. Retry a failed run through manual dispatch; preserve the remote snapshot and checkpoint rather than deleting them.

Actual remote restoration and continued publication were verified by the second successful Actions run above. For continuing recovery checks, use the CLI's `restore`, `verify` and `status` commands in a fresh private workspace; use their `--help` output for exact options. Verify that restored CSV keys, counts and source hashes reproduce the published private manifest. An interrupted-publication recovery drill remains outstanding: an interrupted write must not replace the previous valid pointer.

Source corrections create new revisions. Old predictions remain attached to old revisions and are not silently treated as current. Reprocessing after a model change creates a new method version. The existing source and model history remain inspectable.

## Model preparation and manual training

Collection does not depend on an accepted model. Without one, automatic stance output remains unavailable while the source archive and descriptive work continue.

Start with the private 300-example owner pilot described in [MODEL_CARD.md](MODEL_CARD.md). The owner supplies actual labels; synthetic or assistant-generated choices are never represented as owner-confirmed gold.

`Train private stance candidate` is manually dispatched with immutable private-dataset and upstream-model commit hashes. It fetches the registered training labels and local DistilBERT assets, trains locally, and stores candidate checkpoints in the private dataset repository. It neither evaluates untouched test labels nor promotes a model. Source and annotation contents must not appear in public logs or Actions artifacts.

Use a valid private model/label store with sufficient free space before training. Candidate training is optional and may exceed a free CPU job budget; checkpoints support continuation. A failed or incomplete candidate is not a deployable model. The daily workflow never triggers automatic retraining.

## Operational acceptance record

Keep a private fourteen-day observation record with scheduled start, actual start, completion, source availability, pending work, retained-storage size, errors and published snapshot ID. Record missed jobs as missed. Actual restore/continuation passed on the second manual run; complete the separate interrupted-publication recovery test and capacity assessment. Owner labeling, representative diplomat usability sessions, real model acceptance, and this observation period are external work; passing synthetic CI does not complete them.

The separate `Check live browser collection` workflow uses a fixed authorized development date. Its pinned Ubuntu 24.04/Python 3.12 environment repairs the earlier Ubuntu 26.04/Playwright mismatch. The actual live check passed among the six checks for merged source PR #187. That result establishes collection health at the observed run, not continuing external-service availability.

## Free-runner resource limits

The private/public repository budgets default to 80 GB and 10 GB respectively. Provider `usedStorage` accounts for repository history; it does not establish the account's remaining allowance when other repositories exist. Check the account storage dashboard before activation and keep the combined usage inside the free allowance. The service never upgrades the account or purges original evidence automatically.

Restore refuses individual artifacts above 512 MiB, manifests above 16 MiB, and insufficient local disk space (twice the transfer size plus a 1 GiB reserve). A verified restore installs the complete `workspace/data/` directory atomically. These are explicit free-runner limits; exceeding them requires repartitioning or a different execution host, not silently dropping records.
