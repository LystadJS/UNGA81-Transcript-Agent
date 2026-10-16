# Coordinator source-to-readout v1 — synthetic engineering acceptance (15 October 2026)

**Decision: PASS for isolated, synthetic-only interchange mapping and withholding behavior. NOT APPROVED for real-source use, automatic publication, or merge.** Source authority and reviewer/statistical decisions remain separate. No real UN text, 37 reserved transcripts, 24 owner decisions, D1 O1–O5, Shiny, Outlook, browser, manifests or website files were opened or modified.

## Exact pinning and provenance

- Repository: `LystadJS/UNGA81-Transcript-Agent`.
- Coordinator branch: `coord/evidence-first-readout-adapter`, based on `main` commit `691f13bb53232f72a40461855c8e08a78b21befe`.
- Worker readout import: unmodified PR #70 `028e3d26f707401cbff498593ab27f64e2cc072a` in a separate checkout. This worker PR is **draft and unmerged**, and its code has not been vendored or copied into this coordinator branch.
- v1 authority: `docs/parallel-work/interchange-v1.schema.json`, `INTERCHANGE_V1.md`, native W1 validators; exact commit is the base above.
- Source basis: invented synthetic bytes and string texts, Unicode code points, deterministic JSON pointer `/records/0/text`. The v1 upstream reports the distinct synthetic aggregate source and selection hashes. `UpstreamValidation` is an exact-digest **consistency receipt, not an independent original-source certificate or cryptographic signature**.

## Hosted CI

- [GitHub Actions run #38768705355](https://github.com/LystadJS/UNGA81-Transcript-Agent/actions/runs/38768705355) — **PASS**, job `116538585735`.
- Environment: GitHub Ubuntu runner, Python 3.13, Node 22, `jsonschema==4.26.0`; bridge uses no model training or random draws. Pinned PR #70 checkout is asserted at exact commit.
- 30 new bridge tests: **PASS**, 0 failed. Checks include official v1 schema, population and model accounting, trust-receipt/digest mismatches, duplicate identities, source/parent/representation/text hash mismatch, JSON pointer and Unicode bound refusal, unavailable/excluded sources, contrary-role and false-absence safeguards, country and stance restriction, missing fits and failed-source withholding.
- 46 inherited PR #70 offline privacy/format/source tests: **PASS**, 0 failed; these were executed against the pinned worker checkout.
- Native v1, W1 validation framework, passage corpus, and latent comparison regressions: **PASS** on the coordinator branch's accepted upstream version. The actual native W1→W2 synthetic producer emitted a v1 envelope with **24 eligible** observations; the independent coordinator validation accepted its structural and fit ledger while deliberately **not** treating it as an approved readout.
- Five offline synthetic scenarios, each JSON/Markdown/HTML: **PASS**; two independently generated output directories are byte-identical. Exact synthetic manifest SHA-256: `7d9e3d3303cb00eb3f088a3260e58c18cc2164ffabb20e8793e32124f1f75ffb`. Cases: descriptive-only PASS (with independent fictional review verdict), and partial-statistical, unreviewed, failed-source, missing-evidence **WITHHELD**.
- Invented cohort accounting: 5 in declared inventory, 4 observed rows, 2 eligible, 1 available-but-excluded, 1 unavailable row, 1 unobserved-inventory item, **2 missing total**, 1 unassigned. Selected model: 1 planned/attempted/converged fit, 0 failed/skipped in this fixture. Different denominators are not conflated.

## Contract/gate disposition

| Check | Result |
| --- | --- |
| Coordinator namespace and workflow ownership | PASS — `research/integration/diplomatic_readouts/**` plus new coordinator-owned workflow only |
| Official v1 JSON Schema and relational identity/fit invariants | PASS for synthetic |
| Native W1-generated v1 envelope accepted as *metadata*, not source authority | PASS |
| Readout closed-world source proof, reviewer decision, privacy and deterministic exports | PASS on synthetic data |
| Missing, excluded, failed, contrary, country and stance refusal | PASS (synthetic negatives) |
| Original-source UN byte/selection authentication and private approved source frame | NOT RUN; **real source mode disabled** |
| Actual owner reviewer labels or proposition-specific national stance | NOT RUN / WITHHELD |
| Null calibration, dependence and statistical-release approval | NOT RUN / WITHHELD |
| D1 O1–O5/Shiny/Outlook/browser/public release testing | NOT APPLICABLE to this nonpublishing, import-only integration draft |
| Merge, email, draft modification, website publication | NOT PERFORMED |

## Limitations and next gate

The upstream digest, source registry object and reviewer decision remain trusted-host inputs; no class constructor or SHA digest establishes origin or reviewer independence. The isolated synthetic adapter **does not authenticate a live UN source or authorize a substantive diplomatic conclusion**. It excludes real/development splits, modified offset bases, sourced country positions, and unsupported statistical results by default. Language similarity is not policy agreement, clustering is not coordination, and temporal movement is not necessarily realignment.

**Next executable step:** coordinator independently reviews this PR's exact final head and the read-only CI job; subsequently proposes a separate authenticated source-registry/privileged-review adapter design after the needed source and human approvals. No merge, production injection, automatic publication, opening reserved transcripts or relaxing frozen gates follows from synthetic PASS.
