# Humanitarian policy contract v1

Implemented interfaces: `site/issue-ontology.js` and `site/issue-extraction.js`.

The two policy objects are allowing humanitarian relief access and protecting civilians from conflict harm. General aid, funding, development, biographical material, and institutional names alone do not establish these positions. The existing conservative national-expression rules remain authoritative; the adapter does not expand unsupported lexical matches.

A national observation has country_id, policy_id, context_id, date and support / oppose / qualified stance. Conditions remain attached; qualified does not mean conflicting. Different national statements on the same date may conflict and are retained for downstream resolution. Collective affiliations, unresolved wording and unsupported languages are withheld. Unspecified and domestic contexts cannot supply a bilateral comparison.

Requested action, reported condition and claimed implementation may overlap and are attached only to supporting sentence indices. These discourse labels are descriptive and do not independently imply support. All extracted observations remain assistant_provisional. No human-confirmed benchmark is created by this module.

Each observation carries a versioned source_revision_id, provenance hashes, original source URL and sentence indices. Public materialized observations omit raw source excerpts. Browser interfaces may retrieve permitted source wording separately. Repeat sources cannot add country-level weight. Conflicting metadata for one source ID is withheld pending correction.

The ontology and extractor versions form part of result cache identity. This initial adapter implements agenda A3 and D2 and the materialization interface for D6; calibrated extraction tournament acceptance remains pending benchmark confirmation and evaluation gates.

## Benchmark preparation

`research/issue_history/benchmark/review.py` creates metadata-only source-linked annotation packets with empty annotations and zero human-confirmed labels. Stratification fields retain year, body, language and recorded national status for sampling. Hash-based source splits support reproducible development diagnostics; the separate source-blocked temporal splitter withholds sources crossing temporal boundaries. Neither establishes a representative benchmark or model eligibility. Owner confirmation requires a separately supplied receipt and explicit annotations. Actual owner review, class coverage, temporal holdouts and leakage audit remain acceptance gates.

## Vote binding

The normalized vote adapter preserves categories, explicit eligibility and resolution stage/version. `bind_resolution` requires explicit policy/context/rationale/provenance and review state. A policy keyword alone creates no binding. Unspecified and domestic context bindings cannot enter bilateral comparison. Owner-confirmed binding state requires a confirmation receipt. This implements B5/B6 validation boundaries against synthetic fixtures; remote-family parsing and empirical coverage reconciliation remain pending.

## Extraction assessment boundary

`benchmark/assessment.py` evaluates deterministic candidate predictions against explicitly owner-confirmed, source-hash-bound labels. It requires receipt fields, disjoint source splits and a declared source-blocked temporal protocol. Attribution, stance, policy object and context accuracy include absent predictions and abstentions as errors; per-class joint accuracy and abstention counts expose majority-class shortcuts. Class coverage and accuracy gates are conservative configurable engineering defaults, not scientifically validated thresholds. Synthetic provenance always prevents eligibility, and the tool never promotes an extractor. Model calibration, external validity and resource acceptance remain separate unmet gates.
