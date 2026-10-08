# Independent nuisance and held-out readiness audit

**Audit date:** 8 October 2026. **Disposition: HOLD — not ready to execute real held-out evaluation.** The 37 reserved meetings (5–6 October) remain unopened. This review inspected only cached development texts, previously saved numerical arrays, and the **already-frozen metadata roster**. It did not check live availability or collect any reserved transcript.

## Scope and independently verified evidence

The SHA256-sealed evaluation lock remains intact (`2c96f479fae0eded4b226882e05462b7f800c32fa066a6bb26df043b5d278039`). Eleven independently checked lock/source/model references match their original bytes. All **1,293** original development source segments and **2,596** technical passage text slices reproduce their source hashes and Unicode offsets with **zero mismatches**. Exactly **1,641** strict provisional passages map to **523 observed source segments** in **16 meetings**. These are not human-verified independent speeches. No source row from the reserved split entered the audit. The original held-out inventory contains 37 meeting metadata records, of which **33** were marked transcript-available and **4** unavailable *at the frozen snapshot*; this does not establish current availability. The actual development input contains October 1–2 records only, although the declared window was October 1–4.

## Key sensitivity results

| Independent check | Result | Correct interpretation |
|---|---:|---|
| Lexical–semantic cross-meeting 15-neighbor overlap | **39.4%** | Reproduces the earlier descriptive source-paired metric |
| Both representations masked for explicit country names | **40.8%** | Country-name masking does not remove the generic paired-retrieval signal |
| Cross-meeting semantic neighbors with same genre | **64.2%** | Versus **46.7%** under a uniform eligible-neighbor baseline; substantial genre structure remains |
| Cross-meeting semantic neighbors with same recorded role | **67.1%** | Versus **57.1%** uniform baseline; role structure remains |
| Repeated-country subset: same-country semantic neighbors | **9.1%** | Descriptive recorded-country recurrence, not policy similarity |
| After explicit country-name masking | **3.8%** | Much smaller; demonyms/agenda/roles remain |
| Excluding same-genre neighbors (original / masked) | **5.8% / 2.1%** | Changes eligible retrieval population; comparisons are **not additive causal effects** |

The source population is concentrated: **338 of 523** strict source segments (64.6%) occur in just four Human Rights Council meetings, and the three largest meetings account for **48.9%**. **152 of 523** segments (29.1%) lack resolved country attribution. The recorded-country test conditions on just **319** segments representing 86 countries observed in at least two meetings. Equal-meeting weighting gives cross-representation overlap **40.4%** versus 39.4% under equal-source weighting; dropping one entire development meeting at a time gives **37.9%–42.3%**. This robustness is descriptive, not external replication or calibration.

The matching source metadata has affiliation/group/function fields but **no distinct speaker identity**; recurrence of the *same person* across proceedings is therefore not independently assessable. In the strict population, zero exact source-text hash families repeat across meetings, but the larger original development source layer contains three such families. The earlier country-name dictionary also matches the generic English word **“island” 32 times** and **“Thai” six times**; these false-positive/ambiguous masking candidates limit any claim that the 3.8% residual precisely isolates country self-identification. Revisions must be performed as separately named sensitivity runs, not retrospective changes to the frozen analysis.

## Independent readiness assessment

| Gate | Status | Evidence / missing requirement |
|---|---|---|
| Saved source and frozen numerical hashes | **PASS** | Eleven cryptographic file references and full Unicode passage-slice reconstruction checked |
| Reserved transcript access restriction | **PASS for this audit** | No reserved transcript requested, read, embedded, fitted or scored |
| Frozen 37-meeting metadata frame | **PASS** | Sealed count and source-frame identity; current availability not assessed |
| Synthetic-only evaluator guardrails | **PASS in tested cases** | Six malformed/non-synthetic fixture variants rejected; no authorization implied |
| Real raw-source evaluation pipeline | **BLOCKED** | Synthetic dry-run accepts artificial vectors; it does not exercise full real source parsing, classifier/eligibility behavior and frozen inference on representative synthetic JSON responses |
| Country, role, speaker and genre nuisance separation | **NOT ESTABLISHED** | Genre/role concentration and source-name signal remain; no person-level speaker identifier |
| Independent substantive-null calibration | **NOT ESTABLISHED** | Two development conditional references do not test political-cluster existence; earlier model settings informed development selection |
| Held-out eligibility/missingness/coverage | **UNKNOWN** | Held-out text must not be inspected without separate authorization; minimum 200 parents, eight meetings and 70% movable fraction cannot be established from metadata alone |

**Disposition: HOLD.** The seal is a valid record of the prior heuristic protocol, but it is not a signed approval, a functioning real-source evaluator, or evidence of political nonrandomness. The two within-development p-values are conditional on a narrow set of nuisance assumptions and do not account for all earlier analytical choices. A successful synthetic decision branch is only a code-path rehearsal. Without a distinct speaker identifier, cross-source recurrence of the same person can only be bounded through proxies rather than verified.

## Prioritized remedies, without accessing the 37 transcripts

1. **Build and adversarially validate a production-shaped artificial UN response fixture.** It must exercise exact 37-roster identity, status/coverage accounting, source hash and timestamp failures, language and transcription flags, safe parent segmentation and country missingness, machine-only review, saved TF-IDF/LSA and local MiniLM transforms, meeting-level aggregation, and lock-consistent no-refit predictions. Keep all fake dates/IDs and fail closed on unauthorized real-source URLs.
2. **Add separately declared development sensitivity analyses for agenda and speaker-proxy dependence.** Standardize or block by meeting family/genre/recorded role; quantify available affiliations, duplicated formulas, self-country references and source-level uncertainty. This is not a replacement for genuine speaker identity or a null calibrated for policy agreement.
3. **Audit the masking dictionary** for generic aliases, demonyms and false negatives, then evaluate a *new*, explicitly versioned masking sensitivity. Retain the frozen prior reference, original text, and review audit unmodified.
4. **Treat out-of-domain genre and missingness as prospective preflight gates.** Eight of the 33 originally available reserved meeting metadata records have genres absent from the strict development population (press, Security Council, high-level and meetings/events). Determine how abstentions, translation and missing country labels will be disclosed before any content is seen. If the fixed one-shot metric cannot be evaluated, report **inconclusive**, never re-optimize on the reserved period.
5. **Require separate explicit authorization before any reserved-source acquisition.** The existing 37-meeting frozen roster and decision threshold should remain sealed; any stronger alternative evaluation must be declared as a separate protocol, not silently substituted.

## Audit limitations and reproducibility

This audit independently rebuilt 15-nearest-neighbor tables from saved matrices using direct cosine similarity, aggregated by source segment with the originally specified token-count weights. It inspected the *actual code* of the frozen evaluator and performed six adversarial synthetic-fixture rejection checks, plus five data-free metric tests. It did **not** re-download original development transcripts, validate transcription/audio against recordings, identify real speakers, run a new semantic model, access the reserved transcript content, establish statistical independence, or measure held-out predictive performance.

The companion `independent_audit.py` runs only on an existing source-bound **development** checkpoint, saved semantic outputs and saved masked outputs; it has no network client or holdout loader. The full private inspection JSON contains development meeting IDs only. **Only this aggregate report and source-free validation record are suitable for the public repository.**
