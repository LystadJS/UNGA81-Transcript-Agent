# Daily transcript warehouse operations

The operational pipeline collects configured meetings, keeps immutable source revisions, and generates consistent research CSV snapshots. The browser application remains usable without configuring this service. Private and public metadata publication are verified, including a combined run on 12 November 2026 (UTC). The capability matrix records current coverage and evidence. Scheduled reliability, account-wide capacity and model acceptance remain separate checks.

## Storage and account setup

Use Hugging Face dataset repositories under your existing account:

1. A **private** dataset repository for the SQLite warehouse, raw sources, state, private CSVs and optional model artifacts.
2. A separate **public** dataset repository for allowlisted metadata. This project uses `LystadJS/UN-Transcript-Agent-Public`, created through the authorized provisioning workflow. It must never contain the private warehouse, transcript text or annotations.

Configure these GitHub Actions settings in this source repository:

| Setting | Type | Purpose |
| --- | --- | --- |
| `HF_TOKEN` | Secret | Least-privilege write access to the configured dataset repositories; never a browser credential |
| `HF_DATASET_REPO` | Variable | Private `owner/dataset` repository |
| `HF_PUBLIC_DATASET_REPO` | Optional consistency check | If set, must match the public target in `config/publication.json`; no additional variable is required for this deployment |
| `ARCHIVE_MANIFEST_URL` | Optional consistency check | If set, must match the checked-in `site/archive-config.json` endpoint |
| `HF_ACCEPTED_MODEL_PATH` | Optional variable | Directory of an owner-approved model within the private dataset |
| `HF_ACCEPTED_MODEL_REVISION` | Optional variable | Immutable 40-character commit SHA containing that model and its acceptance receipt |

The service does not create accounts, enter billing details, enable paid tiers, or purchase compute. Free-provider quotas and availability can change. Count retained history in storage budgets. Missing credentials, wrong repository visibility, or an exhausted budget must fail before transient-only collection or unsafe publication.

The source Pages site and portfolio mirror use the same checked-in public manifest endpoint. The Pages build preserves `site/archive-config.json` when no environment override is present; a supplied override must match. The daily job loads the versioned target from `config/publication.json`. No token belongs in either public configuration file.

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

Actual remote restoration and continued publication were verified by the second successful Actions run above. For continuing recovery checks, use the CLI's `restore`, `verify` and `status` commands in a fresh private workspace; use their `--help` output for exact options. Verify that restored CSV keys, counts and source hashes reproduce the published private manifest. The isolated real-provider interruption drill passed in run 43184679678: an interrupted staged write retained the previous pointer and both recovery/retry reproduced the artifacts. Production data stayed untouched; continue failure-mode recovery checks.

Source corrections create new revisions. Old predictions remain attached to old revisions and are not silently treated as current. Reprocessing after a model change creates a new method version. The existing source and model history remain inspectable.

## Model preparation and manual training

Collection does not depend on an accepted model. Without one, automatic stance output remains unavailable while the source archive and descriptive work continue.

Start with the private 300-example owner pilot described in [MODEL_CARD.md](MODEL_CARD.md). The owner supplies actual labels; synthetic or assistant-generated choices are never represented as owner-confirmed gold.

`Train private stance candidate` is manually dispatched with immutable private-dataset and upstream-model commit hashes. It fetches the registered training labels and local DistilBERT assets, trains locally, and stores candidate checkpoints in the private dataset repository. It neither evaluates untouched test labels nor promotes a model. Source and annotation contents must not appear in public logs or Actions artifacts.

Use a valid private model/label store with sufficient free space before training. Candidate training is optional and may exceed a free CPU job budget; checkpoints support continuation. A failed or incomplete candidate is not a deployable model. The daily workflow never triggers automatic retraining.

## Operational acceptance record

Keep a private fourteen-day observation record with scheduled start, actual start, completion, source availability, pending work, retained-storage size, errors and published snapshot ID. Record missed jobs as missed. Actual restore/continuation passed on the second manual run; the isolated interruption drill also passed in run 43184679678. Complete account-wide capacity assessment and continue recovery observation. Owner labeling, representative diplomat usability sessions, real model acceptance, and this observation period are external work; passing synthetic CI does not complete them.

The separate `Check live browser collection` workflow uses a fixed authorized development date. Its pinned Ubuntu 24.04/Python 3.12 environment repairs the earlier Ubuntu 26.04/Playwright mismatch. The actual live check passed among the six checks for merged source PR #187. That result establishes collection health at the observed run, not continuing external-service availability.

## Free-runner resource limits

The private/public repository budgets default to 80 GB and 10 GB respectively. Provider `usedStorage` accounts for repository history; it does not establish the account's remaining allowance when other repositories exist. Check the account storage dashboard before activation and keep the combined usage inside the free allowance. The service never upgrades the account or purges original evidence automatically.

Restore refuses individual artifacts above 512 MiB, manifests above 16 MiB, and insufficient local disk space (twice the transfer size plus a 1 GiB reserve). A verified restore installs the complete `workspace/data/` directory atomically. These are explicit free-runner limits; exceeding them requires repartitioning or a different execution host, not silently dropping records.

## Meeting versus inventory coverage

Public meeting partitions and meeting totals exclude `inventory:<date>` coverage records. Those rows describe date-level inventory checks and remain in private `coverage.csv` for audit. New manifests report their latest-per-date counts separately as `coverage.inventory_dates` and `coverage.inventory_statuses`; their statuses do not enter meeting denominators. Older snapshots remain immutable and may include inventory checks in their meeting totals. Distinct stored-meeting and current-segment counts were unaffected by that export defect.

## Restore and regenerate the real research exports

Manually dispatch **Verify restored research exports** (`restored-export-audit.yml`) to restore the current private snapshot, open SQLite in read-only mode, check integrity and foreign keys, and regenerate all private and public export files into a separate temporary directory. Every file must match the sealed snapshot byte for byte. This checks database/export coherence beyond downloaded-file checksums; a sealed but stale CSV fails. The job makes no remote writes and publishes only aggregate verification metadata. Use the matching exporter code for an older snapshot; a method/schema change may correctly fail exact reproduction. Never update archived bytes to make a failed audit pass.

## Provision the public metadata dataset

The manually dispatched **Provision public metadata archive** workflow uses the existing `HF_TOKEN` and `HF_DATASET_REPO` settings. It permits only the same owner's dedicated `UN-Transcript-Agent-Public` dataset. It restores the current private snapshot, validates every public field and file before creating a repository, and publishes only the allowlisted projection. It never changes an existing private repository's visibility or adopts an unrelated nonempty repository. Permission failures stop provisioning without changing the private archive. It verifies an anonymous manifest read after publication; no private restore or source-bearing log artifact is uploaded.

Successful provisioning alone does not configure daily public refresh or the browser URL. Record its verified manifest URL, then configure those through a separate reviewed source change. Repeating setup for an already published snapshot verifies its existing remote bytes rather than adding duplicate commits. Account-wide quota acceptance remains separate; no paid storage request is made.

A public-storage outage does not prevent private collection/publication. After the private snapshot is verified, public publication runs as a separate downstream step. If it fails, the workflow exits unsuccessfully and records `private_publication: published`, `public_publication: failed`, and a sanitized exception type in its run receipt. The prior public snapshot remains visible with its own timestamp. Retry through a later bounded run; never describe a fresh private archive as a fresh public report. Private publication failures still prevent public publication and cursor advancement.

## Verified public endpoint and daily activation

Provisioning run [43198037327](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43198037327) created `LystadJS/UN-Transcript-Agent-Public` using the existing token and verified anonymous access to its source-free projection of snapshot `20261112T092603Z-1fd9c19974c2`. Its stable manifest is `https://huggingface.co/datasets/LystadJS/UN-Transcript-Agent-Public/resolve/main/latest.json`.

`config/publication.json` is the versioned daily publication target; `site/archive-config.json` is the matching read-only browser endpoint. The Actions job loads that public repository without requiring another administrative repository variable. If `HF_PUBLIC_DATASET_REPO` is set, it must agree with the versioned target. The Pages builder uses the checked-in endpoint; an `ARCHIVE_MANIFEST_URL` override must match it. This prevents code deployment from silently disabling or redirecting archive access. Local CLI publication remains explicit through `--public-repo`.

## Anonymous public archive verification

**Verify public archive access** runs after successful main-branch warehouse jobs and supports manual source/portfolio/both checks. A real Chromium browser loads each selected deployed application at desktop and mobile widths, verifies the manifest and partitions, exercises filtering and keyboard focus, and saves a checksum-matching public CSV. It rejects source-transcript requests, write requests and authorization headers. The receipt contains only URLs/identifiers, dates, aggregate counts and boolean checks. Following a warehouse job, the public snapshot timestamp must be at least that job's creation time; a stale prior publication cannot pass as the new result. General freshness is bounded at 48 hours.

Pull-request checks for this monitor exercise the already deployed source application. Live network failures remain failures. These engineering checks do not replace diplomat usability sessions or scientific/model evaluation.

## Source-free operational receipts

New warehouse runs upload only `operational-receipt-<attempt>/operational-receipt.json` to Actions, retained for 30 days. A strict projection includes run/attempt/event, processing status, snapshot identity/time, aggregate coverage, publication outcomes, model acceptance boolean and before/after retained repository bytes. Source text, local paths, annotations, provider error strings and credentials are excluded. This artifact is monitoring evidence, not durable archive storage.

A missing pipeline receipt produces `completed_pipeline_receipt: false` and `snapshot: null`; it never claims a fresh snapshot. Missing storage measurements remain null. `processing_status` describes the job before receipt upload; use GitHub's final run conclusion to determine workflow success, including an artifact-upload failure. Compare run attempts explicitly. Retained repository usage includes history/staging and is not account-wide quota certification. Complete scheduled observation still requires checking actual scheduled run dates and outcomes; manual reruns do not fill missing scheduled dates.

Run the read-only observation report with `PYTHONPATH=src python tools/observe_operational_runs.py --output /tmp/un-observation.json`. It uses authenticated `gh api` for the canonical workflow inventory and anonymous HTTPS for the public manifest; it never reads HF credentials, transcript sources or labels. Defaults cover 12–25 November 2026 UTC. Keep generated reports outside the code repository.

The report lists each expected 11:17 UTC date separately and never substitutes manual retries for scheduled runs. It reports `not_due`, `awaiting_start`, `missing`, `running_or_queued`, `successful` or `unsuccessful`; the reporting grace period is two hours and delays over fifteen minutes are flagged. These are monitoring conventions, not guarantees about GitHub scheduling. The GitHub API exposes creation/start times, not an original scheduled-for timestamp, so date association uses UTC creation date. Reruns explicitly flag uninspected earlier attempts. Bounded pagination failures stop the report instead of declaring absent runs; a failed public-manifest probe leaves workflow evidence intact and freshness unavailable. `operational_acceptance` remains false regardless of individual successes.

Storage metadata reads are batched in groups of at most 100 and cached only for an exact immutable commit SHA within one process. Restore, existing-raw checks and staged-file verification still download and check every required file's size and hash. Mutable branch references are rejected, missing paths are cached only after a successful metadata response, and new revisions cannot reuse old metadata. This reduces provider request pressure without weakening archive verification; no claim is made that the earlier transient publication failure was caused by a rate limit.

For one observed run, use `PYTHONPATH=src python tools/inspect_operational_run.py --run-id RUN_ID --output /tmp/un-run.json` (optionally `--attempt N`). It reads only the canonical warehouse workflow metadata, bounded job timing and the exact `operational-receipt-N` artifact. It rejects extra ZIP members, oversized data, private fields, mismatched attempts and unrelated workflows; it does not download arbitrary artifact URLs. The final run conclusion and last completed job timestamp are reported separately from the processing receipt. Old runs without artifacts and expired artifacts remain explicitly missing/expired. A successful workflow with no receipt is not treated as verified snapshot evidence.

In the managed engineering environment, the direct `gh api` artifact redirect can return Forbidden while the GitHub connector's `download_workflow_artifact` succeeds. Use that authorized connector fallback, then validate the downloaded ZIP with `receipt_from_zip` and compare its SHA-256 to GitHub's artifact metadata. Do not weaken ZIP/field/attempt validation or expose signed download URLs. Provider `usedStorage` readings are reported measurements; a zero reading for a populated public repository is not proof of zero physical storage. Keep account-wide capacity acceptance open until measurement semantics and other account usage are reconciled.

### Monitoring artifact transport failures

The inspector distinguishes a genuinely missing/expired receipt from a present artifact whose download is `unavailable` or whose bytes/contents are `invalid`. It still writes the verified run outcome and timing; invalid/unavailable evidence returns a nonzero exit status and never becomes operational acceptance. Provider bodies, signed URLs and exception strings are omitted.

If the managed shell cannot follow GitHub's artifact redirect, use the authorized GitHub connector to download only the exact `operational-receipt-ATTEMPT` artifact. Then run `PYTHONPATH=src python tools/inspect_operational_run.py --run-id RUN_ID --receipt-zip PRIVATE_LOCAL_ZIP --output /tmp/run-inspection.json`. This fallback requires the live artifact's SHA-256, strict single-member ZIP bounds, allowlisted fields and matching run/attempt/event. It cannot substitute a different artifact or bypass an unavailable provider digest. No private warehouse, annotation or transcript artifact is needed.

### Weekly inventory capacity and checkpoint changes

Production configuration permits up to **70 inventory dates per run**, with the preceding 14 dates refreshed daily. This leaves up to 56 historical date slots per daily run and supports a session-year frame within a week under successful responses. The previous 21-date setting left seven historical slots and could not finish a growing session frame in seven daily runs. Source downloads remain capped at 100 meetings / 100,000,000 bytes per run; response, pagination, retry, runner-time and storage bounds are unchanged. Inventory pagination reserves bytes before each network request. Outages, multi-page inventories and exhausted budgets can still prevent completion; this is capacity planning, not a service guarantee.

`inventory_progress` in the source-free run/monitoring receipt records the week, selected/recent/pending date counts, actual inventory completion and whether the configured daily date allowance is nominally sufficient for seven runs. Inventory completion is separate from unavailable/deferred transcripts. The configured service may finish its inventory while transcript coverage remains partial. Reserved dates count as explicitly excluded without network access. Larger historical selections require reviewing the nominal-capacity flag and free-service constraints.

Changing only runtime bounds preserves the selection cursor and known-meeting checks. A changed venue, date frame or exact meeting selection still resets selection bookkeeping while preserving stored source history. Legacy checkpoints migrate only when the original snapshot's recorded configuration matches their saved configuration hash and has the same selection; absent/mismatched proof retains the conservative reset behavior. Full configuration hashes remain in the run history.


### Inventory metadata and database version

The operational working copy now uses additive SQLite schema version 2. Complete validated inventories supply metadata for selected meetings whose transcripts are unavailable or deferred. Private bundles add `inventory_meetings.csv`; public fields and stored-source revision metadata remain unchanged. Historical schema-1 snapshots replay under their original export behavior. See [inventory metadata and compatibility](INVENTORY_METADATA.md) before rollback or research joins.


### Failed monitoring lookups

The scheduled observer never overwrites its prior report when the GitHub workflow inventory is inaccessible, malformed or incomplete. It exits nonzero and writes a separate `OUTPUT.error.json` receipt containing the failed observation time, fixed operation/reason, numeric HTTP status when available, and whether the prior report was preserved. Provider bodies, URLs, stderr and credentials are excluded. Compare observation timestamps: a retained successful report is old evidence, and an older error sidecar can remain after a later successful check.

If workflow inventory succeeds but the public manifest fails, the current report retains workflow evidence, marks public freshness unavailable, and records only the public operation/error type/HTTP status. Neither case grants service acceptance or fills a missing scheduled date. The observer does not dispatch collection, change scheduling or read private archive contents.

### Retry and refresh ordering

The warehouse alternates advertised meetings without a stored source and refreshes of stored meetings, oldest attempt first within each group. Stored identity comes from the verified SQLite archive, not the latest `deferred` status. The checkpoint retains which group should go next, so even a one-attempt run or a failed retry does not permanently crowd out refreshes. Existing response, byte, meeting and reserved-source limits still apply. Inventory claims do not guarantee downloadable English text.
