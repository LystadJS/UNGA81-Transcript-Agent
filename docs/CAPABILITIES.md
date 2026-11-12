# Current capability and acceptance matrix

This is the current operational status guide, updated after the first successful private archive publication on 12 November 2026 (UTC). `site/release.json` identifies the released browser version. Historical validation receipts retain their original scope and date; they are not a fresh full-system test.

| Capability | Implementation boundary | Deployment / empirical status |
| --- | --- | --- |
| Existing browser collection and reporting | Browser-selected public UN inventory, source links, summaries, recovery and exports | Source PR #187 merged after all six checks passed, including actual live collection; source Pages deployment succeeded |
| Durable operational collection | Versioned selection, bounded refresh/backfill, immutable source revisions, SQLite warehouse | Four actual runs published to the owner's private Hugging Face dataset; successive fresh runners restored the archive and continued collection |
| Research CSV snapshots | Consistent keyed exports, dictionary, hashes, source and run history | Four real private snapshots published; latest corrected coverage records 569 known / 314 stored meetings and 22,548 current segments; coverage remains partial |
| Public archive | Read-only manifest/partition browser with source and coverage metadata | Unconfigured until a permitted public snapshot URL is supplied |
| Five-level semantic stance | Candidate training, source-bound inference contract, explicit uncertainty and evaluation policy | **No accepted trained model or owner benchmark is supplied** |
| Issue discovery | Versioned catalog and source-linked candidate discovery | New candidates do not silently become validated policy propositions |
| Exploratory methods | Existing browser TF-IDF, dimensional methods and clustering remain available | Exploratory patterns do not establish alignment, influence or causation |
| Historical issue/vote research | Separate private ingestion and research structures | Public historical archive and fitted empirical models remain unaccepted |
| R/Shiny D1 | Separate preserved local workflow | Twelve executable adapters among 42 registered methods; not 42 operational methods |
| Daily operation | Scheduled workflow plus explicit failure/freshness reporting | Manual activation, remote restore/continuation and isolated real-provider interruption recovery passed; fourteen-day scheduled observation and account-wide capacity acceptance remain outstanding |

The first [actual archive run](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43154577386) reported 87 meetings and 76,284,090 downloaded bytes, with partial coverage. Its private snapshot ID is `20261112T042431Z-98493e2e5511` (UTC). The [second actual run](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43155142584) successfully restored that archive and published `20261112T043029Z-314632fa4d79`, reporting 78 downloaded meetings and 75,470,172 bytes. These run counts may overlap through refreshes and must not be added as unique meetings. Both runs had partial coverage, successful private publication, no configured public storage, and model status `not_evaluated_missing_labels`. These are operational receipts, not empirical stance acceptance. See [the acceptance record](OPERATIONAL_ACCEPTANCE.md) for the deployment and recovery boundaries.

The source repository's Pages deployment succeeded. The main portfolio [mirror update in PR #151](https://github.com/LystadJS/LystadJS.github.io/pull/151) remains unmerged: its mirror audit passed, while 27 inherited portfolio tests failed with the relevant tests and assets unchanged from its main branch. The preferred portfolio URL therefore must not be described as having received this operational update.

## Acceptance dependencies

1. Complete account-wide capacity acceptance and continued recovery observation. Isolated real-provider interruption recovery passed in run 43184679678; production data and its pointer were left untouched.
2. Complete the fourteen-day scheduled observation record. Configure distinct public storage and the public manifest URL only if metadata publication is desired.
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
