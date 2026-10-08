# Conditional development references and frozen temporal-evaluation contract

**Status:** development-only reference calculations executed; future evaluation **specified but not run**.  No content from any of the 37 reserved meetings (5–6 October 2026) was downloaded, viewed, tokenized, embedded, fit, scored or used to set model thresholds.  Human adjudication is deferred.  These results are **not evidence of statistically nonrandom diplomatic coalitions**.

## Frozen question and observation

The model and population are the October development checkpoint already fitted before this phase: 2,057 source-audit eligible passages; 1,641 in the strict machine-only population.  The comparison uses **523 observed source segments across 16 meetings**, aggregating each source segment's eligible technical passages with declared passage-token weights into one L2-normalized 64-dimensional saved lexical LSA vector and one L2-normalized 384-dimensional saved MiniLM vector.  One observed segment is *not* necessarily one independently verified speech.  No model is retrained on shuffled or reserved inputs.

The initial fitting already inspected development text; this is an **internal diagnostic reference**, not an independent pre-registration or an untouched external test.  The two target statistics and the following conditions were declared before running the conditional draws in `research/reference_tests/plan.json`.

### Null A — paired representation retrieval

The statistic is the **mean fraction of shared 15 nearest neighbors**, excluding the query's entire meeting in both lexical and semantic high-dimensional spaces.  Null reassignment shuffles **whole source-segment semantic vectors**, never individual passage children, only among units **in the same meeting and frozen parent-length tercile** (`<=197`, `198–365`, `>365` tokens).  Lexical observations, both representation geometries and neighbor graphs, meeting/date/genre distribution, length-bin distribution, per-segment passage grouping, observed language, and source identities are unchanged.  This tests whether the *lexical/semantic correspondence for the same source segment* exceeds that expected after such conditional re-pairing, **not** whether either clustering is nonrandom.  An additional nuisance sensitivity restricts swaps by recorded actor-role class; it is descriptive and not a third hypothesis test.

### Null B — recurrence of recorded country labels

The statistic is the fraction of 15 cross-meeting raw-semantic nearest neighbors with the same **recorded country** among 319 known-attribution source segments from 86 countries each represented in two or more development meetings.  Labels are permuted within meeting × fixed length bin, leaving missing-attribution units outside the test.  The semantic vectors and neighborhood graph are fixed.  This tests *recorded country-label recurrence*, not policy agreement.  Country names within a transcript, diplomatic formulas, unreviewed attribution and repeated speakers can generate this result even without a shared political position.

For each null, use 999 seeded conditionally blocked permutations and right-tail Monte Carlo p = `(1 + #reference statistics >= observed) / 1000`.  Apply Holm correction to the **two** declared tests.  Report all failures and assessable denominators.  Within-block exchangeability is a working assumption; it cannot be verified from these observational sources.  Source/genre imbalance, speech dependence, latent agenda, lexical self-references and selection on prior fit results remain important.  A random row-order permutation does not test document structure, and these tests do not claim to do so.

## Executed development results

| Frozen diagnostic | Observed | Null mean | Null 95th percentile | Holm p | What it supports |
|---|---:|---:|---:|---:|---|
| Shared cross-meeting lexical/semantic neighbors | 0.3940 | 0.1122 | 0.1219 | 0.002 | Same-document paired representations recover related high-dimensional retrieval structure beyond the meeting/length shuffle |
| Same recorded country among semantic neighbors | 0.0911 | 0.0158 | 0.0190 | 0.002 | Country metadata is associated with semantic proximity conditional on the tested nuisance blocks |

The richer role-conditioned reference for the first test has mean **0.1200**, and its 95th percentile is **0.1304**.  Both tests can distinguish their observed conditional associations from these synthetic reassignments, **but cannot distinguish substantively meaningful diplomatic relationships from source labels, entity names, unmeasured agenda structure, or common transcription style**.  Their p-values are conditional/exploratory, not calibrated against all settings previously searched.  There is no global topic/cluster-null test, causal inference, stance model, or held-out validation in this release.

Source accounting: all **523** parent segments are represented, with 516 exchangeable under meeting/length blocking and 502 exchangeable when also blocking by actor role.  The recorded-country test has **319** eligible parents, **86** repeated countries and 310 exchangeable units.  Reversing the **13 prior machine contextual suggestions** leaves strict membership identical (0 changed strict passages); **16** inclusive memberships differ.  All 37 holdout records remain metadata-only.

## Frozen next-stage evaluation, not authorization to execute it

`evaluation_plan.json` and the committed SHA256-sealed `research/reference_tests/evaluation-lock.json` freeze the evaluation before reserved text is exposed.  They bind: original corpus/frame; SHA256 of the reserved **metadata ID/date roster** (not transcript content); model/tokenizer revision; saved full-fitted lexical LSA transform/vocabulary/IDF and semantic PCA transform; k-means centroids/labels (semantic) and recoverable lexical centers; machine-only inclusion rules; conditional Monte Carlo family; source-dependent group logic; all denominators, failure conditions, and the one allowed primary evaluation.  New-source transcript analysis is **not** implemented or run as part of this stage.

The locked primary future measure is the cross-meeting parent-level lexical/semantic neighbor overlap **minus its holdout conditional null mean**, under the same 15-neighbor blocked-reference procedure, after applying the frozen text transforms without refitting.  A replication check requires:

- At least **200** eligible source parents, **8** represented meetings, **15** other-meeting neighbors per query, and **70%** exchangeable parents in declared strata.  Otherwise mark **not assessable**, not zero.
- One predeclared primary evaluation, two-test Holm familywise alpha **0.05**, a positive excess, and excess at least **half the development reference excess**.  The sealed numerical floor is **0.14090298**.  This threshold is a predeclared *heuristic*, not independently calibrated predictive accuracy.
- Separate descriptive counts for *every* reserved meeting including unavailable transcripts and retrieval errors, genre, role, language, lengths, country missingness, duplicate/text-hash overlap with development, source failures and abstention/novelty rates.  Never silently change the source roster, reuse training rows or substitute meetings.
- No hyperparameter selection, vocabulary/IDF recalibration, encoder fine-tuning, centroid fitting, threshold search or inference from 2-D display coordinates.  If the criteria fail, report **inconclusive/not replicated**; do not reoptimize on the holdout.

The prior 13 contextual development overrides are source-specific and **are not carried into new-source machine classifications**.  The strict development cohort was unaffected, but any future eligibility/composition differences must still be reported.  Whole meetings and dates are separated; recurring speakers, source series, boilerplate and foundation-model pretraining mean statistical independence is **not established**.  An external assessor must review attribution and examples before a policymaker-facing substantive interpretation.

**Critical release gate:** The sealed evaluation protocol is **not authorization to open the reserved corpus**.  Only separate owner authorization permits a new evaluator to collect the 37 previously reserved meeting transcripts under the frozen roster.  This phase explicitly never invokes the UN collection API, reads holdout transcript content, or estimates holdout performance.

## Reproduce from conversation checkpoint

Use Python 3.13, Node 22 and the pinned semantic comparison requirements.  From the project root with the matching original development checkpoint and semantic-result directory:

```sh
python -m unittest discover -s research/reference_tests -p test_reference.py -v
OPENBLAS_NUM_THREADS=1 python research/reference_tests/reference.py \
  <checkpoint>/UN_machine_review_results <semantic-results> <new-empty-output-dir>
```

Outputs: `reference.json` (also committed as text-free `research/reference_tests/development-reference.json`; hash-sealed aggregate diagnostics and limitations); `reference-draws.npz` (numeric Monte Carlo draws, loaded with `allow_pickle=False`); `evaluation-lock.json` (sealed, metadata-only future protocol); and `plans.json` (immutable study settings).  This implementation has no network client and runs under an explicit socket-blocking context.  Checksums, full source provenance, and output hashes are included in the accompanying conversation checkpoint, **not** committed as real source records to this public repository.  No production `site/` or `un/` code, prior human decisions, original transcripts, or release gates changed.
