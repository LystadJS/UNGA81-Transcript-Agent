# Day-summary owner evaluation protocol

**Lock status:** frozen at `2026-11-05T18:11:28Z`, before opening or scoring the untouched test sample.

**Machine-readable lock:** [`research/day_summary_evaluation/acceptance-lock.json`](../research/day_summary_evaluation/acceptance-lock.json).

**Source registration:** [`research/day_summary_evaluation/sample-registration.json`](../research/day_summary_evaluation/sample-registration.json).
**Evaluation role:** the owner is the single reviewer and finalizer for this operational pilot. Owner-confirmed decisions are human review, but they are not independent gold labels or inter-rater agreement.

## Decision this protocol supports

This evaluation asks whether one browser generation action produces a usable daily orientation from the available English transcripts. It evaluates the deterministic day summary, its three default visualizations, and their source bindings. It does not validate official agendas, speaker identities, government positions, real-world importance, or population-level accuracy.

The 37 reserved meetings dated 5–6 October 2026 are outside this protocol. Their transcripts must remain unopened. An untouched test sample must come from separately authorized, non-reserved sources and must be committed by source identifiers and hashes before its labels or engine output are inspected.

At lock time, the public workspace contains owner-reviewed passage-relevance pilots and product-level daily packet checks, but no qualifying owner-reviewed day-summary development bundle spanning the coverage required below. The thresholds were therefore locked prospectively. The immutable threshold lock keeps its legacy sample commitments empty, and the separate source-registration manifest is also empty. That state is **insufficient**, not a pass; samples may be added to that manifest without changing these thresholds.

Every registered sample must be recorded before its review begins. Each day binds its meeting IDs, dates, bodies, meeting types, source IDs, and source SHA-256 hashes. Development and untouched-test registrations must use disjoint dates, source IDs, and source hashes. The registration document is canonically hashed and binds to the threshold-lock hash; reviews and browser receipts bind back to both hashes.

## Evaluation stages

1. **Prospective acceptance lock.** This document and the JSON lock fix the metrics, denominators, minimum sample coverage, thresholds, critical errors, and one-action browser checks before a qualifying development or untouched sample exists. Changing any locked value creates a new protocol version and requires another untouched sample.
2. **Development evaluation.** Register and score qualifying owner-reviewed daily samples. Record each sample date, body, meeting type, meeting identifier, source version/hash, and review-file identity. Repair is allowed after this stage, but every repair and affected rule version must be recorded. Development evaluation and repair do not change the prospectively locked thresholds.
3. **Untouched test.** Freeze the test manifest before content review. Run the locked engine once, save the exact report, and then reveal the owner labels. Do not tune rules, labels, topic aliases, or thresholds after viewing test results.
4. **Decision.** Report every numerator and denominator. A rate with an unmet minimum denominator is `insufficient`, never a pass. Acceptance requires every rate threshold, every critical-error gate, the sample-coverage gate, and the one-action browser gate.

Development and test results remain separate. A pooled descriptive total may be reported only after both stage-level tables are shown; it cannot rescue a failed test gate.

## Review unit and label contract

The owner reviews the complete collected English record for each included day, with meeting boundaries and collection gaps visible. The review file records:

- substantive policy questions that should appear at day level;
- allowed synonym links and explicit different-policy boundaries;
- each generated proposal, disagreement, development, or other substantive claim as `supported`, `unsupported`, or `uncertain`;
- each recorded-country attribution as `correct`, `incorrect`, `collective`, or `unresolved`;
- meeting and source identifiers for every reviewed item; and
- a reason for every error or uncertain decision.

Every claim, topic, grouping, and attribution decision carries its meeting ID, body, and meeting type. Per-body and per-meeting-type results are computed from those row-level bindings. Uncertain or unreviewable items remain outside both metric and minimum-coverage denominators and are reported separately. The evaluator must not convert an uncertain item into a success. Repeated identical claims, exact repeated passages, and resumed copies count once for claim support and national participation, while their meeting provenance remains visible.

## Locked error measures

| Measure | Numerator | Assessable denominator | Acceptance threshold |
|---|---|---|---:|
| Unsupported claim rate | Generated substantive claims marked unsupported | Generated substantive claims marked supported or unsupported | **≤ 5%** |
| Missed substantive-topic rate | Owner-identified substantive policy questions absent from generated topics after allowed synonym matching | Owner-identified substantive policy questions marked present or missed | **≤ 15%** |
| Incorrect grouping rate | Reviewed grouping decisions that merge different policy questions or split owner-approved synonyms | Reviewed grouping decisions marked correct or incorrect | **≤ 5%** |
| Attribution error rate | Generated recorded-country attributions marked incorrect | Generated recorded-country attributions marked correct or incorrect | **≤ 5%** |

A claim means one displayed proposal, disagreement, consequential development, or substantive narrative assertion. Chart cells are descriptive measures rather than claims, but their source drill-down and counting-unit assertions are checked under the browser gate.

### Critical errors

Any of the following fails the evaluated stage regardless of the aggregate rates:

- a displayed substantive claim has no retained source passage and allowed source link;
- a source excerpt, record identifier, or meeting identifier does not bind to the saved collection;
- an explicitly collective statement is assigned to one country;
- two policy questions that the locked owner review marks as different are merged into one country position;
- repeated passages increase a country-topic participation cell above binary presence; or
- the browser reports success while a required summary or visualization is silently absent.

## Minimum assessable coverage

The development set must span at least **3 days, 3 UN bodies, 4 meeting types, 12 meetings, 40 generated substantive claims, 30 owner-identified substantive topics, 25 grouping decisions, and 30 recorded-country attribution decisions**.

The untouched test must span at least **2 days, 2 UN bodies, 3 meeting types, 6 meetings, 25 generated substantive claims, 20 owner-identified substantive topics, 15 grouping decisions, and 20 recorded-country attribution decisions**. At least one test day must contain multiple bodies and at least two meeting types. No one body may supply more than 70% of assessable claims or owner-identified topics.

Meeting type is a source-metadata category, such as General Assembly plenary, Main Committee, Security Council, Human Rights Council, treaty body, press briefing, or another explicitly recorded type. The evaluation must publish the achieved distribution and all coverage gaps.

## One-action browser acceptance

Starting from a retained daily collection or a newly completed daily collection, one activation of **Generate report** must produce, without a second analysis action:

1. the complete day-level summary;
2. meeting-specific distinctions;
3. topic distribution;
4. topic-by-country matrix;
5. meeting-by-topic overview;
6. a visible counting unit for every chart;
7. a readable table alternative for every chart;
8. source drill-downs for every available chart; and
9. an explicit insufficient-data message for every unavailable chart.

The gate requires **100% completion in every assessable browser run**, zero uncaught JavaScript errors, and no document overflow at the tested desktop and 390-pixel mobile widths. The saved analysis JSON and standalone HTML must retain the same summary and visualization data. A hashed browser receipt must bind the tested summary hashes to the registration and threshold lock; the semantic thresholds cannot pass without that receipt. Optional PCA, clustering, NMF, similarity, and lexical methods must stay inside advanced controls and are not prerequisites for the default summary.

## Reporting and interpretation

The evaluation report must include the locked protocol identifier, engine version, sample-manifest hash, owner-review hash, exact confusion counts, uncertain counts, per-day results, aggregate results, body/meeting-type distribution, browser evidence, and the number of reserved transcripts opened. That last value must remain zero.

Passing this protocol means the deterministic browser workflow met the locked operational criteria on the declared owner-reviewed samples and one untouched sample. It does not establish representative accuracy, independent human agreement, verified national policy, or fitness for unattended publication.
