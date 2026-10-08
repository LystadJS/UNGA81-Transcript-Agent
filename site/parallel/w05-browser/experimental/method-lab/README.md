# W5 — Experimental Browser Research Method Lab

**Status: isolated, development-only prototype; no public release.**

The coordinator reserves `site/parallel/w05-browser/**` for W5 in `docs/parallel-work/OWNERSHIP.md`. This lab is at `site/parallel/w05-browser/experimental/method-lab/` rather than the conflicting requested top-level `site/experimental/method-lab/`. Active site loaders, D1 gates, held-out transcripts, release manifests and the website mirror are untouched.

## Architecture

| File | Function |
| --- | --- |
| `contracts.js` | Strict v1.0.0 interchange and relational validation, full model–observation accounting, source/selection hash comparison |
| `adapters.js` | Validated interchange and legacy latent-run read models; SHA-256 checked export/replay |
| `worker.js`, `task-controller.js` | Cancellable same-origin Web Worker, progress, metadata/resources, replay and current numerical kernels |
| `index.html`, `method-lab.js`, `method-lab.css` | Standalone responsive source-linked inspection and side-by-side comparison |
| `fixtures/synthetic-contract.json` | Three model outputs, four eligible records, one explicitly missing source; no transcripts |
| `test-method-lab.cjs`, `test-browser.cjs` | Synthetic contracts, legacy/current saved runs, failures/cancellation, Node/Chromium numeric parity and device smoke |

## Use

From the repository root, serve the existing site directory over localhost or HTTPS:

~~~sh
python3 -m http.server 8000 --directory site
# http://localhost:8000/parallel/w05-browser/experimental/method-lab/
~~~

**Open synthetic fixture** for an immediate text-free read-only example. To import validated results, select a `un.parallel-analysis.v1` envelope or `un.method-lab-saved-run.v1` archive. Source-checked `un.latent-saved-run.v1` archives are replayed by the existing `UNLatent.restore` after explicit development-data authorization. To compute, import a local `un.browser.corpus.v1` or reviewed bundle, a validated `un.latent-plan.v1` plan, and authorize development/synthetic material. The original `UNLatent.run` pipeline supplies PCA/LSA score representations, clustering and NMF.

**Limits remain unchanged:** 40 MiB input, 600 retained observations and 128 MiB archives. No automatic sampling, refits on import or model promotion. Missing sources, excluded and unassigned results, fit attempts, status denominators and uncertainties remain explicit. GMM responsibilities, NMF shares, HDBSCAN strengths and consensus pair frequencies are not political probabilities. Paired comparisons require identical source hashes *and hash bases*, selection, unit, split and observation identities; cross-representation numerical comparisons are withheld absent an approved protocol.

Import-only/experimental: W1–W4 source checks, consensus, graph and longitudinal outputs. Optional local MiniLM is **feasibility-only**, with no model weights or inference installed. There are no third-party API calls or unexpected text transmissions. All automatic requests are same-origin under the restrictive page CSP. An HTTPS original-source link opens only on user click. **Legacy saved-run exports include original user-supplied text and must remain private**; metadata-only interchange exports do not.

## Tests

~~~sh
node site/parallel/w05-browser/experimental/method-lab/test-method-lab.cjs
BROWSER_BIN=chromium node site/parallel/w05-browser/experimental/method-lab/test-browser.cjs
~~~

The optional Chromium test requires Node 22+, local Chromium, and no npm or external network. It tests 1440px and 390px viewports, source inspection, stale-export invalidation, and retained PCA/LSA score parity with Node. See `ACCEPTANCE.md` for executed versus pending evidence. Coordinator review, upstream W1–W4 method acceptance, browser/device measurements and separate shared-entry-point integration are required before merge.
