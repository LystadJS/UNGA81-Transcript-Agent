# Daily UN briefing: full analytical backend, five-output email

**Design D1 · 25 September 2026 · based on R workflow 2.1.0**

**Delivery status:** Architecture, 42-method registry, data contracts, publication contract, and native-R structural tests. This is not an upgraded production workflow and does not claim that the proposed models have been fitted, run on the speeches, or deployed. The v2.1 source and its archives remain unchanged.

## 1. Decision

Build two deliberately separate layers:

1. **Analytical backend:** register every previously discussed mechanism; process new eligible data with each appropriate fitted method; refit on a controlled schedule; retain every result, diagnostic, failure, and non-delivery reason.
2. **Editorial/reporting layer:** accept only five fixed analytical products, assembled from released source-supported results. It must not discover and attach arbitrary charts or expose a new section simply because another model ran.

The email retains the existing masthead, executive takeaway, and region-grouped country summaries. “Only five outputs” applies to the analytical insert, not to deletion of the requested country readouts. Existing prevalence bars, the region-by-issue heatmap, the issue co-occurrence network, nearest-neighbor lists, dendrograms, and research forecasts become **audit-only** rather than additional inline figures.

```text
Source collection + immutable evidence archive
                    |
          Versioned feature / label store
                    |
        All-method registry and run accounting
          /            |                \
   Current results   Model diagnostics   Forecast/research results
          \            |                /
           Validation + publication rules
                    |
        Exactly five reporting products
                    |
Approved USUN email + country summaries by region
                    |
   Separate full audit and reproduction package
```

“Run all methods” means every method is considered on every daily run. Eligible inference and due fits execute; unchanged eligible results can be reused with exact provenance. Missing labels/history, unsupported methods, failed diagnostics, unavailable dependencies, and resource limits produce explicit status rows. **Registration, a cached result, and a newly executed fit are different events.**

## 2. The exact five outputs

### O1. Fixed-topic monitor — Iran, Cuba, Ukraine, AI

Always display four rows, in that order. Each row gives countries with supported topic presence, the available-country-text denominator, and unresolved decisions. Missing source texts appear separately in the coverage note; they are never added to the “absent” count. Preserve the additional broad categories in the backend.

For an issue with A available country texts:

`present + absent + unresolved = A`

This is a count of countries represented in the retrieved, scoped corpus—not a census of all UN members. Report scoped inventory incompleteness independently. Do not treat silence, a failed retrieval, an unresolved model decision, and an explicitly stated neutral position as equivalent.

**Methods:** rules, TF-IDF, embeddings, semantic reference matching, all supervised issue-classifier variants, and proposition-specific stance classification. The rule and embedding components retrieve candidates and provide comparisons; released task-specific models produce the published decisions. They are not combined by an unvalidated majority vote.

**Stance is about an explicit proposition**, not about a country or broad subject in the abstract. For example, a model may code a statement about a named sanctions measure, a specified nuclear agreement, civilian protection, or a particular AI-governance mechanism. “Supports Iran” and “opposes AI” are not default labels. A speech may take different positions on different propositions under the same topic.

The fixed-topic table can add a short source-linked description of a verified new position. It does not display country loyalty scores or generic sentiment. Relevance similarity is not a probability; raw cosine values cannot be displayed as “86% topic salience.” An interpretable optional emphasis measure is the proportion of eligible passages assigned to an issue, with its denominator and classification uncertainty, after validation.

**Cold start:** retain the four rows with “Not assessed,” “Unresolved,” or “No qualifying text,” as appropriate. No-match rule outputs remain unresolved unless a validated full-text negative decision exists.

### O2. Emerging issues — no more than three items

Use a compact table: **theme | countries / eligible denominator | comparator | source-supported description**. Include short source links or refer to matching country readouts.

**Methods:** residual passage retrieval, hierarchical/K-means/PAM/HDBSCAN clustering, LDA, STM, the R-native embedding-topic pipeline, and change detection. Diffusion and forecast models can supply research hypotheses, but not observed emergence claims without direct source evidence.

A candidate must be new to, or measurably changed within, the **observed comparable corpus**, not merely absent from the fixed four-topic list. Compare passage-level content with historical themes and the full 13-category taxonomy; allow new subtopics inside a familiar category. One isolated national statement may be a reportable country development but is not automatically a cross-country emerging theme.

Count distinct countries as well as passages so a long speech cannot create a supposedly widespread theme. Inspect representative passages, outliers, and near-duplicates. The descriptor generator receives bounded source excerpts and no ability to change counts or cluster membership. Label wording must be descriptive and supported, with the same evidentiary standard as the summaries.

Do not compare today's raw topic count with yesterday's raw count and call the difference a trend when the country roster changed. Use a matched-country/genre/issue comparison when available; otherwise report composition-adjusted estimates only under an explicit weighting/model specification, or withhold the change claim. Never conceal the raw denominators.

**Cold start:** “Insufficient comparable history to assess emergence.” Current-day themes can remain in the country summaries; do not relabel them as emerging to fill the slot. An all-noise HDBSCAN fit is a valid result, not a reason to force clusters. [S6, S8]

### O3. Country discourse map — one figure

Use **Country discourse map**, rather than implying the unsupervised coordinates measure diplomatic policy positions. The default published view is a fixed-reference PCA map; PCoA is an independently validated alternative. Country colors follow the existing regional display groups. Neutral cluster outlines may be added only when stability supports them. [S4, S5]

**Methods:** TF-IDF/embeddings, PCA, PCoA, hierarchical clustering, K-means, PAM, HDBSCAN, UMAP, and compatible alignment diagnostics. UMAP remains an audit/sensitivity view by default. It is not the basis for measured movement or network edges.

Compute meaningful distances in the retained high-dimensional representation. A low-dimensional picture is a display, not the full measurement. Axes remain PC1/PC2 or coordinate 1/2 unless a separate validated interpretation supports substantive names. Show explained variation or an appropriate projection-fidelity diagnostic. If the projection is uninformative or unstable, withhold rather than attach a misleading figure.

Use an encoder, preprocessing policy, vocabulary/IDF, and reference projection frozen before the reporting cutoff. Apply new data through that fixed representation. When the reference changes, create a new version and reconstruct a comparable historical series before reporting changes across it. UMAP supports a fixed-model transform in R, but that does not eliminate the need to assess distortion. [S5]

Countries without new speeches are not newly observed points. A historical-reference marker may be shown only with a distinct visual treatment and last-observation date. New countries get a point but no invented prior movement. Do not add an absent U.S., Chinese, or Russian speech by pretending a historical statement belongs to today.

**Cold start:** a current-day descriptive map may be shown when the geometry is adequate, explicitly labeled cross-sectional. Otherwise: “Map withheld: insufficient comparable observations or projection quality.”

### O4. Rhetorical movement — up to three measured changes

Use a small before/after table or dumbbell figure. Each entry contains **country | baseline date | current date | measured change | evidence explaining it**. Select by a predeclared descriptive change measure after quality screening; the number is not an evaluative ranking of countries or policies.

**Methods:** within-country historical distance, anomaly models, change-point detection, compatible Procrustes alignment, experimental `driftmapR`, dynamic cluster correspondence, hidden Markov/latent transition/dynamic-mixture models, and forecast residual diagnostics.

Compare the same country, matched genre and issue/proposition, using compatible features. The reporting cycle is daily; the observations need not be. Prefer the previous comparable speech or a declared historical baseline over a fictitious “yesterday” observation. General-debate records alone do not justify a balanced daily country panel.

Preserve separately: (a) changed policy proposition, (b) changed topic mix, (c) changed phrasing, and (d) changed speaker, translation, transcript quality, or source version. A movement in semantic space is not itself proof of changed policy. The explanation must cite actual before/after passages, not merely terms with large embedding weights.

When a frozen PCA basis is used, no daily Procrustes correction is necessary. For separately estimated compatible maps, alignment must pass shared-entity, full-rank anchor, conditioning, and residual checks. It cannot fix a changed encoder, incomparable speech composition, or absent repeated entities. Retain global translation/scale diagnostics because alignment can remove some collective changes.

`driftmapR` remains behind a pinned, experimental adapter until its exact supported operating regime is accepted. Existing project constraints do not authorize presenting its studentized/joint regions as calibrated confidence regions. Bootstrap text blocks cannot manufacture independent country-level replications; uncertainty must match a declared sampling/measurement model. A single before/after pair supports descriptive distance, not an empirically estimated within-country standard deviation.

Use “measured change” or “flagged for review,” not “statistically significant” unless the actual validated inferential test supports it. Control alert multiplicity across countries, topics, models, and repeated runs; related model agreement does not create independent corroboration.

**Cold start:** “No comparable prior observation,” “No new comparable text,” or “No changes passed the publication rules.” These are distinct states and none means zero movement.

### O5. Discourse-network changes — compact observed changes

Use a compact edge-change table by default; a small, legible network is optional. Identify **which relationship changed, between which observations, under which edge definition, and with what joint coverage**. Limit the visible examples to three.

**Methods:** distinct similarity/stance networks; Louvain, Leiden, spectral clustering, stochastic block models; graph metrics; dynamic correspondence; and diffusion-related diagnostics. [S7, S10]

Maintain four distinct layers:

- topic co-occurrence;
- textual/semantic similarity;
- agreement on the same explicit stance propositions;
- independently sourced diplomatic actions or UN votes, when separately authorized and collected.

Do not silently fuse these into one “alignment” measure. Positive text similarity can coexist with opposite positions. A node's centrality is not proof of diplomatic influence. An inferred cluster is not a formal coalition; the email uses “discourse network” unless documented cooperative action supports a stronger term.

Compute edges only for observations with adequate common coverage. Keep missing edges separate from zero similarity or disagreement. Compare matched node sets and show entry/exit changes separately. Use stable community correspondence to distinguish label switching, cluster splits, and genuinely changed membership. Never add a spanning-tree connection just to make the graph visually connected.

Signed agreement/disagreement needs a compatible signed method; do not feed negative edges into positive-weight Louvain/Leiden routines. Select a stochastic-block likelihood consistent with the observed edge data, rather than treating continuous cosine values as Bernoulli observations. [S7, S10]

**Cold start:** “No comparable prior network.” Do not quietly replace a change analysis with a static coalition claim.

## 3. Full backend inventory

`config/method_registry.csv` and its JSON equivalent enumerate **42 components**. These include variants and supporting mechanisms, not 42 independent confirmations of any claim.

| Family | Methods included | Normal run policy | Visible destination |
|---|---|---|---|
| Representation | Rules/lexicons; TF-IDF/cosine; embeddings; fixed-topic semantic relevance | Process changed source hashes; keep reference transformations frozen | O1–O5 as appropriate |
| Geometry/clustering | PCA; PCoA; hierarchical; K-means; PAM; UMAP; HDBSCAN | New-snapshot fits or fixed-model transforms; preserve diagnostic alternatives | Primarily O2/O3 |
| Supervised coding | Logistic; elastic net; random forest; boosting; embedding classifiers; fine-tuned text transformer; proposition-specific stance | Daily inference; scheduled refit with new approved labels | O1; source-supported inputs to O3–O5 |
| Topic discovery | LDA; STM; embedding-cluster/descriptor pipeline | Daily assignment and novelty scan; periodic reference updates | O2 |
| Change measurement | Historical distance; isolation forest; change points; Procrustes; `driftmapR` | Daily update on comparable observations; bounded resampling | O4 |
| Latent dynamics | Cluster correspondence; HMM; latent transition; dynamic mixture | Daily filtering/assignment; periodic parameter fits | O4/O5 |
| Networks | Separate graph layers; Louvain; Leiden; spectral; SBM; graph metrics | New-network evaluation with repeated-seed checks | O5 |
| Forecasting/diffusion | Supervised issue/stance/shift/membership forecasts; temporal transformer; hazards; network autocorrelation; relational events; Bayesian diffusion | Daily eligible prediction; scheduled fitting; research-only by default | Audit only until separately released; never a sixth slot |

The production candidate for a task is not automatically the most complex method. Each family has a declared primary model or validated ensemble; competing models run as challengers or diagnostics. All numerical outputs remain archived, including outcomes that disagree with the published primary.

## 4. Daily inference is not daily retraining

**On each daily collection:** identify new/revised source bytes, normalize and deduplicate, update evidence, derive changed features, run all eligible inference tasks, assess freshness of cached artifacts, check every registry entry, assemble five packets, render, validate, and archive.

**Weekly default training window:** compare classifier candidates, topic references, anomaly baselines, and applicable network models when training inputs have changed. All parameter choices are made inside temporally valid training/validation data. Promotion produces a versioned release decision; a newly fitted model does not replace the current model merely because its training metric improved.

**Monthly default training window:** expensive latent-state, Bayesian, and neural fits, subject to learning curves, resource benchmarks, and actual data. Every daily report still records their most recent inference/reuse/non-delivery state. Cadences are proposed operational defaults, not mathematical requirements.

Use `targets` for change-aware dependency execution and per-country/per-method branching. Do not copy entire corpora into every worker. Frozen training artifacts are separate from the daily report job so a slow research fit cannot indefinitely block publication. [S2]

For the stated 16 GB home machine, start with **two outer workers, one heavy training job, no nested parallelism, and an 8 GiB process-budget target**. These are conservative design settings, not measured runtime guarantees. Record actual peak memory and elapsed time during acceptance. Dense all-passage pairwise matrices are prohibited by default; use sparse representations, nearest-neighbor structures, batching, and disk-backed historical features. Neural training requires a measured tokenizer/checkpoint/VRAM/driver benchmark, not merely a “high-end GPU” description.

The scheduler produces local unsent drafts. This design does not create a Windows task, authorize new API processing, or enable sending.

## 5. Data and eligibility rules

### 5.1 Preserve the correct observational grain

Archive source documents, then distinguish **passage → statement → country × genre × issue × observation window**. Also retain the original statement-level records after daily country aggregation. Country/date alone is not a sufficient analytic key when speeches span multiple meetings, speakers, agenda items, or source versions.

Maintain both **event time** and **first available/retrieved time**. A corrected transcript can revise a historical estimate, but a replay of what was known on an earlier reporting day must use that day's information set. Original and revised reports have different source versions; do not rewrite historical forecasts silently.

Metadata-only entries never provide substantive evidence. Automated transcript flags, translation uncertainty, country-attribution uncertainty, and all collection exclusions remain traceable.

### 5.2 Labels and weak supervision

Keep human-adjudicated labels distinct from model-generated and rule-generated labels. Two model passes are not two independent human annotators, and exact quoted-substring checks do not prove semantic entailment. The existing v2.1 replay has preserved v1 decisions plus provisional additions; it is a display/replay fixture, not homogeneous supervised gold or a ready historical baseline. Recode historical examples consistently and retain a separate human-reviewed test set before fitting a released issue/stance classifier. [S1]

Use uncertainty/disagreement sampling to prioritize the review queue, but include a probability-sampled component so evaluation is not confined to difficult cases. Track which sampling design produced each gold label; report performance on a representative holdout rather than on the active-learning queue alone.

The training set may grow autonomously from authorized sources; adjudication and validated release are separate responsibilities. Unsupervised methods do not require hand labels to fit, but they still require an evaluation protocol before publication.

### 5.3 Validation cannot be replaced by a sample-size slogan

No fixed universal statement such as “500 passages makes the model valid” belongs in the release policy. Required sample support depends on prevalence, dependence, dimension, task, and loss. Learning curves, per-class support, independent country/statement groups, chronological holdouts, and uncertainty in validation metrics determine whether the method is eligible.

For supervised models use **forward-in-time splits**, keeping a complete speech and its near-duplicates inside one fold. For generalization to unseen countries, add held-out-country evaluation as a separate objective; ordinary time validation does not establish that result. Fit vocabulary/IDF, selection, normalization, projections, calibration and thresholds within the appropriate training folds. Keep a final untouched temporal test period. `rsample` supports time-ordered and grouped splitting, but the combined leakage-safe design must be explicitly constructed. [S3]

Assess issue-wise precision, recall, precision–recall curves, calibration, abstention/coverage, and error subgroups; overall accuracy is not sufficient for rare Cuba/Iran references. For stance, also report proposition-specific confusion and abstention. The publication threshold should follow a predeclared false-claim cost and measured holdout precision, not an arbitrary model score.

For clustering, report stability under seeds, reasonable hyperparameters, and valid resampling; coherence and silhouette are diagnostics, not a guarantee of geopolitical meaning. Preserve all-noise, one-cluster, and unstable outcomes rather than force a pretty pattern.

For sequential models, require real repeated comparable country observations and a declared time index. Never fill a country's non-speaking days with zero topic/stance vectors. Separate filtered real-time states from retrospectively smoothed states that use future information.

### 5.4 Forecast and diffusion eligibility

The primary forecast target is **the next comparable observed speech**, or another explicitly defined horizon with its observation/selection model. “Will mention AI tomorrow” is not well-defined when no speech is expected or recorded. Distinguish appearance of a topic, stance on a named proposition, semantic movement, and cluster-state transition as separate targets.

Compare forecasts with persistence and base-rate baselines, using forward testing and calibration. Freeze inputs at their historical availability time. Fresh forecasts are research-only in D1, are not used to manufacture a current development, and do not enter the five-slot packet by default.

Diffusion work needs first-observed endorsement/adoption definitions, an at-risk population, lagged exposures, and censoring rules. Phrase reuse and a policy adoption are different events. Common shocks, selection into speaking, and preexisting similarity can explain correlated language. Do not report causal spread from a fitted network coefficient alone.

Relational event models need observed **sender, receiver, action, and time** with an appropriate risk set; shared words do not constitute a diplomatic interaction. Additional institutional-membership or diplomatic-event datasets require their own verified collection contracts. [S9]

## 6. Publication firewall

The term means a strict software interface, not another machine-learning model. Each analytical producer returns a typed packet containing:

`slot_id, state, payload, source_snapshot_id, model_id, definition_id, as_of_cutoff, evidence_refs, quality_checks, release_status, model_provenance`

Eight checks must pass for a ready packet: **source, time cutoff, version compatibility, metric definition, coverage, validation, uncertainty, and neutral source-faithful interpretation**. These checks are grounded in their own artifacts; setting a Boolean to TRUE is not enough to establish truth.

Only a **released primary model or explicitly validated ensemble** can provide a ready packet. Challenger outputs remain in the audit. Disagreements can cause abstention or downgrade confidence, but do not trigger post hoc selection of whichever result creates the strongest headline. Predictions and measured observations remain separately typed.

The renderer accepts exactly `O1` through `O5`, in fixed order. Missing or failed outputs retain a short, accurate reason. A sixth section is a structural error. Title changes, alternative plots, and decorative fallback content cannot circumvent the limit. The executive takeaway is generated only from these accepted packets and verified country summaries; it cannot introduce an unsupported sixth analysis.

The full email order is:

```text
USUN masthead + date + coverage/status
Executive takeaway (at most three short sentences)
O1  Fixed topics: Iran | Cuba | Ukraine | AI
O2  Emerging issues
O3  Country discourse map
O4  Rhetorical movement
O5  Discourse-network changes
Country readouts
  Africa
  Asia-Pacific
  Europe & Eurasia
  Near East
  Western Hemisphere
  Unmapped, only when necessary
Source/coverage note + footer
```

Country names are alphabetized **within each regional heading**. These remain the existing analytical regional groups, not newly claimed continents or UN electoral classifications. [S1]

## 7. Outlook compatibility and audit separation

Keep the already approved full-width table structure, masthead, seal, native-R MIME construction, escaped text, UTF-8, CRLF lines, `X-Unsent: 1`, and real-or-empty recipient/sender headers. Embed each referenced PNG exactly once via CID. Retain the 840-pixel maximum display width and conservative actual image-size checks. No JavaScript, external chart loaders, data URIs in the EML, source filenames, or internal evidence IDs in reader-facing prose.

Use tables for O1 and O2, one map for O3, a compact table or figure for O4, and a small edge-change table or network for O5. Maximum three analytical images; five sections do not mean five large charts. Plaintext contains the same five outputs with key values/limitations and evidence links. Do not revert to dense technical content merely because the HTML images are unavailable.

The audit bundle contains all 42 method-status records; all fitted artifacts actually produced; all candidate-model comparisons; uncertainty/coverage diagnostics; topic and stance coding; dimensionality and network alternatives; source excerpts; training/validation splits; package/model versions; raw model responses; and the original three issue charts. A result that failed or was withheld remains visible here with its reason, not silently dropped.

No hosted audit URL is invented. Internal research files are local or attached only through an explicitly selected distribution policy. Large numerical artifacts are not automatically attached to every institutional email.

## 8. Runtime and reproducibility

Daily application code remains R-native. R packages may use C/C++ or LibTorch internally; this does not require a Python daily process. Neural and advanced Bayesian backends remain optional, resource-gated installations. A BERTopic-like pipeline in R is a distinct implementation requiring its own validation, not a renamed execution of the Python package.

Candidate dependencies are grouped by function in the registry: `targets`, `quanteda`, `quanteda.textstats`, `Matrix`, `irlba`, `stats`, `cluster`, `uwot`, `dbscan`, `glmnet`, `ranger`, `xgboost`, `rsample`, `yardstick`, `topicmodels`, `stm`, `isotree`, `changepoint`, `strucchange`, `vegan`, `clue`, `depmixS4`, `LMest`, `igraph`, `RSpectra`, `blockmodels`, `survival`, `sna`, `remify`, `remstats`, `remstimate`, `brms`, `cmdstanr`, `torch`, and `luz`, with a pinned experimental `driftmapR` adapter. Installation, binaries, pretrained checkpoint compatibility, and cross-platform fit behavior require acceptance testing; the list is not an installed dependency lock. [S2–S10]

Continue the existing RDS/CSV evidence path; add a versioned DuckDB historical store when history warrants it. Parquet/Arrow are optional exports, not necessary for the first 39-country fixture.

Hash source bytes, preprocessing, codebook/label versions, embedding weights/tokenizer, reference corpus, model artifact, training cutoff, hyperparameters, seed, window specification, release policy, package lock and graphics/font environment. A byte-identical archived replay reuses stored outputs or identical frozen execution inputs; a fresh remote model call is not promised identical.

Every method has a daily summary state: executed, reused, not due, failed, withheld for quality, not implemented, or blocked by data/labels/history/dependencies/authorization/resources/version/supported regime. Execution and reuse must identify their artifact and time interval. Method-level stage ledgers can contain additional rows, but the daily summary must account for all 42 registrations.

## 9. Implementation sequence and acceptance

This is staged implementation of one integrated design, not removal of advanced methods from the registry.

1. **Contracts and historical store:** install five-slot routing and exhaustive ledgers; preserve current summaries/regions; add event/availability-time records; recode the historical fixture under one taxonomy.
2. **Current-day analytical layer:** deploy representations, issue coding, geometry, clustering, topic discovery, and three display factories; keep unqualified historical slots explicit.
3. **Supervised release process:** build adjudicated labels and temporal/grouped evaluation; fit all classifiers under bounded schedules; approve a primary per task.
4. **Historical and network layer:** add comparable snapshots, movement, change detection, community correspondence, latent dynamics, and experimental `driftmapR` with supported-regime constraints.
5. **Research forecasting/diffusion:** add independently verified outcomes/exposure/event data, compare all advanced models, and keep outputs audit-only until separately released.

Acceptance requires actual R execution of each implemented adapter on controlled fixtures; nonempty source-backed end-to-end runs; failed/empty/all-noise/missing-history tests; no leaked future data; valid comparative denominators; no unvalidated model promotion; full method accounting; five-slot and plaintext parity; R reproducibility; and native Outlook inspection. Browser checks are not native Outlook tests.

**D1 itself passes only the structural contract tests supplied here.** It does not establish predictive accuracy, cluster validity, `driftmapR` calibration, live-source collection success, or implementation of all 42 models.

## Sources

Source identifiers refer to `docs/SOURCES.md` and `validation/source_provenance.json`. They distinguish the inspected v2.1 workflow from public method/package documentation. All deployment choices, cadences, caps, and publication rules above are proposed design decisions—not empirical findings from a new model run.
