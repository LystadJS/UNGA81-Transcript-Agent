# U1: question-first briefing interface

**Synthetic implementation candidate. Not integrated, merged, deployed or independently accepted.**

U1 owns only `site/parallel/w07-diplomat-ux/**`, on `feat/parallel-w07-diplomat-ux`, stacked against `coord/c0-product-contracts`. Its immutable dependency is accepted C0 commit `884097997f89b0040e4418480378f077e3b65434`. `dependency-lock.json` pins all eight consumed/validated C0 files; none are copied into this subtree or changed.

## Ordinary workflows

- **Explore:** choose a country, topic or inclusive date range, then Create briefing. Dates and the US comparison baseline are explicit defaults, not silently altered filters.
- **Meetings:** search a name and select the dated/forum-specific meeting. Numeric-looking identifiers `01` and `1` remain distinct. Shared country/topic/date selections remain visible.
- **Saved briefings:** save and reopen the original result during the current session, with fresh access checks and no new resolve or fit. Saving is memory-only; closing/reloading the page clears saved items. Persistence is not implemented.

Outputs include a descriptive overview, complete fictional coverage counts, supporting evidence in a keyboard-oriented native dialog, country highlighting and clearly separated partial, empty, failed and unavailable states. No statistical inputs or algorithm selection appear. A missing source is not a zero finding. Collective affiliation is not national attribution. No policy stance is inferred.

Country highlighting changes the presentation only. There is no geometry or numerical trajectory component to refit in U1. The comparison and changes sections are explicitly unavailable placeholders, not invented coordinates or alternate baseline calculations.

## Synthetic preview

From a checkout of this branch, with Node 22.16.0 or a compatible runtime:

```sh
node site/parallel/w07-diplomat-ux/tests/fixture-host.mjs --port=8765
```

Open the loopback URL printed by the process. The host serves only six U1 assets and the two pinned C0 runtime modules. It binds to 127.0.0.1, refuses foreign Origin/Host, serves no directory listings or arbitrary repository files, uses no-store/CSP/nosniff headers, and accepts no transcript path, model or external URL. Stop it with Ctrl+C. This host is a **test harness**, not a deployable source or approval service; the browser also refuses non-loopback/non-HTTP use.

Invented examples are dated 23–25 September 2024. The 23 September meeting is complete; the 24 September meeting includes one unavailable example record; the 25 September meeting demonstrates a reader failure. Canada + Peace and dialogue on 23 September produces a genuine synthetic no-match. Dates outside the small catalog withhold instead of claiming empty real history. Source text is newly authored and prefixed “Invented example”; country labels do not describe empirical country positions.

The host constructs deterministic descriptive metadata wrappers, not fitted models or authoritative upstream source validation. C0's required attempt fields describe the fictional reader outcome. `model_runs=0`; no model is downloaded or run. Product worker/tree IDs are deliberately all-zero **fictional fixture fields**, labeled `fictional_fixture_not_a_commit_receipt`, never represented as actual executed Git identities. Actual source/test identities belong in the separate engineering receipt.

## Trust boundary and export

`controller.mjs` imports the accepted C0 implementations of `assess`, `exportReadModel`, strict parsing and validation. Incoming bundles have exactly four fields: query, capability, product, receipts. They cannot supply a keyring, expected receipt-set hash, clock, output destination or readiness flag. The current expected `trustedReceiptSetSha256` comes from the separately queried **trusted host ledger**, not from hashing incoming receipts. Only the fixture host constructs that ledger from its own invented cases. Its signing keys are ephemeral, stay in server process memory, are never sent to the browser and are not committed. Test-only signing is not operational source/reviewer approval.

The controller checks ledger identity and keyring both before and after asynchronous work. It clears displayed content, source details and exports when selections change, imports fail/cancel, context changes or a pending result becomes stale. The browser checks current trust every second while visible, on focus, before evidence access and before export. Hiding the page clears the active view. These are fail-closed consumers of a synthetic in-memory ledger, not a real revocation distribution system.

Exports call C0 afresh for `local_export`; stale `can_export` values are never used as authority. Exported visible sections must also match the currently permitted view. Only C0's filtered read model is serialized to JSON, never the unfiltered product, decision set, keys, evidence prose or hidden results. This first version does not offer HTML/PDF/PNG export or printing. Browser/OS capture cannot be made a security boundary by CSS.

Evidence is fetched only for a reference present in the freshly assessed view. The fixture host independently reassesses access, and the client verifies the returned source/meeting ID and SHA256 text digest before showing it with `textContent`. No imported HTML, executable hooks or arbitrary source URLs are rendered.

The ordinary workflow needs no file import. The expandable preview information contains a bounded synthetic-bundle inspection input for integration checks. Unknown, real, oversized, duplicate-key or self-authorizing bundles clear the previous result. Read-only exported JSON does not itself confer importable permissions.

## Modules

| File | Role |
|---|---|
| `index.html`, `styles.css`, `app.mjs` | Standalone question-first UI, responsive layout, native focus/dialog behavior and safe DOM construction |
| `controller.mjs` | C0-dependent orchestration, fresh trust checks, private in-memory saves, stale-work guards, safe exports/evidence |
| `provider.mjs` | Bounded same-origin synthetic-host transport; replace through separately accepted U2/C1 integration, not new tuning code |
| `copy.mjs` | Plain-language states, limitations and titles |
| `tests/fixtures.mjs`, `fixture-host.mjs` | Invented metadata/text and ephemeral test-only issuer; no operational PKI |
| `tests/test_controller.mjs` | Native functional, trust-boundary, race, source, import, HTTP and ownership-dependency controls |
| `tests/browser_qa.py` | Strict real HTTP Chromium interaction and responsive/replay/export suite, no injected-DOM fallback |
| `tests/guard_owned.py` | Full-checkout exact-head and path/mode guard for a coordinator runner |

## Reproduce native tests

```sh
node site/parallel/w07-diplomat-ux/tests/verify_dependencies.mjs
node --test site/parallel/w07-diplomat-ux/tests/test_controller.mjs
node --test research/integration/product_contracts/test_*.mjs
node research/integration/product_contracts/emit_contracts.mjs /tmp/u1-c0-emission
python research/integration/product_contracts/check_schemas.py /tmp/u1-c0-emission
```

Use a fresh emission directory. The C0 schema check uses the existing Python jsonschema dependency. Do not regenerate the accepted interface lock. Native controller tests do not establish rendered accessibility, browser WebCrypto support or served-browser acceptance.

## Required coordinator browser acceptance

U1 has no workflow ownership. No shared workflow or build allowlist is modified. In an execution-capable full checkout, check out the exact U1 head and independently compose/test its effective tree against the pinned C0 base. Keep any coordinator workflow in its separate namespace/PR. Run:

```sh
python site/parallel/w07-diplomat-ux/tests/guard_owned.py --head "$(git rev-parse HEAD)"
python -m pip install -r site/parallel/w07-diplomat-ux/tests/requirements-browser.txt
python -m playwright install --with-deps chromium
python site/parallel/w07-diplomat-ux/tests/browser_qa.py --output /tmp/u1-browser-qa
```

An existing Chromium can be passed with `--chromium /path/to/chromium`. Do not disable an administrator navigation restriction to make this pass. The script starts its own allowlisted fixture host with ephemeral test controls, navigates the actual page over HTTP, and requires application startup before executing 22 named cases. Failed navigation exits 2 and writes BLOCKED with `served_navigation_verified=false`; it never substitutes injected DOM or static screenshots. All candidate errors remain visible. Generated screenshots/exports belong outside the repository.

Manual visual inspection, screen-reader operation, contrast review, browser zoom and broader browser coverage still require assessment. Static labels/CSS and controller tests are not a WCAG conformance claim.

## Dependency reconciliation

The C0 handoff's historical PR82 defect snapshot is superseded by PR82 `81110db49786a05f9c8f8ce4d5103c92fe255586` / PR87 `dc8f98dec92cd34242f9ed7c6ce85814291ada38`, which record repaired mandatory-R engineering acceptance. PR92 `76fbfd73f440306dfd9fc72a6431704f7b09b45d` separately implements trajectory Phase 2 and records automated checks, with further review outstanding. U1 does not consume or approve those implementations: no trajectory display contract has been integrated into its C0 read model. Its placeholder remains unavailable for that reason, not because the old R defects are claimed to remain unresolved.

Merged PR71 remains the unchanged upstream security baseline. Real sources, source authenticity, operational key/ledger custody, empirical models, calibrated uncertainty and actual source/owner decisions are outside U1. G01–G13, temporal v2/v3 and holdout restrictions, original hashes, completed owner decisions, all 37 reserved meetings and D1 O1–O5 remain untouched. No merges, deployment, portfolio mirror, public-site wiring or delivery is performed.
