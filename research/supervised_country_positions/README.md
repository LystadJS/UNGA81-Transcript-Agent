# Country positions — supervised research prototype

**Branch:** feat/supervised-country-positions  
**Status:** engineering-only, fictional synthetic data. No diplomatic inference, trained real classifier, public report, or daily adapter. Substantive country-alignment outputs remain withheld.

## Purpose and interpretation

This work extends the existing issue-relevance and stance research without changing upstream implementations. A country is **not** automatically classified as generally US-aligned or China-aligned. The analytical unit is a **named policy proposition** in a specified year, connected to a recorded country affiliation and original passage.

Pairwise comparison counts agreement only when both countries have an eligible explicit **support** or **oppose** stance on the *same* proposition. It is not an alliance score, voting prediction, causal model or political-ideology label.

The six **draft** propositions cover Ukraine, Cuba and binding AI governance. Reviewers must refine and freeze the questions, source frame and interpretation before real fitting.

## Files

| File | Role |
| --- | --- |
| **propositions.v1.json** | Draft versioned policy-object definitions and coding exclusions. |
| **prepare_review.py** | Reads existing un.review.v1 CSVs and original text; verifies SHA-256 and Unicode offsets; creates blind source-balanced packets and unfinalized candidate annotation CSVs. |
| **annotation.html** | Offline blind source-linked annotation form; local private JSON import/export and human rationale. |
| **m12_m17_adapter.R** | Directly invokes unchanged M12 and M17 kernels from research/engines.R, rejecting real input. |
| **position_core.cjs** | Synthetic-only provenance, speech-family rollups, positions, pairwise agreement and evidence links. |
| **synthetic_fixture.cjs**, **build_synthetic.cjs** | Fictional actors in two hypothetical years; deterministic JSON generator. |
| **viewer.html** | Local-only heatmap, schematic agreement network, two independent reference comparisons and source inspector. |
| **test_positions.cjs**, **test_prepare_review.py**, **test_m12_m17_adapter.R** | Synthetic and invalid-input regressions. |

Upstream un.review.v1, un.browser.corpus.v1, and un.passage-corpus.v1 remain authoritative. This work does not change the shared parallel-analysis contract. In particular, cluster membership weights are *not* stance probabilities. M12/M17 continue to enforce source/country/time separation, frozen feature order, and synthetic-only fitting.

## Quick start — fictional example

From the repository root, run:

    node research/supervised_country_positions/test_positions.cjs
    node research/supervised_country_positions/build_synthetic.cjs /tmp/fictional-positions.json

Open **research/supervised_country_positions/viewer.html** locally and use the file picker to open the generated fictional JSON. On Windows, use a path such as C:\un-private\fictional-positions.json.

Additional tests, when the required runtimes/dependencies are installed:

    python3 research/supervised_country_positions/test_prepare_review.py
    Rscript research/supervised_country_positions/test_m12_m17_adapter.R

The R tests require glmnet and the dependencies of the preexisting research kernels. No model is downloaded.

## Private blind annotation workflow

1. Create/populate a private **un.review.v1** workspace with the original source/metadata rules in docs/DATA_GUIDE.md. Keep original transcripts and review decisions **outside** public Git.
2. Prepare a deterministic source-family-balanced review packet:

       python3 research/supervised_country_positions/prepare_review.py prepare \
         --workspace PRIVATE_WORKSPACE \
         --count 60 \
         --output PRIVATE_FOLDER/issue-stance-packet.json

3. Open **annotation.html** locally, import the packet, enter a reviewer pseudonym, code issue relevance and then proposition-specific stance, and record rationale. Export a draft. No model suggestions appear and no decisions are prefilled.
4. Check and export candidate annotation rows:

       python3 research/supervised_country_positions/prepare_review.py export \
         --packet PRIVATE_FOLDER/issue-stance-packet.json \
         --draft PRIVATE_FOLDER/country-position-private-draft.json \
         --output PRIVATE_FOLDER/candidate-annotations.csv

5. Inspect/merge **unfinalized** candidate annotations into the private workspace. Human finalization and adjudications remain separate explicit acts. The exporter never creates gold labels or marks review complete. Use the existing review_data.py validator only after the complete source/split/reviewer bundle has been assembled.

The packet records sources without retrievable original evidence, checks exact parent bytes/hashes and text offsets, and excludes reserved meetings dated 5–6 October 2026. Missingness is not negative evidence. The owner-approved single-reviewer pilot does not imply independent agreement.

## Analytical and display rules

- A recorded individual-country affiliation is not automatically an authenticated person or a government-wide position. Collective/uncertain speakers and unavailable sources are excluded from agreement.
- **Support and oppose** are the only agreement-contributing stances; conditional, descriptive, insufficient, unmentioned and mixed are separately identifiable. Multiple excerpts/translations from one source family count as one opportunity.
- Pairwise edges require two or more comparable propositions. Each has an agreement count, disagreement count, coverage denominator, and evidence IDs. No statistical confidence interval, influence inference, or ideological label is invented.
- Comparison with the fictional U.S. and China reference actors uses **two independent proportions**. These need not sum to one and may have different eligible proposition sets.
- The network is a **schematic circular layout** rather than a political embedding. No coordinates are learned from diplomatic evidence.

## Empirical and publication gates

1. Review/freeze propositions and balanced source sampling, including contrary and nuisance-only examples.
2. Collect genuine reviewed labels with verified text hashes, recorded attribution, provenance, source dependencies, missing-data records and source-date comparability.
3. Fit and evaluate a separately approved real-data adapter, using frozen train/calibration/test splits, group/temporal transfer, class metrics, calibration, abstention and baselines. This synthetic branch does not unlock training on real inputs.
4. Validate aggregation against independent source groups, contested within-country positions, unequal issue coverage, translation and speaker-role effects.
5. Obtain separate coordinator integration acceptance before any shared browser, publication gate, daily pipeline, public asset or website mirror change.

**Frozen protections:** no actual transcript bytes, private annotation rows, real scores or country assignments are committed; the 37 reserved October 5–6 meeting texts remain unopened; original hashes, human choices and D1 O1–O5 gates remain unchanged.


## First real-source annotation pilot (planning and intake only)

The protocol is frozen in **pilot_protocol.v1.json**.  Read **ANNOTATION_CODEBOOK.md** before assigning a label.  The new *pilot_pipeline.py* builds a **private** original-PV-quality-gated source roster, deterministic source-disjoint train/calibration/test allocations, and split-specific blind review packets.  No source-linked row data or real model output is committed to GitHub.

This is a different deliverable from the fictional synthetic network.  The pre-existing owner-reviewed AI **issue relevance** pilot contains 24 decisions but **no two-proposition human stance gold**.  The prior historical corpus analysis described an original-PV-strong candidate subset; its **private source/PDF bytes and source-row quality manifest are not accessible from this conversation**.  Thus no real stance labels, actual country group assignments, or empirical score can be claimed yet.

### Required private input

Place the original reviewed speech text bytes and exact **un.review.v1** CSVs in a private workspace **outside this public Git checkout**.  For each canonical source ID, also fill a private **source_quality.csv**, using **source_quality.template.csv** as the required header.  It must reflect an actual P2 or later original-UN-PV audit, not an invented verification.

- Source entries must record genuine official UN HTTPS URLs, canonical text SHA-256, ISO3, English General Debate date, and source family.
- Source quality must include official A/session/PV.meeting symbol, **previously checked** original PDF digest, strong full-speech correspondence, official-PV method, individual recorded country capacity and verification basis.
- The planner **rechecks canonical text bytes and offsets**, but does **not independently replay PDF bytes or certify a real speaker's identity**.  Missing or contradictory quality records are withheld.
- Only **2016–2023** comparable sources can enter the split; 2024–2025 modality discontinuities and all reserved October 5–6, 2026 meeting texts are ineligible.

### Reproducible private CLI

From the repository root (use actual absolute private paths, not literal placeholders):

    python3 research/supervised_country_positions/pilot_pipeline.py plan \
      --workspace PRIVATE_UN_REVIEW_WORKSPACE \
      --outdir PRIVATE_PILOT_OUTPUT \
      --seed 20261009

This creates a digest-locked private pilot_plan.json and un.review.v1-compatible splits.csv, plus a **complete disposition ledger** for missing/ineligible source rows.  Assignment uses 2016–2019 train, 2020–2021 calibration and 2022–2023 test windows, with *country-disjoint* groups and frozen family/full-text hashes.  It does not generate new interviews, speaker identities, transcripts, or labels.

Then produce the first **development-only** packet:

    python3 research/supervised_country_positions/pilot_pipeline.py packet \
      --workspace PRIVATE_UN_REVIEW_WORKSPACE \
      --plan PRIVATE_PILOT_OUTPUT/pilot_plan.json \
      --split train --count-per-proposition 48 \
      --output PRIVATE_PILOT_OUTPUT/train-review.json

Open **annotation.html** locally and import the train packet.  Review the two named propositions using original source context, then export the private draft.  For the owner-approved single-reviewer pilot, check the explicit first-person attestation only after personally completing the selected decisions.  The unreviewed/backup draft remains a draft; **it is never rebranded as gold automatically**.

Verify a genuinely owner-attested draft (private, aggregate report only):

    python3 research/supervised_country_positions/pilot_pipeline.py audit \
      --packet PRIVATE_PILOT_OUTPUT/train-review.json \
      --draft PRIVATE_PILOT_OUTPUT/country-position-private-draft.json \
      --output PRIVATE_PILOT_OUTPUT/train-review-audit.json

After full human review, use the original un.review.v1 exporter/finalization and validator.  Calibration may receive its own separately sourced review packet later.  The **test packet cannot be generated without an explicit --authorize-test-review flag** and must not inform codebook, feature, threshold or model selection.  There is no live real-data training adapter in this phase.

Pilot planning targets **96 development, 32 calibration and 32 held-out test proposition–passage pairs**, equally divided between the two propositions.  These are **targets**, not achieved sample sizes; shortages are surfaced.  Roughly 70% of targets use predeclared lexical screens and 30% unfiltered random controls, both **unlabeled**.  The source-frame is purposively verified and cannot establish corpus-wide rates.

Native synthetic acceptance includes **test_pilot_pipeline.py**, invoked through the original read-only CI workflow via test_prepare_review.py.  All unchanged M12/M17 and publication gates remain intact.

**Current empirical gate:** NO HUMAN PROPOSITION-STANCE GOLD; NO VERIFIED PRIVATE SOURCE INPUT IN THIS TURN; NO REAL TRAIN/CALIBRATION/TEST ALLOCATION GENERATED; NOT PUBLICATION ELIGIBLE.
