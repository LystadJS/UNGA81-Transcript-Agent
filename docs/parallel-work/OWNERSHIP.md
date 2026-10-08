# Exclusive namespace and branch ownership register

**Status:** branch names below are reservations for worker use, not claims that the seven branches or PRs have been created. Each worker owns exactly one branch and the indicated files. No shared worker edits. Coordinator branch for this initial protocol: `coord/parallel-interchange-v1`.

| ID | Reserved worker branch | Exclusive new implementation namespace | Allowed public tests and documentation |
| --- | --- | --- | --- |
| W1 | `feat/parallel-w01-source-validation` | `research/parallel/w01-source-validation/**` | Only inside that subtree |
| W2 | `feat/parallel-w02-consensus` | `research/parallel/w02-consensus/**` | Only inside that subtree |
| W3 | `feat/graph-based-learning` | `research/graph_methods/**` | Within that subtree, plus **only** `.github/workflows/graph-based-learning-research.yml` under the 8 October 2026 owner-approved exception |
| W4 | `feat/longitudinal-latent-structure` | `research/longitudinal/**` | Within this subtree, **plus only** the new `.github/workflows/longitudinal-framework.yml` under the 8 October 2026 owner-approved exception |
| W5 | `feat/parallel-w05-browser` | `site/parallel/w05-browser/**` | Only inside that subtree; synthetic Node tests colocated |
| W6 | `feat/parallel-w06-visualization` | `site/parallel/w06-visualization/**` | Only inside that subtree |
| W7 | `feat/parallel-w07-diplomat-ux` | `site/parallel/w07-diplomat-ux/**` | Only inside that subtree |

Worker code may **import** existing production APIs and the read-only v1 schema, but must not rewrite their source. Each PR contains files **only** in its owned prefix, except the precisely named W3 and W4 new workflows approved below. Worker-specific documentation/tests go inside that prefix, not `docs/**` or `tools/**`. Workers can give the coordinator an integration patch proposal in the PR description. Do not add a worker to an existing `site/index.html`, `site/latent.html` or loader by directly changing that file.

### Coordinator-only shared surfaces

- `AGENTS.md`, `README.md`, `docs/NEXT_STEPS.md`, all `docs/parallel-work/**` and shared contract versions.
- Existing browser entry points and loaders: `site/index.html`, `site/latent.html`, `site/app.js`, `site/analysis-ui.js`, `site/latent-ui.js`, `site/latent-worker.js`, `site/cluster-worker.js`, `site/app.css`, `site/analysis.css`, and any existing referenced shared site asset. **Treat all other pre-existing `site/**` paths as integration-owned too**, even if not listed.
- `site/release.json`, `site/numerics-manifest.json`, `un/**/PACKAGE_MANIFEST.json`, built/public manifests, `tools/build_pages.py`, `.github/workflows/**` (except the **new**, path-limited W3 and W4 synthetic workflows explicitly approved below), and all existing `un/**`, `research/corpus/**`, `research/reference_tests/**` and shared `research/engines*.R` source.
- `LystadJS/LystadJS.github.io` mirror, workflow, portfolio pages and live verification.

**Immutables even for the coordinator (unless a separate explicit authorized protocol is provided):** frozen held-out lock and protocol; the 37 October 5–6 transcript contents; original corpus/source hash records; 24 completed owner review decisions; D1 O1–O5 gates. Do not touch these as part of the seven-workstream integration.

### Owner-approved W3 exception — 8 October 2026

The repository owner explicitly approved the path/CI exception for [PR #16](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/16), after requesting coordinator review and authorizing its merge. The W3 reservation now adopts the existing `feat/graph-based-learning` branch and exclusive `research/graph_methods/**` implementation namespace. **Only PR #16** may add the *new* `.github/workflows/graph-based-learning-research.yml` workflow. It must stay limited to W3 synthetic engineering and read-only regression/contract tests, with `contents: read`. This exception does not authorize changes to any pre-existing workflow, shared entry point/loader, `site/**`, `un/**`, frozen source or evaluation protocol, D1 O1–O5 gates, versioned interchange schema, release manifests, or portfolio mirror. W3 workers must not modify `docs/parallel-work/**`; this coordinator-only decision records the already-issued owner approval.

The original proposed `feat/parallel-w03-spectral-diffusion` / `research/parallel/w03-spectral-diffusion/**` reservation is superseded for W3; no second spectral/diffusion implementation branch is authorized. This is a **file-ownership and uniquely named CI exception only**, not independent scientific validation, permission to open the 37 reserved October 5–6 transcripts, approval to infer political positions or influence, or public browser/D1 release authority. Coordinator PR acceptance, per-head CI, source provenance, and W1 compatibility gates remain required before any merge. PR #16 must remain engineering-only unless a subsequent distinct validation/release decision is made.

### Owner-approved W4 exception — 8 October 2026

The repository owner explicitly approved reconciliation of [PR #18](https://github.com/LystadJS/UNGA81-Transcript-Agent/pull/18) with this contract. The W4 reservation above now adopts the already-existing `feat/longitudinal-latent-structure` branch and its exclusive `research/longitudinal/**` path. **Only PR #18** may add `.github/workflows/longitudinal-framework.yml`, which must be path-limited to W4 synthetic tests with read-only permissions. This permits no edits to any pre-existing workflow, shared loader, browser source, frozen data, project-wide registry, or release gate. W3's separately authorized exception above is unaffected; the other workstreams retain their original boundaries. The former `feat/parallel-w04-longitudinal` / `research/parallel/w04-longitudinal/**` proposal is superseded for W4; no second longitudinal implementation branch is authorized.

This is a **path/CI exception, not a scientific or production approval**. W4 remains engineering-only until explicit source-lineage, dependence, statistical-comparability, real longitudinal coverage and release reviews pass. The separate coordinator acceptance checklist still applies, and no acceptance or merge is implied by this exception.

### Ownership enforcement

Before reviewing any worker PR, list every changed filename (including renames, symlinks, submodules, workflow changes and deleted files). Reject any file outside its namespace **and any narrowly approved W3/W4 new workflow exception**, including path traversal or changes introduced through generated assets. Reject competing PRs claiming one output/entry-point namespace, even if the Git diff does not mechanically conflict. Reserve a coordinator integration PR to connect accepted modules to existing browser files. Workers never independently merge, enable auto-merge or force-push.
