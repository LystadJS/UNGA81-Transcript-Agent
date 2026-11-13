<p align="center">
  <img src="assets/readme-banner.svg" alt="USUN seal and UNGA81 Transcript Agent: source-linked analysis of United Nations proceedings" width="100%" />
</p>

<p align="center">
  <a href="docs/BROWSER_ANALYSIS.md"><img alt="JavaScript browser application" src="https://img.shields.io/badge/JavaScript-browser-062135?style=flat-square" /></a>
  <a href="site/release.json"><img alt="Browser release record" src="https://img.shields.io/badge/Browser-release_record-002D74?style=flat-square" /></a>
  <a href="docs/LATENT_COMPARISON.md"><img alt="Node.js 22 for tests" src="https://img.shields.io/badge/Node.js-22%20tests-062135?style=flat-square" /></a>
  <a href="research/README.md"><img alt="Python 3.11 or newer for optional research" src="https://img.shields.io/badge/Python-3.11%2B%20optional-062135?style=flat-square" /></a>
</p>

<p align="center">
  <a href="docs/BROWSER_ANALYSIS.md"><img alt="TF-IDF and cosine similarity" src="https://img.shields.io/badge/Methods-TF--IDF%20%2B%20cosine-002D74?style=flat-square" /></a>
  <a href="docs/LSA_COMPARISON.md"><img alt="PCA and LSA" src="https://img.shields.io/badge/Methods-PCA%20%2F%20LSA-002D74?style=flat-square" /></a>
  <a href="docs/PARTITION_METHODS.md"><img alt="k-means, PAM, and hierarchical clustering" src="https://img.shields.io/badge/Methods-clustering-002D74?style=flat-square" /></a>
  <a href="docs/HDBSCAN.md"><img alt="HDBSCAN" src="https://img.shields.io/badge/Methods-HDBSCAN-002D74?style=flat-square" /></a>
  <a href="docs/NMF.md"><img alt="NMF and Gaussian mixtures" src="https://img.shields.io/badge/Methods-NMF%20%2F%20GMM-002D74?style=flat-square" /></a>
  <a href="docs/DISPLAY_AUDIT.md"><img alt="UMAP and MDS visualization" src="https://img.shields.io/badge/Display-UMAP%20%2F%20MDS-002D74?style=flat-square" /></a>
</p>

<p align="center">
  <a href="https://lystadjs.github.io/un/transcript-agent/meeting-reports.html"><strong>Prepare a meeting report</strong></a>
  &nbsp;&middot;&nbsp;
  <a href="https://lystadjs.github.io/un/transcript-agent/archive.html">Browse the archive</a>
  &nbsp;&middot;&nbsp;
  <a href="docs/MEETING_REPORTING.md">Reporting guide</a>
</p>

## Purpose

On its _https://transcripts.un.org/en_ website, the United Nations has built a comprehensive repository for address and meeting transcripts created by using automatic speech recognition.  These transcripts preserve what diplomatic officials _said_, but this does not necessarily correlate to what deserves the most attention.  **The UNGA81 Transcript Agent transforms open-source meeting records into source-based evidence for diplomatic readouts, comparative text analysis, and nonrandom latent information discovery.**  Users can examine a single meeting or a range of proceedings, follow recurring issues, compare language across speakers and regions, and reference the passages behind each result.  

**The governing rule for this project is simple: an analytical claim should remain connected to its source, its denominator, and its limitations.**

## Start in the browser

**Start with [Meeting reports](https://lystadjs.github.io/un/transcript-agent/meeting-reports.html): select proceedings, inspect their evidence, and prepare a mission briefing, negotiation record or evidence digest.** No installation or coding is needed. Reports retain source context, recorded speaker information, coverage gaps and your separately labeled notes. Automatic five-class stance estimates remain withheld. The [advanced exploratory workspace](https://lystadjs.github.io/un/transcript-agent/) remains available for descriptive methods, clustering and component analysis.

## Choose a workflow

| Workflow | Use it for | Entry point |
| --- | --- | --- |
| **Meeting reports** | Select meetings, search exact source passages, reuse mission preferences, add evidence and notes, and export documented HTML, JSON and full evidence CSV. | [Open Meeting reports](https://lystadjs.github.io/un/transcript-agent/meeting-reports.html) · [Reporting guide](docs/MEETING_REPORTING.md) |
| **Advanced exploratory workspace** | Collect published transcripts on demand; analyze a meeting, topic, date range, or region; export visual reports and evidence. No installation or external AI API required. | [Open workspace](https://lystadjs.github.io/un/transcript-agent/) |
| **Daily transcript archive** | Browse the published, versioned collection with source coverage and permitted metadata downloads. Coverage remains partial; automatic stance estimates are withheld pending acceptance. | [Archive](https://lystadjs.github.io/un/transcript-agent/archive.html) · [Operations](docs/OPERATIONS.md) |
| **Latent-structure comparison** | Reopen saved runs; compare PCA/LSA, clustering, and component settings; inspect reviewed excerpts against their parent speeches. | [Open comparison](https://lystadjs.github.io/un/transcript-agent/latent.html) |
| **Local R / Shiny briefing** | Run the controlled D1 analysis, set tracked issues, review the five-slot briefing, and save an unsent Outlook draft. | [Local setup](un/ui/START_HERE.md) |

## Meeting-reporting workflow — no installation

1. Open [Meeting reports](https://lystadjs.github.io/un/transcript-agent/meeting-reports.html). Find proceedings by date, or select meetings in the [archive](https://lystadjs.github.io/un/transcript-agent/archive.html) and send them to the reporting workspace. Check current availability and explicitly load up to five meetings at a time.
2. Search the loaded English evidence. Choose a report template, set mission priorities, select supporting passages and add your own notes. Reusable mission preferences contain settings only; saved report JSON retains the source records and your work.
3. Choose **Prepare report**. Inspect the dated country expressions, U.S. comparison gaps and source context before circulation. Recorded affiliation does not verify national speaking capacity, and a missing extract does not establish neutrality. Prepare the report again after edits to update its exports.
4. Save the source-bound JSON to reopen your work. Download the script-free HTML report or the full evidence CSV. The CSV includes all passages from the selected meetings, independently of search and appendix selection, and excludes your notes. HTML can be printed from the browser.

Inventory and transcript requests reach [transcripts.un.org](https://transcripts.un.org/en); evidence inspection and deterministic reporting run on your device. The workspace does not upload reports or notes automatically. A browser may load a newer source revision than the scheduled archive; the saved report identifies the revision actually used. See the [reporting and export contract](docs/MEETING_REPORTING.md).

For topic/date-range analysis, regional filters, clustering or component methods, use the separate [advanced workspace](https://lystadjs.github.io/un/transcript-agent/) and its [collection and method guide](docs/BROWSER_ANALYSIS.md). Exploratory similarity is not policy agreement. The daily warehouse and research CSV snapshots below remain separate from these browser exports.

## Daily operational pipeline

The production package adds configured daily collection, immutable raw-source and SQLite revisions, research CSV snapshots, and a read-only public archive interface. GitHub Actions provides bounded daily processing; an owner-controlled **private Hugging Face dataset repository** provides durable storage. The deployed public archive uses a separate allowlisted metadata export and public repository; canonical transcripts, private research CSVs and annotations remain in private storage. The code does not purchase services or activate an account automatically.

**Five-level automatic stance remains gated on actual owner-reviewed labels, a trained checkpoint, and empirical acceptance.** Model preparation, training and evaluation interfaces do not supply a validated classifier. Uncertain, missing, conditional and collective evidence remains separate from neutral stance. Existing exploratory methods remain available independently.

Start with [operations and setup](docs/OPERATIONS.md), [architecture](docs/ARCHITECTURE.md), the [capability matrix](docs/CAPABILITIES.md), and the [model card](docs/MODEL_CARD.md). The capability matrix distinguishes implemented engineering, external configuration, deployment, and empirical acceptance. No fourteen-day operating record or diplomat usability acceptance is claimed by committing these files.

## Optional developer and local R workflows

The following installation steps apply only to the separate R briefing application. They are not required to collect, summarize or analyze transcripts in the browser.

### Local R & Shiny workflow

For the Windows briefing application, install **R 4.3 or newer** and use a short checkout path to avoid Windows extraction and model-filename limits. From PowerShell:

```powershell
git clone https://github.com/LystadJS/UNGA81-Transcript-Agent.git
cd UNGA81-Transcript-Agent\un\ui
.\Setup.bat
.\Verify.bat
.\Start.bat
```

Choose **Use the installed pipeline**, enter a reporting date, and add up to 20 issues to track. Generate the readout, examine the evidence and coverage, then save the **unsent** `.eml`, HTML, plaintext, or audit archive (and PDF when a compatible renderer is available). User-defined topics retrieve candidate passages; they do not alter the frozen corpus or automatically classify national positions. Use [the local UI guide](un/ui/START_HERE.md) for interface modes and [the D1 setup guide](un/START_HERE.md) for command-line runs and dependency controls.

## How it works

```text
UN transcript inventory + published source records
                     |
           Source identity and provenance
                     |
    Date / meeting / language / region selection
                     |
      Exact-text deduplication + topic matching
                     |
        Descriptive and optional exploratory
              text-analysis methods
                     |
      Coverage + diagnostics + source passages
                     |
     Visual HTML / JSON / CSV / printable report
             (local R also: EML draft)
```

**Collection and interpretation remain separate operations.** The collector records which meetings and transcript segments were available; eligibility rules and deduplication determine what enters each analysis; methods describe that retained text. Reports preserve the source links, selection settings, and missing-data accounting needed to inspect a result rather than treating the chart as the evidence.

### Implemented method layers

| Layer | What is available | Interpretive boundary |
| --- | --- | --- |
| **Descriptive browser analysis** | Frequencies by date and speaker region, passage lengths, TF-IDF, and cosine similarity. | Counts and lexical resemblance describe observed text, not support or opposition. |
| **Exploratory browser analysis** | PCA or LSA; k-means, PAM, hierarchical clustering, HDBSCAN, and Gaussian mixtures; NMF components; UMAP and optional MDS displays; group-refit and sensitivity diagnostics. | Clusters, components, and distances have no automatic diplomatic labels. Noise, ambiguity, withheld fits, and population changes remain visible. |
| **Frozen R D1 pipeline** | Rule-based issue evidence, frozen TF-IDF, PCA/PCoA, clustering and network diagnostics; **12 executable adapters out of 42 registered methods**. | Daily publication gates remain separate from research diagnostics. An adapter's existence is not authority to publish its output. |

[Detailed method inventory](docs/INVENTORY.md) · [Latent comparison and saved-run contracts](docs/LATENT_COMPARISON.md) · [Research roadmap](docs/NEXT_STEPS.md)

## Outputs, review, and limitations

Browser reports can be exported as standalone HTML with linked source evidence, JSON containing settings and analytical results, and CSVs for retained passages and supported diagnostics. The local R workflow additionally assembles a USUN-themed Outlook draft, with predefined analytical slots and country readouts. **These outputs are drafts for inspection, not automatic judgments about countries or instructions to distribute a briefing.**

English transcript tracks may include interpretation or automatic transcription. Missing or late source records remain coverage gaps; an individual transcript segment is not necessarily a complete speech. Exact-text deduplication does not establish that near-duplicates are absent. A small or dependent set of meetings cannot support claims of independent replication merely because it contains many passages.

**Research status (8 October 2026):** the lexical/semantic, country-name, agenda, and speaker-attribution controls are development-stage diagnostics. Production-shaped collection tests use synthetic responses. The **37 reserved held-out meeting transcripts remain unopened**, and no substantive alignment, stance, or forecasting model has been authorized for release by these tests. See [development controls](docs/DEVELOPMENT_CONTROLS.md), [synthetic acceptance](docs/PRODUCTION_SHAPED_ACCEPTANCE.md), and [roster-adapter verification](docs/ROSTER_ADAPTER_PUBLICATION.md).

## Repository guide

| Path | Contents |
| --- | --- |
| [`site/`](site/) | Browser collector, local numerical analysis, report builder, and comparison workspace |
| [`src/`](src/) · [`config/`](config/) · [`tests/`](tests/) | Operational collection, persistence, export and model contracts; versioned maintainer settings; source-free tests |
| [`un/`](un/) | R analytical pipeline, Shiny UI, email templates, configuration, and frozen policies |
| [`research/`](research/) | Development-only text, representation, and evaluation methods with explicit validation boundaries |
| [`docs/`](docs/) | Method contracts, operating guides, acceptance records, and research roadmap |
| [`reports/`](reports/) · [`examples/`](examples/) | Evidence-oriented examples and historical reports |

The browser and comparison releases are recorded in [`site/release.json`](site/release.json). For reproducible local checks, start with [`REPRODUCE.md`](REPRODUCE.md). Historical acceptance records are labeled by their original run and should not be mistaken for a new full-system test. See [open-PR triage](docs/PR_TRIAGE.md) before reusing unmerged work.

<sub>Public reports are analytical aids. Verify quotations, transcription, speaker attribution, coverage, and conclusions against the linked UN records before citing or circulating findings.</sub>

## Historical issue infrastructure (1.34.0)

The [implementation ledger](docs/implementation-agenda/STATUS.md) records progress toward the three-input, ten-year issue workflow. The new `issue-archive.html` workspace consumes verified, versioned historical bundles and saves frozen reports. The separate historical issue archive is not provisioned; use the existing saved-collection issue page while historical source acquisition and empirical assessment remain incomplete. The current-session meeting archive above is deployed. Maintainer store/ingestion modules use Python standard libraries; end users need only a browser. Experimental model code is not a calibrated production trajectory.
