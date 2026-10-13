# Supervised development review — private intake and source-affiliation preflight

**Date:** 13 October 2026  
**Scope:** exclusively the **2016–2019 training/development** source partition and its previously frozen 96-item review packet.  
**Decision:** development source integrity **PASS**; automated original-PV source-affiliation concordance **PASS**; **owner-exported review-draft validation NOT RUN (file not supplied)**; owner-finalized position labels and empirical release **WITHHELD**.

This coordinator receipt contains **non-identifying aggregate counts, method descriptions and document/packet hashes only**. No original speech text, original-PV bytes, named national positions, speaker/person names, per-item source or country keys, private review records, or row-level analysis is committed. The original source and test locks, human decisions, D1 O1–O5 gates, and all site release/mirror assets were unchanged.

## Supplied inputs and restrictive handling

- Reopened **only** the user-supplied **UNGA81_Supervised_Development_Annotation_2026-10-12.zip**, and the **frozen plan/metadata and 2016–2019 training text entries** of **UNGA81_Supervised_Private_Source_Foundation_2026-10-12.zip**.
- The source-side attribution crosscheck additionally opened **only 42 original-PV PDFs from 2016–2019**, selected by the training packet's official meeting IDs from the separately uploaded **105-PV archive**. Each PDF byte SHA-256 matched the frozen source-quality ledger.
- The 2020–2021 calibration and 2022–2023 held-out test **speech/PDF texts were not opened**. The 37 reserved October 5–6 2026 transcripts were not opened.
- The original source-quality fields identify a **recorded individual national address capacity**, not an independently verified speaker/person, governmental-wide stance, or assurance that the passage speaks in a solely national capacity.

## Independent executed source-bound checks

| Gate | Status | Evidence/limitation |
| --- | --- | --- |
| Frozen source-plan SHA-256 and train-packet SHA-256 | **PASS** | Canonical JSON checksums recomputed, plus direct byte identity of the packet in the separate development ZIP and the private source foundation |
| Manifest and source-quality identities | **PASS for train** | Frozen codebook digest, sources/quality CSV digests, complete allocation metadata and disjoint country/speech-family/meeting/full-text SHA groups checked |
| Canonical 2016–2019 **training** text bytes | **236/236 PASS** | Local SHA-256 on **3,143,404 UTF-8 bytes** against the frozen training source manifest; no calibration or test parent source bytes read |
| Exact review quotations, original offsets and adjacent context | **96/96 PASS** | Original parent text, zero-based Unicode-codepoint-exclusive spans, 220-codepoint neighbor context; duplicate/unknown packet item IDs and unreviewed status checked |
| Original-PV PDF byte hashes, training meetings | **42/42 PASS** | Only original-PV PDFs for the selected development cases, with 77 distinct train speech sources among the 96 cases |
| Original-PV speaker/header affiliation | **96/96 machine concordant** | 52 extracted national-delegation `(Country)` speaker headings and 44 formal “Address by” headings agree with the recorded national country code. This is a **source-affiliation crosscheck only**, not proof of human speaker identity, sole-country/collective speaking capacity, or expressed stance |
| Original-PV normalized passage evidence | **96/96 located** | Full-passage approximate local text agreement `>= 92.4/100` under independent PDF extraction; extracted text is not itself the canonical original source basis |
| Disputed human attributions | **NONE SUBMITTED / NOT ADJUDICATED** | One generic “on behalf of the Government and people” national-capacity wording was **not treated as a multinational group dispute**. Human passage-specific role/quoted-context review remains obligatory |
| Actual exported owner draft | **MISSING — NOT VALIDATED** | No `country-position-private-draft.json` or owner-confirmed issue/stance decisions were present in the supplied files. Frozen foundation's review/annotation tables are empty |
| Owner-reviewed stance labels and gold/finalized labels | **0 / 0** | No human labels fabricated; empty candidate annotation CSV kept as a header-only placeholder |
| Review-intake validator negative controls | **9/9 synthetic checks PASS** | Correct dummy (unfinalized) draft accepted as candidate only; wrong packet SHA, missing attestation, improper gold flag, duplicate ID, unsupported stance, contradictory issue/stance, future timestamp and foreign source ID all rejected |

## Immutable source/packet lineage

- Frozen private source plan SHA-256: `2c6359c8a8827a19473b4b1f8aa006378ecefb68d6b9cef4df4f4d6b500278e8`.
- Frozen private 96-item development packet SHA-256: `436f0d0528bd7994ddb26a8452195922ace5cafca1ae6d327d143c91aa42c960`.
- Pre-existing proposition codebook SHA-256: `794e67a741952139c31c009d41af6914113651ead46a041fde4811475fca026e`.
- Private review preflight ZIP SHA-256: `1ba7e3e669dbda44af19c42276382ab4693c3810d9077aec0e046a4db6b08b08`.

All private item-level source-heading and attribution checks reside **only in the separate private conversation download**. The independent speaker heading parser and the private draft intake script are tools for review and fail-closed candidate intake; neither authenticates a human reviewer nor creates adjudication without actual owner choices.

## Remaining gates

1. **Owner action:** export the actual `country-position-private-draft.json` from the local offline development reviewer and supply it separately. Its packet digest and all 96 available source IDs must match the frozen development packet; absent choices remain unlabeled rather than assumed negative.
2. **Private candidate intake:** require explicit owner self-attestation, exact reviewed item IDs and proposition versions, valid issue/stance vocabulary, rationales, UTC review timestamps, no duplicate decisions, and no claimed gold/publication status. A syntactically valid draft is still **unfinalized** and its reviewer identity has not been independently authenticated.
3. **Human source attribution:** inspect the linked original-PV heading and affected passage context for actual speaker capacity, quoted positions and genuine group statements. Resolve/withhold any substantive ambiguity by an actual human finalization; an automated heading match must not auto-assign country policies.
4. **Separate later scientific gates:** source-separated calibration and untouched held-out test protocol, real supervised fitting acceptance, per-class accuracy, dependence-aware uncertainty, stance/evidence audit, and a discrete empirical release decision. These remain **NOT RUN / WITHHELD**.

**Release status:** historical development-source integrity and source-affiliation engineering **PASS**; owner review and real country-alignment **PENDING**. No new public results or country stances may be inferred.
