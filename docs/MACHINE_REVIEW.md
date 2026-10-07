# Machine development review and lexical exploration

## Operating mode — owner instruction, 7 October 2026

The owner explicitly requested that ChatGPT conduct the development batch review
without waiting for their participation. Human review and adjudication are deferred.
Proceed with clearly provisional machine-reviewed exploration; do not manufacture
human approvals or replace the completed earlier pilot. This instruction supersedes
any roadmap wording that makes returned human choices a prerequisite for this
provisional research path. It does not authorize access to the 37 reserved meetings.

The implementation lives in `research/machine_review/`. It is separate from the
browser workspace, the frozen corpus contract and the daily publication pipeline.
It does not change `site/`, `un/`, the original source frame or the earlier owner
review decisions. Source-linked real results are delivered as conversation artifacts,
not published transcript or review data in this public repository.

## Completed batch

All **1,293 development source segments** received deterministic full-text triage,
followed by targeted contextual inspection and **13 source-hash-bound machine
overrides**. This is rule-assisted machine review, not an independent human reading
of every source or an audio check. No corrected transcript wording was invented.
Every annotation records the machine role, source identity, exact evidence spans,
reason, uncertainty flags and neighboring source identities. All 2,596 original
passage partitions are retained, including excluded observations.

| Proposed source type | Source segments |
|---|---:|
| Substantive-speech candidate | 552 |
| Procedure | 550 |
| Uncertain | 52 |
| Press question | 51 |
| Speech fragment | 47 |
| Mixed speech/procedure | 25 |
| Right of reply | 15 |
| Suspected transcription issue | 1 |
| **Total** | **1,293** |

Roles are separated from recorded country affiliations. A chair's country metadata
does not establish that their floor-management intervention is a national policy
statement. Unmapped affiliations can be organizations, officials or genuinely
unresolved speakers; they are not automatically missing countries.

The new `un.corpus-machine-review.v1` ledger is intentionally incompatible with the
human-confirmation schema. All rows have `actor_kind: machine`, `status: provisional`,
`human_confirmed: false`, `extent: unknown` and no verified speech ID. The original
human-review template remains pending, and complete-speech denominators remain
unavailable. A source's machine type is a proposal, not an adjudicated fact.

## Declared analysis populations

| Population | Eligible passages | Purpose |
|---|---:|---|
| Strict provisional | **1,641** | Substantive/reply candidates without presiding, press or possible-truncation flags |
| Inclusive provisional | **1,910** | Adds mixed, fragment and official-press material for selection sensitivity |
| Original audit baseline | **2,057** | Unchanged baseline eligibility for comparison |

The strict population represents **523 observed source segments in 16 meetings**.
These are not 523 independently verified complete speeches. Original exclusions
remain in force in all populations. No passage is silently sampled or deleted.
The full dataset exceeds the existing browser's 600-observation bound, so this
phase uses a separate offline sparse Python research runner with a declared
5,000-observation safety envelope. The browser limit is unchanged.

## Executed exploratory analysis

The saved plan precedes fitting. It uses development-only TF-IDF unigrams/bigrams,
retains explicit negation, and compares six fixed configurations: 32/64-dimensional
LSA; k-means with 6/10 clusters; Ward with 10 clusters; and strict/inclusive/baseline
populations. Clustering uses row-normalized retained geometry, not two-dimensional
display positions. All six fits completed. NMF with 8 and 12 components also
completed and converged. Its composition summaries adjust arbitrary component
scale before calculating component-mass shares.

All **16 leave-one-development-meeting-out refits** completed after independently
refitting the vocabulary, IDF, LSA and k-means on the remaining development meetings.
Their adjusted Rand indices compare overlapping training observations with the
primary fit: median **0.626**, range **0.582–0.792**. These are sensitivity checks,
not independent replication, held-out evaluation or significance tests.

Changing the strict LSA dimension from 32 to 64 with k=10 gives ARI **0.581**;
changing k-means to Ward in the strict 64-dimensional geometry gives **0.505**.
Common-ID comparisons with inclusive and original baseline fits give **0.580**
and **0.522**, respectively, and are explicitly marked as changed-population
comparisons. None of these numbers is a probability of diplomatic agreement.

The eight-component summaries recover recognizable agenda themes, including
technical assistance, decolonization, Iran/nuclear-oversight language, civilian
protection, social protection, the Marshall Islands nuclear legacy, racism and
human-rights institutions. These are analyst descriptors of source-linked language
components, not factual endorsement of statements in automatic transcripts.
Meeting/agenda composition strongly structures these results; settings materially
change the partitions. No diplomatic coalition or statistically nonrandom policy
alignment is established.

Composition exports compare equal-passage, equal-observed-parent and equal-meeting
summaries. Unfitted observations stay in denominators. Equal observed-parent weight
is not equal verified-speech weight; neither is a country-weighted model fit.

## Reproduce from the delivered local checkpoint

Use Python 3.13 and Node 22. Install `research/machine_review/requirements.txt`.
The original corpus validator re-derives text from saved response bytes before
machine review or analysis. No collection command is called.

```sh
python research/machine_review/review.py \
  /path/to/work/build/corpus.json /new/output/review \
  --overrides /path/to/contextual-overrides.json

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
python research/machine_review/analysis.py \
  /path/to/work/build/corpus.json /new/output/review/machine-review.json \
  /new/output/analysis

python -m unittest discover -s research/machine_review -p 'test_*.py' -v
```

The 13 contextual overrides are in the private delivery, not committed as public
review choices. Omitting `--overrides` produces a new deterministic rule-only run,
not an exact reproduction of the adjudication proposals delivered here. Output
directories must not already exist. Machine-ledger timestamps change on a new run;
compare source-bound choices and numerical values rather than timestamped file
hashes. Saved numeric arrays load with `numpy.load(..., allow_pickle=False)`.

## Validation and boundaries

57 new synthetic checks passed, including source binding, Unicode evidence,
machine-versus-human separation, prohibited holdout rows, weight denominators,
deterministic fitting and pickle-free exports. The unchanged 53 corpus checks
and 15 existing analytical/source suites passed in GitHub run **37698414562**.
All eight numeric archives reloaded without pickle. A second complete local run
reproduced every stored numeric array, fit diagnostic, assignment and component
output exactly in the same pinned runtime.

The executed notebook preserves five figures and exact source-linked examples.
Desktop/mobile in-memory rendering of the saved HTML was checked at 1440/390 px,
with no overflow, script errors or external requests. Direct local-file browser
navigation was blocked by the sandbox administrator and is not claimed as tested;
no security setting was changed. Notebook execution and in-memory rendering are
separate checks. Initial short-chair classification and object-array export defects
were corrected and covered by regression tests before final delivery.

**Holdout:** no reserved transcript was downloaded, read, fitted or scored. Existing
metadata reservations are unchanged. No semantic encoder, formal null-reference
test, country-stance classifier, verified complete-speech corpus or leadership
publication gate was added in this phase.

## Next phase

Add one pinned local semantic encoder and compare it with the saved lexical
reference on the **same provisional development passage identities**. Keep this
machine-only status visible in every export. Test paraphrase, negation, opposing
positions on the same issue and procedural contamination. Develop nuisance-aware
validation and a model-specific evaluation protocol before any reserved-text access.
Human adjudication may occur later; it is not a blocker for these provisional
engineering and exploratory comparisons.
