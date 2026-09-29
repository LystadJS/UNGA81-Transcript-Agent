# Current project inventory

Updated 29 September 2026 for the I5 extension. The original inventory used
application commit `42125d1`; current changes and new acceptance evidence are
documented in [I5](I5.md). Historical results remain identified below.

The project is a local R transcript-processing and draft-briefing application,
with a Shiny interface and an explicitly gated analytical research layer.
It is not yet a fully validated diplomatic stance, forecasting, or autonomous
monitoring system. Twelve of 42 registered analytical methods have executable D1
adapters. Recording a method's prerequisites is not executing that method.

## Repository layout

| Location | Purpose |
|---|---|
| `un/ui/` | Shiny app, upload/practice backend, USUN theme, local icons, preview, UI tests |
| `un/interfaces/shiny_v1.R` | Hash-pinned bridge into the D1 pipeline |
| `un/R/` | Source intake, summarization, validation, history, analytics, publication, email and figures |
| `un/config/`, `un/design/` | Operational configuration, frozen policies, method registry and design contracts |
| `un/scripts/` | Windows setup, run, scheduling, API-key setup and verification helpers |
| `un/examples/` | Replay data and preserved reference/history fixtures |
| `un/output/`, `un/validation/` | Shipped historical runs and validation evidence |
| `un/tests/`, `un/ui/tests/` | Regression, adapter and controller test scripts |
| `un/templates/`, `un/assets/` | Outlook email theme and approved seal |
| `docs/legacy/` | Preserved earlier repository documents, not current execution instructions |

The imported package has 2,290 files. Its longest member path is 186 characters.
Use a short checkout location. Hash-based model filenames intentionally retain
their full identities; the surrounding descriptive paths were shortened.

## Capabilities

- Choose dates and up to 20 user-defined tracked issues; add literal related
  phrases and passage exclusions. Preserve source quotations and character offsets.
- Review topic candidates, suggested research themes, coverage and diagnostics.
- Produce unsent EML, HTML and plaintext; optionally PDF when a renderer works.
  Export evidence CSV, settings JSON and an audit ZIP.
- Run analysis in a separate R worker, show progress, support cancellation, block
  duplicate clicks, and warn when settings no longer match completed results.
  Server generation, duplicate-click, cancellation and disconnect tests pass;
  complete browser acceptance is outstanding.
- Save and restore topic preferences in the browser without saving transcript text there.
- Archive source bytes, hashes, requests, run configuration, artifacts, evidence,
  method status and publication decisions for audit/reproduction.
- CLI source modes include live UN collection, supported local JSON/DOCX/ZIP
  intake, and archived replay. The live collector targets configured General
  Assembly/general-debate sources, not an unrestricted all-UN crawler.
- CLI supports exact-excerpt analysis and a separately configured external-model
  generation/review path. The Shiny adapter prohibits external AI processing and
  uses extractive configuration for live runs. A model review is not human review.
- Windows scheduling helpers exist but this repository has not installed or
  activated a daily task. Nothing automatically sends email.

## User workflow and the three interface modes

Set up R and dependencies with the pipeline/UI setup instructions, then launch
`un/ui/Start.bat`. Choose input mode, dates and issues; optionally refine phrases;
generate; inspect source evidence and coverage; save an unsent draft for review.

| Mode | Actual behavior |
|---|---|
| Installed pipeline | One reporting date. Uses bundled replay when that date has an example folder; otherwise runs the live D1 collector with extractive/no-external-AI settings. Processes the full corpus before applying user topics. |
| My transcript files | TXT with required metadata, TXT ZIPs, or statement CSV. Uses the separate prototype backend, not the D1 historical/registry reconciliation pipeline. |
| Practice | Eighteen fictional training statements, dated 24 September 2026. Uses the prototype backend. |

Installed-pipeline state is isolated by request hash. User topics do not filter
the discovery corpus or rewrite the legacy Iran/Cuba/Ukraine/AI codebook. This
is not a shared rolling longitudinal-history workflow across arbitrary UI requests.

Sources: [UI input contract](../un/ui/docs/INPUTS.md),
[integration contract](../un/ui/docs/INTEGRATION.md),
[adapter implementation](../un/interfaces/shiny_v1.R),
[CLI entry point](../un/run_daily.R).

## Methods actually implemented in D1

| ID | Method | What it does and publication boundary |
|---|---|---|
| M01 | Rules and lexicons | Retrieves issue evidence candidates. Does not establish issue absence or calibrated classification. |
| M02 | Frozen TF-IDF and cosine similarity | Builds sparse lexical features; freezes vocabulary/IDF per namespace; transforms statements and equally pools distinct statement text by country, with L2 normalization. Similarity is lexical, not diplomatic alignment. |
| M05 | PCA | Primary two-dimensional descriptive country map, with frozen-reference projection and quality/source checks. The only registered producer that can release a ready analytical email packet, for O3. |
| M06 | PCoA/classical MDS | Geometry challenger on Euclidean chord distances from the same TF-IDF space. Not independent confirmation of PCA and not an alternative automatic publication producer. |
| M07 | Hierarchical clustering | Average linkage primary; complete and Ward.D2 sensitivity checks; candidate k=2..6. Uses full feature distances, not the plotted 2D coordinates. Audit-only. |
| M09 | PAM/k-medoids | Candidate k=2..6, silhouette/size selection, exemplar medoids and 100 fixed-seed roster-deletion replicates per k. Audit-only. |
| M08 | K-means | Multistart full-feature clustering with roster-deletion checks. Audit-only. |
| M31 | Lexical similarity network | Versioned cosine edges; stance/event layers unavailable. Audit-only. |
| M32 | Louvain | Weighted lexical community detection and stability checks. Audit-only. |
| M33 | Leiden | Weighted modularity communities and stability checks. Audit-only. |
| M34 | Spectral clustering | Normalized-adjacency partitioning with eigenspace checks. Audit-only. |
| M36 | Network metrics | Single-snapshot degree, strength, betweenness, components and density; temporal comparisons unavailable. Audit-only. |

The runtime adapter list in [09_method_registry.R](../un/R/09_method_registry.R)
is authoritative for implementation. The registry CSV still contains original
`design_only` labels, even for executable adapters; those static labels are not current
execution status. The runtime writes actual method and prerequisite ledgers.

### Separate UI research analysis

[ui/R/analysis.R](../un/ui/R/analysis.R) implements a separate per-run TF-IDF
representation, average-linkage and PAM comparisons, silhouette and size checks,
12 roster-deletion replicates for each selected method, descriptive PCA/PCoA,
cluster-specific terms and example passages. Its reference is per-run, not the
frozen D1 M02 reference. It needs at least 12 eligible nonempty feature vectors
for clustering. Suggested themes are research candidates, never released O2 results.

## Exactly five analytical email slots

1. O1: fixed-topic / user-tracked issue monitor.
2. O2: emerging issues.
3. O3: country discourse map.
4. O4: rhetorical movement.
5. O5: discourse-network changes.

Country readouts follow, grouped by region and alphabetized. Slots remain present
when unavailable, with reasons. Five slots does not mean five working/released
models. O1 candidate counts do not constitute a released classifier; O2, O4 and
O5 lack released producers. Only M05/O3 has a conditional release path. M07/M09
remain audit-only even if their engineering screens pass.

Source: [publication contract implementation](../un/R/15_publish_packets.R).

## Limits and known gaps

- Literal matching is not semantic relevance, stance, support, importance, or
  policy alignment. Non-match is unresolved. Accuracy/recall is not established.
- Thirty registry methods remain unimplemented: embeddings, supervised issue
  and stance models, advanced topic models, longitudinal change, further network models,
  forecasting and diffusion are roadmap items. No implemented human-gold-label
  import adapter is declared by the current readiness context.
- The UI discovery branch is English-only based on declared metadata; no language
  detection or translation. File-upload mode does not perform authoritative
  country-registry reconciliation or comprehensive near-duplicate resolution.
- Upload/practice requests span at most 32 dates; installed-pipeline mode accepts
  only one date. Up to 20 topics, 100 characters per label, and 30 include/exclude
  phrases per list. TXT 2 MB; CSV 50 MB; total upload/uncompressed ZIP text 100 MB;
  at most 2,500 combined statement rows.
- UI research fitting is capped at 500 eligible texts and 5,000 terms. D1 feature
  policy separately caps 1,000 statements, 250 countries and 10,000 terms, plus
  character/matrix resource limits. These are different backends with different caps.
- Frozen references check R/package/tokenizer environment identity. A copied
  Linux reference is not guaranteed reusable on Windows; use the prescribed fresh
  local reference setup instead of weakening integrity checks.
- On the archived 39-speech replay, both hierarchical and PAM clustering failed
  their quality screens. Their groupings are not released geopolitical blocs.
- Full browser acceptance and native Outlook rendering remain
  outstanding. Static screenshots and MIME checks do not establish those.
- The most recent Windows backend check was 96/97: PDF export failed when the
  detected Python launcher could not run. The subsequent I5 server acceptance installed `zip` in an isolated QA library
  and passed generation/cancellation/disconnect checks. PDF generation is optional and environment-dependent.
- EML generated by the UI adapter wraps the portable HTML in a new MIME draft;
  it does not reuse the CLI's CID-image MIME assembly. Treat native Outlook image
  rendering as unverified for that path.
- Live-source intake depends on source availability/schema. This inventory did
  not rerun collection or prove a newly downloaded UN ZIP is accepted.
- The separate September 28 five-email/383-turn execution bundle described in
  the old reproduction document is not included in this repository import.

## Validation evidence, with dates/scopes kept separate

| Evidence | Recorded result |
|---|---|
| Earlier checkpoint documents | 371 inherited tests |
| Later integrated Linux acceptance | 373 inherited tests + 97 UI backend + 9 adapter; full 39-speech replay and topic invariance recorded |
| Recent Windows packaging checks | 62 R files parsed, 9 adapter checks passed, 2,567 saved references resolved, checksums/extraction passed; backend 96/97 |
| Theme update | Actual UI constructor rendered; desktop/mobile static previews passed; no full Shiny startup |
| I5 extension | New regression and controller acceptance; see [I5 evidence](../un/validation/i5/README.md) |

The 371 and 373 totals are different historical records, not a fresh combined
claim. Dependency CSVs likewise contain build-environment snapshots, not a live
inventory of the user's machine. See [integration acceptance](../un/validation/SHINY_CHECK.md),
[packaging report](packaging.md), and [theme checks](../un/ui/THEME.md).

## Complete registered-method inventory

The following implementation classification uses the current executable adapter
list. Registry intent and package candidates are not promises of operational support.

| ID | Registered method | Current D1 implementation |
|---|---|---|
| M01 | Fixed-topic rules and lexicons | Implemented; publication limits above |
| M02 | TF-IDF and cosine similarity | Implemented; publication limits above |
| M03 | Sentence and document embeddings | Not implemented |
| M04 | Fixed-topic semantic relevance | Not implemented |
| M05 | Principal components analysis | Implemented; publication limits above |
| M06 | Principal coordinates analysis / classical MDS | Implemented; publication limits above |
| M07 | Hierarchical clustering | Implemented; publication limits above |
| M08 | K-means | Implemented within I5 scope above; audit-only |
| M09 | PAM / k-medoids | Implemented; publication limits above |
| M10 | UMAP | Not implemented |
| M11 | Unpenalized logistic issue classifier | Not implemented |
| M12 | Elastic-net multilabel issue classifier | Not implemented |
| M13 | Random forest classifiers | Not implemented |
| M14 | Gradient-boosted trees | Not implemented |
| M15 | Embedding plus regularized classifier | Not implemented |
| M16 | Fine-tuned text transformer | Not implemented |
| M17 | Proposition-specific stance models | Not implemented |
| M18 | Latent Dirichlet allocation | Not implemented |
| M19 | Structural topic model | Not implemented |
| M20 | Embedding-topic pipeline with cluster descriptors | Not implemented |
| M21 | HDBSCAN density clustering | Not implemented |
| M22 | Within-country historical distance | Not implemented |
| M23 | Isolation-forest anomaly detection | Not implemented |
| M24 | Change-point detection | Not implemented |
| M25 | Longitudinal Procrustes alignment | Not implemented |
| M26 | driftmapR movement and resampling | Not implemented |
| M27 | Dynamic cluster correspondence | Not implemented |
| M28 | Hidden Markov model | Not implemented |
| M29 | Latent transition analysis | Not implemented |
| M30 | Dynamic mixture model | Not implemented |
| M31 | Separate similarity and stance networks | Implemented within I5 scope above; audit-only |
| M32 | Louvain communities | Implemented within I5 scope above; audit-only |
| M33 | Leiden communities | Implemented within I5 scope above; audit-only |
| M34 | Spectral clustering | Implemented within I5 scope above; audit-only |
| M35 | Stochastic block models | Not implemented |
| M36 | Network structure metrics | Implemented within I5 scope above; audit-only |
| M37 | Issue / stance / shift / membership forecasting | Not implemented |
| M38 | Temporal transformer / sequence model | Not implemented |
| M39 | Discrete-time / survival adoption hazard | Not implemented |
| M40 | Network autocorrelation | Not implemented |
| M41 | Relational event models | Not implemented |
| M42 | Bayesian diffusion model | Not implemented |
