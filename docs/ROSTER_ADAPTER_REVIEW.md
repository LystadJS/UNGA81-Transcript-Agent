# Roster-bound collection and dependency-control review

**8 October 2026 — validation passed locally; repository publication pending.**
The remote source reviewed was `ab7273d37f8fcff9870f257084cc8fd1dcda7876`
(PR #9). No new GitHub commit or workflow execution is claimed. The current
session exposes read-only GitHub actions and has no working command-line GitHub
connection. The companion patch is checked against that exact base.

**All 37 reserved transcripts remain unopened.** Only the already-frozen metadata
roster was read to verify its digest. Development diagnostics use the unchanged
saved October 1–2 text within the declared October 1–4 window. Synthetic collection
uses generated 2099 dates and fictitious identifiers, not any reserved transcript.

## What is implemented and independently checked

The new `roster_adapter.cjs` binds 37 synthetic slots one-to-one to SHA256
commitments for the ordered frozen reserved ID/date roster. Only those commitments
leave the binding step; real URLs are never passed to a transport. The fixture
transport is in-memory, uses the `.invalid` domain, and has no HTTP client. It
cannot be mistaken for a validated live collection adapter.

Each available slot has a bounded two-attempt schedule. Retries retain the exact
endpoint; unavailable slots are not requested. An append-only receipt records all
slots, attempts, status codes, response hashes, final failures and the derived
corpus hash. Validated source bytes pass through the original corpus parser,
Unicode passage partitioner, machine-only review and frozen transformations.
The historical parser's UN-origin check requires a schema bridge for fictitious
IDs; those bridged links are never requested.

Independent oracles check exact endpoint sets, status arithmetic, raw JSON sentence
reconstruction and every Unicode passage span. Adversarial cases include missing,
duplicated or reordered slots; real dates/URLs; encoded traversal; changed roster
commitments; redirected or substituted replies; invalid response hashes; malformed
JSON content and timestamp fields; oversized or absent bodies; invalid retries;
reused transport state; and overridden transport callbacks. These checks are
independent calculations in this session, **not an external organizational review**.

## Executed synthetic acceptance

| Item | Actual result |
|---|---:|
| Synthetic roster | 37 slots |
| Successful / unavailable / failed simulated sources | 34 / 2 / 1 |
| Transport attempts, all in memory | 36 |
| Strict synthetic passages / source segments / meetings | 220 / 216 / 27 |
| Network attempts during guarded adapter/inference checks | 0 |
| Human approvals or model refits | 0 |
| Real reserved transcripts accessed | 0 |

Two full final-code runs used the actual pinned local MiniLM encoder and saved
lexical/semantic transforms and returned byte-identical receipts and diagnostic
results. Scikit-learn fitting entry points were patched to raise during inference.
The 64-dimensional lexical versus raw 384-dimensional semantic diagnostic is kept
separate from the older 64D/64D rehearsal.

The historical evaluator returns **INCONCLUSIVE_SYNTHETIC** because its conservative
coverage guard rejects collected meetings with no strict eligible rows. This is
not evidence that actual held-out coverage fails. The guard is stricter than the
listed numerical coverage minima; it remains visible rather than being silently
removed or mislabeled as part of a new scientific protocol. This patch leaves the
sealed evaluation and historical results unchanged.

## Stronger agenda and speaker-proxy diagnostics

Institutional series now distinguish individual GA committees, plenary proceedings
and the HRC session, rather than using genre alone. Asset events without a
supported series stay unknown. A series is only an **agenda proxy**, not an observed
agenda item. Complete affiliation-plus-function pairs are a separate coarse
**speaker proxy**, not a person identifier. Both fields must be recorded. Missing
values are never treated as equal identities or as evidence of different people.

| Retrieval restriction | Eligible queries | Overlap | Baseline on those same queries | Expected overlap from independent uniform eligible-neighbor selection |
|---|---:|---:|---:|---:|
| None beyond different meetings | 523 / 523 | 39.4% | 39.4% | 3.3% |
| Different institutional series | 507 / 523 | 37.4% | 39.6% | 7.1% |
| Different complete speaker proxy | 78 / 523 | 57.9% | 46.5% | 22.3% |
| Different series and complete proxy | 76 / 523 | 66.6% | 47.4% | 39.4% |
| No shared listed procedural phrase | 523 / 523 | 65.5% | 39.4% | 45.2% |
| At most two neighbors per meeting | 523 / 523 | 31.5% | 39.4% | Not computed |

The eligible pool changes with these restrictions. A higher overlap in a much
smaller candidate pool is not improved substantive validity. For example, excluding
shared procedural phrases yields 65.5% observed overlap but already implies 45.2%
overlap under independent uniform draws from the resulting pools. That comparison
is a descriptive geometric reference, **not a calibrated political null**.

Only **78 of 523** source segments contain both affiliation and function; **445**
lack at least one field. Only three complete proxy values recur across meetings,
and there are **zero recorded distinct speaker IDs**. The combined series/proxy
comparison covers only 76 segments. These analyses do not resolve same-person
recurrence in the full corpus, and affiliation alone is not promoted to identity.

Meeting-balanced summaries, same-query baselines and candidate-pool accounting
accompany every comparison. Five whole-series omission recalculations were also
executed without fitting. Removing the four HRC meetings leaves 185 parents across
12 meetings; its descriptive overlap is 52.1%, but it changes the retrieval
population and does not establish independent replication.

The procedural phrase diagnostic uses only three declared strings: “thank you,”
“on behalf of,” and “distinguished delegates.” It does not automatically classify
substantive phrases such as “human rights” or “technical assistance” as boilerplate.
No source text, country-mask version or prior machine decision was edited.

## Validation and preservation

**48 new checks passed:** 35 adapter tests and 13 dependency-control tests. The
complete reference Python suite passed 69 tests (including those 13). Also executed:
57 machine-review tests, all 47 semantic tests with the pinned model (no skips),
53 corpus-contract tests, and 15 additional numerical/source regression suites.
The two final dependency runs are byte-identical. Exact file and source hashes are
recorded in `ROSTER_ADAPTER_VALIDATION.json` and the delivered evidence manifest.

These are **local executions**. The new read-only GitHub Actions workflow is included
in the patch but has not run on GitHub. Its default job exercises synthetic
collection, parsing and machine eligibility, not private-model inference. The
receipt explicitly distinguishes an omitted encoder run from a passing encoder run.

The original evaluation lock, source roster, reference tests, model-fitting code,
`site/`, `un/`, existing human decisions and publication gates are untouched. No
model weights, fonts, real transcript text, row-level real vectors or real review
ledgers are added by the repository patch.

## Readiness and remaining scope

**Engineering:** passed within the offline fixture and development scope. This is
not a live HTTP transport, upstream availability check or authorization mechanism
for actual transcript access. Fake response hashes are known in advance; actual
future responses would need newly captured provenance under a separately authorized
collector. Full live-source readiness cannot be certified from these fixtures.

**Scientific:** no policy-alignment release. Real agenda-item labels and genuine
speaker identifiers remain missing, and no substantively justified political null
has been calibrated. The independent uniform-neighbor reference and institutional
proxies must not be presented as solving those limitations. The old numerical
threshold and original two-test family have not been retrospectively changed.

**Repository:** synchronization is the only unfinished delivery step. Apply the
version-checked patch in a write-enabled session, then run its GitHub CI and verify
the resulting commit before calling it deployed or merged. Do not repeat the batch
human-review request or open the 37 reserved sources to complete this step.

## Reproduction

From a checkout of the declared base with the supplied patch and the existing
pinned Python 3.13 / Node 22 requirements installed:

```sh
node research/reference_tests/test_roster_adapter.cjs
python -m unittest discover -s research/reference_tests -p 'test_*.py' -v
python research/reference_tests/roster_integration.py NEW_SYNTHETIC_RECEIPT.json \
  --checkpoint PATH_TO_UN_MACHINE_REVIEW_RESULTS \
  --semantic PATH_TO_SAVED_SEMANTIC_RESULTS \
  --model PATH_TO_PINNED_LOCAL_MINILM
python research/reference_tests/dependency_controls.py \
  PATH_TO_UN_MACHINE_REVIEW_RESULTS PATH_TO_SAVED_SEMANTIC_RESULTS NEW_CONTROLS.json
```

No command above collects real transcript sources. Output files cannot be
overwritten. The encoder artifacts are supplied by the existing pinned-model
workflow; they are not bundled with this patch.

Methodological reference: the official scikit-learn documentation distinguishes
[group-dependent evaluation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data)
from random row splits and warns against [fitting preprocessing on test inputs](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).
These general principles do not establish that the present proxies are adequate.
