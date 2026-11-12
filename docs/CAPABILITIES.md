# Current capability and acceptance matrix

This is the current operational status guide. `site/release.json` identifies the released browser version. Historical validation receipts retain their original scope and date; they are not a fresh full-system test.

| Capability | Implementation boundary | Deployment / empirical status |
| --- | --- | --- |
| Existing browser collection and reporting | Browser-selected public UN inventory, source links, summaries, recovery and exports | Existing deployed product; current live service health requires the separate live check |
| Durable operational collection | Versioned selection, bounded refresh/backfill, immutable source revisions, SQLite warehouse | Requires owner-controlled private HF storage configuration and a successful first run |
| Research CSV snapshots | Consistent keyed exports, dictionary, hashes, source and run history | Synthetic contracts do not establish complete real-source coverage |
| Public archive | Read-only manifest/partition browser with source and coverage metadata | Unconfigured until a permitted public snapshot URL is supplied |
| Five-level semantic stance | Candidate training, source-bound inference contract, explicit uncertainty and evaluation policy | **No accepted trained model or owner benchmark is supplied** |
| Issue discovery | Versioned catalog and source-linked candidate discovery | New candidates do not silently become validated policy propositions |
| Exploratory methods | Existing browser TF-IDF, dimensional methods and clustering remain available | Exploratory patterns do not establish alignment, influence or causation |
| Historical issue/vote research | Separate private ingestion and research structures | Public historical archive and fitted empirical models remain unaccepted |
| R/Shiny D1 | Separate preserved local workflow | Twelve executable adapters among 42 registered methods; not 42 operational methods |
| Daily operation | Scheduled workflow plus explicit failure/freshness reporting | Fourteen-day observation, restore drill and capacity acceptance remain outstanding |

## Acceptance dependencies

1. Configure private durable storage; optionally configure distinct public storage and the public manifest URL.
2. Execute and retain real collection/recovery receipts without opening reserved material.
3. Complete the owner-labeled 300-example codebook pilot, then expand benchmark coverage.
4. Train and assess the candidate on source-disjoint calibration and untouched test data; record failed gates as failures.
5. Complete representative diplomat usability sessions and the fourteen-day observation period.

The operational release may collect and expose permitted descriptive metadata while stance remains withheld. Publication of code is not completion of external account setup, human labeling, model accuracy acceptance or an elapsed observation period.

## Prior development summary repair

Release 1.40.0 repaired daily-summary extraction using the owner's three-day development review. The repair replay covers 12 meetings and 439 retained segments. A new owner review of repaired output and untouched acceptance remain outstanding. See [DAY_SUMMARY_EVALUATION_STATUS.md](DAY_SUMMARY_EVALUATION_STATUS.md) for the distinction between the earlier missing-sample receipt and the later repair evidence.

## Licensing and data handling

The codebase includes third-party numerical licenses in `site/NUMERICS_LICENSES.txt` and `site/HDBSCAN_LICENSE.txt`. No new blanket license is applied to inherited code, UN transcript text or annotation records. Resolve redistribution rights before adding source-bearing fields to public exports; preserve package/model license notices. Public availability alone does not establish a redistribution license.

The [PR triage](PR_TRIAGE.md) records the disposition recommended for existing unmerged work. It does not merge, close or promote those branches.
