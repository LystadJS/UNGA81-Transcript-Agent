# W4 — Longitudinal latent-structure diagnostics

**Status:** engineering-only, synthetic-first; no diplomatic time-series inference, published clusters, or corpus access. This work adds a read-only comparison adapter. It does **not** alter M22, M24, M25, M27, the reserved evaluation, the driftmapR repository, or browser entry points.

## Run (offline)

Requires Python 3.11+, NumPy, SciPy; JSON Schema validation in tests uses `jsonschema` when the repository schema is present. From repository root:

```bash
python -m pip install -r research/longitudinal/requirements.txt
python -m unittest discover -s research/longitudinal -p 'test_*.py' -v
python research/longitudinal/run_demo.py --output /tmp/un-w4-no-change
python research/longitudinal/run_demo.py --motion --output /tmp/un-w4-known-motion
node docs/parallel-work/validate-contract.cjs
python research/methods.py
```

The runner **refuses to overwrite** an existing output directory. All fixtures and CSV exports are fictional, carry synthetic SHA-256 identifiers rather than text, and are explicitly barred from publication as substantive evidence. Output is `analysis.json`, `interchange-v1.json`, `aligned-coordinates.csv`, and `cluster-correspondence.csv`. The source-aware v1 envelope satisfies the coordinator's required field shapes; its model results represent **imported labels**, never newly fitted models (`attempted_fits: 0`). An imported label must carry its **original cluster fit ID, parameters hash and training-selection hash**, separate from the display map fit. No upstream fit-failure accounting is invented by this adapter; the producing method must supply its own fit ledger before empirical integration. Original `source_sha256` and `selection_sha256` are mandatory inputs for any *development* interchange export; their hash basis must be retained, not recomputed from the adapter. CI also executes merged W1's `research/validation_framework/interchange.cjs` `validateRelational()` against **both actual W4-generated envelopes**; this is an engineering-level cross-workstream shape/count check, not an authentication of upstream real-corpus hashes.

## What the diagnostics estimate

| Quantity | Supported comparison | Interpretation |
| --- | --- | --- |
| Whole-roster centroid shift | Actor-equal aggregates in each period, all actors | Descriptive, strongly composition dependent |
| Common-actor shift | Same recorded actor, common genres, equal meeting/genre weights | Descriptive shift with reduced actor/genre turnover |
| Within-actor cosine/chord and Euclidean distances | Identical frozen high-dimensional vocabulary/preprocessing or pinned embedding basis | Linguistic representation change, **not** political movement |
| Common-source actor distances | Same actor and same source-family series across periods | Sensitivity to meeting series / coverage |
| Rigid map alignment | Externally predeclared, full-rank, stable anchors on independent fitted maps | Display normalization; residual/conditioning/scale reported |
| Saved-transform map | Exactly the same map fit reused across periods | Identity transform; no artificial Procrustes fitting |
| Cluster correspondence | Shared actor membership, arbitrary labels, abstentions | Equal meeting votes within genre, then equal genre votes per actor; duplicate passages cannot dominate. Overlap counts, split/merge candidates and unmatched groups, not diplomatic coalitions |
| Paired-source-family bootstrap | ≥6 complete repeated source families, source families resampled as whole trajectories | Descriptive percentile sensitivity; **not** a calibrated confidence interval |
| Map stress | Pairwise 4D vs 2D distances (bounded sample, optimally rescaled only for diagnostic) | Display fidelity; never fit stability or inferential support |

A label `cluster:0` is noise/abstention; `null` denotes absent fit, including at actor-level correspondence. They have separate counts and neither is imputed. Chronological ordering is explicit; no daily zeros are manufactured. Identical `representation_fingerprint`, ID, version, feature count and map-fit provenance are required. A **full refit** means *the display map* may be independently fitted; the input high-dimensional vector basis must remain pinned. Independently retrained embeddings or changing lexical vocabularies are rejected until a separate supported cross-basis experiment exists.

For full-refit maps, explicitly pass stable `anchor_ids` (at least map dimension + 2, independent centered full rank). The adapter enforces rotation conditioning and relative anchor RMSE; it does not discover stationary actors from outcomes. Anchor stationarity remains an unverified substantive assumption even with low residuals. High residuals fail closed. A low residual does not prove stable political meaning. Predeclare anchor controls and verify held-out anchor residuals on real data before substantive use.

## Input contract and future data specification

A `un.longitudinal-panel.v1` object has: `split` (`synthetic`/`development`); nonoverlapping ISO-date `periods[]` with `id,start,end`; one pinned `feature_space` with `id,version,fingerprint,dimension,fit_policy`; `map_space` with `method,dimension`; and `observations[]` with stable `id`, `period`, `date`, `actor_id`, `actor_kind` (`verified_speaker`, `recorded_affiliation`, `unknown`, `synthetic`), `speaker_id` only where verified, `country` affiliation if available, `genre`, `meeting_id`, `source_family_id`, `parent_id`, `parent_text_sha256`, source/text SHA-256, `source_hash_basis`, optional source URL/json pointer/Unicode code-point `start,end`, `source_status`, `missing_reason`, `representation_id/version/fingerprint`, pinned `map_fit_id`, optional integer `cluster` (0=noise, `null`=not fitted), and, when a label is present, mandatory `cluster_fit_id`, `cluster_parameters_sha256`, `cluster_training_selection_sha256` from the original fitted partition; `vector` (full frozen feature dimensions) and `map` (display dimensions). For development rows, also declare `unit` and `review_status`; `speech_id` is accepted only with confirmed speech review and is **not** `speaker_id`. Unavailable/failed source observations must be preserved without vectors or fabricated labels.

Before ingesting new periods, collect **independently verified** actor identifiers, identical source lineage/duplicate groups, meeting-level genre and source-family labels, available/missing inventory, and strictly forward dates. Freeze a lexical vocabulary/IDF or an embedding checkpoint **before** period comparisons. Preserve the original feature basis, fitting cohorts and selection hashes; record whether maps are saved-transform projections or independent refits. Preselect external stable anchors, record coverage in both periods, and obtain repeated sources across time. Treat verified speaker identity and recorded national affiliation as separate observation units; country is **not** a verified speaker, government stance or formal vote. Panels with insufficient repeated actor × genre, missing meetings, no stable anchor basis, or insufficient independent source families should withhold movement/inference rather than extrapolate.

### External dependencies and non-deliveries

1. **W1** must independently verify real source identity, representation comparability, source-group dependence and sufficient historical panel. This module's syntactic/hash consistency checks do not authenticate source bytes.
2. **W2/W3** may deliver source-linked fitted clusters to feed correspondence; their validation and source linkage remain separate gates.
3. **Coordinator** must reconcile branch/path ownership against `docs/parallel-work/OWNERSHIP.md`, review the additive GitHub workflow, and integrate an accepted `un.parallel-analysis.v1` envelope into W5–W7 consumers without mutating original D1/browser files.
4. M24's independent-Gaussian observation-index change-point method is **not** called: the October development corpus is not a rich independent longitudinal series. M26/driftmapR is **not** imported or claimed calibrated; re-examine its source and supported operating regime separately.
5. The existing 37 reserved October 5–6 meeting texts, sealed evaluation lock, original hashes, human-reviewed decisions and O1–O5 gates remain unchanged; they are not read by this module or its tests.

## Real historical P2 inventory: nullable source identities (2026-10-08 correction)

The panel validator now recognizes **unverified** P2 inventory separately from genuinely **unavailable** or failed sources and accepts both kinds of incomplete inventory rows with **null** meeting ID, source-family ID, date, text SHA-256, source SHA-256, and absent per-observation representation metadata, provided source status explicitly indicates unavailable and a nonempty reason is retained. No vectors, display coordinates or cluster labels may be fabricated. Available observations **still require** actual ISO dates, real meeting/source identifiers, source/text SHA-256, pinned feature identity and finite features. An entire unverified period is explicitly **withheld**, not treated as zero linguistic movement. The output CSV writer can represent zero aligned-coordinate rows without indexing a nonexistent first row.

**Interchange incompatibility:** Coordinator schema `un.parallel-analysis.v1` currently requires a nonnull string `observations[].date`. The corrected private P2 inventory contains 269 unverified country-year cells and unknown dates. The v1 source-status enum also has no `unverified` value. `to_interchange_v1()` therefore *refuses* to export that mixed frame rather than invent placeholder source dates. A coordinator-approved nullable-date new contract version or separately typed missing-source inventory adapter is required before W5/W6 public browser use. Do not change the frozen coordinator interchange v1 semantics by stealth.

**Real pilot boundary:** the restricted 99-country, 523 strong original-PV-corroborated speech panel is a purposively selected development subset; it has 269 unverified country-year cells. W4 full-refit alignment is unnecessary if a frozen reference map is reused, and meeting identities across the two eras have **zero literal paired original PV groups**; W4's paired-family bootstrap must remain withheld. Meeting-group leave-one-out checks and affiliation closure audit may be reported descriptively, but cannot be presented as calibrated independence. Source provenance and person authentication remain separate from this engineering fix.

## Methodology acceptance boundaries

Synthetic benchmarks cover an actor-roster-only shift with zero within-actor motion, known motion under rigid map rotation, fixed reference projection, missing source meeting, cluster-label permutation/split/merge/noise **versus missing fits**, unstable or rank-deficient anchors, chronological ordering independent of supplied list order, mismatched vocabulary/embedding/cluster-fit identity, corrupted source hashes, duplicate IDs, invalid offsets and false speaker-versus-speech attribution, insufficient bootstrap groups, replay determinism, JSON/CSV output and v1 interchange structure. These are engineering controls, not independent corpus replication, bootstrap-coverage calibration, political interpretation or verified future-data readiness.
