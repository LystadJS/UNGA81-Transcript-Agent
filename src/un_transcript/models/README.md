# Local semantic model workbench

The operational collector does not contain an accepted stance model. Without a
hash-verified, owner-released model directory, `analyze_segments` emits lexical
issue candidates and descriptive counts with **no stance predictions**. The 128
issue definitions are a provenance-bound export of the existing browser catalog;
they are retrieval definitions, not a validated comprehensive stance ontology.
Names such as a treaty title must be refined to a precise proposition before a
new catalog version and benchmark are frozen. Each reviewed definition must set
`classification_enabled=true` before that freeze; a passing global score cannot
enable an issue without its own denominator, precision, and recall evidence.

This package implements a candidate training and evaluation path. It does not
turn assistant decisions into owner labels. Model training, inference, and export
run locally in the Python process, without a hosted inference API. GitHub Actions
execution is cloud compute, not an on-premises server.

## Private workflow

Keep original sources, labels, model checkpoints, and receipts outside public Git.
Install `requirements-model.txt` in an isolated environment. For CPU-only Torch,
install the declared Torch version from the official CPU index before installing
the remaining requirements. Commands below run with the package installed or
`PYTHONPATH=src` from the repository root.

1. `python -m un_transcript.models prepare-pilot --segments PRIVATE_SEGMENTS.json
   --catalog config/issues.json --policy config/model-policy.json --output NEW_PRIVATE_PACKET_DIR`
   freezes a supplied source frame, canonical propositions, thresholds, and
   chronological train/calibration/test splits. At least three dates are required.
   The initial pilot contains at most 300 pairs (180/60/60 across splits),
   stratified by issue and source with a 70/30 lexical-candidate/control target.
   Missing strata remain explicit sample shortages. A separate queue contains up
   to 30 novel lexical issue candidates. This purposive pilot cannot pass the full
   acceptance benchmark; a separate registered complete-source sample is required.
   All choices are empty and `owner_confirmed=false`. Reserved October
   5–6 sources are excluded. Keep the untouched test packet sealed.
2. The owner codes the actual development packet and records reviewer identity,
   review time, original-text focal spans, exact proposition, interpretability,
   stance, and attribution correctness. Confirmations must reflect actual review.
   The separate complete-source declaration attests that all issues, including
   retrieval misses, were considered. Do not set it merely to pass a validator.
3. Obtain `distilbert/distilbert-base-uncased` at a specific immutable upstream
   revision into a private local directory. `train --labels TRAIN.json
   --registration REGISTRATION.json --base-model LOCAL_MODEL --revision COMMIT_SHA
   --policy config/model-policy.json --output NEW_CANDIDATE_DIR` trains a shared
   DistilBERT encoder with five-class stance and seven-class interpretability
   heads, plus a TF-IDF/logistic baseline. No model download occurs in this
   command. The local assets and declared upstream revision are pinned in the
   training identity; the command does not independently authenticate upstream
   hosting. Training uses CPU, AdamW, learning rate 0.00002, three epochs by default,
   batch size eight, and a deterministic seed. These are candidate settings, not
   validated optimal parameters. `--resume CHECKPOINT.pt` resumes an interrupted
   run only with the same inputs. No silent truncation is allowed; gold focal
   spans that do not fit any overlapping window cause an explicit refusal.
4. `calibrate --labels CALIBRATION.json --registration REGISTRATION.json
   --model-dir CANDIDATE_DIR --output NEW_CALIBRATED_DIR` fits a stance temperature
   over the declared grid on separate owner-reviewed focal spans. It requires all
   five labels and at least 25 clear calibration examples. The probability decision
   thresholds remain fixed at the frozen policy values. Calibration does not
   constitute acceptance.
5. `predict-benchmark --labels TEST.json --registration REGISTRATION.json
   --model-dir CALIBRATED_DIR --catalog config/issues.json --split test
   --output NEW_PREDICTIONS.json` executes both the candidate and the matched
   training-only baseline on the same untouched pairs. Retrieval/attribution
   misses remain abstentions. Run this only after candidate and calibration choices
   are frozen. `evaluate --labels TEST.json --registration REGISTRATION.json
   --predictions PREDICTIONS.json --model-dir CALIBRATED_DIR
   --policy config/model-policy.json --catalog config/issues.json --output NEW_RECEIPT.json`
   computes source-bound acceptance. Failure exits with code 2; zero denominators
   never become zero error rates. The receipt includes meeting-cluster bootstrap
   intervals, individual issue eligibility, and a matched baseline comparison.
6. Only after a passing real-source evaluation and an actual owner release decision,
   `approve --receipt RECEIPT.json --model-dir CALIBRATED_DIR --catalog config/issues.json
   --owner OWNER_ID --confirm-release` creates `acceptance.json`. The scheduled
   workflow never invokes this command. Releasing a candidate is distinct from
   generating a synthetic test receipt. New model/catalog/policy versions require
   their own source-bound assessment; do not retune against the opened test set.

## Runtime and interpretation

`analyze_segments(segments, catalog, model_dir=None)` returns `issues`,
`predictions`, `evidence`, `issue_candidates`, `analytical_results`, and
`model_status`. It accepts source identity aliases `source_id`/`revision_id`,
`source_hash`/`artifact_sha256`, and `attribution_kind`/`capacity`. Source revisions
form part of candidate and prediction identities. Every evidence offset is a
Unicode code-point offset into the original segment text. Only accepted model
artifacts, an exact catalog match, and individually eligible issues can emit
production predictions. Unknown/collective capacity does not become a national
stance. Artifact hashes bind the ONNX model, config, tokenizer and vocabulary.

The substantive classes are strongly oppose, oppose, neutral, support, and
strongly support. Neutral means explicitly neutral on the precise proposition.
Not discussed, no expressed position, conditional, mixed, unclear, and unresolved
attribution remain separate statuses. A confident material qualification in a
different overlapping window blocks an unqualified stance. Conflicting windows
abstain rather than average into neutral. The ordinal categories are not an
equal-interval numerical scale.

The current discovery output is an uncatalogued lexical candidate queue and
   issue-mention counts. It is **not** accepted semantic topic discovery, stance
inference, statistical nonrandomness, or historical country alignment. Future
embedding/clustering outputs must retain their own versioned methods, provenance,
and evaluation. This workbench leaves the existing synthetic research guards and
reserved evaluation corpus intact.
