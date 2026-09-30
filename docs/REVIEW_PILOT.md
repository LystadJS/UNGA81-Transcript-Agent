# AI pilot: one owner, audit-only import

## Completed owner pilot — 30 September 2026

The owner saved all 24 reviews at 20:06 UTC. Fresh loader validation passed:
12 relevant, 11 not relevant and one insufficient-context label, covering 21
source speeches. All 24 records matched the daily corpus and were attached to
its private audit copy. Native daily validation passed, and a subsequent hash
check confirmed all 158 pre-existing files and the audit sidecar checksums.
See the [completion record](../research/validation/i9/owner-completion.json).
Individual labels, reviewer identity and source passages remain in the private
local workspace; the repository contains only aggregate completion evidence.

The unresolved passage remains unresolved. Its surrounding text is available
locally in `review-work/ai-pilot/unresolved-context.html`; any changed label needs
a new review revision. The completed packet is preserved. The instructions below
describe the original workflow and how to reproduce it with a new packet.

Next: resolve that passage if the added context permits, then collect later-date
speeches for a separate evaluation set. The 23 binary labels can inform the next
development step, but this enriched, single-date pilot does not establish model
accuracy. BERT training and the real-data training adapter remain future work;
the completed deliverable here is human-label collection and audit integration.

The owner selected Artificial Intelligence as the first issue and explicitly
chose to be the sole reviewer and finalizer. The operational review mode is
`single_reviewer_pilot`. It does not claim inter-reviewer agreement or independent
adjudication. The earlier independent-review workflow remains available as the
default for other bundles; it is not required for this owner-approved pilot.

## Finish the local pilot

The prepared private workspace is `review-work/ai-pilot`. While its local server
is running, open **http://127.0.0.1:8767/**. Read the 24 passages, choose Relevant,
Not relevant or Insufficient context, and save the completed review. The form
requires an explicit confirmation that the owner reviewed every choice. No
labels or human sign-off were preassigned by the assistant.

The sample contains up to 12 lexical candidates and 12 non-hits, shuffled with a
fixed seed. Sampling status is not a label. The pilot is enriched for annotation
practice; label proportions are not corpus prevalence estimates. Its codebook
includes AI systems, applications, opportunities, risks and governance, while
general technology/digital development alone does not establish AI relevance.
Relevance is separate from support, opposition or policy alignment.

All 39 archived source speeches have the same recorded date, 23 September 2026.
The pilot therefore has no fabricated train/calibration/test split. Source URLs
were absent in the supplied archive. The packet uses a content-addressed archive
reference and the time it was observed locally as conservative availability
evidence; it does not invent an official UN URL or first-publication time.

The configured save action imports the finished review into a private copy of
the completed daily run and invokes the native daily validator. Original run
files, emails, model gates and O1-O5 outputs are preserved. The form reports
whether the audit step succeeded. `workflow.json` records success; on a validation
problem the labels remain saved and `workflow-error.txt` records the problem.
The pilot is only actually complete once the owner saves the form. Engineering
fixtures used for tests are explicitly distinct from this human review.

## Selected checkpoint

The owner chose **Google BERT, 2 layers / 128 hidden units / 2 attention heads**:
[`google/bert_uncased_L-2_H-128_A-2`](https://huggingface.co/google/bert_uncased_L-2_H-128_A-2).
Its publisher describes an English, uncased BERT miniature and lists Apache-2.0.
The [pinned repository](https://huggingface.co/google/bert_uncased_L-2_H-128_A-2/tree/30b0a37ccaaa32f332884b96992754e246e48c5f)
contains a safetensors weight file. It fits the current bounded BERT architecture.

- Revision: `30b0a37ccaaa32f332884b96992754e246e48c5f`.
- Weight SHA-256: `7fb69ad9f6866d8983183c930e33828f326470bf6ad8bbb2ad4ed957a92e9414`.
- Local bundle: `research/runs/bert-pilot` (ignored by Git).
- Loaded classifier architecture: 4,386,178 parameters; 30,522 tokenizer entries.
- Config/vocabulary were checked against publisher Git blob identities; weights
  against the publisher LFS SHA-256. Generated tokenizer assets are locally hashed.

This is a **user-selected candidate for local pilot evaluation**, not an approved
AI relevance classifier. The pretrained encoder loads successfully; a binary
classifier head is newly initialized and must be trained. No human labels have
been sent to a remote model service. No real-data fine-tuning or accuracy claim
is made by preparing the checkpoint. The four-layer alternative was not selected
or downloaded.

## Loader and daily audit integration

`tools/reviewed_loader.py` first copies the exact input bytes into an isolated
snapshot. It validates review roles, timestamps, source hashes, quotations,
offsets, named targets and final labels, then emits provenance-bound records.
Changed labels or source bytes change the bundle identity. Single-reviewer
status is carried into the result. Insufficient context stays unresolved, with
no binary label. The loader refuses unreviewed input and does not train a model.

The `pilot` capability checks annotation completeness without pretending a
single-date sample is a training evaluation set. `labels` and `stance` additionally
require the existing forward-time split checks. In all cases,
`model_fit_authorized=false` and `publication_eligible=false`.

The post-run `attach` command requires a completed, validated daily run and at
least one exact country/text-hash match. It writes only beneath
`audit/reviewed_labels/<bundle hash>/`, with labels, a receipt and checksums.
The receipt binds all pre-existing run files and lists matched and unmatched
passages. The original run checksum manifest is retained; the new sidecar has
its own manifest. This is a reviewed-label **audit attachment**, not a new fitted
daily method, UI prediction integration or automatic release approval. The daily
adapter count remains 12; the 42 methods and 133 prerequisites are unchanged.

## Reproduce on another checkout

From the repository root, use new output names:

```powershell
python tools/pilot_review.py prepare review-work/ai-pilot un/examples/2026-09-23/speeches.json
python tools/pilot_review.py serve review-work/ai-pilot --port 8767
# After the owner saves the form:
python tools/reviewed_loader.py export review-work/ai-pilot review-work/ai-import.json
python tools/reviewed_loader.py attach review-work/ai-pilot C:\path\to\completed-daily-run
Rscript tools/validate_review_run.R C:\path\to\un C:\path\to\completed-daily-run
```

To connect the save action automatically, add `--daily-run`, `--package-root` and
`--rscript` to `serve`, using the relevant local paths. The server binds only to
127.0.0.1; there is no cloud publication or external transmission of reviews.
The local server must remain running while the form is used. Existing completed
pilot/output directories are never overwritten by preparation/import commands.

In the isolated neural environment described in [I8](../research/I8.md):

```powershell
research/neural-env/Scripts/python tools/prepare_checkpoint.py research/runs/bert-pilot
python tools/test_review_data.py
python tools/test_reviewed_loader.py
```

Checkpoint preparation downloads only the three pinned publisher files and
builds the local tokenizer; it does not download or execute remote custom code.
For an integration fixture on a copy of a daily run:

```powershell
python tools/check_daily_review.py C:\path\to\completed-daily-run review-work/integration-check
```

Its synthetic labels are marked as engineering fixtures and cannot be reported
as completed human review. See [I9 evidence](../research/validation/i9/README.md).

## Recommended next steps

1. Save the 24 pilot labels; check that the form reports successful audit import.
2. Resolve passages marked insufficient and refine the AI codebook if needed.
3. Add later-date speeches before measuring forward-time performance. Start with
   a simple lexical/logistic baseline and compare the selected BERT candidate.
4. Keep predictions audit-only until the owner has inspected errors and decided
   the quality is useful for this operational workflow. No multiple-reviewer
   requirement is imposed on this pilot.
