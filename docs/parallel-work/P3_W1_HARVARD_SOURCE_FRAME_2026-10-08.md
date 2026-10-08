# P3: Harvard v14 provenance and source-aware W1 longitudinal preframe

**Date:** 8 October 2026. **Disposition:** source-identity/date/missingness preflight PASS; **native W1 real frame validation, text representation and empirical fits WITHHELD**. This is a coordinator source-contract checkpoint, not country-alignment output or a publication release.

## Previously verified original UN source inputs

The P2 [63 original-PV source-byte report](W4_P2_REPLAYED_ORIGINAL_BYTES_2026-10-08.md) is merged on `main`. Both authorized private archives were supplied and re-opened in P3: all **63 original PDFs** (53,218,960 bytes) still match the original per-file source SHA-256. The P2 complete country-year ledger includes **523** source-strong 2016–2023 original-PV/Harvard **saved-digest** links from 55 distinct official meeting PDFs and **269** non-verified year opportunities. Its selection SHA-256 is independently reproduced: `3ebec834635e4d493e8035aeede3321efb951aa22f2f61d81f6ac7a0f65a4c89`.

**Important new inventory finding:** only **520/523** source-corroborated observations have a meeting/actor date that agrees with the independent UN speaker index. **Three** have no independently resolved event date. The fixed 99 affiliation × 8 year frame consists of 520 source-linked **and date-verified** candidates, three source-linked **but date-unverified** cells, and 269 original-source-unverified cells. The last 272 are not to be silently discarded, relabelled as an actual absence or given invented dates.

| Historical inventory group | Cells | Current model fit eligibility |
| --- | ---: | --- |
| Original-PV-backed, saved Harvard digest, independent date match | **520** | **WITHHELD**, raw Harvard text not reverified |
| Original-PV-backed, saved Harvard digest, date missing | **3** | **WITHHELD**, date missing |
| Source not verified in selected P2 acquisition | **269** | **WITHHELD**, original source missing/unreviewed |
| Complete repeated actor × year grid | **792** | **0 fitted observations** |

The 523 observed P2 source-corroborated cells span eight years with counts **56, 53, 71, 72, 63, 66, 83, 59** for 2016–2023 respectively. The largest original-PV group includes 16 source-corroborated cells; this is source concentration, not independent replicated country evidence. The selected historical meetings were purposively acquired, not a probability sample. Recorded country affiliation is not independently verified human identity, policy position, voting pattern, alliance or causal effect.

## Independent v14 Harvard original file acquisition

The original published file is Harvard Dataverse dataset DOI `10.7910/DVN/0TJX8Y`, `UNGDC_1946-2025.tar.gz`. The previously verified P2 source code independently pinned:

- SHA-256 `55077dccf7242cdf544aa95c4797c68e443b0c37344c9c112a2e2392ddfcf8e5`;
- source publisher MD5 recorded in P2 `81bdd06086d9e7c4e67026acb7325df3`.

New `research/integration/p3_harvard_archive_audit.py` verifies the **exact original archive** by both fixed digests, checks traversal/symlinks/duplicates and year/session country-key integrity, and releases only aggregate counts. Its six synthetic and corruption-refusal tests pass. The separately isolated read-only GitHub Actions trial used an independently discovered file ID `13591895` but the Harvard server returned **HTTP 400**; no source text was obtained or published in that trial. Thus this checkpoint **does not claim a fresh Harvard speech-text SHA verification**, and the saved 840 source-strong correspondence scores have not yet been replayed from Harvard original bytes in P3.

## Private deliverables, method compatibility, and next gates

The owner received a **private** reproducible package in this conversation (not GitHub) with:

- all 792 exact country×year source inventory rows, original-PV digest/source family and saved Harvard speech file hash where present;
- a separate 520-row date-verified W1 prevalidation candidate set;
- a public-safe hash/count/dependence receipt and an offline source-replay builder;
- four adversarial source-ledger refusals and deterministic replay of the complete frame (SHA-256 `7f7ab119fb64c1ed3501059c2dd2ae51832ee3b89b80c4c07bf5dd29a4d019a8`).

**These are not native `un.source-validation.frame.v1` inputs.** The current W1 validator accepts at most 600 rows per input and explicitly requires valid source event dates. A true W1 source-frame adapter must retain the separate **792-cell population ledger** and either validate a new historical General Debate dual-source contract or build a bona fide supported upstream `un.review.v1` source dataset. Do **not** mislabel P2 country-year rows as an original `un.review.v1` or `un.passage-corpus.v1` source merely to pass a schema check. Original Harvard v14 text SHA must be read and verified from **raw original text bytes**, not assumed from the saved P2 ledger.

After raw archive acquisition: independently reproduce all 840 Harvard country-speech/PV seven-token whole-speech coverage measures against the source-verified UN originals, resolve three dates, keep the 269 non-verified cells visible, verify speaker/role semantics and meeting/source-family grouping, freeze a 2016–2023 text/vector basis with consistent selection hashes, then test actual W1 grouped resampling and only later W4 descriptive movement. Source-group sensitivity is not a calibrated confidence interval.

**Immutables:** No changes to `research/reference_tests/evaluation-lock.json`, 37 reserved Oct 5–6, 2026 meeting texts, 24 owner decisions, original corpus hashes, D1 O1–O5 release gates, the public research browser, W4 worker PR #18, or portfolio mirror. No private country/person/meeting-row evidence, raw archive, original PDFs or source texts are committed.

**Status: P3 private source preflight complete; Harvard raw retrieval and native W1 empirical source contract blocked; real W1/W4 fits 0; publication withheld.**
