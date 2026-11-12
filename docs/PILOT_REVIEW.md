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
