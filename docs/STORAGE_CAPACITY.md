# Storage accounting and zero-budget limits

Provider `usedStorage` is recorded as a provider meter, not assumed to equal every file's logical size. On 12 November 2026 the populated public dataset reported zero while its current tree contained 16 regular Git files totalling 1,889,831 bytes. A current-tree sum also omits replaced/deleted objects retained by history.

The manually dispatched **Measure project storage capacity** workflow reads metadata only. It inventories advertised branches, tags, conversion refs and pull-request refs, then deduplicates Git blobs and large-file objects across their reachable commits. It checks that the default head and advertised refs are unchanged at the end. Missing metadata, inconsistent object sizes, changed refs or configured scan bounds fail the measurement rather than producing a complete-capacity claim. It never fetches source/annotation payloads or changes repository history.

The conservative project-budget basis used before production ingestion and writes is:

`max(provider_reported_bytes, reachable_unique_large_bytes) + reachable_unique_git_blob_bytes`

This intentionally retains the larger large-object/provider value and adds ordinary Git blobs plus LFS pointer blobs, including reachable historical versions. It can overcount where a provider meter already includes some Git data. It is not exact packed disk usage, an account bill, or proof of available account quota: Git tree/commit overhead, packing, unadvertised/unreachable objects and other account repositories remain outside the inventory. Account-wide capacity acceptance stays false.

The probe is bounded to 16 advertised refs, 200 distinct reachable commits and 500,000 tree-metadata entries per repository, with a 20-minute workflow timeout. The SDK's commit-listing call returns a complete history list before the commit-count bound is checked; expensive per-commit tree scans stop at the declared bound. Raising bounds requires an explicit code/configuration review; deleting or squashing history is not an automatic remedy.

Existing budgets remain 80 GB private and 10 GB public. Collection, private/public publication, pilot/reviewer uploads and training use this basis. Incomplete or changed metadata blocks new ingestion/writes; read-only restore remains available. The receipt retains the raw provider meter as a separate measurement. No paid upgrade, account-plan change or history deletion is performed.

The provider's [storage documentation](https://github.com/huggingface/hub-docs/blob/main/docs/hub/storage-limits.md), read on 12 November 2026 (file blob `84e1a36b133f104ca39b917b0127e271e4b553f2`), lists a 100 GB free private allowance, best-effort public storage, and separate Git repository/file-count recommendations. Its suggestions to buy storage, contact support or squash history are not this project's operating instructions. This project preserves revisions and stops within its configured free-service limits.

## Verified measurement, 12 November 2026

[Capacity run 43214811857](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43214811857) passed using metadata only. Private revision `7799d3a8975a628321d54b70f2828469efbccde4` retained 1,701,819,500 unique large-file bytes and 609,077,314 unique Git-blob bytes across 24 commits and one advertised ref: **2,310,896,814 budget-basis bytes**. Its provider meter matched the large-file total in this sample. Public revision `d66384951798e25c026f350994a1a0df897b7e20` retained **1,892,160 Git-blob bytes** across eight commits and one ref, with no large files and a zero provider meter. This is measured repository history, not account-wide capacity certification.

Snapshot staging uses commits of at most 100 files, within the provider's recommended 50–100-file HTTP upload batch range. Every commit uses the preceding immutable commit as its expected parent. All staged files are then downloaded and hash-verified at the final staging revision before a separate pointer commit. A timeout or conflict leaves the previous pointer intact; a retry uses a new snapshot identity and never overwrites a partial staging prefix. This bounds request size, not total runtime, and does not establish the cause of the earlier transient provider failure.
