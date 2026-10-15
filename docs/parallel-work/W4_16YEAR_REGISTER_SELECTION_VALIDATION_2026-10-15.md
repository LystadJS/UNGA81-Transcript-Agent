# W4 2008–2023 original-source genre, translation, roster and selection audit

**15 October 2026 — source/metadata validation, NOT empirical inference or release approval.**

## Decision

The fixed 99 recorded-affiliation × 16-year inventory has 1,584 unique country-year keys; 1,574 original-source-correlated records and ten unverified/structurally noneligible records. This source-coverage PASS is not sufficient for comparable speech-level genre, translation, a fully specified participation-at-risk roster, or source-selection probability identification. No model, 64-D reference, CI, site release or original-source mutation was executed.

## Independent provenance checks

- P1 and P2 private ZIP SHA-256 manifests: 28 of 28 members verified; no omitted entries.
- All 223 original UN General Debate PV PDFs covering 2008–2023 independently rehashed against saved raw-byte acquisition manifests. These checks use historical authorized project originals; the UN did not provide publisher-signed SHA-256 reference checksums.
- The predeclared 118-source 2008–2015 audit split recomputes to the original digest (90 development plus 28 quality-audit PVs). The 105 2016–2023 original PV documents and all prior source-linked 792 source statuses, original meeting dates, per-PDF and speech-text hashes reconcile exactly against the previous accepted 2016–2023 sidecar. Two of the 223 indexed sources do not contribute to the fixed 99-country available-source panel; 221 do.
- All 1,574 verified country-year rows reference an official UN index source meeting and agree on the index meeting date. All 10 unknowns preserve genuinely null source hashes, dates and meeting IDs; none is silently represented as no speech.

## Genre

All 3,379 UN speaker-index entries over 2008–2023 carry the GENERAL DEBATE agenda label. Yet 2,096 are co-tagged SPECIAL STATEMENTS; 188/223 PV meeting documents have at least one such index co-tag. Index tagging is NOT speech-boundary adjudication, so it cannot independently certify canonical delivered-address genre or guarantee comparable segmentation.

The combined 1,584-row P2 register has no speech-level genre field; the earlier 792-row 2016–2023 inventory labels its cells general_debate, but no new speech-level cross-era adjudication has been performed here. In 15 pre-2016 affiliation-years, the speaker index lists more than one PV meeting candidate (2009: 1, 2010: 9, 2011: 3, 2014: 2). Unique Harvard-text-to-original-PV corroboration does not alone justify the originally chosen one-address-per-affiliation-year sampling rule.

The 2020 index has 379 entries representing 192 distinct member-state labels (187 excess same-state/same-PV entries), and the 2021 index 278 entries representing 193 labels (85 excess same-state/same-PV entries). These are not 379 or 278 independent national addresses. Preserve original index rows and reconcile the canonical address before weighting or fitting.

## Translation

All 223 original-PV document source URLs request the official English version. This does not establish that each country's address was orally delivered in English, nor the translation/interpretation/version mechanism used in producing the English PV. The combined 16-year source register has zero independently authenticated per-speech delivered-language or translation-mode fields. All 1,574 corresponding derived row-level metadata values remain explicitly NOT_ADJUDICATED, not invented as English. The optional full-document language-cue scan exceeded the local execution bound and is NOT RUN; generic document cues cannot be assigned to an actor without segment evidence.

## Roster, source selection and missingness

The frozen 99 labels are country affiliations, not repeated independently identified humans. A complete 16-year UN membership/participation-at-risk roster is not established. Three preadmission affiliation-years are structurally not at risk and retained separately inside the original 1,584 expected cells; they must not be called absent speeches or removed without a distinct estimand decision. Gross observed source coverage is 1,574/1,584 (99.37%). An explicitly separate descriptive risk-set sensitivity gives 1,574/1,581 (99.56%) but DOES NOT change the frozen denominator.

Missing evidence includes four other original source-unverified new records, one nonmatching historical Harvard speech and two inherited older unresolved records. There are seven unresolved at-risk opportunities plus the three structural non-opportunities. None has imputed text, source identities, source weights or zero vectors.

The pre-2016 90/28 source-quality partition was deterministic, NOT a randomized sample. Every indexed PV is now available, but original Harvard speech availability, index inclusion, text verification and translation may depend on observed or unobserved features. No known source-selection inclusion probabilities apply to the complete affiliation-year target. No propensity model was fitted; estimated verification q, propensity support threshold <0.10, capped inverse weights, clipped fraction and standardized covariate balance are NOT RUN, not passes. Uniform speech opportunity for the fixed 99x16 panel is structurally nonpositive for the three preadmission cells. MAR cannot be established from observed speech evidence; MNAR sensitivity bounds remain NOT RUN.

## Separate decisions

| Gate | Status |
| --- | --- |
| Source identity, 99x16 keys, official meeting/date metadata | PASS |
| Meeting-index General Debate provenance | PASS (index level only) |
| Speech-level genre and translation measurement comparability | NOT VERIFIED |
| Annual roster at-risk and canonical source choice | INCOMPLETE |
| Source selection probability/positivity/MAR assumptions | NOT RUN or NOT IDENTIFIABLE; structural risk-set FAIL |
| Full 16-year lexical/model fits and preregistered 36-cell known-truth calibration | NOT RUN |
| Calibrated empirical inference and public empirical release | FAIL / FAIL |

GitHub PRs #51, #52, #59 and #61 were merged independently on 15 October 2026; those engineering-source merges do not validate inference. This audit did NOT merge PRs, modify the source hashes, open any of the 37 reserved October 5–6, 2026 transcripts, alter frozen D1 O1–O5 or publish source-linked country records.

**Next:** privately review speech-level segment/genre, delivery language and translation provenance; adjudicate multi-PV canonical speech choices and duplicated index records; validate annual UN membership risk-set status, then pre-register a selection/positivity/MNAR evidence audit before any numerical model fitting. The detailed private 1,584-row metadata register, source-only reproduction script, six regression controls and full technical report were provided separately outside public GitHub.

