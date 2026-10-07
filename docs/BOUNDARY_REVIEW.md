# Expanded development corpus — source-linked boundary review

The **local boundary-review packet** presents all 1,293 original source segments
and their 2,596 exact technical passage windows from the frozen development
checkpoint. The 21-meeting inventory includes 20 cached transcript responses and
one unavailable meeting. No topic or result-based subsampling is performed.

The 37 reserved meetings on 5–6 October remain unopened. The packet includes only
their count and date range, not their IDs, titles, links or text. Packet generation
reads the saved development corpus and makes no network requests. It does not
rerun the completed owner audio/boundary pilot or invent new human decisions.

## Use the delivered ZIP

Extract it, then open **index.html** in a browser that permits local active HTML.
No server, installation, API key, model or transcript upload is required. A
managed browser may restrict local HTML; use an approved environment rather than
changing security settings. Original UN links are optional, manual navigation to
the selected development meeting; cached response files work without those links.

1. Enter your reviewer name and select a meeting. The queue uses original segment
   order. Read the complete segment plus previous/next source context.
2. Choose the source type and observed speech extent. Assign a speech ID only
   when that identity is supported. The helper button fills a unique ID but never
   confirms the decision. Near-complete coverage requires a note.
3. Select **Confirm and next**. Selecting fields alone saves a draft. Confirmed
   choices are read-only until explicitly reopened; no automatic/batch approval
   is provided.
4. Use **Save review JSON** before closing and retain downloaded versions. Resume
   with **Resume saved JSON**. Upload the saved JSON to the project for validation;
   partial reviews are supported. Browser storage is a convenience, not a backup.

Each segment includes the unaltered extracted text, recorded affiliation and
speaker metadata, exact raw-response/text hashes, JSON pointers, sentence offsets,
local raw JSON and original development-meeting link. Source timestamp warnings
remain visible; links are not verified audio-boundary annotations. Every technical
window shows exact zero-based Unicode code-point bounds, token count and existing
eligibility/exclusion reasons. Source text uses textContent, never interpreted HTML.

The entire queue remains present, including short, empty, procedural and uncertain
records. Display filters do not change the cohort or its denominator. An unavailable
meeting has a coverage entry but no invented task. “Confirmed reviews” measures
recorded decisions, not the number of eligible speeches or resolved uncertainties.

## Decision scope

The packet writes the existing `un.corpus-boundary-review.v1` contract. It supports
whole-source-segment type, observed extent, explicit speech identity, reviewer,
timestamp and notes. It does **not** edit text, split an internal speaker boundary,
merge source text, correct country attribution or apply audio correction notes.
For a mixed-speaker/internal-boundary problem, choose `uncertain`, retain unknown
extent and describe the needed split; do not call the entire record a complete
speech. A technical 160-token boundary is not a semantic topic boundary.

A shared speech ID is accepted only within the same meeting with consistent
recorded country, affiliation and speaker metadata. Matching metadata are a
necessary consistency check, not proof of a common speech. The reviewer remains
responsible for the identity/extent judgment. Draft choices do not become reviewed
observations. Existing corpus eligibility and weighting rules remain unchanged.

Imports reject a mismatched source bundle/packet, altered text hash, unknown or
duplicate source ID, unknown choice field, malformed confirmation, invalid time,
and conflicting speech grouping. The name/timestamp records an explicit local
review action; it is not independent authentication or inter-rater agreement.

## Rebuild and validate locally

Run from the repository with Node.js 22. Restore the original checkpoint to a local,
ignored directory first. Do not collect new sources or open reserved meetings.
Output paths must be new; the builder never overwrites an existing review packet.

```sh
node tools/boundary_packet.cjs build path/to/work/build/corpus.json NEW_PACKET_DIRECTORY
node tools/boundary_packet.cjs validate path/to/work/build/corpus.json saved-review.json
```

The first command re-derives the entire corpus from its original response bytes,
then verifies every source/partition hash before writing `index.html`, the pending
review template, source queue, cached raw responses, manifest, instructions and
checksums. Identical inputs and implementation produce identical packet files.
The second command validates returned choices and performs an in-memory rebuild
through the unchanged corpus contract. It writes no modified corpus. After that
check, use `tools/passage_corpus.cjs build` with the original frame/source bundle,
a new output directory and the saved review as its fourth argument.

Text-bearing packets, returned choices and screenshots of real sources remain
local artifacts, not source-repository or public-website assets. The generic
builder, data-free UI, synthetic tests and documentation are committed. `site/`,
`un/`, the frozen sampling frame and the existing numerical kernels are unchanged.
No website mirror update is necessary because this is not a public UI deployment.

## Acceptance

```sh
node tools/test_boundary_packet.cjs
node tools/test_passage_corpus.cjs
```

`Development boundary review` CI runs the new shared-contract tests and all 15
existing source/analytical regression suites. Browser acceptance uses a synthetic
packet for actual confirmation, export/import, resume and rejection tests. A
separate real-source rendering run checks coverage, exact text and links without
classifying or confirming any real observation. Desktop/mobile layouts, original
source markup safety, cached-source preservation and zero external requests are
recorded. A local loopback preview is distinguished from direct-file acceptance;
the initial sandbox browser blocked both navigations by administrator policy.
Final results are recorded in `BOUNDARY_REVIEW_VALIDATION.json` when available.

No model is fit, no weighted estimator is introduced, and no held-out performance,
independent replication or nonrandom diplomatic finding is implied by this packet.
