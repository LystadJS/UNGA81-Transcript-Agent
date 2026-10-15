# U2: metadata-only question router

Synthetic-only implementation candidate. No source reader, model fitting, operational issuer, public output, merge or deployment. U2 owns only `research/integration/question_router/**` and is stacked on C0 `884097997f89b0040e4418480378f077e3b65434`. Accepted U1 `afb92e82881dc11003170899aef9958682d61abe` is a separately supplied, read-only consumer dependency, not copied or merged into this branch.

## What it does

The ordinary input is U1's five-field selection: `{page, country, topic, meeting, period}`. All five fields are required; unselected values are null. Country and topic are canonical registry identifiers. `page` is `explore` or `meetings`; a meetings selection requires an exact meeting ID. Statistical settings and additional fields are rejected.

Country/topic lookup supports explicit registered wording aliases. Meeting-name search returns a date/forum-disambiguated list; resolving an ambiguous name fails rather than choosing the first match. IDs remain strings, including `01`, `1`, `1e5`, `NA`, and 160-character identifiers. Nothing is inferred from a country mention in source language.

Dates are inclusive New York calendar dates. UTC timestamp conversion is explicit; DST does not change the number of selected calendar days. Absent dates use the selected meeting's actual catalog date or the recorded catalog default. Requested dates are never clipped. Unknown dates stay unknown. Gaps between inventory periods, protected metadata, the reserved October 5–6 2026 range and simulated live ranges over 31 days produce explicit unavailability before any bundle lookup. Saved/historical simulation does not authorize real history.

The router produces the existing closed `un.research-query.v1` and evaluates existing `un.product-capability.v1` / `un.evidence-product.v1` inputs using unchanged C0. It selects stored products by exact query and capability hashes, in the predeclared capability/fallback order. It does not search parameters, rank attractive displays, train a model, sign a result, fetch a transcript or invent missing coordinates. No qualifying stored product is a normal unavailable outcome.

## API

```js
import {createRouter, createU1Provider} from './router.mjs';
const router = await createRouter({
  metadata,                         // closed, synthetic metadata snapshot
  expectedMetadataSha256,            // independent trusted host configuration pin
  getBundle: storedProductLookup,    // async ({query_sha256, capability_sha256}) => bundle | null
  getTrust: currentDecisionLedger    // async productHash => {keys, commitment, revision, now}
});
const plan = await router.plan({page:'explore',country:'BRA',topic:null,meeting:null,period:null});
const routed = await router.route({page:'explore',country:'BRA',topic:null,meeting:null,period:null});
// routed contains an explicit state, plan, complete routing trace, and a C0-checked bundle/readiness when available.
const provider = createU1Provider(router); // consumed by U1's unchanged createController
```

`routeQuery(query)` also accepts a fully formed canonical C0 query, including multiple countries or an explicitly selected non-US baseline. `planQuery(query)` preflights it without reading products. `country`, `topic`, `meetings`, and `meeting` perform metadata resolution. `catalog()` returns a defensive copy. `invalidate()` cancels pending routes and clears admitted product identities; recreate the router after a metadata/policy update. Plans and route receipts carry `authority: none`, not permission to publish or display an unchecked result.

The metadata input has exactly six fields: `schema: un.question-router-metadata.v1`, `fixture_kind: synthetic`, `catalog`, `inventory`, `bindings`, `policies`. `metadata.mjs` is the executable closed-shape and relational definition. It does not introduce a replacement source-inventory schema. The tests' `fixtureMetadata()` supplies a complete source-free example.

`catalog` contains only a version, New York timezone, simulated collection kind, country/topic names and aliases, meeting names/dates/forums/protected markers, and the explicit default period. Each metadata binding joins one original inventory observation to its country capacity, topic classification/completeness, language, and exact parent/span. Policies contain C0 capability objects and one nullable entrypoint per C0 intent. Every fallback reference, including unreachable chains, is checked for cycles and the 16-hop bound before use.

## Source and population invariants

The original `docs/parallel-work/source-inventory-v1.cjs` validator and schema execute directly. Original row-key order is preserved because its inventory hash is SHA-256 of `JSON.stringify(observations)`, not C0 canonical JSON. U2 never replaces this hash with its own. Non-synthetic splits/bases, an unvalidated legacy binding, duplicate parents, missing metadata joins, contradictory meeting dates and mismatched source counts are rejected. A one-period or wholly empty sidecar still fails the existing upstream schema; U2 does not weaken that requirement to manufacture an empty result.

The fit population is fixed by date, meeting and topic, not the country highlight/filter. Frame accounting includes every in-scope row: eligible + excluded + missing + unverified. Topic uncertainty and unverified sources remain distinct from known exclusions. Missing rows are not removed just because their unknown country/topic would be inconvenient. `source_states` preserves the original inventory's source-only denominators alongside the derived eligibility counts.

Country filters select the display subset only. Recorded affiliations and collective statements are not promoted to national capacity. Unknown national attribution withholds a country query rather than claiming no matches. Source-available metadata for other countries can remain in the fixed fit population; the count in `fit_population` is therefore the reference cohort, not the selected country's speech count. `display_population.count` is the selected display count. The plan records the distinction explicitly; highlighting inside U1 never calls the router or refits anything.

Derived fit identity is C0 `digest({schema:'u2.fit-population.v2', source, parent_selection, inventory, period, meeting, topic, classification, unit_basis})`. The sorted `unit_basis` binds each eligible observation's exact parent ID, start/end offsets, parent length and language. Changing a fitted source unit invalidates stored fits; country display selections and navigation aliases do not. Prior v1 fit identities must not be reused or silently migrated. The original source selection hash is retained separately as `parent_selection_sha256`. Display/selection identity is `digest({schema:'u2.display-population.v1',parent:fitHash,countries,ids})`. Neither overwrites the original inventory/source hash. A stored product must match these exact identities, complete counts, declared weighting/dependence, query/recipe and every displayed evidence source/hash/capacity/span. Mixed-language or mixed-genre cohorts are explicitly unsupported by this single-summary adapter; they are not silently pooled.

All failed and skipped attempts from examined products remain in the routing trace even when a separately approved descriptive fallback succeeds. An empty result requires no selected display records; missing/unverified/failed accounting is still assessed by C0 and cannot be hidden as a complete zero.

## Trust boundary

`expectedMetadataSha256` is a separately configured host snapshot pin, not proof of UN provenance. It must not be accepted from an uploaded metadata bundle. Similarly, `getTrust` must provide the current out-of-band keyring and **complete** decision-set commitment. Production router code never calls `receiptSetDigest` to authorize incoming approvals and contains no signer. Test code alone creates ephemeral in-memory keys and a fictional ledger.

C0 verifies every signature, full-set commitment, source/product/query/capability/worker/tree/destination binding and expiry. U2 checks host trust identity again after verification and rejects intervening key/ledger changes. Unknown imported product hashes receive no keys. Source, review, engineering or output rejection is terminal; the router cannot seek another product to bypass those decisions. A methodology-specific hold may fall back only to a separately checked descriptive product. A valid optional section can remain available under C0's per-section rules.

The router snapshots untrusted inputs before asynchronous work, rejects executable objects through C0's data boundary, limits collections/import size, and suppresses raw exception messages and rejected products. Cancellation or a newer request prevents older completion from restoring a result. It does not sandbox malicious JavaScript already executing in the trusted host.

## U1 integration boundary

The provider adapter returns U1's existing catalog and four-field bundle shapes. Native interoperability tests execute the **exact accepted U1 controller**, covering country/topic/meeting products, partial/empty states, saves, fresh filtered exports, revoked keys, omitted vetoes and expiry. This is controller interoperability, not a new served-browser acceptance run or shared-site integration.

Two limitations remain explicit. First, U2 is metadata-only: `getEvidence` refuses with `evidence_service_not_connected`. Source prose delivery belongs to a separately authorized evidence service. Second, when no stored bundle exists, U2 returns a structured `unavailable` route, but U1's existing `resolve` exception path displays a generic `failed / could_not_create`. The adapter does not fabricate a signed status product to conceal this contract gap. C1/U1 must separately map those no-product route reasons into user-facing unavailability. Both behaviors are regression-tested, not silently claimed complete. No U1-owned file is patched by U2.

## Reproduce

Run from the U2 checkout with Node 22.16.0 and the existing C0 Python jsonschema dependency:

```sh
node research/integration/question_router/tests/verify_dependencies.mjs
node --test research/integration/question_router/tests/test_router.mjs
node --test research/integration/product_contracts/test_*.mjs
node research/integration/product_contracts/emit_contracts.mjs /tmp/u2-c0-emission
python research/integration/product_contracts/check_schemas.py /tmp/u2-c0-emission
node research/integration/question_router/demo.mjs > /tmp/u2-demo-a.json
node research/integration/question_router/demo.mjs > /tmp/u2-demo-b.json
cmp /tmp/u2-demo-a.json /tmp/u2-demo-b.json
```

The nine-case demo emits only fictional query/count/routing summaries, not signed bundles, keys or source prose. No method runs. Use fresh emission directories; never regenerate C0's accepted interface lock.

For consumer tests, set `U1_CHECKOUT` to a separate checkout at `afb92e82881dc11003170899aef9958682d61abe`:

```sh
U1_CHECKOUT=/path/to/accepted-u1 node research/integration/question_router/tests/verify_dependencies.mjs --with-u1
U1_CHECKOUT=/path/to/accepted-u1 node --test research/integration/question_router/tests/test_u1_integration.mjs
```

Missing or wrong U1 bytes fail, not skip. The lock pins ten C0/inventory files and the unchanged accepted U1 controller. A full-checkout coordinator should also run `tests/guard_owned.py --head <exact-U2-SHA>` and native effective-tree integration, then assess U2 source/consumer/browser wiring in its own namespace. U2 has no workflow ownership. See `ACCEPTANCE.md` and `COORDINATOR_HANDOFF.md` for executed evidence and remaining scope.

All original source hashes, 37 unopened reserved transcripts, completed human decisions, G01–G13/null rules, temporal v2 failures/v3 holdout and D1 O1–O5 remain controlling. No empirical model choice, calibrated inference, operational key service, public-build privacy certification, merge, deployment, mirror or email is authorized.

## Independent-review repairs

Coordinator PR101 retains the original independent failure cases outside worker ownership. The repair candidate changes only U2 metadata preflight, derived fitted-unit identity and stored-product admission; all original tests, C0/U1 source and source-inventory hashes remain untouched.

- R1: in-scope catalog meetings without inventory rows cannot disappear. Protected or unknown-date catalog entries withhold first; a known meeting without any inventory row returns `meeting_inventory_missing`, not a zero-record result. Out-of-period meetings and unrelated explicitly unselected meetings do not widen scope.
- R2: the v2 derived fit hash commits to the exact fitted unit definitions. This is a change to U2's own derived identity algorithm, not the original inventory/source hash convention or a C0 schema change. Recreate stored products under separately authorized test-host decisions; do not rewrite previous receipts.
- R3: a non-descriptive section cannot expose findings/results/displays when its fit ledger has zero successful attempts. The complete failed/skipped ledger is retained; an inconsistent payload is refused rather than passed to another recipe. Source-only descriptive sections can remain available when justified by their separate decisions.

The source-matched independent local suite has 33 cases: original candidate 21 passed/12 failed; repair 33 passed. Those are 12 failed cases across three defects, not 12 separate vulnerabilities. Exact-head/effective-tree hosted results and the final engineering disposition are recorded externally on PR99/PR101 so that acceptance does not change tested bytes. All real-source, model-quality, human-review and release restrictions remain in place. The documented U1 no-product presentation gap and disconnected evidence service remain outside U2 ownership.
