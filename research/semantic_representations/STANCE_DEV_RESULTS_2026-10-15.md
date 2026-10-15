# Preregistered 30-family stance development evaluation — executed 2026-10-15

**Engineering validation:** PASS. **Scientific stance validation:** NOT ESTABLISHED. **PR #66:** DRAFT, DO NOT MERGE.

## Freeze and execution order

Prospective rules, strata, candidate methods, abstention behavior and development advancement criteria were committed *before execution* at protocol commit `4efec4645a5878252e761a7af3d3b3248660ef4d`, file `STANCE_DEV_PROTOCOL_FROZEN_2026-10-15.md` (blob `14c102ac8e5a1af896733b38da67086d9c9607c9`). The evaluator implementation and fixture text were committed afterwards as `stance_dev_evaluation.py` (blob `afc15414c7ec23c740c94a38826badaeb2755901`) and `test_stance_dev_evaluation.py` (blob `dceb96ff2d46b0d9276aa35edf51df9f85d25c22`). The earlier four- and sixteen-family adverse synthetic records remain unchanged, not retrofitted as training.

**Native coordinator execution:** Complete full-repository checkout on exact accepted base and copied PR #66 source blobs, coordinator-only test commit `c475bfa91542f11425649f8726043031afc19807`; [GitHub Actions run #38812678143](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38812678143), job `116689532103`, SUCCESS. Pinned original MiniLM ONNX checkpoint, tokenizer and artifact SHA-256 checks PASS. Exact upstream Python 3.13 dependency runtime. Predeclared 9 adversarial unit tests PASS. Two fresh Python processes independently encoded all 120 new synthetic strings with zero failed batches or not-fitted rows and returned identical full canonicalized JSON receipts. Receipt SHA-256:

`314d38673983f7ed311869a4521bd8bbc6f1f34e4cf2a11ab8083e0b6e112b37`

Synthetic selection SHA-256 (ordered 120 IDs, canonical JSON): `5e0c644dbbd4ec7447950595e48a6d28f1cdd44ea592788343417066c719296a`. These are invented public-safe cases, never actual UN meeting texts.

## All attempted cases and results

Source population: 30 authored synthetic families, four statements each = **120** text observations. Strata: explicit first-person 8, negated stance cues 6, conditional qualifications 4, quotes/third-party 4, changed object/proposition scope 4, ambiguous/no cues 4. For M0 and L0, a nonabstaining cosine is only textual relatedness; it is **not** stance attribution.

| Method | Explicit 8 correct | Negated 6 correct | Combined evaluable 14 correct | Guard-family abstention (16) | Model failures |
|---|---:|---:|---:|---:|---:|
| Pinned MiniLM-L6-v2 cosine | 0 | 0 | **0/14** | 0/16 (not an abstaining method) | 0 |
| Same-synthetic-source fitted word 1–2 gram TF-IDF cosine | 0 | 0 | **0/14** | 0/16 (not an abstaining method) | 0 |
| S1 strict polarity-gated MiniLM | 8 | 6 | **14/14** | **16/16**, all 48 guard pair comparisons | 0 |
| S2 fixed signed-coordinate TF-IDF (sign magnitude 2) | 8 | 6 | **14/14** | **16/16**, all 48 guard pair comparisons | 0 |

M0/L0 remaining guard-family ordering results were retained in CI: the unmodified MiniLM cosine ranked intended paraphrase first in 3/4 altered-proposition scope cases and 0/12 other guard cases. The lexical baseline ranked it first in 0/16 guard cases. These outcomes are **not** stance predictions because the source proposition or actor identity is withheld for guard cases.

The **S1 and S2 improvements are engineered into the representation rule**: they explicitly inspect familiar support/oppose verbs, invert narrow `do not` forms, require *artificially assigned proposition IDs*, and abstain for conditionals, quotes, changed scope and cue-free text. Their 14/14 is a unit-like behavioral check, **not evidence that the system understands unseen stance**. They share the same polarity extraction rules and cannot be counted as two independent confirmations of diplomatic agreement. None was trained, optimized or threshold-tuned on the cases.

## Preregistered advancement decision

The **development-only** rule required >=13/14 correct cue comparisons; >=15/16 guard-family abstentions; no silent failed inference; and 100% adversarial refusal in added negative controls. The execution met the numeric thresholds for **both S1 and S2** and all 9 new tests passed, including tampered source/identity, restricted split, quote/condition/scope refusals. Therefore **S1 qualifies only for design of a genuinely independent, newly authored synthetic holdout**, with S2 retained as a dependent secondary comparator. This is **not** authorization to open any reserved 2026 meeting transcripts, run real-data inference, or publish empirical findings. No statistically calibrated confidence or out-of-sample accuracy is established.

Before any future independent synthetic holdout, independently author heldout sentences/labels; include paraphrases with polarity words absent, indirect modality, nested negation, quotation, third-party speech, same-word different-object propositions and different-word same-object propositions. Fix heldout design and source metadata before viewing scores. The original historical lexical TF-IDF/LSA fitted geometry was **not** available or used; only the synthetically fitted L0 comparator was evaluated. No actual independently pinned stance-trained neural checkpoint was selected or executed; S1/S2 are handcrafted rule-composition alternatives.

## Hard constraints

No private text, model vector caches, source-linked empirical rows, original-PV/Harvard source bytes, holdout meeting text, reserved October 2026 evaluation content or credentials were opened or added to public GitHub. All source provenance, D1 O1–O5, human decisions, empirical fit and public publication remain unchanged/WITHHELD. Benchmark and its complete numeric evaluation are engineering-only; no website, mirror, source package or release was touched.
