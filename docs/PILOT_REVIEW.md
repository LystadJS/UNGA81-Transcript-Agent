# Owner review: initial 300-example feasibility pilot

This private packet contains 180 training pairs, 60 calibration pairs and 60 later-date test pairs. Each pair asks about one actor's expressed stance toward one precise proposition in a dated passage. The packet has no suggested model labels. It is a feasibility pilot, not the untouched launch-acceptance benchmark.

Start with `review/train-review.csv`. Review the first 30 rows as a codebook trial, save your progress, and note unclear definitions before completing the remaining training rows. Preserve the original packet and work on a private copy. The full passage, recorded speaker/country/capacity and official source link accompany each row. Recorded national affiliation is not proof of national speaking capacity.

Fill only `status`, `label`, `national_attribution_valid`, `owner_confirmed` and `notes`. Keep identifiers, source hashes, passages and propositions unchanged. Do not upload completed rows to GitHub or a public dataset. Each row must contain your actual judgment; leave unfinished rows blank. Use `true` for owner_confirmed only after reviewing that row. Use true/false for national_attribution_valid only when supported, otherwise leave blank and explain the uncertainty. Training also requires completed packet-level reviewer identity and review date in the label JSON; returned CSVs must be validated and reconciled with the frozen registration before training.

## Status and label

- `clear`: an assessable expressed stance. Choose exactly one label below.
- `not_discussed`: the policy proposition is not discussed.
- `no_expressed_position`: discussed without an expressed position.
- `conditional`: position depends on a stated condition. Record it in notes.
- `mixed`: genuinely conflicting positions on the same proposition. Preserve both in notes.
- `unclear`: insufficient evidence, ambiguous meaning or unreliable transcription.
- `unresolved_attribution`: unclear who holds the expressed position, including unresolved national versus collective capacity.

For every status except clear, leave label blank. Silence is not neutral. Quoted opponents' statements are not the speaker's own stance. An explicitly collective statement must not become a national stance through the speaker's country affiliation.

For clear positions, use `strongly_oppose`, `oppose`, `neutral`, `support`, or `strongly_support`. Strong labels require explicit emphatic rejection or commitment/intensity beyond ordinary disagreement or endorsement. Strength is not confidence. Neutral requires affirmative evidence of neutrality or a stated neither-support-nor-opposition position. If meaning, attribution or scope remains unresolved, use the appropriate separate status rather than forcing a five-level label. Explain borderline strength distinctions in notes for the codebook review.

## Review order and evaluation separation

Complete training review first. Freeze codebook changes before reviewing `review/calibration-review.csv`; calibration may tune model thresholds. Keep `sealed/` closed until the candidate and thresholds are frozen, then review its 60 later-date pairs without model predictions. The seal is procedural: the owner has file access. Do not use those examples for training or debugging. If opened early, record contamination and obtain a fresh untouched evaluation sample.

The total pilot is 300 pairs across all three stages, not 300 immediately available training labels. Later comprehensive acceptance requires a separately expanded benchmark. `novel-issue-draft.json` is an optional discovery list, not additional labeled pilot examples or an accepted issue catalog.

CSV text starting with spreadsheet formula characters has a protective apostrophe. Original text remains in the JSON drafts and is bound by the registration hashes. Packet checksums and source snapshot are recorded in `packet-manifest.json`. Keep all originals for reconciliation; never edit the sealed registration to accommodate a changed source.

## Offline browser review

The separate **Build private browser reviewer** workflow converts the pinned original training packet into a private `training-review.html`; it does not resample examples or load calibration/test files. Download the HTML while signed into Hugging Face and open the local file in your browser. Enter a reviewer ID, choose a status and any applicable stance, then confirm each reviewed example. Edits clear confirmation.

**Export reviewed JSON** includes confirmed examples only, retaining original source fields and the registration hash. Upload that JSON to the private assistant conversation for validation, codebook adaptation and reconciliation before any training. **Save progress JSON** includes unfinished work; import it into the same HTML to resume. The HTML makes no automatic network requests and uses no browser storage. Save a progress file before closing. Source-changing, duplicate or mismatched imports are rejected. This training reviewer intentionally excludes all 60 calibration and 60 sealed test examples.

## Validating returned reviews

Use `python -m un_transcript.models.review_intake --draft PRIVATE/train-draft.json --registration PRIVATE/registration.json --packet-manifest PRIVATE/packet-manifest.json --reviewer-manifest PRIVATE/reviewer-manifest.json --returned PRIVATE/un-pilot-reviewed.json --output PRIVATE/validated-training.json`. Obtain original inputs and reviewer manifest from their pinned private dataset revisions. The command verifies frozen input checksums and rejects unfinished progress exports, altered source fields and wrong packet identities. Add `--previous PRIVATE/validated-training.json` and choose a new output path to combine later returns. Identical repeated examples are deduplicated; conflicting judgments or reviewer identities require explicit resolution. Partial confirmed subsets retain their original feasibility-pilot status. This command never trains, promotes a model, changes sealed splits or claims comprehensive acceptance.

### Review identity and conflicting imports

Confirmed choices belong to the reviewer ID under which they were confirmed. Changing that ID preserves choices but clears all confirmations, requiring review under the new identity. Imports from another reviewer cannot merge into confirmed work. A conflicting imported judgment cannot overwrite a confirmed example: save the current file, inspect the conflict, and explicitly unconfirm/edit the affected example before importing a resolved version. Identical repeats remain safe. The intake tool independently rejects mixed reviewers, conflicting judgments, incorrect export schemas/counts and malformed prior-export hashes. These checks establish file consistency, not proof of a person's identity or scientific validity.

Latest verified training reviewer: [download the private HTML](https://huggingface.co/datasets/LystadJS/UN-Transcript-Agent-Private/resolve/d90a021976f4acca064930f73733926c54d91958/reviewers/43217469148-1/training-review.html?download=true), while signed into Hugging Face. [Build 43217469148](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/43217469148) passed on 12 November 2026 with 180 training examples from the unchanged original pilot. This revision includes reviewer-identity/conflict protections. Existing progress/review JSON from the original packet can be imported; sealed/calibration examples remain absent. No completed human review is implied by the build.
