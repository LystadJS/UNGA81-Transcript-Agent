# Ten-year issue workflow execution ledger

Updated 24 October 2026. Engineering checks use invented metadata; they are not empirical model acceptance. The public archive is not provisioned. Official GA/SC vote files are verified in private staging; the private GA import is capacity-limited at98,000 accepted rows and 7,740 SC rows are stored. Source acquisition, owner-confirmed evaluation and operational deployment remain release gates for the desired end state.

| Task | Implemented result | Remaining work |
| --- | --- | --- |
| A1 | Reader workflow, report, failure and performance contract | Measure full production reference workload |
| A2 | Versioned source/evidence/vote/artifact/eligibility schemas | Production hosting selection/provisioning |
| A3 | Humanitarian ontology and requested-context resolver | Source-supported ontology expansion |
| A4 | Same-estimand temporal/source-separated assessment contract | Owner-confirmed empirical benchmark |
| B1 | SQLite schema migration and rollback backup | Hosted operational migration acceptance |
| B2 | Immutable revisions, idempotent writes, transitive invalidation | Production-scale evaluation |
| B3 | Official GA v6/SC v7 vote bytes/headers inspected; recent transcript inventory adapter | Historical transcript/committee coverage and publication permissions |
| B4 | Strict normalized transcript adapter and hash checks | Remote format adapters after inspecting actual formats |
| B5 | Actual GA/SC CSV adapters, recorded-vote modality, exact country joins, decision/subpart preservation | Other voting families |
| B6 | Source-linked resolution/policy binding validation | Reviewed actual resolution bindings |
| B7 | Bounded resumable ingestion, retry/quarantine/checkpoints | Source-specific network acquisition |
| B8 | Incremental refresh and atomic publication/health safeguards | Approved feed, host, scheduler and live freshness |
| B9 | 7,740 SC rows/516 resolutions reconciled; private 98,000 GA rows imported with durable cursor | Remaining GA import paused at200 MiB free-space reserve; more storage required |
| C1 | Bounded policy/year/body bundles, independent affiliation rosters, method provenance, hashes, privacy allowlists | Populated permitted historical snapshot |
| C2 | IndexedDB cache, verified reuse/recovery, resumable shards | Production browser acceptance on real scale |
| C3 | Selective policy/year/body transport, exact query filters, immutable subset identities and legacy fallback | Real-data database/query parity |
| C4 | Fully versioned, hash-verified browser result cache and targeted invalidation | Production accepted-model artifacts |
| D1 | Empty owner-review packets and source/temporal splits | Actual owner-confirmed labels |
| D2 | Existing conservative rule extractor adapter | Representative empirical assessment |
| D3 | Audit checkpoint remains segregated | Resource-approved production classifier and benchmark |
| D4 | Not implemented | Approved semantic model, benchmark and resource limits |
| D5 | Extraction assessment gates and abstention accounting | Accepted candidate evaluated on real labels |
| D6 | Canonical revision-bound country-event materialization | Production event extraction and acceptance |
| E1 | Country/date/context panels and explicit missingness | Production panel reconciliation |
| E2 | Exact-date observed comparison and changing U.S. reference | Real-source acceptance |
| E3 | Experimental categorical recency prototype | Fitted state-space estimator, validation and calibrated uncertainty |
| E4 | Experimental one-sided categorical kernel prototype | Compatible fitted smooth estimator and held-out validation; prototype is not a GAM |
| E5 | Separate observed vote-alignment baseline | Complete verified voting coverage/bindings |
| E6 | Not implemented | Dynamic vote estimator and eligible empirical benchmark |
| E7 | Eligible same-estimand tournament and fallback | Actual fitting/assessment of eligible production candidates |
| E8 | Versioned artifact/dependency contracts | Durable production accepted-artifact materialization |
| F1 | Canonical policy/context resolver; unsupported qualifiers withheld | Broader validated topic coverage |
| F2 | Country-count opinion climate including recorded unknowns | Real snapshot acceptance |
| F3 | Source-linked issue overview with named country positions, conditions, dated U.S. comparisons and historical/current gaps | Broader source-supported proposal detail and real archive acceptance |
| F4 | Opinion distributions and country/policy matrix | Production-scale usability evaluation |
| F5 | Historical coverage and dated U.S. reference observations | Membership/eligibility visualization and certified coverage |
| F6 | Automatic observed country charts and explicit gaps | Accepted-model estimates/uncertainty overlay |
| F7 | Worker-based single-button archive report orchestrator | Historical snapshot provisioning; normal path currently unavailable |
| F8 | Frozen report envelope, exclusions, inputs/results and source versions | Production real-snapshot replay acceptance |
| G1 | Source-free actual-browser acceptance passed for 1.34.2 | Real populated archive replay |
| G2 | Maintainer store/export checks and bounded ten-year synthetic browser timing harness | Actual CI timings pending; production data/device budgets remain unmeasured |
| G3 | 1.34.2 source and mirror merged; deployment/live hashes passed | Full public data/model release withheld |

Next execution sequence: finish integration/browser acceptance; publish the source-free engineering milestone; obtain and verify permitted source-family downloads; ingest bounded reconciled year/body shards; collect owner-confirmed evaluation labels; assess extraction and compatible models; provision the historical snapshot; verify the normal three-input workflow against actual evidence. No manual prompt is needed to advance an unblocked engineering dependency. External access and actual owner labeling cannot be replaced by fabricated evidence.

Storage: only C: is available; the import preserves200 MiB headroom. The368,130,256-byte GA download was replaced by an11,307,870-byte gzip after its decompressed SHA-256 matched exactly. Only our superseded/reproducible scratch artifacts were removed. Existing user collections were untouched. Resume bulk import only with at least1 GiB free and the saved source/window/adapter identity. Private rows remain unbound to policy; full-resolution votes never become isolated policy positions.

Automatic continuation is active hourly in the owning chat. It advances unblocked dependencies, stays quiet when conditions are unchanged, and resumes bulk ingestion only when at least 1 GiB is free. The remaining public archive and empirical model gates are unchanged.

The full GA CSV window reconciles 205,738 rows in 1,066 resolution/decision groups, with no blank totals, duplicate country codes or mismatched publisher totals. The private database contains only 98,000 of those rows; 107,738 remain to import. Input reconciliation does not establish complete database coverage or a policy position.

The GA database currently has 507 complete 193-country groups plus a partial 149-of-193 group for A/RES/77/208. That partial group is not a complete published vote distribution. The full-file reconciliation and the partial database are distinct results.

A read-only engineering replay reproduced all 98,000 imported GA normalized outputs against the authoritative source hashes and evidence fields. The cursor was explicitly rebaselined to the current dependency hashes without changing offsets or counts; its original backup and review receipt preserve lineage. This engineering verification is not owner-confirmed policy annotation.

24 October selective-history engineering: independent source-family/date/body affiliation rosters preserve unknown-country denominators while policy shards are pruned. Subsets retain the full pinned manifest plus a unique selection cache identity. Incompatible ontology/extractor versions create explicit comparison gaps; unsupported ontologies are withheld. Legacy unversioned evidence stays marked. Generation validates the same topic/date bounds as reopening and rejects frozen reports above the 60 MB reopen limit. Source-free Node and Python checks are recorded in SELECTIVE_HISTORY_ACCEPTANCE.md; actual-browser CI passed and version 1.34.2 was published and live-verified. Bulk import remains paused below the 1 GiB restart threshold; private source and cursor pins were untouched.

Release acceptance: source PR137 merged (f5f7c5651702e5a84032b18d150dd6c8d2d301a6); all four source workflows passed, including actual-browser run40057277533 and store run40057277497. Website PR52 merged (b08af2fb19f4d0e634f1d4746d72195df3d664cb) after regression40057353371 and mirror audit40057353303 passed. Deployment40057594264, live verifier40057594452 and postmerge mirror audit40057594449 passed. A separate ten-asset hash check and visible live controls/availability safeguard confirmed 1.34.2. Synthetic save/reopen acceptance is distinct from actual populated archive acceptance. Current engineering agenda remains approximately60% complete; no empirical model or archive completeness claim follows.

Next unblocked engineering: improve the source-linked substantive issue overview (F3) and add browser performance budgets/acceptance at representative synthetic historical scale (G2), preserving observed-only fallback and all empirical gates. Continue automatically. Bulk import remains stopped at its durable 98,000-GA/7,740-SC checkpoint until C: has at least1 GiB free; last check191,012,864 bytes.

Current update (23 October local time): country-first source-linked summaries and ten-year synthetic browser performance acceptance implemented. Current country and U.S. qualifications survive deduplication; summary comparison dates and sources remain explicit and distinct from the latest U.S. expression. Report indexes replace repeated country/date scans; the deterministic fixture retained the exact pre-optimization report hash. Local summary/report/client/model checks passed; actual-browser performance, save/reopen and publication remain pending for 1.35.0. No private staging, source imports, reserved transcripts or model acceptance changed.
