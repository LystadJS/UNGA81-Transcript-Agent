# Versioned analytical interchange contract — v1.0.0

**Schema:** `un.parallel-analysis.v1` (adapter layer only). **Status:** initial coordinator contract; public repo may contain its schema and synthetic fixtures, **not** private transcript-derived row-level outputs. A worker can comply by exporting this envelope from its exclusive namespace after reading upstream data through existing validators; it never modifies `site/analysis-core.js`, `site/cluster-core.js`, `site/latent-core.js`, `research/corpus/contract.cjs`, R/D1 kernels or the evaluation lock.

## 1. Upstream source schemas remain authoritative

| Source interface | Existing identity/provenance | v1 adapter rule |
| --- | --- | --- |
| `un.browser.corpus.v1` in `site/analysis-core.js` | `records[].id,date,country,region,language,scope,meeting,text,source_url,text_sha256`; `coverage[]`; optional reviewed-unit `parent_id,start,end` | Copy IDs/hashes and metadata, never rewrite `records`; derive meeting ID from validated `meeting_slug` or official source URL only when unambiguous; else `meeting_id:null` and reason |
| `un.latent-comparison.v1` / saved runs in `site/latent-core.js` | `source_hash`, `selection_hash`, source manifest with IDs/hashes, runtime, plan, fit entries and source-bound coverage | Keep original hashes **with their original hash basis**; record matched ID+text-hash order and archived fitted model/settings identity |
| `un.passage-frame.v1` / `un.passage-corpus.v1` in `research/corpus/contract.cjs` | `meeting_id`, `source_family_id`, `raw_sha256`, `text_sha256`, `parent_id`, `speech_id`, `parent_start/end`, `json_pointer`, `split`, review and exclusion arrays; `selection_sha256` | Directly preserve exact IDs and offsets. Respect **development-only** selection and withheld speech/country weighting |
| `un.review.v1` in `tools/review_data.py` | `sources.csv: source_id,iso3,event_date,available_at,genre,language,source_url,text_path,text_sha256,duplicate_group`; `passages.csv: passage_id,source_id,start,end,quote`; `history.csv: representation_id,comparable_group,observation_index` | Adapter may refer to verified sources/passage IDs and comparable periods; never promote unreviewed labels to gold |
| Browser partition `un.text-clusters.v1`, GMM and NMF | `points[].id,text_sha256,cluster` (0 unassigned); GMM `memberships`, NMF `shares`; explicit exclusions/skip diagnostics | Preserve numerical outputs and type their memberships; never interpret as stance or calibrated diplomatic probabilities |

Hash caveat: the browser collector hashes a decoded UTF-8 response string, while the research corpus hashes the retained original response bytes; do **not** assume hashes computed on different inputs are interchangeable. `text_sha256` always identifies the existing canonical observed text for that interface; offsets refer to the **source interface's** own text, not arbitrary HTML.

## 2. Envelope fields (normative)

`interchange-v1.schema.json` checks required shapes; producers **also** enforce these relational rules.

| Field | Type/meaning |
| --- | --- |
| `schema` | Exactly `un.parallel-analysis.v1` |
| `contract_version` | `1.0.0` or backward-compatible v1.x; never reinterpret a field |
| `producer` | `workstream_id` W1–W7, `adapter_version`, `code_sha256`, `runtime`, `generated_at`, `fixture_kind` |
| `upstream` | Immutable `source_schema`, `source_engine`, `source_hash_basis`, `source_sha256` (or null + `missing_reason`), `frame_sha256`, `corpus_sha256`, `selection_sha256`, `review_sha256` (nullable where genuinely unavailable) |
| `cohort` | `split` development/synthetic; `population` and `unit` (source_segment/passage/reviewed_speech/parent/country_period/synthetic), `selection_policy`, `weighting`, `total_in_frame`, `eligible`; `source_group_unit` and `duplicate_policy` |
| `observations[]` | **One row per observed eligible or excluded identity**, keyed by `id`; `text_sha256`, `parent_id`, `parent_text_sha256`, `meeting_id`, `speech_id`, `source_family_id`, `date`, `country`, `source_url`, `json_pointer`, Unicode `start/end`, `unit`, `review_status`, `exclusion_reasons[]`, `source_status`, `missing_reason` |
| `models[]` | Unique `model_id`, `method_family`, `method`, `representation_id`, `representation_version`, `fit_version`, `fit_split`, `parameters_sha256`, `training_selection_sha256`, `diagnostic_basis`; optional display version tracked separately |
| `results[]` | Exactly one row for each model–eligible-observation pair **or** documented model-level skip; `model_id`, `observation_id`, `status`, `cluster`, `membership_kind`, `memberships`, `membership_strength`, `representation_basis_id`, `reason` |
| `coverage` | Inventory/selected/excluded/missing/not-fitted/assigned/unassigned tallies **per model**, attempted/successful/failed fit counts; `failure_ledger[]` reason and attempt/seed/group, including timeouts |
| `evidence[]` | `observation_id`, `source_url`, `json_pointer`, `start/end` when available, `role` (representative/contrary/ambiguous/context), `proposition_id` nullable and `verification`; **no transcript excerpts** in public artifacts |
| `diagnostics[]` | `model_id`, `name`, numeric/string/null `value`, `denominator`, `unit`, `status`, `reason`; e.g. ARI on assigned-both, pair opportunities, held-out withheld |
| `limitations[]` | Explicit scoped methodological/interpretive caveats, preferably `code,scope,description`. `publication_eligible:false` and `evaluation_role:'engineering_only'` are mandatory in v1 |

**Identity join:** join on `upstream source/schema identity + observation id + text_sha256`, never country name, order, display X/Y, cluster ordinal or a re-tokenized string. Keep `null` genuinely missing; never use `""` or `0` as a missing country, parent, probability or coordinate. `meeting_id` must be a verified official slug or null (not manufactured from an ambiguous title). Speech ID is null unless explicitly reviewed. Country metadata is an **affiliation label**, not an authenticated speaker, formal vote or stance.

**Offsets:** when provided, `start` and `end` are integers, zero-based, end-exclusive **Unicode code points** into the versioned parent/source representation; they must satisfy `0 <= start < end` and the parent's verified bound if present. If offset basis is unavailable, both are null; do not invent spans. Evidence URLs point to original HTTPS UN material and can have a JSON pointer for local original source navigation.

## 3. Model output and missingness rules

- `results[].status` is one of `assigned`, `unassigned`, `not_fitted`, `excluded`. `assigned` requires integer `cluster >= 1`; `unassigned` requires `cluster:0`; `not_fitted`/`excluded` require `cluster:null` and nonempty reason. A fit skipped in full has a `failure_ledger` entry and per-observation `not_fitted` rows where eligible; an empty results array may be used only for a zero-eligible cohort with explicit coverage.
- `membership_kind` is `gmm_responsibility`, `nmf_share`, `hdbscan_strength`, `consensus_frequency`, or `none`. Arrays for GMM/NMF must have the declared component order, finite nonnegative values and sum to 1 (tolerance 1e-6); for GMM they are **conditional model responsibilities**, for NMF normalized component contributions, *not* comparable probabilities or diplomatic stance. HDBSCAN strength is scalar 0–1, not an array. A consensus frequency must declare pair-opportunity denominators, eligible method families and assignment policy; it is not a posterior.
- `representation_id/version` denotes the actual trained transformation, vocabulary/IDF, checkpoint and preprocessing identity, not just `pca`, `lsa` or `semantic`. Distinguish fit geometry from UMAP/MDS display coordinates. Graph/diffusion producers must declare affinity construction, distance, neighborhood size, kernel, normalization, connected components, eigensolver and degeneracy/sensitivity.
- No comparison across runs with different source hashes, selection digests, observation unit, representation bases or fit/graph policies unless a **named** cross-basis/alignment protocol is supplied. Retain unmatched, splits/merges, arrivals/departures and missing periods; never imply an uninterrupted complete series.
- The full source frame includes absent/unavailable meeting entries in `coverage`; no output may imply `excluded` means source absent. `total_in_frame` counts the declared inventory; `eligible` counts selected eligible observational units; these have different denominators and must not be equated.
- Null evidence, failed bootstrap, missing transcription and unresolved attribution remain explicit. An issue not mentioned in an incomplete text is **unknown**, not negative. Do not normalize probabilities, co-assignment or weights over only successes without showing the omitted denominator.
- Never claim null-calibrated discovery, independent replication, government positions, influence, coalitions or causality from descriptive clusters/plots. W1 must preregister the group-preserving reference hypothesis and adjust any search before inferential labels.

## 4. Mapping example (synthetic, no source text)

```json
{
  "schema": "un.parallel-analysis.v1",
  "contract_version": "1.0.0",
  "producer": {"workstream_id":"W2","adapter_version":"0.1.0","code_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","runtime":"node-22","generated_at":"2026-10-08T00:00:00Z","fixture_kind":"synthetic"},
  "upstream": {"source_schema":"un.browser.corpus.v1","source_engine":"synthetic-browser-fixture","source_hash_basis":"utf8_corpus_export","source_sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","frame_sha256":null,"corpus_sha256":null,"selection_sha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","review_sha256":null,"missing_reason":null},
  "cohort": {"split":"synthetic","population":"synthetic_passages","unit":"synthetic","selection_policy":"all synthetic rows","weighting":"equal_passage","source_group_unit":"meeting","duplicate_policy":"retain_and_audit","total_in_frame":1,"eligible":1},
  "observations": [{"id":"synthetic-1","text_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","parent_id":null,"parent_text_sha256":null,"meeting_id":null,"speech_id":null,"source_family_id":null,"date":"2026-10-01","country":null,"source_url":null,"json_pointer":null,"start":null,"end":null,"unit":"synthetic","review_status":"not_applicable","exclusion_reasons":[],"source_status":"available","missing_reason":null}],
  "models": [{"model_id":"demo-1","method_family":"partition","method":"pam","representation_id":"synthetic-representation-1","representation_version":"1","fit_version":"1","fit_split":"synthetic","parameters_sha256":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee","training_selection_sha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","diagnostic_basis":"synthetic fixture"}],
  "results": [{"model_id":"demo-1","observation_id":"synthetic-1","status":"unassigned","cluster":0,"membership_kind":"none","memberships":null,"membership_strength":null,"representation_basis_id":"synthetic-representation-1","reason":"Synthetic explicit abstention"}],
  "coverage": {"inventory_meetings":1,"observations_total":1,"eligible":1,"excluded":0,"unavailable_sources":0,"models":[{"model_id":"demo-1","eligible":1,"assigned":0,"unassigned":1,"not_fitted":0,"excluded":0,"attempted_fits":1,"successful_fits":1,"failed_fits":0}],"failure_ledger":[]},
  "evidence": [],
  "diagnostics": [{"model_id":"demo-1","name":"synthetic_coverage","value":0,"denominator":1,"unit":"observation","status":"descriptive","reason":null}],
  "limitations": [{"code":"synthetic_only","scope":"all","description":"Illustrative only; no diplomatic source, accuracy or release claim."}],
  "publication_eligible": false,
  "evaluation_role": "engineering_only"
}
```

**Adapters:** W1–W4 implement `toInterchangeV1(source, fitted, context)` independently in their own namespace and call upstream validators. W5 may read validated v1 envelopes and present an **explicit experimental view**, but workers cannot patch the existing browser loaders. W6/W7 consume only accepted typed read models. Keep the full original source bundle and source-linked review material **local and private**; a public PR can submit the synthetic example above with a text-free validation receipt.
