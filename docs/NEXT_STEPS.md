# Unsupervised diplomatic discovery — roadmap, 7 October 2026

**North star:** discover recurring, non-obvious structure in diplomatic language;
measure its sensitivity to reasonable analytical choices; inspect the underlying
evidence; and eventually track comparable actors and themes over time. A larger
method menu is not the objective. Neither attractive maps nor stable clusters
establish political alignment, coordination, influence, or statistical nonrandomness.

## A. Comparison foundation — implemented in this phase

The [comparison workspace](LATENT_COMPARISON.md), `site/latent.html`, adds:

- Source-bound saved runs containing original input bytes, review material,
  settings, output JSON, module hashes and stored coordinates. Reopening restores
  the stored numerical output without a refit; current rendering may differ from
  a historical renderer. Two saved runs can be compared explicitly.
- Full-parent versus reviewed-excerpt analysis with the same selected parent
  cohort, original offsets, partial-text coverage, duplicate exclusions, and
  separate counts. Each model keeps its original fitting weights. Equal-parent
  composition is an additional summary, not a weighted model fit.
- Reusable bounded plans for PCA/LSA, k-means, PAM, Ward/average, HDBSCAN, Gaussian
  mixtures and NMF; dimension/count/density/covariance/display alternatives;
  shared group-refit settings; source-linked maps and diagnostic exports.
- Explicitly withheld comparisons when units, source identities/hashes, usable
  populations or required fitted groups differ. Noise remains visible. NMF
  components and hard partitions are not interchangeable quantities. There is
  no composite best-method score or new publication producer.

Version 1.1 completes separate saved-run A/B coverage charts, hard and overlapping
component weighting summaries, dedicated CSVs and complete-cohort replay checks.
The actual twelve-excerpt pilot now passes archive and browser acceptance;
three-parent fits remain withheld. This is engineering acceptance, not evidence
of a representative corpus or a substantive diplomatic finding. See the
[validation record](comparison-refinement-validation.json) and
[prioritized implementation sequence](DISCOVERY_PRIORITIES.md).

Acceptance is also recorded by `Latent comparison acceptance` in GitHub Actions,
including existing numerical/provenance regressions and synthetic browser checks.
The implementation guide separates private-pilot, synthetic and deployed checks.

The earlier reviewed-unit import and separate correction ledger remain intact.
All 24 owner decisions in the audio/boundary pilot are complete: twelve included
excerpts from three speeches; six supported audio outcomes, five discrepancy
notes and one unclear outcome. Do not request that completed review again. Exact
replacement-span editing and aligned corrected-text versions remain separate work.

## B. Improve the observation — provisional machine review completed; human adjudication deferred

**Implementation:** [expanded corpus and weighting contract](PASSAGE_CORPUS.md) now freezes 21 development meetings (1–4 October 2026) and 37 reserved comparison meetings (5–6 October), preserves complete source-segment partitions and original bytes, and supplies explicit descriptive weights. Speech/country weights remain withheld until new-source boundaries and attribution support them. The reserved text has not been collected or evaluated; this is not yet independent replication. Existing weighted model fitting remains disabled.

**Owner-directed machine path:** [the automated batch and lexical exploration](MACHINE_REVIEW.md) now covers all 1,293 development source segments, retaining all 2,596 passage partitions. The strict provisional population contains 1,641 passages from 523 observed parents in 16 meetings. Six clustering fits, two NMF decompositions and 16 leave-one-development-meeting-out refits completed. Machine proposals remain separate from human confirmations; human adjudication is deferred and must not block further provisional engineering or exploration. The 37 reserved transcripts remain unopened.

Expand beyond purposive windows to a declared sample of complete or near-complete
speech partitions, preserving meeting → speech → passage lineage. Select sources
across dates, genres and recorded affiliations without selecting only examples
that support an attractive clustering. Preserve procedural and uncertain records
in the source layer; make analytical exclusions explicit.

Freeze the unit-selection and weighting policy before substantive comparison:
passage-weighted summaries answer a different question from equal-speech or
equal-country summaries. Add parent/country-weighted fitting only with a defined
objective and method-specific validation. Keep whole parents together; evaluate
meeting and affiliation dependence separately rather than calling either grouping
independent by assumption. Distinguish missing transcription from issue absence.

**Acceptance:** complete lineage and exclusion accounting; recoverable original
text; reviewed boundary decisions; documented selection/coverage; more distinct
source groups; inspection of protocol, length, transcription and genre effects.
The existing three-speech pilot remains an engineering example. Its full-parent
clustering is correctly withheld by the current four-observation minimum.

## C. Semantic representation — first pinned comparison implemented

See [SEMANTIC_COMPARISON.md](SEMANTIC_COMPARISON.md) for executed coverage, paired comparisons and limitations. The remaining criteria below govern later promotion, not an unimplemented encoder.

Retain TF-IDF → PCA/LSA permanently as the transparent lexical baseline. Add one
locally executed, version-pinned sentence/document encoder, with license and
checkpoint hashes, explicit passage-length handling, cached vectors and resource
limits. The existing small BERT relevance classifier is not automatically an
appropriate semantic embedding model. Do not silently truncate long passages.

Compare exactly the same passage identities under lexical and semantic geometry,
with separately recorded transformation and fit references. Benchmark sensitivity
to paraphrase, negation, shared protocol and different positions on the same issue.
A semantic neighbor is not a policy ally. Multilingual comparison requires its
own language/interpretation and translation comparability assessment.

**Acceptance:** reproducible inference and reloaded vectors; no text leaves the
approved execution environment; no leakage from future observations; source-linked
contrast cases; representation/neighborhood and clustering comparisons that do
not select a winner from appearance alone.

## D. Separate robust structure from a claim of nonrandom structure

The current comparison phase measures sensitivity. It does not supply a formal
null test. PCA and LSA are related transformations of the same lexical data;
agreement between them is not independent semantic corroboration.

Before using the phrase “nonrandom signal,” define a specific null hypothesis and
an exchangeability/dependence contract. Design reference corpora or simulations
that preserve the nuisance structure relevant to that hypothesis, such as source
groups, genre, passage length and token prevalence. Permuting row order alone does
not test whether a text matrix has latent clusters. Use held-out source groups or
periods to evaluate findings selected during development, and account for the
settings searched. Calibrate any proposed release threshold independently.

Build an ensemble association matrix only after this contract is frozen. Avoid
letting many near-identical settings or display-only UMAP variants receive extra
votes. Preserve method-family weights, eligible-pair denominators, unassigned
coverage and failures. Do not interpret a consensus fraction as the probability
of diplomatic agreement. One-to-one correspondence is inappropriate for genuine
splits/merges; retain those explicitly.

**Acceptance:** nuisance-only and known-structure fixtures; a declared independent
holdout; failed-fit accounting; balanced ensemble weighting; distinguishable
stability, external replication and null-calibrated evidence.

## E. Connect themes, actors and time

Begin with actor × latent-component profiles and source examples, then assemble
comparable country/genre/language observations across reporting periods. Freeze a
reference transform for genuine out-of-sample movement; separately evaluate full
refits and their alignment. Changes in corpus composition, vocabulary or missing
sources must not masquerade as a country's movement.

Integrate existing M22 within-country distance, M25 Procrustes and M27 cluster
correspondence as separate audit-only adapters once their inputs exist. Track
arrivals/departures and splits/merges. Estimate uncertainty in the retained
high-dimensional space before presenting two-dimensional arrows. M26/driftmapR
still requires verified source, interface and supported-regime evidence; it does
not block this phase. M24 change points and dynamic mixtures follow a defined
historical observation contract, not merely a larger number of snapshots.

**Acceptance:** held-out-period evaluation; common-source comparisons; separated
roster/composition effects; stable alignment anchors; movement distinguishable
from estimation and display variation; source-backed actor/theme interpretation.

## F. Produce decision-facing evidence, then integrate delivery

Organize outputs around questions: emerging themes, discourse communities,
boundary actors, changing actor profiles, and source-backed anomalies. Every
candidate finding should show its comparison population, sensitivity, missing
coverage, representative and contrary passages, and a reviewer interpretation.
Do not infer a bridge actor merely from an unstable assignment or a UMAP location.
Stance requires an explicit proposition and stance-specific evidence.

Promote accepted components into the daily pipeline one at a time. Browser
features, research kernels and daily adapters remain separate: D1 has twelve
executable adapters; the separate research layer has 29 engineering kernels.
No work in this phase changes those counts or O1–O5 publication gates. Relevant
Shiny, Outlook, replay and source-failure checks must accompany delivery changes.

Spectral clustering can later reuse the D1 implementation under an explicit graph
construction contract. Diffusion maps follow a kernel/normalization sensitivity
study; geometric diffusion is not evidence of diplomatic influence. Add a hosted
worker only after measured workload requirements exceed the browser envelope.

## Separate supervised and causal branches

The AI relevance pilot retains its [development/fresh-test sequence](NEXT_REVIEW_ROUND.md).
Source/boundary review supplies no relevance or stance labels. Classification,
forecasting, event-risk and causal diffusion models retain their own training,
evaluation and data prerequisites. They are not prerequisites for transparent
unsupervised source exploration, and their current safeguards are not bypassed.

**Boundary-review packet:** [the source-linked development packet](BOUNDARY_REVIEW.md) remains available for later human adjudication. Its original pending decisions and the previously completed owner pilot are unchanged. Machine review is stored in a separate schema and does not complete that human packet.

**Completed follow-on:** the pinned local semantic-embedding comparison now uses the same provisional development identities, retaining strict/inclusive selection sensitivity and machine-only status. See the executed record below. Internal split/correction cases stay unresolved rather than being promoted to complete speeches. Do not wait for human adjudication to continue this provisional path. Keep all 37 reserved temporal transcripts unopened until separately authorized under a frozen model-specific evaluation protocol. Establish null-reference and held-out-source validation before promoting discovered groups as nonrandom diplomatic structure.


## Pinned semantic comparison completed

[The local semantic comparison](SEMANTIC_COMPARISON.md) is implemented on the unchanged provisional populations. Six fits and 16 development-meeting omission refits completed, with full token coverage and source-bound caches. Lexical/semantic agreement is partial; authored opposition probes and poor 2-D fidelity prohibit stance or coalition claims. Human adjudication remains deferred and does not block this provisional research path.

**Current next step:** implement nuisance-preserving development reference tests and pre-register a model-specific evaluation protocol. Keep all 37 reserved meetings unopened until separately authorized. Do not add more encoders or promote consensus percentages as diplomatic agreement before these checks.


## Development nuisance references and frozen held-out protocol — 8 October 2026

The [executed conditional-reference assessment](NUISANCE_REFERENCE.md) adds parent-level blocked tests of (1) cross-meeting lexical/semantic neighbor agreement and (2) recorded-country semantic recurrence. Both exceed meeting/length shuffled development references but **do not establish** statistically nonrandom diplomatic coalitions, shared policy positions or independent reproducibility. Recorded country names and meeting agendas are potential confounds. The preserved 37-meeting temporal comparison remains **metadata-only and unopened**. A SHA256-sealed evaluation lock fixes future transforms, eligibility, source coverage, metrics, failure accounting, alpha adjustment and a one-shot replication heuristic, without implementing or authorizing holdout acquisition.

**Next recommended phase:** build synthetic nuisance-only and known-structure controls for the declared reference questions, audit the sensitivity to recorded country names and genre, and prepare a separately authorized, fail-closed held-out evaluator. Do not open reserved content until the owner explicitly authorizes that independent evaluation. Human attribution/boundary adjudication remains deferred and must precede policy-facing coalition interpretations.

## Development confound controls and synthetic evaluator — 8 October 2026

[The nuisance-only controls and country-name masking comparison](DEVELOPMENT_CONTROLS.md) are complete without reopening any reserved source. Source metadata *without diplomatic text* crossed the earlier conditional overlap threshold, and an artificial country-identity signal reproduced country-neighbor enrichment. Masking 3,330 country-name occurrences in 1,243 strict development passages reduced the raw semantic same-country neighbor share from 9.1% to 3.8%, while lexical/semantic neighbor overlap remained above its conditional reference. This exposes substantial entity/metadata confounding; do not present the remaining associations as evidence of coalitions, stance or nonrandom geopolitics.

The held-out evaluator now has a **synthetic-only** dry-run mode covering all 37 fictitious meeting-status rows, passing/nonpassing and insufficient-coverage branches, and SHA256-verified frozen transformation/centroid prediction smoke tests. These do not authorize real reserved source access or validate real out-of-period accuracy. The original sealed evaluation lock remains unchanged. Human adjudication remains deferred. **Next:** an independent scientific review of null/reference adequacy, recurring-speaker/agenda confounding, masked/unmasked source examples and holdout reliability; only after that and separate explicit owner approval should any real held-out evaluation be considered. Until then all 37 reserved transcripts must remain unopened.


## Independent nuisance and reserved-source readiness audit — 8 October 2026

[Independent read-only audit](INDEPENDENT_NUISANCE_AUDIT.md) verifies every saved development text slice and the sealed source/model lock, reproduces the key lexical/semantic and country-masking figures without using the original scoring helper, and measures genre/role and meeting concentration. Agenda and country self-reference remain major explanations; person-level speaker recurrence is unidentifiable from the saved metadata. The existing 37-meeting evaluation lock is unchanged; no reserved transcript was accessed. **Readiness = HOLD**, not an authorized release. Before requesting separate authorization, validate a production-shaped, wholly synthetic raw-transcript/coverage/eligibility/frozen-inference pipeline and declare additional source-overlap, agenda, role and speaker-proxy handling without choosing new thresholds from the reserved period.
