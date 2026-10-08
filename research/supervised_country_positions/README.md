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
