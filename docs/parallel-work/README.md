# Parallel development coordination

**Coordinator document set — 8 October 2026.** Baseline `main`: `f8d1c239e163c5167e44d97ddb42c2c07562a3a9` (PR #14 already merged). These documents are a proposed coordination protocol; they do not certify that worker implementations, model validations, or website releases exist.

| Document | Purpose |
| --- | --- |
| [PLAN.md](PLAN.md) | Seven workstreams, phases, handoffs and release boundary |
| [OWNERSHIP.md](OWNERSHIP.md) | Reserved branches, exclusive code namespaces and coordinator-only paths |
| [DEPENDENCIES.md](DEPENDENCIES.md) | Contract-first dependency graph and conflict resolution |
| [PR_ACCEPTANCE.md](PR_ACCEPTANCE.md) | Per-PR evidence, replay, CI and integration checklist |
| [INTERCHANGE_V1.md](INTERCHANGE_V1.md) | Versioned analytical interchange contract, adapters and examples of mapping |
| [interchange-v1.schema.json](interchange-v1.schema.json) | Structural JSON Schema for text-free, analytical metadata envelopes |

## Scope and source of truth

`LystadJS/UNGA81-Transcript-Agent` is the source of truth. Work on this branch is **documentation/contract only**. An analytical interchange envelope is a **derived, versioned adapter output**, not a replacement for `un.browser.corpus.v1`, `un.latent-comparison.v1`, `un.passage-corpus.v1`, the reviewed-data schemas, or any original bytes. Existing production and R/D1 kernels continue unchanged.

Read `AGENTS.md`, `docs/NEXT_STEPS.md`, `docs/PASSAGE_CORPUS.md`, `docs/LATENT_COMPARISON.md`, and `research/reference_tests/AGENTS.md` before implementing. Important contracts live in `research/corpus/contract.cjs`, `site/analysis-core.js`, `site/cluster-core.js`, `site/latent-core.js`, and `tools/review_data.py`.

The October 5–6 **37 reserved meetings stay unopened**. Do not download, display, parse, embed, inspect, score or fit their transcript text. Frozen inventory metadata and their existing digest may be referenced without opening content. No modification to `research/reference_tests/evaluation-lock.json`, original corpus/source digests, completed human decisions, or O1–O5 gates. Keep private original text, review materials, annotation ledgers and source-linked row-level analyses outside the public repository. Public PRs may carry synthetic fixtures and non-identifying aggregate test receipts only.

## Integration policy

Workers may start independent feature branches from current `main`, each inside its owned namespace. They open PRs but never merge, enable auto-merge or rewrite another worker's branch. All changes to shared entry points and published site assets are coordinator-only follow-on integrations. For each PR, the coordinator re-fetches `main`, reads changed paths, checks upstream interfaces, reviews CI and provenance, rejects overlaps, and merges only validated compatible work. Merge order is evidence-driven, not completion-time-driven. Do not force-push shared branches.

After a **validated source PR is merged** and the public build passes, the coordinator alone synchronizes approved site assets into `LystadJS/LystadJS.github.io` via the established `scripts/sync_un_project.py` mirror workflow, checks the deployed URL and asset hashes, and records that verification. A documentation or analysis-only PR does not trigger a website mirror.

**Current status:** coordination protocol staged; no independent worker acceptance, source integration, or website synchronization claimed. Reinspect PRs only when requested; no asynchronous monitoring.
